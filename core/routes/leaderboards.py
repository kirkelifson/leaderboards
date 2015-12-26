__author__ = 'gnaughton'
from flask import render_template, jsonify
from sqlalchemy.exc import OperationalError

from core import app
from core.models import db, DBScore
import urllib2
import json
import datetime


@app.route('/leaderboards')
@app.route('/leaderboards/<int:page>')
def leaderboards_main(page=1):
    stats_page = DBScore.query.order_by(DBScore.tick_time).paginate(page)

    time_convert = {'66': 0.015, '100': 0.01}
    for stat in stats_page.items:
        content = urllib2.urlopen('http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=' +
                                  app.config['STEAM_API_KEY'] + '&steamids=' + stat.steamid).read()
        work = json.loads(content)
        stat.timeconverted = float(stat.tick_time) * time_convert[str(stat.tick_rate)]
        stat.timeconverted = str(datetime.timedelta(seconds=stat.timeconverted))
        if "." in stat.timeconverted:
            stat.timeconverted = stat.timeconverted[:-4]
        stat.steamid = work["response"]["players"][0]["personaname"]
        stat.avatar = work["response"]["players"][0]["avatar"]
    return render_template('leaderboards/index.html', stats_page=stats_page)


@app.route('/postscore/<steamid>/<map>/<int:ticks>/<int:tickrate>', methods=['GET'])
def post_score(steamid, map, ticks, tickrate):
    try:
        # takes 64-bit steamid
        score = DBScore(steamid, map, ticks, tickrate, 0)
        db.session.add(score)
        db.session.commit()
    except OperationalError as e:
        print e
        return "{\"result\": \"False\"}"
    return "{\"result\": \"True\"}"


@app.route('/getscores', methods=['GET'])
def get_scores():
    allscores = DBScore.query.order_by(DBScore.tick_time)
    return jsonify(json_list=[i.serialize for i in allscores.all()])
