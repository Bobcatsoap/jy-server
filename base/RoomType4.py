# -*- coding: utf-8 -*-
import json

import KBEngine
from KBEDebug import *
from RoomBase import *
import time


class RoomType4(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)
        # 最大玩家数量
        self.info["maxPlayersCount"] = 5
        # 底分
        self.info["betBase"] = 1
        # 游戏模式 0：普通模式，1：激情模式 2：疯狂模式
        self.info["playMode"] = 0
        # 最大抢庄
        self.info["maxGrabBanker"] = 4
        # 最大局数
        self.info["maxChapterCount"] = 10
        # 游戏玩法 0：看牌抢庄 1：无花抢庄
        self.info["gamePlay"] = 0
        # 禁止搓牌 勾选为True
        self.info["prohibitedCuoPai"] = False
        # 暗抢庄家 勾选为True
        self.info["darkGrabBanker"] = False
        # 开房时间
        self.info["createRoomTime"] = int(time.time())
        # 是否推送到俱乐部
        self.info["hasPushToGuild"] = False
        # 房间等级
        self.info["level"] = 0
        # 
        self.info["playerInGame"] = {}
        # 特殊牌型
        self.info["cardTypeMultiple"] = None
        # 游戏开始类型
        self.info["gameStartType"] = 0
        # 推注
        self.info["tuiZhu"] = 0
        # 买码
        self.info["maiMa"] = False
        # 推注限制
        self.info["tuiZhuLimit"] = False
        # 下注加倍
        self.info["betDouble"] = False
        # 王赖玩法
        self.info["scorpion"] = 0





