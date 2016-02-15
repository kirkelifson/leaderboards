__author__ = 'rabsrincon'

from functools import update_wrapper, wraps
from flask import current_app, abort, request
from flask.ext.login import LoginManager, current_user
from core import app

rank_user_banned, rank_user_normal, rank_user_senior, rank_momentum_normal, rank_momentum_senior, rank_momentum_admin, rank_webmaster = range(7)

def access_required(access, nextUrl=None):
	def accessWrapper(func):
		@wraps(func)
		def decorated(*args, **kwargs):
			if current_app.login_manager._login_disabled:
				return func(*args, **kwargs)
			elif not current_user.is_authenticated:
				if nextUrl is not None:
					setattr(request, 'next_url', nextUrl)
				return current_app.login_manager.unauthorized()
			elif current_user.access < access:
				if nextUrl is not None:
					setattr(request, 'next_url', nextUrl)
				return current_app.login_manager.unauthorized()
			return func(*args, **kwargs)
		return decorated
	return accessWrapper

def unauthenticated_only(func):
	@wraps(func)
	def decorated(*args, **kwargs):
		if current_user.is_authenticated:
			return current_app.login_manager.unauthenticated()
		return func(*args, **kwargs)
	return decorated

class ExtendedLoginManager(LoginManager):
	unauthenticated_callback = lambda: abort(403)
	def __init__(self, app=None, add_context_processor=True):
		super(ExtendedLoginManager, self).__init__(app, add_context_processor)
	def unauthenticated_handler(self, func):
		self.unauthenticated_callback = func
		return func
	def unauthenticated(self):
		return self.unauthenticated_callback()

app.jinja_env.globals.update(rank_momentum_normal=rank_momentum_normal)
app.jinja_env.globals.update(rank_momentum_admin=rank_momentum_admin)



    

