#!/bin/bash

# (Salt is already installed on the image)

# Kill the salt minion while we change things.
sudo pkill -9 -f salt-minion

# Edit Minion config to
# set Salt Master location
# The database instance is created before the master instance, so it won't know its hostname.
# For now, just let the database instance provision itself.
#sudo sed -i 's/#master: salt/master: $master_dns/' /etc/salt/minion
# automatically call 'highstate' on connection.
#sudo sed -i "s/#startup_states: ''/startup_states: highstate/" /etc/salt/minion

# Set the grains so we can target minions as workers.
echo -e 'roles:\n  - database' | sudo tee -a /etc/salt/grains

# Start the salt minion backup.
#sudo service salt-minion start

# This may be more reliable.
sudo salt-call state.highstate --local
