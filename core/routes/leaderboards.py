__author__ = 'gnaughton'
from flask import render_template, jsonify
from sqlalchemy.exc import OperationalError

from core import app
from core.models import db, DBScore, DBMap
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
        return "{\"result\": false}"
    return "{\"result\": true}"


@app.route('/getscores', methods=['GET'])
def get_scores():
    allscores = DBScore.query.order_by(DBScore.tick_time)
    return jsonify(json_list=[i.serialize for i in allscores.all()])

@app.route('/getscores/<map>/<tickrate>/<steamid>', methods=['GET'])
def get_scores_filtered(map, tickrate, steamid):
    user_scores = DBScore.query.filter_by(steamid=steamid).filter_by(game_map=map).first()
    if user_scores is None:
        data = DBScore.query.filter_by(game_map=map).order_by(DBScore.tick_time).paginate(1, 10)
    else:
        start = user_scores.id - 5
        while start < 0:
            start += 1
        data = DBScore.query.filter_by(game_map=map).offset(start).limit(10).all()
    return jsonify(json_list=[i.serialize for i in data])
@app.route('/getfriendscores/<map>/<steamid>', methods=['GET'])
def get_scores_friends(map, steamid):
    content = urllib2.urlopen('http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key=' + app.config['STEAM_API_KEY'] + '&steamid=' + steamid +'&relationship=friend').read()
    work = json.loads(content)
    idlist = [trend['steamid'] for trend in work['friendslist']['friends']]
    data = DBScore.query.filter_by(game_map=map).filter(DBScore.steamid.in_(idlist)).all()
    return jsonify(json_list=[i.serialize for i in data])

@app.route('/mapinfo/<map>/<gamemode>/<difficulty>/<layout>',  methods=['GET'])
def map_info_getter(map, gamemode, difficulty, layout):
	map_results = DBMap.query.filter(DBMap.map_fullname.like('%' + map + '%'))
	if gamemode > 0:
		map_results.filter_by(gamemode=gamemode)
	if difficulty > 0:
		map_results.filter_by(difficulty=difficulty)
	if layout > 0:
		map_results.filter_by(layout=layout)

	return jsonify(json_list=[i.serialize for i in map_results])

def get_total_runs():
    return db.session.query(DBScore).count()

app.jinja_env.globals.update(get_total_runs=get_total_runs)
