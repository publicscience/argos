# Used to try getting env variables first.
import os

# Database config.
DB_HOST = os.getenv('DB_HOST', 'localhost')
