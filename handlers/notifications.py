
from base import BaseHandler
from utils.emailFunctions import send_notification_email
from models import  TradeSettings
VALID_RESPONSE = [200, 201, 202]

firebase_url = 'https://tenex-capital.firebaseio.com'

class SendNotificationsHandler(BaseHandler):
	def get(self):
		code = self.request.get("code")
		if code == "23123321":
			thisSettings = TradeSettings.query(TradeSettings.exchange_pair == "gdax_cex1").get()
			send_notification_email(thisSettings.email_notification)
		return ""
