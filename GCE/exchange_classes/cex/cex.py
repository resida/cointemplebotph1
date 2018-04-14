# https://github.com/matveyco/cex.io-api-python

"""
    See https://cex.io/rest-api
"""

import hashlib
import hmac
import json
import time

from GCE.currency_classes.abstract import Currencies
from GCE.currency_classes.bitcoin.bitcoin import Bitcoin
from GCE.currency_classes.ethereum.ethereum import Ethereum
from GCE.currency_classes.ethereum_classic.ethereum_classic import EthereumClassic
from GCE.currency_classes.litecoin.litecoin import Litecoin

import requests

from ..abstract import Exchange


CEX_BUY_POLL_TIME = 0.2
BASE_URL = 'https://cex.io/api/%s/'

PUBLIC_COMMANDS = {
    'currency_limits',
    'ticker',
    'last_price',
    'last_prices',
    'convert',
    'price_stats',
    'order_book',
    'trade_history'
}


class Cex(Exchange):
    def __init__(self, username, api_key, api_secret):
        self.currencies = {
            Currencies.bitcoin: Bitcoin("BTC", 3),
            Currencies.ethereum: Ethereum(),
            Currencies.ethereum_classic: EthereumClassic(),
            Currencies.litecoin: Litecoin()
        }
        
        self.next_call_time = 0
        self.username = username
        self.api_key = api_key
        self.api_secret = api_secret
        self.ask_price = 0
        self.bid_price = 0
        self.continue_threads = True
        self.start_time = time.time()
        self.test_mode_active = False
        
        num_confs_btc = 3  # CEX requires 6 confirmations to confirm deposit
        super(Cex, self).__init__(num_confs_btc=num_confs_btc)

    @property
    def __nonce(self):
        while time.time() < self.next_call_time:
            time.sleep(.03)
        nonce = str(int(time.time() * 1000) + 200000)
        self.next_call_time = time.time() + .41
        return nonce

    # can use something v similar for websocket
    def __signature(self, nonce):
        message = nonce + self.username + self.api_key
        signature = hmac.new(bytearray(self.api_secret.encode('utf-8')), message.encode('utf-8'),
                             digestmod=hashlib.sha256).hexdigest().upper()
        return signature

    def __post(self, url, param):
        result = requests.post(url, data=param, headers={'User-agent': 'bot-cex.io-' + self.username})
        result.raise_for_status()
        return result.json()

    def api_call(self, command="", action="", param={}, **kwargs):
        """
        :param command: Query command for getting info
        :type commmand: str
        :param param: Extra options for query
        :type options: dict
        :return: JSON response from CEX.IO
        :rtype : dict
        """
        
        if command not in PUBLIC_COMMANDS:
            nonce = self.__nonce
            param.update({
                'key': self.api_key,
                'signature': self.__signature(nonce),
                'nonce': nonce
            })
        
        request_url = (BASE_URL % command) + action
        result = self.__post(request_url, param)
        return result

    def wait_for_order(self, order_id):
        """
        "c" - canceled (not executed)
        "cd" - cancel-done (partially executed)
        "d" - done (fully executed) "a" - active."
        """
        order = self.get_order(order_id)
        while order["status"] != "d":
            time.sleep(CEX_BUY_POLL_TIME)
        assert order["status"] == "d"
        return order

    def get_order(self, order_id):
        return self.api_call(command='get_order_tx', param={"id", order_id})

    def update_ticker(self):
        return_val = self.ticker()
        self.ask_price = return_val["ask"]
        self.bid_price = return_val["bid"]

    def get_ask_price(self):
        return self.ask_price

    def get_bid_price(self):
        return self.bid_price

    def ticker(self, market='BTC/USD'):
        """
        :param market: String literal for the market (ex: BTC/ETH)
        :type market: str
        :return: Current values for given market in JSON
        :rtype : dict
        """
        return self.api_call(command='ticker', param=None, action=market)

    @property
    def balance(self):
        return self.api_call(command='balance')

    @property
    def get_myfee(self):
        return self.api_call(command='get_myfee')

    def get_deposit_address(self, currency):
        parameters = {'currency': self.currencies[currency].identifier,
                      'nonce': self.__nonce}
        r = self.api_call(command='get_address', param=parameters)
        return r["data"]
    
    @property
    def currency_limits(self):
        return self.api_call(command='currency_limits')

    def open_orders(self):
        return self.api_call(command='open_orders')

    def active_order_status(self):
        orders_list = {'orders_list': self.ids_should_be_in_open_orders()}
        return self.api_call(command='active_orders_status', param=orders_list)

    def cancel_order(self, order_id, wo_id=''):
        return self.api_call(wo_id=wo_id, command='cancel_order', param={'id': order_id})

    def cancel_orders(self, market='BTC/USD'):
        return self.api_call(command='cancel_orders', action=market)

    def buy(self, currency, amount):
        currency_identifier = self.currencies[currency].identifier
        market_price = self.order_book(market=currency_identifier + "/USD")["bids"][0][0]
        params = {
            'type': "buy",
            'amount': amount,
            'price': market_price}
        
        return self.api_call(command='place_order', param=params, action=currency_identifier + "/USD")

    def sell(self, currency, amount):
        currency_identifier = self.currencies[currency].identifier
        market_price = self.order_book(market=currency_identifier + "/USD")["bids"][0][0]
        params = {
            'type': "sell",
            'amount': amount,
            'price': market_price}
        
        return self.api_call(command='place_order', param=params, action=currency_identifier + "/USD")
    
    def get_balance(self, currency):
        """Returns the current available balance of the given currency.
        The CEX API only returns balances for those accounts which
        have money. Therefore if the user does not have any BTC, there
        will be no BTC key in the result dictionary.
        
        :param currency:
        :return: float of the current available balance
        
        """
        account_balances = self.api_call(command='balance')
        try:
            return float(account_balances[self.currencies[currency].identifier]["available"])
        except KeyError:
            # specified currency does not have a balance
            return 0

    def sell_limit_order(self, wo_uuid, amount, price, market='BTC/USD'):
        params = {
            'type': 'sell',
            'amount': amount,
            'price': price
        }
        
        return self.api_call(wo_id=wo_uuid, command='place_order', param=params, action=market)

    def open_positions(self, market='BTC/USD'):
        return self.api_call(command='open_positions', action=market)

    def close_position(self, position_id, market='BTC/USD'):
        return self.api_call(command='close_position', param={'id': position_id}, action=market)

    def get_order(self, order_id, wo_id=''):
        return self.api_call(wo_id=wo_id, command='get_order', param={'id': order_id})

    def order_book(self, depth=1, market='BTC/USD'):
        return self.api_call(command='order_book', action=market + '/?depth=' + str(depth))

    def trade_history(self, since=1, market='BTC/USD'):
        return self.api_call(command='trade_history', action=market + '/?since=' + str(since))
