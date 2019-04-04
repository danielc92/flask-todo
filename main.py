from flask import Flask, redirect, flash, request, url_for, session, render_template, jsonify
from flask_pymongo import PyMongo
import hashlib
from functools import wraps
from datetime import datetime
import json
from random import choice

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret'
app.config['SALT'] = 'salty'
app.config['MONGO_URI'] = "mongodb://localhost:27017/todoDB"
mongo = PyMongo(app)


# Load quote data
with open('./quotes.json', 'r') as f:
    quotes = json.load(f)


# Drop the database
# mongo.db.todo.drop()

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
            data['register-date'] = datetime.now().strftime('%Y-%m-%d')
            data['password'] = hash_password(data['password'], salt=app.config['SALT'])
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

@app.route('/', methods=['POST', 'GET'])
@login_required
def home():
    """If request is post process task form, else render board page with a random quote."""
    if request.method == 'POST':
        # Create task dictonary, grab name, desc and value from form
        # Auto generate the status as incomplete and the datetime
        task = dict()
        task['name'] = request.form.get('task-name')
        task['desc'] = request.form.get('task-desc')
        task['value'] = request.form.get('task-value')
        task['status'] = 'incomplete'
        task['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Push task using session as unique id
        mongo.db.todo.update({'email':session['logged_in']}, {'$push': {'tasks': task}})
        return redirect(url_for('home'))
    else:
        data = mongo.db.todo.find({'email':session['logged_in']})[0]
        quote = choice(quotes)
        return render_template('board.html', quote=quote, title='Todo - Board', data=data)


@app.route('/about')
@login_required
def about():
    """Render about page."""
    return render_template('about.html', title='Todo - About')


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
