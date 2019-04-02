from flask import Flask, redirect, url_for, session, render_template
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret'
app.config['MONGO_URI'] = "mongodb://localhost:27017/todoDB"
mongo = PyMongo(app)

# Main routes
@app.route('/register')
def register():
    return 'register'

@app.route('/login')
def login():
    return 'login'

@app.route('/')
def home():
    return render_template('base.html', title='Todo - Home')

@app.route('/members')
def members():
    return 'members'

# Test routes
@app.route('/query-users')
def qusers():
    return 'users query'


if __name__ == '__main__':
    app.run(debug=True)