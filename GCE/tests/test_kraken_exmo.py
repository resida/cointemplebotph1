from GCE.currency_classes.abstract import Currencies
from GCE.exchange_container import Exchanges

exchanges = Exchanges()

kraken = exchanges.ex_dict["kraken"]
exmo = exchanges.ex_dict["exmo"]
gdax = exchanges.ex_dict["gdax"]
cex = exchanges.ex_dict["cex"]
bittrex = exchanges.ex_dict["bittrex"]


exchanges.initiate_arbitrage(exmo, cex, 0.002, Currencies.bitcoin)
