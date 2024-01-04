from celery import shared_task
import flask_excel as excel
from applications.mail_service import *
from applications.database import *
from jinja2 import Template
import datetime

@shared_task(ignore_result=False)
def say_hello():
    print('Hello there!')


# @shared_task(ignore_result=False)
# def create_resource_csv():
#     # get the stuff from db
    
#     csv_output = excel.make_response(stuff, ['product', 'price'], 'csv')
#     filename="test.csv"
    
#     with open(filename, 'wb') as f:
#         f.write(csv_output.data)
    
#     return filename

def monthly_usage(email):
    db = get_db()
    cursor = db.cursor()
    query = '''SELECT * FROM orders WHERE email = ? '''
    cursor.execute(query, (email,))
    all_orders = cursor.fetchall()
    cursor.close()
    total = 0
    today = datetime.date.today()
    start_of_last_month = today.replace(day=1) - datetime.timedelta(days=30)

    for order in all_orders:
        order_date = datetime.date.fromisoformat(order[2])
        if order_date >= start_of_last_month:
            total += order[3]
    t = Template("""\
    <html>
        <head></head>
        <body>
            <p>Hi {{ email }},</p>
            <p>You have ordered a total of {{ total }} INR in the past month.</p>
            <p>Thanks!</p>
        </body>
    </html>
    """)
    return t.render(email=email, total=total)

@shared_task(ignore_result=True)
def daily_reminder():
    db = get_db()
    cursor = db.cursor()
    subject = "Knock knock"
    query = '''SELECT email FROM users WHERE email LIKE '%@%' '''
    cursor.execute(query)
    all_emails = cursor.fetchall()
    cursor.close()
    for email in all_emails:
        send_message(email[0], subject, "Hey, we've been missing you!")
    # send_message(to, subject, "hello")
    return "OK"


@shared_task(ignore_result=True)
def monthly_report():
    db = get_db()
    cursor = db.cursor()
    subject = "Monthly report"
    query = '''SELECT email FROM users WHERE email LIKE '%@%' '''
    cursor.execute(query)
    all_emails = cursor.fetchall()
    cursor.close()
    for email in all_emails:
        send_message(email[0], subject, monthly_usage(email[0]))
    return "OK"

@shared_task(ignore_result=True)
def send_email(to, subject):
    db = get_db()
    cursor = db.cursor()
    try:
        query = '''SELECT email FROM users WHERE email LIKE '%@%' '''
        cursor.execute(query)
        all_emails = cursor.fetchall()
        cursor.close()
        for email in all_emails:
            with open('test.html', 'r') as f:
                template = Template(f.read())
                send_message(email[0], subject, template.render(email=email[0]))
    except Exception as e:
        db.rollback()
        cursor.close()
        print(e)
