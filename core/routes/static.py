__author__ = 'tuxxi'

from flask import render_template, redirect
from core import app

@app.route('/about')
def about():    
	return render_template('about.html')
@app.route('/install')
def install():    
	return render_template('install.html')