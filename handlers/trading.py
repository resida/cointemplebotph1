from __future__ import division

import datetime
import json
import time
import uuid
from google.appengine.api import urlfetch
from base import BaseHandler
from models import TradeSettings
from utils.decorators import user_required
from  utils.server_interaction import place_order, cancel_all_orders

BUCKET_SIZE = 1000
VALID_RESPONSE = [200, 201, 202]

def addSettingsToParams(params, user):
    thisSettings = TradeSettings.query(TradeSettings.user_id == user.key.id()).get()
    print "$$$4" * 1000
    if thisSettings:
        print thisSettings
        params["coin"] = thisSettings.coin
        params["required_spread"] = thisSettings.required_spread
        params["trade_size"] = thisSettings.trade_size
        params["send_to"] = thisSettings.send_to
        params["buy_on"] = thisSettings.buy_on
        params["email_notification"] = thisSettings.email_notification
        params["description_string"] = "if order is set, will send " + str(params["trade_size"]) + " BTC to " + str(
                params["send_to"]) + " when spread reaches " \
                                       + str(
                params["required_spread"]) + "% and will send a notification email to " + str(
                params["email_notification"])
    else:
        print "else"
        params["coin"] = None
        params["required_spread"] = None
        params["trade_size"] = None
        params["send_to"] = None
        params["buy_on"] = None
        params["email_notification"] = None
    return params


class TradingGDAXCEXHandler(BaseHandler):
    @user_required
    def get(self):
        params = {}
        params["exchange_list"] = ["GDAX", "CEX", "KRAKEN", "EXMO", "BITTREX"]
        params["exchange_pair"] = "gdax_cex"
        params = addSettingsToParams(params, self.user)
        return self.render_template("templates/trading_general.html", params)



class UpdateSettingsHandler(BaseHandler):
    @user_required
    def post(self):
        coin = self.request.get("coin", "btc")
        required_spread = self.request.get("required_spread")
        trade_size = self.request.get("trade_size")
        send_to = self.request.get("send_to", "cex")
        buy_on = self.request.get("buy_on", "gdax")

        if send_to == buy_on:
            return self.redirect("/trading/general")
        email_notification = self.request.get("email_notification")
        try:
            required_spread = float(required_spread)
        except:
            required_spread = 100.0
        try:
            trade_size = float(trade_size)
        except:
            trade_size = 0.0

        exchange_pair = "%s_%s" % (buy_on, send_to)
        thisSettings = TradeSettings.query(TradeSettings.user_id == self.user.key.id()).get()
        if not thisSettings:
            thisSettings = TradeSettings()
        thisSettings.coin = coin
        thisSettings.exchange_pair = exchange_pair
        thisSettings.required_spread = float(required_spread)
        thisSettings.trade_size = float(trade_size)
        thisSettings.send_to = send_to
        thisSettings.buy_on = buy_on
        thisSettings.email_notification = email_notification
        thisSettings.user_id = int(self.user.key.id())
        thisSettings.put()

        return self.redirect("/trading/general")


def firebase_update(set_list, set_dict):
    firebase_url = 'https://tenex-capital.firebaseio.com'
    url_string = ""
    for item in set_list:
        url_string += "/" + item
    url_string += ".json"
    payload = set_dict
    response = urlfetch.fetch(
            url=str(firebase_url + url_string),
            method=urlfetch.PATCH,
            payload=json.dumps(payload),
            deadline=20
    )


def firebase_write(set_list, set_dict):
    firebase_url = 'https://tenex-capital.firebaseio.com'
    url_string = ""
    for item in set_list:
        url_string += "/" + item
    url_string += ".json"
    payload = set_dict
    response = urlfetch.fetch(
            url=str(firebase_url + url_string),
            method=urlfetch.PUT,
            payload=json.dumps(payload),
            deadline=20
    )


def firebase_push(set_list, set_dict):
    firebase_url = 'https://tenex-capital.firebaseio.com'
    url_string = ""
    for item in set_list:
        url_string += "/" + item
    url_string += ".json"
    payload = set_dict
    response = urlfetch.fetch(
            url=str(firebase_url + url_string),
            method=urlfetch.POST,
            payload=json.dumps(payload),
            deadline=20
    )


def cancel_order_gdax_cexio(thisSettings):
    wo_uuid = thisSettings.current_order_id

    set_list = ["log", "gdax_cex"]
    time_readable = datetime.datetime.now().strftime("%m-%d %H:%M")
    text_to_set = "cancelled order id: " + str(wo_uuid)[0:6]
    set_dict = {"neg_time_unix": -time.time(), "text": text_to_set, "time_readable": time_readable,
                "time_unix": time.time()}
    firebase_push(set_list, set_dict)
    set_list = ["status"]
    set_dict = {"gdax_cex": ""}
    firebase_update(set_list, set_dict)


def place_order_gdax_cexio(thisSettings):
    required_spread = thisSettings.required_spread
    quantity = thisSettings.trade_size
    send_to = thisSettings.send_to
    set_list = ["log", "gdax_cex"]
    time_readable = datetime.datetime.now().strftime("%m-%d %H:%M")
    wo_uuid = str(uuid.uuid4())

    text_to_set = "order id: " + str(wo_uuid)[0:6] + " set order to send " + str(
            quantity) + " BTC to " + send_to + " with required spread: " + str(required_spread)
    set_dict = {"neg_time_unix": -time.time(), "text": text_to_set, "time_readable": time_readable,
                "time_unix": time.time()}
    firebase_push(set_list, set_dict)

    set_list = ["status"]

    set_dict = {"gdax_cex": "ORDER " + str(wo_uuid)[0:6] + " CURRENTLY SET: SEND " + str(
            quantity) + " BTC to " + send_to + " with required spread: " + str(required_spread)}
    firebase_update(set_list, set_dict)

    thisSettings.current_order_id = wo_uuid
    thisSettings.put()


class CancelOrdersHandler(BaseHandler):
    @user_required
    def get(self):
        cancel_all_orders()
        return self.response.out.write("success")


class PlaceTradeHandler(BaseHandler):
    @user_required
    def get(self):
        place_order(self.user.key.id())
