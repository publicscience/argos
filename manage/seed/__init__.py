"""
Seed
==============

Create some seed data.
"""

from argos.web.app import app
from argos.datastore import db
from argos.core.models import Entity, Article, Event, Story, Source
from argos.util.progress import progress_bar
from argos.web.models.oauth import Client
from werkzeug.security import gen_salt

# For creating a test user.
from flask_security.registerable import register_user

import os, json

from datetime import datetime
from dateutil.parser import parse

import random

def seed(debug=False):
    this_dir = os.path.dirname(__file__)
    seeds = open(os.path.join(this_dir, 'seed.json'), 'r')
    sources = open(os.path.join(this_dir, 'seed_sources.json'), 'r')

    sample_images = [
        'https://upload.wikimedia.org/wikipedia/commons/d/d5/Michael_Rogers_-_Herbiers_2004.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/6/6e/Brandenburger_Tor_2004.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/ChicagoAntiGaddafiHopeless.jpg/576px-ChicagoAntiGaddafiHopeless.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Evo_morales_2_year_bolivia_Joel_Alvarez.jpg/640px-Evo_morales_2_year_bolivia_Joel_Alvarez.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/2010_wet_season_cloud_over_colombia.jpg/640px-2010_wet_season_cloud_over_colombia.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Barack_Obama_at_Las_Vegas_Presidential_Forum.jpg/640px-Barack_Obama_at_Las_Vegas_Presidential_Forum.jpg'
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/2010-10-23-Demo-Stuttgart21-Befuerworter.png/640px-2010-10-23-Demo-Stuttgart21-Befuerworter.png',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/51%C2%BA_Congresso_da_UNE_%28Conune%29.jpg/640px-51%C2%BA_Congresso_da_UNE_%28Conune%29.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Tough_return%2C_365.35.jpg/640px-Tough_return%2C_365.35.jpg'
    ]

    print('Resetting the database...')
    db.drop_all()
    db.create_all()

    # Create sources
    print('Creating sources...')
    for url in json.load(sources):
        s = Source(ext_url=url, name='The Times') # fake name
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
                image=random.choice(sample_images), # fake image
                score=random.random() * 100 # fake score
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
    Event.cluster(articles, threshold=0.02, debug=True)
    num_events = Event.query.count()
    print('Created {0} event clusters.'.format(num_events))

    print('Clustering events into stories...')
    events = Event.query.all()
    Story.cluster(events, threshold=0.02, debug=True)
    num_stories = Story.query.count()
    print('Created {0} story clusters.'.format(num_stories))

    print('\n\n==============================================')
    print('From {0} sources, seeded {1} articles, found {2} entities, created {3} events and {4} stories.'.format(num_sources, num_articles, num_entities, num_events, num_stories))
    print('==============================================\n\n')

    client = app.test_client()
    ctx = app.test_request_context()
    ctx.push()
    register_user(email='t@t.c', password='password')
    ctx.pop()
    print('\n\n==============================================')
    print('Created a test user, email is t@t.c, password is password')
    print('==============================================\n\n')

    client = Client(
        #client_id=gen_salt(40),
        #client_secret=gen_salt(50),
        client_id='test',
        client_secret='test',
        _redirect_uris='http://localhost:5000/authorized',
        _default_scopes='userinfo',
        _allowed_grant_types='authorization_code refresh_token password',
        user_id=None,
        is_confidential=True # make a confidential client.
    )
    db.session.add(client)
    db.session.commit()
    print('\n\n==============================================')
    print('Created a test client:\nclient id: {0}\nclient secret: {1}'.format(client.client_id, client.client_secret))
    print('==============================================\n\n')


