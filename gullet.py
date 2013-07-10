#!./shallowthought-env/bin/python

'''
Gullet
==============

An HTTP downloader.
Can resume downloads if the server supports it
(that is, it responds with an Accepts-Range header).
'''

import urllib2
import math
import os

CHUNK = 16 * 1024

url = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-stub-articles5.xml.gz'
filename = url.split('/').pop()
file = '/Users/ftseng/Desktop/%s' % (filename)

def main():
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
            print 'We have to start from the beginning...'
            outfile = open(file, 'wb')

        # Pull out the chunks!
        for chunk in iter(lambda: resp.read(CHUNK), ''):
            # Write the chunk to the file.
            outfile.write(chunk)

            # Show progress.
            downloaded_size += len(chunk)
            print (downloaded_size/total_size) * 100

    except urllib2.HTTPError, e:
        print 'HTTP Error:', e.code, url
    except urllib2.URLError, e:
        print 'URL Error:', e.reason, url

if __name__ == '__main__':
    main()