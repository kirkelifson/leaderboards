__author__ = 'rabsrincon'

from flask import render_template, redirect, request, flash, url_for, jsonify
from core.models import DBEmailingList, db, DBContact
from flask.ext.wtf import Form, RecaptchaField
from wtforms import TextField, TextAreaField, SelectField, SubmitField
from wtforms.validators import InputRequired, Email, Optional
from flask_login import current_user
from urlparse import urljoin
from urllib import urlencode
import urllib2 as urlrequest

import json
import string
import random

from core import app

class ContactForm(Form):
    name = TextField("Name", validators=[InputRequired("Please enter your name.")])
    email = TextField("Email", validators=[InputRequired("Please enter your email."), Email("Email must be valid")])
    department = SelectField("Department to forward this message", choices=[('gen', 'General'), ('pro', 'Programmers'), ('map', 'Mappers'), ('web', 'WebMasters')], validators=[Optional()])
    subject = TextField("Subject", validators=[Optional()])
    message = TextAreaField("Message", validators=[InputRequired("Message can not be empty")])
    recaptcha = RecaptchaField()
    submit = SubmitField("Send")

class MailListForm(Form):
    email = email = TextField("Email", validators=[InputRequired("Please enter your email."), Email("Email must be valid")])
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
        success = False
        if form.validate() == False:
            flash('Errors on the form. Fix them and try submititng again')
        else:
            department_convert = {'gen': '<@channel>', 'pro': '<#C053U99PL|coders>', 'map':'<#C054J6L49|mappers>', 'web':'<#C0540H60C> & <#C054N9BDH>'}
            msg = "Message"
            try:
                contact = DBContact(form.email.data.encode('utf-8'), form.name.data.encode('utf-8'), form.department.data.encode('utf-8'), form.subject.data.encode('utf-8'), form.message.data.encode('utf-8'), request.remote_addr)
                db.session.add(contact)
                db.session.commit()
                userid = ''
                if current_user.get_id() is not None and current_user.is_authenticated:
                    userid = '\n(Is logged in as <http://steamcommunity.com/profiles/'+ str(current_user.steamid) +'|' + str(current_user.steamid) +'>'
                    if current_user.email is not None:
                        userid += ' Registered email: '+ current_user.email
                        if not current_user.verified:
                            userid += ' - Not verified'
                    userid += ')'
                msg =  "Message *#"+ str(contact.id) +"*\nNew message from *" + str(form.name.data.encode('utf-8')) + "* (" + str(form.email.data.encode('utf-8')) + ") directed to " + department_convert.get(str(form.department.data.encode('utf-8')), "@channel") + str(userid) + "\nSubject: " + str(form.subject.data.encode('utf-8')) + "\n\n" + str(form.message.data.encode('utf-8'))
                
                slack = Slack(url=app.config["SLACK_CONTACTBOT_URL"])
                response = slack.notify(text=msg)
                if response == 'ok':
                    flash('Message sent.' + str(form.name.data.encode('utf-8')) + ', we\'ll get back to you shortly.')
                    success = True
                else:
                    flash('Contact API failed. Try again later')
                    success = False
            except:
                flash('An error ocurred while processing the message. Ensure the message is valid')
                success = False        
        return render_template('contact.html', form = form, success = success)
            
    else:
        deps = ['gen','pro','map','web']
        depart = request.args.get('department')
        if not depart is None and depart.encode('utf-8') in deps:
            form.department.data = depart.encode('utf-8')
        if not request.args.get('subject') is None:
            form.subject.data = request.args.get('subject').encode('utf-8')
        if current_user is not None and current_user.is_authenticated:
            if current_user.email:
                form.email.data = current_user.email
            form.name.data = current_user.username
        return render_template('contact.html', form=form)



