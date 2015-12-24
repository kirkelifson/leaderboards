__author__ = 'gnaughton'

from flask import render_template, redirect, request, flash, url_for
from flask_login import login_user

from core import app
from core.models import DBUser


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/store')
def storefront():
    return render_template('store.html')

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

@app.route('/dashboard/')
def dashboard():
    return render_template('dashboard/index.html')