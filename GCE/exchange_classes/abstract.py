class Exchange(object):
    def __init__(self, num_confs_btc=6, transfer_time=1800):
        """Constructor
        :param num_confs_btc: :param transfer_time: the number
        of seconds to poll a transaciton before reporting it as a
        failure
        
        :returns: object
        :rtype: Exchange
        
        """
        
        # number of confirmations needed to confirm btc deposit
        self.num_confs_btc = num_confs_btc
        self.transfer_time = transfer_time
    
    def buy(self, currency, amount):
        """Generic method to place buy market order.
        
        :param currency: a reference to the Currencies enum
        :param amount: amount of currency to be bought
        
        """
        raise NotImplementedError
   
    def sell(self, currency, amount):
        """Generic method to place a sell market order
        
        :param currency: a reference to the Currencies enum
        :param amount: amount of currency to be sold
        
        """
        raise NotImplementedError
    
    def transfer(self, currency, amount, address):
        """Generic method to transfer currency to the given address
        
        :param currency: a reference to the Currencies enum
        :param amount: the amount to be transferred
        :param address:  hash of the destination address
        
        """
        raise NotImplementedError
    
    def get_deposit_address(self, currency):
        """Returns the hash of the address to be used for depositing the
        currency
        
        :param currency:  a reference to the Currencies enum
        :returns: hash of the address for depositing
        
        """
        raise NotImplementedError
    
    def get_balance(self, currency):
        """Returns the current available balance of the given currency
        
        :param currency:
        :return: float of the current available balance
        
        """
        raise NotImplementedError

    def get_order(self, order_id):
        """
        Returns the detail of the provided order_id
        :param order_id:
        :return:
        """
        raise NotImplementedError

    def wait_for_order(self, order_id):
        """When an order is placed in an exchange, it's not guaranteed to be
        fulfilled immediately this method blocks excecution until the
        order is fulfilled.
        
        :param order_id:
        :return:
        
        """
        raise NotImplementedError
        
    def return_transaction_from_address(self, address, amount):
        """Some exchanges (Ex: gdax) don't return the blockchain transaction
        hash immediately, this method blocks execution and returns the
        transaction hash for a given address
        
        :param address: hash of the address
        :param amount: original btc amount sent
        :return: transaction hash for a given_address
        
        """
        raise NotImplementedError
