# source your argos virtualenv
source /env/argos/bin/activate

# run celerybeat which periodically runs tasks.
# the tasks that are run are defined in argos/conf/default/celery.py
celery beat --app=argos.tasks.celery --schedule=/var/lib/celery/beat.db --pidfile=
