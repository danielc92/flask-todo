""" IMPORTS """
from flask import Flask, redirect, flash, request, url_for, session, render_template, jsonify
from flask_pymongo import PyMongo
from flask_recaptcha import ReCaptcha
from functools import wraps
from datetime import datetime
from random import choice
from uuid import uuid4
import hashlib, json, os, binascii


""" HELPER FUNCTIONS """

def hash_password(password, salt):
    """Return slow hashed SHA512 password, given password and salt."""
    encode='utf-8'
    dk = hashlib.pbkdf2_hmac('sha512', 
                             bytes(password, encode), 
                             bytes(salt, encode), 
                             100000)
    hashed = binascii.hexlify(dk)
    hashed_string = hashed.decode(encode)
    return hashed_string

def validate_password(password):
    """Function to validate password."""

    password = str(password)
    error=None

    valid_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*'

    # First check length
    length = len(password)
    if 10<=length<=20:
        # Second, check chars
        for char in password:
            if char not in valid_chars:
                error=True
                break
    else:
        error=True

    return error


def return_uuid():
    """Return a unique code."""
    return str(uuid4())


def return_timestamp():
    """Return timestamp from the current datetime."""
    now = datetime.now()
    stamp = datetime.timestamp(now)
    return stamp

def timestamp_to_datetime(stamp, format_code='%Y-%b-%d'):

    """Return string formatted datetime from timestamp object, given a format_code."""
    datetime_ = datetime.fromtimestamp(stamp)
    formatted = datetime_.strftime(format_code)
    return formatted

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


app = Flask(__name__)
app.jinja_env.filters['timestamp_to_datetime'] = timestamp_to_datetime
app.config['SECRET_KEY'] = 'top-secret'
app.config['SALT'] = 'salty'
app.config['RECAPTCHA_ENABLED'] = True

# Call recaptcha settings from environment variables
app.config['RECAPTCHA_SITE_KEY'] = os.getenv('RECAP_SITE')
app.config['RECAPTCHA_SECRET_KEY'] = os.getenv('RECAP_SECRET')

# Initialize recaptcha instance providing site key, secret key and app instance
recaptcha = ReCaptcha(app=app,
                      secret_key=app.config['RECAPTCHA_SECRET_KEY'],
                      site_key=app.config['RECAPTCHA_SITE_KEY'],
                      is_enabled=app.config['RECAPTCHA_ENABLED'])

if app.config['ENV'] == 'testing':
    app.config['MONGO_URI'] = "mongodb://localhost:27017/todoDB"
else:
    app.config['MONGO_URI'] = os.getenv('mongouri')

print(app.config['MONGO_URI'][:12])
mongo = PyMongo(app)


# Load quote data
with open('./quotes.json', 'r', encoding='utf8', errors='ignore') as f:
    quotes = json.load(f)

# Generate a random quote
quote = choice(quotes)


"""
Form Metadata

Register
* reg-name : 'the full name of applicant'
* reg-email : 'the email address of applicant/username'
* reg-password : 'the password'
* reg-confirm : password 'confirmation password above'
* reg-dob : 'date of birth of applicant'

Login
* log-email : 'email used to register'
* log-password : 'password used to register'
"""


""" ROUTES """

