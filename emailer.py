import json
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def sendEmail(user, pwd, recipient, subject, body, json=None):

    FROM = user
    TO = recipient if isinstance(recipient, list) else [recipient]
    SUBJECT = subject
    TEXT = body

    # # Prepare actual message
    # message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    # """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    message = MIMEMultipart()
    message['Subject'] = SUBJECT
    message['From'] = FROM
    message['To'] = ', '.join(TO)
    message.attach(MIMEText(TEXT, 'plain'))
    if (json != None):
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(json)
        encoders.encode_base64(part)

        part.add_header('Content-Disposition', 'attachment; filename="state.json"')

        message.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(FROM, TO, message.as_string())
        server.close()
        print('successfully sent the mail')
    except:
        print("failed to send mail")

with open("data/email.json", "r") as f:
    emailInfo = json.load(f)

def sendSupportEmail(contents):
    sendEmail(emailInfo.get("Address"), emailInfo.get("Credentials"), emailInfo.get("Address"), "Support", contents)

def sendBugReport(description, log):
    sendEmail(emailInfo.get("Address"), emailInfo.get("Credentials"), emailInfo.get("Address"), "Bug Report", description, log.URHandler.getJSON())
