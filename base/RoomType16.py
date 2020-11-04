# -*- coding: utf-8 -*-
import time

import KBEngine
from KBEDebug import *
from RoomBase import *
import Utils
import json


class RoomType16(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)
        # 最大局数
        self.info["maxNum"] = 4
        # 最大玩家数量
        self.info["maxPlayersCount"] = 4
        # 游戏内玩家
        self.info["playerInGame"] = {}
        self.info["createRoomTime"] = int(time.time())
        # 游戏是否开始
        self.gameStart = False
        # 开始时间
        self.startTime = ""
        # 结束时间
        self.endTime = ""
        # 房间玩家
        self.users = ""
        # 游戏结束积分
        self.scores = ""
        # 是否推送俱乐部
        self.info["hasPushToGuild"] = False

    def onRoomInit(self):
        """
        cell--->base
        :return:
        """
        RoomBase.onRoomInit(self)
        DEBUG_MSG("[Room id %s]---------> onRoomInit" % self.info["roomId"] )
        self.roomId = self.info["roomId"]
        self.startTime = Utils.getStrNowTime()

    def loginToRoom(self, account):
        """
        某个Entity请求登录到该房间
        :param account: 要进入本房间的实体account
        """
        if len(self.users) == 0:
            self.users = str(account.userId)
        else:
            self.users += "," + str(account.userId)
        self.entities[account.id] = account
        _args = [self.info["type"], self.info["roomType"], self.info["roomId"]]
        account.callClientFunction("JoinRoomSuccess", _args)

    def logoutRoom(self, entityId):
        """
        某个玩家请求登出该场景
        :param entityId: 登出者的id
        """
        account = self.entities[entityId]
        self.users = self.users.replace(str(account.userId), "")
        self.users = self.users.replace(",,", ",")

        if entityId in self.entities:
            del self.entities[entityId]

        # 通知scene的cell部分，有人离开了
        if self.cell is not None:
            self.cell.onLeave(entityId)

    # def onGetCell(self):
    #     """
    #     entity的cell部分被创建成功
    #     """
    #     DEBUG_MSG("[Room id %s]---------> onGetCell" % self.id)
    #     self.cell.baseToCell({"func": "# ", "dic": self.info, "roomConfig": self.roomConfig})

    def onDestroy(self):
        """
        entity的cell部分被销毁
        :return:
        """
        DEBUG_MSG("[Room id %s]---------> onDestroy" % self.id)
        RoomBase.onDestroy(self)
        self.endTime = Utils.getStrNowTime()

    def roomEnd(self, args):
        """
        args {entityId: [userId, score], ...}
        :param args:
        :return:
        """
        DEBUG_MSG("[RoomType15 id %s]---------> roomEnd type(%s) args %s" % (self.id, type(args), args))
        info = {}
        max_score = -1
        for k, v in args.items():
            info[v[0]] = v[1]
            if v[1] >= max_score:
                max_score = v[1]
        self.scores = json.dumps(info)
        self.writeToDB()

    def chapterStart(self, args):
        DEBUG_MSG("[RoomType15 id %s]---------> chapterStart args %s" % (self.id, args))
        cn = args["cn"]
        self.gameStart = True
        if cn == 0:
            for entity in self.entities.values():
                rs = json.loads(entity.rooms)
                rs.append(self.databaseID)
                entity.rooms = json.dumps(rs)

    def chapterEnd(self, args):
        DEBUG_MSG("[RoomType15 id %s]---------> chapterEnd args %s" % (self.id, args))
        # msg = json.dumps(args)
        cn = args["cn"]
        entity = self.createUserEntity
        # payType: 1:房主支付;2:AA支付
        if cn == 0:
            if self.roomConfig["payType"] == 1:
                # 第一局结束，扣钻石
                subtract = self.roomConfig["juShu"] // 8 * 10 * self.roomConfig["playerNum"]
                room_card = entity.roomCard
                entity.roomCard = room_card - subtract
                # 同步钻石数量
                entity.callClientFunction("pro_roomCard", [entity.roomCard])
            elif self.roomConfig["payType"] == 2:
                subtract = self.roomConfig["juShu"] // 8 * 10
                for en in self.entities:
                    room_card = en.roomCard
                    en.roomCard = room_card - subtract
                    # 同步钻石数量
                    en.callClientFunction("pro_roomCard", [en.roomCard])


