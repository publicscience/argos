"""
Memory
======================

Interface for Solr.
"""

import httplib2
import sunburnt

SOLR_URL = 'http://localhost:8983/solr/'

class Memory:
    """
    An interface for Solr.
    """

    def __init__(self):
        """
        Setup and connect to Solr,
        and return a SolrInterface.
        """
        h = httplib2.Http(cache='/var/tmp/solr_cache')
        self.memory = sunburnt.SolrInterface(url=SOLR_URL, http_connection=h)


    def recall_page(self, title, page=0, per_page=10):
        """
        Retrieves pages by title.

        Args:
            | title (str)       -- the title of the page to retrieve
            | page (int)        -- the page number to return
            | per_page (int)    -- the number of results to return per page
        """
        return self.memory.query(title=title).paginate(start=page*per_page, rows=per_page).execute().result.docs


    def forget(self, doc):
        """
        Deletes a doc from Solr.

        Args:
            | doc (dict)  -- the doc object to delete
        """
        self.memory.delete(doc)
        self.memory.commit()


    def recall(self, doc_id):
        """
        Retrieves a doc by id from Solr.

        Args:
            | doc_id (str)  -- the doc id to retrieve
        """
        response = self.memory.query(id=doc_id).execute()
        if response:
            return response.result.docs[0]


    def memorize(self, doc):
        """
        Adds a doc to Solr.

        Args:
            | doc (str)  -- the doc content
        """
        self.memory.add(doc)
        self.memory.commit()

