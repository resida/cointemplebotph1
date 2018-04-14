import base64
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
from requests.auth import AuthBase

from ..abstract import Exchange
from ..blockcypher import get_most_recent_unnconfirmed_txn


class Gdax(Exchange):
    def __init__(self, key, b64secret, passphrase, url='https://api.gdax.com', *args, **kwargs):
        self.currencies = {
            Currencies.bitcoin: Bitcoin("BTC", 6),  # GDAX requires 6 deposit confirmations
            Currencies.ethereum: Ethereum(),
            Currencies.ethereum_classic: EthereumClassic(),
            Currencies.litecoin: Litecoin()
        }
        self.url = url
        self.auth = GdaxAuth(key, b64secret, passphrase)
        self.buy_poll_time = 0.2
    
    def get_account(self, account_id):
        r = requests.get(self.url + '/accounts/' + account_id, auth=self.auth)
        return r.json()
    
    def get_accounts(self):
        return self.get_account('')
    
    def get_account_history(self, account_id):
        result = []
        r = requests.get(self.url + '/accounts/{}/ledger'.format(account_id), auth=self.auth)
        result.append(r.json())
        if "cb-after" in r.headers:
            self.history_pagination(account_id, result, r.headers["cb-after"])
        return result
    
    def history_pagination(self, account_id, result, after):
        r = requests.get(self.url + '/accounts/{}/ledger?after={}'.format(account_id, str(after)), auth=self.auth)
        if r.json():
            result.append(r.json())
        if "cb-after" in r.headers:
            self.history_pagination(account_id, result, r.headers["cb-after"])
        return result
    
    def get_account_holds(self, account_id):
        result = []
        r = requests.get(self.url + '/accounts/{}/holds'.format(account_id), auth=self.auth)
        result.append(r.json())
        if "cb-after" in r.headers:
            self.holds_pagination(account_id, result, r.headers["cb-after"])
        return result
    
    def holds_pagination(self, account_id, result, after):
        r = requests.get(self.url + '/accounts/{}/holds?after={}'.format(account_id, str(after)), auth=self.auth)
        if r.json():
            result.append(r.json())
        if "cb-after" in r.headers:
            self.holds_pagination(account_id, result, r.headers["cb-after"])
        return result
    
    def buy(self, currency, amount):
        return self.place_order(amount, "buy", self.currencies[currency].identifier)
    
    def buy_btc(self, amount):
        return self.buy(Currencies.bitcoin, amount)
    
    def sell(self, currency, amount):
        return self.place_order(amount, "sell", self.currencies[currency].identifier)
    
    def sell_btc(self, amount):
        return self.buy(Currencies.bitcoin, amount)
    
    def place_order(self, amount, order_type, product_id):
        """This functions pings the gdax exchange and places a market order
        for the amount of product_id provided
        
        """
        data = {}
        data["side"] = order_type
        data["product_id"] = product_id + "-USD"
        data["size"] = amount
        data["type"] = "market"
        r = requests.post(self.url + '/orders',
                          data=json.dumps(data),
                          auth=self.auth)
        print r.json()
        r.raise_for_status()
        return r.json()
    
    def transfer_btc(self, amount, address):
        payload = {
            "amount": amount,
            "currency": "BTC",
            "crypto_address": address
        }
        r = requests.post(self.url + "/withdrawals/crypto", data=json.dumps(payload), auth=self.auth)
        r.raise_for_status()
        
        return r.json()
    
    def transfer(self, currency, amount, address):
        payload = {
            "amount": amount,
            "currency": self.currencies[currency].identifier,
            "crypto_address": address
        }
        return requests.post(self.url + "/withdrawals/crypto", data=json.dumps(payload), auth=self.auth)
    
    def get_deposit_address(self, currency):
        """The deposit address returned is *not* a cryptocurrency wallet
        address. It is an identifier used to deposit money into a GDAX
        trading account.
        
        Deposit requests take the form:
        {
            "amount": 10.00,
            "currency": "USD",
            "payment_method_id": "bc677162-d934-5f1a-968c-a496b1c1270b"
        }
        
        Source: https://docs.gdax.com/#deposits
        
        """
        r = requests.post(self.url + "/payment-methods", data=None, auth=self.auth)
        payment_methods = json.loads(r.json())
        for payment_method in payment_methods:
            if payment_method["currency"] == self.currencies[currency].identifier:
                return payment_method["id"]
    
    def get_balance(self, currency):
        for account in self.get_accounts():
            if account["currency"] == self.currencies[currency].identifier:
                return account["balance"]
    
    def return_transaction_from_address(self, address, amount):
        return get_most_recent_unnconfirmed_txn(address, amount)
        
    def wait_for_order(self, order_id):
        """Here is a naive implementation to wait for a GDAX order to
        complete, in the future, we can consider using GDAX's webhooks
        instead of doing long polling
        """
        order = self.get_order(order_id)
        while order["status"] != "done":
            time.sleep(self.buy_poll_time)
            order = self.get_order(order_id)
        assert order["status"] == "done"
        return order
    
    def cancel_order(self, order_id):
        r = requests.delete(self.url + '/orders/' + order_id, auth=self.auth)
        return r.json()
    
    def cancel_all(self, data=None, product=''):
        if type(data) is dict:
            if "product" in data:
                product = data["product"]
        r = requests.delete(self.url + '/orders/',
                            data=json.dumps({'product_id': product or self.product_id}), auth=self.auth)
        return r.json()
    
    def get_order(self, order_id):
        r = requests.get(self.url + '/orders/' + order_id, auth=self.auth)
        return r.json()
    
    def get_orders(self):
        result = []
        r = requests.get(self.url + '/orders/', auth=self.auth)
        result.append(r.json())
        if 'cb-after' in r.headers:
            self.paginate_orders(result, r.headers['cb-after'])
        return result
    
    def paginate_orders(self, result, after):
        r = requests.get(self.url + '/orders?after={}'.format(str(after)), auth=self.auth)
        if r.json():
            result.append(r.json())
        if 'cb-after' in r.headers:
            self.paginate_orders(result, r.headers['cb-after'])
        return result
    
    def get_fills(self, order_id='', product_id='', before='', after='', limit=''):
        result = []
        url = self.url + '/fills?'
        if order_id:
            url += "order_id={}&".format(str(order_id))
        if product_id:
            url += "product_id={}&".format(product_id or self.product_id)
        if before:
            url += "before={}&".format(str(before))
        if after:
            url += "after={}&".format(str(after))
        if limit:
            url += "limit={}&".format(str(limit))
        r = requests.get(url, auth=self.auth)
        result.append(r.json())
        if 'cb-after' in r.headers and limit is not len(r.json()):
            return self.paginate_fills(result, r.headers['cb-after'], order_id=order_id, product_id=product_id)
        return result
    
    def paginate_fills(self, result, after, order_id='', product_id=''):
        url = self.url + '/fills?after={}&'.format(str(after))
        if order_id:
            url += "order_id={}&".format(str(order_id))
        if product_id:
            url += "product_id={}&".format(product_id or self.product_id)
        r = requests.get(url, auth=self.auth)
        if r.json():
            result.append(r.json())
        if 'cb-after' in r.headers:
            return self.paginate_fills(result, r.headers['cb-after'], order_id=order_id, product_id=product_id)
        return result
    
    def get_fundings(self, result='', status='', after=''):
        if not result:
            result = []
        url = self.url + '/funding?'
        if status:
            url += "status={}&".format(str(status))
        if after:
            url += 'after={}&'.format(str(after))
        r = requests.get(url, auth=self.auth)
        # r.raise_for_status()
        result.append(r.json())
        if 'cb-after' in r.headers:
            return self.get_fundings(result, status=status, after=r.headers['cb-after'])
        return result
    
    def repay_funding(self, amount='', currency=''):
        payload = {
            "amount": amount,
            "currency": currency  # example: USD
        }
        r = requests.post(self.url + "/funding/repay", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def margin_transfer(self, margin_profile_id="", transfer_type="", currency="", amount=""):
        payload = {
            "margin_profile_id": margin_profile_id,
            "type": transfer_type,
            "currency": currency,  # example: USD
            "amount": amount
        }
        r = requests.post(self.url + "/profiles/margin-transfer", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def get_position(self):
        r = requests.get(self.url + "/position", auth=self.auth)
        return r.json()
    
    def close_position(self, repay_only=""):
        payload = {
            "repay_only": repay_only or False
        }
        r = requests.post(self.url + "/position/close", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def deposit(self, amount="", currency="", payment_method_id=""):
        payload = {
            "amount": amount,
            "currency": currency,
            "payment_method_id": payment_method_id
        }
        r = requests.post(self.url + "/deposits/payment-method", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def coinbase_deposit(self, amount="", currency="", coinbase_account_id=""):
        payload = {
            "amount": amount,
            "currency": currency,
            "coinbase_account_id": coinbase_account_id
        }
        r = requests.post(self.url + "/deposits/coinbase-account", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def withdraw(self, amount="", currency="", payment_method_id=""):
        payload = {
            "amount": amount,
            "currency": currency,
            "payment_method_id": payment_method_id
        }
        r = requests.post(self.url + "/withdrawals/payment-method", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def coinbase_withdraw(self, amount="", currency="", coinbase_account_id=""):
        payload = {
            "amount": amount,
            "currency": currency,
            "coinbase_account_id": coinbase_account_id
        }
        r = requests.post(self.url + "/withdrawals/coinbase", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def crypto_withdraw(self, amount="", currency="", crypto_address=""):
        payload = {
            "amount": amount,
            "currency": currency,
            "crypto_address": crypto_address
        }
        r = requests.post(self.url + "/withdrawals/crypto", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def get_payment_methods(self):
        r = requests.get(self.url + "/payment-methods", auth=self.auth)
        return r.json()
    
    def get_coinbase_accounts(self):
        r = requests.get(self.url + "/coinbase-accounts", auth=self.auth)
        return r.json()
    
    def create_report(self, report_type="", start_date="",
                      end_date="", product_id="", account_id="",
                      report_format="", email=""):
        payload = {
            "type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "product_id": product_id,
            "account_id": account_id,
            "format": report_format,
            "email": email
        }
        r = requests.post(self.url + "/reports", data=json.dumps(payload), auth=self.auth)
        return r.json()
    
    def get_report(self, report_id=""):
        r = requests.get(self.url + "/reports/" + report_id, auth=self.auth)
        return r.json()
    
    def get_trailing_volume(self):
        r = requests.get(self.url + "/users/self/trailing-volume", auth=self.auth)
        return r.json()


class GdaxAuth(AuthBase):
    """Provided by gdax: https://docs.gdax.com/#signing-a-message
    """
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
