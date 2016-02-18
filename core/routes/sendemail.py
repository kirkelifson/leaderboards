__author__ = 'rabsrincon'

from smtplib import SMTP_SSL as SMTP
from email import MIMEText

class EmailConnection(object):
	def __init__(self, sender, server, port, username, password, debug=False):
		self.sender = sender
		self.smtp = SMTP(server, port)
		self.smtp.login(username, password)
		self.smtp.set_debuglevel(False)
		self.debug = debug

	def send(self, sendto, subject, message):
		if isinstance(sendto, basestring):
			sendto = [sendto]

		for to in sendto:
			msg = MIMEText(message, 'plain')
			msg['Subject'] = subject
			msg['To'] = to
			msg['From'] = self.sender

			if not self.debug:
				try:
					self.smtp.sendmail(self.sender, [to], msg.as_string())
				except:
					pass
			else:
				print msg.as_string()

	def __del__(self):
		self.smtp.close()


    

