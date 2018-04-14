#!/usr/bin/env python
# coding=utf-8

import logging
from collections import OrderedDict
import webapp2
from webapp2_extras import routes
from base import RedirectHandler
from handlers.auth import VerificationHandler, ResetPasswordHandler, ForgotPasswordHandler, LogoutHandler, \
    LoginHandler, SignupHandler
from handlers.home import HomeHandler, UsersHandler
from handlers.trading import PlaceTradeHandler, CancelOrdersHandler, TradingGDAXCEXHandler, UpdateSettingsHandler
from handlers.logs_handlers import ExchangeAPIMonitorHandler, ExchangeAPIMonitorAJAXHandler

from models import DataStoreSessionFactorExtended
from secrets import secret_string

token_max_age = 604800 * 3  # 3 weeks
token_new_age = 1800
token_cache_age = 600


class ReverseProxyMiddleware(object):
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        real_host = environ.get('HTTP_X_REAL_HOST') or environ.get('HTTP_X_FORWARDED_SERVER')
        if real_host:
            environ['HTTP_HOST'] = real_host
            environ['SERVER_NAME'] = real_host
        real_ip = environ.get('HTTP_X_REAL_IP') or environ.get('HTTP_X_FORWARDED_FOR')
        if real_ip:
            environ['REMOTE_ADDR'] = real_ip
        return self.application(environ, start_response)


config = {  # user_attributes is a list of attributes in the User model that will be cached in the session.
    'webapp2_extras.auth': {
        'user_model': 'models.User',
        'user_attributes': ['email', 'verified'],
        'session_backend': 'datastore',
        'token_max_age': token_max_age,
        'token_new_age': token_new_age,
        'token_cache_age': token_cache_age
    },
    'webapp2_extras.sessions': {
        'secret_key': secret_string,
        'backends': {
            'securecookie': 'webapp2_extras.sessions.SecureCookieSessionFactory',
            'datastore': DataStoreSessionFactorExtended,
            'memcache': 'webapp2_extras.appengine.sessions_memcache.MemcacheSessionFactory',
        }
    }
}

orderedRouteDict = OrderedDict(
        [
            ("mainRoute", {"route": '/', "handler": HomeHandler, "name": 'home'}),
            ("usersHandlerRoute", {"route": '/users', "handler": UsersHandler, "name": 'UsersHandler'}),

            # UI
            ("tradingPairRoute",
             {"route": '/trading/general', "handler": TradingGDAXCEXHandler, "name": 'trading_pair'}),

            # TRADING
            ("placeTradeRoute", {"route": '/work_exchange', "handler": PlaceTradeHandler, "name": 'place_trade'}),
            ("cancelOrdersRoute", {"route": '/cancel_order', "handler": CancelOrdersHandler, "name": 'cancel_orders'}),

            # AUTH
            ("verifyRoute",
             {"route": '/verify/<type:v|p|c>/<user_id:\d+>-<signup_token:.+>', "handler": VerificationHandler,
              "name": 'verification'}),
            ("resetPasswordRoute", {"route": '/password/reset', "handler": ResetPasswordHandler, "name": 'resetpw'}),
            ("forgotPasswordRoute", {"route": '/password/forgot', "handler": ForgotPasswordHandler, "name": 'forgot'}),
            ("logoutRoute", {"route": '/logout', "handler": LogoutHandler, "name": 'logout'}),
            ("loginRoute", {"route": '/login', "handler": LoginHandler, "name": 'login'}),
            ("signupRoute", {"route": '/signup', "handler": SignupHandler, "name": 'signup'}),

            ("UpdateSettingsRoute",
             {"route": '/update_settings/', "handler": UpdateSettingsHandler, "name": 'UpdateSettings'}),

            ("SendNotificationRoute",
             {"route": '/send_notification_email', "handler": UpdateSettingsHandler, "name": 'SendNotification'}),

            ##Logging
            ("ExchangeAPIMonitorRoute",
             {"route": '/logs/general', "handler": ExchangeAPIMonitorHandler, "name": 'ExchangeAPIMonitor'}),
            ("ExchangeAPIMonitorAJAXRoute", {"route": '/logs/ajax/general', "handler": ExchangeAPIMonitorAJAXHandler,
                                             "name": 'ExchangeAPIMonitorAJAX'})

        ]
)

addList = []
for item in orderedRouteDict:
    addList.append(webapp2.Route(orderedRouteDict[item]["route"], orderedRouteDict[item]["handler"],
                                 orderedRouteDict[item]["name"]))
app = webapp2.WSGIApplication(addList, debug=True, config=config)
app = ReverseProxyMiddleware(app)
