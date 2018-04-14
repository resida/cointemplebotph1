from __future__ import division
import calendar
import os
import hmac
import time
import logging
import urllib
from hashlib import sha512
from global_variables import LENGTH_OF_UUID4
from secrets import secret_string


#http://stackoverflow.com/questions/25363433/why-does-webapp2-auth-get-user-by-session-change-the-token token auto created for session?
def csrf_decorator(handler):
	def check_csrf(self, *args, **kwargs):
		token = self.request.get("csrf")
		if not token:
			return self.display_session_error()
		logging.info("delivered csrf param" + token)
		if len(token) == LENGTH_OF_UUID4:
			logging.info("len(token) != LENGTH_OF_UUID4:")
			if not self.session.get(token):
				return self.display_session_error()
		else:
			logging.info("len(token) == LENGTH_OF_UUID4:")
			if not validate_token(token, secret_string):#adding a session variable check in here possibly?
				return self.display_session_error()
		return handler(self, *args, **kwargs)
	return check_csrf

def test_decorator(handler):
	def check_csrf2(self, *args, **kwargs):
		token = self.request.get("csrf")
		if not token:
			return self.display_session_error()
		logging.info("delivered csrf param" + token)
		if False:
			logging.info("decorator has self.user")
			if not validate_token(token, secret_string):#adding a session variable check in here possibly?
				return self.display_session_error()
		else:
			logging.info("decorator does not have self.user")
			if not self.session.get(token):
				return self.display_session_error()
		return handler(self, *args, **kwargs)
	return check_csrf2


def user_required(handler):
	#handler is the get function i believe ...
	def check_login(self, *args, **kwargs):
		user = self.user
		logging.info(user)
		auth = self.auth
		logging.info(auth)
		redirectpath = urllib.quote_plus(self.request.path_qs) #changed this, need to make sure its right
		logging.info(redirectpath)
		self.session['redirect_url'] = redirectpath
		#auth.get_user_by_session() must be true ... but return handler(self, *args, **kwargs) must point to something w a worker module
		#if auth.get_user_by_session
		if auth.get_user_by_session():
			logging.info("has auth get by session")
			return handler(self, *args, **kwargs)
		logging.info("doesn't have auth get by session")
		logging.info(auth.get_user_by_session())
		return self.redirect('/login')
	return check_login

def generate_token(userid, secret, time_valid=7200):
	expiration_time = int(time.time()) + time_valid  # that's time in seconds. time_valid by default is 7200s (2 hours)
	if userid and secret:
		message = '%s---%s' % (userid, expiration_time)
		hmac_hash = hmac_hash_sha512(key=secret, message=message)
		return '%s|%s,%s' % (userid, hmac_hash, expiration_time)


def validate_token(token, secret):
	if not token or not secret:
		return False
	expiration_time = token.split(',')[1]
	current_time = int(time.time())
	if current_time >= expiration_time:
		return False
	userid = token.split('|')[0]
	other_part = token.split('|')[1]
	hmac_hash = other_part.split(',')[0]
	message = '%s---%s' % (userid, expiration_time)
	if hmac_hash == hmac_hash_sha512(key=secret, message=message):
		return True
	return False


# the new hashing algorith to use
def hmac_hash_sha512(key, message):
	return hmac.new(key=key, msg=message, digestmod=sha512).hexdigest()