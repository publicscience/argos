from web.app import app

from database.datastore import init_db_flask

# Initialize the database
init_db_flask(app)

# Import routes (which depend on 
# the database)
from web import routes

# Run!
app.run(debug=True)
