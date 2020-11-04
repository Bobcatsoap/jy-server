import os
import time

from pay.alipay import AliPay, ISVAliPay

current_dir = os.path.dirname(os.path.realpath(__file__))


def get_app_certs():
    path = os.path.join(current_dir, "keys/app")
    return (
        os.path.join(path, "app_private_key.pem"),
        os.path.join(path, "app_public_key.pem")
    )


_ali_pay = None
_return_url = "http://122.114.150.35:56789/alipay"


def init():
    _app_private_key_path, _app_public_key_path = get_app_certs()
    print(_app_private_key_path)
    global _ali_pay
    _ali_pay = AliPay(
        appid="2016091700530792",
        app_notify_url="http://122.114.150.35:56789/alipay",
        app_private_key_path=_app_private_key_path,
        alipay_public_key_path=_app_public_key_path,
        sign_type="RSA2",
        debug=True
    )


def get_order_info(_out_trade_no, _amount, _subject="金币", _type="app"):
    global _ali_pay, _return_url
    if _type == "app":
        # app
        query_params = _ali_pay.api_alipay_trade_app_pay(
            out_trade_no=_out_trade_no,
            total_amount=_amount,
            subject=_subject,
            return_url=_return_url
        )
    else:
        # web
        query_params = _ali_pay.api_alipay_trade_page_pay(
            out_trade_no=_out_trade_no,
            total_amount=_amount,
            subject=_subject,
            return_url=_return_url
        )
        query_params = "https://openapi.alipaydev.com/gateway.do?{0}".format(query_params)
    # print(query_params)
    return query_params

# init()
# get_order_info(100)
# get_order_info(100,"金币","web")
