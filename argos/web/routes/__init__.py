from argos.web.app import app

from flask import jsonify

@app.errorhandler(404)
def internal_error(error):
    return jsonify(status=404, message='The resource you requested was not found.'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.exception(error)
    return jsonify(status=500, message='Internal server error.'), 500

from argos.web.routes import api, auth, oauth
