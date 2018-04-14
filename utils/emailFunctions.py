from utils.auxFunctions import getQAorProd
from google.appengine.api import urlfetch, mail, app_identity, memcache
from global_variables import SIGN_UP_FLOW_EMAIL_ADDRESS_PROD, SIGN_UP_FLOW_EMAIL_ADDRESS_QA, SERVICE_NAME, ABOUT_PAGE_URL, SUPPORT_EMAIL_ADDRESS_QA, SUPPORT_EMAIL_ADDRESS_PROD
from utils.auxFunctions import getQAorProd


def send_notification_email(email):
	message_body1 = """
		Trade Completed
	""".format(ervice_name=SERVICE_NAME)
	message_body = message_body1 + getBottomSignature_body()
	html_message_body1 = """
		Trade Completed
	""".format(service_name=SERVICE_NAME)
	html_message_body = html_message_body1
	senderEmail = "notification@coin-temple.appspotmail.com"
	emailToSend = mail.EmailMessage(sender=senderEmail,
									to=email,
									subject=SERVICE_NAME + " trade notification",
									body=message_body,
									html=html_message_body)
	emailToSend.send()


def send_signup_verify_email(email, url):
	message_body1 = """
		Thank you for signing up to {service_name}.
		To verify your email address, follow this link or cut and paste it into your browser: {url}
	""".format(url=url,
			   service_name=SERVICE_NAME)
	message_body = message_body1 + getBottomSignature_body()
	html_message_body1 = """
		<p>Thank you for signing up to {service_name}.</p>
		<p>To verify your email address, follow this link or cut and paste it into your browser: <a href="{url}">{url}</a></p>
	""".format(url=url,
			   service_name=SERVICE_NAME)

	html_message_body = html_message_body1

	if getQAorProd() == "qa":
		senderEmail = SIGN_UP_FLOW_EMAIL_ADDRESS_QA
	else:
		senderEmail = SIGN_UP_FLOW_EMAIL_ADDRESS_PROD

	emailToSend = mail.EmailMessage(sender=senderEmail,
									to=email,
									subject=SERVICE_NAME + " signup verification",
									body=message_body,
									html=html_message_body)
	emailToSend.send()



def send_forgot_password_email(email, url):

	if getQAorProd() == "qa":
		supportEmail = SUPPORT_EMAIL_ADDRESS_QA
		senderEmail = SIGN_UP_FLOW_EMAIL_ADDRESS_QA
	else:
		supportEmail = SUPPORT_EMAIL_ADDRESS_PROD
		senderEmail = SIGN_UP_FLOW_EMAIL_ADDRESS_PROD


	message_body1 = """
		If you forgot your password, please visit this url: {url}
		If not, ignore this email. Contact {supportemail} if you have questions.
		This link will expire in 3 hours.
	""".format(url=url,
			   supportemail=supportEmail)
	message_body = message_body1 + getBottomSignature_body()
	html_message_body1 = """
		<p>If you forgot your password, please visit this url: <a href="{url}">{url}</a></p>
		</p>If not, ignore this email. Contact <a href="mailto:{supportemail}">{supportemail}</a> if you have questions.</p>
		<p>This link will expire in 3 hours.</p>
	""".format(url=url,
			   supportemail=supportEmail)
	html_message_body = html_message_body1
	emailToSend = mail.EmailMessage(sender=senderEmail,
									to=email,
									subject=SERVICE_NAME + " password",
									body=message_body,
									html=html_message_body)
	emailToSend.send()

def getBottomSignature_body():


	if getQAorProd() == "qa":
		supportEmail = SUPPORT_EMAIL_ADDRESS_QA
	else:
		supportEmail = SUPPORT_EMAIL_ADDRESS_PROD

	return '''
		If you have any questions or concerns, please go to {about_page_url}, or email {supportemail}.
		Best Regards,
		The {service_name} Team
	'''.format(about_page_url=ABOUT_PAGE_URL,
			   supportemail=supportEmail,
			   service_name=SERVICE_NAME)


def getBottomSignature_body_html():

	if getQAorProd() == "qa":
		supportEmail = SUPPORT_EMAIL_ADDRESS_QA
	else:
		supportEmail = SUPPORT_EMAIL_ADDRESS_PROD


	return '''
		<br>
		<p>If you have any questions or concerns, please go to <a href="{about_page_url}">{about_page_url}</a>, or email <a href="mailto:{supportemail}">{supportemail}</a>.
		<p>Best Regards,</p>
		<p>The {service_name} Team</p>
	'''.format(about_page_url=ABOUT_PAGE_URL,
			   supportemail=supportEmail,
			   service_name=SERVICE_NAME)