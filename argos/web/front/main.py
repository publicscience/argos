import argos.web.models as models

from datetime import datetime

import humanize

from flask import Blueprint, request, render_template

bp = Blueprint('main', __name__)

PER_PAGE = 20

@bp.route('/')
@bp.route('/latest')
def index():
    page = request.args.get('page', 1)
    events = models.Event.query.paginate(page, per_page=PER_PAGE).items
    return render_template('index.jade', events=events)

@bp.route('/events/<int:id>')
def events(id):
    event = models.Event.query.get(id)
    return render_template('event.jade', event=event)

@bp.app_template_filter()
def naturaltime(dt):
    """
    A tempalte filter for rendering
    datetimes in human-readable form,
    e.g. "1 hour ago", "5 days ago", etc.

    Example usage (in `pyjade`)::

        div= event.updated_at|naturaltime
    """
    return humanize.naturaltime(datetime.utcnow() - dt)
