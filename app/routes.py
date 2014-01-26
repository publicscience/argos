from flask import jsonify
from app import app

@app.errorhandler(404)
def internal_error(error):
    return jsonify(error=404, text='The resource you requested was not found.'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.exception(error)
    return jsonify(error=500, text='Internal server error.'), 500
