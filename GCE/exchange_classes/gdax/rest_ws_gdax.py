#https://github.com/matveyco/cex.io-api-python
#PUBLIC ENDPOINTS
#We throttle public endpoints by IP: 3 requests per second, up to 6 requests per second in bursts.

#PRIVATE ENDPOINTS
#We throttle private endpoints by user ID: 5 requests per second, up to 10 requests per second in bursts.

"""
    See https://docs.gdax.com/#ids
"""
import websocket
from operator import itemgetter
import hmac
import hashlib
import time
import requests
import threading
import json
from collections import deque
#from firebase import set_in_firebase, set_child_value, firebase_read_value, firebase_push_value
from security.secrets import TEST_GDAX_API_KEY, TEST_GDAX_API_SECRET, TEST_GDAX_API_PASSPHRASE
import base64
from requests.auth import AuthBase
import sys
import datetime
import logging
logging.basicConfig()

BASE_URL = u'https://api.gdax.com'
PUBLIC_CALLS = {u'products', u'product_order_book', u'ticker', u'product_trades', u'product_historic_rates', u'product_24hr_stats', u'currencies', u'time'}
PRIVATE_CALLS = {u'account':u'GET', u'accounts':u'GET', u'account_history':u'GET', u'account_holds':u'GET', u'history_pagination':u'GET', u'holds_pagination':u'GET', u'buy':u'POST', u'sell':u'POST', u'cancel_order':u'POST', u'cancel_all':u'POST'}

'''
def record_log_in_firebase_func(result, request_url, param, rate_of_calls, time_elapsed, wo_id):
    push_dict = {"result":str(result),"request_url":str(request_url),"param":str(param), "timestamp":time.time(),
                 "neg_timestamp":-time.time(), "api_rate":rate_of_calls,"time_elapsed":time_elapsed, "wo_id":wo_id}
    firebase_push_value(["cexio_bitfinex", "api_call_log"], push_dict)

def ws_price_health_check(ask_price, bid_price):
    response_var = requests.get("https://cex.io/api/ticker/BTC/USD")
    response_json = json.loads(response_var.text)
    test_variable = abs(float(response_json["ask"]) - ask_price) * 100 / ask_price
    test_variable_2 = abs(float(response_json["bid"]) - bid_price) * 100 / bid_price
    if test_variable > 1 and test_variable_2 > 1:
        # health warning
        print "may be problematic"
    else:
        print "prices healthy"
'''

