#!/bin/bash

echo 'deb http://www.rabbitmq.com/debian testing main' | sudo tee -a /etc/apt/sources.list
wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
sudo apt-key add rabbitmq-signing-key-public.asc
rm rabbitmq-signing-key-public.asc

sudo apt-get update -y

#sudo apt-get install rabbitmq-server -y --force-yes
