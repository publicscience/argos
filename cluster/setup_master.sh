#!/bin/bash

# Add Salt, RabbitMQ, and MongoDB APT repos.
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:saltstack/salt -y
echo 'deb http://www.rabbitmq.com/debian testing main' | sudo tee -a /etc/apt/sources.list
wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
sudo apt-key add rabbitmq-signing-key-public.asc
rm rabbitmq-signing-key-public.asc
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list
sudo apt-get update -y

# Install Salt, RabbitMQ, MongoDB, and git.
sudo apt-get install salt-master -y
sudo apt-get install rabbitmq-server -y --force-yes
sudo apt-get install mongodb-10gen -y
sudo apt-get install git -y

sudo apt-get upgrade -y

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
sudo sed -i '/#\s\{4\}\-\s\/srv\/(\salt\|pillar\)/ s/^#//' /etc/salt/master

# Start Salt, RabbitMQ, and MongoDB
sudo service mongodb start
sudo service salt-master start
sudo rabbitmq-server
