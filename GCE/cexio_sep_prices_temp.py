import httplib
# from exmo import ExmoAPI
import urllib

import ccxt

from exchange_classes.bittrex.bittrex import *
# def __init__(self, key, b64secret, passphrase, api_url="https://api.gdax.com"):
from exchange_classes.cex.cex import Cex
from exchange_classes.gdax.gdax import Gdax
from secrets import TEST_CEX_KEY, TEST_CEX_SECRET, TEST_CEX_UID, \
    TEST_GDAX_KEY, TEST_GDAX_SECRET, TEST_GDAX_PASSPHRASE, TEST_EXMO_KEY, TEST_EXMO_SECRET, TEST_BITTREX_KEY, \
    TEST_BITTREX_SECRET, TEST_KRAKEN_KEY, TEST_KRAKEN_SECRET
from firebase import set_child_value

gdax_global = Gdax(TEST_GDAX_KEY, TEST_GDAX_SECRET, TEST_GDAX_PASSPHRASE)
cex_global = Cex(TEST_CEX_UID, TEST_CEX_KEY, TEST_CEX_SECRET)
my_bittrex = Bittrex(TEST_BITTREX_KEY, TEST_BITTREX_SECRET)
krk_global = ccxt.kraken({
    'apiKey': TEST_KRAKEN_KEY,
    'secret': TEST_KRAKEN_SECRET
})
#exmo_global = ExmoAPI(TEST_EXMO_KEY, TEST_EXMO_SECRET)
def RRR():

    api_key = TEST_EXMO_KEY
    api_secret = TEST_EXMO_SECRET
    nonce = int(round(time.time() * 1000))
    params = {"nonce": nonce}
    params = urllib.urlencode(params)
    H = hmac.new(api_secret, digestmod=hashlib.sha512)
    H.update(params)
    sign = H.hexdigest()
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key": api_key,
               "Sign": sign}
    conn = httplib.HTTPSConnection("api.exmo.com")
    conn.request("POST", "/v1/user_info", params, headers)
    response = conn.getresponse()
    return_val = json.load(response)
    conn.close()
    return return_val

def prices():
    try:
        response = requests.get("https://bittrex.com/api/v1.1/public/getmarketsummary?market=usdt-btc")
        json_r = json.loads(response.text)
        result_dict = json_r["result"][0]
        bid = result_dict["Bid"]
        ask = result_dict["Ask"]
        firebase_dict = {
            "bid": bid,
            "ask": ask,
            "last_update_time": time.time()
        }
        set_child_value(["BITTREX", "prices", "btc"], firebase_dict)
        response = requests.get("https://api.exmo.com/v1/ticker/")
        json_r = json.loads(response.text)
        btscusd_dict = json_r["BTC_USD"]
        bid = btscusd_dict["buy_price"]
        ask = btscusd_dict["sell_price"]
        firebase_dict = {
            "bid": bid,
            "ask": ask,
            "last_update_time": time.time()
        }
        set_child_value(["EXMO", "prices", "btc"], firebase_dict)
        response = requests.get("https://api.kraken.com/0/public/Trades?pair=XBTUSD")
        json_r = json.loads(response.text)
        result_dict = json_r["result"]["XXBTZUSD"]
        bid = result_dict[0][0]
        ask = result_dict[0][0]
        firebase_dict = {
            "bid": bid,
            "ask": ask,
            "last_update_time": time.time()
        }
        set_child_value(["KRAKEN", "prices", "btc"], firebase_dict)
        response = requests.get("https://cex.io/api/ticker/BTC/USD")
        json_r = json.loads(response.text)
        bid = json_r["bid"]
        ask = json_r["ask"]
        firebase_dict = {
            "bid": bid,
            "ask": ask,
            "last_update_time": time.time()
        }
        set_child_value(["CEX", "prices", "btc"], firebase_dict)
        response = requests.get("https://api.gdax.com/products/BTC-USD/ticker")
        json_r = json.loads(response.text)
        bid = json_r["bid"]
        ask = json_r["ask"]
        firebase_dict = {
            "bid": bid,
            "ask": ask,
            "last_update_time": time.time()
        }
        set_child_value(["GDAX", "prices", "btc"], firebase_dict)
    except:
        print "prices"
        time.sleep(2)

def balances():
    try:
        cexio_balances = cex_global.balance
        usd_avail = float(cexio_balances["USD"]["available"])
        btc_avail = float(cexio_balances["BTC"]["available"])
        usd_orders = float(cexio_balances["USD"]["orders"])
        btc_orders = float(cexio_balances["BTC"]["orders"])
        set_child_value(["CEX", "positions", "total", "USD"], usd_avail + usd_orders)
        set_child_value(["CEX", "positions", "total", "BTC"], btc_avail + btc_orders)

    except:
        print "cexio_balances"

    try:
        gdax_balances = gdax_global.get_position()
        usd_avail = float(gdax_balances['accounts']['USD']['balance'])
        btc_avail = float(gdax_balances['accounts']['BTC']['balance'])
        set_child_value(["GDAX", "positions", "total", "USD"], usd_avail)
        set_child_value(["GDAX", "positions", "total", "BTC"], btc_avail)


    except:
        print "gdax_balances"

    try:
        exmo_balances = RRR()
        usd_avail = float(exmo_balances['reserved']['USD'])
        btc_avail = float(exmo_balances['reserved']['BTC'])
        set_child_value(["EXMO", "positions", "total", "USD"], usd_avail)
        set_child_value(["EXMO", "positions", "total", "BTC"], btc_avail)

    except:
        print "exmo"


    try:
        
        usd_avail = my_bittrex.get_balance('USDT')
        btc_avail = my_bittrex.get_balance('BTC')

        set_child_value(["BITTREX", "positions", "total", "USD"], usd_avail["result"]["Available"])
        set_child_value(["BITTREX", "positions", "total", "BTC"], btc_avail["result"]["Available"])
        

    except:
        print "bittrex"

    try:
        result = krk_global.fetch_balance()
        #{'info': {}, 'total': {}, 'used': {}, 'free': {}}
        if "USD" in result["total"]:
            usdavail = result["total"]["USD"]
        else:
            usdavail = 0
        if "BTC" in result["total"]:
            btcavail = result["total"]["BTC"]
        else:
            btcavail = 0
        set_child_value(["KRAKEN", "positions", "total", "USD"], usdavail)
        set_child_value(["KRAKEN", "positions", "total", "BTC"], btcavail)
    except:
        print "kraken"

    #set_child_value(["CEX", "balances"], firebase_dict)

while True:
    prices()
    balances()

    time.sleep(2)
