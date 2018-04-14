import logging
import string
import datetime
import urllib
import uuid
import time
import json
from random import randint
from google.appengine.ext import ndb
from utils.auxFunctions import getQAorProd, getSupportEmail, getURLBase
from translation.getlang import getLang
from webapp2_extras.appengine.auth.models import UserToken
import datetime
from google.appengine.api import search, memcache, urlfetch
from global_variables import VALID_RESPONSE,MAX_BEFORE_SIGNUP_CAPTCHA, MAX_SIGNUP_REQUESTS_BEFORE_TEMP_BAN, \
	MAX_BEFORE_LOGIN_CAPTCHA, MAX_LOGIN_ATTEMPTS_BEFORE_TEMP_BAN, WINDOW_IN_SECONDS, MAX_TEMP_BAN_BEFORE_PERMANENT

from libraries.validate_email import validate_email

from webapp2_extras.auth import InvalidPasswordError, InvalidAuthIdError

from utils.decorators import csrf_decorator, user_required, test_decorator

from utils.emailFunctions import send_signup_verify_email, send_forgot_password_email
from models import IpSignupCounter, User
from base import BaseHandler

class SignupHandler(BaseHandler):

	def get(self):
		if self.user:
			return self.redirect('/')
		self.auth.unset_session()
		params = {}
		params['auth_signup_trans'] = getLang(self, 'auth_signup')
		return self.render_template('templates/auth_signup.html', params=params)


	@csrf_decorator
	def post(self):
		ipcheck = checkIPAndCaptcha(self, 'signup')
		logging.info(ipcheck)
		if ipcheck == '30minBan':
			params = {"error": 'Too many signup requests from same ip address. Please wait 30 minutes.'}
			params['auth_signup_trans'] = getLang(self, 'auth_signup')
			return self.render_template('templates/auth_signup.html', params)
		password = self.request.get('password')
		email = self.request.get('email')
		repeatPassword = self.request.get("repeatpassword")
		error = ''
		if not password or not repeatPassword or password != repeatPassword:
			error = 'passwords did not match or password was not valid'
		elif not email or not validate_email(email):
			error = 'email not valid'
			logging.info(email)
			logging.info(validate_email(email))
		if error:
			logging.info(error)
			params = {"error": error}
			params['auth_signup_trans'] = getLang(self, 'auth_signup')
			return self.render_template('templates/auth_signup.html', params)

		email = email.lower()
		password = password
		#not sure if i should have email here twice or not ...

		#second arg is unique properties i believe it is a list of the keyworded properties that must be unique and
		#does not interact with the auth id which is the first property

		user_data = self.user_model.create_user(email,["email"],password_raw=password,verified=False,email=email)

		if not user_data[0]: #user_data is a tuple, [0] will be false if an email with this account already exists
			error = "This email address already has an account."
			params = {"error": error}
			params['auth_signup_trans'] = getLang(self, 'auth_signup')
			return self.render_template('templates/auth_signup.html', params)

		logging.info("user_data " + str(user_data))

		user = user_data[1]
		logging.info("user " + str(user))
		user_id = user.get_id()
		token = self.user_model.create_signup_token(user_id)
		verification_url = self.uri_for('verification', type='v', user_id=user_id, signup_token=token, _full=True)
		send_signup_verify_email(email=email, url=verification_url)
		message = "We've sent you a verification email, please click on the verification link in the email to confirm your account."
		params = {'message': message}
		return self.render_template('templates/message.html', params)


