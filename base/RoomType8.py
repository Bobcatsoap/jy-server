# -*- coding: utf-8 -*-
import datetime
import json

import KBEngine

from FrameWork.Mgr import RoomManager
from KBEDebug import *
from RoomBase import *
import time


class RoomType8(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)
        # 最大玩家数量
        self.info["maxPlayersCount"] = 10
        # 底分
        self.info["betBase"] = 10
        # 是否授权买入
        self.info["hasAnthorizeBuying"] = False
        # 房间时间
        self.info["roomTime"] = 10
        # 开房时间
        self.info["createRoomTime"] = int(time.time())
        # 是否开启抢庄
        self.info["hasGrapBanker"] = False
        # 是否推送到俱乐部
        self.info["hasPushToGuild"] = False
        # 房间等级
        self.info["level"] = 0
        self.info["playerInGame"] = {}

    def cellToBase(self, pyDic):
        """

        :param pyDic:
        :return:
        """
        RoomBase.cellToBase(self, pyDic)