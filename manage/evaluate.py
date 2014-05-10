"""
Evaluate
==========
For evaluating performance.
Can seed some hand-selected data
for this purpose.
"""

from argos.datastore import db
from argos.core.models import Source, Feed, Article, Author, Concept, Event, Story
from argos.core.membrane import evaluator, extractor
from argos.web.models.oauth import Client
from argos.util.progress import progress_bar

import json
import random
import numpy
import cProfile, pstats
import dateutil.parser
from unittest.mock import patch
from werkzeug.security import gen_salt
from colorama import Fore

# For creating a test user.
from flask_security.registerable import register_user
from flask import current_app

from flask.ext.script import Command, Option


class EvaluateCommand(Command):
    option_list = (
        Option(dest='cmd'),
        Option('--step', '-s', dest='step', default=0.05, type=float),
        Option('--min_threshold', '-min', dest='min_threshold', default=0.0, type=float),
        Option('--max_threshold', '-max', dest='max_threshold', default=1.0, type=float),
    )
    def run(self, cmd, step, min_threshold, max_threshold):
        if cmd == 'generate':
            generate()
        elif cmd == 'seed':
            seed()
        elif cmd == 'event':
            evaluate_events(step, min_threshold, max_threshold)
        elif cmd == 'story':
            evaluate_stories(step, min_threshold, max_threshold)
        elif cmd == 'clean':
            clean()
        else:
            print('Unrecognized command, use either `generate`, `seed`, `event`, or `story`.')


def seed():
    """
    Seeds the evaluation data into the evaluation database.
    """
    seed = json.load(open('manage/data/evaluation/seed.json'))

    print('Resetting the database...')
    db.drop_all()
    db.create_all()

    print('Seeding the articles...')
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


def generate():
    """
    This generates or updates evaluation seed data based on the
    data in the `seed_source.json` file.
    """
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


def evaluate_events(step, min_threshold, max_threshold):
    """
    Evaluate the event clustering algorithm.
    """
    clean()

    # Patch things that are time-consuming,
    # but which aren't being evaluated here.
    # In particular, summarization is *REALLY* slow,
    # and not being looked at here, so it's patched out.
    patches = start_patches()

    # Load the annotated data.
    print('Assembling expected article clusters...')
    expected_events = {}
    seed = json.load(open('manage/data/evaluation/seed.json'))
    for source_name, source_data in seed['sources'].items():
        for feed_url, raw_articles in source_data['feeds'].items():
            for article_data in raw_articles:
                article = Article.query.filter_by(ext_url=article_data['ext_url']).first()
                event_id = article_data['event']

                # Create the list for this event,
                # if it doesn't already exist.
                if not expected_events.get(event_id, False):
                    expected_events[event_id] = []

                # Keep track of which articles are
                # supposed to be clustered together.
                expected_events[event_id].append(article)
    print('\nExpecting {0}{1}{2} events.'.format(Fore.RED, len(expected_events), Fore.RESET))

    print('Clustering articles...')
    articles = Article.query.all()
    p = cProfile.Profile()

    # Run the clustering at the varying thresholds
    # and collect the scores.
    all_scores = {}
    for threshold in numpy.linspace(min_threshold, max_threshold, (max_threshold-min_threshold)/step):
        print('\nClustering with threshold {0}{1}{2}'.format(Fore.YELLOW, threshold, Fore.RESET))
        p.runcall(Event.cluster, articles, threshold=threshold, debug=False)
        num_events = Event.query.count()
        print('Created {0}{1}{2} events:'.format(Fore.YELLOW, num_events, Fore.RESET))
        print('{0}---{1}'.format(Fore.RED, Fore.RESET))

        # Evaluate the performance.
        # This could use refining!
        events = Event.query.all()
        scores = []
        for event in events:
            # So we can inspect the cluster compositions.
            print(set(event.members))

            # The lower the diff, the better.
            diffs = [len(set(event.members).symmetric_difference(set(expected))) for expected in expected_events.values()]

            # Get the minimum difference.
            scores.append(min(diffs))
        print('{0}---{1}'.format(Fore.RED, Fore.RESET))

        # Tweak the score so that the closer it is to 1, the better.
        final_score = 1/(sum(scores) + 1)
        print('Final score was {0}{1}{2}\n'.format(Fore.GREEN, final_score, Fore.RESET))

        # Save the score.
        all_scores[threshold] = final_score

        # Reset events.
        Event.query.delete()

    # Get the best score.
    best_threshold = max(all_scores, key=all_scores.get)
    print('{0}The threshold {1} had the best score of {2}.{3}'.format(Fore.GREEN, best_threshold, all_scores[best_threshold], Fore.RESET))

    # Print profiling results.
    print('\nProfiling statistics from the clustering...')
    print('{0}Note:{1} this profiling *does not* take into account summarization times, since that is patched out.'.format(Fore.RED, Fore.RESET))
    ps = pstats.Stats(p)
    ps.sort_stats('time').print_stats(10)

    # Disable patches.
    stop_patches(patches)

    ## Cleanup
    print('\nCleaning up...')
    clean()

    print('Done.')


