#!/bin/bash

# Install Salt
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:saltstack/salt -y
sudo apt-get update -y
sudo apt-get install salt-minion -y
sudo apt-get install salt-master -y
sudo apt-get upgrade -y

# Enable fileserver at /srv/salt
# and enable pillar at /srv/pillar
# This is necessary to run a masterless minion.
sudo sed -i '/#\(file\|pillar\)_roots:/ s/^#//' /etc/salt/minion
sudo sed -i '/#\s\{2\}base:/ s/^#//' /etc/salt/minion
sudo sed -i '/#\s\{4\}\-\s\/srv\/\(salt\|pillar\)/ s/^#//' /etc/salt/minion

# Provision as a masterless minion.
sudo salt-call state.highstate --local
