import requests


SATOSHIS_PER_BITCOIN = 100000000


def get_most_recent_unnconfirmed_txn(address, original_amount_sent):
    """
    Since some exchanges don't expose the transaction id of the transfer. Here we attempt to get the transaction id
    from the blockchain address. If multiple unconfirmed transactions are present, we try to get the transaction hash
    by finding the most recent transaction with the matching btc amount sent
    :param address The desitnation bitcoin address
    :param original_amount_sent The amount of BTC sent

    """
    r = requests.get("https://api.blockcypher.com/v1/btc/main/addrs/%s" % address)
    r.raise_for_status()
    unconfirmed_txns = r.json()["unconfirmed_txrefs"]
    for txn in unconfirmed_txns:
        if txn["value"] == int(original_amount_sent * SATOSHIS_PER_BITCOIN):
            return txn["tx_hash"]
        else:
            continue
    raise LookupError("Could not deduce transaction id from address %s"
                      "Found %s unconfirmed transactions for address none of which matched matched the sent btc amount." % (address, len(unconfirmed_txns)))

def get_num_confirmations_transaction(txn_id):
    r = requests.get("https://api.blockcypher.com/v1/btc/main/txs/%s" % txn_id)
    r.raise_for_status()
    return r.json()["confirmations"]


