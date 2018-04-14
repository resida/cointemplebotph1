from GCE.currency_classes.abstract import Currency


class EthereumClassic(Currency):
    def __init__(self, identifier="ETC"):
        self.identifier = identifier
