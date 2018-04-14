# -*- coding: utf-8 -*-
#! /usr/bin/python
from exchange_container import Exchanges
import os
from flask import Flask, jsonify, make_response, request
from flask_restful import Api, reqparse
import flask_restful as restful
import socket
try:
    import thread
except ImportError:
    import _thread as thread
import json
import sys
sys.path.append('/home/martindell90/coin-temple-dev/coin-temple-2')
exchanges_global = Exchanges()
appll = Flask(__name__, static_url_path="")
api = Api(appll)
GCE_NAME = socket.gethostname()

def addHeaders(response):
    response.headers['X-Frame-Options'] = 'sameorigin'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Permitted-Cross-Domain-Policies'] = '-1'
    response.headers['Content-Security-Policy'] = "default-src 'self' ; style-src 'unsafe-inline' ; img-src 'self'"
    return response


class CancelWorking(restful.Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        """
        self.reqparse.add_argument('Access-Nonce', location='headers')
        self.reqparse.add_argument('Access-Key', location='headers')
        self.reqparse.add_argument('Access-Signature', location='headers')
        """
        self.reqparse.add_argument('id_string')
        super(CancelWorking, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        """
        nonce = args['Access-Nonce']
        api_key = args['Access-Key']
        signature = args['Access-Signature']
        if not is_valid(nonce, api_key, signature):
            print("invalid")
            return "invalid"
        """
        id_string = args["id_string"]
        global exchanges_global
        exchanges_global.cancel_working_list([id_string])
        return ""

class WorkExchange(restful.Resource):
    """
    this is the main function called when an order is placed
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        """
        self.reqparse.add_argument('Access-Nonce', location='headers')
        self.reqparse.add_argument('Access-Key', location='headers')
        self.reqparse.add_argument('Access-Signature', location='headers')
        """
        self.reqparse.add_argument('wo_params_dict', type=str, required=True, help='missing arg', location='json')
        super(WorkExchange, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()

        """
        nonce = args['Access-Nonce']
        api_key = args['Access-Key']
        signature = args['Access-Signature']
        if not is_valid(nonce, api_key, signature):
            print("invalid")
            return "invalid"
        """

        wo_params_dict = args["wo_params_dict"]
        wo_params_dict = json.loads(wo_params_dict)
        print wo_params_dict
        global exchanges_global
        exchanges_global.create_wo(wo_params_dict)
        return ""

class Home(restful.Resource):
    def get(self):
        response1 = "1"
        response = make_response(response1, 200)
        response = addHeaders(response)
        return response

#working orders - an logical program

api.add_resource(Home, '/', endpoint='home')
api.add_resource(CancelWorking, '/cancel', endpoint='cancel_working')
api.add_resource(WorkExchange, '/work_exchange', endpoint='work_exchange')

if __name__ == '__main__':
    appll.run(host='0.0.0.0',port=80) #port=443, ssl_context='adhoc'