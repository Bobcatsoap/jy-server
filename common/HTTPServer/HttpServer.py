# coding:utf-8
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import urllib.request
import io, shutil
import json
from pay import AliPay
import HttpRequest

current_dir = os.path.dirname(os.path.realpath(__file__))
path = current_dir
sys.path.append(path)


# from HTTPServer.pay import AliPay
# from HTTPServer import HttpRequest


server = None


def startServer(_port):
    """

    :param _port:
    :return:
    """
    addr = ('', _port)
    global server
    server = HTTPServer(addr, RequestHandler)
    server.serve_forever()


# def startInThread(port):
#     thread = Thread(target=startServer, args=[port])
#     thread.start()
#
#     _start_time = int(time.time())
#     while not server:
#         if int(time.time()) > _start_time + 5:
#             print("Time out")
#             break
#     print("[HttpServer] start success")
#     return server


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """

        :return:
        """
        mpath, margs = urllib.parse.splitquery(self.path)  # ?分割
        self.do_get(mpath, margs)

    def do_get(self, path, args):
        _fun = args.decode()
        print(args)
        if _fun == "alipayOI":
            self.outputtxt("getData")

    def do_POST(self):
        mpath, margs = urllib.parse.splitquery(self.path)
        datas = self.rfile.read(int(self.headers['content-length']))
        self.do_post(mpath, margs, datas)

    def do_post(self, path, margs, datas):
        print("POST path = %s margs = %s datas = %s" % (path, margs, datas))
        if path == "/alipayOI":
            _json = datas.decode()
            _dic = json.loads(_json)
            # print(_dic)
            _orders_id = _dic["orders_id"]
            _subject = _dic["subject"]
            _amount = _dic["amount"]
            _type = _dic["type"]
            _code = AliPay.get_order_info(_orders_id, float(_amount), _subject, _type)
            self.outputtxt(_code)
        else:
            pass

    def outputtxt(self, content):
        # 指定返回编码
        enc = "UTF-8"
        content = content.encode(enc)
        f = io.BytesIO()
        f.write(content)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        shutil.copyfileobj(f, self.wfile)


AliPay.init()
startServer(45678)
