#!/bin/bash

# (Salt is already installed on the image)

# Set env variables.
# The application will uses these to configure Celery and the DB.
echo -e '\nexport DB_HOST='$master_dns | sudo tee -a /etc/environment
echo -e 'export BROKER_URL=amqp://guest@'$master_dns'//' | sudo tee -a /etc/environment

# Edit Minion config to
# set Salt Master location
sudo sed -i 's/#master: salt/master: $master_dns/' /etc/salt/minion
# automatically call 'highstate' on connection.
sudo sed -i "s/#startup_states: ''/startup_states: highstate/" /etc/salt/minion

# Set the grains so we can target minions as workers.
echo -e 'roles:\n  - worker' | sudo tee -a /etc/salt/grains

# Restart Salt Minion
#sudo service salt-minion restart
sudo salt-minion
