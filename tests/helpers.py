from argos.web.models import User
from argos.web.models.oauth import Client, Token
from argos.datastore import db

from datetime import datetime
from flask_security.utils import login_user
from flask import Blueprint, jsonify, request
from werkzeug.security import gen_salt

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

@blueprint.route('/test_auth', methods=['POST'])
def test_auth():
    """
    A route for authenticating a user (OAuth), for testing.
    """
    user_id = request.form['id']

    client = Client(
        client_id=gen_salt(40),
        client_secret=gen_salt(50),
        _redirect_uris='http://localhost:5000/authorized',
        _default_scopes='userinfo',
        _allowed_grant_types='authorization_code refresh_token',
        user_id=user_id,
    )
    db.session.add(client)

    token = Token(
        access_token=gen_salt(40),
        refresh_token=gen_salt(40),
        token_type='authorization_code',
        _scopes='userinfo',
        expires=datetime.max,
        client_id=client.client_id,
        user_id=user_id
    )
    db.session.add(token)
    db.session.commit()
    return jsonify(token=token.access_token)

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
