from utils.decorators import csrf_decorator, user_required
from models import IpSignupCounter, User
from base import BaseHandler
from random import randint
import json
import logging
VALID_RESPONSE = [200, 201, 202]

class HomeHandler(BaseHandler):
    @user_required
    def get(self):
        params = {}
        params['home_page'] = True
        return self.redirect("/trading/general")

class UsersHandler(BaseHandler):
    @user_required
    def get(self):
        allUsers = User.query().fetch()
        return_dict = {}
        for user in allUsers:
            return_dict[user.email] = True
        return self.response.out.write(json.dumps(return_dict))
