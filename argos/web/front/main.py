import argos.web.models as models

from datetime import datetime

import humanize

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext.security import current_user

bp = Blueprint('main', __name__)

PER_PAGE = 20

@bp.route('/')
@bp.route('/latest')
def latest():
    page = request.args.get('page', 1)
    events = models.Event.query.paginate(page, per_page=PER_PAGE).items
    return render_template('events/collection.jade', events=events, title='The latest events')

@bp.route('/trending')
def trending():
    page = request.args.get('page', 1)
    events = models.Event.query.order_by(models.Event._score.desc()).paginate(page, per_page=PER_PAGE).items
    return render_template('events/collection.jade', events=events, title='The latest, most shared events')

@bp.route('/events/<int:id>')
def event(id):
    event = models.Event.query.get(id)
    return render_template('events/member.jade', event=event)

@bp.route('/stories/<int:id>')
def story(id):
    story = models.Story.query.get(id)
    return render_template('stories/member.jade', story=story)

@bp.route('/concepts/<string:slug>')
def concept(slug):
    concept = models.Concept.query.get(slug)
    return render_template('concepts/member.jade', concept=concept)

@bp.route('/watching')
def watching():
    if current_user.is_authenticated():
        events = models.Event.query.join(models.Event.stories).filter(models.Event.stories.any(models.Story.id.in_([story.id for story in current_user.watching]))).all()
        return render_template('events/collection.jade', events=events, title='The latest from stories you\'re watching', empty_msg='You aren\'t watching any stories!')
    else:
        flash('You need to be logged in')
        return redirect(url_for('security.login'))

@bp.route('/bookmarked')
def bookmarked():
    if current_user.is_authenticated():
        events = current_user.bookmarked
        return render_template('events/collection.jade', events=events, title='Your bookmarked events', empty_msg='You haven\'t bookmarked anything!')
    else:
        flash('You need to be logged in')
        return redirect(url_for('security.login'))

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
