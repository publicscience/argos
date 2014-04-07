import argos.web.models as models
from argos.datastore import db

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext.security import current_user, login_required

bp = Blueprint('user', __name__)

PER_PAGE = 20

@bp.route('/')
def feed():
    page = request.args.get('page', 1)

    if current_user.is_authenticated() and len(current_user.watching) > 0:
        # Get all the events which belong to stories that the user is watching.
        # This is so heinous, and probably very slow – but it works for now.
        # Eventually this will also have highly-promoted stories as well.
        events = models.Event.query.join(models.Event.stories).filter(models.Event.stories.any(models.Story.id.in_([story.id for story in current_user.watching]))).order_by(models.Event.created_at.desc()).all()
        title = 'Your latest events'

    # Default to trending events
    else:
        # Filter to only show events which have been clustered
        # (i.e. they belong to at least one story)
        events = models.Event.query.filter(models.Event.stories).order_by(models.Event._score.desc()).paginate(page, per_page=PER_PAGE).items
        title = 'The latest, most shared events'
    return render_template('events/collection.jade', events=events, title=title)

@bp.route('/watching')
def watching():
    if current_user.is_authenticated():
        events = models.Event.query.join(models.Event.stories).filter(models.Event.stories.any(models.Story.id.in_([story.id for story in current_user.watching]))).all()
        return render_template('events/collection.jade', events=events, title='The latest from stories you\'re watching', empty_msg='You aren\'t watching any stories!')
    else:
        flash('You need to be logged in')
        return redirect(url_for('security.login'))

@bp.route('/watch', methods=['POST', 'DELETE'])
@login_required
def watch():
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

@bp.route('/bookmark', methods=['POST', 'DELETE'])
@login_required
def bookmark():
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

@bp.route('/bookmarks')
def bookmarks():
    if current_user.is_authenticated():
        events = current_user.bookmarked
        return render_template('events/collection.jade', events=events, title='Your bookmarks', empty_msg='You haven\'t bookmarked anything!')
    else:
        flash('You need to be logged in')
        return redirect(url_for('security.login'))
