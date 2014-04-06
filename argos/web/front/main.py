import argos.web.models as models

from flask import Blueprint, request, render_template

bp = Blueprint('main', __name__)

PER_PAGE = 20

@bp.route('/latest')
def latest():
    page = request.args.get('page', 1)
    # Filter to only show events which have been clustered
    # (i.e. they belong to at least one story)
    events = models.Event.query.filter(models.Event.stories).paginate(page, per_page=PER_PAGE).items
    return render_template('events/collection.jade', events=events, title='The latest events')

@bp.route('/trending')
def trending():
    page = request.args.get('page', 1)
    # Filter to only show events which have been clustered
    # (i.e. they belong to at least one story)
    events = models.Event.query.filter(models.Event.stories).order_by(models.Event._score.desc()).paginate(page, per_page=PER_PAGE).items
    return render_template('events/collection.jade', events=events, title='The latest, most shared events')

@bp.route('/events/<int:id>')
def event(id):
    event = models.Event.query.get(id)
    return render_template('events/member.jade', event=event)

@bp.route('/events/<int:id>/articles')
def event_articles(id):
    event = models.Event.query.get(id)
    return render_template('articles.jade', entity=event)

@bp.route('/events/<int:id>/mentions')
def event_mentions(id):
    event = models.Event.query.get(id)
    return render_template('mentions.jade', entity=event)

@bp.route('/stories/<int:id>')
def story(id):
    story = models.Story.query.get(id)
    return render_template('stories/member.jade', story=story)

@bp.route('/stories/<int:id>/mentions')
def story_mentions(id):
    story = models.Story.query.get(id)
    return render_template('mentions.jade', entity=story)

@bp.route('/concepts/<string:slug>')
def concept(slug):
    concept = models.Concept.query.get(slug)
    return render_template('concepts/member.jade', concept=concept)

@bp.route('/concepts/<string:slug>/articles')
def concept_articles(slug):
    concept = models.Concept.query.get(slug)
    return render_template('articles.jade', entity=concept)