from app import app
from models import User
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

