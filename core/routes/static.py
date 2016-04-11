__author__ = 'tuxxi'

from flask import render_template, redirect, flash, url_for
from core import app
from core.models import DBDoc, db

@app.route('/about')
def about():
	return redirect(url_for('team'))

@app.route('/install')
def install():
	entry = ''
	try:
		entry = DBDoc.query.filter_by(subject="installing").first()
	except:
		pass
	return render_template('install.html', entry=entry)    