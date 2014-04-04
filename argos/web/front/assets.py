from flask.ext.assets import Environment, Bundle

assets = Environment()

css = Bundle('css/index.sass', filters='sass', depends='css/**/*.sass', output='css/index.css')
assets.register('css_all', css)
