#!/bin/bash

# Install Salt
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:saltstack/salt -y
sudo apt-get update -y
sudo apt-get install salt-minion -y
sudo apt-get install salt-master -y
sudo apt-get upgrade -y

# Set env variables.
# The application will uses these to configure Celery and the DB.
export DB_HOST=$master_dns
export BROKER_URL=amqp://guest@$master_dns//

# Edit Minion config to
# set Salt Master location
sudo sed -i 's/#master: salt/master: $master_dns/' /etc/salt/minion

# Start Minion
salt-minion -d
