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

# Run custom setup script instead
# of Salt's virtualenv setup (below).
#app-venv:
    #cmd.run:
        #- cwd: /var/app/digester/
        #- name: /var/app/digester/do setup venv
        #- require:
            #- pkg: app-pkgs
            #- pip: pip-pkgs
            #- git: digester
            #- pkg: lxml-deps
            #- pkg: mwlib-deps

app-nltk-data:
    cmd.run:
        - cwd: /var/app/digester/
        - name: /var/app/digester/do setup nltk
        - require:
            #- cmd: app-venv
            - virtualenv: app-venv

# Setup the virtualenv.
# Having a lot of issues with this.
# For now, using custom setup script.
app-venv:
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