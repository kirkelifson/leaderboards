__author__ = 'rabsrincon'

from flask import render_template, flash, url_for, redirect
from core import app
from core.models import DBDoc, db

def is_valid_subject(subject):
    return str(subject) in global_subjects


@app.route('/docs', methods=['GET'])
@app.route('/docs/<subject>', methods=['GET'])
def docs(subject=None):
    entry = None
    docs = db.session.query(DBDoc).filter_by(is_deleted=False).all()
    # This will tell the page if we're in a doc page or not. Defaults to no
    is_doc = False
    if subject is not None:
        entry = DBDoc.query.filter_by(subject=subject).filter_by(is_deleted=False).first()
        if entry is None:
            flash('Nothing found with that subject.')
            redirect(url_for('docs'))
        else:
            is_doc = True    
    return render_template('docs.html', entry=entry, docs = docs, is_doc = is_doc, subject=subject)

        
    
    


