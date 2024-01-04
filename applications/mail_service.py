from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "localhost"
SMTP_PORT = 1025
SENDER_EMAIL = 'dripto_dummy@ds.study.iitm.ac.in'
SENDER_PASSWORD = 'dummy_password'

def send_message(to, subject, content_body):
    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['To'] = to
    message['Subject'] = subject

    message.attach(MIMEText(content_body, 'html'))
    client = SMTP(host=SMTP_HOST, port=SMTP_PORT)
    client.send_message(msg=message)
    client.quit()
