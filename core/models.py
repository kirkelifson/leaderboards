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
from flask import url_for
from core.routes.defuseraccess import rank_user_banned, rank_user_normal, rank_momentum_normal, rank_momentum_admin, rank_webmaster
from core.routes.sendemail import EmailConnection

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
    game_map = db.Column(VARCHAR(5000), nullable=False)
    stylized_mapname = db.Column(VARCHAR(5000), nullable=True)
    filepath = db.Column(VARCHAR(5000), nullable=False)
    thumbnail = db.Column(VARCHAR(5000), nullable=False, default='http://cdn.akamai.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg')
    gamemode = db.Column(INTEGER(unsigned=True))
    difficulty = db.Column(INTEGER(unsigned=True))
    layout = db.Column(INTEGER(unsigned=True))

    def __init__(self, game_map, stylized_mapname, filepath, thumbnail, gamemode, difficulty, layout):
        self.game_map = game_map
        self.stylized_mapname = stylized_mapname
        self.filepath = filepath
        self.thumbnail = thumbnail
        self.gamemode = gamemode
        self.difficulty = difficulty
        self.layout = layout

    @property
    def serialize(self):
        return {
            'id'         : self.id,
            'game_map'    : self.game_map,
            'stylized_mapname' : self.stylized_mapname,
            'filepath' : self.filepath,
            'thumbnail' : self.thumbnail,
            'gamemode'  : self.gamemode,
            'difficulty'  : self.difficulty,
            'layout'  : self.layout,
        }

    @staticmethod
    def get_id_for_game_map(game_map):
        map = DBMap.query.filter_by(game_map=game_map).first()
        if map is not None:
            return map.id
        else:
            return -1

    def __repr__(self):
        return '<Map %s>' % self.id
    
def get_map_thumbnail(mapfilename):
    try:
        map = DBMap.query.filter_by(game_map=mapfilename).first()
        if map is None or not map.thumbnail:
            return 'http://cdn.akamai.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
        else:
            return str(map.thumbnail)
    except:
        return 'http://cdn.akamai.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
    
app.jinja_env.globals.update(get_map_thumbnail=get_map_thumbnail)

def get_friendslist(steamid):
        options = {
            'key': app.config['STEAM_API_KEY'],
            'steamid': str(steamid),
            'relationship': 'friend'
        }
        url = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?%s' % urllib.urlencode(options)
        rv = json.load(urllib2.urlopen(url))
        return [trend['steamid'] for trend in rv['friendslist']['friends']] or {}

def get_steam_userinfo(steamid):
        options = {
            'key': app.config['STEAM_API_KEY'],
            'steamids': str(steamid)
        }
        url = 'http://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0001/?%s' % urllib.urlencode(options)
        rv = json.load(urllib2.urlopen(url))
        return rv['response']['players']['player'][0] or {}

def get_steamid_avatar(steamid):
    try:
        user = DBUser.query.filter_by(steamid=steamid).first()
        if user is None or user.avatar is None:
            info = get_steam_userinfo(steamid)
            if info is not None and info['avatar']:
                return info['avatar']
        else:
            return user.avatar
    except:
        return 'http://cdn.akamai.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'

def get_steamid_personaname(steamid):
    try:
        user = DBUser.query.filter_by(steamid=steamid).first()
        if user is None or user.username is None:
            info = get_steam_userinfo(steamid)
            if info is not None and info['personaname']:
                return info['personaname']
        else:
            return user.username
    except:
        return 'Unknown'

app.jinja_env.globals.update(get_steamid_avatar=get_steamid_avatar)
app.jinja_env.globals.update(get_steamid_personaname=get_steamid_personaname)


class DBScore(db.Model):
    __tablename__ = 'scores'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    steamid = db.Column(BIGINT(), nullable=False)
    mapid = db.Column(INTEGER(), nullable=False)
    tick_time = db.Column(INTEGER(unsigned=True), nullable=False)
    tick_rate = db.Column(INTEGER(unsigned=True), nullable=False)
    zone_hash = db.Column(VARCHAR(512))
    date = db.Column(DATETIME(), nullable=False)

    def __init__(self, steamid, mapid, tick_time, tick_rate, zone_hash):
        self.steamid = steamid
        self.mapid = mapid
        self.tick_time = tick_time
        self.tick_rate = tick_rate
        self.zone_hash = zone_hash
        self.date = time.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def serialize(self):
        return {
            'id'         : self.id,
            'steamid'    : self.steamid,
            'game_map'   : self.get_mapname,
            'tick_time'  : self.tick_time,
            'tick_rate'  : self.tick_rate,
            'zone_hash'  : self.zone_hash,
            'date'       : dump_datetime(self.date)
        }

    @property
    def serialize_many2many(self):
        return [ item.serialize for item in self.many2many]

    def get_mapname(self):
        map = DBMap.query.filter_by(id=self.mapid).first()
        if map is not None:
            return str(map.game_map)
        else:
            return 'Unknown'

    def __repr__(self):
        return '<Score %s>' % self.id


