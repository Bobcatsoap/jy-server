# -*- coding: utf-8 -*-
import copy

import KBEngine

import Const
import RoomType7Calculator
from KBEDebug import *
from RoomBase import *
import json
import time

# 准备倒计时时间
_timeReady = 5
# 抢庄倒计时时间
_timeBanker = 5
# 分牌动画时间
_create_card_time = 1
# 押注倒计时时间
_timeStake = 10
# 闲家配牌倒计时时间
_timeOtherMatch = 30
# 庄家配牌倒计时
_timeMatchBanker = 20
# 结算时间
_timeSettlement = 5
# 选庄家动画时间
choice_banker_time = 2
# 骰子及发牌时间
_timeDealCard = 8
# 比牌动画时间
_time_compare_cards = 8
# 解散房间倒计时
time_disband = 30
# 牌值 黑红梅方 a,b,c,d
total_cards = ['a8', 'b8', 'c8', 'd8',
               'a7', 'b7', 'c7', 'd7',
               'a10', 'b10', 'c10', 'd10',
               'a6', 'b6', 'c6', 'd6',
               'a4', 'b4', 'c4', 'd4',
               'b12', 'd12', 'b2', 'd2',
               'a9', 'c9', 'a5', 'c5',
               'a11', 'c11', '99', '100']
# key 下注上限
stake_table = {5000: [500, 1000, 2000, 5000], 50000: [5000, 10000, 20000, 50000],
               300000: [20000, 40000, 80000, 300000]}

# 总结算清理玩家倒计时
settlement_clear_players_time = 20


