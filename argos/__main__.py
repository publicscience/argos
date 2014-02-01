from web import app, routes

from database.datastore import init_with_flask

# Initialize the database
init_with_flask(app)

app.run(debug=True)
