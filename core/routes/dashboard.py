__author__ = 'gnaughton'
from flask import render_template, redirect, request, flash, url_for, abort
from flask_login import login_user, logout_user, current_user

from core import app
from core.models import DBUser, DBTeam
from core.routes.defuseraccess import lvl_min_userof_momentumteam
from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, Email, Optional

class OptionalIf(Optional):
    # a validator which makes a field required if
    # another field is set

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(OptionalIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('No field named "%s" in form' % self.other_field_name)
        if other_field.data is not None:
            super(OptionalIf, self).__call__(form, field)

class ManageForm(Form):
    nickname = TextField("Nickname")
    realname = TextField("Real name", validators=[OptionalIf(nickname)])
    role = TextField("Role", validators=[InputRequired("Your role can not be empty")])
    submit = SubmitField("Send")

class SettingsForm(Form):
    email = TextField("Email", validators=[InputRequired("Enter a valid email"), Email("Email must be valid")])
    submit = SubmitField("Send")

dashboard_destinations = ['home','manage','settings']

def is_valid_destination(destination):
    return destination in dashboard_destinations

@app.route('/dashboard/<destination>')
def dashboard(destination = 'home'):
    if current_user.get_id() is not None and current_user.is_authenticated:
        if not is_valid_destination(destination):
            destination = 'home'
        return render_template('dashboard/index.html', destination=destination)
    else:
        flash('You can\'t access here without login in first')
        return redirect(url_for('login', next='dashboard_r_home'))
@app.route('/dashboard')
@app.route('/dashboard/')
def dashboard_r_home():
    return redirect(url_for('dashboard',destination='home'))

@app.route('/dashboard/manage', methods=['GET', 'POST'])
def dashboard_manage():
    if current_user.get_id() is not None and current_user.is_authenticated and current_user.access >= lvl_min_userof_momentumteam():
        form = ManageForm()
        if request.method == 'GET':
            member = DBTeam.query.filter_by(steamid=current_user.steamid).first()
            if member is None:
                member.upgradeto_memberof_momentum()
            form.nickname.data = member.nickname
            form.realname.data = member.realname
            form.role.data = member.role
        else:
            try:
                member = DBTeam.query.filter_by(steamid=current_user.steamid).first()
                if member is None:
                    flash('A very big internal error has happend. Please contact the webmaster' + url_for(contact))
                else: 
                    member.user_updateinfo(str(form.nickname.data.encode('utf-8')),str(form.realname.data.encode('utf-8')),str(form.role.data.encode('utf-8')))
                    flash('Info updated')
            except:
                flash('An error occurred while trying to process your info. Your info has not been saved')
        return render_template('dashboard/manage.html',destination='manage',form=form)
    else:
        flash('Authorized personnel only.', category='login')
        return redirect(url_for('login', next='dashboard_r_home'))

@app.route('/dashboard/home')
def dashboard_home():
    if current_user.get_id() is not None and current_user.is_authenticated:
        return render_template('dashboard/home.html',destination='home')
    else:
        flash('You need to log in before being able to acces the resource.', category='login')
        return redirect(url_for('login', next='dashboard_r_home'))

@app.route('/dashboard/settings', methods=['GET', 'POST'])
def dashboard_settings():
    if current_user.get_id() is not None and current_user.is_authenticated and current_user.access >= lvl_min_userof_momentumteam():
        form = SettingsForm()
        if request.method == 'GET':
            form.email.data = current_user.email
        else:
            try:
                if not current_user.email == form.email.data:
                    current_user.update_handlenewemail(form.email.data)
                    flash('Email adress updated')
            except:
                form.email.data = None
                flash('An error occurred while trying to process your info. Your info has not been saved',category='dashboard')
        return render_template('dashboard/settings.html', destination='settings', form=form)
    else:
        flash('You need to log in before being able to acces the resource.', category='login')
        return redirect(url_for('login', next='dashboard_settings'))

def momteam_pending():
    if current_user.get_id() is not None and current_user.is_authenticated and current_user.access >= lvl_min_userof_momentumteam():
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
