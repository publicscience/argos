"""
Request
==============
"""

from urllib import request, error, parse
from time import sleep

MAX_RETRIES = 6

def make_request(url, max_retries=MAX_RETRIES, open_func=None):
    """
    Get the response for a given url or Request.

    Make Unicode-safe requests
    which retry on certain errors:

    * 503 Service Unavailable
    * Connection Reset
    * URLError

    Args:
        | url (str/Request)     -- the url or Request to open.
        | max_retries (int)     -- the maximum number of times to retry (optional)
        | open_func (function)  -- the function to use to open the url/Request. Defaults to `urllib.request.urlopen`, but you can pass in a custom opener as well.
    """
    retries = 0

    if open_func is None:
        open_func = request.urlopen

    while retries < max_retries:
        try:
            quoted_url = parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
            return open_func(quoted_url)

        except error.HTTPError as e:
            if e.code == 503 and retries < max_retries:
                sleep(1*retries)
                retries += 1
            else:
                raise

        except (ConnectionResetError, error.URLError) as e:
            if retries < max_retries:
                sleep(1*retries)
                retries += 1
            else:
                raise
