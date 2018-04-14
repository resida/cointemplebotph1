from __future__ import division
import jinja2
import datetime
import webapp2
import uuid
import os
import logging
import json

from webapp2_extras import auth, sessions, routes
from utils.auxFunctions import addResponseHeaders, getQAorProd
from google.appengine.api import modules, urlfetch, memcache, channel, app_identity, search
import random
from secrets import secret_string
from utils.decorators import generate_token

import time

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class BaseHandler(webapp2.RequestHandler):

	def __init__(self, request, response):
		# Set self.request, self.response and self.app.
		self.initialize(request, response)
		# ... add your custom initializations here ...
		try:
			if "taskqueue" not in self.request.path_qs:
				logging.info(self.request.GET)
		except Exception as (e):
			logging.info("no lang param given: " + str(e))
		# call to parent init
		super(BaseHandler, self).__init__(request=request, response=response)

	@webapp2.cached_property
	def auth(self):
		return auth.get_auth(request=self.request)

	@webapp2.cached_property
	def user_info(self):
		return self.auth.get_user_by_session()#might have session token in it
		#http://webapp2.readthedocs.io/en/latest/_modules/webapp2_extras/auth.html not sure if makes sense to use the same token for auth


	@webapp2.cached_property
	def user(self):
		"""Shortcut to access the current logged in user."""
		u = self.user_info
		return self.user_model.get_by_id(u['user_id']) if u else None

	@webapp2.cached_property
	def user_model(self):
		"""Returns the implementation of the user model."""
		return self.auth.store.user_model

	@webapp2.cached_property
	def session_store(self):
		return sessions.get_store(request=self.request)

	@webapp2.cached_property
	def session(self):
		"""Shortcut to access the current session."""
		return self.session_store.get_session(backend="datastore", max_age=3600)

	def render_template(self, view_filename, params=None):


		if not params:
			params = {}
		user = self.user_info
		logging.info("self.session " +str(self.session))
		logging.info(user)
		params['user'] = user
		template = JINJA_ENVIRONMENT.get_template(view_filename)
		if self.user:
			csrf = generate_token(self.user.get_id(), secret_string)
		else:
			csrf = str(uuid.uuid4())
			self.session[csrf] = True
		params['csrf'] = csrf
		params['curr_version_id'] = os.environ['CURRENT_VERSION_ID'].split('.')[1]
		params['QAorProd'] = getQAorProd()

		logging.info(self.user)
		if self.user:
			params["isMorgan"] = (self.user.email == "martindell90@gmail.com")
			params["loggedIn"] = True
			params["loggedInEmail"] = self.user.email

		else:
			params["loggedIn"] = False

		self = addResponseHeaders(self)



		return self.response.out.write(template.render(params).encode('utf-8'))





	def display_session_error(self):
		return self.render_template('templates/sessionerror.html')

	def display_message(self, message):
		"""Utility function to display a template with a simple message."""
		params = {'message': message}
		return self.render_template('templates/message.html', params)

	# this is needed for webapp2 sessions to work
	def dispatch(self):
		# Get a session store for this request.
		self.session_store = sessions.get_store(request=self.request)
		try:
			# Dispatch the request.
			super(BaseHandler, self).dispatch()
		finally:
			# Save all sessions.
			self.session_store.save_sessions(self.response)

	def handle_exception(self, exception, debug):
		# Log the error.
		# Set a custom message.
		tracking_id = str(uuid.uuid4()).replace('-', '')
		logging.error(tracking_id)
		logging.exception(exception)
		self.display_message('Server Error. Tracking ID: {tracking_id}'.format(tracking_id=tracking_id))

		# If the exception is a HTTPException, use its error code.
		# Otherwise use a generic 500 error code.
		if isinstance(exception, webapp2.HTTPException):
			self.response.set_status(exception.code)
		else:
			self.response.set_status(500)


class RedirectHandler(webapp2.RequestHandler):
	def get(self, path):
		url = self.request.url
		if "https://www." in url:
			new_url = url.replace("https://www.", "https://")
			return self.redirect(new_url, permanent=True)
		else:
			return self.redirect(url, permanent=True)

