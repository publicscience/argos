"""
Services
========

Access to external knowledge sources.
"""

import os
import glob
import inspect
import importlib

PACKAGE = __package__
SERVICES = globals()

for f in glob.glob(os.path.dirname(__file__)+"/*.py"):
    name = os.path.basename(f)[:-3]
    if name != '__init__':
        module = importlib.import_module("%s.%s" % (PACKAGE, name))
        for (k, v) in inspect.getmembers(module):
            if k.isupper():
                if isinstance(v, str):
                    SERVICES[k] = v.format(**globals())
                else:
                    SERVICES[k] = v

def process(profile, services):
    """
    Apply the specified services to the profile.

    E.g.
    services.process(profile, {
        'open_secrets': ['organizations'],
        'influence_explorer': ['recipients_for_organization']
    })

    The service name is its module name,
    so if there is the module `influence_explorer.py`,
    it's service name is `influence_explorer`.

    Each method for a service has the profile
    passed into it as a parameter.
    """
    # Set the profile's sources if there are none.
    if not profile.get('sources', None):
        profile['sources'] = []

    # For each of the specified services...
    for name, methods in services.items():
        service = SERVICES[name]

        # Call each of the specified methods
        # for this service, and update
        # the profile with its returned data.
        for method in methods:
            profile.update(getattr(service, method)(profile))

        # Update the sources.
        profile['sources'].append(name.replace('_', ' ').title())
