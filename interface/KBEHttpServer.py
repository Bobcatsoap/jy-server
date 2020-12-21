import urllib.parse
import urllib.request
import Const
from KBEHTTPServer import MinHTTPServer
import random
import DBCommand

from KBEDebug import *
from HTTPServer import HttpRequest
import json
import ssl


def tourist(req, resp):
    def getTouristAccount():
        """
        游客账号
        :return:
        """
        seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&()_+=-"
        sa = []
        for i in range(9):
            sa.append(random.choice(seed))
        salt = ''.join(sa)
        return "a*" + salt

    _name = getTouristAccount()
    INFO_MSG('[interface KBEHttpServer] tourist accountName %s' % _name)
    resp.body = _name.encode()
    resp.end()


def wx_code(req, resp):
    INFO_MSG('[KBEHttpServer] datas = %s' % req.datas)
    INFO_MSG('[KBEHttpServer] method = %s' % req.method)
    INFO_MSG('[KBEHttpServer] url = %s' % req.url)
    # INFO_MSG('[KBEHttpServer] version = %s' % req.version)
    _code = req.params.get('code', None)
    INFO_MSG('[KBEHttpServer] wx_code params = %s code = %s' % (req.params, _code))
    _result = HttpRequest.req_wx_asset_token(_code)
    INFO_MSG('[KBEHttpServer] wx_code _result = %s' % _result)
    _dic = json.loads(_result)
    _asset_token = _dic["access_token"]
    _open_id = _dic["openid"]
    INFO_MSG('[KBEHttpServer] wx_code _asset_token = %s _open_id = %s' % (_asset_token, _open_id))
    _account = "w*" + _open_id
    _password = "123456"
    _r_dic = {"access_token": _asset_token, "account": _account, "password": _password, "refresh_token": _dic["refresh_token"]}
    INFO_MSG('[_r_dic] wx_code access_token = %s account = %s password=%s refresh_token=%s' % (_asset_token, _account, _password, _dic["refresh_token"]))
    resp.body = json.dumps(_r_dic).encode()
    resp.end()


def wx_public_hao_user_info(req, resp):
    """
    获取点击微信公众号的玩家信息
    :param req:
    :param resp:
    :return:
    """
    _code = req.params.get('code', None)
    user_id = int(req.params.get('state', None))
    
    _app_id = "wxc886ed4534c46ffd"
    _secret = "385801f848faca703e83fc6e1bd28647"
    _url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code" % (
        _app_id, _secret, _code)
    context = ssl._create_unverified_context()
    _response = urllib.request.urlopen(_url, context=context)
    # 返回结果编码
    _result = _response.read().decode('utf-8')
    INFO_MSG('[KBEHttpServer] wx_public_hao_user_info = %s' % _result)
    _dic = json.loads(_result)

    DBCommand.update_invite_code_relations(user_id, _dic["unionid"])
    resp.body = 'success'.encode()
    resp.end()


def alipay(req, resp):
    INFO_MSG('[interface KBEHttpServer] alipay')
    out_trade_no = req.params.get('out_trade_no', None)
    KBEngine.chargeResponse(out_trade_no, b's', KBEngine.SERVER_SUCCESS)
    resp.body = 'success'.encode()
    resp.end()


def phoneRegister(req, resp):
    """
    手机注册
    这里验证码直接发给客户端，客户端负责对比，时间控制
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] phoneRegister req.params=%s' % req.params)
    _phoneNumber = req.params.get('phoneNumber', None)
    _code = random.randint(100000, 999999)
    HttpRequest.sendVerificationCode(_phoneNumber, _code)
    resp.body = str(_code).encode()
    resp.end()


def setPassword(req, resp):
    """
    重设密码
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] setPassword req.params=%s' % req.params)
    _accountName = req.params.get('accountName', None)
    _newPassword = req.params.get('newPassword', None)

    def callback(error):
        if error:
            _data = {"accountName": _accountName, "password": _newPassword, "result": 0, "error": error}
            resp.body = json.dumps(_data).encode()
            resp.end()
            return
        _data = {"accountName": _accountName, "password": _newPassword, "result": 1, "error": None}
        resp.body = json.dumps(_data).encode()
        resp.end()
        DEBUG_MSG("setPassword------>body = %s" % resp.body)

    DBCommand.setAccountPassword(_accountName, _newPassword, callback)


def check_game_version(req, resp):
    client_version = req.params.get('clientVersion', None)
    result = {}
    if str(client_version) == Const.GameVersion:
        # 成功
        result["result"] = 1
        result["downloadUrl"] = ""
    else:
        # 失败
        result["result"] = 0
        result["downloadUrl"] = "https://lifetech.me/cnBI08"
        result["updateUrl"] = "http://cdn-src.by4m4sk.cn/"
        result["updateApkName"] = "xyhy-release-8-29.apk"
    resp.body = json.dumps(result).encode()
    resp.end()


def req_company_info_state(req, resp):
    """
    请求首页公司信息
    :param req:
    :param resp:
    :return:
    """
    s='''抵制不良游戏,拒绝盗版游戏,注意自我保护,谨防上当受骗,适度游戏益脑,沉迷游戏伤身,合理安排时间,享受健康生活'''
    _data = '''抵制不良游戏,拒绝盗版游戏,注意自我保护,谨防上当受骗,适度游戏益脑,沉迷游戏伤身,合理安排时间,享受健康生活
著作权人:郑州国金科技有限公司  出版单位:郑州国金科技有限公司
豫网文[2017]  5320-139 号'''
    resp.body = json.dumps(s).encode()
    resp.end()


server = None


def start():
    global server
    server = MinHTTPServer.MinHTTPServer()
    server.listen(56719)
    # server.staticRes('html')
    server.route('/getTouristAccount', tourist)
    server.route('/wxCode', wx_code)
    server.route('/alipay', alipay)
    server.route('/phoneRegister', phoneRegister)
    server.route('/setPassword', setPassword)
    server.route('/CheckGameVersion', check_game_version)
    server.route('/reqCompanyInfo', req_company_info_state)
    server.route('/wx_public_hao_user_info', wx_public_hao_user_info)


def stop():
    server.stop()

