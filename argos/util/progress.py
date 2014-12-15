import sys
from time import time

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

    if percent == 100:
        print('\n')

class Progress():
    def print_progress(self, percent):
        """
        Show a progress bar.
        """
        if not hasattr(self, 'start_time'):
            self.start_time = time()
            elapsed_time = 0
        else:
            elapsed_time = time() - self.start_time
        if percent == 0:
            estimated = 0
        else:
            estimated = elapsed_time/percent
        remaining = estimated - elapsed_time
        percent *= 100

        if remaining > 3600:
            countdown = '{:8.2f}hrs'.format(remaining/3600)
        elif remaining > 60:
            countdown = '{:8.2f}min'.format(remaining/60)
        else:
            countdown = '{:8.2f}sec'.format(remaining)

        width = 100
        info = '{0:8.3f}% {1}'.format(percent, countdown)
        sys.stdout.write('[{0}] {1}'.format(' ' * width, info))
        sys.stdout.flush()
        sys.stdout.write('\b' * (width+len(info)+2))

        for i in range(int(percent)):
            sys.stdout.write('=')
            sys.stdout.flush()
        sys.stdout.write('\b' * (width+len(info)+2))

        if percent == 100:
            print('\n')