class GDAXAPI(object):

    def __init__(self, api_key=TEST_GDAX_API_KEY, api_secret=TEST_GDAX_API_SECRET, api_passphrase=TEST_GDAX_API_PASSPHRASE):
        self.next_call_time = 0
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.ask_price = 0
        self.bid_price = 0
        self.old_ask = 0
        self.old_bid = 0
        self.max_working_orders = 5
        self.working_order_dict = {}
        self.continue_threads = True
        self.api_calls_this_time_period = 0.0
        self.time_period_length_in_seconds = 180
        self.time_period_start = 0
        self.api_calls_per_second = 0.0
        self.queue = deque()
        self.start_time = time.time()
        self.test_mode_active = False
        self.auth = GdaxAuth(api_key, api_secret, api_passphrase) #todo: add this scheme to cexio
        self.ws = None
        t = threading.Thread(target=self.maintain_websocket_thread)
        t.start()

        t = threading.Thread(target=self.update_ticker_thread)
        t.start()

    def discontinue_threads(self):
        self.continue_threads = False

    def api_call(self, **kwargs):
        if "wo_id" in kwargs:
            wo_id = kwargs["wo_id"]
        else:
            wo_id = ''
        command = kwargs["command"]
        if "param" in kwargs:
            param = kwargs["param"]
        else:
            param = {}
        if "action" in kwargs:
            action = kwargs["action"]
        else:
            action = ''
        if "call" in kwargs:
            call = kwargs["call"]
        else:
            call = ''
        """
        :param command: Query command for getting info
        :type commmand: str
        :param param: Extra options for query
        :type options: dict
        :return: JSON response from CEX.IO
        :rtype : dict
        """
        print command
        print call
        if call not in PUBLIC_CALLS:
            call_type = PRIVATE_CALLS[call]
            before_time = time.time()
            if call_type == 'GET':
                r = requests.get(BASE_URL + '/' + str(command) + '/', auth=self.auth)
            else:
                r = requests.post(BASE_URL + '/' + command + '/', data=json.dumps(kwargs), auth=self.auth)
            after_time = time.time()
            time_elapsed = after_time - before_time
            self.queue.append((time.time(), time_elapsed))
        else:
            before_time = time.time()
            r = requests.get(BASE_URL + '/' + command + '/')  # no authentication needed
            after_time = time.time()
            time_elapsed = after_time - before_time
            self.queue.append((time.time(), time_elapsed))

        #t = threading.Thread(target=self.update_queue)
        #t.start()
        #t = threading.Thread(target=record_log_in_firebase_func, args=[result, request_url, param, self.api_calls_per_second, time_elapsed, wo_id])
        #t.start()
        print r.json()
        return r.json()

    def balance(self, account_id=''):
        return self.api_call(call='accounts', command='accounts', param=None, action=None)

    def ticker(self, market):
        """
        :param market: String literal for the market (ex: BTC/ETH)
        :type market: str
        :return: Current values for given market in JSON
        :rtype : dict
        """
        #wo_id, command, param = None, action = ''
        print market
        return self.api_call(call='ticker', command='products/{}/ticker'.format(market), param=None, action=None)

    def update_dicts(self, bids_dict, asks_dict, data, ask_or_bid):
        if ask_or_bid == "bids":
            bids_dict[data[0]] = data[1]
        elif ask_or_bid == "asks":
            asks_dict[data[0]] = data[1]

    def update_queue(self):
        TIME_WINDOW_SECS = 600.0
        avg_latency = 0.0
        try:
            while self.queue[0][0] < time.time() - TIME_WINDOW_SECS:
                self.queue.popleft()
        except IndexError:
            print "there are no records in the queue."

        for item in self.queue:
            avg_latency += item[1]
        if len(self.queue):
            avg_latency = avg_latency/len(self.queue)

        dfds = time.time() - self.start_time
        if dfds < TIME_WINDOW_SECS:
            self.api_calls_per_second = float(len(self.queue)) / float(dfds)
        else:
            self.api_calls_per_second = float(len(self.queue)) / float(TIME_WINDOW_SECS)
        '''
        set_child_value(["bitfinex_gdax", "num_calls_per_sec"], self.api_calls_per_second)
        if avg_latency:
            set_child_value(["bitfinex_gdax", "avg_latency"], avg_latency)
        '''

    def update_ticker(self):
        return_val = self.ticker()
        if type(return_val) != dict:
            return_val = json.loads(return_val)
        self.ask_price = return_val["ask"]
        self.bid_price = return_val["bid"]

    def update_ticker_thread(self):
        counter = 0
        while self.continue_threads:
            counter += 1
            if counter % 20000 == 0:
                self.update_queue()
                #ws_price_health_check(self.ask_price, self.bid_price)
            try:
                if time.time() - self.ws.last_update_time < 8:
                    self.ask_price = self.ws.best_ask
                    self.bid_price = self.ws.best_bid
                else:
                    print "did update ticker"
                    self.update_ticker()
                    #set_child_value(["gdax", "prices", "btc", "bid"], self.bid_price)
                    #set_child_value(["gdax", "prices", "btc", "ask"], self.ask_price)
                    time.sleep(2.1)
                if abs(self.old_ask - self.ask_price) > .5 or abs(self.old_bid - self.bid_price) > .5:
                    self.old_ask = self.ask_price
                    self.old_bid = self.bid_price
                    firebase_dict = {
                        "bid": self.bid_price,
                        "ask": self.ask_price,
                        "last_update_time": time.time()
                    }
                    #set_child_value(["gdax", "prices", "btc"], firebase_dict)
            except:
                print "timeout or error gdax"
            time.sleep(.001)

    def maintain_websocket_thread(self):
        self.ws = GDAXWebsocket()
        RESTART_INTERVAL = 2000
        while True:
            try:
                self.ws.connect()
                start_time = time.time()
                while self.ws.ws.sock.connected:
                    time.sleep(1)
                    if time.time() - start_time > RESTART_INTERVAL:
                        break
                self.ws.subscribed_to_orderbook = False
                self.ws.exit()
                time.sleep(2)
            except Exception as ex:
                print "except location 1"
                print ex

    def best_bid_ask(self, bids_dict, asks_dict):
        bid_list = []
        for item in bids_dict:
            bid_list.append((item, bids_dict[item]))
        bid_list.sort(key=itemgetter(0), reverse=True)
        best_bid = bid_list[0][0]
        ask_list = []
        for item in asks_dict:
            ask_list.append((item, asks_dict[item]))
        ask_list.sort(key=itemgetter(0))
        best_ask = ask_list[0][0]
        return best_bid, best_ask

