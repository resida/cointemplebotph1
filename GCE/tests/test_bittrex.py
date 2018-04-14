from GCE.exchange_classes.bittrex.bittrex import Bittrex
import GCE.secrets as secrets

ex_dict = {}
ex_dict["bittrex"] = Bittrex(secrets.TEST_BITTREX_KEY, secrets.TEST_BITTREX_SECRET)

btc_amount = .01
buy_id = ex_dict["bittrex"].buy_btc(btc_amount)
ex_dict["bittrex"].wait_for_order(buy_id)


send_to_address = ex_dict["bittrex"].get_btc_deposit_address()
print send_to_address

ex_dict["bittrex"].transfer_btc(btc_amount, send_to_address)
print "Transfer initiated to bitcoin address %s. Waiting for transaction to be registered on the " \
      "blockchain" % send_to_address
