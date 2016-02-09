__author__ = 'rabsrincon'

from flask import render_template, redirect, request, flash, url_for, jsonify
from flask.ext.wtf import Form, RecaptchaField
from wtforms import TextField, TextAreaField, SelectField, SubmitField
from wtforms.validators import InputRequired, Email, Optional

from urlparse import urljoin
from urllib import urlencode
import urllib2 as urlrequest

import json

from core import app

class ContactForm(Form):
    name = TextField("Name", validators=[InputRequired("Please enter your name.")])
    email = TextField("Email", validators=[InputRequired("Please enter your email."), Email("Email must be valid")])
    department = SelectField("Department to forward this message", choices=[('gen', 'General'), ('pro', 'Programmers'), ('map', 'Mappers'), ('web', 'WebMasters')], validators=[Optional()])
    subject = TextField("Subject", validators=[Optional()])
    message = TextAreaField("Message", validators=[InputRequired("Message can not be empty")])
    recaptcha = RecaptchaField()
    submit = SubmitField("Send")

# https://github.com/satoshi03/slack-python-webhook (MIT license ftw)
class Slack():

    def __init__(self, url=""):
        self.url = url
        self.opener = urlrequest.build_opener(urlrequest.HTTPHandler())

    def notify(self, **kwargs):
        """
        Send message to slack API
        """
        return self.send(kwargs)

    def send(self, payload):
        """
        Send payload to slack API
        """
        payload_json = json.dumps(payload)
        data = urlencode({"payload": payload_json})
        req = urlrequest.Request(self.url)
        response = self.opener.open(req, data.encode('utf-8')).read()
        return response.decode('utf-8')    

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('Errors on the form. Fix them and try submititng again')
            return render_template('contact.html', form=form, success=False)
        else:
            department_convert = {'gen': '<@channel>', 'pro': '<#C053U99PL>', 'map':'<#C054J6L49>', 'web':'<#C0540H60C> & <#C054N9BDH>'}
            msg = "Message"
            try:
                msg =  "New message from *" + str(form.name.data.encode('utf-8')) + "* (" + str(form.email.data.encode('utf-8')) + ") directed to " + department_convert.get(str(form.department.data.encode('utf-8')), "@channel") +"\nSubject: " + str(form.subject.data.encode('utf-8')) + "\n\n" + str(form.message.data.encode('utf-8'))
            except:
                flash('An error ocurred while processing the message. Ensure the message is valid')
                return render_template('contact.html', form=form, success=False)
            slack = Slack(url=app.config["SLACK_CONTACTBOT_URL"])
            response = slack.notify(text=msg)
            if response == 'ok':
                return render_template('contact.html', success=True, sender_name=form.name.data)
            else:
                flash('Contact API failed. Try again later')
                return render_template('contact.html', form=form, success=False)
    else:
        deps = ['gen','pro','map','web']
        depart = request.args.get('department')
        if not depart is None and depart.encode('utf-8') in deps:
            form.department.data = depart.encode('utf-8')
        if not request.args.get('subject') is None:
            form.subject.data = request.args.get('subject').encode('utf-8')
        return render_template('contact.html', form=form)
