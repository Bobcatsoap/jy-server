# -*- coding: utf-8 -*-
import time

import KBEngine
from KBEDebug import *
from RoomBase import *


class RoomType3(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)

    def newChapter(self, maxPlayerCount=100):
        """
        :param maxPlayerCount:
        :return:
        """
        _chapter = RoomBase.newChapter(self, maxPlayerCount)
        # 牌局所有计时器id
        _chapter["timers"] = {
            # 牌局主计时器
            "main": -1,
            # 机器人下注计时器
            "botBet": -1,
        }
        # 闲注数和
        _chapter["sumBetFree"] = 0
        # 庄注数和
        _chapter["sumBetBanker"] = 0
        # 和注数和
        _chapter["sumBetDraw"] = 0
        # 庄对注数和
        _chapter["sumBetFreeDouble"] = 0
        # 闲对注数和
        _chapter["sumBetBankerDouble"] = 0
        # 当前计时时刻点
        _chapter["deadline"] = -1

    def newPlayer(self, accountEntity):
        """
        :param accountEntity:
        :return:
        """
        _player = RoomBase.newPlayer(self, accountEntity)
        # 闲注数和
        _player["sumBetFree"] = 0
        # 庄注数和
        _player["sumBetBanker"] = 0
        # 和注数和
        _player["sumBetDraw"] = 0
        # 庄对注数和
        _player["sumBetFreeDouble"] = 0
        # 闲对注数和
        _player["sumBetBankerDouble"] = 0

    def newStatisticalData(self):
        """
        全局数据
        :return:
        """
        self.statisticalData = {
            # 神算子eId
            "sszEId": -1,
            # 大富豪eId
            "dfhEId": -1,
            # 玩家记录列表
            "rankingList": [],
            # 玩家历史记录
            "playersHistory": {},
            # 机器人习惯相关配置
            "botAi": {},
            # 牌局历史记录
            "chapterHistory": {
                # 胜负记录 珠盘路
                "winHistory": [],
                # 大路
                "hMapping1": [],
                # 大眼仔
                "hMapping2": [],
                # 甲由路
                "hMapping3": [],
                # 小路
                "hMapping4": [],
            }
        }

    def updateMapping(self):
        """

        :return:
        """
        _chapter_history = self.statisticalData["chapterHistory"]
        _win_history = _chapter_history["winHistory"]
        _t = []
        for i in _win_history:
            _t.append(int(i / 10))
        _mapping_1 = updateMapping1(_t)
        _chapter_history["hMapping1"] = _mapping_1
        _chapter_history["hMapping2"] = updateMapping2(_mapping_1, 1, 1)
        _chapter_history["hMapping3"] = updateMapping2(_mapping_1, 2, 2)
        _chapter_history["hMapping4"] = updateMapping2(_mapping_1, 3, 3)

    def addPlayerInSD(self, _e_id):
        """
        :param _e_id:
        :return:
        """
        # 记录
        _e = KBEngine.entities[_e_id]
        _playerHistory = {
            # 实体id
            "entityId": _e_id,
            # 实体userID
            "userId": _e.info["userId"],
            # 总下注
            "sumBet": 0,
            # 胜负记录
            "winHistory": []
        }
        # 机器人下注偏好
        if _e.info["isBot"] == 1:
            _s_1 = []
            for i in range(0, random.randint(10, 17)):
                _s_1.append(1)
            for i in range(0, random.randint(10, 17)):
                _s_1.append(2)
            for i in range(0, random.randint(0, 3)):
                _s_1.append(3)
            for i in range(0, random.randint(0, 1)):
                _s_1.append(4)
            for i in range(0, random.randint(0, 1)):
                _s_1.append(5)
            _s_2 = []
            # 5, 10, 50 ,100,500,1000,2000,5000
            for i in range(0, random.randint(10, 20)):
                _s_2.append(5)
            for i in range(0, random.randint(10, 15)):
                _s_2.append(10)
            for i in range(0, random.randint(0, 7)):
                _s_2.append(50)
            for i in range(0, random.randint(0, 3)):
                _s_2.append(100)
            for i in range(0, random.randint(0, 1)):
                _s_2.append(500)
            for i in range(0, random.randint(0, 1)):
                _s_2.append(1000)
            _bot_ai = {
                # 龙虎和
                "seed1": _s_1,
                # 下注数
                "seed2": _s_2,
                # 下注概率
                "betProb": random.randint(3, 20),
            }
            self.statisticalData["botAi"][_e_id] = _bot_ai
        _playersHistory = self.statisticalData["playersHistory"]
        _playersHistory[_e_id] = _playerHistory

    def remove_player_from_sd(self, _e_id):
        """
        :param _e_id:
        :return:
        """
        _e = KBEngine.entities[_e_id]
        _playersHistory = self.statisticalData["playersHistory"]
        _playersHistory.pop(_e_id)
        if _e.info["isBot"] == 1:
            self.statisticalData["botAi"].pop(_e_id)

    def refreshRankingList(self):
        """
        刷新排行榜
        :return:
        """
        _playersHistory = self.statisticalData["playersHistory"]
        _l = list(_playersHistory.values())

        if len(_l) == 0:
            return

        def takeWinCount(elem):
            return elem["winHistory"].count(1)

        _elem = max(_l, key=takeWinCount)
        _l.pop(_l.index(_elem))
        self.statisticalData["sszEId"] = _elem["entityId"]

        if len(_l) == 0:
            return

        def takeSumBet(elem):
            return elem["sumBet"]

        _l.sort(key=takeSumBet, reverse=True)
        self.statisticalData["dfhEId"] = _l[0]["entityId"]
        _l.insert(0, _elem)
        _r_l = []
        for i in _l:
            _r_l.append(i["entityId"])
            _r_l.append(i["userId"])
            _r_l.append(i["sumBet"])
            _r_l.append(i["winHistory"].count(1))

            # 查询当前金币
            _e = KBEngine.entities[i["entityId"]]
            _r_l.append(int(_e.accountMutableInfo["goldBean"]))
        self.statisticalData["rankingList"] = _r_l

    # --------------------------------------------------------------------------------------------
    #                            牌局流程
    # --------------------------------------------------------------------------------------------

    def changeChapterState(self, state):
        """
        流程控制
        :param state:0准备阶段1下注2结算
        :return:
        """
        _chapter = self.chapters[self.cn]
        _timers = _chapter["timers"]
        _old = _chapter["chapterState"]
        # 状态却换
        _chapter["chapterState"] = state
        DEBUG_MSG('[Room id %i]------------->changeChapterState to %s' % (self.id, state))
        if _old == -1 and state == 0:
            # 自动模式下开启一个main计时器每隔一定时间检测 是否满足牌局开启条件
            self.retLocations()
            self.callOtherClientsFunction("chapterStateChanged", [state])
            _timers["main"] = self.addTimer(1, 1, 0)
        elif _old == 0 and state == 1:
            # 下注阶段
            self.callOtherClientsFunction("chapterStateChanged", [state])
            # self.retChapterSysPrompt("开始下注")
            self.newCardsLib()
            # 开启一个计时 数秒后进行下一阶段
            _timers["main"] = self.addTimer(17, 0, 0)
            _chapter["deadline"] = time.time() + 17
            # 开启一个计时 用于机器人自动下注
            _timers["botBet"] = self.addTimer(0.5, 0.5, 0)
        elif _old == 1 and state == 2:
            # 结算
            self.callOtherClientsFunction("chapterStateChanged", [state])
            # self.retChapterSysPrompt("小局结算")
            self.settlement()
            # 开启一个计时 数秒后进行下一局
            _timers["main"] = self.addTimer(10, 0, 0)
        else:
            # 不存在的状态切换  抛出异常
            raise Exception('error in changeChapterState')

    def settlement(self):
        """
        结算
        :return:
        """
        DEBUG_MSG('[Room id %i]------------->settlement' % self.id)
        _chapter = self.chapters[self.cn]
        _players = _chapter["players"]
        # 计算赌金池
        _sum_bet = 0
        _sum_bet += _chapter["sumBetFree"]
        _sum_bet += _chapter["sumBetBanker"]
        _sum_bet += _chapter["sumBetDraw"]
        _sum_bet += _chapter["sumBetFreeDouble"]
        _sum_bet += _chapter["sumBetBankerDouble"]
        # 揭示底牌 判断结果
        _cards = _chapter["cardsLib"].copy()
        _cards_1, _cards_2 = randomCards(_cards)
        _cards_1_w = getCardsWeight(_cards_1)
        _cards_2_w = getCardsWeight(_cards_2)
        if _cards_1_w > _cards_2_w:
            _result = 1
        elif _cards_1_w < _cards_2_w:
            _result = 2
        else:
            _result = 3
        _f_1 = isDouble(_cards_1)
        _f_2 = isDouble(_cards_2)
        if _f_1 and _f_2:
            _result_d = 3
        elif _f_1:
            _result_d = 1
        elif _f_2:
            _result_d = 2
        else:
            _result_d = 0
        # 结算
        _bets = {}
        for i in _players.keys():
            _p = _players[i]
            # 计算每个当前玩家要扣除的赌金
            _player_sum_bet = 0
            _player_sum_bet += _p["sumBetFree"]
            _player_sum_bet += _p["sumBetBanker"]
            _player_sum_bet += _p["sumBetDraw"]
            _player_sum_bet += _p["sumBetFreeDouble"]
            _player_sum_bet += _p["sumBetBankerDouble"]
            _bets[i] = -_player_sum_bet
            # 加上赢取的金币
            if _result == 1:
                # 此情况收取手续费
                _v = _p["sumBetFree"] * (1 + 1 * 0.95)
            elif _result == 2:
                _v = _p["sumBetBanker"] * (1 + 1)
            else:
                _v = _p["sumBetDraw"] * (1 + 8)
            if _result_d == 1:
                _v += _p["sumBetFreeDouble"] * (1 + 11)
            elif _result_d == 2:
                _v += _p["sumBetBankerDouble"] * (1 + 11)
            elif _result_d == 3:
                _v += _p["sumBetFreeDouble"] * (1 + 11)
                _v += _p["sumBetBankerDouble"] * (1 + 11)
            _bets[i] += _v
        _playersHistory = self.statisticalData["playersHistory"]
        for k in _bets.keys():
            _gold_add = _bets[k]
            if _gold_add != 0:
                _player = _players[k]
                # 全局统计数据
                _playerHistory = _playersHistory[_player["entity"].id]
                _win_history = _playerHistory["winHistory"]
                if _gold_add > 0:
                    _win_history.append(1)
                else:
                    _win_history.append(0)
                if len(_win_history) > 20:
                    _win_history.pop(0)
                # 处理赌金 对每个玩家的账号金额做增减
                _gold = _player["gold"]
                _gold += _gold_add
                _player_entity = _player["entity"]
                _player["gold"] = _gold
                _player_entity.accountMutableInfo["goldBean"] = _gold
                _player_entity.base.cellToBase(
                    {"func": "setAccountMutableInfo",
                     "dic": {"goldBean": _player_entity.accountMutableInfo["goldBean"]}})
        # 刷新全局玩家下注统计数据排序
        self.refreshRankingList()
        # 统计全局输赢数据 并刷新表格
        _chapter_history = self.statisticalData["chapterHistory"]
        _w_h = _chapter_history["winHistory"]
        _w_h.append(_result * 10 + _result_d)
        if len(_w_h) > 100:
            _w_h.pop(0)
        self.updateMapping()
        # 通知客户端底牌输赢信息
        for i in range(0, 3):
            if i >= len(_cards_1):
                _cards_1.append(-1)
        for i in range(0, 3):
            if i >= len(_cards_2):
                _cards_2.append(-1)
        self.callOtherClientsFunction("settlementInfo",
                                      [_cards_1[0], _cards_1[1], _cards_1[2], _cards_2[0], _cards_2[1], _cards_2[2],
                                       _result * 10 + _result_d])
        # 通知客户端表格信息
        self.callOtherClientsFunction("mapping", _chapter_history["winHistory"])
        self.otherClients.updateMapping("mapping1", _chapter_history["hMapping1"])
        self.otherClients.updateMapping("mapping2", _chapter_history["hMapping2"])
        self.otherClients.updateMapping("mapping3", _chapter_history["hMapping3"])
        self.otherClients.updateMapping("mapping4", _chapter_history["hMapping4"])
        # 将金币为负的机器人移除
        # 通知客户端输赢明细
        _args = []
        for i in _bets.keys():
            _args.append(i)
            _args.append(int(_bets[i]))
        self.callOtherClientsFunction("settlement", _args)

    def newCardsLib(self):
        """
        建立牌库
        :return:
        """
        _chapter = self.chapters[self.cn]
        _cardlib = list(range(0, 52))
        _chapter["cardsLib"] = _cardlib

    def randomCardFromLib(self):
        """
        :return:
        """
        _chapter = self.chapters[self.cn]
        _cardlib = _chapter["cardsLib"]
        _len = len(_cardlib)
        _index = random.randint(0, _len - 1)
        _card = _cardlib.pop(_index)
        return _card

    def betOperation(self, locationIndex, betType, bet):
        """

        :param locationIndex:
        :param betType: 1 闲 2 庄 3 和 4 闲对 5 庄对
        :param bet:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _state = _chapter["chapterState"]
        _players = _chapter["players"]
        # 下注状态才能下注
        if _state != 1:
            return
        # 如果不存在玩家 返回
        if locationIndex not in _players.keys():
            return
        _player = _players[locationIndex]
        # 非本局玩家不能下注
        if not _player["isReady"]:
            return
        # 下注合法性检测
        if betType == 1:
            _player["sumBetFree"] += bet
            _chapter["sumBetFree"] += bet
        elif betType == 2:
            _player["sumBetBanker"] += bet
            _chapter["sumBetBanker"] += bet
        elif betType == 3:
            _player["sumBetDraw"] += bet
            _chapter["sumBetDraw"] += bet
        elif betType == 4:
            _player["sumBetFreeDouble"] += bet
            _chapter["sumBetFreeDouble"] += bet
        elif betType == 5:
            _player["sumBetBankerDouble"] += bet
            _chapter["sumBetBankerDouble"] += bet
        else:
            return
        # 全局统计数据
        _playersHistory = self.statisticalData["playersHistory"]
        _playerHistory = _playersHistory[_player["entity"].id]
        _playerHistory["sumBet"] += bet
        # 玩家剩余金额
        _player_sum_bet = 0
        _player_sum_bet += _player["sumBetFree"]
        _player_sum_bet += _player["sumBetBanker"]
        _player_sum_bet += _player["sumBetDraw"]
        _player_sum_bet += _player["sumBetFreeDouble"]
        _player_sum_bet += _player["sumBetBankerDouble"]
        _bet_residue = _player["gold"] - _player_sum_bet
        # 通知客户端
        # self.retChapterSysPrompt("玩家" + str(locationIndex) + "下注" + str(bet))
        self.callOtherClientsFunction("betResult", [locationIndex, betType, bet, int(_bet_residue)])

    # --------------------------------------------------------------------------------------------
    #                            与客户端交互
    # --------------------------------------------------------------------------------------------

    def playerOperation(self, accountEntityId, jsonData):
        """
        :param accountEntityId:
        :param jsonData:
        :return:
        """
        _player, _operation_name, _args = RoomBase.playerOperation(self, accountEntityId, jsonData)
        if _operation_name == "betOperation":
            self.betOperation(_player["locationIndex"], _args[0], _args[1])
        elif _operation_name == "Reconnect":
            self.reconnect(accountEntityId)

    def reconnect(self, accountId):
        """
        请求重连
        :param accountId: 重连玩家
        :return:
        """
        DEBUG_MSG('[RoomType3 id %i]------>reconnect %s' % (self.id, accountId))
        self.retRoomBaseInfo(accountId)
        self.retLocation(accountId)
        self.retChapterInfo(accountId)

    def retChapterInfo(self, accountId):
        """
        牌局信息
        :return:
        """
        _chapter = self.chapters[self.cn]
        _gold = self.getPlayer(accountId)["gold"]
        self.callClientFunction(accountId, "Reconnect", [str(_chapter["chapterState"]),
                                                         str(int(_chapter["deadline"]) - int(time.time()) - 2),
                                                         str(_gold), str(_chapter["sumBetFree"]),
                                                         str(_chapter["sumBetBanker"]),
                                                         str(_chapter["sumBetDraw"]), str(_chapter["sumBetFreeDouble"]),
                                                         str(_chapter["sumBetBankerDouble"])])

    def retLocation(self, accountId):
        """
        单独通知玩家
        :param accountId:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter["players"]
        _entityIds = []
        _userIds = []
        _locationIndexs = []
        _location_info = {}
        # 神算子大富豪
        _ssz_e_id = self.statisticalData["sszEId"]
        _dfh_e_id = self.statisticalData["dfhEId"]
        if _ssz_e_id != -1:
            _player = self.getPlayer(_ssz_e_id)
            if _player:
                _entityIds.append(_ssz_e_id)
                _userIds.append(_player["entity"].info["userId"])
                _locationIndexs.append(_player["locationIndex"])
        if _dfh_e_id != -1:
            _player = self.getPlayer(_dfh_e_id)
            if _player:
                _entityIds.append(_dfh_e_id)
                _userIds.append(_player["entity"].info["userId"])
                _locationIndexs.append(_player["locationIndex"])
        # 随机剩余玩家
        _c_max = 7 - len(_entityIds)
        _c = 0
        _all_locations = list(_players.keys())
        _all_locations.sort()
        for i in _all_locations:
            _e_ = _players[i]["entity"]
            _entityId = _e_.id
            # 不能和神算子大富豪重复
            if _entityId == _ssz_e_id or _entityId == _dfh_e_id:
                continue
            _entityIds.append(_entityId)
            _userIds.append(_e_.info["userId"])
            _locationIndexs.append(i)
            _c += 1
            if _c >= _c_max:
                break
        _location_info["entityIds"] = _entityIds
        _location_info["userIds"] = _userIds
        _location_info["locationIndexs"] = _locationIndexs
        # 分别通知客户端
        for _p in _players.values():
            _e = _p["entity"]
            if _e.id != accountId:
                continue
            if _e.info["isBot"] == 0:
                _id = _e.id
                _user_id = _e.info["userId"]
                _location_ = _p["locationIndex"]
                _e_s = _entityIds.copy()
                _u_s = _userIds.copy()
                _l_s = _locationIndexs.copy()
                # 不能和自身重复
                if _id in _e_s:
                    _e_s.pop(_e_s.index(_id))
                if _user_id in _u_s:
                    _u_s.pop(_u_s.index(_user_id))
                if _location_ in _l_s:
                    _l_s.pop(_l_s.index(_location_))
                    # 插入到列表最前
                _e_s.insert(0, _id)
                _u_s.insert(0, _user_id)
                _l_s.insert(0, _location_)
                # 去除多余的元素
                if len(_e_s) == 8:
                    _e_s.pop()
                    _u_s.pop()
                    _l_s.pop()
                _location_info["entityIds"] = _e_s
                _location_info["userIds"] = _u_s
                _location_info["locationIndexs"] = _l_s
                _json_data = json.dumps(_location_info)
                _e.clientEntity(self.id).retLocationIndexs(_json_data)

    def clientReq(self, accountEntityId, jsonData):
        """
        client---->cell
        :param accountEntityId:
        :param jsonData:
        :return:
        """
        _accountEntity, _func_name, _args = RoomBase.clientReq(self, accountEntityId, jsonData)
        if _func_name == "leaveRoom":
            self.onLeave(accountEntityId, _args)
        elif _func_name == "reqRankingList":
            _args = self.statisticalData["rankingList"]
            self.callClientFunction(accountEntityId, "retRankingList", _args)
        elif _func_name == "reqMappings":
            _chapter_history = self.statisticalData["chapterHistory"]
            self.callClientFunction(accountEntityId, "mapping", _chapter_history["winHistory"])
            _accountEntity.clientEntity(self.id).updateMapping("mapping1", _chapter_history["hMapping1"])
            _accountEntity.clientEntity(self.id).updateMapping("mapping2", _chapter_history["hMapping2"])
            _accountEntity.clientEntity(self.id).updateMapping("mapping3", _chapter_history["hMapping3"])
            _accountEntity.clientEntity(self.id).updateMapping("mapping4", _chapter_history["hMapping4"])

    def retLocations(self):
        """
        :return:
        """
        DEBUG_MSG('[Room id %s]------>retLocations' % self.id)
        _chapter = self.chapters[self.cn]
        _players = _chapter["players"]
        _entityIds = []
        _userIds = []
        _locationIndexs = []
        _location_info = {}
        # 神算子大富豪
        _ssz_e_id = self.statisticalData["sszEId"]
        _dfh_e_id = self.statisticalData["dfhEId"]
        if _ssz_e_id != -1:
            _player = self.getPlayer(_ssz_e_id)
            if _player:
                _entityIds.append(_ssz_e_id)
                _userIds.append(_player["entity"].info["userId"])
                _locationIndexs.append(_player["locationIndex"])
        if _dfh_e_id != -1:
            _player = self.getPlayer(_dfh_e_id)
            if _player:
                _entityIds.append(_dfh_e_id)
                _userIds.append(_player["entity"].info["userId"])
                _locationIndexs.append(_player["locationIndex"])
        # 随机剩余玩家
        _c_max = 7 - len(_entityIds)
        _c = 0
        _all_locations = list(_players.keys())
        _all_locations.sort()
        for i in _all_locations:
            _e_ = _players[i]["entity"]
            _entityId = _e_.id
            # 不能和神算子大富豪重复
            if _entityId == _ssz_e_id or _entityId == _dfh_e_id:
                continue
            _entityIds.append(_entityId)
            _userIds.append(_e_.info["userId"])
            _locationIndexs.append(i)
            _c += 1
            if _c >= _c_max:
                break
        _location_info["entityIds"] = _entityIds
        _location_info["userIds"] = _userIds
        _location_info["locationIndexs"] = _locationIndexs
        # 分别通知客户端
        for _p in _players.values():
            _e = _p["entity"]
            if _e.info["isBot"] == 0:
                _id = _e.id
                _user_id = _e.info["userId"]
                _location_ = _p["locationIndex"]
                _e_s = _entityIds.copy()
                _u_s = _userIds.copy()
                _l_s = _locationIndexs.copy()
                # 不能和自身重复
                if _id in _e_s:
                    _e_s.pop(_e_s.index(_id))
                if _user_id in _u_s:
                    _u_s.pop(_u_s.index(_user_id))
                if _location_ in _l_s:
                    _l_s.pop(_l_s.index(_location_))
                    # 插入到列表最前
                _e_s.insert(0, _id)
                _u_s.insert(0, _user_id)
                _l_s.insert(0, _location_)
                # 去除多余的元素
                if len(_e_s) == 8:
                    _e_s.pop()
                    _u_s.pop()
                    _l_s.pop()
                _location_info["entityIds"] = _e_s
                _location_info["userIds"] = _u_s
                _location_info["locationIndexs"] = _l_s
                _json_data = json.dumps(_location_info)
                DEBUG_MSG("roomtype3 _e:%s client entity:%s" % (_e, _e.clientEntity))
                _e.clientEntity(self.id).retLocationIndexs(_json_data)

    def onPlayerClientDeath(self, accountEntity):
        """
               玩家非正常离开
               :return:
               """
        # 检测参数合法性
        _accountEntities = self.accountEntities
        _accountEntityId = accountEntity.id
        if _accountEntityId not in _accountEntities.keys():
            return
        # 如果是玩家就移除此玩家
        _player = self.getPlayer(_accountEntityId)
        if _player:
            self.removePlayer(_accountEntityId)
            # 从统计数据中移除
            self.remove_player_from_sd(_accountEntityId)
            # 通知所有客户端座位信息
            self.retLocations()
            # 广播金币
            self.retGolds()
        # 移出房间
        _accountEntities.pop(_accountEntityId)
        self.autoDestroy()
        DEBUG_MSG('[Room id %i]------->onPlayerClientDeath account = %i.' % (self.id, _accountEntityId))

    def retGolds(self):
        """
        广播玩家金币数变化
        :return:
        """
        # _chapter = self.chapters[self.cn]
        # _players = _chapter["players"]
        # # 广播金币变化
        # _l = []
        # for p in _players.values():
        #     _l.append(p["locationIndex"])
        #     _l.append(p["gold"])
        # self.callOtherClientsFunction("goldsChange", _l)

    # --------------------------------------------------------------------------------------------
    #                            计时器
    # --------------------------------------------------------------------------------------------

    def onTimer(self, timerId, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param timerId		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """
        _chapter = self.chapters[self.cn]
        _timers = _chapter["timers"]
        if timerId == _timers["main"]:
            # DEBUG_MSG('[Room id %s]------------->onTimer main %s' % (self.id, timerId))
            _chapter_state = _chapter["chapterState"]
            _players = _chapter["players"]
            if _chapter_state == 0:
                # 默认金币场模式 暂定大于等于2人就开始
                if _chapter["playersCount"] >= 2:
                    # 关闭计时器
                    self.delTimer(timerId)
                    _timers["main"] = -1
                    # 自动准备
                    for i in _players.values():
                        _player_entityId = i["entity"].id
                        self.on_player_ready(_player_entityId)
            elif _chapter_state == 1:
                self.delTimer(timerId)
                _timers["main"] = -1
                self.delTimer(_timers["botBet"])
                _timers["botBet"] = -1
                # 下一阶段
                self.changeChapterState(2)
            elif _chapter_state == 2:
                # 关闭计时器
                self.delTimer(timerId)
                _timers["main"] = -1
                # 流程继续
                _max_players_count = self.info["maxPlayersCount"]
                self.newChapter(_max_players_count)
                # 在场座位上的玩家为下一局玩家
                for i in _players.values():
                    self.newPlayer(i["entity"])
                self.changeChapterState(0)
                ""
        elif timerId == _timers["botBet"]:
            _bots = self.getBotPlayers()
            for b in _bots:
                _ai = self.statisticalData["botAi"][b["entity"].id]
                _s_1 = _ai["seed1"]
                _s_2 = _ai["seed2"]
                _r_p = _ai["betProb"]
                _r_0 = random.randint(0, 99)
                if _r_0 < _r_p:
                    _r_1 = random.choice(_s_1)
                    _r_2 = random.choice(_s_2)
                    self.betOperation(b["locationIndex"], _r_1, _r_2)
                elif _r_0 < _r_p + 2:
                    # 额外下和的概率
                    self.betOperation(b["locationIndex"], 3, 5)
                elif _r_0 < _r_p + 3:
                    # 额外下和的概率
                    self.betOperation(b["locationIndex"], 3, 10)


def updateMapping1(_win_history):
    """

    :return:
    """
    _l = _win_history
    _r = []
    _l_f = -1
    for i in range(0, len(_l)):
        if i == 0:
            _l_v = -1
        else:
            _l_v = _l[i - 1]
        _v = _l[i]
        if _v != 1 and _v != 2 and _v != 3:
            # _win_history[i] = 3
            continue
        if _v == 1:
            if _l_f != 1:
                _l_f = 1
                _r.append([])
            _r[-1].append(1)
        elif _v == 2:
            if _l_f != 2:
                _l_f = 2
                _r.append([])
            _r[-1].append(2)
        elif _v == 3 and len(_r) > 0:
            if _l_v == 1 or _l_v == 2:
                _r[-1][-1] *= 100
            _r[-1][-1] += 1
    return _r


def updateMapping2(_ll, _s, _interval):
    """

    :return:
    """
    _r = []

    def getNext(_ll, _i, _j):
        _len_i = len(_ll)

        if _len_i <= _i:
            return -1, -1
        else:
            _len_j = len(_ll[_i])
            if _len_j <= _j:
                return -1, -1
            else:
                # 下标合法性判断完毕，开始寻找下一个
                _next = _j + 1
                if _len_j <= _next:
                    # 尝试寻找下一列
                    if _len_i <= _i + 1:
                        # 不存在下一列返回
                        return -1, -1
                    else:
                        if len(_ll[_i + 1]) > 0:
                            return _i + 1, 0
                        else:
                            return -1, -1
                else:
                    return _i, _next

    def get(_ll, _i, _j):
        _len_i = len(_ll)

        if _len_i <= _i:
            return -1
        else:
            _len_j = len(_ll[_i])
            if _len_j <= _j:
                return -1
            else:
                return _ll[_i][_j]

    _i = 0
    _j = 0
    _c = 0
    while True:
        _i, _j = getNext(_ll, _i, _j)
        _c += 1
        if _i == -1 and _j == -1:
            break
        if _i == _s and _j == 1:
            break
        if _i > _s:
            break
        if _c > 10000:
            break

    if _i == 0 and _j == 0:
        return _r
    _l = []
    _c = 0
    while True:
        if _i == -1 and _j == -1:
            break
        # 判断有没有规律
        if _j == 0:
            # 第一行
            if len(_ll[_i - 1]) == len(_ll[_i - 1 - _interval]):
                _l.append(1)
            else:
                _l.append(0)
        else:
            # 非第一行
            _l_v = get(_ll, _i - _interval, _j)
            if _l_v == -1:
                # 前一行如果也是没有规律判断 则本行判定有规律
                if _j >= 2:
                    if get(_ll, _i - _interval, _j - 1) == -1:
                        _l.append(1)
                    else:
                        _l.append(0)
                else:
                    _l.append(0)
            else:
                _l.append(1)
        _i, _j = getNext(_ll, _i, _j)
        if _c > 10000:
            break
    # 将_l转换
    _f = -1
    for i in range(0, len(_l)):
        _v = _l[i]
        if _v != _f:
            _f = _v
            _r.append([])
            _r[-1].append(_v)
        else:
            _r[-1].append(_v)
    return _r


def compareCard(_cards_1, _cards_2):
    """
    比较两张牌的大小
    :param _cards_1:
    :param _cards_2:
    :return: 1 0 -1
    """
    _cards_1 = int(_cards_1 / 4)
    _cards_2 = int(_cards_2 / 4)
    if _cards_1 > _cards_2:
        _ret = 1
    elif _cards_1 < _cards_2:
        _ret = -1
    else:
        _ret = 0
    return _ret


def getCardNum(_card):
    """

    :param _card:
    :return:
    """
    return int(_card / 4) + 1


def getCardWeight(_card):
    """

    :return:
    """
    _card_num = getCardNum(_card)
    if _card_num > 9:
        _r = 0
    else:
        _r = _card_num
    return _r


def getCardsWeight(_cards):
    """

    :param _cards:
    :return:
    """
    _l = len(_cards)
    if _l == 0:
        return 0
    _sum = 0
    for i in _cards:
        i = getCardWeight(i)
        _sum += i
    return _sum % 10


def isDouble(_cards):
    """

    :param _cards:
    :return:
    """
    _l = len(_cards)
    if _l <= 1:
        return False
    if getCardNum(_cards[0]) == getCardNum(_cards[1]):
        return True
    else:
        return False


def randomCard(_cards):
    """

    :param _cards:
    :return:
    """
    _l = len(_cards)
    if _l == 0:
        return 0
    _index = random.randint(0, _l - 1)
    _card = _cards.pop(_index)
    return _card


def randomCards(_cards):
    """

    :param _cards:
    :return:
    """
    _cards_1 = []
    _cards_2 = []
    # 给庄闲分别随机两张牌
    _l = len(_cards)
    if _l >= 6:
        _cards_1.append(randomCard(_cards))
        _cards_2.append(randomCard(_cards))
        _cards_1.append(randomCard(_cards))
        _cards_2.append(randomCard(_cards))
        _weight_cards_1 = getCardsWeight(_cards_1)
        _weight_cards_2 = getCardsWeight(_cards_2)
        if _weight_cards_1 <= 5:
            _cards_1.append(randomCard(_cards))
            _card_1_3_w = getCardWeight(_cards_1[2])
            _f = True
            if _weight_cards_2 == 3:
                if _card_1_3_w == 8:
                    _f = False
            elif _weight_cards_2 == 4:
                if _card_1_3_w == 8 or _card_1_3_w == 9 or _card_1_3_w == 0:
                    _f = False
            elif _weight_cards_2 == 5:
                if _card_1_3_w <= 3 or _card_1_3_w >= 8:
                    _f = False
            elif _weight_cards_2 == 6:
                if _card_1_3_w <= 5 or _card_1_3_w >= 8:
                    _f = False
            else:
                _f = False
            if _f:
                _cards_2.append(randomCard(_cards))
        if _weight_cards_2 <= 2:
            _cards_2.append(randomCard(_cards))
    return _cards_1, _cards_2
