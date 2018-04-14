import hashlib
import hmac
import http.client
import json
import sys
import time
from urllib import urlencode

from GCE.currency_classes.abstract import Currencies
from GCE.currency_classes.bitcoin.bitcoin import Bitcoin
from GCE.currency_classes.ethereum.ethereum import Ethereum
from GCE.currency_classes.ethereum_classic.ethereum_classic import EthereumClassic
from GCE.currency_classes.litecoin.litecoin import Litecoin

from ..abstract import Exchange


class Exmo(Exchange):
    """This class wraps the EXMO change API. Specifications for the API
    can be found at: https://exmo.com/en/api.
    """
    
    def __init__(self, api_key, api_secret, api_url='api.exmo.com', api_version='v1'):
        """This method will instantiate a EXMO object which can perform
        EXMO API operations on behalf of the user.
        
        :param API_KEY: The API Key
        :param API_SECRET: The API Secret
        :param API_URL: The API URL, optional
        :param API_VERSION: The API version, optional
        :returns: Returns an EXMO exchange object
        :rtype: ExmoAPI
        
        """
        self.currencies = {
            Currencies.bitcoin: Bitcoin(),
            Currencies.ethereum: Ethereum(),
            Currencies.ethereum_classic: EthereumClassic(),
            Currencies.litecoin: Litecoin()
        }
        self.api_url = api_url
        self.api_version = api_version
        self.api_key = api_key
        self.api_secret = api_secret
    
    def sha512(self, data):
        H = hmac.new(key=self.api_secret, digestmod=hashlib.sha512)
        H.update(data.encode('utf-8'))
        return H.hexdigest()
    
    def api_query(self, api_method, params={}):
        """Translates an API method and a set of parameters (arguments) to a
        request which is invoked on the EXMO web API
        
        :param api_method: The method to invoke
        :param params: The arguments (Passed as a dictionary of key:value pairs)
        :returns: A json decoded response from the remote server
        :rtype: object
        
        """
        params['nonce'] = int(round(time.time() * 1000))
        params = urlencode(params)
        
        sign = self.sha512(params)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Key": self.api_key,
            "Sign": sign
        }
        conn = http.client.HTTPSConnection(self.api_url)
        conn.request("POST", "/" + self.api_version + "/" + api_method, params, headers)
        response = conn.getresponse().read()
        
        conn.close()
        
        try:
            obj = json.loads(response.decode('utf-8'))
            if 'error' in obj and obj['error']:
                print(obj['error'])
                raise sys.exit()
            return obj
        except json.decoder.JSONDecodeError:
            print('Error while parsing response:', response)
            raise sys.exit()
    
    def buy(self, currency, amount):
        """Method to place a buy market order
        
        :param currency: Currencies enum currency to buy
        :param amount: amount btc to be bought
        :return: Response from the server
        
        """
        response = self.api_query("order_create",
                              {
                                  "pair": self.currencies[currency].identifier + "_USD",
                                  "quantity": amount,
                                  "price": 0,
                                  "type": "market_buy"
                              })
        return {"id": response["order_id"], "size": amount, "raw": response}
    
    def sell(self, currency, amount):
        """Generic method to place a sell market order
        
        :param currency: Currencies enum currency to sell
        :param amount: amount to be sold
        :return:
        
        """
        return self.api_query("order_create",
                              {
                                  "pair": self.currencies[currency].identifier + "_USD",
                                  "quantity": amount,
                                  "price": 0,
                                  "type": "market_sell"
                              })
    
    def transfer(self, currency, amount, address):
        """Generic method to transfer a btc to the given address
        
        :param amount: amount btc to be transfered
        :param address: hash of the destination address
        :return:
        
        """
        return self.api_query("withdraw_crypt",
                              {
                                  "amount": amount,
                                  "currency": self.currencies[currency].identifier,
                                  "address": address,
                                  "invoice": "1234"  # required for ripple (XRP)
                              })
    
    def get_deposit_address(self, currency):
        """Returns the hash of the address to be used for depositing btc
        for the exchange
        
        :return: Return the deposit address for a BTC Wallet
        
        """
        return self.api_query("deposit_address", {})
    
    def get_balance(self, currency):
        """Returns the balance for a given currency. EXMO returns all
        available currencies even if there is no balance, so there is
        no need to see if a key exists in the result dictionary.
        
        A sample response looks like this: {u'DASH': u'0', u'USD':
        ...
        u'USDT': u'0', u'XRP': u'0', u'XMR' : u'0', u'EUR': u'0'}
        
        :param currency:
        :returns: balance of a given currency
        :rtype: int
        """
        return self.api_query("user_info")["balances"][self.currencies[currency].identifier]
    
    def wait_for_order(self, order_id):
        """When an order is placed in an exchange, it's not guaranteed to be
        fulfilled immediately this method blocks excecution until the
        order is fulfilled.
        
        :param order_id:
        :return:
        
        """
        return order_id
    
    def return_transaction_from_address(self, address, amount):
        """Some exchanges (Ex: gdax) don't return the blockchain transaction
        hash immediately, this method blocks execution and returns the
        transaction hash for a given address
        
        :param address: hash of the address
        :param amount: original btc amount sent
        :return: transaction hash for a given_address
        
        """
        raise NotImplementedError
