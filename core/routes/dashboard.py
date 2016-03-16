__author__ = 'gnaughton'
from flask import render_template, redirect, request, flash, url_for, abort
from flask_login import login_user, logout_user, current_user, login_required

from core import app
from core.models import DBUser, DBTeam, DBContributor, DBMap, db, DBDoc, DBEmailingList
from core.routes.defuseraccess import rank_user_banned, rank_momentum_normal, rank_momentum_admin, rank_webmaster, access_required, rank_momentum_senior, mapper_required
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, Email, Optional

from urllib import quote_plus

import os
import requests
import re
import string
import json

class ManageForm(Form):
    steamid = TextField("SteamID")
    nickname = TextField("Nickname")
    realname = TextField("Real name")
    role = TextField("Role", validators=[InputRequired("Your role can not be empty")])
    submit = SubmitField("Update info")

class ContributorForm(Form):
    name = TextField("Name", validators=[InputRequired("Name can not be empty")])
    type = TextField("Role")
    special = BooleanField("Is special thanks?")
    submit = SubmitField("Add contributor")

class SettingsForm(Form):
    email = TextField("Email", validators=[InputRequired("Enter a valid email"), Email("Email must be valid")])
    submit = SubmitField("Update info")

class UserlistForm(Form):
    steamid = TextField("Steamid", validators=[InputRequired("Steamid can not be empty")])
    username = 'Username'
    access = TextField("Access", validators=[InputRequired("Access level can not be empty")])
    translator = BooleanField("Is translator?")
    email = 'Email'
    mapper = BooleanField("Is mapper?")
    joindate = 'JoinDate'
    submit = SubmitField("Update user")

class MapsForm(Form):
    mapname = TextField("Map name", validators=[InputRequired("Map name can not be empty")])
    filepath = TextField("File path", validators=[InputRequired("File path can not be empty")])
    thumbnail = TextField("Thumbnail path", validators=[InputRequired("Thumbnail path can not be empty")])
    difficulty = TextField("Map tier", validators=[InputRequired("Difficulty can not be none")])
    submit = SubmitField("Submit map")

class DocsForm(Form):
    title = TextField("Title", validators=[InputRequired("Title can not be empty")])
    text = TextAreaField("Text", validators=[InputRequired("Documentation text can not be empty")])
    subject = TextField("Subject", validators=[InputRequired("Subject can not be empty")])
    is_hidden = BooleanField("Is hidden?")
    submit = SubmitField("Submit doc")
    
dashboard_destinations = ['home','manage','settings','manageuserslist','manageteamlist', 'manageemailinglist' ,'maps','docs']

def is_valid_destination(destination):
    return destination in dashboard_destinations

@app.route('/dashboard/<destination>')
@login_required
def dashboard(destination = 'home'):
    if not is_valid_destination(destination):
        destination = 'home'
    return render_template('dashboard/index.html', destination=destination)
@app.route('/dashboard')
@app.route('/dashboard/')
@login_required
def dashboard_r_home():
    return redirect(url_for('dashboard',destination='home'))

@app.route('/dashboard/manage', methods=['GET', 'POST'])
@access_required(rank_momentum_normal,'dashboard_r_home')
def dashboard_manage():
    form = ManageForm()
    contrib = ContributorForm()
    if request.method == 'GET':
        member = DBTeam.query.filter_by(steamid=current_user.steamid).first()
        if member is None:
            current_user.upgradeto_memberof_momentum()
            member = DBTeam.query.filter_by(steamid=current_user.steamid).first()
        form.nickname.data = member.nickname
        form.realname.data = member.realname
        form.role.data = member.role
    else:
        try:
            if form.validate():
                member = DBTeam.query.filter_by(steamid=current_user.steamid).first()
                if member is None:
                    flash('A very big internal error has happend. Please contact the webmaster' + url_for(contact))
                else: 
                    member.user_updateinfo(str(form.nickname.data.encode('utf-8')),str(form.realname.data.encode('utf-8')),str(form.role.data.encode('utf-8')))
                    flash('Info updated')
            else:
                flash('Form validation failed. Check your inputs.')
        except:
            flash('An error occurred while trying to process your info. Your info has not been saved')
    return render_template('dashboard/manage.html',destination='manage', form=form, form_contributor=contrib)

