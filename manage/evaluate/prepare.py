"""
Prepare
=========
Prepares the database for evaluation.
"""

from argos.datastore import db
from argos.core.models import Source, Feed, Article, Author, Concept
from argos.core.membrane import evaluator, extractor

import random
import dateutil.parser
import json

from manage.evaluate.patch import patch_external, stop_patches

def seed():
    """
    Seeds the evaluation data into the evaluation database.
    """
    confirm = raw_input('This will reset your database. Are you sure?')
    if confirm.lower() not in ['y', 'yes', 'yeah', 'ya', 'aye']:
        print('Nevermind then!')
        return

    seed = json.load(open('manage/data/evaluation/seed.json'))

    patches = patch_external()

    print('Resetting the database...')
    db.drop_all()
    db.create_all()

    print('Seeding the articles...')
    print('This may take awhile...')
    articles = []
    for source_name, source_data in seed['sources'].items():
        source = Source(name=source_name, icon=source_data['icon'])
        db.session.add(source)
        db.session.commit()

        for feed_url, raw_articles in source_data['feeds'].items():
            feed = Feed(ext_url=feed_url, source=source)
            db.session.add(feed)
            db.session.commit()

            for article_data in raw_articles:
                # Create/get authors.
                authors = []
                for name in article_data['authors']:
                    author = Author.query.filter_by(name=name).first()
                    if not author:
                        author = Author(name=name)
                        db.session.add(author)
                    authors.append(author)
                db.session.commit()

                article = Article(
                    ext_url=article_data['ext_url'],
                    source=source,
                    feed=feed,
                    html=article_data['html'],
                    text=article_data['text'],
                    authors=authors,
                    title=article_data['title'],
                    created_at=article_data['created_at'],
                    updated_at=article_data['updated_at'],
                    image=article_data['image'],
                    score=article_data['score']
                )
                db.session.add(article)
                articles.append(article)
    db.session.commit()

    num_articles = Article.query.count()
    num_concepts = Concept.query.count()
    print('\n\n==============================================')
    print('Seeded {0} articles.'.format(num_articles))
    print('Found {0} concepts.'.format(num_concepts))
    print('==============================================\n\n')

    stop_patches(patches)

    print('Done seeding.')


def generate():
    """
    This generates or updates evaluation seed data based on the
    data in the `seed_source.json` file.
    """
    print('Generating seed data...')

    # Load the existing data, to check against.
    try: 
        seed_existing = json.load(open('manage/data/evaluation/seed.json', 'r'))
    except FileNotFoundError:
        seed_existing = {}

    # Copy the url file as a starting template.
    seed = json.load(open('manage/data/evaluation/seed_source.json', 'r'))

    # Some authors to use, since the author extraction doesn't seem to work.
    available_authors = ['Peter Baker', 'Mark Landler', 'Alan Cowell', 'Marina Woo', 'Jessica Smith', 'Hilary Baum']

    def article_exists(article, existing_articles):
        for existing_article in existing_articles:
            if existing_article['ext_url'] == url:
                article.update(existing_article)
                return True
        return False

    print('Gathering article data...')
    for source_name, source_data in seed['sources'].items():
        for feed_url, articles in source_data['feeds'].items():
            for article in articles:
                url = article['ext_url']

                # Skip if the data for this article already exists.
                if seed_existing:
                    existing_articles = seed_existing['sources'][source_name]['feeds'][feed_url]
                else:
                    existing_articles = []

                if not article_exists(article, existing_articles):
                    print('Extracting for url: {0}'.format(url))
                    entry_data, html = extractor.extract_entry_data(url)
                    full_text = entry_data.cleaned_text
                    url = entry_data.canonical_link or url
                    published = dateutil.parser.parse(article['published'])
                    updated = published
                    title = entry_data.title

                    # Download and save the top article image.
                    image_url = extractor.extract_image(entry_data, filename=hash(url))

                    authors = random.sample(available_authors, 2)

                    score = evaluator.score(url)

                    article.update({
                        "ext_url":url,
                        "source":source_name,
                        "feed":feed_url,
                        "html":html,
                        "text":full_text,
                        "authors":authors,
                        "title":title,
                        "created_at":str(published),
                        "updated_at":str(updated),
                        "image":image_url,
                        "score":score
                    })

    json.dump(seed, open('manage/data/evaluation/seed.json', 'w'), sort_keys=True, indent=4, separators=(',', ': '))
    print('Done generating seed data.')


