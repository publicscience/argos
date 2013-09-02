include:
    - deploy

# Ensure necessary packages are installed.
app-pkgs:
    pkg.installed:
        - names:
            - git
            - python3.3
            - python3-pip

# Ensure virtualenv-3.3 is installed.
pip-pkgs:
    pip.installed:
        - names:
            - virtualenv
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
app-venv:
    cmd.run:
        - cwd: /var/app/digester/
        - name: /var/app/digester/do setup worker
        - require:
            - pkg: app-pkgs
            - pip: pip-pkgs
            - git: digester

# Having some issues with installing Python 3.3 requirements...
# Temporarily disabled; the custom setup script in the repository
# seems to do the job.
#app-venv:
    #virtualenv.managed:
        #- name: /var/app/digester/dev-env
        #- venv_bin: virtualenv-3.3
        #- python: /usr/bin/python3.3
        #- requirements: /var/app/digester/requirements.txt
        #- no_site_packages: true
        #- clear: false
        #- require:
            #- pkg: app-pkgs
            #- pip: pip-pkgs
            #- git: digester