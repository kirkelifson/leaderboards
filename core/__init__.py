__author__ = 'gnaughton'

import os

from flask import Flask
from flask_mail import Mail

from core import config


app = Flask("leaderboards")
app.config['APP_PATH'] = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Secrets
app.config.from_envvar('SECRET_KEY')
app.config.from_envvar('STEAM_API_KEY')

app.config.from_object(config)

# 2 megabytes
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

mail = Mail(app)

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
import core.routes.api
import core.routes.defuseraccess
import core.routes.usersession
import core.routes.dashboard
import core.routes.leaderboards
import core.routes.contact
import core.routes.docs
import core.routes.errors
import core.routes.static
