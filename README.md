# Flask TODO App
Designing and building a 'todo' style web application. Flask to be used as web framework. Mongodb as a backend and possibly Redis as a cache store.

# Before you get started
Familiarity with the following will help.
- Python **3.6.5**
- Web frameworks (flask)
- NOSQL databases
- Cache servers

# Requirements
- Login / Register system
- A NOSQL Task system defined by user
- Task page with user scope
- Profile page with user scope
- Members page with global scope

# Setup
**How to obtain this repository:**
```sh
git clone https://github.com/danielc92/flask-todo.git
```
**Modules/dependencies:**
- `flask`
- `flask_pymongo`

Install the following dependences:
```sh
pip install flask flask_pymongo
```

MongoDB
```sh
# Installation using brew
brew install mongodb

# Running locally
mongod
```

# Tests
The following tests have been successfully completed.
- 'Render' 'register', 'login', 'members' and 'home' routes
- Register an account
- Verify hashing function is working
- Create task on 'home' route
- Render tasks on 'home' route

# Contributors
- Daniel Corcoran

# Sources
- [Bulma Documentation](https://bulma.io/)
- [Flask Documentation](http://flask.pocoo.org/)
- [MongoDB Manual](https://docs.mongodb.com/manual/introduction/)
- [Updating nested arrays in MongoDB](https://www.mattburkedev.com/updating-inside-a-nested-array-with-the-mongodb-positional-operator-in-c-number/)
