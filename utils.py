# coding: utf-8

import smtplib, datetime
from settings import emailto, smtp_host
from email.mime.text import MIMEText

def parsedate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%S%z")

def sendmail(text, username):
    msg = MIMEText(text)
    msg['Subject'] = "Uplancebot: Feedback from {}".format(username)
    msg['From'] = 'Uplancebot <uplancebot@uplancebot.me>'
    msg['To'] = emailto
    s = smtplib.SMTP(smtp_host)
    s.send_message(msg)
    s.quit()