@app.route('/dashboard/manage/addcontributor', methods=['GET', 'POST'])
@access_required(rank_momentum_senior,'dashboard_r_home')
def dashboard_manage_contributors():
    if request.method == 'GET':
        return redirect(url_for('dashboard_r_home'))
    contrib = ContributorForm()
    contrib.name.data = request.form.get('name')
    rol = request.form.get('type')
    if not rol:
        rol = None
    contrib.type.data = rol
    special = False
    if request.form.get('special') == 'y':
        special = True
    contrib.special.data = special
    if contrib.validate() == True:
        try:
            contributor = DBContributor(contrib.name.data, contrib.type.data, contrib.special.data)
            contributor.addmyself()
            spec = ''
            if contrib.special.data:
                spec = '(special) '
            return 'Succes, the '+ spec +'contributor '+ contrib.name.data +' added.<br><a href=\"'+ url_for('dashboard_manage') +'\"><< Back to manage</a>'
        except:
            return 'Error creating the new contributor.<br><a href=\"'+ url_for('dashboard_manage') +'\"><< Back to manage</a>'
    else:
        return 'Error creating the new contributor. Form input is faulty.<br>Name: '+ contrib.name.data +'<br>Role: '+ contrib.type.data +'<br>Special?: '+ str(contrib.special.data) + '<br><a href=\"'+ url_for('dashboard_manage') +'\"><< Back to manage</a>'
                

def bool_to_formdata(boolean):
    if boolean:
        return 'y'
    else:
        return 'n'

def formdata_to_bool(char):
    return char == 'y'

@app.route('/dashboard/manage/emailinglist', methods=['GET'])
@access_required(rank_momentum_senior,'dashboard_r_home')
def dashboard_manage_emailinglist():
    email = []
    for entry in DBEmailingList.query.all():
        email.append(entry.email)
    return render_template('dashboard/emailinglist.html',destination='manageemailinglist', listing=email)

@app.route('/dashboard/manage/userslist', methods=['GET', 'POST'])
@access_required(rank_momentum_admin,'dashboard_r_home')
def dashboard_manage_userlists():
    listing = []
    if request.method == 'GET':
        users = DBUser.query.all()
        for user in users:
            uform = UserlistForm()
            uform.username = user.username
            uform.email = user.email
            uform.joindate = str(user.joindate)
            uform.access.data = user.access
            uform.steamid.data= user.steamid
            uform.translator.checked = user.is_translator
            uform.mapper.checked = user.is_mapper
            listing.append(uform)          
        return render_template('dashboard/userslist.html',destination='manageuserslist', listing=listing)
    else:
        # We try to get a user with the given steamid
        try:
            preform = UserlistForm()
            preform.username = request.form.get('username')
            preform.email = request.form.get('email')
            preform.access.data = request.form.get('access')
            preform.steamid.data= request.form.get('steamid')
            preform.translator.checked = formdata_to_bool(request.form.get('translator'))       
            preform.mapper.checked = formdata_to_bool(request.form.get('mapper'))
            if preform.validate():
                if request.form.get('steamid') == None:
                    flash('No steamid submited.')
                user = DBUser.query.filter_by(steamid=str(request.form.get('steamid'))).first()
                if user is None:
                    flash('Error while querying the user. No user found with desired steamid '+ str(request.form.get('steamid')) +'.')
                else:
                    if user.access >= current_user.access:
                        flash('You don\'t have enough permissions to edit this user.')
                    else: # We can edit the user
                        prev = user.access
                        if user.steamid == current_user.steamid:
                            # We can't reach here because last if checks if we have the same access than the modified.. I DO have the same access level than myself
                            flash('You can\'t edit yourself. Try with the settings page.')
                        else:
                            message = ''
                            if str(user.access) != str(request.form.get('access')):
                                user.update_accesslevel(request.form.get('access'))
                                message = 'Access level edited from ' + str(prev) + ' to ' + str(user.access) + '.'
                            if user.is_translator != preform.translator.checked:
                                message = message + ' Translator status from ' + str(user.is_translator) +' to '+ str(preform.translator.checked) + '.'
                                user.update_translatorstatus(preform.translator.checked)
                            if user.is_mapper != preform.mapper.checked:
                                message = message + ' Mapper status from ' + str(user.is_mapper) +' to '+ str(preform.mapper.checked) + '.'
                                user.update_mapperstatus(preform.mapper.checked)
                            flash('User edited: ' + message)
            else:
                flash('Form could not be validated')
            return redirect(url_for('dashboard_manage_userlists'))
        except:
            flash('Error while querying.')
            return render_template('dashboard/userslist.html',destination='manageuserslist', listing=listing)