class VerificationHandler(BaseHandler):
	def get(self, *args, **kwargs):
		self.auth.unset_session()
		user_id = kwargs['user_id']
		signup_token = kwargs['signup_token']
		verification_type = kwargs['type']

		token_obj = UserToken.query(UserToken.token == signup_token).get()
		if verification_type == 'v' and (not token_obj or (token_obj.created < datetime.datetime.now() - datetime.timedelta(days=1))):
			self.auth.unset_session()
			return self.display_message("Token has expired, please contact support or look in your email inbox for a more recent link.")
		elif not token_obj or (token_obj.created < datetime.datetime.now() - datetime.timedelta(hours=3)):
			self.auth.unset_session()
			return self.display_message("Token has expired, please contact support or look in your email inbox for a more recent link.")

		user, ts = self.user_model.get_by_auth_token(int(user_id), signup_token, 'signup')
		if not user:
			logging.info('Could not find any user with id "%s" signup token "%s"', user_id, signup_token)
			self.auth.unset_session()
			return self.abort(404)

		# store user data in the session
		#self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
		self.session['pw_user_id'] = user_id
		if verification_type not in ['v', 'p', 'c']:
			logging.info('verification type not supported')
			self.auth.unset_session()
			return self.abort(404)

		if verification_type == 'v':
			if not user.verified:
				user.verified = True
				user.put()
			self.auth.unset_session()
			params = {'message': 'Account verified. Please <a href="/login">Login</a>.'}
			return self.render_template('templates/message.html', params)
		elif verification_type == 'p':
			self.session['resetpw'] = True
			self.session['signuptoken'] = signup_token
			return self.redirect(self.uri_for('resetpw'))
		else:
			logging.info('verification type not supported')
			self.abort(404)

class ForgotPasswordHandler(BaseHandler):
	def get(self):
		return self._serve_page()

	@csrf_decorator
	def post(self):

		ipcheck =checkIPAndCaptcha(self, 'forgot')
		if ipcheck and ipcheck == '30minban':
			return self._serve_page(brute_force_issue='Too many requests from same ip address. Please wait 30 minutes.')
		email = self.request.get('email')
		user = self.user_model.get_by_auth_id(email.lower())
		if not user:
			logging.info('email w no user entry %s', email)
			return self._serve_page(ifFound=True)
		user_id = user.get_id()
		token = self.user_model.create_signup_token(user_id)
		verification_url = self.uri_for('verification', type='p', user_id=user_id, signup_token=token, _full=True)
		send_forgot_password_email(email=email, url=verification_url)
		return self._serve_page(ifFound=True)

	def _serve_page(self, ifFound=False, brute_force_issue=''):

		email = self.request.get('email')
		params = {
			'email': email,
			'ifFound': ifFound,
			"brute_force_issue": brute_force_issue
		}
		params["auth_forgot_trans"] = getLang(self, 'auth_forgot')
		return self.render_template('templates/auth_forgot.html', params)

class ResetPasswordHandler(BaseHandler):
	def get(self):

		if not self.session.get('resetpw'):
			time.sleep(2)
			return self.redirect(self.uri_for('home'))
		self.session['resetpw'] = None #how does this session thing work? how long does it last?
		# what about incognito vs normal? does it persist across that?
		if not self.session.get('signuptoken'):
			time.sleep(2)
			return self.redirect(self.uri_for('No signup token in session data when resetting password'))
		signup_token = self.session.get('signuptoken')
		self.session['signuptoken'] = None
		params = {
		    'token': signup_token,
		}
		params['auth_resetpw_trans'] = getLang(self, 'auth_resetpw')
		return self.render_template('templates/auth_resetpassword.html', params)

	@csrf_decorator
	def post(self):
		params = {'auth_resetpw_trans':getLang(self, 'auth_resetpw')}
		newpassword = self.request.get('newpassword')
		repeatnewpassword = self.request.get('repeatnewpassword')
		old_token = self.request.get('token')
		if not newpassword or newpassword != repeatnewpassword:
			params["error"] = "passwords do not match"
			return self.render_template('templates/auth_resetpassword.html', params)
		user_id = self.session.get('pw_user_id')
		if not user_id:
			self.auth.unset_session()
			params["error"] = "invalid user"
			return self.render_template('templates/auth_resetpassword.html', params)
		user, ts = self.user_model.get_by_auth_token(int(user_id), old_token, 'signup')
		user.set_password(newpassword)
		user.put()
		self.session['pw_user_id'] = None
		self.auth.unset_session()
		params["passwordUpdated"] = True
		return self.render_template('templates/auth_resetpassword.html', params)

