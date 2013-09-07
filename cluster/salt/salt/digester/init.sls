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

# Start the Celery worker.
{% if 'worker' in grains.get('roles', []) %}
worker:
    cmd.run:
        - cwd: /var/app/digester/
        - name: ./dev-env/bin/celeryd --loglevel=info --config cluster.celery_config
        - require:
            - virtualenv: venv
            - cmd: app-nltk-data
{% endif %}

# Ensure RabbitMQ and MongoDB
# are installed and running.
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
     pkg:
        - installed
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