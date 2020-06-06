# -*- coding: utf-8 -*-
"""Create an application instance."""
import os
from flask.helpers import get_debug_flag

from wolfgang.app import create_app
# from wolfgang.settings import DockerDevConfig, LocalDevConfig, ProdConfig

if os.environ.get('FLASK_ENV') == 'docker':
    from wolfgang.settings import DockerDevConfig as CONFIG
elif get_debug_flag():
    from wolfgang.settings import LocalDevConfig as CONFIG
else:
    from wolfgang.settings import ProdConfig as CONFIG

print("Using config:")
print(CONFIG)

app = create_app(CONFIG)
