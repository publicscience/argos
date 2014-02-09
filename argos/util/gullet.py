"""
Gullet
==============

An HTTP downloader.
Can resume downloads if the server supports it
(that is, it responds with an Accepts-Range header).
"""

from argos.util.logger import logger
from argos.util.progress import progress_bar

# Python 2.7 support.
try:
    from urllib import request
except ImportError:
    import urllib2 as request

import os, time, sys

# Logging.
logger = logger(__name__)

CHUNK = 16 * 1024

def download(url, save_path, progress=False):
    """
    Downloads a file from the specified URL.
    Will resume an existing download if the target
    server supports it (responds with the "Accepts-Range" header).

    Args:
        | url (str)       -- url of the file to download
        | save_path (str) -- path to the directory to save the file
        | progress (bool) -- output progress bar to stdout
    """

    # Strip trailing slash, if there is one.
    save_path = save_path.rstrip('\/')
    filename = url.split('/').pop()
    file = '{0}/{1}'.format(save_path, filename)

    existing_size = 0

    # If file already exists,
    # but there is not a newer file is on the server...
    if os.path.exists(file) and not _expired(url, file):
        # Append to existing file.
        outfile = open(file, 'ab')

        # Figure out how many bytes we've got.
        existing_size = outfile.tell()

        # Setup request for only the remaining bytes.
        headers = {'Range': 'bytes={0}-'.format(existing_size)}
        req = request.Request(url, headers=headers)

    # Otherwise, create a new/overwrite existing file.
    else:
        # Create/overwrite file.
        outfile = open(file, 'wb')
        outfile.seek(0)

        # Vanilla request.
        req = request.Request(url)

    try:
        # Get response.
        resp = request.urlopen(req)

        # Get total size of content.
        total_size = float(resp.headers['Content-Length'].strip())

        # Check if the file has already been downloaded_size.
        if total_size == existing_size:
            logger.info('File already downloaded.')
            return

        # Check that the server accepts ranges.
        # If it does not, the server will ignore the Range header,
        # And we have to start all over again.
        if existing_size > 0 and not resp.headers.get('Accept-Ranges', None):
            logger.info('Server does not allow resuming of downloads.')
            logger.info('Starting from the beginning! :D')
            outfile = open(file, 'wb')
            outfile.seek(0)

        if progress:
            progress_bar( (existing_size/total_size) * 100 )

        # Pull out the chunks!
        for chunk in iter(lambda: resp.read(CHUNK), b''):
            # Write the chunk to the file.
            outfile.write(chunk)

            # Update existing size.
            existing_size += len(chunk)

            percent_complete = (existing_size/total_size) * 100

            # Show progress.
            if progress:
                progress_bar(percent_complete)

        if progress:
            sys.stdout.write('\n')

        # Return the download's filepath.
        return file

    except request.HTTPError as e:
        logger.error('HTTP Error:', e.code, url)
    except request.URLError as e:
        logger.error('URL Error:', e.reason, url)


def _expired(url, file):
    """
    Determines if the remote file
    is newer than the local file.
    """
    req = request.Request(url)
    try:
        resp = request.urlopen(req)

        # Server file last modified.
        last_mod = resp.headers['Last-Modified']
        last_mod_time = time.strptime(last_mod, '%a, %d %b %Y %H:%M:%S %Z')

        # Local file last modified.
        file_last_mod = os.path.getmtime(file)
        file_last_mod_time = time.gmtime(file_last_mod)

        return last_mod_time > file_last_mod_time

    except request.HTTPError as e:
        logger.error('HTTP Error:', e.code, url)
    except request.URLError as e:
        logger.error('URL Error:', e.reason, url)

def main():
    if len(sys.argv) < 2:
        sys.exit('Please pass a URL to download from.')
    url = sys.argv[1]
    save_path = os.getcwd()
    download(url, save_path)
    return 0


if __name__ == '__main__':
    main()
