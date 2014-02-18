"""
Seed
==============

Create some seed data.
"""

from argos.datastore import db
from argos.core.models import Entity, Article, Event, Story, Source
from argos.util.progress import progress_bar

import os, json

from datetime import datetime
from dateutil.parser import parse

def seed(debug=False):
    this_dir = os.path.dirname(__file__)
    seeds = open(os.path.join(this_dir, 'seed.json'), 'r')
    sources = open(os.path.join(this_dir, 'seed_sources.json'), 'r')

    print('Resetting the database...')
    db.drop_all()
    db.create_all()

    # Create sources
    print('Creating sources...')
    for url in json.load(sources):
        s = Source(url)
        db.session.add(s)
    db.session.commit()
    num_sources = Source.query.count()
    print('Created {0} sources.'.format(num_sources))

    # Create articles
    entries = json.load(seeds)
    print('Seeding {0} articles...'.format(len(entries)))
    articles = []
    for entry in entries:
        if debug:
            print(json.dumps(entry, sort_keys=True, indent=4))

        source = Source.query.filter_by(ext_url=entry['source']).first()

        a = Article(
                ext_url=entry['url'],
                source=source,
                html=entry['html'],
                text=entry['text'],
                tags=entry['tags'],
                title=entry['title'],
                created_at = parse(entry['published']),
                updated_at = parse(entry['updated']),
                image='http://frnsys.com/img/projects/album-art.png' # fake image
        )
        articles.append(a)
        db.session.add(a)

        progress_bar(len(articles) / len(entries) * 100)

    db.session.commit()

    num_articles = Article.query.count()
    num_entities = Entity.query.count()
    print('Seeded {0} articles.'.format(num_articles))
    print('Found {0} entities.'.format(num_entities))

    print('Clustering articles into events...')
    Event.cluster(articles, threshold=0.04, debug=True)
    num_events = Event.query.count()
    print('Created {0} event clusters.'.format(num_events))

    print('Clustering events into stories...')
    events = Event.query.all()
    Story.cluster(events, threshold=0.04, debug=True)
    num_stories = Story.query.count()
    print('Created {0} story clusters.'.format(num_stories))

    print('\n\n==============================================')
    print('From {0} sources, seeded {1} articles, found {2} entities, created {3} events and {4} stories.'.format(num_sources, num_articles, num_entities, num_events, num_stories))
    print('==============================================\n\n')


