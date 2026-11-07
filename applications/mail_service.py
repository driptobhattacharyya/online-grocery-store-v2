import os
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.environ.get("SMTP_HOST") or "localhost"
SMTP_PORT = int(os.environ.get("SMTP_PORT") or 1025)
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_USE_TLS = (os.environ.get("SMTP_USE_TLS") or "false").lower() == "true"
SENDER_EMAIL = os.environ.get("SENDER_EMAIL") or "noreply@grocery.local"


def send_message(to, subject, content_body):
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(content_body, "html"))

    with SMTP(host=SMTP_HOST, port=SMTP_PORT) as client:
        if SMTP_USE_TLS:
            client.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            client.login(SMTP_USERNAME, SMTP_PASSWORD)
        client.send_message(msg=message)
