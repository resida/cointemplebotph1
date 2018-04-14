from GCE.currency_classes.abstract import Currency


class Ethereum(Currency):
    def __init__(self, identifier="ETH"):
        self.identifier = identifier
