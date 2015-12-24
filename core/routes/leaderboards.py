__author__ = 'gnaughton'
from flask import render_template, redirect, request, flash, url_for
from flask_login import login_user, logout_user
from sqlalchemy.exc import OperationalError

from valve.steam import id as steamid

from core import app
from core.models import db, DBScore


@app.route('/leaderboards')
@app.route('/leaderboards/<int:page>')
def leaderboards_main(page=1):
    stats_page = DBScore.query.order_by(DBScore.tick_time).paginate(page)
    #for score in stats_page.items:
        #score.steamid =
    return render_template('leaderboards/index.html', stats_page=stats_page)

@app.route('/postscore/<steamid>/<map>/<int:ticks>')
def post_score(ticks=0):
    try:
        score = DBScore(steamid, map, ticks, 0)
        db.session.add(score)
        db.session.commit()
    except OperationalError as e:
        print e
        return "{\"result\": \"False\"}"
    return "{\"result\": \"True\"}"