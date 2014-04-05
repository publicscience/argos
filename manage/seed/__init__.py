"""
Seed
==============

Create some seed data.
"""

from argos.datastore import db
from argos.core.models import Concept, Article, Event, Story, Source
from argos.util.progress import progress_bar
from argos.web.models.oauth import Client
from werkzeug.security import gen_salt

# For creating a test user.
from flask_security.registerable import register_user
from flask import current_app

from flask.ext.script import Command

import json
import os
import random
from datetime import datetime
from dateutil.parser import parse

# Boto outputs a lot of deprecation warnings (because it is
# still in the process of being ported to Py3).
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class SeedCommand(Command):
    """
    Creates seed data for development,
    including Sources, Articles, Events,
    Stories, Concepts, and a test User
    and Client.
    """
    def run(self):
        seed()

def seed(debug=False):
    seeds = open('manage/data/seed.json', 'r')

    sample_images = [
        'https://upload.wikimedia.org/wikipedia/commons/d/d5/Michael_Rogers_-_Herbiers_2004.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/6/6e/Brandenburger_Tor_2004.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/ChicagoAntiGaddafiHopeless.jpg/576px-ChicagoAntiGaddafiHopeless.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Evo_morales_2_year_bolivia_Joel_Alvarez.jpg/640px-Evo_morales_2_year_bolivia_Joel_Alvarez.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/2010_wet_season_cloud_over_colombia.jpg/640px-2010_wet_season_cloud_over_colombia.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Barack_Obama_at_Las_Vegas_Presidential_Forum.jpg/640px-Barack_Obama_at_Las_Vegas_Presidential_Forum.jpg'
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/2010-10-23-Demo-Stuttgart21-Befuerworter.png/640px-2010-10-23-Demo-Stuttgart21-Befuerworter.png',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/51%C2%BA_Congresso_da_UNE_%28Conune%29.jpg/640px-51%C2%BA_Congresso_da_UNE_%28Conune%29.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Tough_return%2C_365.35.jpg/640px-Tough_return%2C_365.35.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Saint_Isaac%27s_Cathedral_in_SPB.jpeg/800px-Saint_Isaac%27s_Cathedral_in_SPB.jpeg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Ponta_de_S%C3%A3o_Louren%C3%A7o_north_north_east.jpg/800px-Ponta_de_S%C3%A3o_Louren%C3%A7o_north_north_east.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/TU_Bibl_01_DSC1099w.jpg/644px-TU_Bibl_01_DSC1099w.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/%D0%9C%D0%B0%D0%BA%D0%B5%D0%B4%D0%BE%D0%BD%D0%B8%D1%83%D0%BC_-_%D0%9A%D1%80%D1%83%D1%88%D0%B5%D0%B2%D0%BE.jpg/800px-%D0%9C%D0%B0%D0%BA%D0%B5%D0%B4%D0%BE%D0%BD%D0%B8%D1%83%D0%BC_-_%D0%9A%D1%80%D1%83%D1%88%D0%B5%D0%B2%D0%BE.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Puente_Mong%2C_Ciudad_Ho_Chi_Minh%2C_Vietnam%2C_2013-08-14%2C_DD_01.JPG/800px-Puente_Mong%2C_Ciudad_Ho_Chi_Minh%2C_Vietnam%2C_2013-08-14%2C_DD_01.JPG',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Autignac%2C_H%C3%A9rault_01.jpg/800px-Autignac%2C_H%C3%A9rault_01.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Caesio_teres_in_Fiji_by_Nick_Hobgood.jpg/800px-Caesio_teres_in_Fiji_by_Nick_Hobgood.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Ash_in_Yogyakarta_during_the_2014_eruption_of_Kelud_01.jpg/800px-Ash_in_Yogyakarta_during_the_2014_eruption_of_Kelud_01.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/12-07-12-wikimania-wdc-by-RalfR-010.jpg/800px-12-07-12-wikimania-wdc-by-RalfR-010.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Mortagne-sur-Gironde_Civellier_Mayflowers_2013.jpg/800px-Mortagne-sur-Gironde_Civellier_Mayflowers_2013.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/British_Museum_Great_Court%2C_London%2C_UK_-_Diliff.jpg/611px-British_Museum_Great_Court%2C_London%2C_UK_-_Diliff.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Mercedes-Benz_Museum_201312_08_blue_hour.jpg/800px-Mercedes-Benz_Museum_201312_08_blue_hour.jpg'
    ]

    print('Resetting the database...')
    db.drop_all()
    db.create_all()

    # Create sources
    print('Creating sources...')
    create_sources()
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
                score=random.random() * 100         # fake score
        )
        articles.append(a)
        db.session.add(a)

        progress_bar(len(articles) / len(entries) * 100)

    print('Creating additional articles...')

    # Collect all appropriate files.
    all_files = []
    for dir, subdir, files in os.walk('manage/data/organized_articles'):
        for file in files:
            filepath = os.path.join(dir, file)
            name, ext = os.path.splitext(filepath)
            if ext == '.txt':
                all_files.append((dir, name, filepath))

    # Create articles for appropriate files.
    for dir, name, filepath in all_files:
        category = dir.split('/')[-1]
        f = open(filepath, 'r')
        article = Article(
                text=f.read(),
                title=name.split('/')[-1],
                ext_url='http://fauxurl/',
                source = Source.query.get(1),       # fake source
                image=random.choice(sample_images), # fake image
                score=random.random() * 100         # fake score
        )
        db.session.add(article)
        articles.append(article)
        progress_bar(len(articles)/len(all_files) * 100)

    db.session.commit()

    num_articles = Article.query.count()
    num_concepts = Concept.query.count()
    print('Seeded {0} articles.'.format(num_articles))
    print('Found {0} concepts.'.format(num_concepts))

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
    print('From {0} sources, seeded {1} articles, found {2} concepts, created {3} events and {4} stories.'.format(num_sources, num_articles, num_concepts, num_events, num_stories))
    print('==============================================\n\n')

    client = current_app.test_client()
    ctx = current_app.test_request_context()
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


def create_sources():
    sources = open('manage/data/seed_sources.json', 'r')

    for source in json.load(sources):
        s = Source(ext_url=source[1], name=source[0])
        db.session.add(s)
    db.session.commit()
