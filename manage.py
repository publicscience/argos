from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import MigrateCommand

from argos.web import api
from manage import CreateSourcesCommand, CreateClientCommand, CreateAdminCommand, SeedCommand, ProfileCommand, EvaluateCommand, PseudoseedCommand

manager = Manager(api.create_app())
manager.add_command('create:sources', CreateSourcesCommand())
manager.add_command('create:client', CreateClientCommand())
manager.add_command('create:admin', CreateAdminCommand())
manager.add_command('profile', ProfileCommand())
manager.add_command('evaluate', EvaluateCommand())
manager.add_command('seed', SeedCommand())
manager.add_command('shell', Shell())
manager.add_command('server', Server(host='0.0.0.0'))
manager.add_command('db', MigrateCommand)
manager.add_command('pseudoseed', PseudoseedCommand())

# Groom (temporary commands for fixes and such)
# none at the moment

if __name__ == '__main__':
    manager.run()