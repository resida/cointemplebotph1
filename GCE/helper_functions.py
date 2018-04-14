import hashlib
import hmac

#secrets import OUR_API_KEY, OUR_API_SECRET

"""
def is_valid(nonce, api_key, signature):
    if not nonce or not api_key or not signature:
        return False
    if api_key != OUR_API_KEY:
        return False
    message = nonce + api_key
    signature_right = hmac.new(OUR_API_SECRET, message, hashlib.sha256).hexdigest()
    if signature_right != signature:
        return False
    return True
"""