@app.route('/dashboard/home')
@login_required
def dashboard_home():
    return render_template('dashboard/home.html',destination='home')

@app.route('/dashboard/settings', methods=['GET', 'POST'])
@login_required
def dashboard_settings():
    form = SettingsForm()
    if request.method == 'GET':
        form.email.data = current_user.email
    else:
        try:
            if not current_user.email == request.form.get('email'):
                current_user.update_handlenewemail(form.email.data)
                flash('Email adress updated. Verification email sent to ' + form.email.data)
        except:
            form.email.data = None
            flash('An error occurred while trying to process your info. Your info has not been saved',category='dashboard')
    return render_template('dashboard/settings.html', destination='settings', form=form)

@app.route('/dashboard/docs', methods=['GET', 'POST'])
@access_required(rank_momentum_normal,'dashboard_r_home')
def dashboard_docs():
    form = DocsForm()
    if request.method == 'POST':
        form.subject.data = request.form.get('subject')
        form.title.data = request.form.get('title')
        form.text.data = request.form.get('text')
        form.subject.data = quote_plus(form.subject.data)
        if form.validate():
            other = DBDoc.query.filter_by(subject=form.subject.data).first()
            tother = DBDoc.query.filter_by(title=form.title.data).first()
            if other is None and tother is None:
                doc = DBDoc(current_user.steamid, form.subject.data.lower(), form.title.data, form.text.data)
                db.session.add(doc)
                db.session.commit()
                flash('Doc added successfully')
            else:
                flash('A doc has already the same subject/title than yours. Consider changing it')
    return render_template('dashboard/docs.html',form = form, destination='docs',edit = False)

@app.route('/dashboard/docs/edit/<int:id>', methods=['GET', 'POST'])
@access_required(rank_momentum_normal,'dashboard_r_home')
def dashboard_docs_edit(id=-1):
    if request.method == 'GET':
        if id <= 0:
            return redirect(url_for('dashbaord_docs'))
        doc = DBDoc.query.filter_by(id=id).first()
        if doc is None:
            flash('No doc with id ' + str(id))
            return redirect(url_for('dashbaord_docs'))
        form = DocsForm()
        form.subject.data = doc.subject
        form.title.data = doc.title
        form.text.data = doc.text
        form.is_hidden.checked = doc.is_deleted
        return render_template('dashboard/docs.html',form = form, destination='docs',edit = True)
    else:
        try:
            form = DocsForm()
            form.subject.data = request.form.get('subject')
            form.title.data = request.form.get('title')
            form.text.data = request.form.get('text')
            form.is_hidden.checked = formdata_to_bool(request.form.get('is_hidden'))  
            if form.validate():
                edict = DBDoc.query.filter_by(subject=form.subject.data).first()
                if edict is not None:
                    edict.title = form.title.data
                    edict.text = form.text.data
                    edict.is_deleted = form.is_hidden.checked
                    db.session.commit()
                    flash('Successfully edited doc.')
                    return render_template('dashboard/docs.html',form = form, destination='docs', edit = True)
                else:
                    flash('Could not find matching doc.')
                    raise Exception
            else:
                flash('Form could not be validated. Check for errors.')
                return render_template('dashboard/docs.html',form = form, destination='docs', edit = True)
        except:
            raise
            return redirect(url_for('dashboard_docs'))

