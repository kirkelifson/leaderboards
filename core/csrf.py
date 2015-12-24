__author__ = 'gnaughton'

import string
import random

from flask import request, abort, session

from core import app


@app.before_request
def csrf_protect():
    if request.method == 'POST':
        # Use below to generate new token with every post
        # token = session.pop('_csrf_token', None)
        token = session.get('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = ''.join([random.choice(string.letters+string.digits) for x in xrange(32)])
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token