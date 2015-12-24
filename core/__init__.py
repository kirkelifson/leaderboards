__author__ = 'gnaughton'

import os

from flask import Flask

from core import config


app = Flask("leaderboards")
app.config['APP_PATH'] = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

app.config.from_object(config)

# 2 megabytes
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

#from util.form.form import render_control

# this is how you could make a function globally available in views
# app.jinja_env.globals.update(render_control=render_control)

# this is how you could add a filter to be globally available in views
# app.jinja_env.filters['formatElapsedTime'] = formatElapsedTime
# login manager
import core.login
import core.csrf

# to add new routes just import them here
import core.routes.main
#import core.routes.dashboard
import core.routes.leaderboards