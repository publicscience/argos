"""
Pseudoseed
==========

Seeds some hand-selected data,
for presentations/demoing and
also for tuning/evaluation.
"""

from argos.datastore import db
from argos.core.models import Source, Feed, Article, Author, Concept, Event, Story
from argos.core.membrane import evaluator, extractor
from argos.web.models.oauth import Client

import json
import random
import dateutil.parser
from werkzeug.security import gen_salt

# For creating a test user.
from flask_security.registerable import register_user
from flask import current_app

from flask.ext.script import Command


class PseudoseedCommand(Command):
    def run(self):
        main()

def main():
    seed = json.load(open('manage/data/pseudoseed.json'))

    print('Resetting the database...')
    db.drop_all()
    db.create_all()

    available_authors = []
    for name in ['Peter Baker', 'Mark Landler', 'Alan Cowell', 'Marina Woo', 'Jessica Smith', 'Hilary Baum']:
        author = Author(name=name)
        available_authors.append(author)
        db.session.add(author)
    db.session.commit()

    # Create the sources
    articles = []
    for source_ in seed['sources']:
        source = Source(name=source_['name'], icon=source_['icon'])
        db.session.add(source)
        db.session.commit()

        for feed_ in source_['feeds']:
            feed = Feed(ext_url=feed_['ext_url'], source=source)
            db.session.add(feed)
            db.session.commit()

            for article_ in feed_['articles']:
                url = article_['url']
                entry_data, html = extractor.extract_entry_data(url)
                full_text = entry_data.cleaned_text
                url = entry_data.canonical_link or url
                published = dateutil.parser.parse(article_['published'])
                updated = published
                title = entry_data.title

                # Download and save the top article image.
                image_url = extractor.extract_image(entry_data, filename=hash(url))

                authors = random.sample(available_authors, 2)

                score = evaluator.score(url)

                article = Article(
                    ext_url=url,
                    source=source,
                    feed=feed,
                    html=html,
                    text=full_text,
                    authors=authors,
                    title=title,
                    created_at=published,
                    updated_at=updated,
                    image=image_url,
                    score=score
                )
                db.session.add(article)
                articles.append(article)
    db.session.commit()

    num_articles = Article.query.count()
    num_concepts = Concept.query.count()
    print('Seeded {0} articles.'.format(num_articles))
    print('Found {0} concepts.'.format(num_concepts))

    print('Clustering articles into events...')
    Event.cluster(articles, threshold=0.5)
    num_events = Event.query.count()
    print('Created {0} event clusters.'.format(num_events))

    print('Clustering events into stories...')
    events = Event.query.all()
    Story.cluster(events, threshold=0.5)
    num_stories = Story.query.count()
    print('Created {0} story clusters.'.format(num_stories))

    print('\n\n==============================================')
    print('Seeded {0} articles, found {1} concepts, created {2} events and {3} stories.'.format(num_articles, num_concepts, num_events, num_stories))
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


