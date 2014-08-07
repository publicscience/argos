import sys

from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import MigrateCommand

from argos.web import api
from manage import web, core

from flask import request

if __name__ == '__main__':
    # Get the command to determine the app config.
    if 'evaluate' in sys.argv[1]:
        config = {
                'SQLALCHEMY_DATABASE_URI': 'postgresql://argos_user:password@localhost:5432/argos_eval'
        }
        app = api.create_app(**config)
    else:
        app = api.create_app()

    # For debugging...
    @app.before_request
    def log_request():
        print(request.url)
        print(request.headers)

    manager = Manager(app)

    # Web
    manager.add_command('create:client', web.CreateClientCommand())
    manager.add_command('create:admin', web.CreateAdminCommand())

    # Core
    manager.add_command('create:sources', core.CreateSourcesCommand())
    manager.add_command('seed', core.SeedCommand())
    manager.add_command('recluster', core.ReclusterCommand())
    manager.add_command('train', core.TrainVectorizerCommand())
    
    # Evaluation
    manager.add_command('profile', core.ProfileCommand())
    manager.add_command('evaluate:event', core.EvaluateEventCommand())
    manager.add_command('evaluate:story', core.EvaluateStoryCommand())

    # Misc
    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell())
    manager.add_command('server', Server(host='0.0.0.0'))

    manager.run()