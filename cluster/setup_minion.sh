#!/bin/bash

# Install Salt
sudo add-apt-repository ppa:saltstack/salt -y
sudo apt-get update -y
sudo apt-get install salt-minion -y
sudo apt-get install salt-master -y
sudo apt-get upgrade -y

# Set Salt Master location and start Minion
sed -i 's/#master: salt/master: $salt_master/' /etc/salt/minion
salt-minion -d

