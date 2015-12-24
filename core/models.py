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


class DBScore(db.Model):
    __tablename__ = 'products'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    steamid = db.Column(VARCHAR(512), nullable=False)
    game_map = db.Column(VARCHAR(5000))
    time = db.Column(INTEGER(unsigned=True))
    zone_hash = db.Column(VARCHAR(512))
    date = db.Column(INTEGER(unsigned=True))

    def __init__(self, steamid, game_map, time, zone_hash):
        self.steamid = steamid
        self.game_map = game_map
        self.time = time
        self.zone_hash = zone_hash
        self.date = int(round(time.time() * 1000))

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
