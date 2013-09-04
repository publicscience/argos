# Start the Celery worker.
app-worker:
    cmd.run:
        - cwd: /var/app/digester/
        - name: /var/app/digester/do worker
        - require:
            - cmd: app-nltk-data
