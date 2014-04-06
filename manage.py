from flask.ext.script import Manager, Shell, Server

from argos.web import api
from manage import PonderCommand, CreateSourcesCommand, CreateClientCommand, SeedCommand, ProfileCommand, EvaluateCommand, ClusterArticlesCommand, ClusterEventsCommand

manager = Manager(api.create_app())
manager.add_command('ponder', PonderCommand())
manager.add_command('create:sources', CreateSourcesCommand())
manager.add_command('create:client', CreateClientCommand())
manager.add_command('cluster:articles', ClusterArticlesCommand())
manager.add_command('cluster:events', ClusterEventsCommand())
manager.add_command('profile', ProfileCommand())
manager.add_command('evaluate', EvaluateCommand())
manager.add_command('seed', SeedCommand())
manager.add_command('shell', Shell())
manager.add_command('server', Server(host='0.0.0.0'))

if __name__ == '__main__':
    manager.run()