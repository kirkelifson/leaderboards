__author__ = 'gnaughton'
from flask import render_template, redirect, request, flash, url_for, abort
from flask_login import login_user, logout_user, current_user

from core import app
from core.models import DBUser, DBTeam
from core.routes.defuseraccess import lvl_min_userof_momentumteam

dashboard_destinations = ['home','manage']

def is_valid_destination(destination):
    return destination in dashboard_destinations

@app.route('/dashboard/<destination>')
def dashboard(destination = 'home'):
    if current_user.get_id() is not None and current_user.is_authenticated:
        if not is_valid_destination(destination):
            destination = 'home'
        return render_template('dashboard/index.html', destination=destination)
    else:
        flash('You can\'t access here without login in first')
        return redirect(url_for('login', next='dashboard_r_home'))
@app.route('/dashboard')
@app.route('/dashboard/')
def dashboard_r_home():
    return redirect(url_for('dashboard',destination='home'))

@app.route('/dashboard/manage')
def dashboard_manage():
    if current_user.get_id() is not None and current_user.is_authenticated and current_user.access >= lvl_min_userof_momentumteam():
        return render_template('dashboard/manage.html',destination='manage')
    else:
        flash('Authorized personnel only.', category='login')
        return redirect(url_for('login', next='dashboard_r_home'))

@app.route('/dashboard/home')
def dashboard_home():
    if current_user.get_id() is not None and current_user.is_authenticated:
        return render_template('dashboard/home.html',destination='home')
    else:
        flash('You need to log in before being able to acces that resource.', category='login')
        return redirect(url_for('login', next='dashboard_r_home'))

def momteam_pending():
    if current_user.get_id() is not None and current_user.is_authenticated and current_user.access >= lvl_min_userof_momentumteam():
        member = DBTeam.query.filter_by(steamid=current_user.steamid).first()
        if member is not None:
            if member.realname is None or member.role is None:
                return True
            else:
                return False
        else:
            return False
    else:
        return False
app.jinja_env.globals.update(momteam_pending=momteam_pending)
