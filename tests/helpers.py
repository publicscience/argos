from argos.web.models import User
from argos.datastore import db
from argos.web.app import app
from flask_security.utils import login_user
from flask import jsonify, request

@app.route('/test_login', methods=['POST'])
def test_login():
    """
    A route for logging in users, for testing,
    since right now users are exclusively authenticated
    via third-party providers.
    """
    id = request.form['id']
    user = User.query.get(id)
    login_user(user)
    return jsonify(success=True)

def save(objs):
    """
    Saves a set of objects to the database.
    """
    if type(objs) is list:
        for obj in objs:
            db.session.add(obj)
    else:
        db.session.add(objs)
    db.session.commit()
