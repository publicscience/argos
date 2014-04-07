from argos.web.models import User, Role
from argos.datastore import db

from flask.ext.script import Command, Option
#from flask.ext.security import UserDatastore

class CreateAdminCommand(Command):
    """
    Makes the user with the specified email
    an admin.
    """
    option_list = (
        Option(dest='email'),
    )
    def run(self, email):
        create_admin(email)

def create_admin(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        print('No user found for email: {0}'.format(email))

    # Create the admin role if necessary.
    role = Role.query.filter_by(name='admin').first()
    if not role:
        role = Role(name='admin')
        db.session.add(role)

    user.roles.append(role)
    db.session.commit()
    print('Admin role successfully added for {0}'.format(email))
