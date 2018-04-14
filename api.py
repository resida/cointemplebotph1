import cexio
import gdax
#from models import Exchange
from secrets import gdax_api_passphrase, gdax_api_pubkey, gdax_api_privkey, cex_api_user_id, cex_api_pubkey, cex_api_privkey

######runs once right now

gdax_api = gdax.AuthenticatedClient(gdax_api_pubkey, gdax_api_privkey, gdax_api_passphrase)
#gdax_api = gdax.AuthenticatedClient(gdax_api_pubkey, gdax_api_privkey, gdax_api_passphrase, api_url="https://api-public.sandbox.gdax.com")
cex_api = cexio.Api(cex_api_user_id, cex_api_pubkey, cex_api_privkey)


# exchange data
gdax_accounts = gdax_api.get_accounts()
gdax_accounts_btc = gdax_accounts[0]
gdax_accounts_usd = gdax_accounts[1]

gdax_balance_btc = float(gdax_accounts_btc['balance'])
gdax_balance_usd = float(gdax_accounts_usd['balance'])

gdax_rate_buy = float(gdax_api.get_product_ticker(product_id='BTC-USD')['bid'])
gdax_rate_sell = float(gdax_api.get_product_ticker(product_id='BTC-USD')['ask'])
gdax_rate_avg = (gdax_rate_buy + gdax_rate_sell)/2

cex_balance = cex_api.balance

cex_rate_buy = float(cex_api.ticker('BTC/USD')['bid'])
cex_rate_sell = float(cex_api.ticker('BTC/USD')['ask'])
cex_rate_avg = (cex_rate_sell + cex_rate_buy)/2

gdax_taker_fee_percent_btc = 0.0025 #percent
gdax_withdraw_fee_percent_btc = 0
gdax_deposit_fee_percent_btc = 0
cex_taker_fee_percent_btc = 0.0025
cex_withdraw_fee_percent_btc = 0.3
cex_deposit_fee_percent_btc = 0

# websocket
# wsClient = gdax.WebsocketClient(url="wss://ws-feed.gdax.com", products="BTC-USD")

# calculations on exchange data
exchange_buy_avg = (gdax_rate_buy + cex_rate_buy)/2
buy_spread = abs((gdax_rate_buy - cex_rate_buy)/exchange_buy_avg)
buy_spread_percent = buy_spread*100

exchange_sell_avg = (gdax_rate_sell + cex_rate_sell)/2
sell_spread = abs((gdax_rate_sell - cex_rate_sell)/exchange_sell_avg)
sell_spread_percent = sell_spread*100

exchange_avg = (gdax_rate_avg + cex_rate_avg)/2
spread = abs((gdax_rate_avg - cex_rate_avg)/exchange_avg)
spread_percent = spread*100


# exchange trading
gdax_buy_amount = 0
gdax_sell_amount = 0
#gdax_buy = gdax_api.buy(price=gdax_rate_avg, size=gdax_buy_amount, product_id='BTC-USD')
#gdax_sell = gdax_api.sell(price=gdax_rate_avg, size=gdax_sell_amount, product_id='BTC-USD')
#cex_buy_amount = 0
#cex_sell_amount = 0
#cex_buy = cex_api.buy_limit_order(price=cex_rate_buy, amount=cex_buy_amount, market='BTC/USD')
#cex_sell = cex_api.sell_limit_order(price=cex_rate_buy, amount=cex_sell_amount, market='BTC/USD')


# exchange withdrawal and depositing
cex_trading_wallet_btc = ''
#gdax_withdraw = gdax_api.crypto_withdraw(amount=gdax_buy_amount, currency="BTC", payment_method_id=cex_trading_wallet_btc)
print cex_balance
#wsClient = gdax_api.WebsocketClient(url="wss://ws-feed.gdax.com", products="BTC-USD")
print wsClient