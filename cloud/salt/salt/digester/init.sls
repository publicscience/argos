include:
    - deploy

# Ensure necessary packages are installed.
app-pkgs:
    pkg.installed:
        - names:
            - git
            - python3.3
            - python3-pip
            - unzip
            # For getting latest python-dateutil.
            - bzr

# Required by lxml.
lxml-deps:
    pkg.installed:
        - names:
            - libxml2-dev
            - libxslt1-dev
            - python-dev
            - lib32z1-dev

# Required by mwlib.
mwlib-deps:
    pkg.installed:
        - names:
            - libevent-dev
            - re2c

# Ensure virtualenv-3.3 is installed.
pip-pkgs:
    pip.installed:
        - names:
            - virtualenv
            - cython
        - bin_env: pip-3.3
        - require:
            - pkg: app-pkgs

# Grab latest version from Github.
digester:
    git.latest:
        - name: {{ pillar['git_repo'] }}
        - rev: {{ pillar['git_rev'] }}
        - target: /var/app/digester/
        - force: true
        - require:
            - pkg: app-pkgs
            - file: deploykey
            - file: publickey
            - file: ssh_config

# Download NLTK data.
app-nltk-data:
    cmd.run:
        - cwd: /var/app/digester/
        - name: /var/app/digester/do nltk
        - require:
            - virtualenv: venv

{% if 'worker' in grains.get('roles', []) %}
# Start the Celery worker.
worker:
    cmd.run:
        - cwd: /var/app/digester/
        - name: ./dev-env/bin/celeryd --loglevel=info --config=cluster.celery_config --logfile=/var/log/celery.log
        - require:
            - virtualenv: venv
            - cmd: app-nltk-data
            - file: db-config
            - file: cluster-config
            - file: app-config
            - file: mq-config

mq-config:
    file.sed:
        - name: /var/app/digester/cluster/celery_config.py
        - before: 'localhost'
        - after: {{ grains.get('mqhost') }}
        - backup: ''
        - flags: 'g'
        - require:
            - git: digester
            - file: celery-config

# Setup db to point to proper host.
db-config:
    file.sed:
        - name: /var/app/digester/config.py
        - before: 'localhost'
        - after: {{ grains.get('dbhost') }}
        - backup: ''
        - flags: 'g'
        - require:
            - file: app-config

salt-minion:
    service.running:
        - enable: True
        - reload: True
        - require:
            - pkg: salt-minion
    pkg:
        - installed
{% endif %}

{% if 'database' in grains.get('roles', []) %}
postgresql:
    service.running:
        - enable: True
        - require:
            - pkg: postgresql
    pkg.installed:
        - name: postgresql
        - require:
            - cmd: postgresql
    cmd.script:
        - source: salt://scripts/install-database.sh
{% endif %}

{% if 'broker' in grains.get('roles', []) %}
rabbitmq-server:
    service.running:
        - enable: True
        - require:
            - pkg: rabbitmq-server
    pkg.installed:
        - require:
            - cmd: rabbitmq-server
    cmd.script:
        - source: salt://scripts/install-rabbitmq.sh

redis-server:
    service.running:
        - enable: True
        - require:
            - file: redis-server
            - file: redis-config
    file.managed:
        - name: /etc/init/redis-server.conf
        - source: salt://deploy/redis-server.conf
        - require:
            - cmd: redis-server
    cmd.script:
        - source: salt://scripts/install-redis.sh

redis-config:
    file.managed:
        - name: /etc/redis/redis.conf
        - makedirs: True
        - source: salt://deploy/redis.conf
{% endif %}

{% if 'master' in grains.get('roles', []) %}
# Setup db to point to proper host.
db-config:
    file.sed:
        - name: /var/app/digester/config.py
        - before: 'localhost'
        - after: {{ grains.get('dbhost') }}
        - backup: ''
        - flags: 'g'
        - require:
            - file: app-config

mq-config:
    file.sed:
        - name: /var/app/digester/cluster/celery_config.py
        - before: 'localhost'
        - after: {{ grains.get('mqhost') }}
        - backup: ''
        - flags: 'g'
        - require:
            - git: digester
            - file: celery-config

salt-master:
    service.running:
        - enable: True
        - require:
            - pkg: salt-master
    pkg:
        - installed
{% endif %}

# The following is run on any non-image instance.
# (since the image does not have any roles set)
{% if grains.get('roles', []) %}
# Copy over the cluster config.
cluster-config:
    file.managed:
        - name: /var/app/digester/cluster/config.ini
        - source: salt://deploy/config.ini
        - require:
            - git: digester

# Copy over the app config.
app-config:
    file.managed:
        - name: /var/app/digester/config.py
        - source: salt://deploy/config.py
        - require:
            - git: digester

# Copy over the Celery config.
celery-config:
    file.managed:
        - name: /var/app/digester/cluster/celery_config.py
        - source: salt://deploy/celery_config.py
        - require:
            - git: digester
{% endif %}


# Setup the virtualenv.
# Having a lot of issues with this.
# For now, using custom setup script.
venv:
    virtualenv.managed:
        - name: /var/app/digester/dev-env
        - cwd: /var/app/digester/
        - venv_bin: virtualenv-3.3
        - requirements: /var/app/digester/requirements.txt
        - no_site_packages: true
        - require:
            - pkg: app-pkgs
            - pip: pip-pkgs
            - git: digester
            - pkg: lxml-deps
            - pkg: mwlib-deps