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
        stats_page = DBScore.query.filter_by(id=DBMap.get_id_for_game_map(map)).order_by(DBScore.tick_time * DBScore.tick_rate).paginate(page)
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
                stats_page = stats_page.filter_by(id=DBMap.get_id_for_game_map(map))
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
                stats_page = stats_page.filter_by(id=DBMap.get_id_for_game_map(map))
            stats_page = stats_page.order_by(DBScore.tick_time * DBScore.tick_rate).order_by(DBScore.mapid).paginate(page)
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


