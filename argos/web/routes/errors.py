from argos.web.app import app

from flask import jsonify
from flask.ext.restful import abort

def not_found():
    return abort(404, message='The resource you requested, {0}, was not found.'.format(request.path), status=404)

def unauthorized():
    return abort(401, message='You are not authorized to access {0}. Have you authenticated?'.format(request.path), status=401)

@app.errorhandler(404)
def internal_error(error):
    return jsonify(status=404, message='The resource you requested was not found.'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.exception(error)
    return jsonify(status=500, message='Internal server error.'), 500
