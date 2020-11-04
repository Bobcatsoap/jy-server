# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
from RoomBase import *
import json
import sys
import time


class RoomType1(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)
        # 最大玩家数量
        self.info["maxPlayersCount"] = 9
        # 底分
        self.info["betBase"] = 10
        # 是否授权买入
        self.info["hasAnthorizeBuying"] = False
        # 最大局数
        self.info["maxRound"] = sys.maxsize
        # 比牌局数
        self.info["compareCardRound"] = 0
        # 看牌局数
        self.info["lookCardRound"] = 0
        # 房间时间
        self.info["roomTime"] = 10
        # 创建房间时间
        self.info["createRoomTime"] = int(time.time())
        # 是否推送到俱乐部
        self.info["hasPushToGuild"] = False
        # 是否开启防作弊
        self.info["hasPreventCheat"] = False
        # 加注规则 1:2倍 2:4倍 3:同分 4:无限
        self.info["addBetRule"] = 0
        # 房间等级
        self.info["level"] = 0
        # 在游戏中的玩家
        self.info["playerInGame"] = {}

    def cellToBase(self, pyDic):
        """

        :param pyDic:
        :return:
        """
        RoomBase.cellToBase(self, pyDic)
        _func_name = pyDic["func"]
