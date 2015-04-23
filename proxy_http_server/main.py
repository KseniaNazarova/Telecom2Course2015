__author__ = 'Ksenia'

import os
import socket
import socketserver
import threading
from urllib.parse import urlparse
from distutils.dir_util import mkpath
from re import sub

HOST_HTTP = 'www.example.com'
HOST = '127.0.0.1'
PORT_HTTP = 8080
PORT = 80
MAXLINE = 1024
MAXPAGE = 65535
CODESIZE = 3
CRLF = '\r\n'
VERSION = 'HTTP/1.1'
CHARSET = 'utf-8'
filename = 'index.html'

def get_mtime_of_file(file):
    from time import gmtime, time
    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    year, month, day, hh, mm, ss, wd, y, z = gmtime(os.path.getmtime(file))
    return '%s, %02d %3s %4d %02d:%02d:%02d GMT' % (weekdayname[wd], day, monthname[month], year, hh, mm, ss)

class Proxy(socketserver.StreamRequestHandler):

    def handle(self):
        self.__sock_cl = self.request
        (self.cmd, self.uri, self.cl_content) = self._get_request_from_client(self.__sock_cl)
        self.cl_content = [x for x in self.cl_content if not x.startswith('Accept-Encoding')]
        self.cl_content.append('Accept-Encoding: ' + CHARSET)

        print(self.cl_content)
        self.host = ''.join([x.split(':')[1].strip() for x in self.cl_content if x.lower().startswith('host')])
        try:
            self._connect_to_HTTP_server(self.host, PORT)
            print((getattr(self, self.cmd))(self.uri, CRLF.join(self.cl_content)))
        except:
            raise Exception('Wrong command')

    def HEAD(self, uri, header):
        return ''.join(self._send_cmd('%s %s %s%s' % ('HEAD', uri, VERSION + CRLF, header + CRLF + CRLF)))

    def POST(self, uri, content):
        print('CONTENT: ' + content)
        header, body = CRLF.join([x for x in content.split(CRLF) if ':' in x]), '&'.join([y for y in content.split(CRLF) if '=' in y])
        print('BODY: ' + body)
        print('HEADER: ' + header)
        print(''.join(self._send_cmd('%s %s %s%s%s' % ('POST', uri, VERSION + CRLF, header + CRLF + CRLF, body + CRLF + CRLF))))

    def GET(self, uri, client_header):
        print("HOST: " + self.host)
        print("URI: " + uri)
        path = os.path.normpath("/".join([self.host, urlparse(uri).path, filename]))
        print("PATH: " + path)
        if os.path.isfile(path):
            print("FILE EXIST")
            if_modified_since = "If-Modified-Since: %s" % get_mtime_of_file(path)
            msg = "%s %s %s%s%s" % ("GET", uri, VERSION + CRLF, client_header + CRLF, if_modified_since + CRLF + CRLF)
            print(msg)
            (server_header, body) = self._send_cmd(msg)
            code = server_header.splitlines()[0].split()[1]
            print(server_header)
            if int(code) == 304:
                file_html = open(path, "r+")
                print("READ FROM FILE:")
                self._send_response_to_client(self.HEAD(uri, "Host: " + self.host), file_html.read())
                file_html.close()
                return True
        print("TRY TO CACHE 1")
        (server_header, body) = self._send_cmd("%s %s %s%s" % ("GET", uri, VERSION + CRLF, client_header + CRLF + CRLF))
        print("SERVER HEADER: ")
        print(server_header)
        code = server_header.splitlines()[0].split()[1]
        print("RESPONSE CODE: ")
        print(code)
        if str(code) in ['200', '206', '302']:
            print("CODE IN")
            self._send_response_to_client(server_header, body)
            if not self._cache_page(server_header, body, uri):
                if os.path.isfile(path):
                    self._removed_cached_page(path)
            return True
        else:
            self._send_response_to_client(server_header, "Code error: " + str(code))

    def _removed_cached_page(self, path):
        os.remove(path)
        while path != path.split("/", 1)[0]:
            path = path.rsplit("/", 1)[0]
            if os.listdir(path) == []:
                os.rmdir(path)
            else:
                break
        return True

    def _cache_page(self, server_header, body, uri="/"):
        if self._get_max_age(server_header) > 0:
            path = os.path.normpath("/".join([self.host, urlparse(uri).path, filename]))
            print("TRY TO CACHE PAGE")
            if not os.path.isdir(path.rpartition(os.path.sep)[0]):
                mkpath(path.rpartition(os.path.sep)[0])
            print("PATH: " + path)
            file_html = open(path, "w+")
            file_html.write(body)
            file_html.close()
            print("PAGE CACHED")
            return True
        else:
            return False

    def _get_max_age(self, header):
        print("HEADER:")
        print(header)
        age_field = list(map(lambda x: [y for y in x.split() if y.startswith("max-age")], header.splitlines()))
        if not self._isListEmpty(age_field):
            res_age = lambda groups: list(set([x for y in groups for x in y]))
            return int(sub('[,;]','', ''.join(res_age(age_field))).split('=')[1])
        else:
            return 0

    def _connect_to_HTTP_server(self, host, port):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((host, port))

    def _send_cmd(self, str):
        self.__sock.send(str.encode(CHARSET))
        return self.__sock.recv(MAXPAGE).decode(CHARSET).split("%s%s" % (CRLF, CRLF), 1)

    def _get_request_from_client(self, sock):
        request = bytes("", CHARSET)
        while bytes("%s%s" % (CRLF, CRLF), CHARSET) not in request:
            request += sock.recv(MAXLINE)
        try:
            (req, *content) = [x for x in request.decode(CHARSET).split(CRLF) if x]
            (cmd, uri, version) = req.split()
            print("COMMAND: %s\nURI: %s\nVERSION: %s" % (cmd, uri, version))
            if version != VERSION:
                raise Exception("Wrong HTTP version: use HTTP/1.1")
            return cmd, uri, content
        except:
            raise Exception("Wrong request")

    def _send_response_to_client(self, header, body):
        print(header)
        print(body)
        l = self.__sock_cl.send(bytes("%s%s" % (header + CRLF, body + CRLF + CRLF), CHARSET))
        print(l)

    def _isListEmpty(self, inList):
        if isinstance(inList, list):
            return all( map(self._isListEmpty, inList))
        return False

def start_server():
    server = socketserver.TCPServer((HOST, PORT_HTTP), Proxy)
    server.allow_reuse_address = True
    server.serve_forever()

start_server()