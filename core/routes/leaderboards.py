__author__ = 'gnaughton'
from flask import render_template, jsonify, flash, redirect, url_for
from sqlalchemy.exc import OperationalError
from flask_login import login_required, current_user

from core import app
from core.models import db, DBScore, DBMap, DBUser, get_steam_userinfo, get_friendslist
import urllib2
import json
import datetime

time_convert = {'66': 0.015, '100': 0.01}

@app.route('/leaderboards')
@app.route('/leaderboards/<int:page>')
def leaderboards_main(page=1):  
    stats_page = DBScore.query.order_by(DBScore.tick_time * DBScore.tick_rate).paginate(page)
    for stat in stats_page.items:
        try:
            stat.timeconverted = float(stat.tick_time) * time_convert[str(stat.tick_rate)]
            stat.timeconverted = str(datetime.timedelta(seconds=stat.timeconverted))
            if "." in stat.timeconverted:
                stat.timeconverted = stat.timeconverted[:-4]
        except:
            print 'Exception caught on leaderboards main page while trying to query it.'
            continue
    return render_template('leaderboards/index.html', stats_page=stats_page, qtype='general')  

@app.route('/leaderboards/<map>')
@app.route('/leaderboards/<map>/<int:page>')
def leaderboards_map(map,page=1):
    if map:
        stats_page = DBScore.query.filter_by(game_map=map).order_by(DBScore.tick_time * DBScore.tick_rate).paginate(page)
        if stats_page is not None:
            for stat in stats_page.items:
                try:
                    stat.timeconverted = float(stat.tick_time) * time_convert[str(stat.tick_rate)]
                    stat.timeconverted = str(datetime.timedelta(seconds=stat.timeconverted))
                    if "." in stat.timeconverted:
                        stat.timeconverted = stat.timeconverted[:-4]
                except:
                    print 'Exception caught on leaderboards main page while trying to query it.'
                    continue
            return render_template('leaderboards/index.html', stats_page=stats_page, map=map, qtype='map')
        else:
            flash('No runs recorded for ' + str(map))
            return redirect(url_for('leaderboards_main', page=page))
    else:
        flash('An error ocurred when trying to access runs for ' + str(map))
        return redirect(url_for('leaderboards_main', page=page))

@app.route('/leaderboards/p/<steamid>/<map>/<int:page>')
@app.route('/leaderboards/p/<steamid>/<map>')
@app.route('/leaderboards/p/<steamid>/<int:page>')
@app.route('/leaderboards/p/<steamid>')
def leaderboards_player(steamid,map=None,page=1):
    try:
        info = get_steam_userinfo(steamid)
        if info is not None:
            stats_page = DBScore.query.filter_by(steamid=steamid)
            if map is not None:
                stats_page = stats_page.filter_by(game_map=map)
            stats_page = stats_page.order_by(DBScore.tick_time * DBScore.tick_rate).paginate(page)
            if stats_page is not None:
                for stat in stats_page.items:
                    try:
                        stat.timeconverted = float(stat.tick_time) * time_convert[str(stat.tick_rate)]
                        stat.timeconverted = str(datetime.timedelta(seconds=stat.timeconverted))
                        if "." in stat.timeconverted:
                            stat.timeconverted = stat.timeconverted[:-4]
                    except:
                        print 'Exception caught on leaderboards main page while trying to query it.'
                        continue
                return render_template('leaderboards/index.html', stats_page=stats_page, pinfo=info,map=map, qtype='player')
            else:
                flash('No runs recorded for ' + str(steamid))
                return redirect(url_for('leaderboards_main'))
        else:
            flash('Wrong steamid')
            return redirect(url_for('leaderboards_main'))
    except:
        flash('An error ocurred when trying to access runs for ' + str(steamid))
        return redirect(url_for('leaderboards_main'))

@app.route('/leaderboards/myfriendsruns')
@app.route('/leaderboards/myfriendsruns/<int:page>')
@app.route('/leaderboards/myfriendsruns/<map>')
@app.route('/leaderboards/myfriendsruns/<map>/<int:page>')
@login_required
def leaderboars_me_friendsruns(map=None, page=1,):
    try:
        idlist = current_user.get_friendslist()
        if idlist is not None:
            stats_page = DBScore.query.filter(DBScore.steamid.in_(idlist))
            if map is not None:
                stats_page = stats_page.filter_by(game_map=map)
            stats_page = stats_page.order_by(DBScore.tick_time * DBScore.tick_rate).order_by(DBScore.game_map).paginate(page)
            if stats_page is not None:
                for stat in stats_page.items:
                    try:
                        stat.timeconverted = float(stat.tick_time) * time_convert[str(stat.tick_rate)]
                        stat.timeconverted = str(datetime.timedelta(seconds=stat.timeconverted))
                        if "." in stat.timeconverted:
                            stat.timeconverted = stat.timeconverted[:-4]
                    except:
                        print 'Exception caught on leaderboards main page while trying to query it.'
                        continue
                return render_template('leaderboards/index.html', stats_page=stats_page, map=map, qtype='myfriends')
            else:
                flash('No runs friend runs recorded')
                return redirect(url_for('leaderboards_main'))
        else:
            flash('You need some friends first :)')
            return redirect(url_for('leaderboards_main'))
    except:
        flash('An error ocurred when trying to access runs for ' + str(current_user.steamid))
        return redirect(url_for('leaderboards_main'))

    
@app.route('/postscore/<steamid>/<map>/<int:ticks>/<int:tickrate>', methods=['GET'])
def post_score(steamid, map, ticks, tickrate):
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
            personalbest = DBScore.query.filter_by(steamid=steamid).filter_by(game_map=map).order_by(DBScore.tick_time * DBScore.tick_rate).first()
            if personalbest is not None:
                if personalbest.tick_time * personalbest.tick_rate > tickrate * ticks: 
                    response['message'] = '#MOM_WebMsg_RunSaved_NewPB'
                else:
                    response['message'] = '#MOM_WebMsg_RunSaved'
                response['PBdiff'] = float((time_convert[str(tickrate)] * ticks) - (personalbest.tick_time * time_convert[str(personalbest.tick_rate)]))
            else:
                response['message'] = '#MOM_WebMsg_FirstRunSaved'
                response['PBdiff'] = None
            score = DBScore(steamid, map, ticks, tickrate, 0)
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

@app.route('/getfriendscores/<steamid>/<map>', methods=['GET'])
@app.route('/getfriendscores/<steamid>', methods=['GET'])
def get_scores_friends(steamid, map=None):
    idlist = get_friendslist(steamid)
    data = DBScore.query.filter(DBScore.steamid.in_(idlist))
    if map is not None:
        data = data.filter_by(game_map=map).order_by(DBScore.game_map)
    data = data.order_by(DBScore.tick_time * DBScore.tick_rate).all()
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
