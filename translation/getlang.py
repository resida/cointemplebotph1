# coding=utf-8

from auth_signup_trans import auth_signup_en, auth_signup_es
from auth_login_trans import auth_login_en, auth_login_es
from auth_forgot_trans import auth_forgot_en, auth_forgot_es
from auth_resetpw_trans import auth_resetpw_en, auth_resetpw_es
from account_trans import account_en, account_es

def getLang(self, route):
	#lang = self.session.get('language')
	lang = 'en'
	if lang:
		if lang == 'en':
			return getRouteDictEnglish(route)
		elif lang == 'es':
			return getRouteDictSpanish(route)
		elif lang == '':
			return getRouteDictEnglish(route)
	else:
		return getRouteDictEnglish(route)


def getRouteDictEnglish(route):
	if route == 'auth_signup':
		return auth_signup_en()
	if route == 'auth_login':
		return auth_login_en()
	if route == 'auth_forgot':
		return auth_forgot_en()
	if route == 'auth_resetpw':
		return auth_resetpw_en()
	if route == 'account':
		return account_en()


def getRouteDictSpanish(route):
	if route == 'auth_signup':
		return auth_signup_es()
	if route == 'auth_login':
		return auth_login_es()
	if route == 'auth_forgot':
		return auth_forgot_es()
	if route == 'auth_resetpw':
		return auth_resetpw_es()
	if route == 'account':
		return account_es()
