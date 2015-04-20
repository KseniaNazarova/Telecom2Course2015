__author__ = 'Ksenia'

import socket
import base64
import ssl
import warnings

CRLF = "\r\n"
MAXLINE = 8192
CODESIZE = 3

unexp_code = 640
errno = {220: "SMTP ready",
         221: "Service closing transmission channel",
         235: "Authentication Succeeded",
         250: "OK",
         251: "User not local; will forward to <forward-path>",
         421: "Service not available, closing transmission channel",
         450: "Requested mail action not taken: mailbox unavailable",
         451: "Requested action aborted: error in processing",
         452: "Requested action not taken: insufficient system storage",
         454: "Temporary authentication failure",
         455: "Server unable to accommodate parameters",
         500: "Invalid command",
         501: "Syntax error in parameters",
         502: "Command not implemented",
         503: "Bad sequence of commands",
         504: "Command parameter not implemented",
         534: "Authentication mechanism is too weak",
         535: "Authentication credentials invalid",
         550: "Requested action not taken: mailbox unavailable",
         551: "User not local; please try <forward-path>",
         552: "Requested mail action aborted: exceeded storage allocation or Too many recipients",
         553: "Requested action not taken: mailbox name not allowed",
         554: "Transaction failed",
         555: "MAIL FROM/RCPT TO parameters not recognized or not implemented",
         640: "Unexpected error",
         10060: "Connection attempt failed",
         11001: "Getaddrinfo failed"}

normal_code = [220, 221, 235, 250, 251, 450, 500, 501, 502, 503, 504, 535, 551, 552, 553]
bad_code = [421, 451, 452, 454, 455, 534, 550, 554, 555, 10060, 11001]


class SMTP_Error(BaseException):

    def __init__(self, code=0):
        print("%d: %s" % (code, errno[code]))

class SMTP():
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
        try:
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__ssl_sock = ssl.wrap_socket(self.__sock)
            self.__ssl_sock.connect((host, port))
            resp_code = int(self.__ssl_sock.recv(MAXLINE).decode('ascii')[:CODESIZE])
            self.__print_response(resp_code)
            return resp_code
        except OSError:
            raise SMTP_Error(10060)

    def __send_cmd(self, cmd, args=""):
        if args == "":
            str = '%s%s' % (cmd, CRLF)
        else:
            str = '%s %s%s' % (cmd, args, CRLF)
        print(str[:-len(CRLF)])
        try:
            self.__ssl_sock.send(str.encode('ascii'))
            #return int(self.__ssl_sock.recv(MAXLINE).decode('ascii')[:CODESIZE])
            return self.receive_code()
        except OSError:
            raise SMTP_Error(10060)
        ### TODO
        ### ADD IF EMPTY CMD
        except:
            raise SMTP_Error(unexp_code)

    def receive_code(self):
        return int(self.__ssl_sock.recv(MAXLINE).decode('ascii')[:CODESIZE])

    def ehlo(self, domain):
        resp_code = self.__send_cmd(self.__cmd_ehlo, domain)
        self.__print_response(resp_code)
        return resp_code

    def auth(self, login, password):
        resp_code = self.__send_cmd(self.__cmd_auth, "LOGIN %s" % base64.b64encode(bytes(login, 'ascii')).decode('ascii'))
        if resp_code == 334:
            resp_code = self.__send_cmd(base64.b64encode(bytes(password, 'ascii')).decode('ascii'))
            self.__print_response(resp_code)
        else:
            self.__print_response(resp_code)
        return resp_code

    def mail_from(self, email):
        resp_code = self.__send_cmd(self.__cmd_mail, "FROM:<%s>" % email)
        self.__print_response(resp_code)
        return resp_code

    def rcpt_to(self, email):
        resp_code = self.__send_cmd(self.__cmd_rcpt, "TO:<%s>" % email)
        self.__print_response(resp_code)
        return resp_code

    def data(self, email_from="", email_to="", subject="", cc="", bcc="", data=""):
        if subject == "":
            warnings.warn("The message can be taken as spam")
        resp_code = self.__send_cmd(self.__cmd_data)
        if resp_code == 354:
            msg = Message()
            resp_code = self.__send_cmd(msg.header(email_from, email_to, subject, cc, bcc) + msg.body(data))
            self.__print_response(resp_code)
        else:
            self.__print_response(resp_code)
        return resp_code

    def quit(self):
        self.__print_response(self.__send_cmd(self.__cmd_quit))
        self.__disconnect_from_server()

    def __disconnect_from_server(self):
        self.__ssl_sock.close()

    def __print_response(self, code=0):
        if code in normal_code:
            print("%d: %s" % (code, errno[code]))
        elif code in bad_code:
            raise SMTP_Error(code)
        else:
            raise SMTP_Error(unexp_code)

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
        if bcc != "":
            self._header += "bcc: %s%s" % (bcc, CRLF)
            email_to += ",%s" % bcc
        if email_to != "":
            self._header += "To: %s%s" % (email_to, CRLF)
        if subject != "":
            self._header += "Subject: %s%s" % (subject, CRLF)
        return self._header

    def body(self, body):
        print(body)
        self._body = "%s%s." % (body, CRLF)
        return self._body