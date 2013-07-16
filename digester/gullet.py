#!../shallowthought-env/bin/python

"""
Gullet
==============

An HTTP downloader.
Can resume downloads if the server supports it
(that is, it responds with an Accepts-Range header).
"""

import urllib2
import os

CHUNK = 16 * 1024

def download(url, save_path):
    """
    Downloads a file from the specified URL.
    Will resume an existing download if the target
    server supports it (responds with the "Accepts-Range" header).

    Args:
        | url (str)       -- url of the file to download
        | save_path (str) -- path to the directory to save the file
    """

    # Strip trailing slash, if there is one.
    save_path = save_path.rstrip('\/')
    filename = url.split('/').pop()
    file = '%s/%s' % (save_path, filename)

    existing_size = 0

    # If file already exists...
    if os.path.exists(file):
        # Append to existing file.
        outfile = open(file, 'ab')

        # Figure out how many bytes we've got.
        existing_size = os.path.getsize(file)

        # Setup request for only the remaining bytes.
        headers = {'Range': 'bytes=%s-' % (existing_size)}
        req = urllib2.Request(url, headers=headers)

    # Otherwise, create a new file.
    else:
        # Create a new file.
        outfile = open(file, 'wb')

        # Vanilla request.
        req = urllib2.Request(url)

    try:
        downloaded_size = 0

        # Get response.
        resp = urllib2.urlopen(req)

        # Get total size of content.
        total_size = float(resp.info().getheader('Content-Length').strip())

        # Check if the file has already been downloaded_size.
        if total_size == existing_size:
            print 'File already downloaded.'
            return

        # Check that the server accepts ranges.
        # If it does not, the server will ignore the Range header,
        # And we have to start all over again.
        if existing_size > 0 and not resp.info().getheader('Accept-Ranges'):
            print 'Server does not allow resuming of downloads.'
            print 'Starting from the beginning! :D'
            outfile = open(file, 'wb')

        # Pull out the chunks!
        for chunk in iter(lambda: resp.read(CHUNK), ''):
            # Write the chunk to the file.
            outfile.write(chunk)

            # Show progress.
            # downloaded_size += len(chunk)
            # print (downloaded_size/total_size) * 100

    except urllib2.HTTPError, e:
        print 'HTTP Error:', e.code, url
    except urllib2.URLError, e:
        print 'URL Error:', e.reason, url

def main():
    import sys
    if len(sys.argv) < 2:
        sys.exit('Please pass a URL to download from.')
    url = sys.argv[1]
    save_path = os.getcwd()
    download(url, save_path)
    return 0

if __name__ == '__main__':
    main()