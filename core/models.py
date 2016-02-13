__author__ = 'gnaughton'

import hashlib
import random
import string
import time
import urllib2, urllib
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import *
from sqlalchemy.sql import func
from core import app
from flask.ext.login import UserMixin
from core.routes.defuseraccess import lvl_newuser_noverified, lvl_min_userof_momentumteam, lvl_userof_momentumteam_admin, lvl_user_banned

saltset = string.letters + string.digits
db = SQLAlchemy(app)

def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]

class DBMap(db.Model):
    __tablename__ = 'maps'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    map_filename = db.Column(VARCHAR(128))
    map_fullname = db.Column(VARCHAR(5000))
    gamemode = db.Column(INTEGER(unsigned=True))
    difficulty = db.Column(INTEGER(unsigned=True))
    layout = db.Column(INTEGER(unsigned=True))

    def __init__(self, map_filename, map_fullname, gamemode, difficulty, layout):
        self.map_filename = map_filename
        self.map_fullname = map_fullname
        self.gamemode = gamemode
        self.difficulty = difficulty
        self.layout = layout

    @property
    def serialize(self):
        return {
            'id'         : self.id,
            'map_fullname'    : self.map_fullname,
            'map_filename'   : self.map_filename,
            'gamemode'  : self.gamemode,
            'difficulty'  : self.difficulty,
            'layout'  : self.layout,
        }

    @staticmethod
    def get_map_thumbnail(mapfilename):
        url = 'http://cdn.momentum-mod.org/maps/' + str(mapfilename) + '/' + mapfilename + '.jpg'
        if str(urllib.urlopen(url).getcode()) == str(200):
            return url
        else:
            return 'http://cdn.momentum-mod.org/maps/default_thumbnail.jpg'

    def __repr__(self):
        return '<Map %s>' % self.id
    
def get_map_thumbnail(mapfilename):
    return DBMap.get_map_thumbnail(mapfilename)
app.jinja_env.globals.update(get_map_thumbnail=get_map_thumbnail)


class DBScore(db.Model):
    __tablename__ = 'scores'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    steamid = db.Column(BIGINT(), nullable=False)
    game_map = db.Column(VARCHAR(5000), nullable=False)
    tick_time = db.Column(INTEGER(unsigned=True), nullable=False)
    tick_rate = db.Column(INTEGER(unsigned=True), nullable=False)
    zone_hash = db.Column(VARCHAR(512))
    date = db.Column(DATETIME(), nullable=False)
    lastmodify = db.Column(DATETIME(), onupdate=func.utc_timestamp())
    timesupdated = db.Column(INTEGER(unsigned=True),default=1)

    def __init__(self, steamid, game_map, tick_time, tick_rate, zone_hash):
        self.steamid = steamid
        self.game_map = game_map
        self.tick_time = tick_time
        self.tick_rate = tick_rate
        self.zone_hash = zone_hash
        self.date = time.strftime('%Y-%m-%d %H:%M:%S')

    def update_runtime(self, newtickrate, newticktime):
        self.tick_rate = newtickrate
        self.tick_time = newticktime
        self.timesupdated = self.timesupdated + 1
        self.date = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()

    @property
    def serialize(self):
        return {
            'id'         : self.id,
            'steamid'    : self.steamid,
            'game_map'   : self.game_map,
            'tick_time'  : self.tick_time,
            'tick_rate'  : self.tick_rate,
            'zone_hash'  : self.zone_hash,
            'date'       : dump_datetime(self.date)
        }

    @property
    def serialize_many2many(self):
        return [ item.serialize for item in self.many2many]

    def __repr__(self):
        return '<Score %s>' % self.id


