__author__ = 'Ksenia'

import socket
import socketserver
import os

HOST_HTTP = "www.example.com"
HOST = "127.0.0.1"
PORT_HTTP = 8080
PORT = 80
MAXLINE = 1024
MAXPAGE = 65535
CODESIZE = 3
CRLF = '\r\n'
VERSION = "HTTP/1.1"

filename = "index.html"
req = "HEAD", "/news HTTP/1.1\nHost: www.bbc.co.uk\nIf-Modified-Since: Mon, 20 Apr 2015 01:20:06 GMT\r\n"

def get_mtime_of_file(file):
    from time import gmtime, time
    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    year, month, day, hh, mm, ss, wd, y, z = gmtime(os.path.getmtime(file))
    return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (weekdayname[wd], day, monthname[month], year, hh, mm, ss)

class Proxy(socketserver.StreamRequestHandler):

    #def __init__(self, sock, host=HOST_HTTP, port=PORT):
    def handle(self):
        self.__sock_cl = self.request
        (self.cmd, self.uri, self.cl_content) = self.__get_request_from_client(self.__sock_cl)
        print(self.cl_content)
        self.host = "".join([x.split(":")[1].strip() for x in self.cl_content if x.lower().startswith("host")])
        print(self.host)
        try:
            self.__connect_to_server(self.host, PORT)
            print((getattr(self, self.cmd))(self.uri, CRLF.join(self.cl_content)))
        except:
            raise Exception("Wrong command")

    def HEAD(self, uri, header):
        return "".join(self.__send_cmd("%s %s %s%s" % ("HEAD", uri, VERSION + CRLF, header + CRLF + CRLF)))

    def POST(self, uri, content):
        print("CONTENT: " + content)
        header, body = CRLF.join([x for x in content.split(CRLF) if ":" in x]), "&".join([y for y in content.split(CRLF) if "=" in y])
        print("BODY: " + body)
        print("HEADER: " + header)
        print("".join(self.__send_cmd("%s %s %s%s%s" % ("POST", uri, VERSION + CRLF, header + CRLF + CRLF, body + CRLF + CRLF))))

    def GET(self, uri, client_header):
        print("HOST: " + self.host)
        print("URI: " + uri)
        path = os.path.normpath("/".join([self.host, uri, filename]))
        print("PATH: " + path)
        if os.path.isfile(path):
            print("FILE EXIST")
            if_modified_since = "If-Modified-Since: %s" % get_mtime_of_file(path)
            msg = "%s %s %s%s%s" % ("GET", uri, VERSION + CRLF, client_header + CRLF, if_modified_since + CRLF + CRLF)
            print(msg)
            (server_header, body) = self.__send_cmd(msg)
            code = server_header.splitlines()[0].split()[1]
            print(server_header)
            if int(code) == 304:
                file_html = open(path, "r+")
                print("READ FROM FILE:")
                print(file_html.read())
                file_html.close()
            else:
                if not self.__cache_page(server_header, client_header, uri):
                    self.__removed_cached_page(path)
                (server_header, body) = self.__send_cmd("%s %s %s%s" % ("GET", uri, VERSION + CRLF, client_header + CRLF + CRLF))
                print(server_header)
                print(body)
        else:
            (server_header, body) = self.__send_cmd("%s %s %s%s" % ("GET", uri, VERSION + CRLF, client_header + CRLF + CRLF))
            self.__cache_page(server_header, client_header, uri)
            print(server_header)
            print(body)

    def __removed_cached_page(self, path):
        os.remove(path)
        while path != path.split("/", 1)[0]:
            path = path.rsplit("/", 1)[0]
            if os.listdir(path) == []:
                os.rmdir(path)
            else:
                break
        return True

    def __cache_page(self, server_header, client_header, uri="/"):
        if self.__get_max_age(server_header) > 0:
            (server_header, body) = self.__send_cmd("%s %s %s%s" % ("GET", uri, VERSION + CRLF, client_header + CRLF))
            print(server_header)
            print(body)
            if body:
                if not os.path.isdir(self.host):
                    os.mkdir(self.host)
                file_html = open(os.path.normpath("/".join([self.host, uri, filename])), "w+")
                file_html.write(body)
                file_html.close()
                print("PAGE CACHED")
            return True
        else:
            return False

    def __get_max_age(self, header):
        age_field = list(map(lambda x: [y for y in x.split() if y.startswith("max-age")], header.splitlines()))
        res_age = lambda groups: list(set([x for y in groups for x in y]))
        print(int("".join(res_age(age_field)).split("=")[1]))

    def __connect_to_server(self, host, port):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((host, port))

    def __send_cmd(self, str):
        self.__sock.send(str.encode('ascii'))
        return self.__sock.recv(MAXPAGE).decode('ascii').split("%s%s" % (CRLF, CRLF))

    def __get_request_from_client(self, sock):
        request = bytes("", 'ascii')
        while bytes("%s%s" % (CRLF, CRLF), 'ascii') not in request:
            request += sock.recv(MAXLINE)
        try:
            (req, *content) = [x for x in request.decode('ascii').split(CRLF) if x]
            (cmd, uri, version) = req.split()
            print("COMMAND: %s\nURI: %s\nVERSION: %s" % (cmd, uri, version))
            if version != VERSION:
                raise Exception("Wrong HTTP version: use HTTP/1.1")
            return cmd, uri, content
        except:
            raise Exception("Wrong request")

def start_server():
    server = socketserver.TCPServer((HOST, PORT_HTTP), Proxy)
    server.allow_reuse_address = True
    server.serve_forever()

#Proxy("www.bbc.co.uk", 80)
start_server()