class DBUser(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    username = db.Column(VARCHAR(30), unique=False)
    email = db.Column(VARCHAR(255), unique=True)
    verified = db.Column(BOOLEAN(), default=False)
    access = db.Column(SMALLINT(unsigned=True), default=rank_user_normal)
    steamid = db.Column(BIGINT(unsigned=True), unique=True, nullable=False)
    avatar = db.Column(TEXT())
    token = db.Column(VARCHAR(32))
    joindate = db.Column(DATETIME())
    last_login = db.Column(DATETIME())
    last_modify = db.Column(DATETIME(), onupdate=func.utc_timestamp())

    def __init__(self, steamid, username=None, email=None, access=0):
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
        if rv is not None and rv.access >= rank_momentum_normal:
            rv.upgradeto_memberof_momentum()
        return rv

    def upgradeto_memberof_momentum(self):
        if self.access >= rank_momentum_normal:
            pre = DBTeam.query.filter_by(steamid=self.steamid).first()
            if pre is None:
                member = DBTeam(self.steamid, nickname=self.username, priority = rank_momentum_admin - self.access)
                db.session.add(member)
                db.session.commit()
            else:
                pre.user_rejoined()

    def upgradeto_memberof_momentum_access(self, access):
        if access >= rank_momentum_normal:
            pre = DBTeam.query.filter_by(steamid=self.steamid).first()
            if pre is None:
                member = DBTeam(self.steamid, nickname=self.username, priority = rank_momentum_admin - int(access))
                db.session.add(member)
                db.session.commit()
            else:
                pre.user_rejoined()
            

    def get_steam_userinfo(self): 
        return get_steam_userinfo(self.steamid) or {}

    def get_friendslist(self):
        return get_friendslist(self.steamid) or {}
    
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

    def update_handlenewemail(self, email):
        if email is not None:
            #Here goes a random token sent to the email to confirm it
            self.verified = False
            sep = ''
            self.token = sep.join([random.choice(saltset) for x in xrange(42)])
            self.email = email
            mailing = EmailConnection('sender','server','port','username','password')
            mailing.send(email,'Momentum Mod verify email','Please follow <a href=\"http://momentum-mod.org'+url_for('dashboard_settings_verifyemail',token=self.token)+'\">'+url_for('dashboard_settings_verifyemail',token=self.token)++'</a> to verify your email')
            db.session.commit()

    def update_verifyemail(self):
        self.verified=True
        self.token = None
        db.session.commit()

    def update_accesslevel(self, newaccess):
        if not self.access == newaccess:
            if newaccess < rank_user_banned:
                newaccess = rank_user_banned
            if newaccess < rank_webmaster:
                newaccess = rank_webmaster
            if self.access < rank_momentum_normal and newaccess >= rank_momentum_normal:
                self.upgradeto_memberof_momentum_access(newaccess)
            if self.access >= rank_momentum_normal and newaccess < rank_momentum_normal:
                member = DBTeam.query.filter_by(steamid=self.steamid).first()
                if member is not None:
                    member.user_teamleft()
            self.access = newaccess
            db.session.commit()

    def update_lastlogin(self):
        self.last_login = func.utc_timestamp()
        db.session.commit()

    def ban_user(self):
        update_accesslevel(rank_user_banned)
        
    def __repr__(self):
        return '<User %r>' % self.username
        

class DBTeam(db.Model):
    __tablename__ = 'team'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    steamid = db.Column(BIGINT(unsigned=True), unique=True, nullable=False)
    realname = db.Column(VARCHAR(255))
    nickname = db.Column(VARCHAR(255))
    role = db.Column(VARCHAR(255))
    priority = db.Column(TINYINT())
    left = db.Column(BOOLEAN(),default=False)

    def __init__(self, steamid, realname=None, nickname=None, role=None, priority=0):
        self.steamid = steamid
        self.realname = realname
        self.nickname = nickname
        self.role = role
        self.priority = priority

    def user_updateinfo(self, nickname, realname, role):
        self.nickname = nickname
        self.realname = realname
        self.role = role
        db.session.commit()

    def user_teamleft(self):
        self.left = True
        db.session.commit()

    def user_rejoined(self):
        self.left = False
        db.session.commit()

class DBContributor(db.Model):
    __tablename__ = 'contributors'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    role = db.Column(VARCHAR(255))
    special = db.Column(BOOLEAN(),default=False)

    def __init__(self, name, role=None, special=False):
        self.name = name
        self.role = role
        self.special = special

    def addmyself(self):
        db.session.add(self)
        db.session.commit()

class DBComment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    targetid = db.Column(INTEGER(unsigned=True), nullable=False)
    fromsteamid = db.Column(BIGINT(unsigned=True), unique=False, nullable=False)
    comment = db.Column(TEXT(),nullable=False)
    date = db.Column(DATETIME(),nullable=False)
    last_modify = db.Column(DATETIME(), onupdate=func.utc_timestamp())
    edited = db.Column(BOOLEAN(),default=False, nullable=False)
    isanswer = db.Column(BOOLEAN(),default=False, nullable=False)
    answerid = db.Column(INTEGER(unsigned=True), nullable=True, default=None)
    atsecond = db.Column(INTEGER(unsigned=True), default=None, nullable=True)

    def __init__(self, targetid, fromsteamid, comment, date=func.utc_timestamp(), atsecond=None):
        self.targetid = targetid
        self.fromsteamid = fromsteamid
        self.comment = comment
        self.date = date
        self.edited = False
        self.atsecond = atsecond

    def edit(self, newcomment, atsecond):
        self.comment = newcomment
        self.atsecond = atsecond
        db.session.commit()

        
