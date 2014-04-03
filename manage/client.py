from argos.datastore import db
from argos.web.models.oauth import Client

from flask.ext.script import Command

from werkzeug.security import gen_salt

class CreateClientCommand(Command):
    """
    Creates an official Client and
    prints its client id and secret.
    """
    def run(self):
        create_client()

def create_client():
    client = Client(
        client_id=gen_salt(40),
        client_secret=gen_salt(50),
        _redirect_uris='http://localhost:5000/authorized',
        _default_scopes='userinfo',
        _allowed_grant_types='authorization_code refresh_token password',
        user_id=None,
        is_confidential=True # make a confidential client.
    )
    db.session.add(client)
    db.session.commit()
    print("client id: {0}\nclient secret: {1}".format(client.client_id, client.client_secret))
