__author__ = 'gnaughton'
from flask import render_template, redirect, request, flash, url_for, abort
from flask_login import login_user, logout_user, current_user, login_required

from core import app
from core.models import DBUser, DBTeam, DBContributor
from core.routes.defuseraccess import rank_user_banned, rank_momentum_normal, rank_momentum_admin, rank_webmaster, access_required, rank_momentum_senior
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Optional

class ManageForm(Form):
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
    email = 'Email'
    submit = SubmitField("Update user")
dashboard_destinations = ['home','manage','settings','manageuserslist']

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
            member.upgradeto_memberof_momentum()
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
                

@app.route('/dashboard/manage/userslist', methods=['GET', 'POST'])
@access_required(rank_momentum_admin,'dashboard_r_home')
def dashboard_manage_userlists():
    listing = []
    if request.method == 'GET':
        users = DBUser.query.all()
        for user in users:
            uform = UserlistForm()
            uform.username = user.username
            uform.email= user.email
            uform.access.data = user.access
            uform.steamid.data= user.steamid
            listing.append(uform)          
        return render_template('dashboard/userslist.html',destination='manageuserslist', listing=listing)
    else:
        # We try to get a user with the given steamid
        try:
            if uform.validate():
                if request.form.get('steamid') == None:
                    return ('No steamid submited.')
                user = DBUser.query.filter_by(steamid=str(request.form.get('steamid'))).first()
                if user is None:
                    return('Error while querying the user. No user found with desired steamid '+ str(request.form.get('steamid')) +'.')
                else:
                    if user.access >= current_user.access:
                        return ('You don\'t have enough permissions to edit this user.')
                    else: # We can edit the user
                        prev = user.access
                        if str(user.access) == str(request.form.get('access')):
                            return ('Tried to change to the same access.')
                        else:
                            if user.steamid == current_user.steamid:
                                # We can't reach here because last if checks if we have the same access than the modified.. I DO have the same access level than myself
                                return ('You can\'t edit yourself. Try with <a href=\"' + url_for('dashboard_settings') + '\">the settings page</a>.')
                            else:
                                user.update_accesslevel(request.form.get('access'))
                                return '<center>User edited: (Access) ' + str(prev) + ' -> ' + str(user.access) + '<br><a href=\"' + url_for('dashboard_manage_userlists') + '\"><< Back to user list</a></center>'
            else:
                return 'Form could not be validated'
        except:
            return ('Error while querying.')
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
            if not current_user.email == form.email.data:
                current_user.update_handlenewemail(form.email.data)
                flash('Email adress updated. Verification email sent to ' + form.email.data)
        except:
            form.email.data = None
            flash('An error occurred while trying to process your info. Your info has not been saved',category='dashboard')
    return render_template('dashboard/settings.html', destination='settings', form=form)

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
