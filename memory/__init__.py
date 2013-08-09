"""
Memory
======================

Interface for Solr.
"""

import httplib2
import sunburnt

SOLR_URL = "http://localhost:8983/solr/"

class Memory:
    def __init__(self):
        """
        Setup and connect to Solr,
        and return a SolrInterface.
        """
        h = httplib2.Http(cache='/var/tmp/solr_cache')
        self.memory = sunburnt.SolrInterface(url=SOLR_URL, http_connection=h)

    def recall_unaudited(self, page, per_page=10):
        """
        Retrieves unaudited Tweets.
        """
        per_page = 10
        return self.memory.query(audited=False).paginate(start=page*per_page, rows=per_page).execute().result.docs

    def recall_audited(self, page, per_page=10):
        """
        Retrieves audited Tweets.
        """
        return self.memory.query(audited=True).paginate(start=page*per_page, rows=per_page).execute().result.docs

    def recall_positive(self, page, per_page=10):
        """
        Retrieves positive (audited) Tweets.
        """
        return self.memory.query(audited=True, positive=True).paginate(start=page*per_page, rows=per_page).execute().result.docs

    def recall_negative(self, page, per_page=10):
        """
        Retrieves negative (audited) Tweets.
        """
        per_page = 10
        return self.memory.query(audited=True, positive=False).paginate(start=page*per_page, rows=per_page).execute().result.docs


    def forget(self, tweet):
        """
        Deletes a Tweet from Solr.
        """
        self.memory.delete(tweet)
        self.memory.commit()

    def recall(self, tweet_id):
        """
        Retrieves a Tweet by id from Solr.
        """
        response = self.memory.query(id=tweet_id).execute()
        if response:
            return response.result.docs[0]

    def memorize(self, tweet):
        """
        Adds a Tweet to Solr.

        Args:
            tweet (string): the Tweet content
        """
        self.memory.add(tweet)
        self.memory.commit()

