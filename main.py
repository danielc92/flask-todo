from flask import Flask, redirect, flash, request, url_for, session, render_template, jsonify
from flask_pymongo import PyMongo
import hashlib
from functools import wraps
from datetime import datetime
import json
from random import choice
from uuid import uuid4

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret'
app.config['SALT'] = 'salty'
app.config['MONGO_URI'] = "mongodb://localhost:27017/todoDB"
mongo = PyMongo(app)

# Drop the database
# mongo.db.todo.drop()

# Load quote data
with open('./quotes.json', 'r') as f:
    quotes = json.load(f)


"""
Form Metadata

Register
* reg-name
* reg-email
* reg-password
* reg-confirm-password
* reg-dob

Login
* log-email
* log-password

"""


# Hashing function for raw passwords
def hash_password(password, salt):
    hashed = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()
    return hashed

def return_uuid():
    return str(uuid4())

def return_date(include_time=False):
    if include_time is True:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        return datetime.now().strftime('%Y-%m-%d')

# Login Required function
def login_required(f):
    """Check if user has been logged in, else redirect them to login route."""
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap


# Main routes
@app.route('/register', methods=['POST', 'GET'])
def register():
    """If request method is POST, process registration form, otherwise render form again."""
    if request.method == 'POST':
        # Reset error
        error = None

        # Gather Register Details
        data = dict()
        data['name'] = request.form.get('reg-name').lower()
        data['email'] = request.form.get('reg-email').lower()
        data['password'] = request.form.get('reg-password')
        data['confirm-password'] = request.form.get('reg-confirm-password')
        data['dob'] = request.form.get('reg-dob')

        # Validation rounds
        if data['password'] != data['confirm-password']:
            error = 'Passwords must match.'

        # Check if email exists in mongo db
        if mongo.db.todo.find({'email':data['email']}).count() > 0:
            error = 'Email already exists.'

        if error:
            return render_template('register.html', error=error)
        else:
            # Redirect to login page if successful.
            data.pop('confirm-password')
            data['register-date'] = return_date()
            data['password'] = hash_password(data['password'], salt=app.config['SALT'])
            data['tasks'] = []
            mongo.db.todo.insert_one(data)
            return redirect(url_for('login'))

        # Print inputs
        print(data)
        return render_template('register.html', title='Todo - Register Page')
    else:
        return render_template('register.html', title='Todo - Register Page')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        error = None
        # Gather login details
        data = dict()
        data['email'] = request.form.get('log-email').lower()
        data['password'] = request.form.get('log-password')

        # Validate credentials
        if mongo.db.todo.find({'email': data['email']}).count() > 0:

            record = mongo.db.todo.find({'email': data['email']})[0]
            password = hash_password(data['password'], salt=app.config['SALT'])

            if record['password'] == password:
                session['logged_in'] = data['email']
                return redirect(url_for('home'))
            else:
                error = 'Incorrect Credentials.'
        else:
            error = 'Email does not exist.'

        if error:
            return render_template('login.html', error=error)

    # Redirect to home
    else:
        return render_template('login.html', title='Todo - Login Page')

@app.route('/logout')
@login_required
def logout():
    """Logout a user by clearing their server side session."""
    session.pop('logged_in')
    return redirect(url_for('login'))

@app.route('/home', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
@login_required
def home():
    """If request is post process task form, else render board page with a random quote."""
    if request.method == 'POST':

        # Create task dictonary. Pull name, description and value from user input.
        task = dict()
        task['name'] = request.form.get('task-name')
        task['desc'] = request.form.get('task-desc')
        task['value'] = request.form.get('task-value')

        # Auto-create uuid, status and date created for the user.
        task['uuid'] = return_uuid()
        task['status'] = 'incomplete'
        task['date-created'] = return_date(include_time=True)

        # Push task using session as unique id
        mongo.db.todo.update({'email': session['logged_in']}, {'$push': {'tasks': task}})

        return redirect(url_for('home', _anchor='piles'))

    else:

        # Store task data on user level
        data = mongo.db.todo.find({'email': session['logged_in']})[0]
        tasks = data['tasks']
        tasks_complete = [t for t in tasks if t['status'] == 'complete']
        tasks_incomplete = [t for t in tasks if t['status'] == 'incomplete']

        # Generate a random quote
        quote = choice(quotes)
        return render_template('board.html',
                               quote=quote,
                               title='Todo - Board',
                               tasks_complete=tasks_complete,
                               tasks_incomplete=tasks_incomplete)


@app.route('/about')
@login_required
def about():
    """Render about page."""
    return render_template('about.html', title='Todo - About')


@app.route('/task-update')
@login_required
def update_task():
    uuid = request.args.get('uuid')
    status = request.args.get('status')

    mongo.db.todo.update({'email': session['logged_in'], 
                          'tasks':{ '$elemMatch':{'uuid': uuid}}},
                         {'$set': {'tasks.$.status': status, 
                         'tasks.$.date-completed':return_date(include_time=True)}})

    return redirect(url_for('home', _anchor="piles"))


@app.route('/features')
@login_required
def features():
    """Render features page."""
    return render_template('features.html', title='Todo - Features')


@app.route('/members')
@login_required
def members():
    """Query all members and render them as cards."""
    data = mongo.db.todo.find()
    return render_template('members.html', data=data, title='Todo - Members')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
