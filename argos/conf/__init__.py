import os
import inspect
import importlib

PACKAGE = __package__

def load_conf_module(name, key=None):
  """ Load a module and its values into globals. """

  if key:
    namespace = globals().setdefault(key.upper(), {})
  else:
    namespace = globals()

  module = importlib.import_module("%s.%s" % (PACKAGE, name))

  for (k, v) in inspect.getmembers(module):
    if k.isupper():
      if isinstance(v, str):
        namespace[k] = v.format(**globals())
      else:
        namespace[k] = v

"""
File names for configuration files.

Configuration files should be of the format:

  #{NAME}.py
"""

NAMES = [
  'celery',
  'app',
  'security'
]

for n in NAMES:
  load_conf_module(n, key=n)
