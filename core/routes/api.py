__author__ = 'rabsrincon'
from flask import render_template, jsonify, flash, redirect, url_for
from sqlalchemy.exc import OperationalError
from flask_login import login_required, current_user

from core import app
from core.models import db, DBScore, DBMap, DBUser, get_steam_userinfo, get_friendslist
import urllib2
import json
import datetime

time_convert = {'66': 0.015, '100': 0.01}
    
@app.route('/postscore/<steamid>/<map>/<int:ticks>/<int:tickrate>', methods=['GET'])
def api_post_score(steamid, map, ticks, tickrate):
    response = {}
    if str(tickrate) not in time_convert:
        response['result'] = False
        response['status'] = 'error'
        response['message'] = '#MOM_WebMsg_RunNotSaved_WrongTickrate'
        response['PBdiff'] = None
        return jsonify(json_list=[response])
    else:
        try:
            # takes 64-bit steamid
            mapid = DBMap.get_id_for_game_map(map)
            if mapid == -1:
                response['result'] = False
                response['status'] = 'MissingMap'
                response['message'] = '#MOM_WebMsg_RunNotSaved_MapNotFound'
                response['PBdiff'] = None
                return jsonify(json_list=[response])
            personalbest = DBScore.query.filter_by(steamid=steamid).filter_by(mapid=mapid).order_by(DBScore.tick_time * DBScore.tick_rate).first()
            if personalbest is not None:
                if personalbest.tick_time * personalbest.tick_rate > tickrate * ticks: 
                    response['message'] = '#MOM_WebMsg_RunSaved_NewPB'
                else:
                    response['message'] = '#MOM_WebMsg_RunSaved'
                response['PBdiff'] = float((time_convert[str(tickrate)] * ticks) - (personalbest.tick_time * time_convert[str(personalbest.tick_rate)]))
            else:
                response['message'] = '#MOM_WebMsg_FirstRunSaved'
                response['PBdiff'] = None
            score = DBScore(steamid, mapid, ticks, tickrate, 0)
            db.session.add(score)
            db.session.commit()  
            response['result'] = True
            response['status'] = 'submitted'
        except OperationalError as e:
            response['result'] = False
            response['status'] = 'error'
            response['message'] = '#MOM_WebMsg_RunNotSaved_InternalServerErrors'
            response['PBdiff'] = None
        return jsonify(json_list=[response])


@app.route('/getscores', methods=['GET'])
def api_get_scores():
    allscores = DBScore.query.order_by(DBScore.tick_time * DBScore.tick_rate)
    return jsonify(json_list=[i.serialize for i in allscores.all()])

@app.route('/getscores/<map>', methods=['GET'])
def api_get_scores_map(map):
    user_scores = DBScore.query.filter_by(game_map=map).order_by(DBScore.tick_time)
    return jsonify(json_list=[i.serialize for i in user_scores.all()])


### THIS ONE NEEDS TO BE RETHOUGHT. I'M TOO DUMB TO KNOW WHAT IT EVEN WANTS TO RETURN AND HOW ###
@app.route('/getscores/<map>/<tickrate>/<steamid>', methods=['GET'])
def api_get_scores_filtered(map, tickrate, steamid):
## OLD VERSION
##     user_scores = DBScore.query.filter_by(steamid=steamid).filter_by(game_map=map).first()
##     if user_scores is None:
##         data = DBScore.query.filter_by(game_map=map).order_by(DBScore.tick_time).paginate(1, 10)
##     else:
##         start = user_scores.id - 5
##         while start < 0:
##             start += 1
##         data = DBScore.query.filter_by(game_map=map).offset(start).limit(10).all()
##     return jsonify(json_list=[i.serialize for i in data])
    response = {}
    response['result'] = False
    response['message'] = 'Needs to be implemented'
    # We even retuenr a 501 code.
    return jsonify(response), 501
## ""NEW VERSION""
##    scores = DBScore.query
##    data = None
##    if map:
##        scores = scores.filter_by(mapid=DBMap.get_id_for_game_map(map))
##    if tickrate and tickrate in time_convert:
##        scores = scores.filter_by(tick_rate=tickrate)
##    if steamid:
##        scores = scores.filter_by(steamid=steamid)
##    if scores.first() is None:
##        data = DBScore.query.filter_by(mapid=DBMap.get_id_for_game_map(map)).order_by(DBScore.tick_time * DBScore.tick_rate).paginate(1, 10)
##    else:
##        start = scores.first().id - 5
##        while start < 0:
##            start += 1
##        data = DBScore.query.filter_by(mapid=DBMap.get_id_for_game_map(map)).offset(start).limit(10).all()   
##    return jsonify(json_list=[i.serialize for i in data])

@app.route('/getfriendscores/<steamid>/<map>', methods=['GET'])
@app.route('/getfriendscores/<steamid>', methods=['GET'])
def api_get_scores_friends(steamid, map=None):
    idlist = get_friendslist(steamid)
    data = DBScore.query.filter(DBScore.steamid.in_(idlist))
    if map is not None:
        data = data.filter_by(game_map=map).order_by(DBScore.game_map)
    data = data.order_by(DBScore.tick_time * DBScore.tick_rate).all()
    return jsonify(json_list=[i.serialize for i in data])

@app.route('/mapinfo/<map>/<gamemode>/<difficulty>/<layout>',  methods=['GET'])
def api_map_info_getter(map, gamemode, difficulty, layout):
        map_results = DBMap.query.filter(DBMap.game_map.like('%' + map + '%'))
	if gamemode > 0:
		map_results.filter_by(gamemode=gamemode)
	if difficulty > 0:
		map_results.filter_by(difficulty=difficulty)
	if layout > 0:
		map_results.filter_by(layout=layout)

	return jsonify(json_list=[i.serialize for i in map_results])

@app.route('/getmapinfo/<map>')
def api_getmapinfo(map):
    response = {}
    if map:
        try:
            mapinfo = DBMap.query.filter_by(game_map=map).first()
            if mapinfo is not None:
                response['result'] = True
                response['status'] = 'success'
                response['mapinfo'] = mapinfo.serialize
            else:
                response['result'] = False
                response['status'] = 'MissingMap'            
        except:
            response['result'] = False
            response['status'] = 'QueryError'
    else:
        response['result'] = False
        response['status'] = 'NullMap'
    return jsonify(json_list=[response])

def get_total_runs():
    return db.session.query(DBScore).count()

app.jinja_env.globals.update(get_total_runs=get_total_runs)
