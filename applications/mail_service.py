"""SMTP mail. Credentials come from the environment; MailHog needs none."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_message(to, subject, content_body):
    host = os.environ.get("SMTP_HOST", "localhost")
    port = int(os.environ.get("SMTP_PORT", "1025"))
    sender = os.environ.get("SENDER_EMAIL", "grocery-store@localhost")
    username = os.environ.get("SMTP_USERNAME", "")
    password = os.environ.get("SMTP_PASSWORD", "")

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(content_body, "html"))

    with smtplib.SMTP(host=host, port=port, timeout=10) as client:
        if username:
            client.login(username, password)
        client.send_message(message)
