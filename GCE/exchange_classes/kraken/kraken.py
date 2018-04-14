# This file is part of krakenex.
#
# krakenex is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# krakenex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser
# General Public LICENSE along with krakenex. If not, see
# <http://www.gnu.org/licenses/gpl-3.0.txt>.


import base64
# private query signing
import hashlib
import hmac
import json
# private query nonce
import time
import urllib

import connection

from ..abstract import Exchange
from GCE.currency_classes.abstract import Currencies
from GCE.currency_classes.bitcoin.bitcoin import Bitcoin
from GCE.currency_classes.ethereum.ethereum import Ethereum
from GCE.currency_classes.ethereum_classic.ethereum_classic import EthereumClassic
from GCE.currency_classes.litecoin.litecoin import Litecoin


class Kraken(Exchange):
    """Kraken.com cryptocurrency Exchange API.
    
    Public methods:
    load_key
    query_public
    query_private
    
    """
    
    def __init__(self, key, secret):
        """Create an object with authentication information.
        
        Arguments:
        key    -- key required to make queries to the API (default: '')
        secret -- private key used to sign API messages (default: '')
        
        """
        self.key = key
        self.secret = secret
        self.uri = 'https://api.kraken.com'
        self.apiversion = '0'
        self.buy_poll_time = 0.2
        self.currencies = {
            Currencies.bitcoin: Bitcoin(),
            Currencies.ethereum: Ethereum(),
            Currencies.ethereum_classic: EthereumClassic(),
            Currencies.litecoin: Litecoin()
        }
        
        self.currencies[Currencies.bitcoin].usd_pair = "XXBTZUSD"
        self.currencies[Currencies.ethereum].usd_pair = "ETHUSD"
        self.currencies[Currencies.ethereum_classic].usd_pair = "ETCUSD"
        self.currencies[Currencies.litecoin].usd_pair = "LTCUSD"
    
    def load_key(self, path):
        """Load key and secret from file.
        
        Argument:
        path -- path to file (string, no default)
        
        """
        with open(path, "r") as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()
    
    def _query(self, urlpath, req={}, conn=None, headers={}):
        """Low-level query handling.
        
        Arguments:
        urlpath -- API URL path sans host (string, no default)
        req     -- additional API request parameters (default: {})
        conn    -- kraken.Connection object (default: None)
        headers -- HTTPS headers (default: {})
        
        """
        url = self.uri + urlpath
        
        if conn is None:
            conn = connection.Connection()
            
        ret = conn._request(url, req, headers)
        return json.loads(ret)
    
    def query_public(self, method, req={}, conn=None):
        """API queries that do not require a valid key/secret pair.
        
        Arguments:
        method -- API method name (string, no default)
        req    -- additional API request parameters (default: {})
        conn   -- connection object to reuse (default: None)
        
        """
        urlpath = '/' + self.apiversion + '/public/' + method
        
        return self._query(urlpath, req, conn)
    
    def query_private(self, method, req={}, conn=None):
        """API queries that require a valid key/secret pair.
        
        Arguments:
        method -- API method name (string, no default)
        req    -- additional API request parameters (default: {})
        conn   -- connection object to reuse (default: None)
        
        """
        urlpath = '/' + self.apiversion + '/private/' + method
        
        req['nonce'] = int(1000 * time.time())
        postdata = urllib.urlencode(req)
        message = urlpath + hashlib.sha256(str(req['nonce']) +
                                           postdata).digest()
        signature = hmac.new(base64.b64decode(self.secret),
                             message, hashlib.sha512)
        headers = {
            'API-Key': self.key,
            'API-Sign': base64.b64encode(signature.digest())
        }
        
        return self._query(urlpath, req, conn, headers)
    
    def buy(self, currency, amount):
        """
        Method to place a buy market order
        
        :param amount: amount btc to be bought
        :return: Response from the server
        
        """
        parameters = {
            "pair": self.currencies[currency].usd_pair,
            "type": "buy",
            "ordertype": "market",
            "volume": amount,
            "post": "viqc"
        }
        response = self.query_private("AddOrder", parameters)
        order_details = self.get_order(response["result"]["txid"][0])
        return {"id": response["result"]["txid"][0], "size": order_details["vol"]}
    
    def sell(self, currency, amount):
        """
        Generic method to place a sell market order
        
        :param amount: amount btc to be sold
        :return:
        
        """
        parameters = {
            "pair": self.currencies[currency].usd_pair,
            "type": "sell",
            "ordertype": "market",
            "volume": amount,
            "oflags": "viqc"
        }
        
        return self.query_private("AddOrder", parameters)
    
    def transfer(self, currency, amount, address):
        """Generic method to transfer a currency to the given address
        
        :param amount: amount to be transfered
        :param address: hash of the destination address
        :return:

        """
        parameters = {
            "aclass": self.currencies[currency].identifier,
            "asset": "USD",
            "key": address,
            "amount": amount
        }
        return self.query_private("Withdraw", parameters)
    
    def get_deposit_address(self, currency):
        """Returns the hash of the address to be used for depositing btc
        for the exchange
        
        :return: Return the deposit address for a BTC Wallet
        
        """
        parameters = {
            #"aclass": self.currencies[currency].identifier,
            #"asset": "USD",
            "method": "btc",  # fixme
        }
        response = self.query_private("DepositMethods", parameters)
        return response["address"]
    
    def get_balance(self, currency):
        """Returns the current available balance of the given currency.
        The Kraken API only returns balances for those accounts which
        have money. Therefore if the user does not have any BTC, there
        will be no BTC key in the result dictionary.
        
        The response in this case will look like this: {u'result': {}, u'error': []}
        For this reason, the API will check for the existence of a key
        in the result, and if it does not exist, will return a value of 0.
        
        :param currency:
        :return: float of the current available balance
        
        """
        query_result = self.query_private("Balance", {})["result"]
        try:
            return query_result[self.currencies[currency].identifier]
        except KeyError:
            # specified currency does not have a balance
            return 0
    
    def get_order(self, order_id):
        """
        
        :param order_id:
        :return: "closed" or "open"
        """
        parameters = {"txid": order_id}
        return self.query_private("QueryOrders", parameters)["result"][order_id]
    
    def wait_for_order(self, order_id):
        """
        When an order is placed in an exchange, it's not guarenteed to be
        fulfilled immediately this method blocks excecution until the
        order is fulfilled
        
        :param order_id:
        :return:
        
        """
        order = self.get_order(order_id)
        while order["status"] != "closed":
            time.sleep(self.buy_poll_time)
            order = self.get_order(order_id)
        return order
    
    def return_transaction_from_address(self, address, amount):
        """
        Some exchanges (Ex: gdax) don't return the blockchain transaction
        hash immediately, this method blocks execution and returns the
        transaction hash for a given address
        
        :param address: hash of the address
        :param amount: original btc amount sent
        :return: transaction hash for a given_address
        
        """
        raise NotImplementedError
