# -*- coding: utf-8 -*-
import copy

import KBEngine

import Const
import RoomType10Calculator
import RoomType7Calculator
from KBEDebug import *
from RoomBase import *
import json
import time

# 选庄家动画时间
choice_banker_time = 2
# 抢庄倒计时时间
_timeGrabBanker = 5
# 切庄倒计时
_timeSwitchBanker = 5
# 接庄倒计时
_timeReceiveBanker = 5
# 押注倒计时时间
_timeStake = 15
# 发牌计时器
_timeDealCards = 2
# 比牌动画时间
_time_compare_cards = 8
# 结算时间
_timeSettlement = 5
# 扣牌时间
_timeMatchBanker = 8
# 解散房间倒计时
time_disband = 30
# 总结算清理玩家倒计时
settlement_clear_players_time = 20


class RoomType10(RoomBase):
    # 牌局信息
    _chapterInfos = {}
    # 是否是手动解散
    is_manual_disband = False
    # 是否是群主解散
    disband_from_creator = False
    # 是否已经总结算
    total_settlement_ed = False
    # 结算次数
    settlement_count = 0
    # 开始标识
    started = False
    # 所有空位的 List
    emptyLocationIndex = []
    # 爆锅上限倍数
    potMaxMultiple = 0

    # 持续当庄次数
    keepBankerCount = 0

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
        # 当前房间状态 0 准备, 1 抢庄, 2 押注/钓鱼, 3 开牌, 4 结算
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
        # 选择庄家动画时间
        _chapter["choiceBankerTime"] = -1
        # 发牌倒计时
        _chapter["dealCardTime"] = -1
        # 抢庄计时器
        _chapter["bankerTimerId"] = -1
        # 结算计时器
        _chapter["settlementTime"] = -1
        # 切庄倒计时
        _chapter['switchBankerTime'] = -1
        # 接庄倒计时
        _chapter['receiveBankerTime'] = -1
        # 下注计时器
        _chapter["stakeTime"] = -1
        # 比牌计时器
        _chapter["compareCardTime"] = -1
        # 配牌计时器
        _chapter['matchCardTime'] = -1
        # 发牌动画计时器
        _chapter["dealCardsTime"] = -1
        # 当前计时时刻点
        _chapter["deadline"] = -1
        # 下注总额
        _chapter["stake"] = {1: 0, 2: 0, 3: 0}
        # 参与抢庄的玩家
        _chapter["grabBankerPlayers"] = []
        # 牌库
        _chapter['cards'] = []
        # 出门
        _chapter["cardsC"] = []
        # 末门
        _chapter["cardsM"] = []
        # 抽奖
        _chapter["accountLottery"] = -1
        # 天门
        _chapter["cardsT"] = []
        # 庄家
        _chapter["cardsZ"] = []
        # 配牌权值
        _chapter["weightsZ"] = -1
        _chapter["weightsC"] = -1
        _chapter["weightsM"] = -1
        _chapter["weightsT"] = -1
        # 比牌结果,99 为无意义的默认值
        _chapter["resultC"] = 99
        _chapter["resultM"] = 99
        _chapter["resultT"] = 99
        # 当前切庄、接庄操作玩家,只在切庄、接庄阶段有意义
        _chapter['currentBankerOperatePlayer'] = -1
        # 解散清除玩家倒计时
        _chapter["settlementClearPlayers"] = -1
        # 输赢情况
        _chapter["settlementArea"] = {"winArea": [], "loseArea": [], "drawArea": []}
        # 锅底的钱
        _chapter["potStake"] = 0
        self.chapters.append(_chapter)
        self.cn = len(self.chapters) - 1

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
        # 抢庄 没有操作:-1    不抢:0     抢:1
        _player["grabBanker"] = -1
        # 玩家押注
        # 1:出门，2：天门，3:末门
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
        # 同意解散状态
        _player["agreeDisband"] = False
        # 接庄
        _player['receiveBanker'] = False
        # 是否已经扣除过AA支付的钻石
        _player['AARoomCardConsumed'] = False
        # 钻石场从零开始
        if self.info["roomType"] == "card":
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 比赛分场带入已有比赛分
        elif self.info["roomType"] == "gameCoin":
            # 比赛分场修改使用比赛分为使用金币
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 普通比赛分场
        elif self.info['roomType'] == 'normalGameCoin':
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        return _player

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
        # 抢庄
        if _func == "GrabBanker":
            self.grab_banker(account_entity_id, _data["result"])
        # 切庄
        elif _func == 'SwitchBanker':
            self.switch_banker(account_entity_id, _data['result'])
        # 接庄
        elif _func == 'ReceiveBanker':
            self.receive_banker(account_entity_id, _data['result'])
        # 准备
        elif _func == "Ready":
            self.player_ready(account_entity_id)
        # 下注
        elif _func == "SetStake":
            self.set_stake(account_entity_id, _data["stake"], _data["stakeIndex"])
        # 补锅
        elif _func == "AddGoldToPot":
            self.add_gold_to_pot(account_entity_id, _data['add'])
        # 扣牌
        elif _func == "MatchCard":
            self.match_card(account_entity_id)
        # 离开房间
        elif _func == "LeaveRoom":
            self.onLeave(account_entity_id, _data)
        elif _func == "SetSeat":
            self.set_seat(account_entity_id, _data["locationIndex"])
        elif _func == "Bless":
            self.bless(account_entity_id, _data["type"])
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
        elif _func == 'ShareToWX':
            self.share_to_wx(account_entity_id)
        elif _func == 'FreeBlessCount':
            self.free_bless_count(account_entity_id)
        elif _func == 'TipCards':
            self.tip_cards(account_entity_id, _data["cards"])

    def tip_cards(self, account_entity_id, cards):
        """
        提示牌型
        :param account_entity_id:
        :param cards:
        :return:
        """
        weight = RoomType10Calculator.get_cards_weights(cards)
        self.callClientFunction(account_entity_id, 'tipCards', {'weight': weight})

    def share_to_wx(self, account_id):
        chapter = self.chapters[self.cn]
        if self.info['roomType'] == 'card':
            title = '八A房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '八A房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '八A房间'
        max_chapter = '局数：' + str(self.info['maxChapterCount'])
        min_stake = '最小下注' + str(self.info['minStake'])
        pot_stake = '锅底:' + str(self.info['potBase'])
        player_count = len(chapter['playerInGame'])
        players = str(player_count) + '缺' + str(self.info['maxPlayersCount'] - player_count)
        eight_x_double = '八叉翻倍' if self.info['eightXDouble'] else ''
        con = str('%s %s %s %s %s' % (players, max_chapter, min_stake, pot_stake, eight_x_double))
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
        self.ret_current_chapter_state(accountEntityId)
        self.retRoomBaseInfo(accountEntityId)
        # 如果比赛已经开始不自动坐下
        if _chapter["currentState"] == 0 and not self.started and len(self.emptyLocationIndex) != 0:
            if len(_chapter["playerInGame"]) < self.info["maxPlayersCount"]:
                self.set_seat(accountEntityId, self.emptyLocationIndex[0])
        # 有观战玩家进入
        else:
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.ret_out_game_player_info(k)
            # 给进入的玩家发送所有玩家信息
            self.ret_player_in_room_info(accountEntityId)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.ret_out_game_player_info(k)
            # 给进入的玩家发送牌局信息
            self.ret_chapter_info(accountEntityId)

    def ret_current_chapter_state(self, accountEntityId):
        """
        发送当前牌局状态信息
        :param accountEntityId:
        :return:
        """
        chapter = self.chapters[self.cn]
        self.callClientFunction(accountEntityId, "CurrentChapterState", {"state": chapter["currentState"]})

    def ret_out_game_player_info(self, accountId=-1):
        _chapter = self.chapters[self.cn]
        _playerOutGameNotEntity = {}

        for k, v in _chapter["playerOutGame"].items():
            _player = {"gold": v["gold"], "locationIndex": int(v["locationIndex"]), "name": v["entity"].info["name"],
                       "stake": v["stake"], "userId": v["entity"].info["userId"], "ip": v["entity"].info["ip"],
                       "headImageUrl": v["entity"].info["headImageUrl"], "ready": v["ready"]}
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerOutGame": _playerOutGameNotEntity}
        DEBUG_MSG('[Room id %i]------>ret_out_game_player_info %s' % (self.id, _args))
        if accountId == -1:
            self.callOtherClientsFunction("RetOutGamePlayerInfo", _args)
        else:
            self.callClientFunction(accountId, "RetOutGamePlayerInfo", _args)

    def ret_player_in_room_info(self, accountId=-1):
        """
        广播房间内所有玩家状态
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGameNotEntity = {}
        _playerOutGameNotEntity = {}
        player_in_game_to_base = {}

        for k, v in _chapter["playerInGame"].items():
            _player = {"gold": v["gold"], "locationIndex": int(v["locationIndex"]), "name": v["entity"].info["name"],
                       "stake": v["stake"], "userId": v["entity"].info["userId"], "ip": v["entity"].info["ip"],
                       'totalGoldChange': v['totalGoldChange'], "headImageUrl": v["entity"].info["headImageUrl"],
                       "ready": v["ready"]}
            player_in_game_to_base[int(v["locationIndex"])] = {"name": v["entity"].info["name"],
                                                               "databaseId": v["entity"].info["dataBaseId"],
                                                               "headImageUrl": v["entity"].info["headImageUrl"]}
            _playerInGameNotEntity[int(k)] = _player
        for k, v in _chapter["playerOutGame"].items():
            _player = {"gold": v["gold"], "locationIndex": int(v["locationIndex"]), "name": v["entity"].info["name"],
                       "stake": v["stake"], "userId": v["entity"].info["userId"], "ip": v["entity"].info["ip"],
                       'totalGoldChange': v['totalGoldChange'], "headImageUrl": v["entity"].info["headImageUrl"],
                       "ready": v["ready"]}
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
        self.base.cellToBase(
            {"func": "refreshPlayerInGame", "playerInGame": player_in_game_to_base, "teaHouseId": tea_house_id})

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
        # 移除空位
        self.emptyLocationIndex.remove(locationIndex)
        # 给base端发送坐下玩家信息
        self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 发送所有玩家信息
        self.ret_player_in_room_info()
        # 每人满时，创建新的房间(onRoomEnd为true时插入在当前房间后面)
        if len(_chapter['playerInGame']) == self.info['maxPlayersCount']:
            self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})

    def player_ready(self, account_id):
        """
        玩家准备
        :param account_id:
        :return:
        """
        DEBUG_MSG("player ready account id:%s" % account_id)
        chapter = self.chapters[self.cn]
        _player = chapter["playerInGame"][account_id]
        if chapter['currentState'] != 0:
            self.callClientFunction(account_id, 'Notice', ['游戏不在准备阶段，无法准备'])
            return
        if self.is_gold_session_room() and _player['gold'] < self.info['roomRate']:
            return
        _player["ready"] = True
        _args = {"accountId": account_id, "ready": True}
        self.callOtherClientsFunction("Ready", _args)

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
            # 准备阶段
            _args = {"state": state, "Timer": 0}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 自动准备
            for k, v in _chapter["playerInGame"].items():
                self.player_ready(k)

            _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
        elif state == 1:
            # 抢庄
            _args = {"state": state, "Timer": _timeGrabBanker}
            self.callOtherClientsFunction("changeChapterState", _args)
        elif state == 2:
            # 下注
            _args = {"state": state, "Timer": _timeStake}
            self.callOtherClientsFunction("changeChapterState", _args)
            _chapter["stakeTime"] = self.addTimer(_timeStake, 0, 0)
            _chapter["deadline"] = time.time() + _timeStake
        elif state == 3:
            # 发牌
            _args = {'state': state, 'Timer': _timeDealCards}
            self.callOtherClientsFunction('changeChapterState', _args)
            self.deal_cards()
            _chapter['dealCardsTime'] = self.addTimer(_timeDealCards, 0, 0)
            _chapter["deadline"] = time.time() + _timeDealCards
        elif state == 4:
            # 扣牌
            _args = {"state": state, "Timer": _timeMatchBanker}
            self.callOtherClientsFunction("changeChapterState", _args)
            _chapter["matchCardTime"] = self.addTimer(_timeMatchBanker, 0, 0)
            _chapter["deadline"] = time.time() + _timeMatchBanker
        elif state == 5:
            # 比牌
            _args = {"state": state, "Timer": _time_compare_cards}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.compare_cards()
            _chapter["compareCardTime"] = self.addTimer(_time_compare_cards, 0, 0)
            _chapter["deadline"] = time.time() + _time_compare_cards
        elif state == 6:
            # 结算
            _args = {"state": state, "Timer": _timeSettlement}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.settlement()
            _chapter["settlementTime"] = self.addTimer(_timeSettlement, 0, 0)
            _chapter["deadline"] = time.time() + _timeSettlement

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

    def banker_type_switch(self):
        """
        设置庄家
        :return:
        """
        chapter = self.chapters[self.cn]
        # grab_banker_type = self.info["grabBankerType"]
        # 如果是第一局，开始抢庄
        if self.cn == 0:
            args = {"Timer": _timeGrabBanker}
            self.callOtherClientsFunction("StartGrab", args)
            chapter["bankerTimerId"] = self.addTimer(_timeGrabBanker, 0, 0)
            chapter["deadline"] = time.time() + _timeGrabBanker
        # 达到锅底的十倍，强制切庄
        elif chapter['potStake'] >= self.info['potBase'] * self.info['potMaxMultiple']:
            self.switch_banker(chapter['banker'], True)
        # 如果当庄不超过三局，上局庄家继续当庄
        elif 1 <= self.keepBankerCount <= 2:
            self.changeChapterState(2)
        # 如果当庄超过三局，每局询问是否切庄
        elif self.keepBankerCount > 2:
            chapter['currentBankerOperatePlayer'] = chapter['banker']
            args = {"Timer": _timeSwitchBanker}
            self.callOtherClientsFunction("StartSwitchBanker", args)
            # 通知庄家切庄
            self.callClientFunction(chapter['banker'], 'SwitchBanker', {})
            chapter["switchBankerTime"] = self.addTimer(_timeSwitchBanker, 0, 0)
            chapter["deadline"] = time.time() + _timeSwitchBanker

    def receive_banker(self, account_id, result):
        """
        接庄
        只有在换庄阶段并且没当过庄家的人才可以接庄
        loop:
        if receive:
            start
        elif not receive:
            notice next receive

        :param account_id:操作者id
        :param result:接庄结果
        :return:
        """
        DEBUG_MSG('[Room id %i]------>receive_banker, accountId %s,result%s' % (self.id, account_id, result))
        chapter = self.chapters[self.cn]
        if chapter['currentState'] != 1:
            self.callClientFunction(account_id, 'Notice', ['游戏不在接庄阶段，无法接庄'])
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
            # 不足锅底无法接庄
            if self.have_gold_limit() and chapter['playerInGame'][account_id]['gold'] < self.info['potBase']:
                self.callClientFunction(account_id, 'Notice', ['%s不够锅底，无法接庄' % self.gold_name])
                return
            chapter['playerInGame'][account_id]['receiveBanker'] = True
            # 锅底返回给上个庄家，同步base货币，清空锅底
            chapter['playerInGame'][chapter['banker']]['gold'] += chapter['potStake']
            self.set_base_player_game_coin(chapter['banker'])
            # 刷新玩家信息
            self.send_gold_info(chapter['banker'])
            chapter['potStake'] = 0
            # 清除当庄次数
            self.keepBankerCount = 0
            # 扣除锅底的钱
            self.add_gold_to_pot(account_id, self.info['potBase'])
            # 发送庄家结果
            self.send_banker_result(account_id, receive_banker_mode=True)
            self.changeChapterState(2)
        # 不接庄
        else:
            chapter['playerInGame'][account_id]['receiveBanker'] = False
            # 通知下个人接庄
            next_account_id = self.get_next_player_id_by_account_id(account_id)
            # 如果下个人是第一局的庄家，证明轮了一遍，总结算
            if next_account_id == self.chapters[0]['banker']:
                self.total_settlement()
                self.write_chapter_info_to_db()
                return
            # 当前接庄玩家
            chapter['currentBankerOperatePlayer'] = next_account_id
            # 通知下个人接庄
            args = {"Timer": _timeReceiveBanker, 'operatorId': next_account_id}
            self.callOtherClientsFunction("StartReceiveBanker", args)
            chapter["receiveBankerTime"] = self.addTimer(_timeReceiveBanker, 0, 0)
            chapter["deadline"] = time.time() + _timeReceiveBanker

    def send_gold_info(self, account_id):
        """
        发送某个玩家的最新货币信息
        :param account_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        player = chapter['playerInRoom'][account_id]
        self.callOtherClientsFunction("refreshGold", {"gold": player["gold"], "accountId": account_id})

    def send_all_gold_info(self):
        for k, v in self.chapters[self.cn]['playerInRoom'].items():
            self.send_gold_info(k)

    def switch_banker(self, account_id, result):
        """
        切庄
        :param account_id:
        :param result:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>switch_banker, accountId %s,result%s' % (self.id, account_id, result))
        chapter = self.chapters[self.cn]
        if chapter['currentState'] != 1:
            self.callClientFunction(account_id, 'Notice', ['游戏不在切庄阶段，无法切庄'])
            return
        # 必须是庄家才能选择切不切庄：
        if account_id != chapter['banker']:
            self.callClientFunction(account_id, 'Notice', ['您不是庄家，无法操作'])
            return
        chapter["switchBankerTime"] = -1
        self.delTimer(chapter["switchBankerTime"])
        if result:
            # 切庄，开始接庄
            next_account_id = self.get_next_player_id_by_account_id(account_id)
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
            # 不切,继续当庄
            self.changeChapterState(2)

    def grab_banker(self, accountId, result):
        """
        抢庄
        :param result:
        :param accountId:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>grabBanker, accountId %s' % (self.id, accountId))
        chapter = self.chapters[self.cn]
        if chapter['currentState'] != 1:
            self.callClientFunction(accountId, 'Notice', ['游戏不在抢庄阶段，无法抢庄'])
            return
        player = chapter["playerInGame"][accountId]
        player["grabBanker"] = result
        if result == 1:
            args = {"result": 1}
            # 收集所有抢庄玩家
            chapter["grabBankerPlayers"].append(accountId)
        else:
            args = {"result": 0}
        args["accountId"] = accountId
        self.callOtherClientsFunction("GrabBankerResult", args)

        # 未抢庄玩家
        unGrabBankerPlayers = []
        for k, v in chapter["playerInGame"].items():
            if v["grabBanker"] == -1:
                unGrabBankerPlayers.append(k)
        # 如果所有人都操作过了进行到下个阶段
        if len(unGrabBankerPlayers) == 0:
            chapter["bankerTimerId"] = -1
            self.delTimer(chapter["bankerTimerId"])
            grab_players = chapter["grabBankerPlayers"]
            # 如果没有人参与抢庄，随机一个参与比赛的玩家
            if len(grab_players) == 0:
                banker = random.choice(list(chapter["playerInGame"].keys()))
            # 如果有人抢庄，随机一个参与抢庄的玩家
            else:
                banker = random.choice(grab_players)
            # 扣除锅底的钱
            self.add_gold_to_pot(banker, self.info['potBase'])
            # 发送庄家结果
            self.send_banker_result(banker)
            chapter["choiceBankerTime"] = self.addTimer(choice_banker_time, 0, 0)
            chapter["deadline"] = time.time() + choice_banker_time

    def match_card(self, account_id):
        """
        扣牌
        :param account_id:
        :return:
        """
        _chapter = self.chapters[self.cn]
        # 只有庄家可以配牌
        if account_id != _chapter['banker']:
            return
        _chapter["matchCardTime"] = -1
        self.delTimer(_chapter["matchCardTime"])
        self.changeChapterState(5)

    def send_banker_result(self, banker_account_id, receive_banker_mode=False):
        """
        此方法发送最终庄家结果，如果设置过庄家不会再设置（接庄模式除外）。
        :param receive_banker_mode:
        :param banker_account_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        # 如果已经设置过庄家不再发送消息，防止多次设置(接庄模式除外）
        if chapter["banker"] != -1 and chapter["bankerIndex"] != -1 and not receive_banker_mode:
            return
        chapter["banker"] = banker_account_id
        chapter["bankerIndex"] = self.get_location_with_account_id(banker_account_id)
        args = {"banker": banker_account_id, 'bankerGold': chapter['playerInGame'][banker_account_id]['gold']}
        self.callOtherClientsFunction("SetBanker", args)

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
        # 扣除庄家锅底钱
        chapter['playerInGame'][account_id]['gold'] -= add
        # 锅底加钱
        chapter['potStake'] += add
        # 通知客户端
        self.callOtherClientsFunction('AddGoldToPot', {'bankerId': account_id, 'modifyGold': add,
                                                       'bankerGold': chapter['playerInGame'][account_id]['gold'],
                                                       'potStake': chapter['potStake']})
        # 同步到base
        self.set_base_player_game_coin(account_id)

    def set_stake(self, accountId, stake, stake_index):
        """
        下注
        :param stake_index: 下注位置
        :param accountId:下注者id
        :param stake:下注金额
        :return:
        """
        chapter = self.chapters[self.cn]
        if chapter['currentState'] != 2:
            self.callClientFunction(accountId, 'Notice', ['游戏不在下注阶段，无法下注'])
            return
        # 不能小于最小下注
        if stake < self.info['minStake']:
            return
        _player_in_room = chapter["playerInRoom"]
        chapter_total_stake = chapter["stake"][1] + chapter["stake"][2] + chapter["stake"][3]
        DEBUG_MSG(
            '[Room id %i]------>setStake, accountId:%s, stake:%s ,stakeIndex:%s,potStake:%s,chapter_total_stake:%s' % (
                self.id, accountId, stake, stake_index, chapter['potStake'], chapter_total_stake))
        # 如果八叉开启，总下注不能超过锅底的一半
        if self.info['eightXDouble']:
            if stake + chapter_total_stake > chapter['potStake'] / 2:
                self.callClientFunction(accountId, "Notice", ["总注超过锅底的一半，无法下注"])
                return

        # 如果八叉关闭，总下注不能超过锅底
        else:
            if stake + chapter_total_stake > chapter['potStake']:
                self.callClientFunction(accountId, "Notice", ["总注超过锅底，无法下注"])
                return

        # 如果超过身上的钱，不能下注
        if self.have_gold_limit() and stake > _player_in_room[accountId]["gold"]:
            self.callClientFunction(accountId, "Notice", ["%s不足" % self.gold_name])
            return

        # 记录玩家下注数
        _player_in_room[accountId]["stake"][int(stake_index)] += stake
        # 记录总下注数
        chapter["stake"][int(stake_index)] += stake
        # 记录本局货币改变
        _player_in_room[accountId]["goldChange"] -= stake
        # 扣除玩家已有货币
        _player_in_room[accountId]['gold'] -= stake
        # 同步房间外
        self.set_base_player_game_coin(accountId)
        # 发送结果
        _args = {"accountId": accountId, "stake": stake, "stakeIndex": int(stake_index),
                 "gold": _player_in_room[accountId]["gold"]}
        self.callOtherClientsFunction("SetStake", _args)

    def deal_cards(self):
        chapter = self.chapters[self.cn]
        # 如果是6的整数倍，重新发牌
        if self.cn % 6 == 0 or self.cn == 0:
            chapter['cards'] = RoomType10Calculator.generate_cards()
        # 如果不是6的整数倍，用上局剩余的牌
        else:
            pre_chapter = self.chapters[self.cn - 1]
            chapter['cards'] = pre_chapter['cards']
            # 洗牌两次
            random.shuffle(chapter['cards'])
            random.shuffle(chapter['cards'])
        DEBUG_MSG('deal_cards cards:%s' % chapter['cards'])

        # 给各个门分牌
        chapter['cardsM'] = chapter['cards'][:2]
        chapter['cardsC'] = chapter['cards'][2:4]
        chapter['cardsT'] = chapter['cards'][4:6]
        chapter['cardsZ'] = chapter['cards'][6:8]
        # 记录各个门牌的大小
        chapter['weightsM'] = RoomType10Calculator.get_cards_weights(chapter['cardsM'])
        chapter['weightsC'] = RoomType10Calculator.get_cards_weights(chapter['cardsC'])
        chapter['weightsT'] = RoomType10Calculator.get_cards_weights(chapter['cardsT'])
        chapter['weightsZ'] = RoomType10Calculator.get_cards_weights(chapter['cardsZ'])
        # 删除牌库中分出的牌
        del chapter['cards'][:8]
        DEBUG_MSG('deal_cards over cards:%s m:%s,c:%s,k:%s,z:%s' % (
            chapter['cards'], chapter['cardsM'], chapter['cardsC'], chapter['cardsT'], chapter['cardsZ']))
        # 给客户端发送牌值
        self.callOtherClientsFunction('DealCards', {'cardsM': chapter['cardsM'], 'cardsC': chapter['cardsC'],
                                                    'cardsT': chapter['cardsT'], 'cardsZ': chapter['cardsZ']})

    def compare_cards(self):
        """
        比牌
        :return:
        """
        chapter = self.chapters[self.cn]
        DEBUG_MSG("[Room7]::compare_cards::weightsZ:%s,weightsT:%s,weightsM:%s,weightsC:%s" % (
            chapter["weightsZ"], chapter["weightsT"], chapter["weightsM"], chapter["weightsC"]))
        # 天门
        _t = RoomType10Calculator.compare_cards(chapter["cardsZ"], chapter["cardsT"], 1)
        # 末门
        _m = RoomType10Calculator.compare_cards(chapter["cardsZ"], chapter["cardsM"], 1)
        # 出门
        _c = RoomType10Calculator.compare_cards(chapter["cardsZ"], chapter["cardsC"], 1)
        # 记录比牌结果
        chapter["resultT"] = _t
        chapter["resultM"] = _m
        chapter["resultC"] = _c
        # 1:输，2：赢，0：平局
        args = {"resultT": _t, "resultM": _m, "resultC": _c, 'weightsC': chapter['weightsC'],
                'weightsZ': chapter['weightsZ'], 'weightsM': chapter['weightsM'], 'weightsT': chapter['weightsT']}
        self.callOtherClientsFunction("CompareCardsResult", args)
        t_area = RoomType10Calculator.get_total_result(_t)
        m_area = RoomType10Calculator.get_total_result(_m)
        c_area = RoomType10Calculator.get_total_result(_c)
        # 记录每个区域的输赢
        chapter["settlementArea"][c_area].append(1)
        chapter["settlementArea"][t_area].append(2)
        chapter["settlementArea"][m_area].append(3)

    def settlement(self):
        chapter = self.chapters[self.cn]
        banker = chapter["banker"]
        # 结算闲家胜利区域
        for area in chapter["settlementArea"]["winArea"]:
            # 当前区域牌的权值
            cards_weights = 0
            # 出门
            if area == 1:
                cards_weights = chapter['weightsC']
            # 天门
            elif area == 2:
                cards_weights = chapter['weightsT']
            # 末门
            elif area == 3:
                cards_weights = chapter['weightsM']
            for k, v in chapter["playerInRoom"].items():
                if k == banker:
                    continue
                # 如果玩家在这个胜场有下注，收回下注并赢得金币
                stake_number = v["stake"][area]
                if stake_number > 0:
                    DEBUG_MSG("[Room10]::Settlement::id:%s,cards_weights:%s,area:%s" % (k, cards_weights, area))
                    # 如果闲家在此门下过注并且牌型为八叉并且开启八叉规则，赢得的钱翻倍
                    if cards_weights == 9 and self.info['eightXDouble']:
                        win_gold = stake_number * 2
                    else:
                        win_gold = stake_number
                    # 总收益：收回下注的钱+赢得的钱
                    DEBUG_MSG("[Room10]::Settlement::id:%s,win_gold:%s,stake_number%s" % (k, win_gold, stake_number))
                    v["goldChange"] += stake_number + win_gold
                    v['gold'] += stake_number + win_gold
                    chapter["playerInRoom"][banker]["goldChange"] -= win_gold
                    # 庄家失败，减少锅底
                    chapter["potStake"] -= win_gold
        # 结算闲家失败区域
        for area in chapter["settlementArea"]["loseArea"]:
            for k, v in chapter["playerInRoom"].items():
                if k == banker:
                    continue
                # 如果玩家在这个输场有下注,注给庄家
                stake_number = v["stake"][area]
                if stake_number > 0:
                    chapter["playerInRoom"][banker]["goldChange"] += stake_number
                    # 庄家获胜，增加锅底
                    chapter["potStake"] += stake_number
        # 结算平局区域
        for area in chapter["settlementArea"]["drawArea"]:
            for k, v in chapter["playerInRoom"].items():
                if k == banker:
                    continue
                stake_number = v["stake"][area]
                # 如果玩家在这个平局场有下注,收回下注
                if stake_number > 0:
                    v["goldChange"] += stake_number
                    # 修改玩家已有货币
                    v['gold'] += stake_number

        args = {"playerGoldInfo": {}, "winArea": [], "loseArea": [], "drawArea": []}
        # 修改金币
        for k, v in chapter["playerInRoom"].items():
            # 修改玩家金币
            self.set_base_player_game_coin(k)
            DEBUG_MSG("[Room7]::Settlement::id:%s,gold change:%s" % (k, v["goldChange"]))
            v["totalGoldChange"] += v["goldChange"]
            player_gold_info = {"gold": v["gold"], "goldChange": float(v["goldChange"]),
                                'totalGoldChange': v['totalGoldChange'],
                                "stake": {1: v["stake"][1], 2: v["stake"][2], 3: v["stake"][3]}}
            args["playerGoldInfo"][k] = player_gold_info
        args["winArea"] = chapter["settlementArea"]["winArea"]
        args["loseArea"] = chapter["settlementArea"]["loseArea"]
        args["drawArea"] = chapter["settlementArea"]["drawArea"]
        args['potStake'] = chapter['potStake']
        self.callOtherClientsFunction("settlement", args)
        chapter["settlementTime"] = self.addTimer(_timeSettlement, 0, 0)
        chapter["deadline"] = time.time() + _timeSettlement
        self.settlement_count += 1
        if self.settlement_count == 1:
            self.base.cellToBase({'func': 'addTodayRoom'})
        # 持续当庄局数+1
        self.keepBankerCount += 1

        # 如果是AA支付，扣除钻石
        if self.info['payType'] == Const.PayType.AA:
            # 需要扣除钻石的玩家
            need_consume_player = []
            # 如果坐下的玩家有没有扣除过AA支付钻石的，结算时扣除
            for k, v in chapter['playerInGame'].items():
                if not v['AARoomCardConsumed']:
                    need_consume_player.append(v["entity"].info["userId"])
                    v['AARoomCardConsumed'] = True
            # 如果钓鱼的玩家有没有扣除过AA支付钻石的，结算时扣除
            for k, v in chapter['playerOutGame'].items():
                if not v['AARoomCardConsumed']:
                    player_stake = v['stake'][1] + v['stake'][2] + v['stake'][3]
                    if player_stake != 0:
                        need_consume_player.append(v["entity"].info["userId"])
                        v['AARoomCardConsumed'] = True
            if len(need_consume_player) != 0:
                self.base.cellToBase({'func': 'AAPayTypeModifyRoomCard', 'needConsumePlayers': need_consume_player})

    def total_settlement(self):
        """
        总结算
        :return:
        """
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

        # 如果有庄家，返还锅底
        if chapter['banker'] != -1:
            chapter['playerInGame'][chapter['banker']]['gold'] += chapter['potStake']
            chapter['potStake'] = 0

        player_in_room = chapter['playerInRoom']

        # 如果总结算时，本局未结算，返回下注
        if self.settlement_count != self.cn + 1:
            for k, v in player_in_room.items():
                v['gold'] += v['stake'][1] + v['stake'][2] + v['stake'][3]

        # 刷新玩家房间内货币信息
        self.send_all_gold_info()

        player_settlement_info = []
        for k, v in chapter["playerInRoom"].items():
            # 同步货币到房间外
            if self.info["roomType"] == "gameCoin":
                self.set_base_player_game_coin(k)
            else:
                self.set_base_player_gold(k)
            # 记录结算信息
            player_settlement_info.append(
                {"accountId": k, "totalGoldChange": v["totalGoldChange"], "name": v["entity"].info["name"],
                 "overBilling": v["overBilling"], "otherBilling": v["otherBilling"],
                 "winnerBilling": v["winnerBilling"], 'gold': v['gold']})
        # 总局数
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        # 遍历每小局信息
        fishing_man = {}
        for ch in range(0, chapter_record_max_count):
            chapter_info = self.chapters[ch]
            for k, v in chapter_info['playerOutGame'].items():
                if v['stake'][1] + v['stake'][2] + v['stake'][3] == 0:
                    continue
                if k not in fishing_man.keys():
                    fishing_man[k] = {"accountId": k, "totalGoldChange": v["goldChange"],
                                      "name": v["entity"].info["name"], "overBilling": 0, "otherBilling": 0,
                                      "winnerBilling": 0, 'gold': v['gold']}
                else:
                    fishing_man[k]['totalGoldChange'] += v['goldChange']
                    fishing_man[k]['gold'] = v['gold']
        for k, v in fishing_man.items():
            player_settlement_info.append(v)
        args = {"settlementInfo": player_settlement_info}
        self.callOtherClientsFunction("TotalSettlement", args)
        self.base.cellToBase({"func": "totalSettlementEd"})
        # 忽略判断，创建一个房间
        self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info, 'ignoreJudge': True, 'onRoomEnd': True})
        # 茶楼统计局数
        if self.is_tea_house_room and self.settlement_count >= 1:
            self.set_base_player_chapter_count()
        # 总结算清理观战和钓鱼的玩家
        _playerOutGameCopy = chapter["playerOutGame"].copy()
        for k, v in _playerOutGameCopy.items():
            self.kick_out(k)

        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(settlement_clear_players_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_clear_players_time

    def write_chapter_info_to_db(self):
        """
        牌局信息写入库
        :return:
        """
        # 至少打一局才写库
        if self.settlement_count < 1:
            return
        # 每位玩家的总战绩
        player_total_record = {}
        # 每小局的详细战绩
        _history_record = {}
        # 总回放
        replay_data = {}
        # 要记录的局数数量,如果中途解散，当局不记录
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        # 记录战绩的玩家
        record_players = []
        # 统计坐下玩家总战绩
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            # 统计玩家总战绩
            player_total_record[k] = {'accountName': v["entity"].info["name"], 'fishing': False,
                                      "winnerBilling": v["winnerBilling"], "overBilling": v["overBilling"],
                                      "otherBilling": v["otherBilling"], "totalGoldChange": v["totalGoldChange"],
                                      "userId": v["entity"].info["userId"]}
            record_players.append(v["entity"].info["userId"])

        # 遍历每小局的信息
        for c in range(0, chapter_record_max_count):
            chapter_info = self.chapters[c]
            chapter_data = []
            # 统计小局回放基本信息
            single_replay = {"playerInfo": {}, "potStake": chapter_info["potStake"], "banker": chapter_info["banker"],
                             'cardsC': chapter_info['cardsC'], 'cardsM': chapter_info['cardsM'],
                             'cardsT': chapter_info['cardsT'], 'cardsZ': chapter_info['cardsZ'],
                             'weightsZ': chapter_info['weightsZ'], 'weightsM': chapter_info['weightsM'],
                             'weightsC': chapter_info['weightsC'], 'weightsT': chapter_info['weightsT'],
                             'resultC': chapter_info['resultC'], 'resultM': chapter_info['resultM'],
                             'resultT': chapter_info['resultT']}

            for k, v in chapter_info["playerInGame"].items():
                # 统计玩家小局战绩
                player_data = {"goldChange": v["goldChange"], "name": v["entity"].info["name"], 'fishing': False,
                               'totalGoldChange': v['totalGoldChange']}
                chapter_data.append(player_data)

                # 统计玩家回放信息
                single_replay['playerInfo'][k] = {"accountId": k, "accountName": v["entity"].info["name"],
                                                  "stake": v["stake"], "dataBaseId": v["entity"].info["dataBaseId"],
                                                  "locationIndex": int(v["locationIndex"]), "gold": v["gold"],
                                                  'fishing': False, "goldChange": v["goldChange"],
                                                  "userId": v["entity"].info["userId"]}

            for k, v in chapter_info['playerOutGame'].items():
                # 只统计钓鱼玩家
                if v['stake'][1] + v['stake'][2] + v['stake'][3] == 0:
                    continue
                # 统计玩家小局战绩
                player_data = {"goldChange": v["goldChange"], "name": v["entity"].info["name"], 'fishing': True,
                               'totalGoldChange': v['totalGoldChange']}
                chapter_data.append(player_data)
                # 统计玩家总战绩
                player_total_record[k] = {'accountName': v["entity"].info["name"], 'fishing': True,
                                          "winnerBilling": v["winnerBilling"], "overBilling": v["overBilling"],
                                          "otherBilling": v["otherBilling"], "totalGoldChange": v["totalGoldChange"],
                                          "userId": v["entity"].info["userId"]}
                # 统计玩家回放信息
                single_replay['playerInfo'][k] = {"accountId": k, "accountName": v["entity"].info["name"],
                                                  "stake": v["stake"], "dataBaseId": v["entity"].info["dataBaseId"],
                                                  "locationIndex": int(v["locationIndex"]), "gold": v["gold"],
                                                  'fishing': True, "goldChange": v["goldChange"],
                                                  "userId": v["entity"].info["userId"]}
            # 存储小局战绩
            _history_record[c] = chapter_data
            replay_data[c] = single_replay
        _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                 "maxChapterCount": self.info["maxChapterCount"], "playerInfo": player_total_record,
                 "historyRecord": _history_record}
        self._chapterInfos = _args
        self.base.cellToBase({"func": "writeChapterInfo", "chapterInfos": self._chapterInfos})
        # 回放存储玩家信息
        self.chapter_replay = {'chapterInfo': replay_data}
        self.base.cellToBase({"func": "writeChapterReplay", "chapterReplay": self.chapter_replay})
        DEBUG_MSG('[Room id %i]------>writeChapterInfoToDB, _chapterInfos %s ' % (self.id, self._chapterInfos))
        if self.is_tea_house_room:
            # 通知base的冠名赛记录该房间
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

    def get_location_with_account_id(self, account_id):
        """
        通过位置获取 id
        :param account_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        return chapter["playerInGame"][account_id]["locationIndex"]

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
        if timerHandle == chapter["mainTimerId"]:
            all_ready = True
            for k, v in chapter["playerInGame"].items():
                if not v["ready"]:
                    all_ready = False
                    break
            if all_ready and len(chapter["playerInGame"]) >= 2:
                self.delTimer(chapter["mainTimerId"])
                chapter["mainTimerId"] = -1
                self.chapter_start()
        elif timerHandle == chapter["bankerTimerId"]:
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
            # 加锅底
            self.add_gold_to_pot(banker, self.info['potBase'])
            self.send_banker_result(banker)
            # 开启选择庄家动画计时器
            chapter["choiceBankerTime"] = self.addTimer(choice_banker_time, 0, 0)
            chapter["deadline"] = time.time() + choice_banker_time
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
        elif timerHandle == chapter['switchBankerTime']:
            # 切庄倒计时
            DEBUG_MSG('[Room id %s]------>onTimer switchBankerTime %s' % (self.id, timerHandle))
            chapter["switchBankerTime"] = -1
            self.delTimer(chapter["switchBankerTime"])
            # 默认切庄
            self.switch_banker(chapter['banker'], True)
        elif timerHandle == chapter['receiveBankerTime']:
            chapter["receiveBankerTime"] = -1
            self.delTimer(chapter["receiveBankerTime"])
            # 判断是否够锅底
            current_banker_operate_player = chapter['playerInGame'][chapter['currentBankerOperatePlayer']]
            if current_banker_operate_player['gold'] >= self.info['potBase']:
                self.receive_banker(chapter['currentBankerOperatePlayer'], True)
            elif not self.have_gold_limit():
                self.receive_banker(chapter['currentBankerOperatePlayer'], True)
            else:
                self.receive_banker(chapter['currentBankerOperatePlayer'], False)

        elif timerHandle == chapter["stakeTime"]:
            # 押注计时器
            DEBUG_MSG('[Room id %s]------>onTimer stakeTime %s' % (self.id, timerHandle))
            chapter["stakeTime"] = -1
            self.delTimer(timerHandle)
            self.changeChapterState(3)
        elif timerHandle == chapter['dealCardsTime']:
            # 发牌
            DEBUG_MSG('[Room id %s]------>onTimer dealCardsTime %s' % (self.id, timerHandle))
            chapter["dealCardsTime"] = -1
            self.delTimer(timerHandle)
            self.changeChapterState(4)
        elif timerHandle == chapter['matchCardTime']:
            DEBUG_MSG('[Room id %s]------>onTimer matchCardTime %s' % (self.id, timerHandle))
            chapter["matchCardTime"] = -1
            self.delTimer(timerHandle)
            self.changeChapterState(5)
        elif timerHandle == chapter["compareCardTime"]:
            DEBUG_MSG('[Room id %s]------>onTimer compareCardTime %s' % (self.id, timerHandle))
            chapter["compareCardTime"] = -1
            self.delTimer(timerHandle)
            self.changeChapterState(6)
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
            # 清理观战的玩家
            _playerOutGameCopy = chapter["playerOutGame"].copy()
            for k, v in _playerOutGameCopy.items():
                self.kick_out(k)
            # 清理坐下的玩家
            _playerInGameCopy = chapter["playerInGame"].copy()
            for k, v in _playerInGameCopy.items():
                self.kick_out(k)

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
        # 继承锅底
        _newChapter["potStake"] = _chapter["potStake"]
        # # 如果是加锅牌九，用上局的庄家
        # # if self.info["pot"]:
        _newChapter["banker"] = _chapter["banker"]
        _newChapter["bankerIndex"] = _chapter["bankerIndex"]
        for k, v in _newChapter["playerInRoom"].items():
            v["stake"] = {0: 0, 1: 0, 2: 0, 3: 0}
            v["grabBanker"] = -1
            # 本局金币变化
            v["goldChange"] = 0
            # 准备
            v["ready"] = False
            # 接庄
            v['receiveBanker'] = False

    def close_all_timer(self):
        """
        关闭所有计时器
        :return:
        """
        chapter = self.chapters[self.cn]
        chapter["mainTimerId"] = -1
        self.delTimer(chapter["mainTimerId"])
        chapter["choiceBankerTime"] = -1
        self.delTimer(chapter["choiceBankerTime"])
        chapter["switchBankerTime"] = -1
        self.delTimer(chapter["switchBankerTime"])
        chapter["receiveBankerTime"] = -1
        self.delTimer(chapter["receiveBankerTime"])
        chapter["bankerTimerId"] = -1
        self.delTimer(chapter["bankerTimerId"])
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
            self.ret_player_in_room_info()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        if accountEntityId in _playerOutGame:
            _player = _playerOutGame[accountEntityId]
            _playerOutGame.pop(accountEntityId)
            _playerInRoom.pop(accountEntityId)
            self.callClientFunction(accountEntityId, "LeaveRoomResult", {"result": "比赛已结束", "inviteRoomInfo": None})
            _player["entity"].destroySelf()
            self.ret_player_in_room_info()
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 从实体列表中移除
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
            DEBUG_MSG("onLeave account_entities:%s" % self.accountEntities)
        self.autoDestroy()

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
            _player = _playerInGame[accountEntityId]
            # 从坐下玩家中移除
            _playerInGame.pop(accountEntityId)
            # 从房间中移除
            _playerInRoom.pop(accountEntityId)
            # 获取玩家座位
            _locationIndex = _player["locationIndex"]
            # 归还座位
            if _locationIndex not in self.emptyLocationIndex:
                self.emptyLocationIndex.append(_locationIndex)
                self.emptyLocationIndex.sort()
            # 通知客户端
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
            # 销毁 cell 端
            _player["entity"].destroySelf()
            # 发送玩家信息
            self.ret_player_in_room_info()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (len(_playerInGame)))
            # 通知 base 玩家数
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        if accountEntityId in _playerOutGame:
            _player = _playerOutGame[accountEntityId]
            #
            player_stake = _player['stake'][1] + _player['stake'][2] + _player['stake'][3]
            DEBUG_MSG('fishing leave stake:%s' % _player['stake'])
            if player_stake != 0:
                self.callClientFunction(accountEntityId, 'Notice', ['离开失败，请等待本局结算'])
                return
            # 从观战玩家中移除
            _playerOutGame.pop(accountEntityId)
            # 从房间中移除
            _playerInRoom.pop(accountEntityId)
            # 通知客户端
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
            # 销毁 cell 端
            _player["entity"].destroySelf()
            # 有观战玩家离开
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.ret_out_game_player_info(k)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.ret_out_game_player_info(k)
            # 通知 base 玩家数
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        # 从实体列表中移除
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
            DEBUG_MSG("onLeave account_entities:%s" % self.accountEntities)
        self.autoDestroy()

    def get_next_location_index(self, location_index):
        """
        获取下个位置
        :param location_index:
        :return:
        """
        current = location_index
        return (current + 1) % self.info["maxPlayersCount"]

    def get_next_player_id_by_account_id(self, account_id):
        """
        通过id寻找下一个玩家
        :param account_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        start_location = chapter['playerInGame'][account_id]['locationIndex']
        for i in range(0, self.info["maxPlayersCount"]):
            # 获取下个位置
            next_player = self.get_next_location_index(start_location)
            for k, v in chapter["playerInGame"].items():
                if v["locationIndex"] == next_player:
                    return k
            start_location = next_player
        return -1

    def reconnect(self, accountId):
        """
        请求重连
        :param accountId: 重连玩家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>reconnect %s' % (self.id, accountId))
        chapter = self.chapters[self.cn]
        self.retRoomBaseInfo(accountId)
        # 玩家信息
        self.ret_player_in_room_info(accountId)
        # 房间信息
        self.ret_chapter_info(accountId)

    def ret_chapter_info(self, accountId):
        chapter = self.chapters[self.cn]
        play_in_room = chapter["playerInRoom"]
        chapter_info = {'currentRound': int(chapter['currentRound']), 'currentState': int(chapter['currentState']),
                        'deadline': int(chapter['deadline']) - int(time.time()), 'banker': int(chapter['banker']),
                        'bankerIndex': int(chapter['bankerIndex']), 'stake': chapter['stake'],
                        'cardsZ': chapter['cardsZ'], 'cardsC': chapter['cardsC'], 'cardsT': chapter['cardsT'],
                        'cardsM': chapter['cardsM'], 'settlementArea': chapter['settlementArea'],
                        'resultT': chapter['resultT'], 'resultC': chapter['resultC'], 'resultM': chapter['resultM'],
                        'started': self.started, 'potStake': chapter['potStake'],
                        'currentBankerOperatePlayer': chapter['currentBankerOperatePlayer'],
                        'disbandSender': self.disband_sender,
                        'teaHouseId': self.info['teaHouseId'] if 'teaHouseId' in self.info.keys() else -1,
                        'isDisbanding': self.is_disbanding, 'weightsT': chapter['weightsT'],
                        'weightsM': chapter['weightsM'], 'weightsC': chapter['weightsC'],
                        'weightsZ': chapter['weightsZ']}
        if len(self.chapters) > 1:
            chapter_info['preBanker'] = self.chapters[self.cn - 1]['banker']
        _playerData = {}
        for k, v in play_in_room.items():
            _playerData[k] = {'goldChange': v['goldChange'], 'name': v['entity'].info['name'],
                              'totalGoldChange': v['totalGoldChange'], 'ready': v['ready'],
                              'locationIndex': v['locationIndex'], 'stake': v['stake'], 'grabBanker': v['grabBanker'],
                              'gold': v['gold'], 'agreeDisband': v['agreeDisband']}
        chapter_info['playerData'] = _playerData
        self.callClientFunction(accountId, 'Reconnect', chapter_info)

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

        # 如果房间,没结算总结算
        if not self.total_settlement_ed:
            self.total_settlement()
            self.write_chapter_info_to_db()
