import os
import json
from datetime import datetime

from flask.ext.script import Command, Option
from ftfy import fix_text_segment

from argos.datastore import db
from argos.core.membrane import evaluator
from argos.core.models import Article, Event, Source, Feed, Author
from argos.util.progress import progress_bar

from unittest.mock import patch

class LoadCorporaCommand(Command):
    """
    Loads exported argos.corpora json into the db.
    """
    option_list = (
        Option(dest='dumppath', type=str),
        Option('-p', '--patch', dest='use_patch', action='store_true', required=False)
    )
    def run(self, dumppath, use_patch):
        if use_patch:
            print('Patching out saving images to S3...')
            patcher = patch('argos.util.storage.save_from_url', autospec=True, return_value='https://i.imgur.com/Zf9mXlj.jpg')
            patcher.start()
        else:
            patcher = None

        print('Loading sources...')
        sources_map = {}
        with open(os.path.join(dumppath, 'sources.json'), 'r') as f:
            sources = json.load(f)
            for i, s in enumerate(sources):
                source = Source.query.filter(Source.name == s['name']).first()
                if not source:
                    source = Source(name=s['name'])
                    db.session.add(source)
                id = s['_id']['$oid']
                sources_map[id] = source

                progress_bar(i/(len(sources) - 1) * 100)

        db.session.commit()

        print('\nLoading feeds...')
        feeds_map = {}
        with open(os.path.join(dumppath, 'feeds.json'), 'r') as f:
            feeds = json.load(f)
            for i, f in enumerate(feeds):
                feed = Feed.query.filter(Feed.ext_url == f['ext_url']).first()
                if not feed:
                    feed = Feed(ext_url=f['ext_url'])
                    db.session.add(feed)
                feed.source = sources_map[f['source']['$oid']]

                id = f['_id']['$oid']
                feeds_map[id] = feed

                progress_bar(i/(len(feeds) - 1) * 100)

        db.session.commit()

        print('\nLoading articles...')
        with open(os.path.join(dumppath, 'articles.json'), 'r') as f:
            articles = json.load(f)
            for i, a in enumerate(articles):

                authors = []
                for author in a['authors']:
                    authors.append(Author.find_or_create(name=author))

                existing = Article.query.filter(Article.ext_url == a['ext_url']).first()

                if not existing:
                    feed = feeds_map[a['feed']['$oid']]
                    article = Article(
                        ext_url=a['ext_url'],
                        source=feed.source,
                        feed=feed,
                        html=None,    # not saved by argos.corpora
                        text=fix_text_segment(a['text']),
                        authors=authors,
                        tags=[],
                        title=fix_text_segment(a['title']),
                        created_at=datetime.fromtimestamp(a['created_at']['$date']/1000),
                        updated_at=datetime.fromtimestamp(a['updated_at']['$date']/1000),
                        image=a['image'],
                        score=evaluator.score(a['ext_url'])
                    )
                    db.session.add(article)
                progress_bar(i/(len(articles) - 1) * 100)

        print('Loaded {0} sources, {1} feeds, and {2} articles.'.format(len(sources), len(feeds), len(articles)))
        print('Done!')

        if patcher is not None:
            patcher.stop()
