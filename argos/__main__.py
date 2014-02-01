from web.app import app
from web import routes

from database.datastore import init_with_flask

# Initialize the database
init_with_flask(app)

# Run!
app.run(debug=True)
