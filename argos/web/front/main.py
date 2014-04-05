import argos.web.models as models
from argos.datastore import db

import re
from datetime import datetime, timedelta

import jinja2
import humanize
from lxml.html.clean import clean_html

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext.security import current_user
from flask.ext import babel

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

@bp.route('/watch', methods=['POST', 'DELETE'])
def watch():
    if current_user.is_authenticated():
        id = request.args.get('story_id', None)
        if id is None:
            return 'You must specify an story_id', 400

        story = models.Story.query.get(id)
        if not story:
            return 'No story by that id', 404

        if request.method == 'POST':
            current_user.watching.append(story)
            db.session.commit()
            return 'Success', 201
        elif request.method == 'DELETE':
            current_user.watching.remove(story)
            db.session.commit()
            return 'Success', 204
    else:
        return 'You must be logged in', 401

@bp.route('/bookmark', methods=['POST', 'DELETE'])
def bookmark():
    if current_user.is_authenticated():
        id = request.args.get('event_id', None)
        if id is None:
            return 'You must specify an event_id', 400

        event = models.Event.query.get(id)
        if not event:
            return 'No event by that id', 404

        if request.method == 'POST':
            current_user.bookmarked.append(event)
            db.session.commit()
            return 'Success', 201
        elif request.method == 'DELETE':
            current_user.bookmarked.remove(event)
            db.session.commit()
            return 'Success', 204
    else:
        return 'You must be logged in', 401

@bp.route('/bookmarked')
def bookmarked():
    if current_user.is_authenticated():
        events = current_user.bookmarked
        return render_template('events/collection.jade', events=events, title='Your bookmarked events', empty_msg='You haven\'t bookmarked anything!')
    else:
        flash('You need to be logged in')
        return redirect(url_for('security.login'))

@bp.app_template_filter()
def natural_datetime(dt):
    """
    A template filter for rendering
    datetimes in human-readable form,
    e.g. "1 hour ago", "5 days ago", etc.

    Example usage (in `pyjade`)::

        div= event.updated_at|natural_datetime
    """
    return humanize.naturaltime(datetime.utcnow() - dt)

@bp.app_template_filter()
def natural_date(date):
    """
    A template filter for rendering
    dates in human-readable form,
    e.g. "5 days ago", etc.

    Example usage (in `pyjade`)::

        div= event.updated_at.date()|natural_date
    """
    dt = datetime.combine(date, datetime.min.time())
    diff = datetime.utcnow() - dt
    if diff <= timedelta(days=2):
        return humanize.naturalday(diff)
    return humanize.naturaltime(diff)

@bp.app_template_filter()
def format_date(date):
    format = 'MMMM d'
    dt = datetime.combine(date, datetime.min.time())
    if (datetime.utcnow() - dt).days > 365:
        format += ' y'
    return babel.format_date(date, format)

@bp.app_template_filter()
def highlight_mentions(text, mentions):
    """
    A template filter for highlighting
    mentions of concepts in a text.

    The mentions are first sorted by name length.
    """
    sorted_mentions = sorted(mentions, key=lambda x: len(x.name), reverse=True)
    for mention in sorted_mentions:
        text = re.sub(
                r' {name}(?!</a>)'.format(name=mention.name),
                ' <a href="{url}">{name}</a>'.format(
                    url=url_for('main.concept', slug=mention.slug),
                    name=mention.name),
                text)
    return text

@bp.app_template_filter()
def sanitize_html(html):
    """
    A template filter for
    sanitizing HTML.
    """
    # Wrap in jinja2.Markup so jinja doesn't
    # re-escape the html.
    return jinja2.Markup(clean_html(html))
