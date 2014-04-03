from tests import RequiresDatabase
from datetime import datetime

from argos.core.models import Source, Article, Event, Story

import manage

class ManageTest(RequiresDatabase):
    patch_knowledge = True
    patch_concepts = True

    def test_create_sources(self):
        mock_find_feed = self.create_patch('argos.core.membrane.feed.find_feed')

        url = 'sup'
        mock_find_feed.return_value = url

        manage.create_sources()
        self.assertTrue(Source.query.count() > 1)

    def test_ponder(self):
        # Add a fake source to work with.
        self.source = Source(ext_url='foo')
        self.db.session.add(self.source)
        self.db.session.commit()

        mock_articles = self.create_patch('argos.core.membrane.collector.get_articles')
        mock_articles.return_value = [
            Article(
                title='Foo',
                published=datetime.utcnow(),
                ext_url='foo.com',
                text='dinosaurs are cool, Clinton'
            )
        ]

        manage.ponder()

        self.assertEquals(Article.query.count(), 1)
        self.assertEquals(Event.query.count(), 1)
        self.assertEquals(Story.query.count(), 1)

        article = Article.query.first()
        self.assertEquals(article.title, 'Foo')
