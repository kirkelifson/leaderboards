__author__ = 'gnaughton'
from flask import render_template, jsonify
from sqlalchemy.exc import OperationalError

from core import app
from core.models import db, DBScore, DBMap, DBUser
import urllib2
import json
import datetime

time_convert = {'66': 0.015, '100': 0.01}

@app.route('/leaderboards')
@app.route('/leaderboards/<int:page>')
def leaderboards_main(page=1):  
    stats_page = DBScore.query.order_by(DBScore.tick_time).paginate(page)
    for stat in stats_page.items:
        if str(stat.tick_rate) not in time_convert:
            print "Run #ID " + str(stat.id) + " had invalid tick_rate(" + str(stat.tick_rate) + "). Set to 66"
            faulty = DBScore.query.filter_by(id=stat.id).first()
            if faulty is not None:
                faulty.tick_rate = '66'
                db.session.commit()
            stat.tick_rate = '66'
        content = urllib2.urlopen('http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=' +
                                  app.config['STEAM_API_KEY'] + '&steamids=' + str(stat.steamid)).read()
        work = json.loads(content)
        stat.timeconverted = float(stat.tick_time) * time_convert[str(stat.tick_rate)]
        stat.timeconverted = str(datetime.timedelta(seconds=stat.timeconverted))
        if "." in stat.timeconverted:
            stat.timeconverted = stat.timeconverted[:-4]
        stat.steamid = work["response"]["players"][0]["steamid"]
        stat.avatar = work["response"]["players"][0]["avatar"]        
    return render_template('leaderboards/index.html', stats_page=stats_page)


@app.route('/postscore/<steamid>/<map>/<int:ticks>/<int:tickrate>', methods=['GET'])
def post_score(steamid, map, ticks, tickrate):
    if str(tickrate) not in time_convert:
        #In case someone tries to submit an invalid tick_rate.
        #Todo: Dehardcode?
        tickrate = '66'
    response = {'result': 'true', 'status': None, 'message': None}
    try:
        # takes 64-bit steamid
        previous = DBScore.query.filter_by(steamid=steamid).filter_by(game_map=map).filter_by(tick_rate=tickrate).first()
        if previous is None:
            score = DBScore(steamid, map, ticks, tickrate, 0)
            db.session.add(score)
            response['status'] = 'submitted'
            db.session.commit()
        else:
            if previous.tick_time >= ticks:
                previous.update_runtime(tickrate, ticks)
                response['status'] = 'updated'
            else:
                response['status'] = 'slower'
                response['message'] = '#MOM_WebMsg_RunIsSlowerThanStored'
        user = DBUser.query.filter_by(steamid=steamid).first()   
        if user is None:
            response['message'] = '#MOM_WebMsg_NeedsFirstLogin'
    except OperationalError as e:
        print e
        response['result'] = 'false'
        response['status'] = 'error'
        response['message'] = '#MOM_WebMsg_RunNotSaved_InternalServerErrors'
    return jsonify(json_list=[response])


@app.route('/getscores', methods=['GET'])
def get_scores():
    allscores = DBScore.query.order_by(DBScore.tick_time)
    return jsonify(json_list=[i.serialize for i in allscores.all()])

@app.route('/getscores/<map>', methods=['GET'])
def get_scores_map(map):
    user_scores = DBScore.query.filter_by(game_map=map).order_by(DBScore.tick_time)
    return jsonify(json_list=[i.serialize for i in user_scores.all()])

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
    data = DBScore.query.filter_by(game_map=map).filter(DBScore.steamid.in_(idlist)).order_by(DBScore.tick_time).all()
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
    totals = db.session.query(DBScore).all()
    return .count()

app.jinja_env.globals.update(get_total_runs=get_total_runs)
