# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
import json


class Account(KBEngine.Entity):
    def __init__(self):
        KBEngine.Entity.__init__(self)
        DEBUG_MSG("Account::__init__:%s." % (self.__dict__))

    def callClientFunction(self, arg):
        """
        :param arg:
        :return:
        """
        DEBUG_MSG("Account::callClientFunction:%s." % (self.__dict__))

    def retAccountInfo(self, arg):
        """

        :param arg:
        :return:
        """
        DEBUG_MSG("Account::callClientFunction:%s." % (self.__dict__))

    def joinGoldRoom(self):
        """
        :return:
        """
        _py_dic = {"func": "JoinRoom", "args": ["RoomType1", "gold", 1]}
        _json_data = json.dumps(_py_dic)
        self.base.clientReq(_json_data)