@app.route('/dashboard/docs/edit/hide/<int:id>', methods=['GET'])
@access_required(rank_momentum_normal,'dashboard_r_home')
def dashboard_docs_edit_hide(id=-1):
    try:
        if id > 0:
            ## Security is not very high here because doc.hide does that job
            doc = DBDoc.query.filter_by(id=id).first()
            if doc is not None:
                doc.hide()
        return redirect(url_for('docs'))
    except:
        return redirect(url_for('docs'))

@app.route('/dashboard/docs/preview', methods=['GET'])
@access_required(rank_momentum_normal,'dashboard_r_home')
def dashboard_docs_preview():
    text = ''
    try:
        text = request.args.get('text')
    except:
        text = 'Could not fetch form data. Please try again.'
    try:
        title = request.args.get('title')
    except:
        title = 'Could not fetch form data. Please try again.'
    return render_template('dashboard/previewdocs.html',preview=text,title = title, is_doc=True)


@app.route('/dashboard/maps', methods=['GET', 'POST'])
@mapper_required('dashboard_maps')
def dashboard_maps():
    if request.method == 'GET':
        mform = MapsForm()
        return render_template('dashboard/maps.html',destination='maps', form = mform)
    else:
        try:
            mfrom = MapsForm()
            mfrom.mapname.data = request.form.get('mapname')
            mfrom.filepath.data = request.form.get('filepath')
            mfrom.thumbnail.data = request.form.get('thumbnail')
            mfrom.difficulty.data = request.form.get('difficulty')
            if mfrom.validate():
                if DBMap.query.filter_by(stylized_mapname=str(request.form.get('mapname'))).count() != 0:
                    flash('There is already a map called '+ str(request.form.get('mapname')) +'.')
                else:
                    mapfile = os.path.basename(mfrom.filepath.data)
                    thumbnail = mfrom.thumbnail.data
                    if mapfile.endswith('.bsp') and thumbnail.endswith('.jpg'):
                        gamemode = -1
                        if mapfile.startswith('bhop_'):
                            gamemode = 2
                        elif mapfile.startswith('surf_'):
                            gamemode = 1
                        else:
                            gamemode = 3
                        thumbnailcode = 0
                        try:
                            thumbnailcode = requests.head(thumbnail)
                        except:
                            thumbnailcode = None
                        if thumbnail is not None and thumbnailcode.status_code == 200:
                            mapo = DBMap(os.path.splitext(mapfile)[0], mfrom.mapname.data, mfrom.filepath.data, mfrom.thumbnail.data, gamemode, mfrom.difficulty.data, 0)
                            db.session.add(mapo)
                            db.session.commit()
                            flash('Map added successfully')
                        else:
                            flash('Could not fetch thumbnail ' + str(thumbnail) + str(thumbnailcode) +'. Check the path to the image')
                    else:
                        flash('Check file extensions.')                    
            else:
                flash('Form could not be validated. Check the errors')
            return render_template('dashboard/maps.html',destination='maps', form = mfrom)
        except:
            raise
            flash('Error while querying.')
            return render_template('dashboard/maps.html',destination='maps', form = mfrom)

@app.route('/dashboard/settings/verify/<token>')
def dashboard_settings_verifyemail(token):
    try:
        if token is not None:
            user = DBUser.query.filter_by(token=token).first()
            if user is not None:
                if user.verified == False:
                    user.update_verifyemail()
                    return 'Success'
                else:
                    return 'Alredy verified'
        return 'Bad token'
    except:
        return 'A problem has been detected. Email not verified. If the problem persists, <a href=\"'+ url_for('contact',department='web',subject='I can not validate my email ' + str(current_user.email) )+'\">you can contact us</a>'


def momteam_pending():
    if current_user.get_id() is not None and current_user.is_authenticated and current_user.access >= rank_momentum_normal:
        member = DBTeam.query.filter_by(steamid=current_user.steamid).first()
        if member is not None:
            if member.realname is None or member.role is None or member.realname == '' or member.role=='':
                return True
            else:
                return False
        else:
            return False
    else:
        return False
app.jinja_env.globals.update(momteam_pending=momteam_pending)
