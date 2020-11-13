# coding:utf-8
import urllib.parse
import urllib.request
import datetime
import hashlib
import json
import ssl

# 短信配置 微信配置
# --------------------------------------------------------------------------------------------
#                              第三方短信服务相关
# --------------------------------------------------------------------------------------------
def sendVerificationCode(_phone_num, _code):
    """
    获取短信验证码
    :param _phone_num:
    :param _code:
    :return:
    """
    # 帐号
    _user_name = "guojin"
    _user_name = urllib.parse.quote(_user_name, encoding='gb2312')
    # 密码
    _now = datetime.datetime.now().strftime('%b-%d-%Y %H:%M:%S')
    _now = str(datetime.datetime.strptime(_now, '%b-%d-%Y %H:%M:%S'))
    _password = "guojin123"
    _password_time_md5 = hashlib.md5((_password + _now).encode("utf-8")).hexdigest()
    # 目标手机号码
    _mobiles = str(_phone_num)
    # 内容
    _content = "%s（手机绑定验证码，验证码五分钟内有效），如非本人操作，请忽略该短信。【亲友娱乐】" % _code
    _content = urllib.parse.quote(_content, encoding='gb2312')
    # 发送请求
    _url = "http://api.sms1086.com/Api/verifycode.aspx?username=%s&password=%s&mobiles=%s&content=%s&f=1&timestamp=%s" % (
        _user_name, _password_time_md5, _mobiles, _content, urllib.parse.quote(_now))
    _response = urllib.request.urlopen(_url)
    # 返回结果编码
    _str = _response.read().decode('utf-8')
    _strs = _str.split('&', 1)
    _str = _strs[0].split('=')[1]
    return _str


def send_message(phone_num, content, account_db_id):
    """
    发送短信
    :param  _phone_num:
    :param  _code:
    :return:
    """
    #  帐号
    _user_name = "guojin"
    _user_name = urllib.parse.quote(_user_name, encoding='gb2312')
    #  密码
    _now = datetime.datetime.now().strftime('%b-%d-%Y  %H:%M:%S')
    _now = str(datetime.datetime.strptime(_now, '%b-%d-%Y  %H:%M:%S'))
    _password = "guojin123"
    _password_time_md5 = hashlib.md5((_password + _now).encode("utf-8")).hexdigest()
    #  目标手机号码
    _mobiles = str(phone_num)
    content = "【芒果小食】您的验证码是%s，手机号%s，10分钟有效，请勿泄露。" % (account_db_id, content)
    #  内容
    _content = urllib.parse.quote(content, encoding='gb2312')
    #  发送请求
    _url = "http://api.sms1086.com/Api/Send.aspx?username=%s&password=%s&mobiles=%s&content=%s&f=1&timestamp=%s" % (
        _user_name, _password_time_md5, _mobiles, _content, urllib.parse.quote(_now))
    _response = urllib.request.urlopen(_url)
    print(_response)
    #  返回结果编码
    _str = _response.read().decode('utf-8')
    _strs = _str.split('&', 1)
    _str = _strs[0].split('=')[1]
    return _str


# --------------------------------------------------------------------------------------------
#                              支付宝订单信息
# --------------------------------------------------------------------------------------------
def reqAlipayOI(_orders_id, _amount, _subject="金币", _type="app"):
    """

    :param _orders_id:
    :param _amount:
    :param _subject:
    :param _type:
    :return:
    """
    # 发送请求
    _url = "http://localhost:45678/alipayOI"
    _data = json.dumps({'orders_id': str(_orders_id), 'amount': str(_amount), 'subject': _subject, 'type': _type})
    _response = urllib.request.urlopen(_url, data=_data.encode())
    # 返回结果编码
    _str = _response.read().decode('utf-8')
    return _str


# --------------------------------------------------------------------------------------------
#                              微信登录
# --------------------------------------------------------------------------------------------
def req_wx_asset_token(_code):
    """
    微信登录配置
    """
    # 发送请求
    _app_id = "wx88ab5f31ca993bc8"
    _secret = "1078be709c7976c67c2026b612db2fa4"
    _url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code" % (
        _app_id, _secret, _code)
    context = ssl._create_unverified_context()
    _response = urllib.request.urlopen(_url, context=context)
    # 返回结果编码
    _str = _response.read().decode('utf-8')
    print(_str)
    return _str


def req_wx_user_info(_access_token, _openid):
    # 发送请求
    _url = "https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%s" % (
        _access_token, _openid)
    context = ssl._create_unverified_context()
    _response = urllib.request.urlopen(_url, context=context)
    # 返回结果编码
    _str = _response.read().decode('utf-8')
    return _str