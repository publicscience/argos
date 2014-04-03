from flask.ext.script import Manager

from argos.web import api
from manage import PonderCommand, LoadSourcesCommand

manager = Manager(api.create_app())
manager.add_command('ponder', PonderCommand())
manager.add_command('load_sources', LoadSourcesCommand())

if __name__ == '__main__':
    manager.run()