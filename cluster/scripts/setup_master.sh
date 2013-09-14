#!/bin/bash

# (Salt is already installed on the image)

# Enable Salt's firewall rules
sudo ufw allow salt

# Edit Master config to
# Accept all pending Minion keys
sudo sed -i 's/#auto_accept: False/auto_accept: True/' /etc/salt/master
# Enable fileserver at /srv/salt
# and enable pillar at /srv/pillar
# (looking for a nicer way of handling this...)
sudo sed -i '/#\(file\|pillar\)_roots:/ s/^#//' /etc/salt/master
sudo sed -i '/#\s\{2\}base:/ s/^#//' /etc/salt/master
sudo sed -i '/#\s\{4\}\-\s\/srv\/\(salt\|pillar\)/ s/^#//' /etc/salt/master

# Set the `role` grain for this instance to be 'master'.
echo -e 'roles:\n  - master' | sudo tee -a /etc/salt/grains
echo -e 'dbhost: $db_dns' | sudo tee -a /etc/salt/grains

# Restart Salt Master.
sudo service salt-master restart

# Provision as a masterless minion.
sudo salt-call state.highstate --local
