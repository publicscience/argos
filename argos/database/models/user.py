from flask.ext.security import UserMixin, RoleMixin

from database.datastore import db

# Table connecting users and roles 
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    """
    A user's Role 
    
    Attributes:

        * id -> Integer (Primary Key)
        * name -> String (Unique)
        * description -> String
    """
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    """ 
    A user 
    
    Attributes:

        * id -> Integer (Primary Key)
        * email -> String (Unique)
        * password -> String (Unique)
        * active -> Bool
        * confirmed_at -> DateTime
        * roles -> [Role]
    """
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
