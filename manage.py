import sys

from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import MigrateCommand

from argos import create_app
from manage import CreateSourcesCommand, SeedCommand, ProfileCommand, EvaluateCommand, ReclusterCommand

from flask import request

if __name__ == '__main__':
    # Get the command to determine the app config.
    if sys.argv[1] == 'evaluate':
        config = {
                'SQLALCHEMY_DATABASE_URI': 'postgresql://argos_user:password@localhost:5432/argos_eval'
        }
        app = create_app(**config)
    else:
        app = create_app()

    # For debugging...
    @app.before_request
    def log_request():
        print(request.url)
        print(request.headers)

    manager = Manager(app)
    manager.add_command('create:sources', CreateSourcesCommand())
    manager.add_command('profile', ProfileCommand())
    manager.add_command('evaluate', EvaluateCommand())
    manager.add_command('seed', SeedCommand())
    manager.add_command('shell', Shell())
    manager.add_command('server', Server(host='0.0.0.0'))
    manager.add_command('db', MigrateCommand)
    manager.add_command('recluster', ReclusterCommand())

    manager.run()