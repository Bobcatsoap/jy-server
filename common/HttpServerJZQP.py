# coding:utf-8
from http.server import HTTPServer, SimpleHTTPRequestHandler

server = None


def startServer(_port):
    """

    :param _port:
    :return:
    """
    addr = ('', _port)
    global server
    server = HTTPServer(addr, SimpleHTTPRequestHandler)
    server.serve_forever()


startServer(12345)
