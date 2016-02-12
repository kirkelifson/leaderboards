__author__ = 'rabsrincon'

from flask import render_template, flash, url_for
from core import app

global_subjects = ['mapping', 'maps-entities']

def is_valid_subject(subject):
    return str(subject) in global_subjects

@app.route('/docs', methods=['GET'])
@app.route('/docs/<subject>', methods=['GET'])
def docs(subject=None):
    if not is_valid_subject(subject):
        subject = None
    return render_template('docs.html', subject=subject)

        
    
    


