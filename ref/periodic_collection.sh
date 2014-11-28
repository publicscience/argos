# source your argos virtualenv
source /env/argos/bin/activate

# create celerybeat schedule folder
sudo mkdir -p /var/lib/celery/
# you should probably chown this dir to whatever user is running celery

# run celerybeat which periodically runs tasks.
# the tasks that are run are defined in argos/conf/default/celery.py
celery beat --app=argos.tasks.celery --schedule=/var/lib/celery/beat.db --pidfile=
