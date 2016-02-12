__author__ = 'gnaughton'

from flask import render_template, url_for
from core import app
from core.models import db, DBTeam

import random

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/team')
def team():
    team = DBTeam.query.order_by(DBTeam.priority).all()
    return render_template('team.html', team=team)

def url_for_random_background():
    number = random.randint(1, 3)
    return url_for('static', filename='frontend/images/' 'bg-'+ str(number) +'.jpg')

app.jinja_env.globals.update(url_for_random_background=url_for_random_background)

def place_steamlink():
    return '<a href=\"http://steampowered.com\">Powered by Steam</a>'

app.jinja_env.globals.update(place_steamlink=place_steamlink)
