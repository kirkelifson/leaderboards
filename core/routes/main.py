__author__ = 'gnaughton'

from flask import render_template, redirect, request, flash, url_for
from flask_login import login_user, logout_user

from core import app
from core.models import DBUser

import random

@app.route('/')
def index():
    return render_template('index.html')

def url_for_random_background():
    number = random.randint(1, 3)
    return url_for('static', filename='frontend/images/' 'bg-'+ str(number) +'.jpg')

app.jinja_env.globals.update(url_for_random_background=url_for_random_background)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    dbuser = DBUser.query.filter_by(username=username).first()

    if dbuser is None or not dbuser.check_password(password):
        flash('Username or password is invalid', 'danger')
        return redirect(url_for('login'))
    login_user(dbuser)
    flash('Logged in successfully', 'success')
    return redirect(request.args.get('next') or url_for('dashboard'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))

