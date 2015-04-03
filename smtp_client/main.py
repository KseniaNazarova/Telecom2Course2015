__author__ = 'Ksenia'

import SMTP_client

def send_to_each_one(emails):
    print(emails)
    for email in emails:
        resp_code = smtp.rcpt_to(email)
        if resp_code != 250 and resp_code != 251:
            break
    return resp_code


HOST = input("HOST: ")
PORT = int(input("PORT: "))
DOMAIN = input("DOMAIN: ")

smtp = SMTP_client.SMTP(HOST, PORT)
while True:
    if smtp.ehlo(DOMAIN) == 250:
        break

while True:
    login = input("Fully-Qualified LOGIN: ")
    password = input("PASS: ")
    if smtp.auth(login, password) == 235:
        break

while True:
    email_from = input("Enter your e-mail: ")
    if smtp.mail_from(email_from) == 250:
        break

while True:
    email_to = input("Enter target e-mails separated by \",\": ")
    email_cc = input("Enter cc e-mails separated by \",\": ")
    email_bcc = input("Enter bcc e-mails separated by \",\": ")
    recipients = lambda groups: list(set([email for emails in groups for email in emails]))
    to = email_to.split(",") if email_to != "" else email_to
    cc = email_cc.split(",") if email_cc != "" else email_cc
    bcc = email_bcc.split(",") if email_bcc != "" else email_bcc
    resp_code = send_to_each_one(recipients([to, cc, bcc]))
    if resp_code == 250 or resp_code == 251:
        break

while True:
    email_subject = input("Enter subject of your e-mail: ")
    if email_subject == "":
        print("Your message may be mistaken for spam")
        continue
    else:
        data = input("Enter your message: ")
        if smtp.data(email_from=email_from, email_to=email_to, subject=email_subject, cc=email_cc, data=data) == 250:
            break

smtp.quit()