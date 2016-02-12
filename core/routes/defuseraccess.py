__author__ = 'gnaughton'

from core import app

#This is meant to be some kind of shadowban. So don't tell anyone! :O
def lvl_user_banned():
    return 0
app.jinja_env.globals.update(lvl_user_banned=lvl_user_banned)
def lvl_newuser_noverified():
    return 1
app.jinja_env.globals.update(lvl_newuser_noverified=lvl_newuser_noverified)
def lvl_min_user_notbanned():
    return lvl_newuser_noverified()
app.jinja_env.globals.update(lvl_min_user_notbanned=lvl_min_user_notbanned)
def lvl_newuser_verified():
    return 2
app.jinja_env.globals.update(lvl_newuser_verified=lvl_newuser_verified)
def lvl_userof_momentumteam_rookie():
    return 7
app.jinja_env.globals.update(lvl_userof_momentumteam_rookie=lvl_userof_momentumteam_rookie)
def lvl_userof_momentumteam_normal():
    return 8
app.jinja_env.globals.update(lvl_userof_momentumteam_normal=lvl_userof_momentumteam_normal)
def lvl_userof_momentumteam_pro():
    return 9
app.jinja_env.globals.update(lvl_userof_momentumteam_pro=lvl_userof_momentumteam_pro)
def lvl_userof_momentumteam_admin():
    return 10
app.jinja_env.globals.update(lvl_userof_momentumteam_admin=lvl_userof_momentumteam_admin)
def lvl_min_userof_momentumteam():
    return lvl_userof_momentumteam_rookie()
app.jinja_env.globals.update(lvl_min_userof_momentumteam=lvl_min_userof_momentumteam)
def lvl_web_maintainment():
    #access requeired for maintenance
    #accunts with this access are not shown publicly, nor have more "power" than admin
    return 11
app.jinja_env.globals.update(lvl_web_maintainment=lvl_web_maintainment)


    

