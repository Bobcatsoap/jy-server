# -*- coding: utf-8 -*-
import copy
from random import shuffle

import RoomType7Calculator
import RoomType11Calculator
from RoomBase import *
import json
import time

# 准备倒计时时间
_timeReady = 5
# 抢庄倒计时时间
_timeBanker = 5
# 分牌动画时间
_create_card_time = 3
# 选庄家动画时间
choice_banker_time = 2
# 押注倒计时时间
_timeStake = 20
# 结算时间
_timeSettlement = 5
# 总结算时间
_timeTotalSettlement = 5
# 骰子及发牌时间
_timeDealCard = 5
# 每位比牌动画时间
_time_compare_cards = 2
# 接庄倒计时
_timeReceiveBanker = 5
# 切锅倒计时
_timeSwitchPot = 5
# 解散房间倒计时
time_disband = 30
# key 下注上限
stake_table = {5000: [500, 1000, 2000, 5000], 50000: [5000, 10000, 20000, 50000],
               300000: [20000, 40000, 80000, 300000]}
# 总结算清理玩家倒计时
settlement_clear_players_time = 30


class RoomType11(RoomBase):
    _chapterInfos = {}
    emptyLocationIndex = []
    card_type = []
    is_manual_disband = False
    # 1 创建者解散
    disband_from_creator = False
    # 1 总结算标志位
    total_settlement_ed = False
    # 1 结算次数
    settlement_count = 0
    started = False

    # 固定庄家
    static_banker = 0

    # 持续当庄次数
    keep_banker_count = 0

    # ready_count_down = {"ready_c_d_1": -1, "ready_c_d_2": -1, "ready_c_d_3": -1, "ready_c_d_4": -1}

    def __init__(self):
        RoomBase.__init__(self)

    def newStatisticalData(self):
        self.emptyLocationIndex = list(range(0, self.info["maxPlayersCount"]))

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
        # 解散清除玩家倒计时
        _chapter["settlementClearPlayers"] = -1
        # 轮询是否可以开始牌局计时器
        _chapter["mainTimerId"] = -1
        # 牌局开始倒计时计时器
        _chapter["chapterStartTimerId"] = -1
        # 分牌倒计时
        _chapter["createCardTime"] = -1
        # 发牌倒计时
        _chapter["dealCardTime"] = -1
        # 抽奖
        _chapter["accountLottery"] = -1
        # 抢庄计时器
        _chapter["bankerTimerId"] = -1
        # 总结算计时器
        _chapter['totalSettlementTime'] = -1
        # 配牌计时器
        _chapter["matchCardTime"] = -1
        # 选择庄家动画时间
        _chapter["choiceBankerTime"] = -1
        # 结算倒计时时间
        _chapter["settlementClearPlayers"] = -1
        # 结算计时器
        _chapter["settlementTime"] = -1
        # 下注计时器
        _chapter["stakeTime"] = -1
        # 比牌计时器
        _chapter["compareCardTime"] = -1
        # 切锅计时器
        _chapter['switchPotTime'] = -1
        # 上庄计时器
        _chapter['receiveBankerTime'] = -1
        # 发牌动画计时器
        _chapter["dealCardAnimationTimerId"] = -1
        # 当前计时时刻点
        _chapter["deadline"] = -1
        # 参与抢庄的玩家
        _chapter["grabBankerPlayers"] = []
        # 未配牌玩家
        _chapter["unMatchedPlayers"] = []
        # 未下注玩家
        _chapter["unStakePlayers"] = []
        _chapter["faceCards"] = []
        # 虚拟发配玩家
        _chapter["virtualPlayerCards"] = {}
        _chapter['currentBankerOperatePlayer'] = -1
        _chapter["cards"] = []
        # 锅底
        _chapter["potStake"] = 0
        self.chapters.append(_chapter)
        self.cn = len(self.chapters) - 1
        if self.cn == 0:
            # 锅底分数赋值
            if self.info["pot"]:
                self.chapters[self.cn]["potStake"] = self.info["potBase"]

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
        # 抢庄 -1:没有操作 0:不抢 1:抢
        _player["grabBanker"] = -1
        # 玩家押注
        _player["stake"] = {1: -1, 2: -1, 3: -1}
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
        _player["cards"] = []
        _player["cardsInfo"] = []
        _player["matched"] = False
        # 大赢家扣费
        _player["winnerBilling"] = 0
        # 其余玩家扣费
        _player["otherBilling"] = 0
        # 超额扣费
        _player["overBilling"] = 0
        # 钻石场默认为0，金币场使用大厅金币，比赛分使用账户在冠名赛的比赛分
        # 发牌顺序
        _player["dealCardIndex"] = -1
        # 接庄
        _player['receiveBanker'] = False
        # 是否已经扣过AA支付的钻石
        _player['AARoomCardConsumed'] = False
        # 钻石场
        if self.info["roomType"] == "card":
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 比赛分场
        elif self.info["roomType"] == "gameCoin":
            # 比赛分场修改使用比赛分为使用金币
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 普通比赛分场
        elif self.info['roomType'] == 'normalGameCoin':
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        _player["agreeDisband"] = False
        # 房间内玩家数量
        _chapter["playersCount"] += 1
        self.base.cellToBase({"func": "playersCount", "count": _chapter["playersCount"]})
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
        self.ret_current_chapter_state(accountEntityId)
        self.retRoomBaseInfo(accountEntityId)
        # self.retPlayerInRoomInfos()
        # 如果比赛一开始，观战状态，发送玩家信息
        # if _chapter["currentState"] != 0:
        #     self.retPlayerInRoomInfos()
        # 如果比赛已经开始不自动坐下
        if _chapter["currentState"] == 0 and not self.started and len(self.emptyLocationIndex) != 0:
            if len(_chapter["playerInGame"]) < self.info["maxPlayersCount"]:
                self.set_seat(accountEntityId, self.emptyLocationIndex[0])
        # 有观战玩家进入
        else:
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.retOutGamePlayerInfo(k)
            # 给进入的玩家发送所有玩家信息
            self.retPlayerInRoomInfos(accountEntityId)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.retOutGamePlayerInfo(k)
            # 给进入的玩家发送牌局信息
            self.ret_chapter_info(accountEntityId)

    def onPlayerClientDeath(self, accountEntity):
        DEBUG_MSG("RoomType11 onPlayerClientDeath accountId:%s" % accountEntity)
        chapter = self.chapters[self.cn]

        for k, v in chapter["playerInGame"].items():
            if v["entity"] == accountEntity:
                v["online"] = False
                # 总结算或者准备阶段掉线，自动踢出
                if chapter["currentState"] == 0 or chapter["currentState"] == 7:
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
            # 有观战玩家离开
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.retOutGamePlayerInfo(k)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.retOutGamePlayerInfo(k)
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        # 从实体列表中移除
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
            DEBUG_MSG("onLeave account_entities:%s" % self.accountEntities)
        self.autoDestroy()

    def kick_out(self, accountEntityId, player_online=True):
        """
                离开房间
                :param player_online:
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
            self.callClientFunction(accountEntityId, "LeaveRoomResult", {"result": "比赛已结束", "inviteRoomInfo": None})
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
            if self.info['pot']:
                # 爆锅或者锅底没钱，自动切换到下个人
                if _chapter['potStake'] <= 0 \
                        or _chapter['potStake'] >= self.info['potBase'] * self.info['potMaxMultiple']:
                    self.switch_pot(_chapter['banker'], True)
                elif self.keep_banker_count >= 3:
                    _chapter['currentBankerOperatePlayer'] = _chapter['banker']
                    # 提示切锅
                    self.callOtherClientsFunction("tipSwitchPot", {'Timer': _timeSwitchPot})
                    # 开启切锅倒计时
                    _chapter['switchPotTime'] = self.addTimer(_timeSwitchPot, 0, 0)
                    _chapter["deadline"] = time.time() + _timeSwitchPot
                else:
                    # 如果不需要切锅，自动准备
                    for k, v in _chapter["playerInGame"].items():
                        self.player_ready(k)
            # 不加锅自动准备
            else:
                # 自动准备
                for k, v in _chapter["playerInGame"].items():
                    self.player_ready(k)

            _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
        elif state == 1:
            # 抢庄
            _args = {"state": state, "Timer": _timeBanker}
            self.callOtherClientsFunction("changeChapterState", _args)
        elif state == 2:
            # 下注
            _args = {"state": state, "Timer": _timeStake}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 如果固定选分并且不是加锅牌九,自动下注
            if self.info["stakeMode"] != 0 and not self.info["pot"]:
                for k, v in _chapter["playerInGame"].items():
                    # 庄家不下注
                    if k == _chapter["banker"]:
                        continue
                    self.set_stake(k, self.info["stakeMode"], 1)
                    if self.info['stakeCount'] >= 2:
                        self.set_stake(k, self.info["stakeMode"], 2)
                    if self.info["stakeCount"] >= 3:
                        self.set_stake(k, self.info["stakeMode"], 3)
            else:
                pass
                # _chapter["stakeTime"] = self.addTimer(_timeStake, 0, 0)
                # _chapter["deadline"] = time.time() + _timeStake
        elif state == 3:
            # 发牌
            _args = {"state": state, "Timer": _timeDealCard}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.create_card()
            _chapter["dealCardTime"] = self.addTimer(_timeDealCard, 0, 0)
            _chapter["deadline"] = time.time() + _timeDealCard
        elif state == 4:
            # 配牌
            _args = {"state": state, "Timer": self.info["autoCompareTime"]}
            self.callOtherClientsFunction("changeChapterState", _args)
            if self.info["autoCompareTime"] != 0:
                _chapter["matchCardTime"] = self.addTimer(self.info["autoCompareTime"], 0, 0)
                _chapter["deadline"] = time.time() + self.info["autoCompareTime"]
        elif state == 5:
            # 比牌
            compare_time = round(_time_compare_cards * len(_chapter["playerInGame"]))
            _args = {"state": state, "Timer": compare_time}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.compare_cards()
            _chapter["compareCardTime"] = self.addTimer(compare_time, 0, 0)
            _chapter["deadline"] = time.time() + compare_time * len(_chapter["playerInGame"])
        elif state == 6:
            # 结算
            _args = {"state": state, "Timer": _timeSettlement}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.settlement()
        elif state == 7:
            # 总结算
            # 关闭所有计时器
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
            _player = {"gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "name": v["entity"].info["name"], "stake": v["stake"],
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       'totalGoldChange': v['totalGoldChange'],
                       "headImageUrl": v["entity"].info["headImageUrl"], "ready": v["ready"]}
            player_in_game_to_base[int(v["locationIndex"])] = {"name": v["entity"].info["name"],
                                                               "databaseId": v["entity"].info["dataBaseId"],
                                                               "headImageUrl": v["entity"].info["headImageUrl"]}
            _playerInGameNotEntity[int(k)] = _player
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

    def retOutGamePlayerInfo(self, accountId=-1):
        _chapter = self.chapters[self.cn]
        _playerOutGameNotEntity = {}

        for k, v in _chapter["playerOutGame"].items():
            _player = {"gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "name": v["entity"].info["name"], "stake": v["stake"],
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       "headImageUrl": v["entity"].info["headImageUrl"], "ready": v["ready"]}
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerOutGame": _playerOutGameNotEntity}
        DEBUG_MSG('[Room id %i]------>retPlayerInRoomInfos %s' % (self.id, _args))
        if accountId == -1:
            self.callOtherClientsFunction("RetOutGamePlayerInfo", _args)
        else:
            self.callClientFunction(accountId, "RetOutGamePlayerInfo", _args)

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
        self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
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
        for k, v in self.chapters[self.cn]["playerInGame"].items():
            self.chapters[self.cn]["unMatchedPlayers"].append(k)
            self.chapters[self.cn]["unStakePlayers"].append(k)
        if self.chapters[self.cn]["banker"] != -1:
            self.chapters[self.cn]["unStakePlayers"].remove(self.chapters[self.cn]["banker"])

        # 通知 base 游戏开始
        if self.cn == 0:
            # 将坐下玩家的DB_ID传入前台
            player_in_game_db_id = []
            for k, v in self.chapters[self.cn]["playerInGame"].items():
                player_in_game_db_id.append(v["entity"].info["dataBaseId"])
            self.base.cellToBase({"func": "roomStart", "roomInfo": self.info, "playerInGameDBID": player_in_game_db_id})
            # 房间开始，并且人未满时创建新的房间(onRoomEnd为true时插入在当前房间后面)
            if len(_chapter['playerInGame']) < self.info['maxPlayersCount']:
                self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})
        self.changeChapterState(1)
        self.set_current_round(self.cn + 1)
        self.banker_type_switch()
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

    def player_ready(self, account_id):
        DEBUG_MSG("player ready account id:%s" % account_id)
        chapter = self.chapters[self.cn]
        _player = chapter["playerInGame"][account_id]
        if chapter['currentState'] != 0:
            self.callClientFunction(account_id, 'Notice', ['游戏不在准备阶段，无法准备'])
            return
        if self.is_gold_session_room() and _player['gold'] < self.info['roomRate']:
            return
        if self.have_gold_limit() and _player["gold"] < self.info["minStake"]:
            if account_id != self.chapters[self.cn - 1]["banker"]:
                return
        _player["ready"] = True
        _args = {"accountId": account_id, "ready": True}
        self.callOtherClientsFunction("Ready", _args)

    def get_ready_player(self):
        chapter = self.chapters[self.cn]
        ready_players = []
        for k, v in chapter["playerInGame"].items():
            if v["ready"]:
                ready_players.append(k)
        return ready_players

    # 抢庄模式
    def banker_type_switch(self):
        """
        设置庄家
        :return:
        """
        chapter = self.chapters[self.cn]
        playerInGame = chapter["playerInGame"]
        grab_banker_type = self.info["grabBankerType"]
        # 加锅牌九
        if self.info["pot"]:
            # 如果有庄家，不抢
            if self.cn >= 1:
                self.changeChapterState(2)
            else:
                # 抢庄倒计时
                args = {"Timer": _timeBanker}
                self.callOtherClientsFunction("StartGrab", args)
                chapter["bankerTimerId"] = self.addTimer(_timeBanker, 0, 0)
                chapter["deadline"] = time.time() + _timeBanker
        # 抢庄
        elif grab_banker_type == 1:
            # 抢庄倒计时
            args = {"Timer": _timeBanker}
            self.callOtherClientsFunction("StartGrab", args)
            chapter["bankerTimerId"] = self.addTimer(_timeBanker, 0, 0)
            chapter["deadline"] = time.time() + _timeBanker
        # 轮庄
        elif grab_banker_type == 2:
            if len(self.chapters) <= 1:
                banker = self.info["creatorAccountId"]
                if banker not in chapter["playerInGame"].keys():
                    # 如果创建者不在房间里，locationIndex 最小的为庄家
                    min_index = sys.maxsize
                    for k, v in chapter["playerInGame"].items():
                        if v["locationIndex"] < min_index:
                            min_index = v["locationIndex"]
                    for k, v in chapter["playerInGame"].items():
                        if v["locationIndex"] == min_index:
                            banker = k
                            break
                DEBUG_MSG('banker id:%s' % banker)

                chapter["bankerIndex"] = self.get_location_with_account_id(banker)
                self.send_banker_result(banker)
                self.changeChapterState(2)

            else:
                pre_chapter = self.chapters[self.cn - 1]
                location = pre_chapter["bankerIndex"]
                chapter["bankerIndex"] = self.get_next_location_have_player(location)
                self.send_banker_result(self.get_account_id_with_location_index(chapter["bankerIndex"]))
                self.changeChapterState(2)
        # 霸王庄
        elif grab_banker_type == 3:
            location_indexes = []
            if self.static_banker == 0:
                for k, v in chapter['playerInGame'].items():
                    location_indexes.append(v['locationIndex'])
                location_indexes.sort()
                DEBUG_MSG('location_indexes%s' % location_indexes)
                self.static_banker = self.get_account_id_with_location_index(location_indexes[0])
            self.send_banker_result(self.static_banker)
            self.changeChapterState(2)

    def send_banker_result(self, banker_account_id, receive_banker_mode=False):
        """
        此方法发送最终庄家结果，如果设置过庄家不会再设置（接庄模式除外）。
        :param banker_account_id:
        :param receive_banker_mode:
        :return:
        """
        chapter = self.chapters[self.cn]
        # 如果已经设置过庄家不再发送消息，防止多次设置
        if chapter["banker"] != -1 and chapter["bankerIndex"] != -1 and not receive_banker_mode:
            return
        chapter["banker"] = banker_account_id
        chapter["bankerIndex"] = self.get_location_with_account_id(banker_account_id)
        args = {"banker": banker_account_id}
        self.callOtherClientsFunction("SetBanker", args)
        if chapter["banker"] in chapter["unStakePlayers"]:
            chapter["unStakePlayers"].remove(chapter["banker"])

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
            DEBUG_MSG('[Room id %i]------>grabBanker currentState %s can"t grab' % (self.id, _chapter['currentState']))
            return
        grab_banker_type = self.info["grabBankerType"]
        args = {"accountId": accountId}
        _chapter["playerInGame"][accountId]["grabBanker"] = result
        if result == 1 and grab_banker_type == 1:
            args["result"] = 1
            # 收集所有抢庄玩家
            _chapter["grabBankerPlayers"].append(accountId)
        else:
            args["result"] = 0
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

    def get_next_location_index(self, location_index):
        """
        获取下个位置
        :param location_index:
        :return:
        """
        current = location_index
        return (current + 1) % self.info["maxPlayersCount"]

    def get_next_location_have_player(self, start_location):
        """
        通过座位找到下个玩家
        :param start_location:
        :return:
        """
        chapter = self.chapters[self.cn]
        for i in range(0, self.info["maxPlayersCount"]):
            # 获取下个位置
            next_location = self.get_next_location_index(start_location)
            for k, v in chapter["playerInGame"].items():
                if v["locationIndex"] == next_location:
                    return next_location
            start_location = next_location
        return -1

    def set_stake(self, accountId, stake, stake_index, isBot=False):
        """
        押注
        :param isBot:
        :param stake_index:
        :param accountId:
        :param stake:
        :return:
        """
        _chapter = self.chapters[self.cn]
        DEBUG_MSG('[Room id %i]------>setStake, accountId %s, stake %s ,stakeIndex %s' % (
            self.id, accountId, stake, stake_index))
        if _chapter['currentState'] != 2:
            DEBUG_MSG(
                '[Room id %i]------>grabBanker currentState %s can"t setStake' % (self.id, _chapter['currentState']))
            return
        # 庄家不能下注
        if accountId == _chapter["banker"]:
            return
        _playerInGame = _chapter["playerInGame"]
        _playerInGame[accountId]["stake"][int(stake_index)] = stake
        _playerInGame[accountId]["goldChange"] -= stake
        _args = {"accountId": accountId, "stake": stake, "stakeIndex": int(stake_index),
                 "gold": _playerInGame[accountId]["gold"] + _playerInGame[accountId]["goldChange"]}
        self.callOtherClientsFunction("SetStake", _args)
        stake_1 = _playerInGame[accountId]["stake"][1]
        stake_2 = _playerInGame[accountId]["stake"][2]
        stake_3 = _playerInGame[accountId]["stake"][3]

        if self.info["stakeCount"] == 1:
            if stake_1 > -1:
                _chapter["unStakePlayers"].remove(accountId)

        if self.info["stakeCount"] == 2:
            if stake_1 > -1 and stake_2 > -1:
                _chapter["unStakePlayers"].remove(accountId)

        if self.info["stakeCount"] == 3:
            if stake_1 > -1 and stake_2 > -1 and stake_3 > -1:
                _chapter["unStakePlayers"].remove(accountId)

        if len(_chapter["unStakePlayers"]) == 0:
            _chapter["stakeTime"] = -1
            self.delTimer(_chapter["stakeTime"])
            self.changeChapterState(3)

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
        # 回放记录
        # 如果最后一局未到结算阶段，不计入战绩
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        for c in range(0, chapter_record_max_count):
            chapter_info = self.chapters[c]
            chapter_data = []
            replay_single_chapter_data = {"playerInfo": {}, "potStake": chapter_info["potStake"],
                                          "banker": chapter_info["banker"]}
            # 回放的牌局所有信息
            for k, v in chapter_info["playerInGame"].items():

                # 记录牌值和类型
                # 牌值和类型转为字符串
                cards_string = []
                for c_s in v["cards"]:
                    s = str(str(c_s[0]) + "+" + str(c_s[1]))
                    if len(c_s) == 3:
                        s += "+" + str(c_s[2])
                    cards_string.append(s)
                cards_info_string = []
                for c_info in v["cardsInfo"]:
                    cards_info_string.append(str(str(c_info[0]) + "+" + str(c_info[1])))

                player_data = {"goldChange": v["goldChange"], "name":
                    v["entity"].info["name"]}
                replay_player_data = {"accountId": k, "accountName": v["entity"].info["name"],
                                      "stake": v["stake"], "cards": cards_string, "cardsInfo": cards_info_string,
                                      "dataBaseId": v["entity"].info["dataBaseId"],
                                      "locationIndex": int(v["locationIndex"]),
                                      "gold": v["gold"],
                                      'cardsMultiple': RoomType11Calculator.get_cards_multiple(v['cards'],
                                                                                               self.info[
                                                                                                   'multipleRules']),
                                      "goldChange": v["goldChange"], "userId": v["entity"].info["userId"]}
                # 存储玩家信息
                replay_single_chapter_data["playerInfo"][k] = replay_player_data
                chapter_data.append(player_data)
            replay_all_chapter_data[c] = replay_single_chapter_data
            _history_record[c] = chapter_data
        replay_data["chapterInfo"] = replay_all_chapter_data
        # 战绩记录
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
        if self.is_tea_house_room:
            # 通知base的冠名赛记录该房间
            self.base.cellToBase(
                {"func": "writeTeaHouseRoom", "teaHouseId": self.info["teaHouseId"], "type": self.info["type"],
                 'recordPlayers': record_players})
        DEBUG_MSG('[Room id %i]------>writeChapterInfoToDB, _chapterInfos %s ' % (self.id, self._chapterInfos))

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
        elif _func == "TipCards":
            self.tip_cards(account_entity_id, _data["cards1"], _data["cards2"])
        elif _func == "MatchCards":
            self.match_card(account_entity_id, _data["cards1"], _data["cards2"])
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
            self.voice_chat(account_entity_id, _data["url"])
        elif _func == "DisbandRoom":
            self.disband_room_broadcast(account_entity_id)
        elif _func == "DisbandRoomOperation":
            self.response_disband(account_entity_id, _data["result"])
        elif _func == "switchPot":
            self.switch_pot(account_entity_id, _data["switchPot"])
        # 接庄
        elif _func == 'ReceiveBanker':
            self.receive_banker(account_entity_id, _data['result'])
        # 补锅
        elif _func == "AddGoldToPot":
            self.add_gold_to_pot(account_entity_id, _data['add'])
        elif _func == "getMaxCardsCombination":
            self.get_max_cards_combination(account_entity_id)
        elif _func == 'ShareToWX':
            self.share_to_wx(account_entity_id)
        elif _func == 'FreeBlessCount':
            self.free_bless_count(account_entity_id)
        elif _func == "Bless":
            self.bless(account_entity_id, _data["type"])

    def refresh_client_state(self):
        """
        刷新玩家在线状态
        :return:
        """
        chapter = self.chapters[self.cn]
        client_state = {}
        for k, v in chapter['playerInGame'].items():
            client_state[v['entity'].id] = not v['entity'].client_death
        self.callOtherClientsFunction('RefreshOnlineState', client_state)

    def share_to_wx(self, account_id):
        chapter = self.chapters[self.cn]
        if self.info['roomType'] == 'card':
            title = '牌九房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '牌九房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '牌九房间'
        max_chapter = '局数：' + str(self.info['maxChapterCount'])
        min_stake = '最小下注' + str(self.info['minStake'])
        pot = ''
        grab_banker_type = ''
        max_multiple = ''
        pot_base = ''
        pot_mode = ''
        stake_mode = ''
        stake_count = str(self.info['stakeCount']) + '道杠'
        game_type = '小牌九' if self.info['playMode'] == 0 else '大牌九'
        player_count = len(chapter['playerInGame'])
        players = str(player_count) + '缺' + str(self.info['maxPlayersCount'] - player_count)
        if self.info['pot']:
            pot = '加锅'
            max_multiple = str(self.info['potMaxMultiple']) + '倍爆锅'
            pot_base = '锅底:' + str(self.info['potBase'])
            pot_mode = '一人一锅' if self.info['onePersonOnePot'] else ''
        else:
            if self.info['grabBankerType'] == 1:
                grab_banker_type = '抢庄'
            elif self.info['grabBankerType'] == 2:
                grab_banker_type = '轮庄'
            elif self.info['grabBankerType'] == 3:
                grab_banker_type = '固定庄'
            if self.info['stakeMode'] == 0:
                stake_mode = '选分'
            else:
                stake_mode = '固定' + str(self.info['stakeMode']) + '分'
        con = str('%s %s %s %s %s %s %s %s %s %s' % (players, max_chapter, pot, game_type,
                                                     max_multiple, pot_base, pot_mode, grab_banker_type,
                                                     min_stake, stake_mode))
        self.callClientFunction(account_id, 'ShareToWX', {'title': title, 'content': con})

    def voice_chat(self, accountId, url):
        """
        语音聊天
        :param accountId:
        :param url:
        :return:
        """
        _args = {"accountId": accountId, "url": url}
        self.callOtherClientsFunction("VoiceChat", _args)

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
        chapter = self.chapters[self.cn]
        pre_chapter = self.chapters[self.cn - 1]
        self.retRoomBaseInfo(accountId)
        self.retPlayerInRoomInfos(accountId)
        self.ret_chapter_info(accountId)

        if accountId == chapter['currentBankerOperatePlayer']:
            # 检测是否需要切锅
            if self.keep_banker_count >= 3 and self.info["pot"] and chapter["currentState"] == 0:
                dead_line = int(chapter["deadline"]) - int(time.time())
                self.callOtherClientsFunction("tipSwitchPot", {'Timer': dead_line})

    def get_player_in_game_count(self):
        """
        返回游戏内玩家数量
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        return len(_playerInGame)

    def get_player_with_location_index(self, location_index):
        for k, v in self.chapters[self.cn]["playerInGame"].items():
            if v["locationIndex"] == location_index:
                return k

    def get_player_info_with_location_index(self, location_index):
        for k, v in self.chapters[self.cn]["playerInGame"].items():
            if v["locationIndex"] == location_index:
                return v

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
            self.delTimer(chapter["bankerTimerId"])
            grab_players = chapter["grabBankerPlayers"]
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
                self.delTimer(chapter["mainTimerId"])
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
        elif timerHandle == chapter["stakeTime"]:
            # 押注计时器
            DEBUG_MSG('[Room id %s]------>onTimer stakeTime %s' % (self.id, timerHandle))
        elif timerHandle == chapter["dealCardTime"]:
            # 发牌动画计时器
            DEBUG_MSG('[Room id %s]------>onTimer dealCardTime %s' % (self.id, timerHandle))
            self.delTimer(chapter["dealCardTime"])
            chapter["dealCardTime"] = -1
            self.changeChapterState(4)
        elif timerHandle == chapter["matchCardTime"]:
            # 配牌计时器
            DEBUG_MSG('[Room id %s]------>onTimer matchCardTime %s' % (self.id, timerHandle))
            chapter["matchCardTime"] = -1
            self.delTimer(chapter["matchCardTime"])
            # 自动配牌
            for k, v in chapter["playerInGame"].items():
                if k not in chapter["unMatchedPlayers"]:
                    continue
                cards1 = [v["cards"][0], v["cards"][1]] if self.info["playMode"] == 0 else [v["cards"][0],
                                                                                            v["cards"][1]]
                cards2 = [v["cards"][0], v["cards"][1]] if self.info["playMode"] == 0 else [v["cards"][2],
                                                                                            v["cards"][3]]
                self.match_card(k, cards1, cards2)
        elif timerHandle == chapter["compareCardTime"]:
            DEBUG_MSG('[Room id %s]------>onTimer compareCardTime %s' % (self.id, timerHandle))
            chapter["compareCardTime"] = -1
            self.delTimer(chapter["compareCardTime"])
            self.changeChapterState(6)
        elif timerHandle == chapter["settlementTime"]:
            DEBUG_MSG('[Room id %s]------>onTimer settlementTime %s' % (self.id, timerHandle))
            chapter["settlementTime"] = -1
            self.delTimer(chapter["settlementTime"])
            self.clear_chapter()
            self.changeChapterState(0)

        elif timerHandle == chapter["settlementClearPlayers"]:
            chapter["settlementClearPlayers"] = -1
            self.delTimer(chapter["settlementClearPlayers"])
            # 清理观战的玩家
            _playerOutGameCopy = chapter["playerOutGame"].copy()
            for k, v in _playerOutGameCopy.items():
                self.kick_out(k)
            # 清理坐下的玩家
            _playerInGameCopy = chapter["playerInGame"].copy()
            for k, v in _playerInGameCopy.items():
                self.kick_out(k)
        elif timerHandle == chapter['receiveBankerTime']:
            # 关闭计时器
            chapter["receiveBankerTime"] = -1
            self.delTimer(chapter["receiveBankerTime"])
            # 如果钱不够无法接庄
            current_banker_operate_player = chapter['playerInGame'][chapter['currentBankerOperatePlayer']]
            if current_banker_operate_player['gold'] >= self.info['potBase']:
                self.receive_banker(chapter['currentBankerOperatePlayer'], True)
            elif not self.have_gold_limit():
                self.receive_banker(chapter['currentBankerOperatePlayer'], True)
            else:
                self.receive_banker(chapter['currentBankerOperatePlayer'], False)
        elif timerHandle == chapter['switchPotTime']:
            chapter["switchPotTime"] = -1
            self.delTimer(chapter["switchPotTime"])
            chapter['currentBankerOperatePlayer'] = chapter['banker']
            self.switch_pot(chapter['currentBankerOperatePlayer'], False)
        elif timerHandle == chapter['totalSettlementTime']:
            chapter["totalSettlementTime"] = -1
            self.delTimer(chapter["totalSettlementTime"])
            self.total_settlement()
            self.write_chapter_info_to_db()

    def ret_current_chapter_state(self, accountEntityId):
        """
        发送当前牌局状态
        :param accountEntityId:
        :return:
        """
        chapter = self.chapters[self.cn]
        self.callClientFunction(accountEntityId, "CurrentChapterState", {"state": chapter["currentState"]})

    # 发牌
    def create_card(self):
        chapter = self.chapters[self.cn]
        # 第一局初始化
        if self.cn == 0:
            chapter["cards"] = RoomType11Calculator.cards.copy()
            chapter["faceCards"] = []
        cards = chapter["cards"]
        DEBUG_MSG("create cards :%s" % cards)
        # 洗牌两次
        shuffle(cards)
        shuffle(cards)
        player_in_game = chapter["playerInGame"]
        player_cards_info = {}
        for k, v in player_in_game.items():
            if self.info["playMode"] == 0:
                v["cards"] = cards[:2]
                del cards[:2]
            elif self.info["playMode"] == 1:
                v["cards"] = cards[:4]
                del cards[:4]
            cards_string = []
            DEBUG_MSG("create_cards accountId:%s,cards:%s" % (k, v["cards"]))
            for c in v["cards"]:
                s = str(c[0]) + "+" + str(c[1])
                if len(c) == 3:
                    s += "+" + str(c[2])
                cards_string.append(s)
            player_cards_info[k] = cards_string
        # 如果玩家数小于 4，构造虚拟玩家，凑够四个
        if len(player_in_game) < 4:
            virtual_player_count = 4 - len(player_in_game)
            for i in range(1, virtual_player_count + 1):
                if self.info["playMode"] == 0:
                    chapter["virtualPlayerCards"][-i] = cards[:2]
                    del cards[:2]
                elif self.info["playMode"] == 1:
                    chapter["virtualPlayerCards"][-i] = cards[:4]
                    del cards[:4]
                DEBUG_MSG("virtual player cards：%s" % chapter["virtualPlayerCards"][-i])
                virtual_cards_string = []
                for c in chapter["virtualPlayerCards"][-i]:
                    s = str(c[0]) + "+" + str(c[1])
                    if len(c) == 3:
                        s += "+" + str(c[2])
                    virtual_cards_string.append(s)
                player_cards_info[-i] = virtual_cards_string

        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        args = {"playerCards": player_cards_info, "dice": [dice1, dice2]}

        self.set_player_deal_index(dice1, dice2)

        self.callOtherClientsFunction("DealCards", args)

    def set_player_deal_index(self, dice1, dice2):
        chapter = self.chapters[self.cn]
        start_index = chapter["playerInGame"][chapter["banker"]]["locationIndex"]
        deal_start = (start_index + dice1 + dice2) % len(chapter["playerInGame"]) - 1
        if deal_start < 0:
            deal_start += len(chapter["playerInGame"])
        DEBUG_MSG("deal start%s" % deal_start)
        for i in range(0, len(chapter["playerInGame"])):
            player_info = self.get_player_info_with_location_index(deal_start)
            if player_info:
                player_info["dealCardIndex"] = i

            deal_start = self.get_next_location_have_player(deal_start)

    def tip_cards(self, accountId, cards1, cards2):
        """
        提示牌型
        :param accountId:
        :param cards1:
        :param cards2:
        :return:
        """
        cards_info1 = RoomType11Calculator.check_cards_type(cards1)
        cards_info2 = RoomType11Calculator.check_cards_type(cards2)
        args = {"cards1Type": cards_info1, "cards2Type": cards_info2}
        self.callClientFunction(accountId, "TipCards", args)
        pass

    def get_match_cards_player_info(self):
        stake_max_1, stake_max_2, stake_max_3 = 0, 0, 0
        chapter = self.chapters[self.cn]
        playerInGame = chapter["playerInGame"]
        notice_player = []
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
        cards_type, number = RoomType11Calculator.check_cards_type(cards)
        args = {"cards": cards, "type": [cards_type, number]}
        self.callClientFunction(accountId, "GetCardsType", args)

    def match_card(self, accountId, cards1, cards2):
        DEBUG_MSG("[RoomType7]-----matchCard-----accountId%s,cards1:%s,cards2:%s" % (
            accountId, cards1, cards2))
        chapter = self.chapters[self.cn]
        cards1_info = RoomType11Calculator.check_cards_type(cards1)
        cards2_info = RoomType11Calculator.check_cards_type(cards2)
        result = RoomType11Calculator.compare_one_couple_cards(cards1_info, cards2_info)
        if result == 1:
            bigger = cards1
            cards1 = cards2
            cards2 = bigger
            bigger_info = cards1_info
            cards1_info = cards2_info
            cards2_info = bigger_info
        # 配牌
        # 小天九
        if self.info["playMode"] == 0:
            chapter["playerInGame"][accountId]["cards"] = cards1
            chapter["playerInGame"][accountId]["cardsInfo"] = [cards2_info, cards1_info]
        elif self.info["playMode"] == 1:
            chapter["playerInGame"][accountId]["cards"] = cards2 + cards1
            chapter["playerInGame"][accountId]["cardsInfo"] = [cards2_info, cards1_info]
        chapter["playerInGame"][accountId]["matched"] = True
        chapter["unMatchedPlayers"].remove(accountId)
        self.callOtherClientsFunction("playerMatchCard", {"accountId": accountId})
        if len(chapter["unMatchedPlayers"]) == 0:
            chapter["matchCardTime"] = -1
            self.delTimer(chapter["matchCardTime"])
            self.changeChapterState(5)

    def compare_cards(self):
        chapter = self.chapters[self.cn]
        banker = chapter["banker"]
        win_info = {}
        cards_info = {}
        for k, v in chapter["playerInGame"].items():
            # 记录牌值和类型
            # 牌值和类型转为字符串
            cards_string = []
            cards_multiple = RoomType11Calculator.get_cards_multiple(v['cards'], self.info['multipleRules'])
            for c in v["cards"]:
                s = str(str(c[0]) + "+" + str(c[1]))
                if len(c) == 3:
                    s += "+" + str(c[2])
                cards_string.append(s)
            cards_info_string = []
            for c_info in v["cardsInfo"]:
                cards_info_string.append(str(str(c_info[0]) + "+" + str(c_info[1])))
                cards_info[k] = {"cards": cards_string, "cardsInfo": cards_info_string, 'cardsMultiple': cards_multiple}
            if k == banker:
                continue
            banker_cards = chapter["playerInGame"][banker]["cards"]
            result = RoomType11Calculator.compare_cards(v["cards"], banker_cards, 2)
            # 1 闲家赢，2 闲家输，0 和
            win_info[k] = result
            # 如果庄家赢
            if result == 2:
                self.calculate_score(banker, k, v["stake"])
            # 如果闲家赢
            elif result == 1:
                self.calculate_score(k, banker, v["stake"])
            # 平局
            elif result == 0:
                # 平局闲家回收下注
                v["goldChange"] += v["stake"][1] + v["stake"][2]
                # 如果是三道
                if self.info["stakeCount"] == 3:
                    v["goldChange"] += v["stake"][3]
            else:
                pass
        args = {"compareResult": win_info, "playerCardsInfo": cards_info}
        self.callOtherClientsFunction("CompareResult", args)

    # 不加锅计算分数
    def calculate_score(self, winner, loser, stake):
        chapter = self.chapters[self.cn]
        player_in_game = chapter["playerInGame"]
        stake = stake[1] if stake[1] >= 0 else 0
        win_gold = stake
        win_gold *= RoomType11Calculator.get_cards_multiple(player_in_game[winner]['cards'],
                                                            self.info['multipleRules'])

        # 如果输家为庄家，扣除庄家金币，闲家收回金币
        if loser == chapter["banker"]:
            player_in_game[winner]["goldChange"] += stake + win_gold
            player_in_game[loser]["goldChange"] -= win_gold
        # 如果赢家为庄家，闲家不收回金币
        elif winner == chapter["banker"]:
            player_in_game[winner]["goldChange"] += win_gold
            player_in_game[loser]['goldChange'] = -win_gold

    def settlement(self):
        chapter = self.chapters[self.cn]
        banker = chapter["banker"]
        player_in_game = chapter["playerInGame"]
        args = {"playerGoldInfo": {}}

        # 加锅牌九数据修正
        # 如果是加锅牌九，退回庄家输掉的超过锅底的钱
        if self.info["pot"]:
            if chapter["playerInGame"][banker]["goldChange"] < 0:
                if abs(chapter["playerInGame"][banker]["goldChange"]) > chapter["potStake"]:
                    # 退回的钱
                    back_gold = abs(chapter["playerInGame"][banker]["goldChange"]) - chapter["potStake"]
                    chapter["playerInGame"][banker]["goldChange"] = -chapter["potStake"]
                    player_list = self.sort_by_card()
                    player_list.reverse()
                    for player in player_list:
                        player_account_id = player["entity"].id
                        if not player_account_id:
                            continue
                        if player_account_id == banker:
                            continue
                        # 只有赢钱的人退
                        if player_in_game[player_account_id]["goldChange"] > 0:
                            if player_in_game[player_account_id]["goldChange"] >= back_gold:
                                player_in_game[player_account_id]["goldChange"] -= back_gold
                                break
                            else:
                                back_gold -= player_in_game[player_account_id]["goldChange"]
                                player_in_game[player_account_id]["goldChange"] = 0

        # # 比赛分场闲家不能输为负数
        # for k, v in chapter["playerInGame"].items():
        #     # 如果闲家输的钱大于已有钱
        #     if k != chapter["banker"]:
        #         if v["gold"] < abs(v["goldChange"]) and v["goldChange"] < 0:
        #             # 减去庄家多赢的钱
        #             banker_back_to_other = abs(v["goldChange"]) - v["gold"]
        #             # 玩家输的钱等于已有钱
        #             v["goldChange"] = -v["gold"]
        #             chapter["playerInGame"][chapter["banker"]]["goldChange"] -= banker_back_to_other

        for k, v in chapter["playerInGame"].items():
            v["gold"] += v["goldChange"]
            if k == chapter["banker"]:
                chapter["potStake"] += v["goldChange"]
            v["totalGoldChange"] += v["goldChange"]
            player_gold_info = {"gold": v["gold"], "goldChange": float(v["goldChange"]),
                                'totalGoldChange': v['totalGoldChange'],
                                "stake": {1: v["stake"][1], 2: v["stake"][2], 3: v["stake"][3]}}
            args["playerGoldInfo"][k] = player_gold_info
            # 设置玩家比赛分
            if self.info["roomType"] == "gameCoin":
                self.set_base_player_game_coin(k)
            # 设置玩家金币
            else:
                self.set_base_player_gold(k)

        args["potStake"] = chapter["potStake"]
        self.callOtherClientsFunction("settlement", args)
        self.settlement_count += 1
        if self.settlement_count == 1:
            self.base.cellToBase({'func': 'addTodayRoom'})
        # 持续当庄局数+1
        self.keep_banker_count += 1

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

        # 如果钻石场超过局数限制，总结算
        if self.cn + 1 >= self.info["maxChapterCount"] and not self.info["pot"]:
            # 超过局数限制，开启总结算计时器
            chapter["totalSettlementTime"] = self.addTimer(_timeTotalSettlement, 0, 0)
            chapter["deadline"] = time.time() + _timeTotalSettlement
        else:
            chapter["settlementTime"] = self.addTimer(_timeSettlement, 0, 0)
            chapter["deadline"] = time.time() + _timeSettlement

    def sort_by_card(self):
        """
        此功能为通过比较闲家牌的大小来判定优先赔付顺序
        使用冒泡排序，元素交换的条件为两个玩家的比牌结果
        比牌采用先比小牌，小牌相同比大牌，大牌也相同随机选择的策略

        # 玩家手牌集合:list
        for i in len(list)-1:
            for j in len(list)-1-j:
                if list[i]>list[j]:
                    list[i],list[j]=list[j],list[i]
        :return:
        """
        chapter = self.chapters[self.cn]
        player_list = []
        for k, v in chapter["playerInGame"].items():
            if k == chapter["banker"]:
                continue
            player_list.append(v)

        # 按牌的大小排序
        for x in range(0, len(player_list) - 1):
            for y in range(0, len(player_list) - 1 - x):
                result = 0
                # 大者放前面
                # 如果是小牌九:
                if self.info["playMode"] == 0:
                    result = RoomType11Calculator.compare_cards(player_list[y]["cards"], player_list[y + 1]["cards"],
                                                                -1)
                # 大牌默认在前面，是0,1，如果配牌顺序修改，此处也需要修改
                # 如果是大牌九:
                elif self.info["playMode"] == 1:
                    # 获取前者的小牌的牌组信息
                    cards_1_info = RoomType11Calculator.check_cards_type(
                        [player_list[y]["cards"][2], player_list[y]["cards"][3]])
                    # 获取后者的小牌的牌组信息
                    cards_2_info = RoomType11Calculator.check_cards_type(
                        [player_list[y + 1]["cards"][2], player_list[y + 1]["cards"][3]])
                    result = RoomType11Calculator.compare_one_couple_cards(cards_1_info, cards_2_info, -1)

                # 计算比牌结果，如果第二组牌大，则第二组牌排在前面
                if result == 2:
                    player_list[y], player_list[y + 1] = player_list[y + 1], player_list[y]

                elif result == 0:
                    # 小牌比完比大牌
                    # 获取前者的大牌的牌组信息
                    cards_1_info = RoomType11Calculator.check_cards_type(
                        [player_list[y]["cards"][0], player_list[y]["cards"][1]])
                    # 获取后者的大牌的牌组信息
                    cards_2_info = RoomType11Calculator.check_cards_type(
                        [player_list[y + 1]["cards"][0], player_list[y + 1]["cards"][1]])
                    result = RoomType11Calculator.compare_one_couple_cards(cards_1_info, cards_2_info, -1)
                    # 计算比牌结果，如果第二组牌大，则第二组牌排在前面
                    if result == 2:
                        player_list[y], player_list[y + 1] = player_list[y + 1], player_list[y]

                    # 如果小牌大牌都一样大，随机
                    elif result == 0:
                        random_int = random.randint(0, 1)
                        if random_int == 1:
                            player_list[y], player_list[y + 1] = player_list[y + 1], player_list[y]
        DEBUG_MSG("sort_by_card_and_deal_card_index:%s" % player_list)
        # 优先得钱的放前面
        return player_list

    def clear_chapter(self):
        DEBUG_MSG('[Room id %i]------>chapterRestart ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _playerInRoom = _chapter["playerInRoom"]
        _playerOutGame = _chapter["playerOutGame"]

        _newChapter = self.newChapter(_chapter["maxPlayerCount"])
        _newChapter["playerInGame"] = copy.deepcopy(_playerInGame)
        _newChapter["playerOutGame"] = copy.deepcopy(_playerOutGame)
        _newChapter["playerInRoom"].update(_newChapter["playerInGame"])
        _newChapter["playerInRoom"].update(_newChapter["playerOutGame"])
        # 继承锅底
        _newChapter["potStake"] = _chapter["potStake"]
        # 如果上局的牌没有用完，继续用上局的牌
        if len(_chapter["cards"]) > 0:
            _newChapter["cards"] = _chapter["cards"]
            _newChapter["faceCards"] += _chapter["faceCards"]
            for k, v in _chapter["playerInGame"].items():
                for card in v["cards"]:
                    _newChapter["faceCards"].append(card)
            for k, v in _chapter["virtualPlayerCards"].items():
                for card in v:
                    _newChapter["faceCards"].append(card)
            DEBUG_MSG("clear chapters,face cards %s" % _newChapter["faceCards"])
        else:
            _newChapter["cards"] = RoomType11Calculator.cards.copy()
            _newChapter["faceCards"] = []

        # 如果是加锅牌九，用上局的庄家
        if self.info["pot"]:
            _newChapter["banker"] = _chapter["banker"]
            _newChapter["bankerIndex"] = _chapter["bankerIndex"]

        for k, v in _newChapter["playerInRoom"].items():
            v["stake"] = {1: -1, 2: -1, 3: -1}
            v["grabBanker"] = -1
            # 本局金币变化
            v["goldChange"] = 0
            # 准备
            v["ready"] = False
            v["matched"] = False
            v["dealCardIndex"] = -1
            DEBUG_MSG("clear chapter,player in room,id:%s,ready:%s" % (k, v["ready"]))
            v["cards"] = []
            v["cardsInfo"] = []

    def ret_chapter_info(self, accountId):
        chapter = self.chapters[self.cn]
        play_in_game = chapter["playerInGame"]
        # 无限自动开牌时间前台重连不需要倒计时
        if self.info["autoCompareTime"] == 0:
            dead_line = -1
        else:
            dead_line = int(chapter["deadline"]) - int(time.time())
        chapter_info = {"currentRound": int(chapter['currentRound']), "currentState": int(chapter["currentState"]),
                        "deadline": dead_line, "banker": int(chapter["banker"]),
                        "started": self.started,
                        "teaHouseId": self.info["teaHouseId"] if "teaHouseId" in self.info.keys() else -1,
                        "cards": self.get_cards_string(chapter["cards"]),
                        "bankerIndex": int(chapter["bankerIndex"]), "potStake": int(chapter["potStake"]),
                        "isDisbanding": self.is_disbanding, "disbandSender": self.disband_sender}

        if len(self.chapters) > 1:
            chapter_info["preBanker"] = self.chapters[self.cn - 1]["banker"]
        _playerData = {}
        for k, v in play_in_game.items():
            _playerData[k] = {"goldChange": v["goldChange"],
                              "name": v["entity"].info["name"],
                              "totalGoldChange": v["totalGoldChange"],
                              "ready": v["ready"],
                              "matched": v["matched"],
                              "locationIndex": v["locationIndex"],
                              "stake": v["stake"],
                              "gold": v["gold"] if chapter['currentState'] == 7 or
                                                   chapter['currentState'] == 6 else v["gold"] + v["goldChange"],
                              "grabBanker": v["grabBanker"],
                              "agreeDisband": v["agreeDisband"]
                              }
            # 牌型对应的倍数
            if len(v['cards']) != 0:
                _playerData[k]['cardsMultiple'] = RoomType11Calculator.get_cards_multiple(v['cards'],
                                                                                          self.info['multipleRules'])
        chapter_info["playerData"] = _playerData
        # 已揭示牌值
        face_cards = self.get_cards_string(chapter["faceCards"])
        chapter_info["faceCards"] = face_cards
        # 当前牌局玩家手牌
        current_chapter_players_cards = {}
        # 当前牌局玩家手牌类型
        current_chapter_players_cards_info = {}
        for k, v in chapter["playerInGame"].items():
            current_chapter_players_cards[k] = self.get_cards_string(v["cards"])
            current_chapter_players_cards_info[k] = self.get_cards_info_string(v["cardsInfo"])
        for k, v in chapter["virtualPlayerCards"].items():
            current_chapter_players_cards[k] = self.get_cards_string(v)
        chapter_info["playerCards"] = current_chapter_players_cards
        chapter_info["playerCardsInfo"] = current_chapter_players_cards_info
        self.callClientFunction(accountId, "Reconnect", chapter_info)

    def get_cards_string(self, cards):
        cards_string = []
        for c in cards:
            s = str(c[0]) + "+" + str(c[1])
            if len(c) == 3:
                s += "+" + str(c[2])
            cards_string.append(s)
        return cards_string

    def get_cards_info_string(self, cardsInfo):
        cards_info_string = []
        for c_info in cardsInfo:
            cards_info_string.append(str(str(c_info[0]) + "+" + str(c_info[1])))
        return cards_info_string

    def total_settlement(self):
        if self.total_settlement_ed:
            return
        self.close_all_timer()
        self.changeChapterState(7)
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
        # 清理观战的玩家
        _playerOutGameCopy = chapter["playerOutGame"].copy()
        for k, v in _playerOutGameCopy.items():
            self.kick_out(k)
        # 同步局数
        if self.is_tea_house_room and self.settlement_count >= 1:
            self.set_base_player_chapter_count()

        # if self.settlement_count >= 1:
        #     chapter["accountLottery"] = self.addTimer(0.5, 0, 0)

        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(settlement_clear_players_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_clear_players_time

    def close_all_timer(self):
        chapter = self.chapters[self.cn]
        chapter["bankerTimerId"] = -1
        self.delTimer(chapter["bankerTimerId"])
        chapter["createCardTime"] = -1
        self.delTimer(chapter["createCardTime"])
        chapter["stakeTime"] = -1
        self.delTimer(chapter["stakeTime"])
        chapter["dealCardTime"] = -1
        self.delTimer(chapter["dealCardTime"])
        chapter["matchCardTime"] = -1
        self.delTimer(chapter["matchCardTime"])
        chapter["compareCardTime"] = -1
        self.delTimer(chapter["compareCardTime"])
        chapter["settlementTime"] = -1
        self.delTimer(chapter["settlementTime"])
        self.disband_timer = -1
        self.delTimer(self.disband_timer)

    def tea_house_disband_room_by_creator(self):
        """
        群主解散房间回调
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

        if self.chapters[self.cn]["currentState"] != 7:
            self.total_settlement()
            self.write_chapter_info_to_db()

    # 切锅
    def switch_pot(self, account_id, switch_pot):
        chapter = self.chapters[self.cn]
        # 只有阶段0,准备阶段，才能切庄
        if chapter['currentState'] != 0:
            self.callClientFunction(account_id, 'Notice', ['游戏不在准备阶段，无法切锅'])
            return
        # 必须是庄家才能选择切不切庄：
        if account_id != chapter['banker']:
            self.callClientFunction(account_id, 'Notice', ['您不是庄家，无法操作'])
            return
        # 关闭计时器
        chapter["switchPotTime"] = -1
        self.delTimer(chapter["switchPotTime"])
        # 一人一锅玩法，切锅时通知下个人接庄
        if self.info['onePersonOnePot']:
            if switch_pot:
                # 切庄，开始接庄
                location_index = chapter['playerInGame'][account_id]['locationIndex']
                next_index = self.get_next_location_have_player(location_index)
                next_account_id = self.get_account_id_with_location_index(next_index)
                # 如果下个人是第一局的庄家，证明轮了一遍，总结算
                if next_account_id == self.chapters[0]['banker']:
                    self.total_settlement()
                    self.write_chapter_info_to_db()
                    return
                chapter['currentBankerOperatePlayer'] = next_account_id
                # 通知下个人接庄
                args = {"Timer": _timeReceiveBanker, 'operatorId': next_account_id}
                self.callOtherClientsFunction("StartReceiveBanker", args)
                chapter["receiveBankerTime"] = self.addTimer(_timeReceiveBanker, 0, 0)
                chapter["deadline"] = time.time() + _timeReceiveBanker
            else:
                chapter['currentBankerOperatePlayer'] = -1
                # 如果不切锅，自动准备，开始
                for k, v in chapter["playerInGame"].items():
                    self.player_ready(k)
        # 经典玩法
        else:
            if switch_pot:
                if chapter["currentState"] == 0:
                    self.total_settlement()
                    self.write_chapter_info_to_db()
            else:
                # 如果不切锅，自动准备
                for k, v in chapter["playerInGame"].items():
                    self.player_ready(k)

    def receive_banker(self, account_id, result):
        """
        接庄
        :param account_id:
        :param result:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>receive_banker, accountId %s,result%s' % (self.id, account_id, result))
        chapter = self.chapters[self.cn]
        # 只有阶段0,准备阶段，才能接庄
        if chapter['currentState'] != 0:
            self.callClientFunction(account_id, 'Notice', ['游戏不在准备阶段，无法接庄'])
            return
        # 非当前玩家不能接庄
        if account_id != chapter['currentBankerOperatePlayer']:
            self.callClientFunction(account_id, 'Notice', ['上庄失败，当前不该你操作'])
            return
        # 庄家不能接庄：
        if account_id == chapter['banker']:
            self.callClientFunction(account_id, 'Notice', ['您是庄家，无法操作'])
            return
        # 关闭计时器
        chapter["receiveBankerTime"] = -1
        self.delTimer(chapter["receiveBankerTime"])
        # 接庄
        if result:
            # 币不足锅底无法接庄
            if self.have_gold_limit() and chapter['playerInGame'][account_id]['gold'] < self.info['potBase']:
                self.callClientFunction(account_id, 'Notice', ['%s不够锅底，无法接庄' % self.gold_name])
                return
            chapter['playerInGame'][account_id]['receiveBanker'] = True
            chapter['potStake'] = 0
            # 加锅
            self.add_gold_to_pot(account_id, self.info['potBase'])
            # 发送庄家结果
            self.send_banker_result(account_id, receive_banker_mode=True)
            # 清除当庄次数
            self.keep_banker_count = 0
            chapter['currentBankerOperatePlayer'] = -1
            # 自动准备,开始
            for k, v in chapter["playerInGame"].items():
                self.player_ready(k)
        # 不接庄
        else:
            chapter['playerInGame'][account_id]['receiveBanker'] = False
            location_index = chapter['playerInGame'][account_id]['locationIndex']
            # 通知下个人接庄
            next_index = self.get_next_location_have_player(location_index)
            next_account_id = self.get_account_id_with_location_index(next_index)
            # 如果下个人是第一个庄家，证明轮了一遍，总结算
            if next_account_id == self.chapters[0]['banker']:
                self.total_settlement()
                self.write_chapter_info_to_db()
                return
            # 下个玩家为当前接庄玩家
            chapter['currentBankerOperatePlayer'] = next_account_id
            # 通知下个人接庄
            args = {"Timer": _timeReceiveBanker, 'operatorId': next_account_id}
            self.callOtherClientsFunction("StartReceiveBanker", args)
            chapter["receiveBankerTime"] = self.addTimer(_timeReceiveBanker, 0, 0)
            chapter["deadline"] = time.time() + _timeReceiveBanker

    def add_gold_to_pot(self, account_id, add):
        """
        往锅里加钱
        :param account_id:
        :param add:
        :return:
        """
        chapter = self.chapters[self.cn]
        if self.have_gold_limit() and add > chapter['playerInGame'][account_id]['gold']:
            self.callClientFunction(account_id, 'Notice', ['%s不足' % self.gold_name])
            return
        # 锅底加钱
        chapter['potStake'] += add
        # 通知客户端
        self.callOtherClientsFunction('AddGoldToPot',
                                      {'bankerId': account_id, 'modifyGold': add,
                                       'bankerGold': chapter['playerInGame'][account_id]['gold'],
                                       'potStake': chapter['potStake']})

    def get_max_cards_combination(self, accountEntityId):
        # 提示最大牌型，只有大天九支持
        if self.info["playMode"] == 1:
            chapter = self.chapters[self.cn]
            player = chapter["playerInGame"][accountEntityId]
            max_combination_string = RoomType11Calculator.get_max_combination(player["cards"])
            self.callClientFunction(accountEntityId, "maxCardsCombination", {"cards": max_combination_string})
