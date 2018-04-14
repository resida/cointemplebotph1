from GCE.currency_classes.abstract import Currencies
from GCE.exchange_container import Exchanges

exchanges = Exchanges()

kraken = exchanges.ex_dict["kraken"]
exmo = exchanges.ex_dict["exmo"]
gdax = exchanges.ex_dict["gdax"]
cex = exchanges.ex_dict["cex"]
bittrex = exchanges.ex_dict["bittrex"]

print "Kraken Balance:"
print kraken.get_balance(Currencies.bitcoin)

print "EXMO Balance:"
print exmo.get_balance(Currencies.bitcoin)

print "GDAX Balance:"
print gdax.get_balance(Currencies.bitcoin)

print "CEX Balance:"
print cex.get_balance(Currencies.bitcoin)

print "Bittrex Balance:"
print bittrex.get_balance(Currencies.bitcoin)
