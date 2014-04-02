from argos.web import api, front

# Run!
if __name__ == '__main__':
    app = api.create_app()
    app.run(host='0.0.0.0')
