__author__ = 'gnaughton'

import hashlib
import random
import string
import time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import *
from core import app
from flask.ext.login import UserMixin

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

    def __repr__(self):
        return '<Map %s>' % self.id

class DBScore(db.Model):
    __tablename__ = 'scores'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    steamid = db.Column(VARCHAR(512), nullable=False)
    game_map = db.Column(VARCHAR(5000))
    tick_time = db.Column(INTEGER(unsigned=True))
    tick_rate = db.Column(INTEGER(unsigned=True))
    zone_hash = db.Column(VARCHAR(512))
    date = db.Column(DATETIME())

    def __init__(self, steamid, game_map, tick_time, tick_rate, zone_hash):
        self.steamid = steamid
        self.game_map = game_map
        self.tick_time = tick_time
        self.tick_rate = tick_rate
        self.zone_hash = zone_hash
        self.date = time.strftime('%Y-%m-%d %H:%M:%S')

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
    username = db.Column(VARCHAR(30), unique=True)
    email = db.Column(VARCHAR(255), unique=True)
    access = db.Column(SMALLINT(unsigned=True))
    password = db.Column(BINARY(20))
    salt = db.Column(VARCHAR(10))
    account = db.Column(VARCHAR(34))
    token = db.Column(VARCHAR(32))
    joindate = db.Column(DATETIME())

    def __init__(self, username, email, password, salt=None, access=0, hash=True, account=None, token=None):
        self.username = username
        self.email = email
        self.salt = salt if salt is not None else ''.join([random.choice(saltset) for x in xrange(6)])

        if not hash:
            self.password = password
        else:
            m = hashlib.sha1()
            m.update(self.salt + password)
            self.password = m.digest()

        self.access = access
        self.joindate = time.strftime('%Y-%m-%d %H:%M:%S')

    def check_password(self, password):
        m = hashlib.sha1()
        m.update(self.salt + password)
        return m.digest() == self.password

    def change_password(self, password, newsalt=True):
        if newsalt:
            self.salt = ''.join([random.choice(saltset) for x in xrange(6)])
        m = hashlib.sha1()
        m.update(self.salt + password)
        self.password = m.digest()
        return

    def get_id(self):
        return unicode(self.id)

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return hasattr(self, 'id')

    def is_active(self):
        return hasattr(self, 'id')

    def __repr__(self):
        return '<User %r>' % self.username
