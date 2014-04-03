from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.jade')

@bp.route('/event')
def event():
    return render_template('event.jade')
