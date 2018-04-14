import threading
import datetime
from firebase import firebase_push_value
import random

import time

def record_order_log_in_firebase(wo_log_dict):
    firebase_push_value(["order_logs", "cex_gdax"], wo_log_dict)

def order_log(order_log_text, wo_uuid):
    time_readable = datetime.datetime.now().strftime("%m-%d %H:%M")
    order_log_dict = {"neg_timestamp": -time.time(), "timestamp": time.time(), "time_readable": time_readable,
                   "wo_id": str(wo_uuid), "text":order_log_text}
    t = threading.Thread(target=record_order_log_in_firebase,args=[order_log_dict])
    t.start()
    return

def exchange_buy_and_send_thread(wo_uuid, cexio_global, gdax_global):
    gdax_snapshot = gdax_global.get_ask_price()
    cexio_snapshot = cexio_global.ask_price
    diff = abs(float(gdax_snapshot)-float(cexio_snapshot))
    average = (float(gdax_snapshot)+float(cexio_snapshot))/2.0
    snapshot_spread = (diff / average)*100.0
    log_text = "gdax: " + str(gdax_snapshot) + " cex: " + str(cexio_snapshot) + " spread: " + str(round(snapshot_spread, 3))
    order_log(log_text, wo_uuid)
    last_time = time.time()
    while True:
        if not cexio_global.get_continue_loop(wo_uuid):
            order_log("cancelled continue loop bp 1", wo_uuid)
            break
        time_trigger = time.time() - last_time > 300
        if time_trigger:
            last_time = time.time()
        time.sleep(.05)
    if cexio_global.get_continue_loop(wo_uuid):
        order_log("got here w continue true", wo_uuid)
    cexio_global.set_continue_loop(wo_uuid, False)