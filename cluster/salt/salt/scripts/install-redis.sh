#!/bin/bash

# Install and compile latest.
wget -O /tmp/redis-stable.tar.gz http://download.redis.io/redis-stable.tar.gz
tar xvzf /tmp/redis-stable.tar.gz -C /tmp/
cd /tmp/redis-stable
make
make install

# Cleanup.
cd ..
rm -rf /tmp/redis-stable
rm /tmp/redis-stable.tar.gz

# Create user.
useradd redis
