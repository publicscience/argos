#!../shallowthought-env/bin/python

"""
Gullet
==============

An HTTP downloader.
Can resume downloads if the server supports it
(that is, it responds with an Accepts-Range header).
"""

import urllib
import os
import sys

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
        req = urllib.Request(url, headers=headers)

    # Otherwise, create a new file.
    else:
        # Create a new file.
        outfile = open(file, 'wb')

        # Vanilla request.
        req = urllib.Request(url)

    try:
        # Get response.
        resp = urllib.urlopen(req)

        # Get total size of content.
        total_size = float(resp.info().getheader('Content-Length').strip())

        # Check if the file has already been downloaded_size.
        if total_size == existing_size:
            print('File already downloaded.')
            return

        # Check that the server accepts ranges.
        # If it does not, the server will ignore the Range header,
        # And we have to start all over again.
        if existing_size > 0 and not resp.info().getheader('Accept-Ranges'):
            print('Server does not allow resuming of downloads.')
            print('Starting from the beginning! :D')
            outfile = open(file, 'wb')

        if progress:
            _progress( (existing_size/total_size) * 100 )

        # Pull out the chunks!
        for chunk in iter(lambda: resp.read(CHUNK), ''):
            # Write the chunk to the file.
            outfile.write(chunk)

            # Show progress.
            if progress:
                existing_size += len(chunk)
                _progress( (existing_size/total_size) * 100 )

        if progress:
            sys.stdout.write('\n')

    except urllib.HTTPError as e:
        print('HTTP Error:', e.code, url)
    except urllib.URLError as e:
        print('URL Error:', e.reason, url)


def _progress(percent):
    """
    Show a progress bar.
    """
    width = 100
    sys.stdout.write('[%s] %s' % (' ' * width, '{:8.4f}'.format(percent)))
    sys.stdout.flush()
    sys.stdout.write('\b' * (width+10))

    for i in xrange(int(percent)):
        sys.stdout.write('=')
        sys.stdout.flush()
    sys.stdout.write('\b' * (width+10))


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