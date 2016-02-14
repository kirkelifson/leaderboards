__author__ = 'gnaughton'

from flask import render_template, url_for
from core import app
from core.models import db, DBTeam
from core.routes.defuseraccess import rank_momentum_senior, access_required
from flask_login import current_user

import random

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/team')
def team():
    team = DBTeam.query.order_by(DBTeam.priority).all()
    showlink = False
    if current_user is not None and current_user.is_authenticated and current_user.access >= rank_momentum_senior:
        showlink = True
    return render_template('team.html', team=team, asfile=False, showlink=showlink)

@app.route('/team/credits.txt')
@access_required(rank_momentum_senior)
def team_credits():
    team = DBTeam.query.order_by(DBTeam.priority).all()
    return render_template('team.html', team=team, asfile=True, time=(3 * db.session.query(DBTeam).count()) + 10)

def url_for_random_background():
    number = random.randint(1, 3)
    return url_for('static', filename='frontend/images/' 'bg-'+ str(number) +'.jpg')

app.jinja_env.globals.update(url_for_random_background=url_for_random_background)

def place_steamlink():
    return '<a href=\"http://steampowered.com\">Powered by Steam</a>'

app.jinja_env.globals.update(place_steamlink=place_steamlink)
