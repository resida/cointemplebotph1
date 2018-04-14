
from base import BaseHandler

import json

from google.appengine.api import urlfetch
import datetime
import operator
VALID_RESPONSE = [200, 201, 202]


firebase_url = 'https://coin-temple.firebaseio.com'
'https://coin-temple.firebaseio.com/working_order_logs.json?orderBy="neg_timestamp"&limitToFirst=1000'
def get_exchange_logs(working_order_id):
	if working_order_id:

		response1 = urlfetch.fetch(
			url=str(firebase_url + '/api_call_log.json?orderBy="neg_timestamp"&limitToFirst=10000'),
			method=urlfetch.GET,
			deadline=20
		)

		orig_api_call_log_dict = json.loads(response1.content)
		api_call_log_list = []
		for item in orig_api_call_log_dict:
			dict_item = orig_api_call_log_dict[item]
			if "wo_id" in dict_item:
				if dict_item["wo_id"] == working_order_id:
					api_call_log_list.append(dict_item)

		dict_list = []
		for item in api_call_log_list:
			orig_dict = item
			if "time_elapsed" not in orig_dict:
				orig_dict["time_elapsed"] = 0.0
			if "timestamp" in orig_dict:
				orig_dict["visible_time"] = datetime.datetime.fromtimestamp(int(orig_dict["timestamp"])).strftime('%H:%M:%S')
			if "cex" in orig_dict["request_url"]:
				orig_dict["exchange"] = "CEX"
			orig_dict["request_url"] = orig_dict["request_url"].replace("https://cex.io/api", "")
			dict_list.append(orig_dict)

		dict_list.sort(key=operator.itemgetter('neg_timestamp'))

		return dict_list
	else:
		response1 = urlfetch.fetch(
			url=str(firebase_url + '/api_call_log.json?orderBy="neg_timestamp"&limitToFirst=10000'),
			method=urlfetch.GET,
			deadline=20
		)
		api_call_log_dict = json.loads(response1.content)
		dict_list = []
		for item in api_call_log_dict:
			orig_dict = api_call_log_dict[item]
			if "time_elapsed" not in orig_dict:
				orig_dict["time_elapsed"] = 0.0
			if "timestamp" in orig_dict:
				orig_dict["visible_time"] = datetime.datetime.fromtimestamp(int(orig_dict["timestamp"])).strftime('%H:%M:%S')
			if "cex" in orig_dict["request_url"]:
				orig_dict["exchange"] = "CEX"
			orig_dict["request_url"] = orig_dict["request_url"].replace("https://cex.io/api", "")
			dict_list.append(orig_dict)
		dict_list.sort(key=operator.itemgetter('neg_timestamp'))
		return dict_list

def get_order_list():
	response1 = urlfetch.fetch(
		url=str(firebase_url + '/working_orders.json?orderBy="neg_timestamp"&limitToFirst=1000'),
		method=urlfetch.GET,
		deadline=20
	)
	api_call_log_dict = json.loads(response1.content)
	dict_list = []
	for item in api_call_log_dict:
		orig_dict = api_call_log_dict[item]
		dict_list.append(orig_dict)

	#dict_list.sort(key=operator.itemgetter('neg_timestamp'))
	return dict_list

def get_order_logs(working_order_id):
	if working_order_id:
		response1 = urlfetch.fetch(
			url=str(firebase_url + '/working_order_logs.json?orderBy="neg_timestamp"&limitToFirst=10000'),
			method=urlfetch.GET,
			deadline=20
		)

		api_call_log_dict = json.loads(response1.content)
		dict_list = []
		for item in api_call_log_dict:
			orig_dict = api_call_log_dict[item]
			if "timestamp" in orig_dict:
				orig_dict["visible_time"] = datetime.datetime.fromtimestamp(int(orig_dict["timestamp"])).strftime('%H:%M:%S')
			if orig_dict["wo_id"] == working_order_id:
				dict_list.append(orig_dict)

		dict_list.sort(key=operator.itemgetter('neg_timestamp'))

		return dict_list
	else:
		response1 = urlfetch.fetch(
			url=str(firebase_url + '/working_order_logs.json?orderBy="neg_timestamp"&limitToFirst=10000'),
			method=urlfetch.GET,
			deadline=20
		)
		api_call_log_dict = json.loads(response1.content)
		dict_list = []
		for item in api_call_log_dict:
			orig_dict = api_call_log_dict[item]
			dict_list.append(orig_dict)

		#dict_list.sort(key=operator.itemgetter('neg_timestamp'))
		return dict_list


class ExchangeAPIMonitorHandler(BaseHandler):
	def get(self):
		shown_order_id = self.request.get("shown_order_id")
		params = {}
		#params["exchange_log_list"] = get_exchange_logs(shown_order_id)
		params["order_log_list"] = get_order_logs(shown_order_id)
		params["order_list"] = get_order_list()
		params["shown_order_id"] = shown_order_id
		return self.render_template("templates/logs.html", params)

class ExchangeAPIMonitorAJAXHandler(BaseHandler):
	def get(self):

		return self.response.out.write(json.dumps({}))