import datetime
import threading
import time
from exchange_classes.blockcypher import get_num_confirmations_transaction
import requests
import secrets
import settings
from exchange_classes.cex.cex import Cex
from exchange_classes.gdax.gdax import Gdax
from exchange_classes.bittrex.bittrex import Bittrex
from exchange_classes.kraken.kraken import Kraken
from exchange_classes.exmo.exmo import Exmo
from currency_classes.abstract import Currencies
from firebase import set_in_firebase, firebase_push_value, firebase_read_value

from working_order_class import WorkingOrder
ACTIVE_EXCHANGE_LIST = ["cexio", "gdax", "kraken", "bittrex", "exmo"]

# The allowed trading margin error between the amount placed as an order and the amount stage to be transfered to the
# desitnation exchange
ALLOWED_TRADE_TRANSFER_MARGIN_ERROR = 0.001


class Exchanges:
    def __init__(self):
        self.wos_dict = {}
        # for ex_name in ACTIVE_EXCHANGE_LIST:
        #    self.wos_dict[ex_name] = {}
        self.ex_dict = {}
        self.ex_dict["cex"] = Cex(secrets.TEST_CEX_UID, secrets.TEST_CEX_KEY, secrets.TEST_CEX_SECRET)
        self.ex_dict["bittrex"] = Bittrex(secrets.TEST_BITTREX_KEY, secrets.TEST_BITTREX_SECRET)
        self.ex_dict["kraken"] = Kraken(secrets.TEST_KRAKEN_KEY, secrets.TEST_KRAKEN_SECRET)
        self.ex_dict["exmo"] = Exmo(secrets.TEST_EXMO_KEY, secrets.TEST_EXMO_SECRET)

        if settings.GDAX_PRODUCTION:
            self.ex_dict["gdax"] = Gdax(secrets.TEST_GDAX_KEY, secrets.TEST_GDAX_SECRET, secrets.TEST_GDAX_PASSPHRASE)
            #self.ex_dict["gdax"] = Gdax(secrets.LIVE_GDAX_KEY, secrets.LIVE_GDAX_SECRET, secrets.LIVE_GDAX_PASSPHRASE)
        else:
            self.ex_dict["gdax"] = Gdax(secrets.TEST_GDAX_KEY, secrets.TEST_GDAX_SECRET, secrets.TEST_GDAX_PASSPHRASE,url="https://api-public.sandbox.gdax.com")

    ###possibly change to architecture where we have the working orders as objects of the exchange container,
    ###not sure how much it actually matters which things the working orders are a part of

    def create_wo(self, wo_params_dict):
        """
        create a working order and run it in a separate thread
        all necessary arguments are within the working order object itself
        :param wo_params_dict: 
        :return: 
        """
        if len(self.wos_dict) > 0:
            print "len(self.wos_dict) > 0"
            return
        # required_spread, quantity, buy_ex, send_ex
        if wo_params_dict["buy_on"] == wo_params_dict["send_to"]:
            return
        wo_obj = WorkingOrder(wo_params_dict)
        wo_obj.continue_loop = True
        self.wos_dict[wo_obj.external_working_order_id] = wo_obj
        time_readable = datetime.datetime.now().strftime("%m-%d %H:%M")
        wo_dict = {"neg_timestamp": -time.time(), "timestamp": time.time(), "time_readable": time_readable,
                   "wo_id": str(wo_obj.external_working_order_id), "required_spread": str(wo_obj.required_spread),
                   "quantity": str(wo_obj.total_quantity)}
        response = firebase_push_value(["working_orders"], wo_dict)
        t = threading.Thread(target=self.working_thread_general, args=[wo_obj])
        t.start()
        # self.create_wo_log(wo_obj)

    def working_thread_general(self, wo_obj):
        wo_obj.counter = 0
        while True:
            wo_obj.counter += 1
            if not wo_obj.continue_loop:
                self.working_order_log("cancelled continue loop bp 1", wo_obj)
                break

            current_spread = self.get_spread(wo_obj)
            print "current_spread: %s" % current_spread
            print "required_spread: %s" % wo_obj.required_spread
            self.working_order_log("actual_spread: " + str(current_spread), wo_obj)

            if self.check_price_criteria_met(current_spread, wo_obj.required_spread):
                # TODO: hardcoding all currencies to btc for now
                self.initiate_arbitrage(self.ex_dict[wo_obj.buy_on], self.ex_dict[wo_obj.send_to], wo_obj.total_quantity, Currencies.bitcoin)

                break
            else:
                time.sleep(5)

    def initiate_arbitrage(self, buy_on_exchange,  send_to_exchange, amount, currency):
                print "Initiating btc buy order for %s" % amount
                buy_status = buy_on_exchange.buy(currency, amount)
                print buy_status
                print "Waiting for order to complete"
                buy_on_exchange.wait_for_order(buy_status["id"])
                print buy_status

                print "BTC buying on origin exchange done. Getting address of destination exchange on %s" % send_to_exchange.__class__.__name__
                send_to_address = send_to_exchange.get_deposit_address(currency)

                print amount, buy_status["size"]
                assert abs(amount - float(buy_status["size"])) <= ALLOWED_TRADE_TRANSFER_MARGIN_ERROR

                print "Sending %s to address: %s" % (buy_status["size"], send_to_address)
                buy_on_exchange.transfer(currency, amount, send_to_address)
                print "Transfer initiated to bitcoin address %s. Waiting for funds to be available on destinations " \
                      "exchange" % send_to_address

                self.wait_for_transfer(send_to_exchange, currency, amount)

                print "Selling %s on exchange %s" % (buy_status["size"], send_to_exchange.__class__.__name__)
                send_to_exchange.sell(currency, buy_status["size"])

    def wait_for_transfer(self, exchange, currency, amount, wait_poll_time=30):
        """This approach uses a naieve implementation that simply
        busy/waits/polls the balance, waiting to report a change.
        When the balance has changed, the function reports that the
        order has been placed.

        @:param exchange: the destination exchange
        @:param currency: the cryptocurrency to be deposited
        @:param amount: the amount to be deposited
        @:param wait_poll_time: time in seconds to wait between checking exchange current balance

        """
        initial_balance = exchange.get_balance(currency)
        start_time = time.time()
        # block until the balance changes/or timeout
        current_balance = exchange.get_balance(currency)
        estimate_balance_after_transfer = initial_balance + amount * 0.90
        while estimate_balance_after_transfer > current_balance:
            print "Current balance: %s, Expected balance: %s" % (current_balance, estimate_balance_after_transfer)
            current_balance = exchange.get_balance(currency)
            if (time.time() - start_time) > exchange.transfer_time:
                return False
            time.sleep(wait_poll_time)
        return True

    def create_wo_log(self, wo_obj):
        time_readable = datetime.datetime.now().strftime("%m-%d %H:%M")
        log_dict = {"neg_time_unix": -time.time(), "time_unix": time.time(), "time_readable": time_readable,
                    "text": "order id: " + str(wo_obj.external_working_order_id)[
                                           0:6] + " started working cexio with required spread: " + str(
                            wo_obj.required_spread)}
        response = firebase_push_value(["log", wo_obj.buy_ex + "_" + wo_obj.send_ex], log_dict)
        wo_dict = {"neg_timestamp": -time.time(), "timestamp": time.time(), "time_readable": time_readable,
                   "wo_id": str(wo_obj.external_working_order_id), "required_spread": str(wo_obj.required_spread),
                   "quantity": str(wo_obj.total_quantity), "buy_cexio": wo_obj.buy_sell}
        response = firebase_push_value(["working_orders", wo_obj.buy_ex + "_" + wo_obj.send_ex], wo_dict)
        set_in_firebase(["status", wo_obj.buy_ex + "_" + wo_obj.send_ex], "WORKING CEXIO")

    def send_notification_email(self):
        requests.get("https://coin-temple.appspot.com/send_notification_email?code=23123321")

    def check_price_criteria_met(self, current_spread, required_spread):
        return current_spread >= required_spread

    def get_spread(self, wo_obj):
        """
        Returns the spread between the send and buy price, note that we are not taking the absolute value between prices
        Becasue we don't want to be trading when the difference between the exchanges is positive
        """
        send_price = firebase_read_value([wo_obj.send_to.upper(), "prices", "btc", "ask"])
        buy_price = firebase_read_value([wo_obj.buy_on.upper(), "prices", "btc", "ask"])
        actual_spread = 200 * (float(send_price) - float(buy_price)) / (float(send_price) + float(buy_price))
        return actual_spread

    def immed_fill(self, wo_obj, trade_size):
        # TODO:  do we need this method to break from the loop?
        immediate_complete_fill = self.grnt_place_working(wo_obj, trade_size)

        if immediate_complete_fill:
            self.ex_dict["cex"].buy(trade_size)
            print "didn't completely fill, error"
        if immediate_complete_fill == "order not made":
            return "order not made"

    def grnt_place_working(self, wo_obj, work_price_usd):
        return_val = self.ex_dict[wo_obj.buy_ex].place_working_order(wo_obj, work_price_usd)
        return return_val

    def working_order_log(self, wo_log_text, wo_obj):
        """
        For moment to moment logging of working order behavior.
        :param wo_log_text: 
        :param wo_obj: 
        :return: 
        """
        time_readable = datetime.datetime.now().strftime("%m-%d %H:%M")
        wo_log_dict = {"neg_timestamp": -time.time(), "timestamp": time.time(), "time_readable": time_readable,
                       "wo_id": str(wo_obj.external_working_order_id), "text": wo_log_text}
        t = threading.Thread(target=self.record_wo_log_in_firebase,
                             args=[wo_log_dict])
        t.start()
        return

    def record_wo_log_in_firebase(self, wo_log_dict):
        firebase_push_value(["working_order_logs"], wo_log_dict)

    def current_spread_pct(self, ex_label_1, ex_label_2):
        return ((self.ex_dict[ex_label_1].ask_price - self.ex_dict[ex_label_2].ask_price) / self.ex_dict[
            ex_label_1].ask_price) * 100.0

    def record_completed_wo(self, wo_obj):
        work_dict = {"quantity": float(wo_obj.work_just_matched_quantity),
                     "price": float(wo_obj.work_just_matched_price), "name": wo_obj.buy_ex}
        hedge_dict = {"quantity": float(wo_obj.hedge_just_matched_quantity),
                      "price": float(wo_obj.hedge_just_matched_price), "name": wo_obj.send_ex}
        server_time = time.time()
        push_dict = {"server_time": server_time}
        push_dict["work"] = work_dict
        push_dict["hedge"] = hedge_dict
        push_dict["external_working_id"] = str(wo_obj.external_working_order_id)
        if wo_obj.buy_sell == "buy":
            push_dict["plus_minus"] = "+"
        else:
            push_dict["plus_minus"] = "-"
        firebase_push_value(["general_completed_working_orders"], push_dict)