# Main routes
@app.route('/register', methods=['POST', 'GET'])
def register():
    """If request method is POST, process registration form, otherwise render form again."""
    if request.method == 'POST':
        # Reset error
        error = None

        if recaptcha.verify():

            # Gather Register Details
            data = dict()
            data['name'] = request.form.get('reg-name').lower()
            data['email'] = request.form.get('reg-email').lower()
            data['password'] = request.form.get('reg-password')
            data['confirm-password'] = request.form.get('reg-confirm-password')
            data['about-yourself'] = request.form.get('about-yourself')

            # Validation rounds
            if data['password'] != data['confirm-password']:
                error = 'Passwords must match.'

            # Check if email exists in mongo db
            if mongo.db.todo.find({'email':data['email']}).count() > 0:
                error = 'Email already exists.'

            # Validate the password with simple check
            if validate_password(data['password']):
                error = 'Passwords must be between 10-20 characters and can only contain a-z, A-Z, 0-9, !@#$%^&*.'

            if error:
                return render_template('account/register.html', error=error)
            else:
                # Redirect to login page if successful.
                data.pop('confirm-password')
                data['register-date'] = return_timestamp()
                data['password'] = hash_password(data['password'], salt=app.config['SALT'])
                data['tasks'] = []
                data['identicon-url'] = 'https://avatars.dicebear.com/v2/identicon/{}.svg'.format(return_uuid())
                mongo.db.todo.insert_one(data)
                return redirect(url_for('login'))

            return render_template('account/register.html', title='Todo - Register Page')
        else:
            error = 'Captcha failed, try again.'
            return render_template('account/register.html', title='Todo - Register Page', error=error)

    else:
        return render_template('account/register.html', title='Todo - Register Page')


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

            # If the password is correct set the session and update last login
            if record['password'] == password:
                session['logged_in'] = data['email']
                last_login = return_timestamp()
                mongo.db.todo.update({'email': session['logged_in']}, {'$set': {'last-login':last_login}})
                print('Logged in as: ',session['logged_in'])
                return redirect(url_for('home'))
            else:
                error = 'Incorrect Credentials.'
        else:
            error = 'Email does not exist.'

        if error:
            return render_template('account/login.html', error=error)

    # Redirect to home
    else:
        return render_template('account/login.html', title='Todo - Login Page')

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
        print(request.form.get('task-category'), type(request.form.get('task-category')))
        task['category'] = request.form.get('task-category')

        # Auto-create uuid, status and date created for the user.
        task['uuid'] = return_uuid()
        task['status'] = 'ready'
        task['date-created'] = return_timestamp()

        # Push task using session as unique id
        mongo.db.todo.update({'email': session['logged_in']}, {'$push': {'tasks': task}})

        return redirect(url_for('home', _anchor='piles'))

    else:

        # Store task data on user level
        data = mongo.db.todo.find({'email': session['logged_in']})[0]
        tasks = [t for t in data['tasks'] if t['status'] in ['complete', 'blocked', 'incomplete', 'ready']]

        tasks_complete = [t for t in tasks if t['status'] == 'complete']
        tasks_incomplete = [t for t in tasks if t['status'] == 'incomplete']
        tasks_blocked = [t for t in tasks if t['status'] == 'blocked']
        tasks_ready = [t for t in tasks if t['status'] == 'ready']

        return render_template('board/board.html',
                               quote=quote,
                               title='Todo - Board',
                               tasks_complete=tasks_complete,
                               tasks_incomplete=tasks_incomplete,
                               tasks_blocked=tasks_blocked,
                               tasks_ready=tasks_ready)


@app.route('/about')
@login_required
def about():
    """Render about page."""
    return render_template('generic/about.html', title='Todo - About')


@app.route('/task-update')
@login_required
def update_task():
    uuid = request.args.get('uuid')
    status = request.args.get('status')

    # If they complete task, set the timestamp for completion
    if status == 'complete':
        mongo.db.todo.update({'email': session['logged_in'], 'tasks':{ '$elemMatch':{'uuid': uuid}}},
                             {'$set': {'tasks.$.status': status, 'tasks.$.date-completed': return_timestamp()}})
    else:
        mongo.db.todo.update({'email': session['logged_in'], 'tasks':{ '$elemMatch':{'uuid': uuid}}},
                             {'$set': {'tasks.$.status': status}})

    return redirect(url_for('home', _anchor="piles"))


@app.route('/features')
@login_required
def features():
    """Render features page."""
    return render_template('generic/features.html', title='Todo - Features')


@app.route('/members')
@login_required
def members():
    """Query all members and render them as cards."""
    data = mongo.db.todo.find()
    return render_template('generic/members.html', data=data, title='Todo - Members')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
