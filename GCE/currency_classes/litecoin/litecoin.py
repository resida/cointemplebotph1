from GCE.currency_classes.abstract import Currency


class Litecoin(Currency):
    def __init__(self, identifier="LTC"):
        self.identifier = identifier
