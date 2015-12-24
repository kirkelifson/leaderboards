__author__ = 'gnaughton'
from flask import render_template, redirect, request, flash, url_for
from flask_login import login_user, logout_user

from core import app
from core.models import DBUser


@app.route('/dashboard/')
def dashboard():
    return render_template('dashboard/index.html')