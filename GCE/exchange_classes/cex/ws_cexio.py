import threading

import websocket
import time
import sys
from security.secrets import TEST_CEX_API_KEY, TEST_CEX_API_SECRET
import hmac
import hashlib
import datetime
import json
from operator import itemgetter

class CexioWebsocket(object):
    room_subscribe_message = {
        "e": "subscribe",
        "rooms": ["pair-BTC-USD"]
    }

    order_book_subscribe_message = {
        "e": "order-book-subscribe",
        "data": {
            "pair": [
                "BTC",
                "USD"
            ],
            "subscribe": True,
            "depth":20
        },
        "oid": "1435927928274_3_order-book-subscribe"
    }

    open_orders_subscribe_message = {
        "e": "open-orders",
        "data": {
            "pair": [
                "BTC",
                "USD"
            ]
        },
        "oid": "1435927928274_6_open-orders"
    }

    get_balance_message = {
        "e": "get-balance",
        "data": {},
        "oid": "1435927928274_2_get-balance"
    }

    get_orders_message = {
        "e": "get-balance",
        "data": {},
        "oid": "1435927928274_2_get-balance"
    }


    def __init__(self):
        self.channel_id_this_time = 0
        self.old_best_bid = -1
        self.old_best_ask = -1
        self.best_bid = -1
        self.best_ask = -1
        self.bids_dict = {}
        self.asks_dict = {}
        self.counter = 0
        self.exited = False
        self.update_thread = None
        self.is_authenticated = False
        self.auth_message_sent = False
        self.subscribed_to_orderbook = False
        self.subscribed_to_open_orders = False
        self.time_last_auth_sent = 0
        self.last_balance_sent = 0
        self.last_orders_sent = 0
        self.sent_subscribed_to_room = False
        #self.received_subscribe_message = False

    def exit(self):
        self.exited = True
        self.ws.close()

    def connect(self):
        header = {'origin': 'wss://ws.cex.io/ws/'}

        self.ws = websocket.WebSocketApp('wss://ws.cex.io/ws',
                                    header=header,
                                    on_message=self.__on_message,
                                    on_close=self.__on_close,
                                    on_open=self.__on_open,
                                    on_error=self.__on_error)

        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()

        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            time.sleep(1)
            conn_timeout -= 1
        if not conn_timeout:
            self.exit()
            sys.exit(1)

    def handle_auth(self, json_message):
        if 'e' in json_message:
            if json_message['e'] == 'auth':
                if 'ok' in json_message:
                    if json_message["ok"] == "ok":
                        self.is_authenticated = True
        if not (time.time() - self.time_last_auth_sent > 5):
            return
        if (not self.is_authenticated):
            self.time_last_auth_sent = time.time()
            auth_dict = self.auth_request(TEST_CEX_API_KEY, TEST_CEX_API_SECRET)
            print "sending auth"
            self.ws.send(auth_dict)

    def handle_open_orders(self, json_message):
        pass

    def handle_get_balance(self, json_message):
        if (not self.is_authenticated):
            return
        if time.time() - self.last_balance_sent > 5:
            subscribe_dict = CexioWebsocket.get_balance_message
            subscribe_dict["oid"] = str(int(time.time())) + "_2_get-balance"
            self.last_balance_sent = time.time()
            try:
                self.last_balance_sent = time.time()
                self.ws.send(json.dumps(subscribe_dict))
            except Exception as ex:
                print ex

    def handle_get_orders(self, json_message):
        if (not self.is_authenticated):
            return
        if time.time() - self.last_balance_sent:
            subscribe_dict = CexioWebsocket.room_subscribe_message
            self.sent_subscribed_to_room = True
            self.ws.send(subscribe_dict)

    #############
    #ORDER BOOK FUNCTIONS
    #############

    def best_bid_ask(self, bids_dict, asks_dict):
        # GETS BID AND ASK PRICE FOR ORDER BOOK
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

    def make_order_dicts(self, json_message):
        #CREATES THE ORIGINAL ORDER BOOK
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

    def remove(self, bids_dict, asks_dict, data):
        #REMOVES FROM ORDERBOOK
        if data[0] in bids_dict:
            del bids_dict[data[0]]
        elif data[0] in asks_dict:
            del asks_dict[data[0]]

    def update_dicts(self, bids_dict, asks_dict, data, ask_or_bid):
        # UPDATES ORDER BOOK
        if ask_or_bid == "bids":
            bids_dict[data[0]] = data[1]
        elif ask_or_bid == "asks":
            asks_dict[data[0]] = data[1]

    def handle_subscr_order_book(self, json_message):
        if 'e' in json_message:
            if json_message['e'] == "order-book-subscribe":
                if 'ok' in json_message:
                    if json_message["ok"] == "ok":
                        self.bids_dict, self.asks_dict = self.make_order_dicts(json_message)
                        self.subscribed_to_orderbook = True
        if not self.subscribed_to_orderbook:
            subscribe_dict = CexioWebsocket.order_book_subscribe_message
            subscribe_dict["oid"] = str(int(time.time())) + "_3_order-book-subscribe"
            self.ws.send(json.dumps(subscribe_dict))

    #############
    # ORDER BOOK FUNCTIONS
    #############

    def handle_md_update(self, json_message):
        if "e" in json_message:
            if json_message["e"] == "md_update":
                if json_message["data"]["pair"] == 'BTC:USD':
                    self.counter += 1
                    for bid_or_ask in ["bids", "asks"]:
                        for item in json_message["data"][bid_or_ask]:
                            if type(item) != list:
                                return
                            if item[1] == 0:
                                self.remove(self.bids_dict, self.asks_dict, item)
                            else:
                                self.update_dicts(self.bids_dict, self.asks_dict, item, bid_or_ask)
        if self.counter % 10 == 0:
            self.best_bid, self.best_ask = self.best_bid_ask(self.bids_dict, self.asks_dict)
            print str(self.best_bid) + " " + str(self.best_ask)

    def __on_message(self, ws, message):
        json_message = json.loads(message)
        self.handle_auth(json_message)
        self.handle_get_balance(json_message)
        self.handle_subscr_order_book(json_message)
        self.handle_md_update(json_message)

    def __on_error(self, ws, error):
        pass

    def __on_close(self, ws):
        pass

    def create_signature_Py27(self, key, secret):
        timestamp = int(time.time())
        string = "{}{}".format(timestamp, key)
        return timestamp, hmac.new(secret, string, hashlib.sha256).hexdigest()

    def auth_request(self, key, secret):
        timestamp, signature = self.create_signature_Py27(key, secret)
        return json.dumps({'e': 'auth','auth': {'key': key, 'signature': signature, 'timestamp': timestamp,}, 'oid': 'auth'})

    def __on_open(self, ws):
        auth_request = self.auth_request(TEST_CEX_API_KEY, TEST_CEX_API_SECRET)
        auth_dict = auth_request
        ws.send(auth_dict)

if __name__ == "__main__":
    ws = CexioWebsocket()
    RESTART_INTERVAL = 50
    while True:
        ws.connect()
        start_time = time.time()
        while (ws.ws.sock.connected):
            time.sleep(1)
