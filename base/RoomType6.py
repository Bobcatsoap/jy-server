# -*- coding: utf-8 -*-
import time

from RoomBase import *


class RoomType6(RoomBase):

    def __init__(self):
        RoomBase.__init__(self)
        # 最大玩家数量
        self.info["maxPlayersCount"] = 10
        # 是否授权买入
        self.info["hasAnthorizeBuying"] = False
        # 房间时间
        self.info["roomTime"] = 10
        # 开房时间
        self.info["createRoomTime"] = int(time.time())
        # 是否推送到俱乐部
        self.info["hasPushToGuild"] = False
        self.info["level"] = 1
        self.info["playerInGame"] = {}

    def cellToBase(self, pyDic):
        """
        :param pyDic:
        :return:
        """
        # 1 先继承父类的方法  然后重写自己有特点的方法
        RoomBase.cellToBase(self, pyDic)
        _func_name = pyDic["func"]
        # 1 换桌
        if _func_name == "changeTable":
            account_id = pyDic["accountId"]
            type = pyDic["type"]
            level = pyDic["level"]
            player_entity = KBEngine.entities[account_id]
            DEBUG_MSG("cellToBase------player_entity %s" % player_entity)

            player_entity.call_client_func("changeTable", {})
        elif _func_name == "continueNextChallenge":
            # 准备关服维护
            if self.room_mgr.is_snoring_all_room():
                self.call_client_func("Notice", [self.room_mgr.snoring_msg])
                return
            account_id = pyDic["accountId"]
            player_entity = KBEngine.entities[account_id]
            challenge_mgr = KBEngine.globalData['ChallengeAreaManager'].mgr
            challenge_mgr.enter_challenge_area(pyDic['challengeLevel'], player_entity.databaseID)
