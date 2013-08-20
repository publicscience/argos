#!dev-env/bin/python

from tasks import add

def main():
    add.delay(4,4,'foo')
    add.delay(5,5,'bar')

if __name__ == '__main__':
    main()