class LoginHandler(BaseHandler):
	def get(self):
		if self.user:
			return self.redirect('/')
		return self._serve_page()

	@csrf_decorator
	def post(self):
		email = self.request.get('email')
		email = email.lower()
		password = self.request.get('password')
		try:
			u = self.auth.get_user_by_password(email.lower(), password, remember=False, save_session=False)
			#do i need to call unset session here? i reall dont know how this works
			#why would calling self.user when there is no user make user none later after call get_user_by_password? very odd possibly: http://stackoverflow.com/questions/28746857/webapp2-extras-auth-with-backend-datastore-not-working-properly
			#http://stackoverflow.com/questions/25363433/why-does-webapp2-auth-get-user-by-session-change-the-token is there one token automatically
			#created for each session?
			self.auth.set_session(u)
			user_id = int(self.user.get_id())
			logging.info("self.user " + str(self.user))
			logging.info("self.user_info " + str(self.user_info))
			logging.info(u)
			if u['verified'] != True:
				email = email.lower()
				logging.info(email)
				logging.info(user_id)
				token = self.user_model.create_signup_token(user_id)
				verification_url = self.uri_for('verification', type='v', user_id=user_id, signup_token=token, _full=True)
				send_signup_verify_email(email=email, url=verification_url)
				return self._serve_page(failed=False, verified=True)

			return self.redirect('/')

		except (InvalidAuthIdError, InvalidPasswordError) as e:
			#20 max invalid requests per 30 minutes
			memcache_key = 'request-count-login' + self.request.remote_addr
			memcache_alreadycounted = 'bannedlogin-already-counted' + self.request.remote_addr
			ipcount = memcache.get(key=memcache_key)
			if ipcount is not None and ipcount > MAX_LOGIN_ATTEMPTS_BEFORE_TEMP_BAN:
				memcache.incr(key=memcache_alreadycounted)
				logging.warning("Remote user has %d requests; rejecting." % (ipcount))
				return self._serve_page(brute_force_issue='Too many login requests from same ip address. Please wait 30 minutes.')
			ipcount = memcache.incr(key=memcache_key)
			if ipcount is None:
				memcache.add(key=memcache_key, value=1, time=WINDOW_IN_SECONDS)
				memcache.add(key=memcache_alreadycounted, value=1, time=WINDOW_IN_SECONDS)
			logging.info('Login failed for user %s because of %s', email, type(e))
			return self._serve_page(failed=True)

	def _serve_page(self, failed=False, verified=False, brute_force_issue=''):

		email = self.request.get('email')

		params = {
			"email": email,
			"failed": failed,
			"verified": verified,
			"brute_force_issue": brute_force_issue
	    }
		params['auth_login_trans'] = getLang(self, 'auth_login')
		return self.render_template('templates/auth_login.html', params)


class LogoutHandler(BaseHandler):
	def get(self):
		self.auth.unset_session()
		return self.redirect(self.uri_for('home'))


def getNumInLast10Minutes(last100RequestTimes):
	numInLast10Minutes = 0
	date_10_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=10)
	for time in last100RequestTimes:
		if time > date_10_minutes_ago:
			numInLast10Minutes += 1
	return numInLast10Minutes


def checkIPAndCaptcha(self,typeString):
	ipSignupCounter = IpSignupCounter.query(IpSignupCounter.ipAddress == self.request.remote_addr,IpSignupCounter.typeString ==typeString).get()
	if not ipSignupCounter:
		ipSignupCounter = IpSignupCounter.create(self.request.remote_addr, typeString, [datetime.datetime.utcnow()])
		ipSignupCounter.put()
		return "everything is fine"

	last100TimesList = ipSignupCounter.last100RequestTimes
	last100TimesList.append(datetime.datetime.utcnow())
	ipSignupCounter.last100RequestTimes = last100TimesList
	ipSignupCounter.put()

	numInLastTenMinutes = getNumInLast10Minutes(ipSignupCounter.last100RequestTimes)
	needCaptcha, tempBan = False, False
	if numInLastTenMinutes > 3:
		needCaptcha = True
		if numInLastTenMinutes > 25:
			tempBan = True
			ipSignupCounter.timesBanned = ipSignupCounter.timesBanned + 1
			ipSignupCounter.put()
			logging.warning("User has had %d requests in last 30 minutes, rejecting." % (numInLastTenMinutes))
			return '30minBan'

	if needCaptcha:
		return "everything is fine"
		#captchastatus = sendCaptchaResponsetoGoogle(self)
		#if captchastatus and captchastatus == 'invalidcaptcha':
		 #return 'invalidcaptcha'

	return "everything is fine"



