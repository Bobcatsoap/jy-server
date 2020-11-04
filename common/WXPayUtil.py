import hashlib
import time
import xml.dom.minidom as xmldom
import urllib.request


def get_sign(params, key):
    '''
    获取签名
    :param params: 支付参数按字典序排序的集合
    :param key: 密钥
    :return:
    '''
    s = ""
    for k, v in params.items():
        s += k + "=" + v + "&"
    s += "key" + "=" + key
    s = s.encode("utf-8")
    m2 = hashlib.md5()
    m2.update(s)
    return m2.hexdigest().upper()


def to_xml(params):
    s = "<xml>"
    for k, v in params.items():
        s += "<" + k + ">" + "<![CDATA[" + v + "]]></" + k + ">"
    s += "</xml>"
    return s


def parse_xml_to_dict(xml_string):
    domobj = xmldom.parseString(xml_string)
    elementobj = domobj.documentElement
    cns = elementobj.childNodes
    params = dict()
    for node in cns:
        if type(node) == xmldom.Element:
            params[node.tagName] = node.firstChild.data
    return params


def req_wx_prepayid(order_id, spbill_create_ip, total_fee):
    """
    :param spbill_create_ip: 提交支付的用户的ip
    :param total_fee: 单位:分
    :return:
    """
    key = "709fdf4b783a864f60de92b874bd7a52"
    wxpay_url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
    params = dict()
    params["appid"] = "wxd4d0adb30a11c550"
    params["body"] = "游戏充值"
    params["mch_id"] = "1484556012"
    params["nonce_str"] = str(int(time.time()))
    params["notify_url"] = "http://122.114.150.35:12345/"
    params["out_trade_no"] = order_id
    params["spbill_create_ip"] = spbill_create_ip
    params["total_fee"] = str(total_fee)
    params["trade_type"] = "MWEB"
    sign = get_sign(params, key)
    params["sign"] = sign
    req_body = to_xml(params)
    req_body = req_body.encode("utf-8")
    req = urllib.request.Request(url=wxpay_url, data=req_body)
    result = urllib.request.urlopen(req).read()
    result = result.decode("utf-8")
    res_params = parse_xml_to_dict(result)
    if res_params["return_code"] == "SUCCESS":
        return res_params["mweb_url"]
    else:
        print(res_params)