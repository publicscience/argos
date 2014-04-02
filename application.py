from argos.web import api, front

app = api.create_app()

# Run!
if __name__ == '__main__':
    app.run(host='0.0.0.0')
