"""
Scheduler
==============

This is a scheduled job
to fetch the latest Wikipedia
dump and parse it.

This current version is
*only a sketch*.

Import considerations:
    * The scheduled time interval
    should be longer than it takes
    to parse the dump.
"""

from wikidigester import WikiDigester
import schedule
import time

def job():
    """
    Update the dump
    """
    w = WikiDigester('data/wiki/wiki_temp.xml', 'pages')
    w.fetch_dump()
    w.digest()


def main():
    schedule.every(30).days.at("4:30").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()