def evaluate_stories(step, min_threshold, max_threshold):
    """
    Evaluate the story clustering algorithm.
    """
    clean()

    # Patch things that are time-consuming,
    # but which aren't being evaluated here.
    # In particular, summarization is *REALLY* slow,
    # and not being looked at here, so it's patched out.
    patches = start_patches()

    # Load the annotated data and create "perfect" article clusters.
    print('Assembling expected article clusters ("perfect" events)...')
    expected_events = {}
    expected_stories = {}
    seed = json.load(open('manage/data/evaluation/seed.json'))
    for source_name, source_data in seed['sources'].items():
        for feed_url, raw_articles in source_data['feeds'].items():
            for article_data in raw_articles:
                article = Article.query.filter_by(ext_url=article_data['ext_url']).first()
                event_id = article_data['event']

                # Create the list for this event,
                # if it doesn't already exist.
                if not expected_events.get(event_id, False):
                    expected_events[event_id] = []

                # Keep track of which articles are
                # supposed to be clustered together.
                expected_events[event_id].append(article)

    total_events = len(expected_events)
    completed_events = 0
    for story_name, events in seed['stories'].items():

        # Create the list for this story,
        # if it doesn't already exist.
        if not expected_stories.get(story_name, False):
            expected_stories[story_name] = []

        for event_id, event_title in events.items():
            # Create an event out of the annotated members.
            event = Event(expected_events[int(event_id)])

            # Manually set the titles for easier referencing.
            event.title = '[{0}{1}{2}] {3}'.format(Fore.BLUE, story_name.upper(), Fore.RESET, event_title)

            db.session.add(event)

            # Progress bar, for sanity.
            completed_events += 1
            progress_bar(completed_events/total_events * 100)

            # Keep track of which story this event is
            # supposed to belong to.
            expected_stories[story_name].append(event)
    db.session.commit()
    print('\nExpecting {0}{1}{2} stories.'.format(Fore.RED, len(expected_stories), Fore.RESET))

    print('Clustering events...')
    events = Event.query.all()
    p = cProfile.Profile()

    # Run the clustering at the varying thresholds
    # and collect the scores.
    all_scores = {}
    for threshold in numpy.linspace(min_threshold, max_threshold, (max_threshold-min_threshold)/step):
        print('\nClustering with threshold {0}{1}{2}'.format(Fore.YELLOW, threshold, Fore.RESET))
        p.runcall(Story.cluster, events, threshold=threshold, debug=False)
        num_stories = Story.query.count()
        print('Created {0}{1}{2} stories:'.format(Fore.YELLOW, num_stories, Fore.RESET))
        print('{0}---{1}'.format(Fore.RED, Fore.RESET))

        # Evaluate the performance.
        # This could use refining!
        stories = Story.query.all()
        scores = []
        for story in stories:
            # So we can inspect the cluster compositions.
            print(set(story.members))

            # The lower the diff, the better.
            diffs = [len(set(story.members).symmetric_difference(set(expected))) for expected in expected_stories.values()]

            # Get the minimum difference.
            scores.append(min(diffs))
        print('{0}---{1}'.format(Fore.RED, Fore.RESET))

        # Tweak the score so that the closer it is to 1, the better.
        final_score = 1/(sum(scores) + 1)
        print('Final score was {0}{1}{2}\n'.format(Fore.GREEN, final_score, Fore.RESET))

        # Save the score.
        all_scores[threshold] = final_score

        # Reset stories.
        Story.query.delete()

    # Get the best score.
    best_threshold = max(all_scores, key=all_scores.get)
    print('{0}The threshold {1} had the best score of {2}.{3}'.format(Fore.GREEN, best_threshold, all_scores[best_threshold], Fore.RESET))

    # Print profiling results.
    print('\nProfiling statistics from the clustering...')
    print('{0}Note:{1} this profiling *does not* take into account summarization times, since that is patched out.'.format(Fore.RED, Fore.RESET))
    ps = pstats.Stats(p)
    ps.sort_stats('time').print_stats(10)

    # Disable patches.
    stop_patches(patches)

    ## Cleanup
    print('\nCleaning up...')
    clean()

    print('Done.')


def clean():
    Story.query.delete()
    Event.query.delete()


def start_patches():
    patches = [
            patch('argos.core.brain.summarize.summarize', autospec=True, return_value=['foo']),
            patch('argos.core.brain.summarize.multisummarize', autospec=True, return_value=['foo'])
    ]
    for p in patches:
        p.start()
    return patches


def stop_patches(patches):
    for p in patches:
        p.stop()
