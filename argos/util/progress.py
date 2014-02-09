import sys

def progress_bar(percent):
    """
    Show a progress bar.
    """
    width = 100
    sys.stdout.write('[{0}] {1}'.format(' ' * width, '{:8.4f}'.format(percent)))
    sys.stdout.flush()
    sys.stdout.write('\b' * (width+10))

    for i in range(int(percent)):
        sys.stdout.write('=')
        sys.stdout.flush()
    sys.stdout.write('\b' * (width+10))
