from flask import Blueprint, jsonify, request

from argos.util.logger import logger
logger = logger(__name__)

bp = Blueprint('errors', __name__)

@bp.app_errorhandler(404)
def not_found_error(error):
    return jsonify(status=404, message='The resource you requested was not found.'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    logger.exception('Interal server error when requesting {0}: {1}'.format(request.path, error))
    return jsonify(status=500, message='Internal server error.'), 500
