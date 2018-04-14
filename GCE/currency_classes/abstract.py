from enum import Enum


class Currency(object):
    """Abstract currency classes have some functions to check the
    blockchain. These are implemented within
    currency_classes/bitcoin/bitcoin.py.
    
    Each exchange class will implement a hashmap called
    "currencies". Within this hashmap they will instantiate one of
    each class pointing to an instance. This will amount to a
    singleton model for each exchange. This "singleton" will contain
    information necessary for that particular exchange to trade that
    currency.
    
    To make the example more concrete, to trade BTC on Exmo, the
    identifier in the API requests may just be "BTC", but on Kraken it
    may be "BTZ". Therefore, the Exmo API would say something like:
    currencies["Bitcoin"] = Bitcoin("BTC")
    
    and for Kraken it may look something like this:
    currencies["Bitcoin"] = Bitcoin("BTZ").
    
    """
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        
    def get_deposit_address(self):
        pass


class Currencies(Enum):
    """Enum for currencies
    """
    bitcoin = "bitcoin"
    litecoin = "litecoin"
    ethereum = "ethereum"
    ethereum_classic = "ethereum_classic"
