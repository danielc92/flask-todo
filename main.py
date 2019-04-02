from flask import Flask, redirect, request, url_for, session, render_template, jsonify
from flask_pymongo import PyMongo
import hashlib

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
        data['reg-dob'] = request.form.get('reg-dob')

        # Validation rounds
        if data['password'] != data['confirm-password']:
            error = 'Passwords must match.'

        # Check if email exists in mongo db
        if mongo.db.todo.find({'email':data['email']}).count() > 0:
            error = 'Email already exists.'

        if error:
            return render_template('register.html', error=error)
        else:
            # Store
            data.pop('confirm-password')
            mongo.db.todo.insert_one(data)
            return redirect(url_for('login'))
        # Redirect to login page

        # Print inputs
        print(data)
        return render_template('register.html', title='Todo - Register Page')
    else:
        return render_template('register.html', title='Todo - Register Page')
@app.route('/login', methods=['POST', 'GET'])
def login():

    # Gather login details

    # Validate against mongodb

    # Redirect to home

    return render_template('login.html', title='Todo - Login Page')

@app.route('/')
def home():
    return render_template('base.html', title='Todo - Home')

@app.route('/members')
def members():
    query = mongo.db.todo.find()
    users = ''
    for x in query:
        users += str(x)
    return users

# Test routes
@app.route('/query-users')
def qusers():
    return 'users query'


if __name__ == '__main__':
    app.run(debug=True)