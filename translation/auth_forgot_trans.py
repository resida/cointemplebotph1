# coding=utf-8

from global_variables import SERVICE_NAME

class auth_forgot_en:
	en0 = u"Forgot Password"
	en1 = u"If you enter your email we'll send a password reset link which will be valid for six hours.".format(service_name=SERVICE_NAME)
	en3 = u"If there's an account with that email address, we've sent a password reset link."
	en4 = u"EMAIL"
	en5 = u"SUBMIT"
	en6 = u"SIGNUP"
	en7 = u"email@example.com"

	def __init__(self):
		self.data=[]

class auth_forgot_es:
	en0 = u"Olvidé mi contraseña"
	en1 = u"Introduce tu Email para recibir un enlace para restablecer tu Contraseña."
	en2 = u"(el enlace de restablecimiento es válido por 3 horas)"
	en3 = u"Si hay una cuenta con ese email, hemos enviado un enlace de restablecimiento de contraseña."


	#en3 = u"Si tu email es encontrado en {service_name} entonces un enlace para restablecer tu contraseña ha sido enviado a tu dirección d email.".format(service_name=SERVICE_NAME)
	en4 = u"EMAIL"
	en5 = u"ENVIAR"
	en6 = u"SIGNUP"
	en7 = u"email@example.com"

	def __init__(self):
		self.data=[]

