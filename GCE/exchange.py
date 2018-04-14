import requests
#from ws_gdax import OrderBook, MyOrderBook
from GCE.exchange_classes.cex.ws_cexio import CexioWebsocket

CEX_REST_API_URL = u'https://cex.io/api/%s/'
CEX_WS_API_URL = u'wss://ws.cex.io/ws/'

GDAX_REST_API_URL = u'https://api.gdax.com'
GDAX_WS_API_URL = u'wss://ws-feed.gdax.com'

class Exchanges_API(object):
    def __init__(self, rest_api_url=None, ws_api_url=None, products=None):
        self.ws_api_url = ws_api_url
        self.rest_api_url = rest_api_url
        self.products = products  # defaults currency pair (ie..BTC/USD) to none

    def get_products(self):
        return


class GDAX_API(Exchanges_API):
    def __init__(self):
        super(Exchanges_API, self).__init__()
        self.rest_api_url = GDAX_REST_API_URL.rstrip('/')
        self.ws_api_url = GDAX_WS_API_URL.rstrip('/')
        self.products = None
        self.global_order_book = None
        self.my_order_book = None
        #self.message_type = "subscribe"

    def get_products(self):
        products = requests.get(self.rest_api_url + '/products')
        self.products = products.json()
        # r.raise_for_status()
        return self.products

    def get_global_order_book(self):
        return
        #self.global_order_book = OrderBook()
        #return self.global_order_book

    def get_my_order_book(self):
        return
        #self.my_order_book = MyOrderBook()
        #return self.my_order_book

class CEX_API(Exchanges_API):
    def __init__(self):
        super(Exchanges_API, self).__init__()
        self.rest_api_url = CEX_REST_API_URL.rstrip('/')
        self.ws_api_url = CEX_WS_API_URL.rstrip('/')
        self.products = None
        self.global_order_book = None
        #self.message_type = "subscribe"

    def get_products(self):
        products = 'will input this manually' #todo
        # r.raise_for_status()
        return products

    def get_global_order_book(self):
        self.global_order_book = CexioWebsocket().make_order_dicts()
        #print self.get_global_order_book
        return self.global_order_book


gdax = GDAX_API()
cex = CEX_API()
print gdax.rest_api_url
print gdax.get_products()
print cex.get_global_order_book()
#print gdax.get_order_book()

