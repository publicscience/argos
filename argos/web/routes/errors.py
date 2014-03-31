from argos.web.app import app

from flask import jsonify, request
from flask.ext.restful import abort

from argos.util.logger import logger
logger = logger(__name__)

def not_found():
    return abort(404, message='The resource you requested, {0}, was not found.'.format(request.path), status=404)

def unauthorized():
    return abort(401, message='You are not authorized to access {0}. Have you authenticated?'.format(request.path), status=401)

@app.errorhandler(404)
def not_found_error(error):
    return jsonify(status=404, message='The resource you requested was not found.'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.exception('Interal server error when requesting {0}: {1}'.format(request.path, error))
    return jsonify(status=500, message='Internal server error.'), 500
