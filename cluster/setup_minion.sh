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
echo -e '\nexport DB_HOST='$master_dns | sudo tee -a /etc/environment
echo -e 'export BROKER_URL=amqp://guest@'$master_dns'//' | sudo tee -a /etc/environment

# Edit Minion config to
# set Salt Master location
sudo sed -i 's/#master: salt/master: $master_dns/' /etc/salt/minion
# automatically call 'highstate' on connection.
sudo sed -i "s/#startup_states: ''/startup_states: highstate/" /etc/salt/minion

# Set the grains so we can target minions as workers.
echo -e 'role: worker' | sudo tee -a /etc/salt/grains

# Start Minion
sudo service salt-minion restart

# Start Celery worker.
sudo /var/app/digester/do worker