class RoomType7(RoomBase):
    _chapterInfos = {}
    is_manual_disband = False
    disband_from_creator = False
    total_settlement_ed = False
    settlement_count = 0
    started = False

    def __init__(self):
        RoomBase.__init__(self)
        self.emptyLocationIndex = list(range(0, 4))

    def newChapter(self, maxPlayerCount):
        """
        新牌局
        :param maxPlayerCount:
        :return:
        """
        _chapter = {}
        # 房间玩家数量
        _chapter["playersCount"] = 0
        # 最大玩家数量
        _chapter["maxPlayerCount"] = maxPlayerCount
        # 当前轮数
        _chapter["currentRound"] = 0
        # 当前房间状态 0 准备, 1 抢庄, 2 押注, 3 配牌, 4 结算
        _chapter["currentState"] = 0
        # 游戏内玩家
        _chapter["playerInGame"] = {}
        # 游戏外玩家
        _chapter["playerOutGame"] = {}
        # 房间内所有玩家
        _chapter["playerInRoom"] = {}
        # 庄家id
        _chapter["banker"] = -1
        # 庄家位置
        _chapter["bankerIndex"] = -1
        # 轮询是否可以开始牌局计时器
        _chapter["mainTimerId"] = -1
        # 牌局开始倒计时计时器
        _chapter["chapterStartTimerId"] = -1
        # 分牌倒计时
        _chapter["createCardTime"] = -1
        # 选择庄家动画时间
        _chapter["choiceBankerTime"] = -1
        # 发牌倒计时
        _chapter["dealCardTime"] = -1
        # 抢庄计时器
        _chapter["bankerTimerId"] = -1
        # 庄家配牌计时器
        _chapter["bankerMatchCardTime"] = -1
        # 闲家配牌计时器
        _chapter["otherMatchCardTime"] = -1
        # 结算计时器
        _chapter["settlementTime"] = -1
        # 下注计时器
        _chapter["stakeTime"] = -1
        # 抽奖
        _chapter["accountLottery"] = -1
        # 比牌计时器
        _chapter["compareCardTime"] = -1
        # 发牌动画计时器
        _chapter["dealCardAnimationTimerId"] = -1
        # 当前计时时刻点
        _chapter["deadline"] = -1
        # 下注总额
        _chapter["stake"] = {1: 0, 2: 0, 3: 0}
        # 参与抢庄的玩家
        _chapter["grabBankerPlayers"] = []
        # 牌堆牌值
        _chapter["cardsZ"] = []
        _chapter["cardsK"] = []
        _chapter["cardsT"] = []
        _chapter["cardsG"] = []
        # 配牌权值
        _chapter["Zweights"] = []
        _chapter["Kweights"] = []
        _chapter["Tweights"] = []
        _chapter["Gweights"] = []
        # 比牌结果
        _chapter["TResult"] = []
        _chapter["KResult"] = []
        _chapter["GResult"] = []
        # 解散清除玩家倒计时
        _chapter["settlementClearPlayers"] = -1
        # 需要配牌的闲家
        _chapter["canMatchCardsPlayers"] = {}
        # 可以观看配牌的玩家
        _chapter["canWatchCardsPlayers"] = {1: [], 2: [], 3: []}
        # 输赢情况
        _chapter["settlementArea"] = {"winArea": [], "loseArea": [], "drawArea": []}
        self.chapters.append(_chapter)
        self.cn = len(self.chapters) - 1
        self.info['roomId']
        return _chapter

    def newPlayer(self, accountEntity):
        """
        新玩家
        :param accountEntity:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _player = {}
        # 实体
        _player["entity"] = accountEntity
        # 抢庄 0:没有操作 -1:不抢 1:抢1倍 2:抢2倍 3:抢三倍
        _player["grabBanker"] = -1
        # 玩家押注
        _player["stake"] = {0: 0, 1: 0, 2: 0, 3: 0}
        # 座位
        _player["locationIndex"] = -1
        # 本局金币变化
        _player["goldChange"] = 0
        # 总金币变化
        _player["totalGoldChange"] = 0
        # 准备
        _player["ready"] = False
        # 在线状态
        _player["online"] = True
        # 大赢家扣费
        _player["winnerBilling"] = 0
        # 其余玩家扣费
        _player["otherBilling"] = 0
        # 超额扣费
        _player["overBilling"] = 0
        # 是否已经扣过AA支付的钻石
        _player['AARoomCardConsumed'] = False
        # 金币
        # 钻石场
        if self.info["roomType"] == "card":
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        elif self.info["roomType"] == "gameCoin":
            # 比赛分场修改使用比赛分为使用金币
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        elif self.info['roomType'] == 'normalGameCoin':
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        _player["agreeDisband"] = False
        return _player

    def onEnter(self, accountEntityId):
        """
        有玩家进入,加入到观战玩家列表
        :param accountEntityId:
        :return:
        """
        if not RoomBase.onEnter(self, accountEntityId):
            return
        DEBUG_MSG('[Room id %i]------>onEnter accountId %s' % (self.id, accountEntityId))
        _chapter = self.chapters[self.cn]
        _account = KBEngine.entities[accountEntityId]
        _account.viewing_hall = False
        # 存入账户实体列表，相同实体不能重复登入房间
        if _account.id not in self.accountEntities.keys():
            self.accountEntities[_account.id] = _account
            DEBUG_MSG("on_enter account_entities:%s" % self.accountEntities)
        _player = self.newPlayer(_account)
        _currentState = _chapter["currentState"]
        if accountEntityId not in _chapter["playerInRoom"]:
            _chapter["playerInRoom"][accountEntityId] = _player
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
        else:
            DEBUG_MSG("onEnter-------> account %s on Enter room, but _player already exits" % accountEntityId)
            return
        _chapter["playerOutGame"][accountEntityId] = _player
        # if _account.info["isBot"] == 1:
        #     self.set_seat(accountEntityId, self.emptyLocationIndex[0])
        #     self.player_ready(accountEntityId)
        #     return
        self.retCurrentChapterState(accountEntityId)
        self.retRoomBaseInfo(accountEntityId)
        # self.retPlayerInRoomInfos()
        # # 如果比赛已经开始不自动坐下
        # if _chapter["currentState"] != 0:
        #     return
        # if self.info["roomType"] == "card":
        #     if _chapter["currentState"] == 0:
        #         self.set_seat(accountEntityId, self.emptyLocationIndex[0])
        # elif self.info["roomType"] == "gold":
        #     # 金币场自动坐下
        #     if _chapter["currentState"] == 0:
        #         self.set_seat(accountEntityId, self.emptyLocationIndex[0])
        # 如果比赛一开始，观战状态，发送玩家信息
        # if _chapter["currentState"] != 0:
        #     self.retPlayerInRoomInfos()
        # 如果比赛已经开始不自动坐下
        if _chapter["currentState"] == 0 and len(self.emptyLocationIndex) != 0:
            if len(_chapter["playerInGame"]) < self.info["maxPlayersCount"]:
                self.set_seat(accountEntityId, self.emptyLocationIndex[0])

    # 当玩家掉线
    def onPlayerClientDeath(self, accountEntity):
        DEBUG_MSG("RoomType8 onPlayerClientDeath accountId:%s" % accountEntity)
        chapter = self.chapters[self.cn]

        for k, v in chapter["playerInGame"].items():
            if v["entity"] == accountEntity:
                v["online"] = False
                # 总结算或者准备阶段掉线，自动踢出
                if chapter["currentState"] == 0 or chapter["currentState"] == 9:
                    self.kick_out(k, player_online=False)
                break

        all_offline = True
        for k, v in chapter["playerInGame"].items():
            if v["online"]:
                all_offline = False
                break

        if all_offline:
            # self.total_settlement()
            # self.writeToDB()
            for k, v in copy.deepcopy(chapter["playerInGame"]).items():
                self.kick_out(k, player_online=False)

    def onLeave(self, accountEntityId, leave_param=None):
        """
        离开房间
        :param accountEntityId:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>onLeave accountId %s' % (self.id, accountEntityId))
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _currentState = _chapter["currentState"]
        if accountEntityId in _playerInGame:
            # if _currentState != 0 and _currentState != 7:
            #     self.callClientFunction(accountEntityId, "Notice", ["游戏正在游戏中,请等待游戏结束"])
            #     return
            _player = _playerInGame[accountEntityId]

            _playerInGame.pop(accountEntityId)
            _playerInRoom.pop(accountEntityId)
            _locationIndex = _player["locationIndex"]
            if _locationIndex not in self.emptyLocationIndex:
                self.emptyLocationIndex.append(_locationIndex)
                self.emptyLocationIndex.sort()
            if leave_param is None:
                leave_param = {"inviteRoomInfo": None}
            leave_param.update({"result": 1})
            another_room = {}
            if 'JoinAnotherRoom' in leave_param:
                del leave_param['JoinAnotherRoom']
                another_room = leave_param['inviteRoomInfo']
                del leave_param['inviteRoomInfo']
            self.callClientFunction(accountEntityId, "LeaveRoomResult", leave_param)
            if another_room:
                self.callClientFunction(accountEntityId, "JoinAnotherRoom", another_room)
            _player["entity"].destroySelf()
            self.retPlayerInRoomInfos()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        if accountEntityId in _playerOutGame:
            _player = _playerOutGame[accountEntityId]

            _playerOutGame.pop(accountEntityId)
            _playerInRoom.pop(accountEntityId)
            if leave_param is None:
                leave_param = {"inviteRoomInfo": None}
            leave_param.update({"result": 1})
            another_room = {}
            if 'JoinAnotherRoom' in leave_param:
                del leave_param['JoinAnotherRoom']
                another_room = leave_param['inviteRoomInfo']
                del leave_param['inviteRoomInfo']
            self.callClientFunction(accountEntityId, "LeaveRoomResult", leave_param)
            if another_room:
                self.callClientFunction(accountEntityId, "JoinAnotherRoom", another_room)
            _player["entity"].destroySelf()
            self.retPlayerInRoomInfos()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        # 从实体列表中移除
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
            DEBUG_MSG("onLeave account_entities:%s" % self.accountEntities)
        self.autoDestroy()

    def kick_out(self, accountEntityId, isBot=False, player_online=True):
        """
        离开房间
        :param accountEntityId:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>onLeave accountId %s' % (self.id, accountEntityId))
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _currentState = _chapter["currentState"]
        if accountEntityId in _playerInGame:
            _player = _playerInGame[accountEntityId]
            _playerInGame.pop(accountEntityId)
            _playerInRoom.pop(accountEntityId)
            _locationIndex = _player["locationIndex"]
            if _locationIndex not in self.emptyLocationIndex:
                self.emptyLocationIndex.append(_locationIndex)
                self.emptyLocationIndex.sort()
            if player_online:
                self.callClientFunction(accountEntityId, "LeaveRoomResult", {"result": 1, "inviteRoomInfo": None})
            if player_online:
                _player["entity"].destroySelf()
            self.retPlayerInRoomInfos()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        if accountEntityId in _playerOutGame:
            _player = _playerOutGame[accountEntityId]
            _playerOutGame.pop(accountEntityId)
            _playerInRoom.pop(accountEntityId)
            self.callClientFunction(accountEntityId, "LeaveRoomResult", {"result": 1, "inviteRoomInfo": None})
            _player["entity"].destroySelf()
            self.retPlayerInRoomInfos()
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        # 从实体列表中移除
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
            DEBUG_MSG("onLeave account_entities:%s" % self.accountEntities)
        self.autoDestroy()

    def changeChapterState(self, state):
        """
        改变游戏状态
        :param state:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _chapter["currentState"] = state
        self.base.cellToBase({"func": "changeRoomState", "roomState": state})
        if state == 0:
            # 准备
            _args = {"state": state, "Timer": 0}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 机器人自动准备
            # self.bots_ready()
            # 自动准备
            if self.cn > 0:
                for k, v in _chapter["playerInGame"].items():
                    self.player_ready(k)
            _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
        elif state == 1:
            # 抢庄
            _args = {"state": state, "Timer": _timeBanker}
            self.callOtherClientsFunction("changeChapterState", _args)
        elif state == 2:
            # 分牌
            _args = {"state": state, "Timer": _create_card_time}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.create_card()
            _chapter["createCardTime"] = self.addTimer(_create_card_time, 0, 0)
            _chapter["deadline"] = time.time() + _create_card_time
        elif state == 3:
            # 下注
            _args = {"state": state, "Timer": _timeStake}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 机器人下注
            # self.bots_set_stake()
            _chapter["stakeTime"] = self.addTimer(_timeStake, 0, 0)
            _chapter["deadline"] = time.time() + _timeStake
        elif state == 4:
            # 发牌
            _args = {"state": state, "Timer": _timeDealCard}
            self.callOtherClientsFunction("changeChapterState", _args)
            dice1 = random.randint(1, 6)
            dice2 = random.randint(1, 6)
            _args = {"cardsZ": _chapter["cardsZ"], "cardsT": _chapter["cardsT"],
                     "cardsK": _chapter["cardsK"], "cardsG": _chapter["cardsG"],
                     "diceValue1": dice1, "diceValue2": dice2}
            self.callOtherClientsFunction("DealCards", _args)
            _chapter["dealCardTime"] = self.addTimer(_timeDealCard, 0, 0)
            _chapter["deadline"] = time.time() + _timeDealCard
        elif state == 5:
            # 庄家配牌
            _args = {"state": state, "Timer": _timeMatchBanker}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 机器人配牌
            # self.bots_match_card()
            _chapter["bankerMatchCardTime"] = self.addTimer(_timeMatchBanker, 0, 0)
            _chapter["deadline"] = time.time() + _timeMatchBanker
        elif state == 6:
            # 闲家配牌
            _args = {"state": state, "Timer": _timeOtherMatch}
            self.callOtherClientsFunction("changeChapterState", _args)
            player_match_info = self.get_match_cards_player_info()
            _chapter["canMatchCardsPlayers"][1] = player_match_info[0]
            _chapter["canMatchCardsPlayers"][2] = player_match_info[1]
            _chapter["canMatchCardsPlayers"][3] = player_match_info[2]
            match_account = {
                1: {"matchPlayer": player_match_info[0], "watchPlayers": _chapter["canWatchCardsPlayers"][1]},
                2: {"matchPlayer": player_match_info[1], "watchPlayers": _chapter["canWatchCardsPlayers"][2]},
                3: {"matchPlayer": player_match_info[2], "watchPlayers": _chapter["canWatchCardsPlayers"][3]}}
            _args = {"matchAccount": match_account}
            self.callOtherClientsFunction("OtherPlayerMatchCard", _args)
            # 机器人配牌
            # self.bots_match_card()
            _chapter["otherMatchCardTime"] = self.addTimer(_timeOtherMatch, 0, 0)
            _chapter["deadline"] = time.time() + _timeOtherMatch
            # 给没人下注的门自动配牌
            self.auto_match_card_in_un_stake()
        elif state == 7:
            # 比牌
            _args = {"state": state, "Timer": _time_compare_cards}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.compare_cards()
            _chapter["compareCardTime"] = self.addTimer(_time_compare_cards, 0, 0)
            _chapter["deadline"] = time.time() + _time_compare_cards
        elif state == 8:
            # 结算
            _args = {"state": state, "Timer": _timeSettlement}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.settlement()
            _chapter["settlementTime"] = self.addTimer(_timeSettlement, 0, 0)
            _chapter["deadline"] = time.time() + _timeSettlement
        elif state == 9:
            # 结算
            # 关闭所有计时器
            self.close_all_timer()
            _args = {"state": state, "Timer": 0}
            self.callOtherClientsFunction("changeChapterState", _args)

    def retPlayerInRoomInfos(self, accountId=-1):
        """
        广播房间内所有玩家状态
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGameNotEntity = {}
        _playerOutGameNotEntity = {}
        player_in_game_to_base = {}

        for k, v in _chapter["playerInGame"].items():
            # 如果是非结算、总结算阶段金币为gold否则为gold+goldChange
            player_gold = 0
            if _chapter["currentState"] < 8:
                player_gold = v["gold"] + v["goldChange"]
            else:
                player_gold = v["gold"]
            _player = {"gold": player_gold, "locationIndex": int(v["locationIndex"]),
                       "name": v["entity"].info["name"], "stake": v["stake"],
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       'totalGoldChange': v['totalGoldChange'],
                       "headImageUrl": v["entity"].info["headImageUrl"], "ready": v["ready"]}
            _playerInGameNotEntity[int(k)] = _player
            player_in_game_to_base[int(v["locationIndex"])] = {"name": v["entity"].info["name"],
                                                               "databaseId": v["entity"].info["dataBaseId"],
                                                               "headImageUrl": v["entity"].info["headImageUrl"]}
        for k, v in _chapter["playerOutGame"].items():
            _player = {"gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "name": v["entity"].info["name"], "stake": v["stake"],
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       'totalGoldChange': v['totalGoldChange'],
                       "headImageUrl": v["entity"].info["headImageUrl"], "ready": v["ready"]}
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerInGame": _playerInGameNotEntity, "playerOutGame": _playerOutGameNotEntity}
        DEBUG_MSG('[Room id %i]------>retPlayerInRoomInfos %s' % (self.id, _args))
        if accountId == -1:
            self.callOtherClientsFunction("RetPlayerInRoomInfos", _args)
        else:
            self.callClientFunction(accountId, "RetPlayerInRoomInfos", _args)

        tea_house_id = -1
        if self.is_tea_house_room:
            tea_house_id = self.info['teaHouseId']
        self.base.cellToBase({"func": "refreshPlayerInGame", "playerInGame": player_in_game_to_base,
                              "teaHouseId": tea_house_id})

    def get_seat_players(self):
        chapter = self.get_current_chapter()
        _players = chapter["playerInGame"]
        return _players

    def get_seat_player_by_entity_id(self, entityId):
        """
        通过实体id获取坐下玩家
        :param entityId:
        :return:
        """
        _chapter = self.get_current_chapter()
        for k, v in _chapter['playerInGame'].items():
            if v['entity'].id == entityId:
                return v

    def set_seat(self, accountId, locationIndex):
        """
        设置座位
        :param accountId: 设置座位玩家
        :param locationIndex: 座位号0-8
        :return:
        """
        DEBUG_MSG('[Room id %i]------>setSeat accountId %s, locationIndex %s ' % (self.id, accountId, locationIndex))
        _chapter = self.chapters[self.cn]
        if accountId not in _chapter["playerOutGame"]:
            return
        for player in _chapter["playerInGame"].values():
            if player["locationIndex"] == locationIndex:
                return
        _chapter["playerInGame"][accountId] = _chapter["playerOutGame"].pop(accountId)
        _chapter["playerInGame"][accountId]["locationIndex"] = locationIndex
        if self.cn < 1:
            if len(_chapter["playerInGame"]) == 1:
                _chapter["firstMan"] = accountId

        self.emptyLocationIndex.remove(locationIndex)
        self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        self.retPlayerInRoomInfos()
        # 每人满时，创建新的房间(onRoomEnd为true时插入在当前房间后面)
        if len(_chapter['playerInGame']) == self.info['maxPlayersCount']:
            self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})

    def stand_up(self, accountId, locationIndex):
        """
        站起
        :param accountId: 站起玩家
        :param locationIndex: 座位
        :return:
        """
        DEBUG_MSG('[Room id %i]------>standUp accountId %s, locationIndex %s ' % (self.id, accountId, locationIndex))
        _chapter = self.chapters[self.cn]
        if _chapter["currentState"] != 0:
            return
        if accountId not in _chapter["playerInGame"]:
            return
        _chapter["playerOutGame"][accountId] = _chapter["playerInGame"].pop(accountId)
        _chapter["playerOutGame"][accountId]["locationIndex"] = -1
        self.emptyLocationIndex.append(locationIndex)
        self.emptyLocationIndex.sort()
        self.retPlayerInRoomInfos()

    def chapter_start(self):
        """
        牌局开始
        :return:
        """
        DEBUG_MSG('[Room id %i]------>chapterStart ' % self.id)
        self.started = True
        self.info["started"] = True
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        # 金币场扣除房费
        if self.is_gold_session_room():
            for k, v in _playerInGame.items():
                v['gold'] -= self.info['roomRate']
                self.set_base_player_gold(k)
        if len(self.get_ready_player()) < 2:
            _args = {"startGameResult": False, "error": "准备人数不足"}
            self.callClientFunction(self.info["creatorAccountId"], "StartGame", _args)
            return
        # 通知 base 游戏开始
        if self.cn == 0:
            # 将坐下玩家的DB_ID传入前台
            player_in_game_db_id = []
            for k, v in self.chapters[self.cn]["playerInGame"].items():
                player_in_game_db_id.append(v["entity"].info["dataBaseId"])
            self.base.cellToBase(
                {"func": "roomStart", "roomInfo": self.info, "playerInGameDBID": player_in_game_db_id})
            # 房间开始，并且人未满时创建新的房间(onRoomEnd为true时插入在当前房间后面)
            if len(_chapter['playerInGame']) < self.info['maxPlayersCount']:
                self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})
        # _args = {"startGameResult": True, "error": ""}
        # self.callClientFunction(self.info["creatorAccountId"], "StartGame", _args)
        self.changeChapterState(1)
        self.set_current_round(self.cn + 1)
        self.banker_type_switch()
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

    def player_ready(self, account_id):
        DEBUG_MSG("player ready account id:%s" % account_id)
        chapter = self.chapters[self.cn]
        _player = chapter['playerInGame'][account_id]
        if chapter['currentState'] != 0:
            self.callClientFunction(account_id, 'Notice', ['游戏不在准备阶段，无法准备'])
            return
        if self.is_gold_session_room() and _player['gold'] < self.info['roomRate']:
            return
        chapter["playerInGame"][account_id]["ready"] = True
        _args = {"accountId": account_id, "ready": True}
        self.callOtherClientsFunction("Ready", _args)

    def bots_ready(self):
        for k, v in self.get_bots().items():
            if not v["ready"]:
                v["ready"] = True
                _args = {"accountId": k, "ready": True}
                self.callOtherClientsFunction("Ready", _args)

    def get_ready_player(self):
        chapter = self.chapters[self.cn]
        ready_players = []
        for k, v in chapter["playerInGame"].items():
            if v["ready"]:
                ready_players.append(k)
        return ready_players

    # 自动给没有下注的门配牌
    def auto_match_card_in_un_stake(self):
        chapter = self.chapters[self.cn]
        # 闲家自动配牌
        # k：门的 index 。v：该门可以配牌的玩家，-1 为没有玩家
        # 遍历可以配牌的门的玩家列表，如果该门没有配并且没有真实玩家可以配牌，系统自动配牌
        for k, v in copy.deepcopy(chapter["canMatchCardsPlayers"]).items():
            cards1, cards2 = [], []
            if k == 3 and v == -1:
                cards1, cards2 = chapter["cardsG"][:2], chapter["cardsG"][2:]
                DEBUG_MSG('[Room]cards1 %s,cards2 %s' % (cards1, cards2))
            elif k == 2 and v == -1:
                cards1, cards2 = chapter["cardsT"][:2], chapter["cardsT"][2:]
                DEBUG_MSG('[Room]cards1 %s,cards2 %s' % (cards1, cards2))
            elif k == 1 and v == -1:
                cards1, cards2 = chapter["cardsK"][:2], chapter["cardsK"][2:]
                DEBUG_MSG('[Room]cards1 %s,cards2 %s' % (cards1, cards2))
            else:
                continue
            self.match_card(v, k, cards1, cards2)

    def dealCards(self):
        """
        发牌
        :return:
        """

        pass

    # 抢庄模式
    def banker_type_switch(self):
        """
        设置庄家
        :return:
        """
        chapter = self.chapters[self.cn]
        # playerInGame = chapter["playerInGame"]
        # if self.info["roomType"] == "card":
        grab_banker_type = self.info["grabBankerType"]
        # 抢庄
        if grab_banker_type == 1:
            # 抢庄倒计时
            args = {"Timer": _timeBanker}
            self.callOtherClientsFunction("StartGrab", args)
            chapter["bankerTimerId"] = self.addTimer(_timeBanker, 0, 0)
            chapter["deadline"] = time.time() + _timeBanker
        # 轮庄
        elif grab_banker_type == 2:
            if len(self.chapters) <= 1:
                # 第一个进入的人是第一局的庄家
                first_man = chapter["firstMan"]
                if first_man not in chapter["playerInGame"].keys():
                    # 如果第一个人不在房间里，locationIndex 最小的为庄家
                    min_index = sys.maxsize
                    for k, v in chapter["playerInGame"].items():
                        if v["locationIndex"] < min_index:
                            min_index = v["locationIndex"]
                    for k, v in chapter["playerInGame"].items():
                        if v["locationIndex"] == min_index:
                            first_man = k
                            break
                chapter["bankerIndex"] = self.get_location_with_account_id(first_man)
                self.send_banker_result(first_man)
                self.changeChapterState(2)
            else:
                pre_chapter = self.chapters[self.cn - 1]
                location = pre_chapter["bankerIndex"]
                chapter["bankerIndex"] = self.get_next_location_can_banker(location)
                self.send_banker_result(self.get_account_id_with_location_index(chapter["bankerIndex"]))
                self.changeChapterState(2)
        # elif self.info["roomType"] == "gold":
        # if len(self.chapters) <= 1:
        #     bot = self.get_a_bots()
        #     self.send_banker_result(bot)
        # else:
        #     # 抢庄倒计时
        #     args = {"Timer": _timeBanker}
        #     self.callOtherClientsFunction("StartGrab", args)
        #     chapter["bankerTimerId"] = self.addTimer(_timeBanker, 0, 0)
        #     chapter["deadline"] = time.time() + _timeBanker
        #     # 机器人自动抢庄
        #     self.bots_grab_banker()
        # 抢庄倒计时
        # args = {"Timer": _timeBanker}
        # self.callOtherClientsFunction("StartGrab", args)
        # chapter["bankerTimerId"] = self.addTimer(_timeBanker, 0, 0)
        # chapter["deadline"] = time.time() + _timeBanker
        # 机器人自动抢庄
        # self.bots_grab_banker()

    # 发送最终庄家结果
    def send_banker_result(self, banker_account_id):
        chapter = self.chapters[self.cn]
        # 如果已经设置过庄家不再发送消息，防止多次设置
        if chapter["banker"] != -1 and chapter["bankerIndex"] != -1:
            return
        chapter["banker"] = banker_account_id
        chapter["bankerIndex"] = self.get_location_with_account_id(banker_account_id)
        args = {"banker": banker_account_id}
        self.callOtherClientsFunction("SetBanker", args)
        # self.changeChapterState(2)

    # 玩家抢庄请求处理
    def grab_banker(self, accountId, result):
        """
        抢庄
        :param accountId:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>grabBanker, accountId %s' % (self.id, accountId))
        _chapter = self.chapters[self.cn]
        if _chapter['currentState'] != 1:
            self.callClientFunction(accountId, 'Notice', ['游戏不在抢庄阶段，无法抢庄'])
            return
        current_state = _chapter["currentState"]
        grab_banker_type = self.info["grabBankerType"]
        player = _chapter["playerInGame"][accountId]
        player["grabBanker"] = result
        args = {}
        # 抢庄时金币必须大于最小下注的十倍
        if self.have_gold_limit():
            if result == 1 and grab_banker_type == 1 and player["gold"] >= self.info["betLimit"] * 10:
                args = {"result": 1}
                # 收集所有抢庄玩家
                _chapter["grabBankerPlayers"].append(accountId)
            else:
                args = {"result": 0}
        else:
            if result == 1 and grab_banker_type == 1:
                args = {"result": 1}
                # 收集所有抢庄玩家
                _chapter["grabBankerPlayers"].append(accountId)
            else:
                args = {"result": 0}
        args["accountId"] = accountId
        self.callOtherClientsFunction("GrabBankerResult", args)

        # 未抢庄玩家
        unGrabBankerPlayers = []
        for k, v in _chapter["playerInGame"].items():
            if v["grabBanker"] == -1:
                unGrabBankerPlayers.append(k)
        if len(unGrabBankerPlayers) == 0:
            _chapter["bankerTimerId"] = -1
            self.delTimer(_chapter["bankerTimerId"])
            grab_players = _chapter["grabBankerPlayers"]
            # 如果没有人参与抢庄，随机一个参与比赛的玩家
            if len(grab_players) == 0:
                banker = random.choice(list(_chapter["playerInGame"].keys()))
            # 如果有人抢庄，随机一个参与抢庄的玩家
            else:
                banker = random.choice(grab_players)
            self.send_banker_result(banker)
            _chapter["choiceBankerTime"] = self.addTimer(choice_banker_time, 0, 0)
            _chapter["deadline"] = time.time() + choice_banker_time

    # 通过位置获取Id
    def get_account_id_with_location_index(self, location_index):
        """
        通过位置找到 Account_ID
        :param location_index:
        :return:
        """
        chapter = self.chapters[self.cn]
        player_in_game = chapter["playerInGame"]
        for k, v in player_in_game.items():
            if v["locationIndex"] == location_index:
                return k

    # 通过 id 获取位置
    def get_location_with_account_id(self, account_id):
        chapter = self.chapters[self.cn]
        return chapter["playerInGame"][account_id]["locationIndex"]

    # 找到一个机器人
    def get_a_bots(self):
        for k, v in self.chapters[self.cn]["playerInGame"].items():
            if v["entity"].info["isBot"] == 1:
                return k
        return None

    # 获得下个位置

    def get_next_location_index(self, location_index):
        current = location_index
        return (current + 1) % self.info["maxPlayersCount"]

    # 获取所有闲家
    def get_other_players(self):
        chapter = self.chapters[self.cn]
        other_players = {}
        for k, v in chapter["playerInGame"].items():
            if k != chapter["banker"]:
                other_players[k] = v
        return other_players

    # 获取下个有玩家的位置
    def get_next_location_can_banker(self, start_location):
        chapter = self.chapters[self.cn]
        for i in range(0, self.info["maxPlayersCount"]):
            # 获取下个位置
            next = self.get_next_location_index(start_location)
            for k, v in chapter["playerInGame"].items():
                # 如果是比赛分场，有玩家的位置等于下个位置并且该玩家可以当庄家
                if self.have_gold_limit():
                    if v["locationIndex"] == next and v["gold"] >= self.info["betLimit"] * 10:
                        return next
                else:
                    if v["locationIndex"] == next:
                        return next
            start_location = next
        return -1

    def set_stake(self, accountId, stake, stakeIndex, isBot=False):
        """
        押注
        :param accountId:
        :param stake:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>setStake, accountId %s, stake %s ,stakeIndex %s' % (
            self.id, accountId, stake, stakeIndex))
        _chapter = self.chapters[self.cn]
        if _chapter['currentState'] != 3:
            self.callClientFunction(accountId, 'Notice', ['游戏不在下注阶段，无法下注'])
            return
        _playerInGame = _chapter["playerInGame"]
        chapter_total_stake = _chapter["stake"][1] + _chapter["stake"][2] + _chapter["stake"][3]

        # 庄家当前货币
        banker_gold = _playerInGame[_chapter["banker"]]["gold"] + _playerInGame[_chapter["banker"]]["goldChange"]
        # 总下注不能超过庄家总金币
        if stake + chapter_total_stake > banker_gold:
            self.callClientFunction(accountId, "Notice", ["当前总注超过庄家%s，无法下注" % self.gold_name])
            return

        if stake > _playerInGame[accountId]["gold"] + _playerInGame[accountId]["goldChange"] and not isBot:
            self.callClientFunction(accountId, "Notice", ["%s不足" % self.gold_name])
            return

        _playerInGame[accountId]["stake"][int(stakeIndex)] += stake
        _chapter["stake"][int(stakeIndex)] += stake
        # 下注就可以观看配牌
        if accountId not in _chapter["canWatchCardsPlayers"][int(stakeIndex)]:
            _chapter["canWatchCardsPlayers"][int(stakeIndex)].append(accountId)
        _playerInGame[accountId]["goldChange"] -= stake
        _args = {"accountId": accountId, "stake": stake, "stakeIndex": int(stakeIndex),
                 "gold": _playerInGame[accountId]["gold"] + _playerInGame[accountId]["goldChange"]}
        self.callOtherClientsFunction("SetStake", _args)

    def write_chapter_info_to_db(self):
        """
                牌局信息写入库
                :return:
                """
        # 至少打一局才写库
        if self.settlement_count < 1:
            return
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _playerData = {}
        _playerInfo = []
        _history_record = {}
        replay_data = {"chapterInfo": {}}
        replay_all_chapter_data = {}
        # 如果最后一局未到结算阶段，不计入战绩
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        for c in range(0, chapter_record_max_count):
            chapter_info = self.chapters[c]
            chapter_data = []
            # 这一小局除玩家信息外的信息
            replay_single_chapter_data = {"playerInfo": {},
                                          "cardsZ": chapter_info["cardsZ"],
                                          "cardsT": chapter_info["cardsT"],
                                          "cardsK": chapter_info["cardsK"],
                                          "cardsG": chapter_info["cardsG"],
                                          "TResult": chapter_info["TResult"],
                                          "GResult": chapter_info["GResult"],
                                          "KResult": chapter_info["KResult"],
                                          "cardsTInfo1": chapter_info["Tweights"][0],
                                          "cardsTInfo2": chapter_info["Tweights"][1],
                                          "cardsKInfo1": chapter_info["Kweights"][0],
                                          "cardsKInfo2": chapter_info["Kweights"][1],
                                          "cardsGInfo1": chapter_info["Gweights"][0],
                                          "cardsGInfo2": chapter_info["Gweights"][1],
                                          "cardsZInfo1": chapter_info["Zweights"][0],
                                          "cardsZInfo2": chapter_info["Zweights"][1],
                                          "banker": chapter_info["banker"]}
            for k, v in chapter_info["playerInGame"].items():
                # 这一小局玩家的输赢和基本信息。作为战绩存储
                player_data = {"goldChange": v["goldChange"], "name":
                    v["entity"].info["name"]}

                # 这一小局回放用的玩家信息。回放使用
                replay_player_data = {"accountId": k, "accountName": v["entity"].info["name"],
                                      "stake": v["stake"],
                                      "dataBaseId": v["entity"].info["dataBaseId"],
                                      "locationIndex": int(v["locationIndex"]),
                                      "gold": v["gold"],
                                      "goldChange": v["goldChange"], "userId": v["entity"].info["userId"]}
                #
                replay_single_chapter_data["playerInfo"][k] = replay_player_data
                # 存储这一小局所有玩家战绩
                chapter_data.append(player_data)
            # 存储所有小局回放
            replay_all_chapter_data[c] = replay_single_chapter_data
            # 存储所有小局
            _history_record[c] = chapter_data
        replay_data["chapterInfo"] = replay_all_chapter_data
        # 记录战绩的玩家
        record_players = []
        for k, v in _playerInGame.items():
            _playerData = {"accountId": k, "accountName": v["entity"].info["name"],
                           "winnerBilling": v["winnerBilling"], "overBilling": v["overBilling"],
                           "otherBilling": v["otherBilling"],
                           "totalGoldChange": v["totalGoldChange"], "userId": v["entity"].info["userId"]}
            _playerInfo.append(_playerData)
            record_players.append(v["entity"].info["userId"])
        _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                 "maxChapterCount": self.info["maxChapterCount"],
                 "playerInfo": _playerInfo, "historyRecord": _history_record}
        self._chapterInfos = _args
        self.base.cellToBase({"func": "writeChapterInfo", "chapterInfos": self._chapterInfos})
        # 回放存储玩家信息
        self.chapter_replay = replay_data
        self.base.cellToBase({"func": "writeChapterReplay", "chapterReplay": self.chapter_replay})
        DEBUG_MSG('[Room id %i]------>writeChapterInfoToDB, _chapterInfos %s ' % (self.id, self._chapterInfos))
        if self.is_tea_house_room:
            # 通知base的朋友圈记录该房间
            self.base.cellToBase(
                {"func": "writeTeaHouseRoom", "teaHouseId": self.info["teaHouseId"], "type": self.info["type"],
                 'recordPlayers': record_players})

    def set_current_round(self, currentRound):
        """
        设置当前轮数
        :param currentRound:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>setCurrentRound currentRound %s' % (self.id, currentRound))
        _chapter = self.chapters[self.cn]
        _chapter["currentRound"] = currentRound
        _args = {"currentRound": currentRound}
        self.callOtherClientsFunction("RetCurrentRound", _args)

    def playerOperation(self, account_entity_id, jsonData):
        """
        玩家操作
        :param account_entity_id:
        :param jsonData:
        :return:
        """
        DEBUG_MSG(
            '[Room id %i]------>playerOperation accountId %s ,jsonData %s' % (self.id, account_entity_id, jsonData))
        _py_dic = json.loads(jsonData)
        _func = _py_dic["func"]
        _data = _py_dic["args"]
        _playerInGame = self.chapters[self.cn]["playerInGame"]
        if _func == "GrabBanker":
            self.grab_banker(account_entity_id, _data["result"])
        elif _func == "Ready":
            self.player_ready(account_entity_id)
        elif _func == "SetStake":
            self.set_stake(account_entity_id, _data["stake"], _data["stakeIndex"])
        elif _func == "CheckCardsType":
            self.check_cards_type(account_entity_id, _data["cards"])
        elif _func == "MatchCards":
            self.match_card(account_entity_id, _data["matchIndex"], _data["cards1"], _data["cards2"])
        elif _func == "LeaveRoom":
            self.onLeave(account_entity_id, _data)
        elif _func == "GetCardsType":
            self.get_cards_type(account_entity_id, _data["cards"])
        elif _func == "SetSeat":
            self.set_seat(account_entity_id, _data["locationIndex"])
        elif _func == "StandUp":
            self.stand_up(account_entity_id, _data["locationIndex"])
        elif _func == "Reconnect":
            self.reconnect(account_entity_id)
        elif _func == "EmotionChat":
            self.emotion_chat(account_entity_id, _data["index"], _data["type"])
        elif _func == "VoiceChat":
            self.voiceChat(account_entity_id, _data["url"])
        elif _func == "DisbandRoom":
            self.disband_room_broadcast(account_entity_id)
        elif _func == "DisbandRoomOperation":
            self.response_disband(account_entity_id, _data["result"])
        elif _func == "TipCardsType":
            self.tip_cards_type(account_entity_id, _data["cards"])
        elif _func == 'ShareToWX':
            self.share_to_wx(account_entity_id)
        elif _func == 'FreeBlessCount':
            self.free_bless_count(account_entity_id)
        elif _func == "Bless":
            self.bless(account_entity_id, _data["type"])

    def share_to_wx(self, account_id):
        chapter = self.chapters[self.cn]
        if self.info['roomType'] == 'card':
            title = '纸牌牌九房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '纸牌牌九房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '纸牌牌九房间'
        max_chapter = '局数：' + str(self.info['maxChapterCount'])
        min_stake = '最小下注' + str(self.info['betLimit'])
        grab_banker_type = ''
        if self.info['grabBankerType'] == 1:
            grab_banker_type = '抢庄'
        elif self.info['grabBankerType'] == 2:
            grab_banker_type = '轮庄'
        player_count = len(chapter['playerInGame'])
        players = str(player_count) + '缺' + str(self.info['maxPlayersCount'] - player_count)
        con = str('%s %s %s %s' % (players, max_chapter, min_stake, grab_banker_type))
        self.callClientFunction(account_id, 'ShareToWX', {'title': title, 'content': con})

    def voiceChat(self, accountId, url):
        """
        语音聊天
        :param accountId:
        :param url:
        :return:
        """
        # chapter = self.chapters[self.cn]
        # # 获取当前玩家可以语音的区域
        # can_voice_area = self.get_voice_area(accountId)
        # if len(can_voice_area) != 1:
        #     return
        # else:
        #     for k, v in chapter["playerInGame"].items():
        #         # 如果该玩家下了多门不接收语音
        #         if len(self.get_voice_area(k)) != 1:
        #             continue
        #         # 如果是机器人不接收语音
        #         if v["entity"].info["isBot"] == 1:
        #             continue
        #         if self.get_voice_area(k)[0] == can_voice_area[0]:
        #             _args = {"accountId": accountId, "url": url}
        #             self.callClientFunction(k, "VoiceChat", _args)
        self.callOtherClientsFunction("VoiceChat", {"accountId": accountId, "url": url})

    def get_voice_area(self, accountId):
        chapter = self.chapters[self.cn]

        can_receive_area = []
        if accountId in chapter["canWatchCardsPlayers"][1]:
            can_receive_area.append(1)
        if accountId in chapter["canWatchCardsPlayers"][2]:
            can_receive_area.append(2)
        if accountId in chapter["canWatchCardsPlayers"][3]:
            can_receive_area.append(3)
        # 如果多门下注，不能发送语音
        if len(can_receive_area) != 1:
            return []
        return can_receive_area

    def emotion_chat(self, account_id, index, emotion_type):
        """
        表情聊天
        :param emotion_type:
        :param account_id:
        :param index:
        :return:
        """
        _args = {"accountId": account_id, "index": index, "type": emotion_type}
        self.callOtherClientsFunction("EmotionChat", _args)

    def reconnect(self, accountId):
        """
        请求重连
        :param accountId: 重连玩家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>reconnect %s' % (self.id, accountId))
        self.retRoomBaseInfo(accountId)
        self.retPlayerInRoomInfos(accountId)
        self.retChapterInfo(accountId)

    def getPlayerInGameCount(self):
        """
        返回游戏内玩家数量
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        return len(_playerInGame)

    def onTimer(self, timerHandle, userData):
        """
        计时器回调
        :param timerHandle:
        :param userData:
        :return:
        """
        RoomBase.onTimer(self, timerHandle, userData)

        chapter = self.chapters[self.cn]
        playerInGame = chapter["playerInGame"]
        if timerHandle == chapter["bankerTimerId"]:
            # 抢庄计时器
            DEBUG_MSG('[Room id %s]------>onTimer bankerTimerId %s' % (self.id, timerHandle))
            chapter["bankerTimerId"] = -1
            self.delTimer(timerHandle)
            grab_players = chapter["grabBankerPlayers"]
            banker = -1
            # 如果没有人参与抢庄，随机一个参与比赛的玩家
            if len(grab_players) == 0:
                banker = random.choice(list(playerInGame.keys()))
            # 如果有人抢庄，随机一个参与抢庄的玩家
            else:
                banker = random.choice(grab_players)
            self.send_banker_result(banker)
            chapter["choiceBankerTime"] = self.addTimer(choice_banker_time, 0, 0)
            chapter["deadline"] = time.time() + choice_banker_time
        elif timerHandle == chapter["mainTimerId"]:
            all_ready = True
            for k, v in chapter["playerInGame"].items():
                if not v["ready"]:
                    all_ready = False
                    break
            if all_ready and len(chapter["playerInGame"]) >= 2:
                self.delTimer(timerHandle)
                chapter["mainTimerId"] = -1
                self.chapter_start()
        # elif timerHandle == chapter["accountLottery"]:
        #     DEBUG_MSG('[Room id %s]------>onTimer accountLottery %s' % (self.id, timerHandle))
        #     chapter["accountLottery"] = -1
        #     self.Lottery()
        elif timerHandle == chapter["choiceBankerTime"]:
            # 选择庄家动画时间
            DEBUG_MSG('[Room id %s]------>onTimer choiceBankerTime %s' % (self.id, timerHandle))
            chapter["choiceBankerTime"] = -1
            self.delTimer(chapter["choiceBankerTime"])
            self.changeChapterState(2)
        elif timerHandle == chapter["createCardTime"]:
            DEBUG_MSG('[Room id %s]------>onTimer createCardTime %s' % (self.id, timerHandle))
            chapter["createCardTime"] = -1
            self.delTimer(timerHandle)
            self.changeChapterState(3)
        elif timerHandle == chapter["stakeTime"]:
            # 押注计时器
            DEBUG_MSG('[Room id %s]------>onTimer stakeTime %s' % (self.id, timerHandle))
            chapter["stakeTime"] = -1
            self.delTimer(timerHandle)
            self.changeChapterState(4)
        elif timerHandle == chapter["dealCardTime"]:
            # 发牌动画计时器
            DEBUG_MSG('[Room id %s]------>onTimer dealCardTime %s' % (self.id, timerHandle))
            self.delTimer(timerHandle)
            chapter["dealCardTime"] = -1
            self.changeChapterState(5)
        elif timerHandle == chapter["bankerMatchCardTime"]:
            # 庄家配牌计时器
            DEBUG_MSG('[Room id %s]------>onTimer bankerMatchCardTime %s' % (self.id, timerHandle))
            chapter["bankerMatchCardTime"] = -1
            self.delTimer(timerHandle)
            self.match_card(chapter["banker"], 0, chapter["cardsZ"][:2], chapter["cardsZ"][2:])
        elif timerHandle == chapter["otherMatchCardTime"]:
            # 闲家配牌计时器
            DEBUG_MSG('[Room id %s]------>onTimer otherMatchCardTime %s' % (self.id, timerHandle))
            chapter["otherMatchCardTime"] = -1
            self.delTimer(timerHandle)
            DEBUG_MSG('[Room id %s]------>onTimer cardsG %s,cardsT %s,cardsK %s' % (self.id, chapter["cardsG"],
                                                                                    chapter["cardsT"],
                                                                                    chapter["cardsK"]))

            # 给没有配牌的门自动配牌
            for k, v in copy.deepcopy(chapter["canMatchCardsPlayers"]).items():
                cards1, cards2 = [], []
                if k == 3:
                    cards1, cards2 = chapter["cardsG"][:2], chapter["cardsG"][2:]
                    DEBUG_MSG('[Room]cards1 %s,cards2 %s' % (cards1, cards2))
                if k == 2:
                    cards1, cards2 = chapter["cardsT"][:2], chapter["cardsT"][2:]
                    DEBUG_MSG('[Room]cards1 %s,cards2 %s' % (cards1, cards2))
                if k == 1:
                    cards1, cards2 = chapter["cardsK"][:2], chapter["cardsK"][2:]
                    DEBUG_MSG('[Room]cards1 %s,cards2 %s' % (cards1, cards2))
                self.match_card(v, k, cards1, cards2)
        elif timerHandle == chapter["compareCardTime"]:
            DEBUG_MSG('[Room id %s]------>onTimer compareCardTime %s' % (self.id, timerHandle))
            chapter["compareCardTime"] = -1
            self.delTimer(timerHandle)
            self.changeChapterState(8)
        elif timerHandle == chapter["settlementTime"]:
            DEBUG_MSG('[Room id %s]------>onTimer settlementTime %s' % (self.id, timerHandle))
            # 超过局数总结算
            if self.cn + 1 >= self.info["maxChapterCount"]:
                self.total_settlement()
                self.write_chapter_info_to_db()
                return
            chapter["settlementTime"] = -1
            self.delTimer(timerHandle)
            self.clear_chapter()
            self.changeChapterState(0)

        elif timerHandle == chapter["settlementClearPlayers"]:
            chapter["settlementClearPlayers"] = -1
            self.delTimer(chapter["settlementClearPlayers"])
            # 清理玩家
            _playerInGameCopy = chapter["playerInGame"].copy()
            for k, v in _playerInGameCopy.items():
                self.kick_out(k)

    def retCurrentChapterState(self, accountEntityId):
        chapter = self.chapters[self.cn]
        self.callClientFunction(accountEntityId, "CurrentChapterState", {"state": chapter["currentState"]})

    # 分牌
    def create_card(self):
        chapter = self.chapters[self.cn]
        cards_temp = copy.deepcopy(total_cards)
        random.shuffle(cards_temp)
        random.shuffle(cards_temp)
        chapter["cardsZ"], chapter["cardsK"] = cards_temp[:4], cards_temp[4:8]
        chapter["cardsT"], chapter["cardsG"] = cards_temp[8:12], cards_temp[12:16]
        args = {"cardsZ": chapter["cardsZ"], "cardsK": chapter["cardsK"], "cardsT": chapter["cardsT"],
                "cardsG": chapter["cardsG"]}
        self.callOtherClientsFunction("CreateCards", args)

    def check_cards_type(self, accountId, cards):
        RoomType7Calculator.check_cards_type(cards)

    def tip_cards_type(self, account_entity_id, cards1):
        card_type_1, number_1 = RoomType7Calculator.get_cards_weights(cards1)
        self.callClientFunction(account_entity_id, "tipCards",
                                {"accountId": account_entity_id, "type": card_type_1, "number": number_1,
                                 "card": cards1})

    def get_match_cards_player_info(self):
        stake_max_1, stake_max_2, stake_max_3 = 0, 0, 0
        chapter = self.chapters[self.cn]
        playerInGame = chapter["playerInGame"]
        notice_player = []
        # 获取每个门的最大下注数
        for k, v in playerInGame.items():
            if k == chapter["banker"]:
                continue
            DEBUG_MSG("[Room7]---get_match_cards_player_info---v[stake]%s" % v["stake"])
            if v["stake"][1] > stake_max_1:
                stake_max_1 = v["stake"][1]
            if v["stake"][2] > stake_max_2:
                stake_max_2 = v["stake"][2]
            if v["stake"][3] > stake_max_3:
                stake_max_3 = v["stake"][3]
        DEBUG_MSG("[Room7]---get_match_cards_player_info--stake1max%s,stake2max%s,stake3max%s" % (
            stake_max_1, stake_max_2, stake_max_3))
        players1, players2, players3 = [], [], []
        for k, v in playerInGame.items():
            if k == chapter["banker"]:
                continue
            if v["stake"][1] == stake_max_1:
                players1.append(k)
            if v["stake"][2] == stake_max_2:
                players2.append(k)
            if v["stake"][3] == stake_max_3:
                players3.append(k)

        # 如果没有人下注，自动配牌，可以配牌玩家为-1
        if stake_max_1 == 0:
            players1 = [-1]
        if stake_max_2 == 0:
            players2 = [-1]
        if stake_max_3 == 0:
            players3 = [-1]

        DEBUG_MSG("[Room7]---get_match_cards_player_info--players1%s,players2%s,players3%s" % (
            players1, players2, players3))

        if len(players1) > 1:
            random.shuffle(players1)
            notice_player.append(players1[0])
        else:
            notice_player.append(players1[0])

        if len(players2) > 1:
            random.shuffle(players2)
            notice_player.append(players2[0])
        else:
            notice_player.append(players2[0])

        if len(players3) > 1:
            random.shuffle(players3)
            notice_player.append(players3[0])
        else:
            notice_player.append(players3[0])

        return notice_player

    def get_cards_type(self, accountId, cards):
        cards_type, number = RoomType7Calculator.get_cards_weights(cards)
        args = {"cards": cards, "type": [cards_type, number]}
        self.callClientFunction(accountId, "GetCardsType", args)

    def match_card(self, accountId, matchIndex, cards1, cards2):
        DEBUG_MSG("[RoomType7]-----matchCard-----accountId%s,matchIndex%s,cards1:%s,cards2:%s" % (
            accountId, matchIndex, cards1, cards2))
        chapter = self.chapters[self.cn]
        # 庄家配牌
        if chapter["currentState"] == 5:
            if accountId == chapter["banker"] and matchIndex == 0:
                chapter["bankerMatchCardTime"] = -1
                self.delTimer(chapter["bankerMatchCardTime"])
                card_type, number = RoomType7Calculator.get_cards_weights(cards1)
                cards1_weights = [card_type, number]
                card_type, number = RoomType7Calculator.get_cards_weights(cards2)
                cards2_weights = [card_type, number]
                comapre_result = RoomType7Calculator.compare_one_couple_cards(cards1_weights, cards2_weights)
                # 大的放后面
                if comapre_result == 2:
                    chapter["cardsZ"] = cards1 + cards2
                    chapter["Zweights"] = [cards1_weights, cards2_weights]
                else:
                    chapter["cardsZ"] = cards2 + cards1
                    chapter["Zweights"] = [cards2_weights, cards1_weights]
                args = {"accountId": accountId, "matchIndex": matchIndex, "result": 1}
                self.callOtherClientsFunction("MatchCardsResult", args)
                self.changeChapterState(6)
        # 闲家配牌
        if chapter["currentState"] == 6 and accountId != chapter["banker"]:
            type, number = RoomType7Calculator.get_cards_weights(cards1)
            cards1_weights = [type, number]
            type, number = RoomType7Calculator.get_cards_weights(cards2)
            cards2_weights = [type, number]
            compare_result = RoomType7Calculator.compare_one_couple_cards(cards1_weights, cards2_weights)
            if compare_result == 1:
                t = cards1
                cards1 = cards2
                cards2 = t
                t_weights = cards1_weights
                cards1_weights = cards2_weights
                cards2_weights = t_weights
            if matchIndex == 1:
                chapter["cardsK"] = cards1 + cards2
                chapter["Kweights"] = [cards1_weights, cards2_weights]
            elif matchIndex == 2:
                chapter["cardsT"] = cards1 + cards2
                chapter["Tweights"] = [cards1_weights, cards2_weights]
            elif matchIndex == 3:
                chapter["cardsG"] = cards1 + cards2
                chapter["Gweights"] = [cards1_weights, cards2_weights]

            del chapter["canMatchCardsPlayers"][matchIndex]
            args = {"accountId": accountId, "matchIndex": matchIndex, "result": 1}
            self.callOtherClientsFunction("MatchCardsResult", args)
            if len(chapter["canMatchCardsPlayers"]) == 0:
                chapter["otherMatchCardTime"] = -1
                self.delTimer(chapter["otherMatchCardTime"])
                self.changeChapterState(7)

    def compare_cards(self):
        chapter = self.chapters[self.cn]
        DEBUG_MSG("[Room7]::compare_cards::Zweights:%s,Tweights:%s,Gweights:%s,Kweights:%s" % (
            chapter["Zweights"], chapter["Tweights"], chapter["Gweights"], chapter["Kweights"]))
        # 天门
        T = RoomType7Calculator.compare_cards(chapter["Zweights"], chapter["Tweights"], 1)
        # 过门
        G = RoomType7Calculator.compare_cards(chapter["Zweights"], chapter["Gweights"], 1)
        # 坎门
        K = RoomType7Calculator.compare_cards(chapter["Zweights"], chapter["Kweights"], 1)
        chapter["TResult"] = T
        chapter["KResult"] = K
        chapter["GResult"] = G
        # 1:输，2：赢，0：平局
        args = {"TResult": T, "GResult": G, "KResult": K, "cardsT": chapter["cardsT"], "cardsK": chapter["cardsK"],
                "cardsG": chapter["cardsG"], "cardsZ": chapter["cardsZ"],
                "cardsTInfo1": chapter["Tweights"][0], "cardsTInfo2": chapter["Tweights"][1],
                "cardsKInfo1": chapter["Kweights"][0], "cardsKInfo2": chapter["Kweights"][1],
                "cardsGInfo1": chapter["Gweights"][0], "cardsGInfo2": chapter["Gweights"][1],
                "cardsZInfo1": chapter["Zweights"][0], "cardsZInfo2": chapter["Zweights"][1]}
        self.callOtherClientsFunction("CompareCardsResult", args)
        T_results = self.get_total_result(T)
        G_results = self.get_total_result(G)
        K_results = self.get_total_result(K)
        chapter["settlementArea"][G_results].append(3)
        chapter["settlementArea"][T_results].append(2)
        chapter["settlementArea"][K_results].append(1)

    def get_total_result(self, couple_result):
        if couple_result[0] == 2 and couple_result[1] == 2:
            return 'winArea'
        elif couple_result[0] == 1 and couple_result[1] == 1:
            return "loseArea"
        else:
            return "drawArea"

    def settlement(self):
        chapter = self.chapters[self.cn]
        banker = chapter["banker"]
        banker_gold = chapter["playerInGame"][banker]["gold"]
        # 所有胜利门总注
        win_total_stake = 0
        for area in chapter["settlementArea"]["winArea"]:
            win_total_stake += chapter["stake"][area]
        # 结算胜利区域
        for area in chapter["settlementArea"]["winArea"]:
            for k, v in chapter["playerInGame"].items():
                if k == banker:
                    continue
                # 如果玩家在这个胜场有下注，收回下注并赢得金币
                stake_number = v["stake"][area]
                if stake_number > 0:
                    if banker_gold >= win_total_stake:
                        win_gold = stake_number
                    else:
                        # 玩家在所有
                        win_gold = stake_number / win_total_stake * banker_gold
                    # 收回下注的钱+赢得的钱
                    DEBUG_MSG("[Room7]::Settlement::id:%s,win_gold:%s,stake_number%s" % (k, win_gold, stake_number))
                    v["goldChange"] += stake_number + win_gold
                    chapter["playerInGame"][banker]["goldChange"] -= win_gold
        # 结算失败区域
        for area in chapter["settlementArea"]["loseArea"]:
            for k, v in chapter["playerInGame"].items():
                if k == banker:
                    continue
                # 如果玩家在这个输场有下注,注给庄家
                stake_number = v["stake"][area]
                if stake_number > 0:
                    chapter["playerInGame"][banker]["goldChange"] += stake_number
        # 结算平局区域
        for area in chapter["settlementArea"]["drawArea"]:
            for k, v in chapter["playerInGame"].items():
                if k == banker:
                    continue
                stake_number = v["stake"][area]
                # 如果玩家在这个平局场有下注,收回下注
                if stake_number > 0:
                    v["goldChange"] += stake_number

        args = {"playerGoldInfo": {}, "winArea": [], "loseArea": [], "drawArea": []}
        # 修改金币
        for k, v in chapter["playerInGame"].items():
            # 金币场赢钱抽成
            # if self.info["roomType"] == "gold":
            #     if v["goldChange"] > 0:
            #         v["goldChange"] *= 0.95
            v["gold"] += v["goldChange"]
            # 修改玩家金币
            # self.set_player_gold(k, v["gold"])
            DEBUG_MSG("[Room7]::Settlement::id:%s,gold change:%s" % (k, v["goldChange"]))
            v["totalGoldChange"] += v["goldChange"]
            player_gold_info = {"gold": v["gold"], "goldChange": float(v["goldChange"]),
                                'totalGoldChange': v['totalGoldChange'],
                                "stake": {1: v["stake"][1], 2: v["stake"][2], 3: v["stake"][3]}}
            args["playerGoldInfo"][k] = player_gold_info
        args["winArea"] = chapter["settlementArea"]["winArea"]
        args["loseArea"] = chapter["settlementArea"]["loseArea"]
        args["drawArea"] = chapter["settlementArea"]["drawArea"]
        self.callOtherClientsFunction("settlement", args)
        chapter["settlementTime"] = self.addTimer(_timeSettlement, 0, 0)
        chapter["deadline"] = time.time() + _timeSettlement
        self.settlement_count += 1
        if self.settlement_count == 1:
            self.base.cellToBase({'func': 'addTodayRoom'})
        # 如果是AA支付，扣除钻石
        if self.info['payType'] == Const.PayType.AA:
            # 需要扣除钻石的玩家
            need_consume_player = []
            # 如果坐下的玩家有没有扣除过AA支付钻石的，结算时扣除
            for k, v in chapter['playerInGame'].items():
                if not v['AARoomCardConsumed']:
                    need_consume_player.append(v["entity"].info["userId"])
                    v['AARoomCardConsumed'] = True
            if len(need_consume_player) != 0:
                self.base.cellToBase({'func': 'AAPayTypeModifyRoomCard', 'needConsumePlayers': need_consume_player})

    def clear_chapter(self):
        DEBUG_MSG('[Room id %i]------>chapterRestart ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _playerInRoom = _chapter["playerInRoom"]
        _playerOutGame = _chapter["playerOutGame"]

        _newChapter = self.newChapter(_chapter["maxPlayerCount"])
        # 使用 deepcopy 避免每局战绩的玩家赢钱数相同
        _newChapter["playerInGame"] = copy.deepcopy(_playerInGame)
        _newChapter["playerOutGame"] = copy.deepcopy(_playerOutGame)
        _newChapter["playerInRoom"].update(_newChapter["playerInGame"])
        _newChapter["playerInRoom"].update(_newChapter["playerOutGame"])
        for k, v in _newChapter["playerInRoom"].items():
            v["stake"] = {0: 0, 1: 0, 2: 0, 3: 0}
            v["grabBanker"] = -1
            # 本局金币变化
            v["goldChange"] = 0
            # 准备
            v["ready"] = False

        # _playerInGameCopy = _newChapter["playerInGame"].copy()
        # for k, v in _playerInGameCopy.items():
        #     # # 金币为零时踢出
        #     # if v["gold"] == 0:
        #     #     self.kick_out(k)
        #     # 掉线时踢出
        #     if not v["online"]:
        #         self.kick_out(k, player_online=False)
        #     min_stake = stake_table[self.info["betLimit"]][0]
        #     if v["gold"] < min_stake:
        #         self.kick_out(k)

    def retChapterInfo(self, accountId):
        chapter = self.chapters[self.cn]
        play_in_game = chapter["playerInGame"]
        chapter_info = {}
        chapter_info["currentRound"] = int(chapter["currentRound"])
        chapter_info["currentState"] = int(chapter["currentState"])
        chapter_info["deadline"] = int(chapter["deadline"]) - int(time.time())
        chapter_info["banker"] = int(chapter["banker"])
        chapter_info["bankerIndex"] = int(chapter["bankerIndex"])
        chapter_info["stake"] = chapter["stake"]
        chapter_info["cardsZ"] = chapter["cardsZ"]
        chapter_info["cardsK"] = chapter["cardsK"]
        chapter_info["cardsT"] = chapter["cardsT"]
        chapter_info["cardsG"] = chapter["cardsG"]
        chapter_info["canMatchCardsPlayers"] = chapter["canMatchCardsPlayers"]
        chapter_info["canWatchCardsPlayers"] = chapter["canWatchCardsPlayers"]
        chapter_info["settlementArea"] = chapter["settlementArea"]
        chapter_info["TResult"] = chapter["TResult"]
        chapter_info["GResult"] = chapter["GResult"]
        chapter_info["KResult"] = chapter["KResult"]
        chapter_info["started"] = self.started
        chapter_info["disbandSender"] = self.disband_sender
        chapter_info["teaHouseId"] = self.info["teaHouseId"] if "teaHouseId" in self.info.keys() else -1
        chapter_info["isDisbanding"] = self.is_disbanding
        if len(chapter["Tweights"]) != 0:
            chapter_info["cardsTInfo1"] = chapter["Tweights"][0]
            chapter_info["cardsTInfo2"] = chapter["Tweights"][1]
        if len(chapter["Kweights"]) != 0:
            chapter_info["cardsKInfo1"] = chapter["Kweights"][0]
            chapter_info["cardsKInfo2"] = chapter["Kweights"][1]
        if len(chapter["Gweights"]) != 0:
            chapter_info["cardsGInfo1"] = chapter["Gweights"][0]
            chapter_info["cardsGInfo2"] = chapter["Gweights"][1]
        if len(chapter["Zweights"]) != 0:
            chapter_info["cardsZInfo1"] = chapter["Zweights"][0]
            chapter_info["cardsZInfo2"] = chapter["Zweights"][1]
        if len(self.chapters) > 1:
            chapter_info["preBanker"] = self.chapters[self.cn - 1]["banker"]
        _playerData = {}
        for k, v in play_in_game.items():
            _playerData[k] = {"goldChange": v["goldChange"],
                              "name": v["entity"].info["name"],
                              "totalGoldChange": v["totalGoldChange"],
                              "ready": v["ready"],
                              "locationIndex": v["locationIndex"],
                              "stake": v["stake"],
                              "grabBanker": v["grabBanker"],
                              "gold": v["gold"] + v["goldChange"],
                              "agreeDisband": v["agreeDisband"]
                              }
        chapter_info["playerData"] = _playerData
        self.callClientFunction(accountId, "Reconnect", chapter_info)

    # def set_player_gold(self, accountId, gold):
    #     """
    #     设置玩家金币数量,通知base
    #     :param accountId:
    #     :param gold:
    #     :return:
    #     """
    #     _chapter = self.chapters[self.cn]
    #     _playerInRoom = _chapter["playerInRoom"]
    #     _player = _playerInRoom[accountId]
    #     _player["gold"] = int(gold)
    #     _player["entity"].accountMutableInfo["goldBean"] = int(gold)
    #     _player["entity"].base.cellToBase({"func": "setAccountMutableInfo", "dic": {
    #         "goldBean": _player["entity"].accountMutableInfo["goldBean"]}})

    # 机器人抢庄
    def bots_grab_banker(self):
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if v["entity"].info["isBot"] == 1:
                self.grab_banker(k, random.randint(0, 1))

    def bots_set_stake(self):
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if v["entity"].info["isBot"] == 1 and chapter["banker"] != k:
                # 机器人随机下二到五次注
                count = random.randint(3, 8)
                for i in range(1, count):
                    stake = random.choice(stake_table[self.info["betLimit"]])
                    if self.have_gold_limit() and stake > v["gold"] + v["goldChange"]:
                        continue
                    self.set_stake(k, stake, random.randint(1, 3), True)

    def total_settlement(self):
        if self.total_settlement_ed:
            return
        self.close_all_timer()
        self.changeChapterState(9)
        self.total_settlement_ed = True
        chapter = self.chapters[self.cn]

        if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
            self.lottery()

            # 找到大赢家
            winner = {}
            max_win = 0
            for k, v in self.chapters[self.cn]['playerInGame'].items():
                if v['totalGoldChange'] >= max_win:
                    max_win = v['totalGoldChange']

            for k, v in self.chapters[self.cn]['playerInGame'].items():
                if v['totalGoldChange'] == max_win:
                    winner[k] = v

            all_bill = {}
            for k, v in self.chapters[self.cn]['playerInGame'].items():
                all_bill[k] = {"userId": v["entity"].info["userId"], "todayGameCoinAdd": 0, 'winner': 1 if k in winner else 0, "score": v['totalGoldChange']}

            if self.info["winnerBilling"]:
                for k, v in winner.items():
                    winnerBillingCount = 0
                    for i in range(0, len(self.info["winnerBilling"])):
                        if self.info["winnerBilling"][i]['interval'][0] <= v["totalGoldChange"] <= \
                                self.info["winnerBilling"][i]['interval'][1]:
                            winnerBillingConsume = self.info["winnerBilling"][i]['consume']
                            v["totalGoldChange"] -= winnerBillingConsume
                            v["gold"] -= winnerBillingConsume
                            v["winnerBilling"] = -winnerBillingConsume
                            winnerBillingCount += self.info["winnerBilling"][i]['consume']

                    self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                          "todayGameCoinAdd": winnerBillingCount,
                                          "userId": v["entity"].info["userId"]})
                    all_bill[k]["todayGameCoinAdd"] += winnerBillingCount

            if self.info['otherBilling']:
                for k, v in chapter['playerInGame'].items():
                    # 如果大赢家开启，其他玩家不扣大赢家
                    if k in winner and self.info["winnerBilling"]:
                        continue
                    otherBillingCount = 0
                    for i in range(0, len(self.info["otherBilling"])):
                        if self.info["otherBilling"][i]['interval'][0] <= v["totalGoldChange"] <= \
                                self.info["otherBilling"][i]['interval'][1]:
                            otherBillingConsume = self.info["otherBilling"][i]['consume']
                            v["totalGoldChange"] -= otherBillingConsume
                            v["gold"] -= otherBillingConsume
                            v["otherBilling"] = -otherBillingConsume
                            otherBillingCount += self.info["otherBilling"][i]['consume']

                    self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                          "todayGameCoinAdd": otherBillingCount,
                                          "userId": v["entity"].info["userId"]})
                    all_bill[k]["todayGameCoinAdd"] += otherBillingCount
            self.base.cellToBase({"func": "todayBillStatic", "teaHouseId": self.info["teaHouseId"], "bill": list(all_bill.values())})

        player_settlement_info = []
        for k, v in chapter["playerInGame"].items():
            # 同步金币到 base
            if self.info["roomType"] == "gameCoin":
                self.set_base_player_game_coin(k)
            else:
                self.set_base_player_gold(k)
            player_settlement_info.append(
                {"accountId": k, "totalGoldChange": v["totalGoldChange"], "name": v["entity"].info["name"],
                 "overBilling": v["overBilling"], "otherBilling": v["otherBilling"],
                 "winnerBilling": v["winnerBilling"], 'gold': v['gold']})

        args = {"settlementInfo": player_settlement_info}
        self.callOtherClientsFunction("TotalSettlement", args)
        self.base.cellToBase({"func": "totalSettlementEd"})
        # 忽略判断，创建一个房间
        self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info, 'ignoreJudge': True, 'onRoomEnd': True})
        # 记录局数
        if self.is_tea_house_room and self.settlement_count >= 1:
            self.set_base_player_chapter_count()

        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(settlement_clear_players_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_clear_players_time

    # 群主解散房间
    def tea_house_disband_room_by_creator(self):
        """
        解散房间
        :return:
        """
        _chapter = self.chapters[self.cn]
        player_in_game = _chapter["playerInGame"].copy()
        self.disband_from_creator = True
        if not self.started:
            for k, v in player_in_game.items():
                self.kick_out(k)
            else:
                self.autoDestroy()
            return

        if self.chapters[self.cn]["currentState"] != 9:
            self.total_settlement()
            self.write_chapter_info_to_db()

    # 机器人配牌
    def bots_match_card(self):
        chapter = self.chapters[self.cn]
        if chapter["currentState"] == 5:
            for k, v in chapter["playerInGame"].items():
                if v["entity"].info["isBot"] == 1:
                    if k == chapter["banker"]:
                        self.match_card(k, 0, chapter["cardsZ"][:2], chapter["cardsZ"][2:])
                        return
        if chapter["currentState"] == 6:
            match_player = chapter["canMatchCardsPlayers"]
            for k, v in chapter["playerInGame"].items():
                if v["entity"].info["isBot"] == 1:
                    if 1 in match_player and k == match_player[1]:
                        self.match_card(k, 1, chapter["cardsK"][:2], chapter["cardsK"][2:])
                    if 2 in match_player and k == match_player[2]:
                        self.match_card(k, 2, chapter["cardsT"][:2], chapter["cardsT"][2:])
                    if 3 in match_player and k == match_player[3]:
                        self.match_card(k, 3, chapter["cardsG"][:2], chapter["cardsG"][2:])
            return

    def get_bots(self):
        chapter = self.chapters[self.cn]
        bots = {}
        for k, v in chapter["playerInGame"].items():
            if v["entity"].info["isBot"] == 1:
                bots[k] = v
        return bots

    def close_all_timer(self):
        """
        关闭所有计时器
        :return:
        """
        chapter = self.chapters[self.cn]
        chapter["bankerTimerId"] = -1
        self.delTimer(chapter["bankerTimerId"])
        chapter["createCardTime"] = -1
        self.delTimer(chapter["createCardTime"])
        chapter["stakeTime"] = -1
        self.delTimer(chapter["stakeTime"])
        chapter["dealCardTime"] = -1
        self.delTimer(chapter["dealCardTime"])
        chapter["bankerMatchCardTime"] = -1
        self.delTimer(chapter["bankerMatchCardTime"])
        chapter["otherMatchCardTime"] = -1
        self.delTimer(chapter["otherMatchCardTime"])
        chapter["compareCardTime"] = -1
        self.delTimer(chapter["compareCardTime"])
        chapter["settlementTime"] = -1
        self.delTimer(chapter["settlementTime"])
        self.disband_timer = -1
        self.delTimer(self.disband_timer)
