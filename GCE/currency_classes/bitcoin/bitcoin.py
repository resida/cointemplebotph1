from GCE.currency_classes.abstract import Currency


class Bitcoin(Currency):
    
    def __init__(self, identifier="BTC", num_confs=6):
        self.identifier = identifier
        # number of confirmations needed to confirm btc deposit
        self.num_confs = num_confs
