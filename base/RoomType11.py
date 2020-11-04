# -*- coding: utf-8 -*-
from RoomBase import *
import time


class RoomType11(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)
        # 最大玩家数量
        self.info["maxPlayersCount"] = 10
        # 开房时间
        self.info["createRoomTime"] = int(time.time())
        # 房间等级
        self.info["level"] = 0
        self.info["playerInGame"] = {}

    def cellToBase(self, py_dic):
        """

        :param py_dic:
        :return:
        """
        RoomBase.cellToBase(self, py_dic)
        _func_name = py_dic["func"]
