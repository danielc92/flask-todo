from flask import Flask, redirect, flash, request, url_for, session, render_template, jsonify
from flask_pymongo import PyMongo
import hashlib
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret'
app.config['MONGO_URI'] = "mongodb://localhost:27017/todoDB"
mongo = PyMongo(app)

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

# Login Required function
def login_required(f):
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
    if request.method=='POST':
        # Reset error
        error = None

        # Gather Register Details
        data = dict()
        data['name'] = request.form.get('reg-name')
        data['email'] = request.form.get('reg-email')
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
        login = dict()
        login['email'] = request.form.get('log-email')
        login['password'] = request.form.get('log-password')

        # Validate credentials
        if mongo.db.todo.find({'email': login['email']}).count() > 0:
            record = mongo.db.todo.find({'email': login['email']})[0]
            if record['password'] == login['password']:
                session['logged_in'] = login['email']
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
    session.pop('logged_in')
    return redirect(url_for('login'))

@app.route('/', methods=['POST', 'GET'])
@login_required
def home():

    if request.method == 'POST':
        task = dict()
        task['name'] = request.form.get('task-name')
        task['desc'] = request.form.get('task-desc')
        task['status'] = 'incomplete'
        task['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mongo.db.todo.update({'email':session['logged_in']}, {'$push': {'tasks': task}})
        return redirect(url_for('home'))
    else:
        data = mongo.db.todo.find({'email':session['logged_in']})[0]['tasks']
        return render_template('board.html', title='Todo - Board', data=data)

@app.route('/about')
@login_required
def about():
    return render_template('about.html', title='Todo - About')

@app.route('/members')
@login_required
def members():
    data = mongo.db.todo.find()
    return render_template('members.html', data=data, title='Todo - Members')

# Test routes
@app.route('/query-users')
def qusers():
    return 'users query'


if __name__ == '__main__':
    app.run(debug=True)