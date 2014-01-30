from conf.base_security import *

# App Config

SQLALCHEMY_DATABASE_URI = "{DATABASE[default][TYPE]}://{DATABASE[default][HOST]}:{DATABASE[default][PORT]}/{DATABASE[default][NAME]}"

# Security Config

SECURITY_SEND_REGISTER_EMAIL = False 
SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False 
SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False 


