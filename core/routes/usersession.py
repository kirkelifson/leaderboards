__author__ = 'gnaughton'

from flask import render_template, redirect, request, flash, url_for
from flask_login import login_user, logout_user, login_required, current_user
from flask.ext.wtf import Form, RecaptchaField
from wtforms import TextField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email
from flask.ext.openid import OpenID
from sqlalchemy.sql import func
from core.routes.defuseraccess import lvl_newuser_noverified

from core import app
from core.models import DBUser

import re

import urllib2, urllib

_steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')

oid = OpenID(app)

def next_is_valid(next):
    return next in ['dashboard_r_home','index','leaderboards_main']
        
def choose_next(userdesired, fallback):
    if userdesired is not None and next_is_valid(userdesired):
        return url_for(userdesired)
    else:
        return url_for(fallback)

@app.route('/login', methods=['GET'])
@oid.loginhandler
def login():
    if current_user.get_id() is not None and current_user.is_authenticated:
        desired = choose_next(request.args.get('next'),'index')
        return redirect(desired)
    else:
        return oid.try_login('http://steamcommunity.com/openid')


@oid.after_login
def create_or_login(resp):
    match = _steam_id_re.search(resp.identity_url)
    current_user = DBUser.get_or_create(match.group(1),lvl_newuser_noverified())
    steamdata = current_user.get_steam_userinfo()
    current_user.update_steam_userinfo(steamdata)
    current_user.update_lastlogin()
    login_user(current_user)
    flash('You are logged in as %s' % current_user.username, category='login')
    desired = choose_next(request.args.get('next'),'index')
    return redirect(desired)

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))



    

