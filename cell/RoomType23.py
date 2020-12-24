# -*- coding: utf-8 -*-
import copy
import datetime
import random
from random import shuffle

import RoomType23Calculator
from RoomBase import *
import json
import time
import ZJHCalculator
import Account

# 准备倒计时时间
ready_time = 5
# 发牌动画时间
deal_card_to_player_time = 3
# 抢庄时间
grab_banker_time = 5
# 押注倒计时时间
stake_time = 20
# 要牌时间
get_card_time = 10
# 结算时间
settlement_time = 6
# 解散房间倒计时
time_disband = 30
# 总结算清理玩家倒计时
settlement_clear_players_time = 30


class RoomType23(RoomBase):
    # 1 牌局信息
    _chapterInfos = {}
    # 1 外挂玩家
    waiGuaPlayer = None
    # 游戏中最大玩家数量
    emptyLocationIndex = []

    # 可以点击开始的玩家
    # can_start_player = -1

    def __init__(self):
        RoomBase.__init__(self)
        # 游戏玩家
        self.player_list = []
        # 观战中的下局可以开始坐下的玩家
        self.wait_to_seat = []

        self.player_leave_info = []

    def newStatisticalData(self):
        self.emptyLocationIndex = list(range(0, self.info["maxPlayersCount"]))

    def newChapter(self, maxPlayerCount):
        """
        新牌局
        :param maxPlayerCount:
        :return:
        """
        _chapter = dict()
        # 是否授权买入
        _chapter["hasAnthorizeBuying"] = self.info["hasAnthorizeBuying"]
        # 最大局数
        _chapter["maxRound"] = self.info["maxRound"]
        # 房间时间
        _chapter["roomTime"] = self.info["roomTime"]
        # 创建房间时刻
        _chapter["createRoomTime"] = self.info["createRoomTime"]
        # 清除玩家倒计时
        _chapter["settlementClearPlayers"] = -1
        # 房间玩家数量
        _chapter["playersCount"] = 0
        # 最大玩家数量
        _chapter["maxPlayerCount"] = maxPlayerCount
        # 当前轮数
        _chapter["currentRound"] = 0
        # 当前房间状态
        _chapter["currentState"] = 0
        # 当前操作玩家位置
        _chapter["currentLocationIndex"] = -1
        # 房间总注
        _chapter["totalBet"] = 0
        # 轮询是否可以开始牌局计时器
        _chapter["mainTimerId"] = -1
        # 牌局开始倒计时计时器
        _chapter["chapterStartTimerId"] = 0
        # 下注计时器
        _chapter["operateTimerId"] = -1
        # 下注动画计时器
        _chapter["betAnimationTimerId"] = -1
        # 结算计时器
        _chapter["settlementTimerId"] = -1
        # 结算到总结算倒计时
        _chapter['toToTalSettlementTime'] = -1
        # 位置交换计时器
        _chapter["seatAnimationTimerId"] = -1
        # 比牌动画计时器
        _chapter["compareCardTimerId"] = -1
        # 当前计时时刻点
        _chapter["deadline"] = -1
        # 游戏内玩家
        _chapter["playerInGame"] = {}
        # 游戏外玩家
        _chapter["playerOutGame"] = {}
        # 房间内所有玩家
        _chapter["playerInRoom"] = {}
        # 房间内坐下但是没有参与牌局的玩家（针对金币场）
        _chapter["playerInSeatNotGame"] = dict()
        # 牌库
        _chapter["cardsLib"] = []
        # 庄家id
        _chapter["banker"] = -1
        # 开始玩家下标
        _chapter["startLocationIndex"] = -1
        # 开始玩家Id
        _chapter["startAccountId"] = -1
        # 抽奖
        _chapter["accountLottery"] = -1
        # 操作数据
        _chapter["operationRecord"] = []
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
        _locationIndex = -1
        _player = dict()
        # 实体
        _player["entity"] = accountEntity
        # 准备状态
        _player["isReady"] = False
        # 牌
        _player["cards"] = []
        # 房间类型  card gameCoin normalGameCoin
        if self.info["roomType"] == "card":
            _player["score"] = accountEntity.accountMutableInfo["gold"]
        elif self.info["roomType"] == "gameCoin":
            # 比赛分场修改使用比赛分为使用金币
            _player["score"] = accountEntity.accountMutableInfo["gold"]
        elif self.info["roomType"] == "normalGameCoin":
            _player["score"] = accountEntity.accountMutableInfo["gold"]
        # 总带入
        _player["totalScore"] = 0
        # 总金币变化
        _player["totalGoldChange"] = 0
        # 玩家下注的列表
        _player["betList"] = []
        # 下注总额
        _player["totalBet"] = 0
        # 玩家位置信息
        _player["locationIndex"] = _locationIndex
        # 大赢家扣费
        _player["winnerBilling"] = 0
        # 其余玩家扣费
        _player["otherBilling"] = 0
        # 超额扣费
        _player["overBilling"] = 0
        # 同意解散房间
        _player["agreeDisband"] = False
        # 玩家在线状态
        _player["online"] = True
        # 是否已经扣除过AA支付的钻石
        _player['AARoomCardConsumed'] = False
        return _player

    def chapterRestart(self):
        """
        重新开始下一局
        :return:
        """
        # if self.info["roomType"] == "gold":
        #     self.check_gold()
        self.debug_msg('[Room id %i]------>chapterRestart ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]  # 在游戏中的玩家
        _playerInRoom = _chapter["playerInRoom"]  # 在房间中的玩家
        _playerOutGame = _chapter["playerOutGame"]  # 在游戏中观战的玩家
        _newChapter = self.newChapter(_chapter["maxPlayerCount"])  # 游戏中最大的玩家人数
        if self.cn >= int(self.info["maxChapterCount"]):
            self.total_settlement()
            self.write_chapter_info_to_db()
            return
        # 使用 deepcopy 避免每局战绩的玩家赢钱数相同
        _newChapter["playerInGame"] = copy.deepcopy(_playerInGame)
        _newChapter["playerOutGame"] = copy.deepcopy(_playerOutGame)
        _newChapter["playerInRoom"].update(_newChapter["playerInGame"])
        _newChapter["playerInRoom"].update(_newChapter["playerOutGame"])
        for k, v in _newChapter["playerInRoom"].items():  # 遍历在房间中玩家
            v["cards"] = []  # 牌
            v["totalBet"] = 0  # 下注总额
            v["isReady"] = False  # 准备状态
            v["betList"] = []  # 玩家下注的列表

    def chapter_start(self):
        """
        牌局开始
        :return:
        """
        self.debug_msg('[Room id %i]------>chapterStart ' % self.id)
        self.started = True
        self.info["started"] = True
        chapter = self.chapters[self.cn]
        _playerInGame = chapter["playerInGame"]
        # 金币场扣除房费
        # if self.is_gold_session_room():
        #     for k, v in _playerInGame.items():
        #         v['gold'] -= self.info['roomRate']
        #         self.set_base_player_gold(k)
        # 1 通知base游戏开始
        if self.cn == 0:
            # 将坐下玩家的数据库ID传入前台
            player_in_game_db_id = []
            for k, v in self.chapters[self.cn]["playerInGame"].items():
                player_in_game_db_id.append(v["entity"].info["dataBaseId"])
                self.player_entity(v).update_player_stage(Account.PlayerStage.PLAYING, self.max_chapter_count,
                                                          self.current_chapter_count)
            self.notify_viewing_hall_players_chapter_start()
            self.base.cellToBase({"func": "roomStart", "roomInfo": self.info, "playerInGameDBID": player_in_game_db_id})
            # 房间开始，并且人未满时创建新的房间(onRoomEnd为true时插入在当前房间后面)
            if len(chapter['playerInGame']) < self.info['maxPlayersCount'] and self.info["roomType"] != "challenge":
                self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})

        self.changeChapterState(1)
        self.set_current_round(self.cn + 1)
        self.base.cellToBase({"func": "changeRoomState", "roomState": 1})
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

    def chapterReady(self):
        """
        牌局准备
        :return:
        """

        self.debug_msg('[Room id %i]------>chapterReady ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        # 玩家掉线，让其退出房间
        _playerInRoomCopy = _playerInRoom.copy()
        for k, v in _playerInRoomCopy.items():
            # 如果玩家不在线
            if v["entity"].client_death is True:  # TODO client_death 玩家在线状态 [False在线]    [True不在线]
                # 离开房间
                self.onLeave(v["entity"].id)
        self.debug_msg('?????????????%s' % self.info["winnerRaffleInterval"])
        self.debug_msg('?????????????%s' % self.info["winnerBilling"])

    def randomSetSeat(self):
        """
        随机给玩家设置座位
        :return:
        """
        _chapter = self.chapters[self.cn]
        # 获取在游戏中的玩家
        _playerInGame = _chapter["playerInGame"]
        _list = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        # 1 从列表中随机取出len(_playerInGame)个数，以列表返回
        _seats = random.sample(_list, len(_playerInGame))
        _i = -1
        for k, v in _playerInGame.items():
            _i = _i + 1
            # 设置座位
            # k: 设置座位玩家(accountId)
            # _seats[_i]: 座位号0-8(locationIndex)
            self.setSeat(k, _seats[_i])

    def change_operation(self):
        """
        移交操作权限
        :return:
        """
        self.debug_msg('[Room id %i]------>changeOperation ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        # 1 当前操作玩家位置
        _currentLocationIndex = int(_chapter["currentLocationIndex"])
        _startLocationIndex = int(_chapter["startLocationIndex"])
        _locationIndexs = {}
        for k, v in _playerInGame.items():
            _locationIndexs[int(v["locationIndex"])] = v
        _nextLocationIndex = _currentLocationIndex + 1
        max_player_count = _chapter["maxPlayerCount"]
        max_player_count *= 10
        for i in range(max_player_count):
            if _nextLocationIndex >= _chapter["maxPlayerCount"]:
                _nextLocationIndex %= _chapter["maxPlayerCount"]
            if _nextLocationIndex in _locationIndexs.keys():
                if _nextLocationIndex == _startLocationIndex:
                    _currentRound = _chapter["currentRound"] + 1
                    # 判断是否大于房间最大局数,大于最大局数的时候返回
                    _hasNext = self.setCurrentRound(_currentRound)
                    if not _hasNext:
                        self.debug_msg("_currentRound=%s, maxCount=%s" % (_currentRound, self.info["maxRound"]))
                        return
            _nextLocationIndex += 1
            self.debug_msg("startLocationIndex:%s" % _startLocationIndex)
            self.debug_msg("_nextLocationIndex:%s" % _nextLocationIndex)

        for k, v in _playerInGame.items():
            self.debug_msg("locationIndex = %s" % v["locationIndex"])
            if int(v["locationIndex"]) == int(_nextLocationIndex):
                # 1 设置当前操作玩家位置
                self.set_current_location_index(_nextLocationIndex, k)

    def dealCards(self):
        """
        发牌
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        # 1 找到庄家
        _banker = _playerInGame[_chapter["banker"]]
        # 1 庄家先发牌
        _startLocationIndex = int(_banker["locationIndex"])
        _maxPlayerCount = int(_chapter["maxPlayerCount"])
        # 1 牌的列表
        _dealCardList = []
        # 1 给发牌的玩家
        _dealCardPlayers = []
        # 洗牌
        self.random_shuffle_cards_lib()
        # 排序, 从庄家开始发牌
        for i in range(_startLocationIndex, _startLocationIndex + _maxPlayerCount):
            if i >= _maxPlayerCount:
                i %= _maxPlayerCount
            _dealCardList.append(i)
        for k, v in _playerInGame.items():
            if int(v["locationIndex"]) in _dealCardList:
                _dealCardPlayers.append(k)

        # 分牌
        all_cards = []
        for k in _dealCardPlayers:
            _cards = []
            for i in range(0, 3):
                _cards.append(self.randomCardFromLib())
            all_cards.append(_cards)

        # 有人输的太多的话，需要发好牌
        is_in_rand_range = self.is_need_rand_score_control("RoomType23")
        luck_player = None
        if is_in_rand_range:
            luck_player = self.select_max_loser(_playerInGame.values())
            # if luck_player:
            #     self.callClientFunction(luck_player['entity'].id, 'Notice', ['发好牌'])

        if not luck_player:
            # 找连输超过5局的最大连输玩家
            luck_player, max_losing_streak_count = self.get_max_losing_streak_player(_playerInGame.values())
            if max_losing_streak_count < 5:
                luck_player = None
            self.debug_msg(
                '最大连输 %s %s' % (max_losing_streak_count, luck_player['entity'].id if luck_player else luck_player))

            # 60%概率发
            rand_num = random.randint(1, 100)
            if rand_num > 60:
                luck_player = None

        # if not luck_player:
        #     # 幸运数字玩家
        #     is_in_rand_range = self.is_need_rand_score_control("RoomType23")
        #     if is_in_rand_range:
        #         luck_player = self.select_luck_max_loser(_playerInGame.values())

        # 每日发好牌次数控制
        # TODO select_day_good_pai_player 每日发好牌, 选择需要发好牌的玩家，随机选择
        day_player = self.select_day_good_pai_player(_playerInGame.values(), 2)
        if day_player:
            luck_player = day_player
            self.player_entity(luck_player).increase_day_pai_control_count()

        # 给幸运玩家发好牌
        have_pai_player_id = -1
        if luck_player:
            # 获取好牌
            good_card_index = RoomType23Calculator.get_good_pai(all_cards, self.info)
            if good_card_index >= 0:
                luck_player["cards"] = all_cards[good_card_index]
                del all_cards[good_card_index]
                have_pai_player_id = luck_player['entity'].id
                self.debug_msg('good pai player id: %s cards: %s' % (have_pai_player_id, luck_player["cards"]))

        # 给其他人发牌
        for k in _dealCardPlayers:
            if _playerInGame[k]['entity'].id == have_pai_player_id:
                continue
            _playerInGame[k]["cards"] = all_cards[0]
            del all_cards[0]

        # 1 如果是外挂玩家
        if self.waiGuaPlayer:
            _maxCards = [4, 10, 19]
            _maxAccountId = -1
            for k, v in _playerInGame.items():
                if RoomType23Calculator.compare_card(v["cards"], _maxCards, self.info) == 1:
                    _maxCards = v["cards"]
                    _maxAccountId = k
            _playerInGame[_maxAccountId]["cards"] = _playerInGame[self.waiGuaPlayer]["cards"]
            _playerInGame[self.waiGuaPlayer]["cards"] = _maxCards
            self.waiGuaPlayer = None

        _dealCardsDic = []
        for k, v in _playerInGame.items():
            _playData = {"accountId": int(k), "cards": v["cards"]}
            _dealCardsDic.append(_playData)
        self.callOtherClientsFunction("DealCards", _dealCardsDic)

    def random_shuffle_cards_lib(self):
        """
        洗牌
        """
        _chapter = self.chapters[self.cn]
        cards = _chapter["cardsLib"]
        shuffle(cards)
        shuffle(cards)
        for i in range(8):
            self.__gj_pai_rand(cards)
        self.debug_msg("len %s,chapter lib%s" % (len(cards), cards))

    def __gj_pai_rand(self, _chapter_lib):
        """
        牌随机，根据时间值，前X张牌,放在最后
        :param _chapter_lib:
        :return:
        """
        #  取当前时间
        msval = datetime.datetime.now().microsecond
        if msval > 1000:
            msval //= 1000
        pai_val = (msval % 10) + 10

        pull_pais = _chapter_lib[:pai_val]
        del _chapter_lib[:pai_val]
        _chapter_lib.extend(pull_pais)

    def set_current_location_index(self, currentLocationIndex, accountId):
        """
        设置当前操作玩家
        :param currentLocationIndex: 当前操作玩家下标
        :param accountId: 当前操作玩家id
        :return:
        """
        self.debug_msg('[Room id %i]------>setCurrentLocationIndex ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _player = _playerInGame[accountId]
        _chapter["currentLocationIndex"] = currentLocationIndex
        _args = {}
        _chapter["operateTimerId"] = self.addTimer(self.time_down, 0, 0)
        _chapter["deadline"] = int(time.time()) + self.time_down
        self.callOtherClientsFunction("ChangeOperation", _args)

    def setCurrentRound(self, currentRound):
        """
        设置当前轮数
        :param currentRound:
        :return:
        """
        self.debug_msg('[Room id %i]------>setCurrentRound currentRound %s' % (self.id, currentRound))
        _chapter = self.chapters[self.cn]
        if _chapter["maxRound"] - currentRound == 1:  # maxRound 最大局数
            self.callOtherClientsFunction("Notice", ["两轮下注后系统自动比牌"])
        # 1 当前轮数大于牌局最大轮数
        if currentRound > _chapter["maxRound"]:  # maxRound 最大局数
            # 1 获取未弃牌玩家
            _playerHasNoDisCard = self.getHasNoDisCardPlayer()
            _playerHasNoDisCardKeys = list(_playerHasNoDisCard.keys())
            _length = len(_playerHasNoDisCardKeys)
            _maxAccountId = _playerHasNoDisCardKeys[0]
        _chapter["currentRound"] = currentRound
        _args = {"currentRound": _chapter["currentRound"]}
        self.callOtherClientsFunction("RetCurrentRound", _args)
        return True

    def setBanker(self):
        """
        定庄,随机一个庄家
        :return:
        """
        self.debug_msg('[Room id %i]------>setBanker ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]  # 游戏中玩家
        # 1 从在游戏中玩家随机生成一个玩家为庄家   sample生成的是一个列表
        banker_id = self.banker_area_random(list(_chapter["playerInGame"].keys()))
        _banker = [banker_id]
        # _banker = random.sample(_chapter["playerInGame"].keys(), 1)
        # 1 设置庄家为牌局的当前操作玩家
        _chapter["currentLocationIndex"] = _playerInGame[_banker[0]]["locationIndex"]
        _locationIndexs = {}
        # 1 循环游戏中的玩家
        for k, v in _playerInGame.items():
            _locationIndexs[int(v["locationIndex"])] = v
        # 1 开始的玩家的下标
        _startLocationIndex = int(_chapter["currentLocationIndex"]) + 1
        max_player_count = _chapter["maxPlayerCount"]
        max_player_count *= 10
        for i in range(max_player_count):
            if _startLocationIndex >= _chapter["maxPlayerCount"]:
                _startLocationIndex %= _chapter["maxPlayerCount"]
            if _startLocationIndex in _locationIndexs.keys():
                break
            _startLocationIndex += 1
        # 1 牌局开始玩家的下标
        _chapter["startLocationIndex"] = _startLocationIndex
        _startAccountId = 0
        for k, v in _playerInGame.items():
            # 1 找到开始玩家把id设置为开始的ID
            if int(v["locationIndex"]) == _startLocationIndex:
                _startAccountId = k
        _chapter["banker"] = _banker[0]
        _chapter["startAccountId"] = _startAccountId
        _args = {"banker": _banker[0], "startLocationIndex": str(_chapter["startLocationIndex"]),
                 "startAccountId": _startAccountId}
        self.callOtherClientsFunction("SetBanker", _args)

    def set_banker_history_in_cell(self, _chapter):
        # _chapter = self.chapters[self.cn]
        # 在游戏中的玩家
        _playerInGame = _chapter["playerInGame"]
        for k, v in _playerInGame.items():
            if k == _chapter["banker"]:
                v['entity'].info['bankerHistory'].append(1)
            else:
                v['entity'].info['bankerHistory'].append(0)

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

    def setSeat(self, accountId, locationIndex):
        """
        设置座位
        :param accountId: 设置座位玩家
        :param locationIndex: 座位号0-8
        :return:
        """
        self.debug_msg('[Room id %i]------>setSeat accountId %s, locationIndex %s ' % (self.id, accountId, locationIndex))
        _chapter = self.chapters[self.cn]
        # 1 不在观战玩家列表中
        if accountId not in _chapter["playerOutGame"]:  # playerOutGame 观战玩家列表
            return
        # 1 循环游戏中的玩家
        for player in _chapter["playerInGame"].values():
            if player["locationIndex"] == locationIndex:
                return
        _chapter["playerInGame"][accountId] = _chapter["playerOutGame"].pop(accountId)
        _chapter["playerInGame"][accountId]["locationIndex"] = locationIndex
        _player = _chapter["playerInGame"][accountId]
        self.retPlayerInRoomInfos()
        # _args = {"accountId": accountId, "locationIndex": int(locationIndex),
        #          "name": _player["entity"].info["name"]}
        self.emptyLocationIndex.remove(locationIndex)
        # self.callOtherClientsFunction("SetSeat", _args)

        # # 从等待坐下中移除
        if accountId in self.wait_to_seat:  # self.wait_to_seat 观战中的下局可以开始坐下的玩家
            self.debug_msg(
                '[Wait_to_seat]------> kickOut playerOutGame setSeat accountId %s' % (accountId))
            self.wait_to_seat.remove(accountId)  # 根据id移除观战中的下局坐下的玩家
        list1 = [2, 4, 5, 6, 7, 8, 9, 10]
        if self.info["gameStartType"] in list1:
            try:
                self.player_list[0] = -1
            except:
                pass
            if len(_chapter["playerInGame"]) >= self.info["gameStartType"]:
                for k, v in _chapter["playerInGame"].items():
                    self.player_ready(k)
            _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
        self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 每人满时，创建新的房间(onRoomEnd为true时插入在当前房间后面)
        if len(_chapter['playerInGame']) == self.info['maxPlayersCount']:
            # 自动创建房间
            self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})

    def player_ready(self, account_id):
        """TODO E玩家准备
        :param account_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        if chapter["currentState"] != 0:
            return
        _player = chapter["playerInGame"][account_id]
        # 如果玩家的币小于底分 return
        # TODO self.have_gold_limit() 根据是否是比赛币场和比赛币开关判断是否有金币限制
        if self.have_gold_limit() and _player["score"] < self.info["betBase"]:
            return
        # 如果小于房费返回
        # TODO self.is_gold_session_room() 是否是金币场房间
        if self.is_gold_session_room() and _player['score'] < self.info['roomRate']:
            return
        _playerInRoom = chapter["playerInRoom"]
        # 判断account_id 在房间
        if account_id in _playerInRoom.keys():
            _playerInRoom[account_id]["isReady"] = True
            # 1 标志位置为True
            _args = {"accountId": account_id, "ready": True}
            # 向客户端发送准备完成
            # 玩家准备完成
            self.callOtherClientsFunction("Ready", _args)

    # 1 玩家点击下局坐下按钮
    def want_next_game_seat(self, account_id):
        """
        玩家点击下局坐下按钮
        :param accountId:
        :return:
        """
        chapter = self.chapters[self.cn]
        # 1 房间中的玩家
        _playerInRoom = chapter["playerInRoom"]
        # 1 游戏中的玩家
        _playerInGame = chapter["playerInGame"]
        # 1 观战中的玩家
        _playerOutGame = chapter["playerOutGame"]
        # 如果玩家id 在 观战玩家中
        if _playerOutGame[account_id]['score'] < self.info['gameLevel']:
            self.callClientFunction(account_id, 'Notice', ['金币不足，无法坐下'])
            return
        if account_id in _playerOutGame:
            # 已经坐下
            if account_id in self.wait_to_seat:  # self.wait_to_seat 观战中的下局可以开始坐下的玩家
                _args = {"result": 1}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                self.callOtherClientsFunction("NextGameCanSit", self.wait_to_seat)
                return
            if len(self.emptyLocationIndex) > len(self.wait_to_seat):
                self.wait_to_seat.append(account_id)
                _args = {"result": 1}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                self.callOtherClientsFunction("NextGameCanSit", self.wait_to_seat)
                self.get_player_entity(account_id).update_player_stage(Account.PlayerStage.PLAYING,
                                                                       self.max_chapter_count,
                                                                       self.current_chapter_count)
            else:
                _args = {"result": 0}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                return

    def standUp(self, accountId, locationIndex):
        """
        站起
        :param accountId: 站起玩家
        :param locationIndex: 座位
        :return:
        """
        self.debug_msg('[Room id %i]------>standUp accountId %s, locationIndex %s ' % (self.id, accountId, locationIndex))
        _chapter = self.chapters[self.cn]
        # 当前房间状态
        if _chapter["currentState"] != 0:
            return
        # 1 如果玩家不在游戏中
        if accountId not in _chapter["playerInGame"]:
            return
        if self.info["roomType"] == "gameCoin":
            # TODO 设置玩家金币数量
            self.set_base_player_game_coin(accountId)
        _chapter["playerOutGame"][accountId] = _chapter["playerInGame"][accountId]
        itemIndex = _chapter["playerInGame"][accountId]["locationIndex"]
        self.debug_msg('[获取站起玩家位置id]------>standUp accountId %s' % locationIndex)
        self.debug_msg('[前端传的玩家位置id]------>standUp accountId %s' % itemIndex)
        _chapter["playerInGame"].pop(accountId)
        _args = {"accountId": accountId, "locationIndex": itemIndex}
        self.emptyLocationIndex.append(itemIndex)
        self.callOtherClientsFunction("StandUp", _args)

    def addBet(self, accountId, addBetSum):
        """
        加注
        :param accountId: 加注玩家
        :param addBetSum: 加注金额
        :return:
        """
        self.debug_msg('[Room id %i]------>addBet accountId %s, addBetSum %s ' % (self.id, accountId, addBetSum))
        _chapter = self.chapters[self.cn]
        _player = _chapter["playerInGame"][accountId]
        if int(_player['locationIndex']) != int(_chapter["currentLocationIndex"]):
            return
        if self.have_gold_limit() and addBetSum > _player["score"] - _player["totalBet"]:
            self.callClientFunction(accountId, "Notice", ["%s不足,请继续带入" % self.gold_name])
            self.callClientFunction(accountId, "AddBetCallBack", ["0"])
            return False
        # 1 关闭下注计时器
        self.delTimer(_chapter["operateTimerId"])
        _chapter["operateTimerId"] = -1
        # 1 牌局总加注
        # _chapter["totalBet"] += _bet
        _player["betList"].append(addBetSum)
        # 1 玩家总加注
        # _player["totalBet"] += _bet
        _args = {"accountId": accountId, "betSum": addBetSum, "chapterTotalBet": _chapter["totalBet"],
                 "playerTotalBet": _player["totalBet"], "gold": _player["score"] - _player["totalBet"]}
        self.callOtherClientsFunction("AddBet", _args)
        self.callClientFunction(accountId, "AddBetCallBack", ["1"])
        # 记录出牌步骤
        record = {}
        record["accountId"] = accountId
        # 相关类型置为 2
        record["operationType"] = 2
        # 操作  存储玩家加注金额
        record["operationArgs"] = {"addBetSum": addBetSum}
        _chapter["operationRecord"].append(record)
        self.change_operation()

    def drop_bet(self, accountId, betSum):
        """
        下注
        :param accountId: 下注玩家
        :param betSum: 下注金额
        :return:
        """
        self.debug_msg('[Room id %i]------>drapBet accountId %s, betSum %s ' % (self.id, accountId, betSum))
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _player = _playerInGame[accountId]
        # 1 下注金额大于玩家的钱减去加注的钱
        self.debug_msg('betSum-----------------------%s ' % str(betSum))
        self.debug_msg('_player["score"]-----------------------%s ' % str(_player["score"]))
        self.debug_msg('_player["totalBet"]-----------------------%s ' % str(_player["totalBet"]))
        self.debug_msg(_player)
        if self.have_gold_limit() and betSum > _player["score"] - _player["totalBet"]:
            # 带入比赛分
            self.callClientFunction(accountId, "Notice", ["%s不足,请继续带入" % self.gold_name])
            self.callClientFunction(accountId, "BetCallBack", ["0"])
            return False
        self.delTimer(_chapter["operateTimerId"])
        _chapter["operateTimerId"] = -1
        _chapter["totalBet"] += betSum
        # 1 将玩家每次下注的的数量加入到这个列表中
        _player["betList"].append(betSum)
        # 1 玩家总下注的数量
        _player["totalBet"] += betSum
        _args = {"accountId": accountId, "betSum": betSum, "chapterTotalBet": _chapter["totalBet"],
                 "playerTotalBet": _player["totalBet"], "gold": _player["score"] - _player["totalBet"]}
        self.callOtherClientsFunction("BetResult", _args)
        self.callClientFunction(accountId, "BetCallBack", ["1"])
        # 记录出牌步骤
        record = {}
        record["accountId"] = accountId
        # 相关类型置为 1
        record["operationType"] = 1
        # 操作  存储玩家跟注金额
        record["operationArgs"] = {"betSum": betSum}
        _chapter["operationRecord"].append(record)
        return True


    def settlement(self):
        """
        结算
        :return:
        """
        self.debug_msg('[Room id %i]------>settlement ' % self.id)
        # self.close_all_timer()
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _winer = self.getHasNoDisCardPlayer()

        # 设置连输记录
        for k, v in _playerInGame.items():
            if k in _winer:
                self.set_losing_streak_history(v, False)
            else:
                self.set_losing_streak_history(v, True)

        # 1 牌局总下注
        _chapterTotalBet = _chapter["totalBet"]
        for k, v in _winer.items():
            # self.debug_msg('[Room id %i]------>settlement totalBet:%s chapterTotalBet%s cutRatio%s' % (
            #     self.id, v["totalBet"], _chapterTotalBet, self.cutRatio))
            # 1 胜者的  总下注-牌局总下注  等于负的赢钱的价值
            v["totalBet"] = round(float(v["totalBet"] - _chapterTotalBet), 1)
            # 1 获取到赢家的牌型
            cards = _playerInGame[k]["cards"]
            cards_type = RoomType23Calculator.type_of_cards(cards, self.info) if \
                type(RoomType23Calculator.type_of_cards(cards, self.info)) == float or \
                type(RoomType23Calculator.type_of_cards(cards, self.info)) == int else -1
            self.debug_msg('cardsType -----------------%i' % cards_type)
            # 大赢家的牌型是同花顺
            if cards_type == 99:
                for m, n in _playerInGame.items():
                    if m != k:
                        self.debug_msg('straightXiQian compare player: %i  %i' % (k, m))
                        n["totalBet"] += self.info["straightXiQian"]
                        v["totalBet"] -= self.info["straightXiQian"]
            # 大赢家的牌型是豹子
            if cards_type == 100:
                for m, n in _playerInGame.items():
                    if m != k:
                        self.debug_msg('leopardXiQian compare player: %i  %i' % (k, m))
                        n["totalBet"] += self.info["leopardXiQian"]
                        v["totalBet"] -= self.info["leopardXiQian"]

        if self.info["roomType"] == "gameCoin":
            # 首局结算抽水
            if self.settlement_count == 0:
                for k, _p in _playerInGame.items():
                    if self.get_true_gold(_p['entity'].id) < self.info['billingCount']:
                        self.debug_msg('RoomType23 billing_count not enough account_id:%s' % _p['entity'].id)
                        continue
                    billing_count = self.info['billingCount']
                    _p['score'] -= billing_count
                    self.debug_msg('RoomType23 billing_count account_id:%s,count:%s' % (_p['entity'].id, billing_count))
                    self.base.cellToBase({"func": "extractRoomCostToCreator", "billingCount": billing_count})
            # 每小局结算大赢家抽水,保留整数  E小局抽水
            # 获取大赢家
            settlement_winners = self.jh_get_settlement_winners()
            for location_index, v in settlement_winners.items():
                settlement_winner_account_id = v['entity'].id
                # 计算大赢家小局抽水
                settlement_winner_true_gold = self.jh_get_true_gold(settlement_winner_account_id)
                settlement_winner_billing = settlement_winner_true_gold * self.info['settlementBilling']
                v['totalBet'] = -v["totalBet"] - settlement_winner_billing
                v['totalBet'] = round(float(v['totalBet']), 1) * -1
                v['score'] -= settlement_winner_billing
                v['score'] = round(float(v['score']), 1)
                # 同步房费给base
                self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                      "todayGameCoinAdd": settlement_winner_billing,
                                      "userId": v["entity"].info["userId"],
                                      "roomType": Const.get_name_by_type("RoomType23") + "小局"})
        _args = {}
        _toBaseArgs = dict()
        for k, v in _playerInGame.items():
            cards = _playerInGame[k]["cards"]
            cards_type = 0
            # 1 总金币变化等于 下注总额
            self.debug_msg('goldChange -----------------%i' % v["totalGoldChange"])
            v["totalGoldChange"] += -v["totalBet"]
            _playerData = {"gold": v["score"] - v["totalBet"], "goldChange": -v["totalBet"], "cards": v["cards"],
                           'totalGoldChange': v['totalGoldChange'],
                           "type": cards_type}
            _args[k] = _playerData
            v["score"] = v["score"] - v["totalBet"]
            _userId = v["entity"].info["userId"]
            _toBaseArgs[_userId] = {"goldChange": -v["totalBet"]}
        _chapterData = {}
        for k, v in _playerInGame.items():
            _playerData = {"accountName": v["entity"].info["name"], "cards": v["cards"], "goldChange": -v["totalBet"],
                           "cardType": ZJHCalculator.calculatorCard(v["cards"]),
                           "headImageUrl": v["entity"].info["headImageUrl"]}
            _chapterData[k] = _playerData
            # 更新分数控制
            v["entity"].update_score_control(-v['totalBet'])

        # 金币场结算后检测玩家的金币数是否为零
        if self.info["roomType"] == "gold":
            self.check_gold()
            pass
        else:
            item = 0
            for k, v in _playerInGame.items():
                if v["score"] <= 0:
                    self.player_leave_info.append(
                        {"accountId": k, "totalGoldChange": v["totalGoldChange"], "name": v["entity"].info["name"],
                         "overBilling": v["overBilling"], "otherBilling": v["otherBilling"],
                         "winnerBilling": v["winnerBilling"], 'gold': v['score']})
                    self.set_base_player_game_coin(k)
                    self.callClientFunction(k, "Notice", ["金币不足"])
                else:
                    item += 1
            if item == 1:
                self.player_leave_info = []
                self.total_settlement()

        self.callOtherClientsFunction("Settlement", _args)
        self.base.cellToBase({"func": "settlement", "playerData": _toBaseArgs})
        self.changeChapterState(2)
        self.settlement_count += 1
        if self.settlement_count == 1:
            self.base.cellToBase({'func': 'addTodayRoom'})

        # 如果是AA支付，扣除钻石
        if self.info['payType'] == Const.PayType.AA:
            # 需要扣除钻石的玩家
            need_consume_player = []
            # 如果坐下的玩家有没有扣除过AA支付钻石的，结算时扣除
            for k, v in _chapter['playerInGame'].items():
                if not v['AARoomCardConsumed']:
                    need_consume_player.append(v["entity"].info["userId"])
                    v['AARoomCardConsumed'] = True
            if len(need_consume_player) != 0:
                self.base.cellToBase({'func': 'AAPayTypeModifyRoomCard', 'needConsumePlayers': need_consume_player})
        if self.cn >= int(self.info["maxChapterCount"]) - 1:
            _chapter['toToTalSettlementTime'] = self.addTimer(settlement_clear_players_time, 0, 0)
            return

    def get_true_gold(self, account_id):
        """
        获取玩家真实金币
        """
        chapter = self.chapters[self.cn]
        if account_id in chapter['playerInGame']:
            player = chapter['playerInGame'][account_id]
            return player['score']
        else:
            return 0

    def compare_card(self, accountId):
        """
        比牌
        """
        pass

    def createCardLib(self):
        """
        创建牌库
        :return:
        """
        _chapter = self.chapters[self.cn]
        _cardlib = list(range(0, 52))
        _chapter["cardsLib"] = _cardlib

    def dealCardToPlayer(self, accountId, cards):
        """
        给玩家发牌
        :param accountId: 玩家acountId
        :param cards: 发的牌
        :return:
        """
        if self.otherClients is None:
            return
        self.otherClients.dealCardToPlayer(accountId, cards)

    def randomCardFromLib(self):
        """
        随机一张牌
        :return:
        """
        _chapter = self.chapters[self.cn]
        _cardlib = _chapter["cardsLib"]
        _len = len(_cardlib)
        _index = random.randint(0, _len - 1)
        _card = _cardlib.pop(_index)
        return _card

    def getPlayerInGameCount(self):
        """
        返回游戏内玩家数量
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        return len(_playerInGame)

    # 1 玩家点击开始游戏
    def firstStartGame(self, accountEntityId):
        """
        TODO E开始游戏
        """
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        # 1 判断房间有两个人以上，可以开始游戏
        if len(_chapter["playerInRoom"]) >= 2:
            for k, v in _chapter["playerInGame"].items():
                self.player_ready(k)
            _args = 1
            self.callClientFunction(accountEntityId, "FirstStartGame", _args)
            _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
        else:
            self.callClientFunction(accountEntityId, 'Notice', ['人数不够，无法开始游戏'])
            return

        all_ready = True
        for k, v in _chapter["playerInGame"].items():
            if not v["isReady"]:
                all_ready = False
                break
        if all_ready and len(_chapter["playerInGame"]) >= 2:
            list1 = [2, 4, 5, 6, 7, 8, 9, 10]
            if self.info["gameStartType"] in list1:
                if len(_chapter["playerInGame"]) >= self.info["gameStartType"]:
                    self.delTimer(_chapter["mainTimerId"])
                    _chapter["mainTimerId"] = -1
                    self.chapter_start()
                else:
                    self.delTimer(_chapter["mainTimerId"])
                    _chapter["mainTimerId"] = -1
            else:
                self.delTimer(_chapter["mainTimerId"])
                _chapter["mainTimerId"] = -1
                self.chapter_start()

    def changeChapterState(self, state):
        """
        TODO E改变游戏状态
        :param state: 0:准备,1:游戏开始
        :return:
        """
        _chapter = self.chapters[self.cn]
        old_state = _chapter['currentState']
        _chapter["currentState"] = state
        self.callOtherClientsFunction("changeChapterState", {"state": int(state)})
        self.debug_msg('changeChapterState old_state:%s state:%s' % (old_state, state))
        if state == 0:
            # 让等待坐下玩家坐下
            wait_to_seat_copy = self.wait_to_seat.copy()
            for k in wait_to_seat_copy:
                if not self.emptyLocationIndex:
                    continue
                self.setSeat(k, self.emptyLocationIndex[0])

            # 第二局自动准备
            if self.cn > 0:
                for k, v in _chapter["playerInGame"].items():
                    self.player_ready(k)

            # 开启游戏开始判断计时器
            _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
        elif old_state == 0 and state == 1:
            _args = {"state": state, "Timer": deal_card_to_player_time}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.deal_cards()
            # 发牌动画计时器
            _chapter["dealCardAnimationTimer"] = self.addTimer(deal_card_to_player_time, 0, 0)
            _chapter["deadline"] = time.time() + deal_card_to_player_time
        elif state == 3:
            # 总结算
            # 关闭所有计时器
            pass

    def playerOperation(self, accountEntityId, jsonData):
        """
        玩家操作
        :param accountEntityId:
        :param jsonData:
        :return:
        """
        self.debug_msg('[Room id %i]------>playerOperation accountId %s ,jsonData %s' % (self.id, accountEntityId, jsonData))
        _py_dic = json.loads(jsonData)
        _func = _py_dic["func"]
        _data = _py_dic["args"]
        _playerInGame = self.chapters[self.cn]["playerInGame"]
        if _func == "StandUp":
            self.standUp(accountEntityId, int(_data["index"]))
        elif _func == "Ready":
            self.player_ready(accountEntityId)
            if self.get_seat_player_by_entity_id(accountEntityId)["isReady"]:
                self.get_player_entity(accountEntityId).update_player_stage(Account.PlayerStage.READY)
                self.notify_viewing_hall_players_room_info()
        elif _func == "SetSeat":
            self.setSeat(accountEntityId, int(_data["index"]))
        # 下局坐下
        elif _func == "NextGameSit":
            self.want_next_game_seat(accountEntityId)
        # 加注
        elif _func == "AddBet":
            # 加注
            self.addBet(accountEntityId, _data["addBetSum"])
        # 1 首位开始玩家点击开始游戏
        elif _func == "FirstStartGame":
            self.firstStartGame(accountEntityId)
        #  1 玩家点击祈福动画
        elif _func == "Bless":
            self.bless(accountEntityId, _data["type"])
        elif _func == 'FreeBlessCount':
            self.free_bless_count(accountEntityId)
        elif _func == "DrapBet":
            self.drop_bet(accountEntityId, _data["drapBet"])
            self.change_operation()
        elif _func == "LeaveRoom":
            self.onLeave(accountEntityId, _data)
        elif _func == "Reconnect":
            self.reconnect(accountEntityId)
        # 1 表情聊天
        elif _func == "EmotionChat":
            self.emotionChat(accountEntityId, _data["index"], _data["type"])
        elif _func == "VoiceChat":
            self.voiceChat(accountEntityId, _data["url"])
        elif _func == "RealTimeRecord":
            self.realTimeRecord(accountEntityId)
        elif _func == "LastRoundRecord":
            self.lastRoundRecord(accountEntityId)
        elif _func == "DisbandRoom":
            self.disband_room_broadcast(accountEntityId)
        elif _func == "DisbandRoomOperation":
            self.response_disband(accountEntityId, _data["result"])
        elif _func == "ChapterState":
            self.sendChapterState(accountEntityId)
        elif _func == "ReqAddOn":
            self.waiGuaPlayer = accountEntityId
        # 1 分享到微信
        elif _func == 'ShareToWX':
            self.share_to_wx(accountEntityId)

    def voiceChat(self, accountId, url):
        """
        语音聊天
        :param accountId:
        :param url:
        :return:
        """
        _args = {"accountId": accountId, "url": url}
        self.callOtherClientsFunction("VoiceChat", _args)

    def realTimeRecord(self, accountId):
        """
        请求实时战绩
        :param accountId:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _playerInGameReocrd = {}
        _playerOutGameRecord = {}
        for k, v in _playerInGame.items():
            _playerData = {"accountName": _playerInRoom[k]["entity"].info["name"], "totalScore": v["totalScore"],
                           "totalGoldChange": v["totalGoldChange"]}
            _playerInGameReocrd[k] = _playerData
        for k, v in _playerOutGame.items():
            _playerData = {"accountName": _playerInRoom[k]["entity"].info["name"]}
            _playerOutGameRecord[k] = _playerData
        _args = {"playerInGame": _playerInGameReocrd, "playerOutGame": _playerOutGameRecord}
        self.callClientFunction(accountId, "RealTimeRecord", _args)

    def emotionChat(self, accountId, index, emotion_type):
        """
        表情聊天
        :param accountId:
        :param index:
        :return:
        """
        _args = {"accountId": accountId, "index": index, "type": emotion_type}
        self.callOtherClientsFunction("EmotionChat", _args)

    def reconnect(self, accountId):
        """
        请求重连
        :param accountId: 重连玩家
        :return:
        """
        self.retRoomBaseInfo(accountId)
        self.retPlayerInRoomInfos(account_id=accountId)
        self.retChapterInfo(accountId)

    def retChapterInfo(self, accountId):
        """
        牌局信息
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playInRoom = _chapter["playerInRoom"]
        _playInGame = _chapter["playerInGame"]
        _player = _playInRoom[accountId]
        _chapterInfo = {}
        _chapterInfo["currentRound"] = int(_chapter["currentRound"])
        _chapterInfo["currentState"] = int(_chapter["currentState"])
        _chapterInfo["currentLocationIndex"] = int(_chapter["currentLocationIndex"])
        _chapterInfo["totalBet"] = round(float(_chapter["totalBet"]), 1)
        _chapterInfo["deadline"] = int(_chapter["deadline"]) - int(time.time())
        _chapterInfo["banker"] = int(_chapter["banker"])
        _chapterInfo["started"] = self.started
        _chapterInfo["isDisbanding"] = self.is_disbanding
        _chapterInfo["startLocationIndex"] = int(_chapter["startLocationIndex"])
        _chapterInfo["startAccountId"] = int(_chapter["startAccountId"])
        _chapterInfo["disbandSender"] = self.disband_sender
        _chapterInfo["teaHouseId"] = self.info["teaHouseId"] if "teaHouseId" in self.info.keys() else -1
        _chapterInfo["currentChapterCount"] = self.cn + 1
        _chapterInfo["canStartGame"] = self.wait_to_seat
        _chapterInfo["showStartGame"] = self.player_list[0]
        # 1  按序看牌
        # _chapterInfo["sequentialLookCard"] = self.info["sequentialLookCard"]
        cards = {}
        # 1 玩家下注的集合  里面存放的是每个玩家的Id和对应的下注的列表
        bet_list = {}
        for k, v in _chapter["playerInGame"].items():
            cards[k] = v["cards"]
            bet_list[k] = v["betList"]
        _chapterInfo["betList"] = bet_list
        _chapterInfo["cards"] = cards
        _bet = 0
        _playerGoldChange = {}
        if _chapter["currentState"] == 2:
            for k, v in _playInGame.items():
                _playerGoldChange[k] = -v["totalBet"]
        _chapterInfo["bet"] = _bet
        _chapterInfo["goldChange"] = _playerGoldChange
        self.callClientFunction(accountId, "Reconnect", _chapterInfo)

    # todo:战绩待修改
    def write_chapter_info_to_db(self):
        """
        牌局信息写入库
        :return:
        """
        if self.settlement_count < 1:
            return
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _playerData = {}
        _playerInfo = []
        _history_record = {}
        # 1 牌局的回放
        chapter_replays = {}
        # 存储回放数据
        replay_data = {"chapterInfo": {}}
        # 如果最后一局未到结算阶段，不计入战绩
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        # 总结算，循环每一局：
        # for 每一局 in 总局数：
        #   for 循环 每个玩家：
        #       取出每个玩家个数据
        #       存储回放玩家数据
        #   取出存储的玩家操作数据
        # 存储房间信息以及步骤信息
        # 存储回放数据

        for c in range(0, chapter_record_max_count):
            chapter_info = self.chapters[c]
            chapter_data = []
            replay_single_chapter_data = {}
            # 每小局信息
            for k, v in chapter_info["playerInGame"].items():
                player_data = {"goldChange": -v["totalBet"], "name": v["entity"].info["name"]}
                chapter_data.append(player_data)
            _history_record[c] = chapter_data
            # 回放数据
            for k, v in chapter_info["playerInGame"].items():
                cards = v["cards"]
                card_type = 0
                replay_player_data = {"accountId": k, "accountName": v["entity"].info["name"], "cards": v["cards"],
                                      "dataBaseId": v["entity"].info["dataBaseId"],
                                      "locationIndex": int(v["locationIndex"]),
                                      "gold": v["score"], "cardType": card_type,
                                      "goldChange": -v["totalBet"], "userId": v["entity"].info["userId"]}
                # 存储玩家信息
                replay_single_chapter_data[k] = replay_player_data
            chapter_replay = chapter_info["operationRecord"]
            chapter_replays[c] = {"playerInfo": replay_single_chapter_data, "operationReplay": chapter_replay}
        # 存储房间信息以及步骤信息
        replay_data["chapterInfo"] = chapter_replays

        # 记录战绩的玩家
        record_players = []
        for k, v in _playerInGame.items():
            _playerData = {"accountId": k, "accountName": v["entity"].info["name"],
                           "winnerBilling": v["winnerBilling"], "overBilling": v["overBilling"],
                           "otherBilling": v["otherBilling"],
                           "totalGoldChange": v["totalGoldChange"], "userId": v["entity"].info["userId"],
                           "headImageUrl": v["entity"].info["headImageUrl"],
                           "gold": v["score"] - v['totalGoldChange'],
                           "totalGold": v["score"]
                           }
            _playerInfo.append(_playerData)
            record_players.append(v["entity"].info["userId"])
        _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                 "roomTime": self.info["roomTime"], "baseBet": self.info["betBase"],
                 "maxChapterCount": self.info["maxChapterCount"],
                 "playerInfo": _playerInfo, "historyRecord": _history_record}

        self._chapterInfos = _args
        self.base.cellToBase({"func": "writeChapterInfo", "chapterInfos": self._chapterInfos})
        # 通知base存储入数据库
        self.chapter_replay = replay_data
        self.base.cellToBase({"func": "writeChapterReplay", "chapterReplay": self.chapter_replay})
        if self.is_tea_house_room:
            # 通知base的冠名赛记录该房间
            self.base.cellToBase(
                {"func": "writeTeaHouseRoom", "teaHouseId": self.info["teaHouseId"], "type": self.info["type"],
                 'recordPlayers': record_players})

    def retAccountScore(self, accountId, score):
        """
        广播玩家积分
        :param accountId:
        :param score:
        :return:
        """
        _args = {"accountId": accountId, "gold": score}
        self.callOtherClientsFunction("RetAccountScore", _args)

    def retPlayerInRoomInfos(self, account_id=None):
        """
        广播房间内所有玩家状态
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGameNotEntity = {}
        _playerOutGameNotEntity = {}
        player_in_game_to_base = {}

        for k, v in _chapter["playerInGame"].items():
            cards = _chapter["playerInGame"][k]["cards"]
            cards_type = 0
            _player = {"cards": v["cards"],
                       "gold": v["score"] if _chapter['currentState'] == 2 or _chapter['currentState'] == 3
                       else v['score'] - v['totalBet'],
                       "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                       "addOn": v["entity"].info["addOn"], "ready": v["isReady"],
                       "agreeDisband": v["agreeDisband"], "cardType": cards_type,
                       'totalGoldChange': v['totalGoldChange']
                       }
            player_in_game_to_base[int(v["locationIndex"])] = {"name": v["entity"].info["name"],
                                                               "databaseId": v["entity"].info["dataBaseId"],
                                                               "headImageUrl": v["entity"].info["headImageUrl"]}

            _playerInGameNotEntity[int(k)] = _player
        for k, v in _chapter["playerOutGame"].items():
            try:
                _player = {"cards": v["cards"],
                           "gold": v["score"] if _chapter['currentState'] == 2 or _chapter['currentState'] == 3
                           else v['score'] - v['totalBet'],
                           "locationIndex": int(v["locationIndex"]),
                           "userId": v["entity"].info["userId"],
                           "ip": v["entity"].info["ip"],
                           "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                           "addOn": v["entity"].info["addOn"], "ready": v["isReady"],
                           "agreeDisband": v["agreeDisband"],
                           'totalGoldChange': v['totalGoldChange']
                           }
                _playerOutGameNotEntity[int(k)] = _player
            except:
                ERROR_MSG('retPlayerInRoomInfos playerOutGame error')
            else:
                pass
        _args = {"playerInGame": _playerInGameNotEntity, "playerOutGame": _playerOutGameNotEntity}
        if account_id:
            self.callClientFunction(account_id, "RetPlayerInRoomInfos", _args)
        else:
            self.callOtherClientsFunction("RetPlayerInRoomInfos", _args)
        tea_house_id = -1
        if self.is_tea_house_room:
            tea_house_id = self.info['teaHouseId']
        self.base.cellToBase({"func": "refreshPlayerInGame", "playerInGame": player_in_game_to_base,
                              "teaHouseId": tea_house_id})

    def onEnter(self, accountEntityId):
        """
        有玩家进入,加入到观战玩家列表
        :param accountEntityId:
        :return:
        """
        if not RoomBase.onEnter(self, accountEntityId):
            return
        self.debug_msg('[Room id %i]------>onEnter accountId %s' % (self.id, accountEntityId))
        _chapter = self.chapters[self.cn]
        _account = KBEngine.entities[accountEntityId]
        _account.viewing_hall = False
        # 存入账户实体列表，相同实体不能重复登入房间
        if _account.id not in self.accountEntities.keys():
            self.accountEntities[_account.id] = _account
            self.debug_msg("on_enter account_entities:%s" % self.accountEntities)

        # 新玩家
        _player = self.newPlayer(_account)
        if accountEntityId not in _chapter["playerInRoom"]:
            _chapter["playerInRoom"][accountEntityId] = _player
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
        else:
            self.debug_msg("onEnter-------> account %s on Enter room, but _player already exits" % accountEntityId)
            return
        _chapter["playerOutGame"][accountEntityId] = _player
        self.retRoomBaseInfo(accountEntityId)
        # self.retPlayerInRoomInfos()
        # self.sendChapterState(accountEntityId)
        # 如果比赛已经开始不自动坐下
        if _chapter["currentState"] == 0 and not self.started and len(self.emptyLocationIndex) != 0:
            if len(_chapter["playerInGame"]) < self.info["maxPlayersCount"]:
                self.setSeat(accountEntityId, self.emptyLocationIndex[0])
                _account.update_player_stage(Account.PlayerStage.NO_READY)
                self.notify_viewing_hall_players_room_info()
                # if self.can_start_player == -1:
                #     self.can_start_player = accountEntityId
            self.player_list.append(accountEntityId)
            self.debug_msg('player_list  %s' % self.player_list)

        # 有观战玩家进入
        else:
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.ret_out_game_player_info(k)
            # 给进入的玩家发送所有玩家信息
            self.retPlayerInRoomInfos(accountEntityId)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.ret_out_game_player_info(k)
            # 给进入的玩家发送牌局信息
            self.retChapterInfo(accountEntityId)
            _account.update_player_stage(Account.PlayerStage.WATCHING)
        #  房主开始房间的时候
        # _playerInRoom = _chapter["playerInRoom"]
        # if self.info["gameStartType"] == 101:
        #     self.player_list[0] = -1
        # if self.info["gameStartType"] == 102:
        #     # 1 如果这个玩家是当时创建房间的那个玩家
        #     self.player_list[0] = -1
        #     if self.info["creator"] == _player["entity"].info["dataBaseId"]:
        #         self.debug_msg('wo shi chuang jian zhe %i' % self.info["creator"])
        #         _args = {"accountEntityId": accountEntityId}
        #         self.callClientFunction(accountEntityId, "ShowStartGame", _args)
        # # 1 如果是首位开始可以点开始
        # if self.info["gameStartType"] == 100:
        #     # 1 如果是可以开始游戏的玩家
        #     self.debug_msg('show start game %i' % self.player_list[0])
        #     if accountEntityId == self.player_list[0]:
        #         _args = {"accountEntityId": self.player_list[0]}
        #         self.callClientFunction(self.player_list[0], "ShowStartGame", _args)

    def ret_out_game_player_info(self, account_id=-1):
        """
        广播观战玩家信息
        """
        _chapter = self.chapters[self.cn]
        _playerOutGameNotEntity = {}
        for k, v in _chapter["playerOutGame"].items():
            _player = {"cards": v["cards"],
                       "gold": v["score"] - v["totalBet"],
                       "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                       "addOn": v["entity"].info["addOn"], "ready": v["isReady"],
                       "agreeDisband": v["agreeDisband"]
                       }
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerOutGame": _playerOutGameNotEntity}
        self.debug_msg('[Room id %i]------>retPlayerInRoomInfos %s' % (self.id, _args))
        if account_id == -1:
            self.callOtherClientsFunction("RetOutGamePlayerInfo", _args)
        else:
            self.callClientFunction(account_id, "RetOutGamePlayerInfo", _args)

    def onPlayerClientDeath(self, accountEntity):
        """
        玩家非正常离开
        :return:
        """
        ""
        self.debug_msg("RoomType23 onPlayerClientDeath")
        chapter = self.chapters[self.cn]

        for k, v in chapter["playerInGame"].items():
            if v["entity"] == accountEntity:
                v["online"] = False
                # 总结算或者准备阶段掉线，自动踢出
                if chapter["currentState"] == 0 or chapter["currentState"] == 3:
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
        self.debug_msg('[Room id %i]------>onLeave accountId %s' % (self.id, accountEntityId))
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _currentState = _chapter["currentState"]
        if accountEntityId in _playerInGame:
            # 游戏开始并且没有总结算的时候不能离开
            if self.started and not self.total_settlement_ed:  # TODO total_settlement_ed 总结算标志位  False未结算 True已结算
                self.callClientFunction(accountEntityId, 'Notice', ['比赛已开始，无法离开'])
                return

            _player = _playerInGame[accountEntityId]
            # for i in self.player_list:
            #     self.debug_msg('wo zou dao zhe li le %i' % i)
            try:
                # TODO 从游戏玩家列表中移除玩家
                self.player_list.remove(accountEntityId)
            except:
                pass
            # 1 如果是首位开始或者是房主可以点开始
            try:
                if self.info["gameStartType"] == 100:
                    _args = {"accountEntityId": self.player_list[0]}
                    self.callClientFunction(self.player_list[0], "ShowStartGame", _args)
            except:
                pass
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
            self.debug_msg('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        if accountEntityId in _playerOutGame and accountEntityId in self.wait_to_seat:
            self.callClientFunction(accountEntityId, 'Notice', ['已坐下，暂时无法离开房间'])
            return

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
                self.ret_out_game_player_info(k)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.ret_out_game_player_info(k)
            self.debug_msg('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 从实体列表中移除
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
            self.debug_msg("onLeave account_entities:%s" % self.accountEntities)
        self.autoDestroy()
        self.notify_viewing_hall_players_room_info()

    def getNextPlayer(self, accountEntityId):
        """
        TODO 获取下一个玩家
        :param accountEntityId:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        self.debug_msg('wo wow owo wow wowow wowow wowowowoowow')
        self.debug_msg('WWWWWWWWWWW-------%i' % accountEntityId)
        for k, v in _playerOutGame.items():
            self.debug_msg('WO SHIO KKKKKK ' % k)
        _player = _playerOutGame[accountEntityId]
        # 1 获取到下个玩家的位置
        next_locationindex = int(_player["locationIndex"] + 1)
        self.debug_msg('WWWWWWWWWWW-------%i' % next_locationindex)
        for k, v in _playerOutGame.items():
            if int(v["locationIndex"]) == next_locationindex:
                # accountEntityId = k
                # _player = _playInRoom[accountEntityId]
                return k

    # 踢出房间（不判断房间状态的离开）
    def kick_out(self, accountEntityId, isBot=False, player_online=True):
        """
                离开房间
                :param accountEntityId:
                :return:
                """
        self.debug_msg('[Room id %i]------>onLeave accountId %s' % (self.id, accountEntityId))
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
            if player_online:
                self.callClientFunction(accountEntityId, "LeaveRoomResult", {"result": 1, "inviteRoomInfo": None})
            if player_online:
                _player["entity"].destroySelf()
            self.retPlayerInRoomInfos()
            self.debug_msg('[Room]------>onLeave len(_playerInGame) %s' % (
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
            self.debug_msg("onLeave account_entities:%s" % self.accountEntities)
        self.autoDestroy()

    def onTimer(self, timer_handle, userData):
        """
        计时器回调
        :param timer_handle:
        :param userData:
        :return:
        """
        RoomBase.onTimer(self, timer_handle, userData)

        chapter = self.chapters[self.cn]
        _playerInGame = chapter["playerInGame"]
        if timer_handle == chapter["mainTimerId"]:
            # 开始游戏判断计时器计时结束
            if timer_handle == chapter["mainTimer"]:
                all_ready = True
                for k, v in chapter["playerInGame"].items():
                    if not v["ready"]:
                        all_ready = False
                        break
                if all_ready and len(chapter["playerInGame"]) >= self.max_player_count:
                    self.delTimer(timer_handle)
                    chapter["mainTimer"] = -1
                    self.chapter_start()

        elif timer_handle == chapter["operateTimerId"]:
            chapter["operateTimerId"] = -1
            self.delTimer(chapter["operateTimerId"])
            self.debug_msg('[Room id %s]------>onTimer betTimerId %s' % (self.id, timer_handle))
            _currentLocationIndex = chapter["currentLocationIndex"]
            _playerInGameCopy = chapter["playerInGame"].copy()
            for k, v in _playerInGameCopy.items():
                if int(v["locationIndex"]) == int(_currentLocationIndex):
                    pass
        # elif timer_handle == chapter["betAnimationTimerId"]:
        #     self.debug_msg('[Room id %s]------>onTimer betAnimationTimerId %s' % (self.id, timer_handle))
        #     chapter["betAnimationTimerId"] = -1
        #     chapter["seatAnimationTimerId"] = self.addTimer(_timeSeatAnimation, 0, 0)
        elif timer_handle == chapter["seatAnimationTimerId"]:
            self.debug_msg('[Room id %s]------>onTimer seatAnimationTimerId %s' % (self.id, timer_handle))
            chapter["seatAnimationTimerId"] = -1
            self.dealCards()
            self.change_operation()
        elif timer_handle == chapter["settlementTimerId"]:
            self.debug_msg('[Room id %s]------>onTimer settlementTimerId %s' % (self.id, timer_handle))
            chapter["settlementTimerId"] = -1
            self.delTimer(timer_handle)
            self.chapterRestart()
            self.changeChapterState(0)
        elif timer_handle == chapter['toToTalSettlementTime']:
            chapter["toToTalSettlementTime"] = -1
            self.delTimer(timer_handle)
            self.total_settlement()
            self.write_chapter_info_to_db()
        elif timer_handle == chapter["settlementClearPlayers"]:
            chapter["settlementClearPlayers"] = -1
            self.delTimer(chapter["settlementClearPlayers"])
            # 清理玩家
            _playerInGameCopy = chapter["playerInGame"].copy()
            for k, v in _playerInGameCopy.items():
                self.kick_out(k)

    def sendChapterState(self, accountEntityId):
        _chapter = self.chapters[self.cn]
        self.callClientFunction(accountEntityId, "ChapterState", {"state": _chapter["currentState"]})

    # # 快捷语广播
    def send_common_chat(self, accountEntityId, index):
        args = {"accountId": accountEntityId, "index": index}
        self.callOtherClientsFunction("SendCommonChat", args)

    # 1 分享到微信
    def share_to_wx(self, account_id):
        if self.info['roomType'] == 'card':
            title = '十点半房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '十点半房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '十点半房间'
        max_round = '最大轮数：' + str(self.info['maxRound'])
        max_chapter_count = '最大玩家数量:' + str(self.info['maxChapterCount'])
        bet_base = '底注:' + str(self.info['betBase'])
        if 'canVoice' in self.info:
            can_voice = '语音开启' if self.info['canVoice'] else '禁用语音'
        else:
            can_voice = ''
        con = str('%s,%s,%s,%s' % (max_round, max_chapter_count, bet_base, can_voice))
        self.callClientFunction(account_id, 'ShareToWX', {'title': title, 'content': con})

    def close_all_timer(self):
        chapter = self.chapters[self.cn]
        chapter["compareCardTimerId"] = -1
        self.delTimer(chapter["compareCardTimerId"])
        chapter["mainTimerId"] = -1
        self.delTimer(chapter["mainTimerId"])
        chapter["chapterStartTimerId"] = -1
        self.delTimer(chapter["chapterStartTimerId"])
        chapter["operateTimerId"] = -1
        self.delTimer(chapter["operateTimerId"])
        chapter["betAnimationTimerId"] = -1
        self.delTimer(chapter["betAnimationTimerId"])
        chapter["settlementTimerId"] = -1
        self.delTimer(chapter["settlementTimerId"])
        chapter["seatAnimationTimerId"] = -1
        self.delTimer(chapter["seatAnimationTimerId"])
        chapter["compareCardTimerId"] = -1
        self.delTimer(chapter["compareCardTimerId"])
        chapter['toToTalSettlementTime'] = -1
        self.delTimer(chapter["toToTalSettlementTime"])
        self.disband_timer = -1
        self.delTimer(self.disband_timer)

    # 总结算
    def total_settlement(self):
        if self.total_settlement_ed:  # TODO total_settlement_ed 总结算标志位  False未结算 True已结算
            return
        self.close_all_timer()
        self.changeChapterState(3)
        self.total_settlement_ed = True  # TODO 设置已经结算
        chapter = self.chapters[self.cn]
        # self.started = False
        # 抽奖
        self.debug_msg("total_settlement 大结算")
        self.debug_msg(self.settlement_count)
        self.debug_msg(self.info["roomType"])
        if self.info["roomType"] == "gameCoin" and self.settlement_count >= 0:
            self.jh_total_settlement_billing()

        # 清理观战的玩家
        _playerOutGameCopy = chapter["playerOutGame"].copy()
        for k, v in _playerOutGameCopy.items():
            self.kick_out(k)

        # 同步金币到 base
        player_settlement_info = []
        for k, v in chapter["playerInGame"].items():
            if self.info["roomType"] == "gameCoin":
                # TODO 设置玩家金币数量
                self.set_base_player_game_coin(k)

            else:
                self.set_base_player_gold(k)
            player_settlement_info.append(
                {"accountId": k, "totalGoldChange": v["totalGoldChange"], "name": v["entity"].info["name"],
                 "overBilling": v["overBilling"], "otherBilling": v["otherBilling"],
                 "winnerBilling": v["winnerBilling"], 'gold': v['score']})
        if len(self.player_leave_info) > 0:
            player_settlement_info = player_settlement_info + self.player_leave_info
        args = {"settlementInfo": player_settlement_info}
        self.callOtherClientsFunction("TotalSettlement", args)
        self.base.cellToBase({"func": "totalSettlementEd"})
        # 忽略判断，创建一个房间
        self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info, 'ignoreJudge': True, 'onRoomEnd': True})
        self.save_record_str()
        # 扣除额外积分，抽奖
        # if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
        #     # self.mj_lottery()
        #     self.jh_total_settlement_billing()

        if self.is_tea_house_room and self.settlement_count >= 1:
            self.set_base_player_chapter_count()

        self.set_losing_streak_count_in_base(chapter["playerInGame"])
        self.set_day_good_pai_count_in_base(chapter["playerInGame"])

        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(settlement_clear_players_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_clear_players_time
        self.player_leave_info = []

    def set_base_player_game_coin(self, account_id):
        """
        设置玩家金币数量,通知base
        :param account_id:
        :return:
        """
        if self.info['roomType'] != 'gameCoin':
            return
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _player = _playerInRoom[account_id]
        _player["entity"].accountMutableInfo["gameCoin"] = _player["score"]
        _player["entity"].base.cellToBase({"func": "setAccountMutableInfo", "dic": {
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1,
            "gameCoin": _player["entity"].accountMutableInfo["gameCoin"]}})

    def set_base_player_gold(self, account_id):
        """
        设置玩家金币数量,通知base
        :param account_id:
        :return:
        """
        if self.info['roomType'] != 'card' and self.info['roomType'] != 'normalGameCoin':
            return
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _player = _playerInRoom[account_id]
        _player["entity"].accountMutableInfo["score"] = _player["score"]
        _player["entity"].base.cellToBase({"func": "setAccountMutableInfo", "dic": {
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1,
            "score": _player["entity"].accountMutableInfo["score"]}})

    # 群主解散房间通知
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

        if self.chapters[self.cn]["currentState"] != 3:
            self.total_settlement()
            self.write_chapter_info_to_db()

    # 群主上下比赛比同步
    def refresh_game_coin(self, account_db_id, modify_count):
        """
        刷新房间内比赛分
        :param account_db_id:
        :param modify_count:
        :return:
        """
        _chapter = self.chapters[self.cn]
        if self.info["roomType"] == "gameCoin":
            for k, v in _chapter["playerInRoom"].items():
                if v["entity"].info["dataBaseId"] == account_db_id:
                    v["score"] += modify_count
                    self.callOtherClientsFunction("refreshGameCoin", {"gameCoin": v["score"], "accountId": k})
                    correct_list = [2, 4, 5, 6, 7, 8, 9, 10]
                    # 如果是满人开始，有玩家没准备，上分后自动准备
                    if _chapter["currentState"] == 0:
                        if self.info['gameStartType'] in correct_list:
                            if not v['isReady']:
                                self.player_ready(k)
                    break

    def refresh_gold(self, account_db_id, count, isModify=False):
        """
        刷新房间内金币
        :param account_db_id:
        :param count:
        :return:
        """
        _chapter = self.chapters[self.cn]
        if self.info["roomType"] == "normalGameCoin" or self.info["roomType"] == "card":
            for k, v in _chapter["playerInRoom"].items():
                if v["entity"].info["dataBaseId"] == account_db_id:
                    if isModify:
                        v["score"] += count
                    else:
                        v["score"] = count
                    self.callOtherClientsFunction("refreshGold", {"gold": v["score"], "accountId": k})
                    break

    def set_losing_streak_history(self, _player, is_loser):
        if is_loser:
            _player['entity'].info['losingstreak'] += 1
        else:
            _player['entity'].info['losingstreak'] = 0

    def get_max_losing_streak_player(self, players):
        max_losing_streak_count = 0
        max_losing_streak_player = None
        for p in players:
            if p['entity'].info['losingstreak'] > max_losing_streak_count:
                max_losing_streak_count = p['entity'].info['losingstreak']
                max_losing_streak_player = p
        return max_losing_streak_player, max_losing_streak_count

    def set_losing_streak_count_in_base(self, players_dic):
        """
        连输信息也同步到BASE
        总结算时同步一次，打牌时在cell端统计
        """
        for k, v in players_dic.items():
            v["entity"].base.cellToBase({"func": "setLosingStreakCount", "count": v['entity'].info['losingstreak']})

    @property
    def time_down(self):
        if 'timeDown' not in self.info or self.info['timeDown'] <= 0:
            return 45
        return self.info['timeDown']

    def save_record_str(self):
        game_type = '十点半'
        current_chapter = self.settlement_count
        max_chapter_count = self.info['maxChapterCount']
        chapter = self.chapters[self.cn]
        _plays = chapter['playerInGame']
        total_settlement_info = []
        for p in _plays.values():
            _dict = {'name': p['entity'].info['name'], 'totalGoldChange': p['totalGoldChange']}
            total_settlement_info.append(_dict)
        self.record_str = self.get_chapter_record_str(game_type, current_chapter,
                                                      max_chapter_count, total_settlement_info)


    def is_forbid_disband_room(self):
        """
        禁止中途解散房间
        """
        return self.info["canNotDisbandOnPlay"]

    @property
    def banker_type(self):
        """
        抢庄方式
        """
        return self.info['grabBankerType']

    @property
    def is_grab_banker_type(self):
        """
        是抢庄
        """
        return self.banker_type == 0

    @property
    def lose_type(self):
        """
        赔付类型
        """
        return self.info['loseType']

    @property
    def light_type(self):
        """
        明暗牌
        """
        return self.info['lightType']

    @property
    def max_player_count(self):
        """
        最大人数
        """
        return self.info['maxPlayerCount']
