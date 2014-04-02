from argos.web.models import User
from argos.datastore import db
from flask_security.utils import login_user
from flask import Blueprint, jsonify, request

blueprint = Blueprint('tests', __name__)

@blueprint.route('/test_login', methods=['POST'])
def test_login():
    """
    A route for logging in users, for testing.
    """
    id = request.form['id']
    user = User.query.get(id)
    login_user(user)
    return jsonify(success=True)

def save(objs=None):
    """
    Saves a set of objects to the database,
    or just saves changes to the database.
    """
    if objs is not None:
        if type(objs) is list:
            db.session.add_all(objs)
        else:
            db.session.add(objs)
    db.session.commit()