@app.route('/webhooks/incoming/contact', methods=['POST'])
def contact_slackhook():
    response = { 'text':'', 'channel':'#contact' }
    try:
        if request.form.get('token') == app.config["SLACK_CONTACTBOT_TOKEN"]: 
            commands = ['selfassign', 'setresolved', 'getinfo', 'help', 'listunresolved' ]
            commands_help = { 'selfassign': 'Assigns the given case to you.', 'setresolved': 'Marks the given case as resolved', 'getinfo': 'Gets the info from a given entry ID', 'help': 'Shows this help message', 'listunresolved': 'Lists unresolved entries'}
            tips_help = ['Add parameter _global_ at *the end* of a command and the bot will post the answer on the channel instead of PM\'ing it to you. _Example: !contactbot: help global_']
            messaged = request.form.get('text')
            message = messaged.replace("%21","!").replace("+"," ").replace("%3A",":").strip()
            if message:
                command = message.split(' ')[1]
                if command in commands:
                    if command == commands[0]:
                        contactid = message.split(' ')[2]
                        entry = DBContact.query.filter_by(id=contactid).first()
                        if entry is not None:
                            entry.is_assigned = True
                            entry.user = request.form.get('user_name')
                            db.session.commit()
                            response['text'] = 'Case *#' + str(contactid) + '* assigned to ' + str(request.form.get('user_name')) + '.'
                        else:
                            response['text'] = 'Couldn\'t find a case with ID #'+ str(contactid) + '.'
                    elif command == commands[1]:
                        contactid = message.split(' ')[2]
                        entry = DBContact.query.filter_by(id=contactid).first()
                        if entry is not None:
                            entry.is_resolved = True
                            db.session.commit()
                            response['text'] = 'Case *#' + str(contactid) + '* marked as solved.'
                        else:
                            response['text'] = 'Couldn\'t find a case with ID #'+ str(contactid) + '.'
                    elif command == commands[2]:
                        contactid = message.split(' ')[2]
                        entry = DBContact.query.filter_by(id=contactid).first()
                        if entry is not None:
                            info = 'Case *#' + str(contactid) + '* :\nSender\'s name: _' + entry.name + '_\nSender\'s email: _' + entry.email +'_\nSender\'s IP: ' + entry.ip + '\nDepartment code: _' + entry.department + '_\nSubject: _' + entry.subject + '_\n'
                            if entry.is_assigned:
                                info = info + 'Assigned to: _' + entry.user + '_.'
                            else:
                                info = info + 'Not assigned to anyone yet.'
                            info = info + '\n'
                            if entry.is_resolved:
                                info = info + '*Resolved*.'
                            else:
                                info = info + '*Not* resolved yet.'
                            response['text'] = info
                        else:
                            response['text'] = 'Couldn\'t find a case with ID #' + str(contactid) + '.'
                    elif command == commands[3]:
                        info = 'Available commands are:\n'
                        for com in commands:
                            info = info + str(com) + ' (_' + str(commands_help[com]) + '_)\n'
                        info = info + '\n *TIPS* \n'
                        for tip in tips_help:
                            info = info + '·' + str(tip) + '\n'
                        response['text'] = info
                    elif command == commands[4]:
                        entries = DBContact.query.filter_by(is_resolved=False).all()
                        info = 'Unresolved cases are:\n'
                        for entry in entries:
                            info = info + '*# ' + str(entry.id) +'* - _' + str(entry.subject) +'_\n'
                        response['text'] = info
                    else:
                        response['text'] = 'Unknown command \"'+ str(command) + '\".'
                    if str(message.split(' ')[-1]) != "global":
                        response['channel'] = '@' + request.form.get('user_name')
                else:
                    response['text'] = 'Unknown command \"'+ str(command) + '\".'
            else:
                response['text'] = 'Request had missisng argument text.' 
    except:
        response['text'] = 'Internal server error (Probably your command was not formated correctly). Let @rabsrincon know about it.'
    slack = Slack(url=app.config["SLACK_CONTACTBOT_URL"])
    response = slack.notify(text=response['text'],channel=response['channel'])
    if response == 'ok':
        return "",200
    else:
        response['text'] = '*WebHook failed to deliver message using the default method. Fallback used.*\n\n' + response['text']
        return jsonify(response), 200

@app.route('/mailinglist', methods=['GET', 'POST'])
def mailinglist():
    try:
        if request.method == 'GET':
            form = MailListForm()
            return render_template('mailinglist.html', form=form)
        else:
            success = False
            uform = MailListForm()
            uform.email.data = request.form.get('email')
            if uform.validate():
                prev = DBEmailingList.query.filter_by(email= uform.email.data).first()
                if prev is None:
                    delete_token = ''
                    confirmation_token = ''
                    saltset = string.letters + string.digits
                    sep = ''
                    confirmation_token = sep.join([random.choice(saltset) for x in xrange(64)])
                    delete_token = sep.join([random.choice(saltset) for x in xrange(64)])
                    prev = DBEmailingList(uform.email.data, confirmation_token, delete_token)
                    ## We need to send the confirmation email here!   
                    db.session.add(prev)
                    db.session.commit()
                    flash('Thank you for joining us! A confirmation email has been sent.')
                    success = True
                elif prev.is_deleted:
                    prev.update_confirmed()
                    flash('Your email has been resubmitted to the mailing list. Thank you.')
                    success = True
                else:
                    flash('Email already registered')
            else:
                flash('Check for errors, form could not be validated.')
            return render_template('mailinglist.html', form = uform, success = success)
                    
    except:
        flash('There was a problem with your request. Please check your data')
        raise
        return render_template('mailinglist.html', form=None)

@app.route('/mailinglist/token/<token>', methods=['GET'])
def mailinglist_token(token=None):
    try:
        success = False
        if token is not None:
            #Is this a confirmation link?
            uconfirm = DBEmailingList.query.filter_by(confirm_token=token).first()
            if uconfirm is not None:
                #It is a confirmation email
                uconfirm.update_confirmed()
                flash('Your email has been confirmed. Thank you')
                success = True
            else:
                ucancel = DBEmailingList.query.filter_by(delete_token=token).first()
                #Is it a delete email?
                if ucancel is not None:
                    #It is a delete email
                    ucancel.update_deleted()
                    flash('Your email has been removed from the active mailing list.\n If you want to rejoin, please revisit your confirmation link or resubmit your email.')
                    success = True
                else:
                    #It's not a valid token
                    flash('Token is not valid. Please check the validity of the link')
                    success = False
        else:
            flash('Received null token.')
        return render_template('mailinglist_token.html', success = success)
    except:
        flash('There was a problem processing your token.')
        raise
        return redirect(url_for('mailinglist'))
        
        
