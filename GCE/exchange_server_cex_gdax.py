# -*- coding: utf-8 -*-
#! /usr/bin/python
import random
import socket
import threading
import time
import uuid

import flask_restful as restful
from flask import Flask, make_response
from flask_restful import Api, reqparse

# CEX_API_KEY, CEX_API_SECRET, CEX_UID,
from GCE.exchange_classes.cex.cex import Cex
from GCE.exchange_classes.gdax.gdax import Gdax
from GCE.secrets import GDAX_API_KEY, GDAX_API_SECRET, GDAX_PASSPHRASE, TEST_CEX_UID, TEST_CEX_KEY, \
    TEST_CEX_SECRET
from firebase import set_child_value
# what if ... it gets partially filled, and before i have time to check whether its partially filled i make a new order ...
# might need to put everything in one loop and also check for partial fills to be extra professional
from helper_functions import is_valid
from trading_logic import exchange_buy_and_send_thread

#cexio_global = Cex(CEX_UID, CEX_API_KEY, CEX_API_SECRET)
cexio_global = Cex(TEST_CEX_UID, TEST_CEX_KEY, TEST_CEX_SECRET)
gdax_global = Gdax(GDAX_API_KEY, GDAX_API_SECRET, GDAX_PASSPHRASE)
appll = Flask(__name__, static_url_path="")
api = Api(appll)
GCE_NAME = socket.gethostname()

def update_thread():
    global cexio_global
    global gdax_global
    while True:
        try:
            cexio_balances = cexio_global.balance
            usd_avail = float(cexio_balances["USD"]["available"])
            btc_avail = float(cexio_balances["BTC"]["available"])
            usd_orders = float(cexio_balances["USD"]["orders"])
            btc_orders = float(cexio_balances["BTC"]["orders"])
            set_child_value(["cexio", "positions", "total", "USD"], usd_avail+usd_orders)
            set_child_value(["cexio", "positions", "total", "BTC"], btc_avail+btc_orders)
            set_child_value(["cexio", "positions", "avail", "USD"], usd_avail)
            set_child_value(["cexio", "positions", "avail", "BTC"], btc_avail)
        except:
            print "cexio_balances error"
        try:
            gdax_list = gdax_global.balances()
            #add logic for gda balances here
        except:
            print "gdax error"
        time.sleep(25)

def current_spread(cexio_global, gdax_global):
    return ((cexio_global.ask_price - gdax_global.get_ask_price())/cexio_global.ask_price)*100.0

def update_ticker_thread():
    global cexio_global
    global gdax_global
    counter = 0
    last_test_time = 0
    while True:
        time.sleep(3)
        list_of_running = []
        for thread in threading.enumerate():
            list_of_running.append(thread.name)
        if "update_thread" not in list_of_running:
            t = threading.Thread(target=update_thread, name="update_thread")
            t.start()
        if cexio_global.test_mode_active:
            if time.time() - last_test_time > 600:
                if len(cexio_global.working_order_dict) < 5:
                    coin = random.randint(1, 2)
                    if coin == 1:
                        quantity = .01
                        required_spread = round(current_spread(cexio_global, gdax_global) - random.uniform(0.9, 2.5), 1)
                    else:
                        quantity = -.01
                        required_spread = round(current_spread(cexio_global, gdax_global) + random.uniform(0.9, 2.5), 1)
                    create_order(required_spread, quantity)
                    last_test_time = time.time()
        counter += 1

t = threading.Thread(target=update_ticker_thread)
t.start()

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

class CancelOrder(restful.Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('Access-Nonce', location='headers')
        self.reqparse.add_argument('Access-Key', location='headers')
        self.reqparse.add_argument('Access-Signature', location='headers')
        super(CancelOrder, self).__init__()

    def post(self, wo_uuid):
        args = self.reqparse.parse_args()
        nonce = args['Access-Nonce']
        api_key = args['Access-Key']
        signature = args['Access-Signature']
        if not is_valid(nonce, api_key, signature):
            print("invalid")
            return "invalid"
        global cexio_global
        global gdax_global
        return_dict = {}
        cexio_global.set_continue_loop(wo_uuid, False)
        return_dict["successCexio"] = cexio_global.cancel_order(wo_uuid)
        return return_dict

def create_order(required_spread, quantity):
    order_uuid = str(uuid.uuid4())
    return_val = cexio_global.add_working_order(order_uuid)
    if return_val == "temp max working reached":
        print return_val
        return return_val
    cexio_global.set_continue_loop(order_uuid, True)
    cexio_global.set_required_spread(order_uuid, required_spread)
    cexio_global.set_total_quantity(order_uuid, quantity)
    if quantity > 0:
        cexio_global.set_buy_sell(order_uuid, "buy")
    else:
        cexio_global.set_buy_sell(order_uuid, "sell")
    cexio_global.set_remaining_quantity(order_uuid, abs(float(quantity)))
    t = threading.Thread(target=exchange_buy_and_send_thread, args=[order_uuid, cexio_global, gdax_global])
    t.start()

class PlaceOrder(restful.Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        args = self.reqparse.parse_args()
        self.reqparse.add_argument('Access-Nonce', location='headers')
        self.reqparse.add_argument('Access-Key', location='headers')
        self.reqparse.add_argument('Access-Signature', location='headers')
        self.reqparse.add_argument('required_spread')
        self.reqparse.add_argument('quantity')
        super(PlaceOrder, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        required_spread = float(args['required_spread'])
        quantity = float(args['quantity'])
        nonce = args['Access-Nonce']
        api_key = args['Access-Key']
        signature = args['Access-Signature']
        if not is_valid(nonce, api_key, signature):
            print("invalid")
            return "invalid"
        create_order(required_spread, quantity)
        return ""

class Home(restful.Resource):
    def get(self):
        response1 = "1"
        response = make_response(response1, 200)
        response = addHeaders(response)
        return response

class TestModeToggle(restful.Resource):
    def get(self):
        global cexio_global
        if cexio_global.test_mode_active:
            cexio_global.test_mode_active = False
        else:
            cexio_global.test_mode_active = True
        response1 = "1"
        response = make_response(response1, 200)
        response = addHeaders(response)
        return response

api.add_resource(Home, '/', endpoint='home')
api.add_resource(CancelOrder, '/cancelOrder/<o_uuid>', endpoint='cancel_order')
api.add_resource(PlaceOrder, '/place_order', endpoint='place_order')
api.add_resource(TestModeToggle, '/toggle_test_mode', endpoint='toggle_test')

if __name__ == '__main__':
    appll.run(host='0.0.0.0',port=443, ssl_context='adhoc') #port=443, ssl_context='adhoc'




