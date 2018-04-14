from __future__ import division
import time
import hmac
from google.appengine.api import memcache, app_identity,  modules, urlfetch, memcache
from global_variables import SUPPORT_EMAIL_ADDRESS_PROD, SUPPORT_EMAIL_ADDRESS_QA
import datetime

def pretty_date(time=False):

	now = datetime.datetime.utcnow()
	if type(time) is int:
		diff = now - datetime.datetime.fromtimestamp(time)
	elif isinstance(time,datetime.datetime):
		diff = now - time
	elif not time:
		diff = now - now
	second_diff = diff.seconds
	day_diff = diff.days
	#print time
	#print datetime.datetime.now()
	#print day_diff

	if day_diff < 0:
		return ''

	if day_diff == 0:
		if second_diff < 10:
			return "just now"
		if second_diff < 60:
			return str(int(second_diff)) + " seconds ago"
		if second_diff < 120:
			return "a minute ago"
		if second_diff < 3600:
			return str(int(second_diff / 60)) + " minutes ago"
		if second_diff < 7200:
			return "an hour ago"
		if second_diff < 86400:
			return str(int(second_diff / 3600)) + " hours ago"
	if day_diff == 1:
		return "Yesterday"
	if day_diff < 7:
		return str(int(day_diff)) + " days ago"
	if day_diff < 31:
		return str(int(day_diff / 7)) + " weeks ago"
	if day_diff < 365:
		return str(int(day_diff / 30)) + " months ago"
	return str(int(day_diff / 365)) + " years ago"

def addResponseHeaders(self):
	#https://developers.google.com/web/fundamentals/security/csp/

	#self.response.headers["Content-Security-Policy"] = "default-src 'unsafe-inline' 'self' https://code.jquery.com/ http://*.googleapis.com https://*.stripe.com https://*.bootstrapcdn.com https://*.googleapis.com https://npmcdn.com https://www.google.com/jsapi; "

	self.response.headers["X-Frame-Options"] = "sameorigin"
	self.response.headers["X-Content-Type-Options"] = "nosniff"
	self.response.headers["Strict-Transport-Security"] = "max-age=31536000"
	self.response.headers["Content-Type"] = "text/html; charset=utf-8"
	self.response.headers["X-XSS-Protection"] = "1; mode=block"
	self.response.headers["Cache-Control"] = "no-cache"
	self.response.headers["Set-Cookie"] = "secure; httponly;"
	self.response.headers["Pragma"] = "no-cache"
	self.response.headers["X-Permitted-Cross-Domain-Policies"] = "master-only"
	self.response.headers["Expires"] = "-1"
	return self

def changeUserBalance(self, amountInCents):
	if not self.user:
		return "user error"


	if self.user.balanceInCents:
		newBalance = self.user.balanceInCents + amountInCents
	else:
		newBalance = amountInCents

	if newBalance < 0:
		return "negative balance error"
	self.user.balanceInCents = newBalance
	self.user.put()
	return "success"



#def decreaseUserBalance(self, amountInCents):

def getQAorProd():
	if app_identity.get_application_id() == 'coin-temple':
		return "prod"
	return "qa"

def getURLBase():
	if app_identity.get_application_id() == 'coin-temple':
		return "https://coin-temple.appspot.com/"
	return "https://coin-temple.appspot.com/"

def getSupportEmail():
	if app_identity.get_application_id() == 'coin-temple':
		return SUPPORT_EMAIL_ADDRESS_QA
	return SUPPORT_EMAIL_ADDRESS_PROD

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
