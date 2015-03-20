__author__ = 'Ksenia'

import socket
import base64
import ssl

CRLF = "\r\n"
MAXLINE = 8192


class SMTP:
    __cmd_ehlo = "EHLO"
    __cmd_auth = "AUTH"
    __cmd_mail = "MAIL"
    __cmd_rcpt = "RCPT"
    __cmd_data = "DATA"
    __cmd_quit = "QUIT"

    def __init__(self, host='', port=0):
        self.host = host
        self.port = port
        self.__connect_to_server(host, port)

    def __connect_to_server(self, host, port):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__ssl_sock = ssl.wrap_socket(self.__sock)
        self.__ssl_sock.connect((host, port))
        print(self.__ssl_sock.recv(MAXLINE))

    def __send_cmd(self, cmd, args=""):
        if args == "":
            str = '%s%s' % (cmd, CRLF)
        else:
            str = '%s %s%s' % (cmd, args, CRLF)
        str = str.encode('ascii')
        print(str)
        self.__ssl_sock.send(str)
        return self.__ssl_sock.recv(MAXLINE)

    def ehlo(self, domain):
        print(self.__send_cmd(self.__cmd_ehlo, domain))

    def auth(self, login, password):
        if self.__send_cmd(self.__cmd_auth, "LOGIN %s" % base64.b64encode(bytes(login, 'ascii')).decode('ascii'))[:3] == b'334':
            print(self.__send_cmd(base64.b64encode(bytes(password, 'ascii')).decode('ascii')))

    def mail_from(self, email):
        print(self.__send_cmd(self.__cmd_mail, "FROM:<%s>" % email))

    def rcpt_to(self, email):
        print(self.__send_cmd(self.__cmd_rcpt, "TO:<%s>" % email))

    def data(self, email_from="", email_to="", subject="", cc="", bcc="", data=""):
        print(self.__send_cmd(self.__cmd_data))
        msg = Message()
        print(self.__send_cmd(msg.header(email_from, email_to, subject, cc, bcc) + msg.body(data)))

    def quit(self):
        print(self.__send_cmd(self.__cmd_quit))
        self.__disconnect_from_server()

    def __disconnect_from_server(self):
        self.__ssl_sock.close()


class Message():

    def __init__(self):
        self._header = ""
        self._body = ""

    def header(self, email_from, email_to, subject, cc, bcc):
        if email_from != "":
            self._header += "From: %s%s" % (email_from, CRLF)
        if cc != "":
            self._header += "cc: %s%s" % (cc, CRLF)
            email_to += ",%s" % cc
            print("LOG " + email_to)
        if bcc != "":
            self._header += "bcc: %s%s" % (bcc, CRLF)
            email_to += ",%s" % bcc
            print("LOG " + email_to)
        if email_to != "":
            self._header += "To: %s%s" % (email_to, CRLF)
        if subject != "":
            self._header += "Subject: %s%s" % (subject, CRLF)
        return self._header

    def body(self, body):
        self._body = "%s%s." % (body, CRLF)
        return self._body

def add_target_emails(gen_emails, add_emails):
    for email in add_emails:
        if email not in gen_emails:
            gen_emails.append(email)
    return gen_emails


HOST = input("HOST: ")
PORT = int(input("PORT: "))
DOMAIN = input("DOMAIN: ")

#HOST = "smtp.mail.ru"
#PORT = 465
#DOMAIN = "mail.ru"

smtp = SMTP(HOST, PORT)
smtp.ehlo(DOMAIN)

login = input("LOGIN: ")
password = input("PASS: ")
smtp.auth(login, password)

email_from = input("Enter your e-mail: ")
smtp.mail_from(email_from)
email_to = input("Enter target e-mails separated by \",\": ")
email_cc = input("Enter cc e-mails separated by \",\": ")
email_bcc = input("Enter bcc e-mails separated by \",\": ")

#email_to = "k-nazarova@mail.ru,knazarova9@mail.ru"
#email_cc = "knazarova9@yandex.ru"
#email_bcc = "knazarova9@rambler.ru"

if email_cc == "" and email_bcc == "":
    for email in email_to.split(","):
        smtp.rcpt_to(email)
else:
    if email_cc != "":
        for email in add_target_emails(email_to.split(","), email_cc.split(",")):
            smtp.rcpt_to(email)
    if email_bcc != "":
        for email in add_target_emails(email_to.split(","), email_bcc.split(",")):
            smtp.rcpt_to(email)

while 1:
    email_subject = input("Enter subject of your e-mail: ")
    if email_subject != "":
        break
    else:
        print("Your message may be mistaken for spam")

data = input("Enter your message: ")

smtp.data(email_from=email_from, email_to=email_to, subject=email_subject, cc=email_cc, data=data)
smtp.quit()