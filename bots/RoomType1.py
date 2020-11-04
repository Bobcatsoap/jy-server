# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *


class RoomType1(KBEngine.Entity):
    def __init__(self):
        KBEngine.Entity.__init__(self)
        DEBUG_MSG("Account::__init__:%s." % (self.__dict__))

    def retChapterSysPrompt(self, str):
        """
        :param str:
        :return:
        """

    def dealCardsToPlayer(self, location, cards):
        """

        :param location:
        :param cards:
        :return:
        """

    def retRoomBaseInfo(self, json_data):
        """

        :param json_data:
        :return:
        """

    def retLocationIndexs(self, json_data):
        """

        :param json_data:
        :return:
        """

    def callClientFunction(self, json_data):
        """
        :param json_data:
        :return:
        """
