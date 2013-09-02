include:
    - deploy

app-pkgs:
    pkg.installed:
        - names:
            - git
            - python3.3
            - python3-pip

pip-pkgs:
    pip.installed:
        - names:
            - virtualenv
        - bin_env: pip-3.3
        - require:
            - pkg: app-pkgs

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

app-venv:
    virtualenv.managed:
        - name: /var/app/env
        - venv_bin: virtualenv-3.3
        - python: /usr/bin/python3.3
        - requirements: /var/app/digester/requirements.txt
        - no_site_packages: true
        - clear: false
        - require:
            - pkg: app-pkgs
            - pkg: pip-pkgs