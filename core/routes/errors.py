__author__ = 'rabsrincon'

#Super simple error management, I was tried of the plain default error page!

from flask import render_template
from core import app

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(500)
def page_not_found(e):
    messages = {404:"We lost something", 403:"You shall not pass", 500:"Something went horribly wrong"}
    return render_template('errors.html', error = e, msg = messages[e.code]), e.code