class DBUser(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    username = db.Column(VARCHAR(30), unique=False)
    email = db.Column(VARCHAR(255), unique=True)
    access = db.Column(SMALLINT(unsigned=True), default=lvl_newuser_noverified())
    steamid = db.Column(BIGINT(unsigned=True), unique=True, nullable=False)
    avatar = db.Column(TEXT())
    token = db.Column(VARCHAR(32))
    joindate = db.Column(DATETIME())
    last_login = db.Column(DATETIME())
    last_modify = db.Column(DATETIME(), onupdate=func.utc_timestamp())

    def __init__(self, steamid, username=None, email=None, access=0, hash=True, token=None):
        self.steamid = steamid
        self.username = username
        self.email = email
        self.access = access
        self.joindate = func.utc_timestamp()

    def get_id(self):
        return unicode(self.id)

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return hasattr(self, 'id')

    def is_active(self):
        return hasattr(self, 'id')

    def get_steamid(self):
        return(self.steamid)

    @staticmethod
    def get_or_create(steamid,access):
        rv = DBUser.query.filter_by(steamid=steamid).first()
        if rv is None:
            newuser = get_steam_userinfo(steamid)
            rv = DBUser(steamid, username=newuser["personaname"], access=access)
            db.session.add(rv)
            db.session.commit()
        if rv is not None and rv.access >=lvl_min_userof_momentumteam() and DBTeam.query.filter_by(steamid=rv.steamid).first() is None:
            rv.upgradeto_memberof_momentum()
        return rv

    def upgradeto_memberof_momentum(self):
        if self.access >= lvl_min_userof_momentumteam():
            pre = DBTeam.query.filter_by(steamid=self.steamid).first()
            if pre is None:
                member = DBTeam(self.steamid, nickname=self.username, priority = lvl_userof_momentumteam_admin() - self.access)
                db.session.add(member)
                db.session.commit()

    def get_steam_userinfo(self):
        options = {
            'key': app.config['STEAM_API_KEY'],
            'steamids': self.steamid
        }
        url = 'http://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0001/?%s' % urllib.urlencode(options)
        rv = json.load(urllib2.urlopen(url))
        return rv['response']['players']['player'][0] or {}  
    
    def update_steam_userinfo(self, userinfo):
        if userinfo is None:
            return False
        changes = False
        if not self.username == userinfo['personaname'] and userinfo['personaname'] is not None:
            self.username = userinfo['personaname']
            changes = True
        if not self.avatar == userinfo['avatar'] and userinfo['avatar'] is not None:
            self.avatar = userinfo['avatar']
            changes = True
        if changes == True:
            db.session.commit()
        return changes

    def update_verifiedemail(self):
        if self.access == lvl_newuser_noverified():
            self.access = lvl_newuser_verified()
            db.session.commit()
            flash('Your email ' + str(self.email) + ' has been verified')
        else:
            flash('Email already verified')

    def update_accesslevel(self, newaccess):
        if self.access == newaccess:
            return
        if newaccess > lvl_userof_momentumteam_admin():
            newaccess = lvl_userof_momentumteam_admin()
        if newaccess < lvl_user_banned():
            newaccess = lvl_user_banned()
        if self.access < lvl_min_userof_momentumteam() and newaccess >= lvl_min_userof_momentumteam:
            member = DBTeam(self.steamid, nickname=self.username, priority = lvl_userof_momentumteam_admin() - newaccess)
            db.session.add(member)
        if self.access >= lvl_min_userof_momentumteam() and newaccess < lvl_min_userof_momentumteam:
            db.session.delete(DBTeam.query.filter_by(steamid=self.steamid).first())
        self.access = newaccess
        db.session.commit()

    def update_lastlogin(self):
        self.last_login = func.utc_timestamp()
        db.session.commit()

    def ban_user(self):
        update_accesslevel(lvl_user_banned())
        
    def __repr__(self):
        return '<User %r>' % self.username

def get_steam_userinfo(steamid):
        options = {
            'key': app.config['STEAM_API_KEY'],
            'steamids': steamid
        }
        url = 'http://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0001/?%s' % urllib.urlencode(options)
        rv = json.load(urllib2.urlopen(url))
        return rv['response']['players']['player'][0] or {}
def get_steamid_avatar(steamid):
    try:
        user = DBUser.query.filter_by(steamid=steamid).first()
        if user is not None and user.avatar is not None:
            return user.avatar
        else:
            info = get_steam_userinfo(steamid)
            if info is not None and info.avatar is not None:
                return info.avatar
        #Default Steam '?' avatar
        return 'http://cdn.akamai.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
    except:
        return 'http://cdn.akamai.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
def get_steamid_personaname(steamid):
    try:
        user = DBUser.query.filter_by(steamid=steamid).first()
        if user is not None:
            return user.username
        else:
            info = get_steam_userinfo(steamid)
            if info is not None and info.personaname is not None:
                return info.personaname
        return 'Unknown'
    except:
        return 'Unknown'

app.jinja_env.globals.update(get_steamid_avatar=get_steamid_avatar)
app.jinja_env.globals.update(get_steamid_personaname=get_steamid_personaname)
        

class DBTeam(db.Model):
    __tablename__ = 'team'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    steamid = db.Column(BIGINT(unsigned=True), unique=True, nullable=False)
    realname = db.Column(VARCHAR(255))
    nickname = db.Column(VARCHAR(255))
    role = db.Column(VARCHAR(255))
    priority = db.Column(TINYINT())

    def __init__(self, steamid, realname=None, nickname=None, role=None, priority=0):
        self.steamid = steamid
        self.realname = realname
        self.nickname = nickname
        self.role = role
        self.priority = priority

