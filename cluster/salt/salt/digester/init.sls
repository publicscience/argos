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
        - name: /var/app/digester/do setup nltk
        - require:
            - virtualenv: venv

{% if 'worker' in grains.get('roles', []) %}
# Start the Celery worker.
worker:
    cmd.run:
        - cwd: /var/app/digester/
        - name: ./dev-env/bin/celeryd --loglevel=info --config cluster.celery_config --logfile /var/log/celery.log
        - require:
            - virtualenv: venv
            - cmd: app-nltk-data
            - file: worker
            - file: db-config
            - file: mail-config
    file.sed:
        - name: /var/app/digester/cluster/celery_config.py
        - before: 'localhost'
        - after: {{ grains.get('master') }}
        - backup: ''
        - flags: 'g'
        - require:
            - git: digester

# Setup db to point to proper host.
db-config:
    file.sed:
        - name: /var/app/digester/config.py
        - before: 'localhost'
        - after: {{ grains.get('master') }}
        - backup: ''
        - flags: 'g'
        - require:
            - file: app-config
        - watch:
            - file: /var/app/digester/config.py

salt-minion:
    service.running:
        - enable: True
        - reload: True
        - require:
            - pkg: salt-minion
    pkg:
        - installed
{% endif %}

{% if 'master' in grains.get('roles', []) %}
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

mongodb:
    service.running:
        - enable: True
        - require:
            - pkg: mongodb
    pkg.installed:
        - name: mongodb-10gen
        - require:
            - cmd: mongodb
    cmd.script:
        - source: salt://scripts/install-mongodb.sh

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
# Move app's cluster config-sample.ini to config.ini.
cluster-config:
    file.managed:
        - name: /var/app/digester/cluster/config.ini
        - source: /var/app/digester/cluster/config-sample.ini
        - require:
            - git: digester

# Setup mail server login.
mail-config:
    file.sed
        - name: /var/app/digester/cluster/config.ini
        - before: 'your-pass'
        - after: {{ grains.get('mail_pass') }}
        - backup: ''
        - flags: 'g'
        - require:
            - file: app-config
        - watch:
            - file: /var/app/digester/cluster/config.ini

# Move app's config-sample.py to config.py.
app-config:
    file.managed:
        - name: /var/app/digester/config.py
        - source: /var/app/digester/config-sample.py
        - require:
            - git: digester
{% endif }


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