class GDAXWebsocket(object):

    def __init__(self, api_key=TEST_GDAX_API_KEY, api_secret=TEST_GDAX_API_SECRET, api_passphrase=TEST_GDAX_API_PASSPHRASE):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.old_best_bid = -1
        self.old_best_ask = -1
        self.best_bid = -1
        self.best_ask = -1
        self.bids_dict = {}
        self.asks_dict = {}
        self.sent_subscribed_to_room = False
        self.exited = False
        self.stop = False
        self.ws = None
        self.wst = None
        self.thread = None
        self.is_authenticated = False
        self._sequence = -1
        self._current_ticker = None
        self.last_balance_sent = 0
        self.last_orders_sent = 0
        self.sent_subscribed_to_room = False
        self.last_update_time = 0
        self.url = 'wss://ws-feed.gdax.com'

    def exit(self):
        self.exited = True
        self.ws.close()

    def create_gdax_signature(self, secret):
        timestamp = str(time.time())
        path = '/users/self/verify'
        message = timestamp + 'GET' + path
        message = message.encode('ascii')
        hmac_key = base64.b64decode(secret)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())
        return signature_b64

    def connect(self):
        if self.url[-1] == "/":
            self.url = self.url[:-1]
        self.ws = websocket.WebSocketApp(self.url,
                                         on_open=self.__on_open,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_error=self.__on_error)
        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()
        conn_timeout = 5
        try:
            while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
                time.sleep(1)
                conn_timeout -= 1
            if not conn_timeout:
                self.exit()
        except Exception as ex:
            print "except location 2"
            print ex

    def __on_open(self, ws):
        auth_request = self.auth_request(self.api_key, self.api_secret, self.api_passphrase)
        self.stop = False
        #sub_params = {'type': 'subscribe', 'product_ids': [u'BTC-USD'], "channels": [u'user']} #authenticated
        #sub_params = {'type': 'subscribe', 'product_ids': ["BTC-USD"]}
        #sub_params = {"type": "open", "user_id": "e758536a-f1a7-444b-8713-8ac6b652804e", "profile_id": "e8861c5c-c373-42f0-a13c-22ce6cfe8a14"}

        #auth_dict = auth_request.update(sub_params)

        ws.send(json.dumps(auth_request))
        #ws.send(sub_params)

    def __on_close(self, ws):
        pass

    def __on_message(self, ws, message):
        while not self.stop:
            try:
                msg = json.loads(message)
            except Exception as e:
                ws.__on_error(e)
            else:
                #ws.handle_open_orders(msg)
                #ws.handle_subscr_order_book(msg)
                #ws.handle_md_update(msg)
                #ws.handle_order_updates(msg)
                print(msg)

    def __on_error(self, ws):
        #print error
        return

    def auth_request(self, key, secret, passphrase):
        timestamp = str(time.time())
        signature = self.create_gdax_signature(secret)
        return {u'type': u'subscribe', u'product_ids': [u'BTC-USD'], u'channels': [u'full'], u'key': key, u'signature': signature, u'timestamp': timestamp,
                u'passphrase': passphrase}

    def handle_get_orders(self, json_message):
        if (not self.is_authenticated):
            return
        if time.time() - self.last_balance_sent:
            subscribe_dict = GDAXWebsocket.room_subscribe_message
            self.sent_subscribed_to_room = True
            self.ws.send(subscribe_dict)

    def remove(self, bids_dict, asks_dict, data):
        if data[0] in bids_dict:
            del bids_dict[data[0]]
        elif data[0] in asks_dict:
            del asks_dict[data[0]]

    def handle_open_orders(self, json_message):
        sub_params = {"type": "open", "user_id": "5844eceecf7e803e259d0365", "profile_id": "765d1549-9660-4be2-97d4-fa2d65fa3352"}

    def make_order_dicts(self, json_message):
        return_bids_dict = {}
        return_asks_dict = {}
        bids_list = json_message["data"]["bids"]
        asks_list = json_message["data"]["asks"]
        for item in bids_list:
            price_level = item[0]
            quantity = item[1]
            return_bids_dict[price_level] = quantity
        for item in asks_list:
            price_level = item[0]
            quantity = item[1]
            return_asks_dict[price_level] = quantity
        return return_bids_dict, return_asks_dict


class GdaxAuth(AuthBase):
    # Provided by gdax: https://docs.gdax.com/#signing-a-message
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or '')
        message = message.encode('ascii')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())
        request.headers.update({
            'Content-Type': 'Application/JSON',
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase
        })
        return request

#asdf = GDAXWebsocket()
#asdf.connect()

rest = GDAXAPI()
#ws.balance()
#rest.ticker('BTC-USD')
#rest.balance()
