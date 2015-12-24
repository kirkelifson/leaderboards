__author__ = 'gnaughton'

from flask_login import LoginManager, current_user

from core import app
from core.models import DBUser


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

app.jinja_env.globals.update(current_user=current_user)

@login_manager.user_loader
def loaduser(id):
    return DBUser.query.get(int(id))
