# -*- coding: utf-8 -*-
import copy
import datetime
import random
from random import shuffle

import RoomType1Calculator
from RoomBase import *
import json
import time
import ZJHCalculator
import Account

# 准备倒计时时间
_timeReady = 5
# 下注动画时间
_timeBetAnimation = 0.5
# 单局结算时间
_timeSettlement = 5
# 结算到总结算时间
_timeToTotalSettlement = 2
# 位置交换动画时间
_timeSeatAnimation = 0
# 比牌动画时间
_timeCompareCardAnimation = 2
# 解散房间倒计时
time_disband = 30
# 总结算清理玩家倒计时
settlement_clear_players_time = 30



class RoomType1(RoomBase):
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
        # 空位
        # _chapter["emptyLocation"] = list(range(0, maxPlayerCount))
        # 是否授权买入
        _chapter["hasAnthorizeBuying"] = self.info["hasAnthorizeBuying"]
        # 最大局数
        _chapter["maxRound"] = self.info["maxRound"]
        # 比牌局数
        _chapter["compareCardRound"] = self.info["compareCardRound"]
        # 焖牌局数
        _chapter["lookCardRound"] = self.info["lookCardRound"]
        # 房间时间
        _chapter["roomTime"] = self.info["roomTime"]
        # 创建房间时刻
        _chapter["createRoomTime"] = self.info["createRoomTime"]
        # # 123 大于 JQK
        _chapter["attStraightBigJqk"] = self.info["attStraightBigJqk"]
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
        # 是否有人看过牌
        _chapter["hasLookCard"] = False
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
        # 机器人计时器
        _chapter["botTimerId"] = -1
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
        # 牌局历史
        _chapter["chapterHistory"] = {}
        # 开始玩家下标
        _chapter["startLocationIndex"] = -1
        # 开始玩家Id
        _chapter["startAccountId"] = -1
        # 抽奖
        _chapter["accountLottery"] = -1
        # 底注
        if "betBase" in self.info.keys():
            _betbase = self.info["betBase"]
        else:
            _betbase = 10
        # 闷牌底注
        _chapter["muffledCardBet"] = _betbase
        # 看牌底注
        _chapter["lookCardBet"] = _betbase * 2
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
        # 1 是否是比牌弃牌
        _player["isCompareDisCard"] = False
        # 是否看过牌
        _player["hasLookCard"] = False
        # 是否开启跟到底
        _player["hasFollowEnd"] = False
        # 是否弃牌
        _player["hasDisCard"] = False
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
        DEBUG_MSG('[Room id %i]------>chapterRestart ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]    # 在游戏中的玩家
        _playerInRoom = _chapter["playerInRoom"]    # 在房间中的玩家
        _playerOutGame = _chapter["playerOutGame"]  # 在游戏中观战的玩家
        _newChapter = self.newChapter(_chapter["maxPlayerCount"])  # 游戏中最大的玩家人数
        if self.cn >= int(self.info["maxChapterCount"]):
            self.total_settlement()
            self.write_chapter_info_to_db()
            return
        # 使用 deepcopy 避免每局战绩的玩家赢钱数相同
        _newChapter["playerInGame"] = copy.deepcopy(_playerInGame)
        _newChapter["playerOutGame"] = copy.deepcopy(_playerOutGame)
        # _newChapter["emptyLocation"] = copy.deepcopy(_chapter["emptyLocation"])
        _newChapter["playerInRoom"].update(_newChapter["playerInGame"])
        _newChapter["playerInRoom"].update(_newChapter["playerOutGame"])
        for k, v in _newChapter["playerInRoom"].items():   # 遍历在房间中玩家
            v["cards"] = []  # 牌
            v["hasLookCard"] = False  # 是否看过牌
            v["isCompareDisCard"] = False   # 是否是比牌弃牌
            v["hasFollowEnd"] = False  # 是否开启跟到底
            v["hasDisCard"] = False  # 是否弃牌
            v["totalBet"] = 0  # 下注总额
            v["isReady"] = False  # 准备状态
            v["betList"] = []  # 玩家下注的列表

    def chapter_start(self):
        """
        TODO 牌局开始
        :return:
        """
        DEBUG_MSG('[Room id %i]------>chapterStart ' % self.id)
        self.started = True
        self.info["started"] = True   # 准备状态
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]  # 在游戏中的玩家
        # 金币场扣除房费
        if self.is_gold_session_room():  # is_gold_session_room  是否是金币场房间 True 开始扣除金币
            for k, v in _playerInGame.items():
                # 减掉玩家金币
                v['score'] -= self.info['roomRate']
                # E 重新设置玩家金币数量
                self.set_base_player_gold(k)
        # 1 创建牌库
        self.createCardLib()
        # 1 更改游戏状态 设置游戏开始
        self.changeChapterState(1)
        _args = {}
        self.callOtherClientsFunction("ChapterStart", _args)
        self.callOtherClientsFunction("currentChapterCount", {"count": self.cn + 1})
        # 1 定庄 设置庄家
        self.setBanker()
        # 坐庄信息同步到BASE
        # self.set_base_player_banker_history(_chapter)
        # 因为炸金花一个房间会进行多局游戏，庄信息只在进房间同步一次，所以庄需要自己记录
        self.set_banker_history_in_cell(_chapter)
        # 1 设置当前轮数
        self.setCurrentRound(0)

        # 通知 base 游戏开始
        if self.cn == 0:
            # 将坐下玩家的DB_ID传入前台
            player_in_game_db_id = []
            for k, v in self.chapters[self.cn]["playerInGame"].items():
                player_in_game_db_id.append(v["entity"].info["dataBaseId"])
                self.player_entity(v).update_player_stage(Account.PlayerStage.PLAYING, self.max_chapter_count,
                                                          self.current_chapter_count)
            # 通知客户端返回房间
            self.notify_viewing_hall_players_chapter_start()
            # 房间开始
            self.base.cellToBase({"func": "roomStart", "roomInfo": self.info, "playerInGameDBID": player_in_game_db_id})
            # 房间开始，并且人未满时创建新的房间(onRoomEnd为true时插入在当前房间后面)
            if len(_chapter['playerInGame']) < self.info['maxPlayersCount']:
                # E 自动创建房间
                self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})
        for k, v in _playerInGame.items():
            # 下注
            self.drop_bet(k, _chapter["muffledCardBet"])
        _chapter["betAnimationTimerId"] = self.addTimer(_timeBetAnimation, 0, 0)
        # 通知改变房间状态
        self.base.cellToBase({"func": "changeRoomState", "roomState": 1})
        # 创建了一个新牌局  牌局+1
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

    def chapterReady(self):
        """
        牌局准备
        :return:
        """

        DEBUG_MSG('[Room id %i]------>chapterReady ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        # 玩家掉线，让其退出房间
        _playerInRoomCopy = _playerInRoom.copy()
        for k, v in _playerInRoomCopy.items():
            # 如果玩家不在线
            if v["entity"].client_death is True:  # TODO client_death 玩家在线状态 [False在线]    [True不在线]
                # 离开房间
                self.onLeave(v["entity"].id)
        DEBUG_MSG('?????????????%s' % self.info["winnerRaffleInterval"])
        DEBUG_MSG('?????????????%s' % self.info["winnerBilling"])

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

    def changeOperation(self):
        """
        移交操作权限
        :return:
        """
        DEBUG_MSG('[Room id %i]------>changeOperation ' % self.id)
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
                        DEBUG_MSG("_currentRound=%s, maxCount=%s" % (_currentRound, self.info["maxRound"]))
                        return
                if not _locationIndexs[_nextLocationIndex]["hasDisCard"]:  # 是否弃牌
                    break
            _nextLocationIndex += 1
            DEBUG_MSG("startLocationIndex:%s" % _startLocationIndex)
            DEBUG_MSG("_nextLocationIndex:%s" % _nextLocationIndex)

        for k, v in _playerInGame.items():
            DEBUG_MSG("locationIndex = %s" % v["locationIndex"])
            if int(v["locationIndex"]) == int(_nextLocationIndex):
                # 1 设置当前操作玩家位置
                self.setCurrentLocationIndex(_nextLocationIndex, k)

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
        is_in_rand_range = self.is_need_rand_score_control("RoomType1")
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
            DEBUG_MSG('最大连输 %s %s' % (max_losing_streak_count, luck_player['entity'].id if luck_player else luck_player))

            # 60%概率发
            rand_num = random.randint(1, 100)
            if rand_num > 60:
                luck_player = None

        # if not luck_player:
        #     # 幸运数字玩家
        #     is_in_rand_range = self.is_need_rand_score_control("RoomType1")
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
            good_card_index = RoomType1Calculator.get_good_pai(all_cards, self.info)
            if good_card_index >= 0:
                luck_player["cards"] = all_cards[good_card_index]
                del all_cards[good_card_index]
                have_pai_player_id = luck_player['entity'].id
                DEBUG_MSG('good pai player id: %s cards: %s' % (have_pai_player_id, luck_player["cards"]))

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
                if RoomType1Calculator.compare_card(v["cards"], _maxCards, self.info) == 1:
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
        DEBUG_MSG("len %s,chapter lib%s" % (len(cards), cards))

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

    def setCurrentLocationIndex(self, currentLocationIndex, accountId):
        """
        设置当前操作玩家
        :param currentLocationIndex: 当前操作玩家下标
        :param accountId: 当前操作玩家id
        :return:
        """
        DEBUG_MSG('[Room id %i]------>setCurrentLocationIndex ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _player = _playerInGame[accountId]
        _chapter["currentLocationIndex"] = currentLocationIndex
        # if _player["hasLookCard"]:
        #     _bet = _chapter["lookCardBet"]
        # else:
        #     _bet = _chapter["muffledCardBet"]
        _args = {"accountId": accountId, "Timer": self.time_down,
                 "lookCardBet": _chapter["lookCardBet"],
                 "muffledCardBet": _chapter["muffledCardBet"]}
        _chapter["operateTimerId"] = self.addTimer(self.time_down, 0, 0)
        _chapter["deadline"] = int(time.time()) + self.time_down
        self.callOtherClientsFunction("ChangeOperation", _args)
        if _player["entity"].info["isBot"] == 1:
            _time = random.randint(5, 8)
            _chapter["botTimerId"] = self.addTimer(_time, 0, 0)

    def setCurrentRound(self, currentRound):
        """
        设置当前轮数
        :param currentRound:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>setCurrentRound currentRound %s' % (self.id, currentRound))
        _chapter = self.chapters[self.cn]
        if _chapter["maxRound"] - currentRound == 1:  # maxRound 最大局数
            self.callOtherClientsFunction("Notice", ["两轮下注后系统自动比牌"])
        # 1 当前轮数大于牌局最大轮数
        if currentRound > _chapter["maxRound"]:   # maxRound 最大局数
            # 1 获取未弃牌玩家
            _playerHasNoDisCard = self.getHasNoDisCardPlayer()
            _playerHasNoDisCardKeys = list(_playerHasNoDisCard.keys())
            _length = len(_playerHasNoDisCardKeys)
            # 1 只剩两个人未弃牌()
            # if _length == 2:
            #     _cards1 = _playerHasNoDisCard[_playerHasNoDisCardKeys[0]]["cards"]
            #     _cards2 = _playerHasNoDisCard[_playerHasNoDisCardKeys[1]]["cards"]
            #     _result = compareCard(_cards1, _cards2, self.info)
            #     if _result == 1:
            #         self.disCard(_playerHasNoDisCardKeys[1], isCompareDisCard=True)
            #     elif _result == -1:
            #         self.disCard(_playerHasNoDisCardKeys[0], isCompareDisCard=True)
            #     else:
            #         ""
            #     return False
            _maxAccountId = _playerHasNoDisCardKeys[0]
            # 有多人未弃牌
            # for i in range(1, _length):
            #     # 1 如果有235大豹子的选项
            #     if _chapter["twoThreeFiveBigLeopard"]:
            #         # 1 获取到这个人的牌
            #         _cards = _playerHasNoDisCard[_playerHasNoDisCardKeys[i]]["cards"]
            #         # 1 得到牌型
            #         _type_1 = typeofCard(_cards, self.info)
            #     else:
            #         # 1 cards1 为未弃牌玩家最大ID的牌
            #         _cards1 = _playerHasNoDisCard[_maxAccountId]["cards"]
            #         _cards2 = _playerHasNoDisCard[_playerHasNoDisCardKeys[i]]["cards"]
            #         _result = compareCard(_cards1, _cards2, self.info)
            #         if _result == 1:
            #             # 1 发起比牌的玩家赢
            #             self.disCard(_playerHasNoDisCardKeys[i], isCompareDisCard=True)
            #         elif _result == -1:
            #             # 1 被比牌的玩家赢
            #             self.disCard(_maxAccountId, isCompareDisCard=True)
            #             _maxAccountId = _playerHasNoDisCardKeys[i]
            #         else:
            #             ""
            # 1 如果有 235 大 豹子 的选项
            # 1 下面这些代码考虑多人未弃牌
            if self.info["twoThreeFiveBigLeopard"]:
                list1 = []
                list2 = []
                # 1循环所有人
                for i in range(_length):
                    # 1 获取到这个人的牌
                    _cards_1 = _playerHasNoDisCard[_playerHasNoDisCardKeys[i]]["cards"]
                    # 1 得到牌型
                    _type_1 = RoomType1Calculator.type_of_cards(_cards_1, self.info)
                    # 1 将所有人的牌型对应的值和ID加到列表中
                    list2.append(_playerHasNoDisCardKeys[i])
                    # 将ID对应的牌型的值加入到列表中
                    list2.append(_type_1)
                # list2里面存放的是从头到尾的每个人的ID 牌的值   类似[7795,100,7895,96,7792,98,7793,95]
                for j in range(len(list2)):
                    if j % 2 == 0:
                        list1.append([list2[j], list2[j + 1]])
                # 1 结果为 类似于  [[7795,100],[7895,96],[7792,98],[7793,95]]
                # 对list1中的每一个小list2的第二个值进行排序(冒泡排序)
                for i in range(len(list1) - 1):
                    for j in range(len(list1) - 1):
                        if list1[j][1] > list1[j + 1][1]:
                            list1[j + 1], list1[j] = list1[j], list1[j + 1]
                # 1 此时的list1里存放的是根据牌型的大小排好序的列表
                # 1 如果既有豹子又有235金花   那么循环除了235金花的所有人  其他的人全部弃牌
                # 1 for 循环只考虑有235金花的情况
                for i in list1:
                    # 1 如果勾选顺子大于金花  金花为97
                    if self.info["straightBigSameColor"]:
                        cards = _playerHasNoDisCard[i[0]]["cards"]
                        cards.sort()
                        _card_1 = int(cards[0] / 4)
                        _card_2 = int(cards[1] / 4)
                        _card_3 = int(cards[2] / 4)
                        # 判断循环的那个人是金花且最大的人是豹子
                        if i[1] == 97 and list1[-1][1] == 100:
                            # 是金花且是235
                            if _card_1 == 1 and _card_2 == 2 and _card_2 == 4:
                                list1.remove(i)
                                # 1 让在列表中的每一个人都弃牌，除了235不弃牌
                                for k in list1:
                                    # TODO 弃牌
                                    self.disCard(k[0], is_settlement_compare_dis_card=True,
                                                 is_compare_card_dis_card=False)
                                return False

                    # 没勾选顺子大于金花的情况  金花为98
                    else:
                        cards = _playerHasNoDisCard[i[0]]["cards"]
                        cards.sort()
                        _card_1 = int(cards[0] / 4)
                        _card_2 = int(cards[1] / 4)
                        _card_3 = int(cards[2] / 4)
                        # 判断循环的那个人是金花且最大的人是豹子
                        if i[1] == 98 and list1[-1][1] == 100:
                            if _card_1 == 1 and _card_2 == 2 and _card_2 == 4:
                                list1.remove(i)
                                # 1 让在列表中的每一个人都弃牌，除了235不弃牌
                                for k in list1:
                                    # 弃牌
                                    self.disCard(k[0], is_settlement_compare_dis_card=True,
                                                 is_compare_card_dis_card=False)
                                return False
                # 1 如果最小的那个人是单张
                if list1[0][1] == 95 and list1[-1][1] == 100:
                    # 1 第一个人的牌
                    DEBUG_MSG('235>baozi')
                    cards = _playerHasNoDisCard[list1[0][0]]["cards"]
                    DEBUG_MSG('zheshi diyige ren de pai %i %i %i' % (cards[0], cards[1], cards[2]))
                    cards.sort()
                    _card_1 = int(cards[0] / 4)
                    _card_2 = int(cards[1] / 4)
                    _card_3 = int(cards[2] / 4)
                    DEBUG_MSG('zheshi diyige ren de pai %i %i %i' % (_card_1, _card_2, _card_3))
                    # 如果是单张 且最小的那个人是235
                    if _card_1 == 1 and _card_2 == 2 and _card_3 == 4:
                        list1.remove(list1[0])
                        DEBUG_MSG('1234567 zhe shi ')
                        # 1 让在列表中的每一个人都弃牌，除了235不弃牌
                        for k in list1:
                            DEBUG_MSG('zhe  shi yao rang ta qi pai de ren %i' % k[0])
                            # 弃牌
                            self.disCard(k[0], is_settlement_compare_dis_card=True)
                        return False
                # 如果不出现 单张235 和 豹子   金花235和豹子出现在同一局的情况下 走正常游戏逻辑
                for i in range(1, _length):
                    # 1 cards1 为未弃牌玩家最大ID的牌
                    _cards1 = _playerHasNoDisCard[_maxAccountId]["cards"]
                    _cards2 = _playerHasNoDisCard[_playerHasNoDisCardKeys[i]]["cards"]
                    _result = RoomType1Calculator.compare_card(_cards1, _cards2, self.info)
                    if _result == 1:
                        # 1 发起比牌的玩家赢
                        # 弃牌
                        self.disCard(_playerHasNoDisCardKeys[i], is_settlement_compare_dis_card=True,
                                     is_compare_card_dis_card=True)
                    elif _result == -1:
                        # 1 被比牌的玩家赢
                        # 弃牌
                        self.disCard(_maxAccountId, is_settlement_compare_dis_card=True,
                                     is_compare_card_dis_card=True)
                        _maxAccountId = _playerHasNoDisCardKeys[i]
                    else:
                        ""
                return False
            # 1 没有勾选 235 大 豹子 的选项   之前的逻辑
            else:
                for i in range(1, _length):
                    # 1 cards1 为未弃牌玩家最大ID的牌
                    _cards1 = _playerHasNoDisCard[_maxAccountId]["cards"]
                    _cards2 = _playerHasNoDisCard[_playerHasNoDisCardKeys[i]]["cards"]
                    _result = RoomType1Calculator.compare_card(_cards1, _cards2, self.info)
                    if _result == 1:
                        # 1 发起比牌的玩家赢
                        # 弃牌
                        self.disCard(_playerHasNoDisCardKeys[i], is_settlement_compare_dis_card=True,
                                     is_compare_card_dis_card=True)
                    elif _result == -1:
                        # 1 被比牌的玩家赢
                        # 弃牌
                        self.disCard(_maxAccountId, is_settlement_compare_dis_card=True,
                                     is_compare_card_dis_card=True)
                        _maxAccountId = _playerHasNoDisCardKeys[i]
                    else:
                        ""
                return False
        _chapter["currentRound"] = currentRound
        _args = {"currentRound": _chapter["currentRound"]}
        self.callOtherClientsFunction("RetCurrentRound", _args)
        return True

    def setBanker(self):
        """
        定庄,随机一个庄家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>setBanker ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]   # 游戏中玩家
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
        DEBUG_MSG('[Room id %i]------>setSeat accountId %s, locationIndex %s ' % (self.id, accountId, locationIndex))
        _chapter = self.chapters[self.cn]
        # 1 不在观战玩家列表中
        if accountId not in _chapter["playerOutGame"]: # playerOutGame 观战玩家列表
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
        # DEBUG_MSG('[Room id %i]------>setSeat emptyLocation %s' % (self.id, self.info["maxPlayersCount"]))
        self.emptyLocationIndex.remove(locationIndex)
        # self.callOtherClientsFunction("SetSeat", _args)

        # # 从等待坐下中移除
        if accountId in self.wait_to_seat:  # self.wait_to_seat 观战中的下局可以开始坐下的玩家
            DEBUG_MSG(
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
        DEBUG_MSG('[Room id %i]------>standUp accountId %s, locationIndex %s ' % (self.id, accountId, locationIndex))
        _chapter = self.chapters[self.cn]
        # 当前房间状态
        if _chapter["currentState"] != 0:
            return
        # 1 如果玩家不在游戏中
        if accountId not in _chapter["playerInGame"]:
            return
        _chapter["playerOutGame"][accountId] = _chapter["playerInGame"][accountId]
        _chapter["playerInGame"].pop(accountId)
        _args = {"accountId": accountId, "locationIndex": locationIndex}
        self.emptyLocationIndex.append(locationIndex)
        self.callOtherClientsFunction("StandUp", _args)

    def addBet(self, accountId, addBetSum):
        """
        加注
        :param accountId: 加注玩家
        :param addBetSum: 加注金额
        :return:
        """
        DEBUG_MSG('[Room id %i]------>addBet accountId %s, addBetSum %s ' % (self.id, accountId, addBetSum))
        _chapter = self.chapters[self.cn]
        _player = _chapter["playerInGame"][accountId]
        if int(_player['locationIndex']) != int(_chapter["currentLocationIndex"]):
            return
        _bet = 0
        #  1 totalBet   下注总额
        # 如果是金币场 并且所带金币小于基本金币 禁止入场
        # self.have_gold_limit()  根据是否是比赛币场和比赛币开关判断是否有金币限制
        if self.have_gold_limit() and addBetSum > _player["score"] - _player["totalBet"]:
            self.callClientFunction(accountId, "Notice", ["%s不足,请继续带入" % self.gold_name])

            self.callClientFunction(accountId, "AddBetCallBack", ["0"])
            return False
        # 1 判断是否看牌
        if _player["hasLookCard"]:
            # 1 看牌底注
            _chapter["lookCardBet"] = addBetSum
            # 1 焖牌底注
            _chapter["muffledCardBet"] = int(addBetSum / 2)
            _bet = _chapter["lookCardBet"]
        else:
            _chapter["lookCardBet"] = int(addBetSum * 2)
            _chapter["muffledCardBet"] = addBetSum
            _bet = _chapter["muffledCardBet"]
        # 1 关闭下注计时器
        self.delTimer(_chapter["operateTimerId"])
        _chapter["operateTimerId"] = -1
        # 1 牌局总加注
        _chapter["totalBet"] += _bet
        _player["betList"].append(addBetSum)
        # 1 玩家总加注
        _player["totalBet"] += _bet
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
        self.changeOperation()

    def drop_bet(self, accountId, betSum):
        """
        下注
        :param accountId: 下注玩家
        :param betSum: 下注金额
        :return:
        """
        DEBUG_MSG('[Room id %i]------>drapBet accountId %s, betSum %s ' % (self.id, accountId, betSum))
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _player = _playerInGame[accountId]
        # 1 下注金额大于玩家的钱减去加注的钱
        DEBUG_MSG('betSum-----------------------%s ' % str(betSum))
        DEBUG_MSG('_player["score"]-----------------------%s ' % str(_player["score"]))
        DEBUG_MSG('_player["totalBet"]-----------------------%s ' % str(_player["totalBet"]))
        DEBUG_MSG(_player)
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

    def followEnd(self, accountId):
        """
        跟到底
        :param accountId: 跟到底的玩家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>followEnd accountId %s' % (self.id, accountId))
        _chapter = self.chapters[self.cn]
        _player = _chapter["playerInGame"][accountId]
        # 1 开启跟到底
        _player["hasFollowEnd"] = True
        _args = {"accountId": accountId}
        self.callOtherClientsFunction("FollowEnd", _args)

    def getHasNoDisCardPlayer(self):
        """
        获取未弃牌玩家
        :return:
        """
        _chapter = self.chapters[self.cn]
        _hasNoDisCardPlayer = {}
        for k, v in _chapter["playerInGame"].items():
            if not v["hasDisCard"]:  # 是否弃牌
                _hasNoDisCardPlayer[k] = v
        return _hasNoDisCardPlayer

    def disCard(self, accountId, is_settlement_compare_dis_card=False, is_compare_card_dis_card=False):
        """
        弃牌
        :param is_settlement_compare_dis_card:
        :param accountId: 弃牌玩家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>disCard accountId %s' % (self.id, accountId))
        _chapter = self.chapters[self.cn]
        _player = _chapter["playerInGame"][accountId]
        if _player['hasDisCard']:  # 是否弃牌
            DEBUG_MSG('[Room id %i]------>disCard accountId %s is already discard' % (self.id, accountId))
            return
        self.delTimer(_chapter["operateTimerId"])
        _chapter["operateTimerId"] = -1
        _player["hasDisCard"] = True  # 是否弃牌
        _player["isCompareDisCard"] = is_compare_card_dis_card
        _args = {"accountId": accountId, "isCompareDisCard": _player["isCompareDisCard"]}
        self.callOtherClientsFunction("DisCard", _args)
        # 记录出牌步骤
        record = {}
        record["accountId"] = accountId
        # 相关类型置为 1
        record["operationType"] = 5
        # 操作  存储玩家跟注金额
        record["operationArgs"] = {"isCompareDisCard": _player["isCompareDisCard"]}
        _chapter["operationRecord"].append(record)
        _hasNoDisCardPlayer = self.getHasNoDisCardPlayer()
        if len(_hasNoDisCardPlayer) < 2:
            self.settlement()
            return
        else:
            if not is_settlement_compare_dis_card:
                self.changeOperation()

    def settlement(self):
        """
        结算
        :return:
        """
        DEBUG_MSG('[Room id %i]------>settlement ' % self.id)
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
            # DEBUG_MSG('[Room id %i]------>settlement totalBet:%s chapterTotalBet%s cutRatio%s' % (
            #     self.id, v["totalBet"], _chapterTotalBet, self.cutRatio))
            # 1 胜者的  总下注-牌局总下注  等于负的赢钱的价值
            v["totalBet"] = int(v["totalBet"] - _chapterTotalBet)
            # 1 获取到赢家的牌型
            cards = _playerInGame[k]["cards"]
            cards_type = RoomType1Calculator.type_of_cards(cards, self.info) if \
                type(RoomType1Calculator.type_of_cards(cards, self.info)) == float or \
                type(RoomType1Calculator.type_of_cards(cards, self.info)) == int else -1
            DEBUG_MSG('cardsType -----------------%i' % cards_type)
            # 大赢家的牌型是同花顺
            if cards_type == 99:
                for m, n in _playerInGame.items():
                    if m != k:
                        DEBUG_MSG('straightXiQian compare player: %i  %i' % (k, m))
                        n["totalBet"] += self.info["straightXiQian"]
                        v["totalBet"] -= self.info["straightXiQian"]
            # 大赢家的牌型是豹子
            if cards_type == 100:
                for m, n in _playerInGame.items():
                    if m != k:
                        DEBUG_MSG('leopardXiQian compare player: %i  %i' % (k, m))
                        n["totalBet"] += self.info["leopardXiQian"]
                        v["totalBet"] -= self.info["leopardXiQian"]

            # v["totalBet"] = int((v["totalBet"] - _chapterTotalBet) * (1 - self.cutRatio / 100))
        _args = {}
        _toBaseArgs = dict()
        for k, v in _playerInGame.items():
            cards = _playerInGame[k]["cards"]
            cards_type = RoomType1Calculator.type_of_cards(cards, self.info) if \
                type(RoomType1Calculator.type_of_cards(cards, self.info)) == float or \
                type(RoomType1Calculator.type_of_cards(cards, self.info)) == int else -1
            # 1 总金币变化等于 下注总额
            DEBUG_MSG('goldChange -----------------%i' % v["totalGoldChange"])
            v["totalGoldChange"] += -v["totalBet"]
            _playerData = {"gold": v["score"] - v["totalBet"], "goldChange": -v["totalBet"], "cards": v["cards"],
                           'totalGoldChange': v['totalGoldChange'],
                           "type": cards_type}
            _args[k] = _playerData
            v["score"] = v["score"] - v["totalBet"]
            _userId = v["entity"].info["userId"]
            _toBaseArgs[_userId] = {"goldChange": -v["totalBet"]}
        # for k, v in _playerInGame.items():

        self.callOtherClientsFunction("Settlement", _args)
        self.base.cellToBase({"func": "settlement", "playerData": _toBaseArgs})
        self.changeChapterState(2)
        # 金币场结算后检测玩家的金币数是否为零
        if self.info["roomType"] == "gold":
            self.check_gold()
            pass
        else:
            item =0
            for k, v in _playerInGame.items():
                if v["score"] <= 0:
                    self.player_leave_info.append({"accountId": k, "totalGoldChange": v["totalGoldChange"], "name": v["entity"].info["name"],
                 "overBilling": v["overBilling"], "otherBilling": v["otherBilling"],
                 "winnerBilling": v["winnerBilling"], 'gold': v['score']})
                    self.set_base_player_game_coin(k)
                    self.callClientFunction(k, "Notice", ["金币不足"])
                else:
                    item += 1
            if item == 1:
                self.player_leave_info = []
                self.total_settlement()
        _chapterHistory = _chapter["chapterHistory"]
        _chapterData = {}
        for k, v in _playerInGame.items():
            _playerData = {"accountName": v["entity"].info["name"], "cards": v["cards"], "goldChange": -v["totalBet"],
                           "cardType": ZJHCalculator.calculatorCard(v["cards"]),
                           "headImageUrl": v["entity"].info["headImageUrl"]}
            _chapterData[k] = _playerData
            # 更新分数控制
            v["entity"].update_score_control(-v['totalBet'])

        if self.info["roomType"] == "gameCoin":
            # 首局结算抽水
            if self.settlement_count == 0:
                for k, _p in _playerInGame.items():
                    if self.get_true_gold(_p['entity'].id) < self.info['billingCount']:
                        DEBUG_MSG('RoomType1 billing_count not enough account_id:%s' % _p['entity'].id)
                        continue
                    billing_count = self.info['billingCount']
                    # _p['totalGoldChange'] -= billing_count
                    _p['score'] -= billing_count
                    DEBUG_MSG('RoomType1 billing_count account_id:%s,count:%s' % (_p['entity'].id, billing_count))

            # 每小局结算大赢家抽水,保留整数  E小局抽水
            # 获取大赢家
            settlement_winners = self.jh_get_settlement_winners()
            DEBUG_MSG('-------------炸金花大赢家一共有%s 个' % str(len(settlement_winners)))
            for location_index, v in settlement_winners.items():
                DEBUG_MSG('-------------------------')
                DEBUG_MSG(v)
                DEBUG_MSG('-------------------------')
                settlement_winner_account_id = v['entity'].id
                # k:account_id v:winner字典
                DEBUG_MSG('RoomType1 settlement_winner_account_id 玩家id %s name %s' % (str(settlement_winner_account_id), str(v["entity"].info["name"])))
                # 计算大赢家小局抽水
                settlement_winner_true_gold = self.jh_get_true_gold(settlement_winner_account_id)
                DEBUG_MSG('RoomType1 settlement_winner_true_gold billing  玩家%s 真实金币%s' % (str(v["entity"].info["name"]), settlement_winner_true_gold))
                DEBUG_MSG('RoomType1 settlementBilling billing 抽水比例 %s' % self.info['settlementBilling'])
                settlement_winner_billing = settlement_winner_true_gold * self.info['settlementBilling']
                DEBUG_MSG('RoomType1 settlement_winner 抽水金额 billing %s' % settlement_winner_billing)
                DEBUG_MSG('RoomType1 settlement_winner_true_gold billing  玩家%s totalGoldChange1 %s' % (str(v["entity"].info["name"]), v['totalGoldChange']))
                v['totalGoldChange'] -= settlement_winner_billing
                DEBUG_MSG('RoomType1 settlement_winner_true_gold billing  玩家%s totalGoldChange2 %s' % (str(v["entity"].info["name"]), v['totalGoldChange']))
                v['totalGoldChange'] = int(v['totalGoldChange'])
                DEBUG_MSG('RoomType1 settlement_winner_true_gold billing  玩家%s totalGoldChange3 %s' % (str(v["entity"].info["name"]), v['totalGoldChange']))
                v['score'] -= settlement_winner_billing
                v['score'] = int(v['score'])
                DEBUG_MSG('RoomType1 settlement_winner_true_gold billing  玩家%s score %s' % (str(v["entity"].info["name"]), v['score']))
                # 同步房费给base
                self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                      "todayGameCoinAdd": settlement_winner_billing,
                                      "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType1")})



        _chapterHistory["chapterData"] = _chapterData
        _chapterHistory["currentRound"] = self.cn + 1
        _chapterHistory["roomId"] = self.info["roomId"]
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
            _chapter['toToTalSettlementTime'] = self.addTimer(_timeToTotalSettlement, 0, 0)
            return

    def get_true_gold(self, account_id):
        """
        获取玩家真实金币
        """
        chapter = self.chapters[self.cn]
        player = chapter['playerInGame'][account_id]
        return player['score']

    def lookCard(self, accountId):
        """
        看牌
        :param accountId: 看牌玩家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>lookCard accountId %s' % (self.id, accountId))
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        # 1 当前轮数
        _currentRound = _chapter["currentRound"]
        # if _currentRound < _chapter["lookCardRound"]:
        #     return
        _player = _chapter["playerInGame"][accountId]
        _player["hasLookCard"] = True
        if not _chapter["hasLookCard"]:
            _chapter["lookCardBet"] = _chapter["muffledCardBet"] * 2
            _chapter["hasLookCard"] = True
        # 1  muffledCardBet  闷牌底注
        # 1 牌型发给客户端  获取到玩家的牌值
        cards = _playerInGame[accountId]["cards"]
        cards_type = RoomType1Calculator.type_of_cards(cards, self.info) if \
            type(RoomType1Calculator.type_of_cards(cards, self.info)) == float or \
            type(RoomType1Calculator.type_of_cards(cards, self.info)) == int else -1
        _args = {"accountId": accountId, "lookCardBet": _chapter["lookCardBet"],
                 "muffledCardBet": _chapter["muffledCardBet"], "type": cards_type}
        self.callOtherClientsFunction("LookCard", _args)
        # 记录出牌步骤
        record = {}
        record["accountId"] = accountId
        # 相关类型置为 1
        record["operationType"] = 3
        # 操作  存储玩家看牌
        record["operationArgs"] = {"accountId": accountId}
        _chapter["operationRecord"].append(record)

    def compareCard(self, accountId, operatedAccountId):
        """
        比牌
        :param accountId: 发起比牌操作的玩家
        :param operatedAccountId: 被比牌的玩家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>compareCard accountId %s' % (self.id, accountId))
        _chapter = self.chapters[self.cn]
        _currentRound = _chapter["currentRound"]
        _playerInGame = _chapter["playerInGame"]
        self.delTimer(_chapter["operateTimerId"])
        _chapter["operateTimerId"] = -1
        # 1 下注的人
        compare_account = _chapter["playerInGame"][accountId]
        follow_bet_count = 0
        # 1 看过牌
        if compare_account["hasLookCard"]:
            follow_bet_count = _chapter["lookCardBet"] * 2 if self.info["compareCardDouble"] \
                else _chapter["lookCardBet"]
        else:
            follow_bet_count = _chapter["muffledCardBet"] * 2 if self.info["compareCardDouble"] \
                else _chapter["muffledCardBet"]
        # 1 下注成功
        drap_success = self.drop_bet(accountId, follow_bet_count)
        if not drap_success:
            self.callClientFunction(accountId, 'Notice', ['金币不足，无法进行比牌'])
            _chapter["currentLocationIndex"] -= 1
            self.changeOperation()
            return
        _cards1 = _playerInGame[accountId]["cards"]
        _cards2 = _playerInGame[operatedAccountId]["cards"]
        # 1 比牌结果
        _result = RoomType1Calculator.compare_card(_cards1, _cards2, self.info, is_manual_compare=True)
        _args = {"accountId": accountId, "operateAccountId": operatedAccountId, "result": _result}
        self.callOtherClientsFunction("CompareCard", _args)
        # _chapter["compareCardTimerId"] = self.addTimer(_timeCompareCardAnimation, 0, 0)
        # 记录出牌步骤
        record = {}
        record["accountId"] = accountId
        # 相关类型置为 1
        record["operationType"] = 4
        # 操作  存储玩家比牌
        record["operationArgs"] = {"accountId": accountId, "operatedAccountId": operatedAccountId, "result": _result}
        _chapter["operationRecord"].append(record)
        # 1 发起比牌的玩家赢
        if _result == 1:
            _chapter["currentLocationIndex"] -= 1
            self.disCard(operatedAccountId, is_settlement_compare_dis_card=False, is_compare_card_dis_card=True)
        # 1 被比牌的玩家赢
        elif _result == -1:
            self.disCard(accountId, is_settlement_compare_dis_card=False, is_compare_card_dis_card=True)

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
        _chapter["currentState"] = state
        self.callOtherClientsFunction("changeChapterState", {"state": int(state)})
        if state == 0:
            wait_to_seat_copy = self.wait_to_seat.copy()
            for k in wait_to_seat_copy:
                DEBUG_MSG(
                    '[Wait_to_seat]------>playerOutGame playerInGame setSeat setSeat accountId %s' % (k))
                if not self.emptyLocationIndex:
                    continue
                self.setSeat(k, self.emptyLocationIndex[0])
            # 1 准备开始  走之前的游戏逻辑
            # if self.info["gameStartType"] == 101:
            # 第一局之后自动准备
            if self.cn > 0:
                for k, v in _chapter["playerInGame"].items():
                    self.player_ready(k)
            _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
        elif state == 2:

            _chapter["settlementTimerId"] = self.addTimer(_timeSettlement, 0, 0)
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
        DEBUG_MSG('[Room id %i]------>playerOperation accountId %s ,jsonData %s' % (self.id, accountEntityId, jsonData))
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
        elif _func == "FollowEnd":
            self.followEnd(accountEntityId)
        elif _func == "DisCard":
            self.disCard(accountEntityId)
        elif _func == "LookCard":
            self.lookCard(accountEntityId)
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
            self.changeOperation()
        elif _func == "CompareCard":
            self.compareCard(accountEntityId, _data["operateAccountId"])
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

    def lastRoundRecord(self, accountId):
        """
        请求上局战绩
        :param accountId:
        :return:
        """
        _args = {}
        if self.cn == 0:
            pass
        else:
            _args = self.chapters[self.cn - 1]["chapterHistory"]
        self.callClientFunction(accountId, "LastRoundRecord", _args)

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
        _chapterInfo["totalBet"] = int(_chapter["totalBet"])
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
        # 闷牌底注
        _chapterInfo["muffledCardBet"] = _chapter["muffledCardBet"]
        # 看牌底注
        _chapterInfo["lookCardBet"] = _chapter["lookCardBet"]
        cards = {}
        # 1 玩家下注的集合  里面存放的是每个玩家的Id和对应的下注的列表
        bet_list = {}
        for k, v in _chapter["playerInGame"].items():
            cards[k] = v["cards"]
            bet_list[k] = v["betList"]
        _chapterInfo["betList"] = bet_list
        _chapterInfo["cards"] = cards
        _bet = 0
        if _player["hasLookCard"]:
            _bet = _chapter["lookCardBet"]
        else:
            _bet = _chapter["muffledCardBet"]
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
                card_type = RoomType1Calculator.type_of_cards(cards, self.info) if \
                    type(RoomType1Calculator.type_of_cards(cards, self.info)) == float or \
                    type(RoomType1Calculator.type_of_cards(cards, self.info)) == int else -1
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
                           "totalGoldChange": v["totalGoldChange"], "userId": v["entity"].info["userId"], "headImageUrl": v["entity"].info["headImageUrl"],
                           # "totalGold": v['gold'] + v['baseSyncGoldChange'] + v['totalGoldChange']  TODO----
                           "gold": v["score"],
                           "totalGold": v["score"] + v['totalGoldChange']
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
            cards_type = RoomType1Calculator.type_of_cards(cards, self.info) if \
                type(RoomType1Calculator.type_of_cards(cards, self.info)) == float or \
                type(RoomType1Calculator.type_of_cards(cards, self.info)) == int else -1
            _player = {"cards": v["cards"], "hasLookCard": v["hasLookCard"], "hasFollowCard": v["hasLookCard"],
                       "hasDisCard": v["hasDisCard"],   # 是否弃牌
                       "isCompareDisCard": v["isCompareDisCard"],
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
                _player = {"cards": v["cards"], "hasLookCard": v["hasLookCard"], "hasFollowCard": v["hasLookCard"],
                           "hasDisCard": v["hasDisCard"],  # 是否弃牌
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
        DEBUG_MSG('[Room id %i]------>onEnter accountId %s' % (self.id, accountEntityId))
        _chapter = self.chapters[self.cn]
        _account = KBEngine.entities[accountEntityId]
        _account.viewing_hall = False
        # 存入账户实体列表，相同实体不能重复登入房间
        if _account.id not in self.accountEntities.keys():
            self.accountEntities[_account.id] = _account
            DEBUG_MSG("on_enter account_entities:%s" % self.accountEntities)

        # E 新玩家
        _player = self.newPlayer(_account)
        if accountEntityId not in _chapter["playerInRoom"]:
            _chapter["playerInRoom"][accountEntityId] = _player
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
        else:
            DEBUG_MSG("onEnter-------> account %s on Enter room, but _player already exits" % accountEntityId)
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
            DEBUG_MSG('player_list  %s' % self.player_list)

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
            self.retChapterInfo(accountEntityId)
            _account.update_player_stage(Account.PlayerStage.WATCHING)
        #  1 房主开始房间的时候
        _playerInRoom = _chapter["playerInRoom"]

        if self.info["gameStartType"] == 101:
            self.player_list[0] = -1
        if self.info["gameStartType"] == 102:
            # 1 如果这个玩家是当时创建房间的那个玩家
            self.player_list[0] = -1
            if self.info["creator"] == _player["entity"].info["dataBaseId"]:
                DEBUG_MSG('wo shi chuang jian zhe %i' % self.info["creator"])
                _args = {"accountEntityId": accountEntityId}
                self.callClientFunction(accountEntityId, "ShowStartGame", _args)
        # 1 如果是首位开始可以点开始
        if self.info["gameStartType"] == 100:
            # 1 如果是可以开始游戏的玩家
            DEBUG_MSG('show start game %i' % self.player_list[0])
            if accountEntityId == self.player_list[0]:
                _args = {"accountEntityId": self.player_list[0]}
                self.callClientFunction(self.player_list[0], "ShowStartGame", _args)
        self.bots_ready()

    def retOutGamePlayerInfo(self, accountId=-1):
        _chapter = self.chapters[self.cn]
        _playerOutGameNotEntity = {}

        for k, v in _chapter["playerOutGame"].items():
            _player = {"cards": v["cards"], "hasLookCard": v["hasLookCard"], "hasFollowCard": v["hasLookCard"],
                       "hasDisCard": v["hasDisCard"],  # 是否弃牌
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
        DEBUG_MSG('[Room id %i]------>retPlayerInRoomInfos %s' % (self.id, _args))
        if accountId == -1:
            self.callOtherClientsFunction("RetOutGamePlayerInfo", _args)
        else:
            self.callClientFunction(accountId, "RetOutGamePlayerInfo", _args)

    def onPlayerClientDeath(self, accountEntity):
        """
        玩家非正常离开
        :return:
        """
        ""
        DEBUG_MSG("RoomType1 onPlayerClientDeath")
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
        DEBUG_MSG('[Room id %i]------>onLeave accountId %s' % (self.id, accountEntityId))
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
            #     DEBUG_MSG('wo zou dao zhe li le %i' % i)
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
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
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
                self.retOutGamePlayerInfo(k)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.retOutGamePlayerInfo(k)
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 从实体列表中移除
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
            DEBUG_MSG("onLeave account_entities:%s" % self.accountEntities)
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
        DEBUG_MSG('wo wow owo wow wowow wowow wowowowoowow')
        DEBUG_MSG('WWWWWWWWWWW-------%i' % accountEntityId)
        for k, v in _playerOutGame.items():
            DEBUG_MSG('WO SHIO KKKKKK ' % k)
        _player = _playerOutGame[accountEntityId]
        # 1 获取到下个玩家的位置
        next_locationindex = int(_player["locationIndex"] + 1)
        DEBUG_MSG('WWWWWWWWWWW-------%i' % next_locationindex)
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

    def onTimer(self, timerHandle, userData):
        """
        计时器回调
        :param timerHandle:
        :param userData:
        :return:
        """
        RoomBase.onTimer(self, timerHandle, userData)

        chapter = self.chapters[self.cn]
        _playerInGame = chapter["playerInGame"]
        if timerHandle == chapter["mainTimerId"]:
            all_ready = True
            for k, v in chapter["playerInGame"].items():
                if not v["isReady"]:
                    all_ready = False
                    break
            if all_ready and len(chapter["playerInGame"]) >= 2:
                list1 = [2, 4, 5, 6, 7, 8, 9, 10]
                if self.info["gameStartType"] in list1:
                    if len(chapter["playerInGame"]) >= self.info["gameStartType"]:
                        self.delTimer(timerHandle)
                        chapter["mainTimerId"] = -1
                        self.chapter_start()
                    else:
                        self.delTimer(timerHandle)
                        chapter["mainTimerId"] = -1
                else:
                    self.delTimer(timerHandle)
                    chapter["mainTimerId"] = -1
                    self.chapter_start()

        elif timerHandle == chapter["operateTimerId"]:
            chapter["operateTimerId"] = -1
            self.delTimer(chapter["operateTimerId"])
            DEBUG_MSG('[Room id %s]------>onTimer betTimerId %s' % (self.id, timerHandle))
            _currentLocationIndex = chapter["currentLocationIndex"]
            _playerInGameCopy = chapter["playerInGame"].copy()
            for k, v in _playerInGameCopy.items():
                if int(v["locationIndex"]) == int(_currentLocationIndex):
                    self.disCard(k)
        elif timerHandle == chapter["betAnimationTimerId"]:
            DEBUG_MSG('[Room id %s]------>onTimer betAnimationTimerId %s' % (self.id, timerHandle))
            chapter["betAnimationTimerId"] = -1
            chapter["seatAnimationTimerId"] = self.addTimer(_timeSeatAnimation, 0, 0)
        elif timerHandle == chapter["seatAnimationTimerId"]:
            DEBUG_MSG('[Room id %s]------>onTimer seatAnimationTimerId %s' % (self.id, timerHandle))
            chapter["seatAnimationTimerId"] = -1
            self.dealCards()
            self.changeOperation()
        elif timerHandle == chapter["settlementTimerId"]:
            DEBUG_MSG('[Room id %s]------>onTimer settlementTimerId %s' % (self.id, timerHandle))
            chapter["settlementTimerId"] = -1
            self.delTimer(timerHandle)
            self.chapterRestart()
            self.changeChapterState(0)
        elif timerHandle == chapter['toToTalSettlementTime']:
            chapter["toToTalSettlementTime"] = -1
            self.delTimer(timerHandle)
            self.total_settlement()
            self.write_chapter_info_to_db()
        # elif timerHandle == chapter["accountLottery"]:
        #     DEBUG_MSG('[Room id %s]------>onTimer accountLottery %s' % (self.id, timerHandle))
        #     chapter["accountLottery"] = -1
        #     self.Lottery()

        # elif timerHandle == chapter["compareCardTimerId"]:
        #     DEBUG_MSG('[Room id %s]------>onTimer compareCardTimerId %s' % (self.id, timerHandle))
        #     if len(self.getHasNoDisCardPlayer()) > 1:
        #         self.changeOperation()
        elif timerHandle == chapter["botTimerId"]:
            chapter["botTimerId"] = -1
            self.delTimer(timerHandle)
            _range = random.randint(0, 10)
            _currentLocationIndex = chapter["currentLocationIndex"]
            _accountId = -1

            for k, v in _playerInGame.items():
                if v["locationIndex"] == _currentLocationIndex:
                    _accountId = k
                    break

            if _range < 3:
                # 看牌
                self.lookCard(_accountId)
            _range = random.randint(0, 100)
            # if _range < 3:
            #     self.disCard(_accountId)
            #
            # elif 4 < _range < 7:
            #     # 比牌
            #
            #     if self.info['compareCardRound'] <= chapter['currentRound']:
            #         accountId = 0
            #         while True:
            #             accountId = random.choice(list(self.getHasNoDisCardPlayer().keys()))
            #             if accountId != _accountId:
            #                 break
            #         self.compareCard(_accountId, accountId)
            #
            #         type = random.randint(1, 2)
            #         if type == 1:
            #             self.disCard(_accountId)
            #         else:
            #             if _playerInGame[_accountId]["hasLookCard"]:
            #                 _bet = chapter["lookCardBet"]
            #             else:
            #                 _bet = chapter["muffledCardBet"]
            #             self.drop_bet(_accountId, _bet)
            #             self.changeOperation()
            if _range <= 50:
                _bet = 100
                if _playerInGame[_accountId]["hasLookCard"]:
                    _bet = chapter["lookCardBet"]
                else:
                    _bet = chapter["muffledCardBet"]
                if _range < 30:
                    self.addBet(_accountId, _bet)
                elif 30 < _range <= 35:
                    self.disCard(_accountId)
                elif 35 < _range < 50:
                    # 比牌
                    if self.info['compareCardRound'] <= chapter['currentRound'] and chapter['currentRound'] > 2:
                        accountId_random = 0
                        for i in range(10):
                            accountId_random = random.choice(list(self.getHasNoDisCardPlayer().keys()))
                            if accountId_random != _accountId:
                                break
                        self.compareCard(_accountId, accountId_random)
                    else:
                        _bet = 100
                        if _playerInGame[_accountId]["hasLookCard"]:
                            _bet = chapter["lookCardBet"]
                        else:
                            _bet = chapter["muffledCardBet"]
                        self.drop_bet(_accountId, _bet)
                        self.changeOperation()

            else:
                _bet = 100
                if _playerInGame[_accountId]["hasLookCard"]:
                    _bet = chapter["lookCardBet"]
                else:
                    _bet = chapter["muffledCardBet"]
                self.drop_bet(_accountId, _bet)
                self.changeOperation()
        elif timerHandle == chapter["settlementClearPlayers"]:
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
            title = '炸金花房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '炸金花房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '炸金花房间'
        max_round = '最大轮数：' + str(self.info['maxRound'])
        look_card_round = '闷牌轮数' + str(self.info['lookCardRound'])
        max_chapter_count = '最大玩家数量:' + str(self.info['maxChapterCount'])
        bet_base = '底注:' + str(self.info['betBase'])
        if 'canVoice' in self.info:
            can_voice = '语音开启' if self.info['canVoice'] else '禁用语音'
        else:
            can_voice = ''
        con = str('%s,%s,%s,%s,%s' % (max_round, look_card_round, max_chapter_count, bet_base, can_voice))
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
        chapter["botTimerId"] = -1
        self.delTimer(chapter["botTimerId"])
        chapter["compareCardTimerId"] = -1
        self.delTimer(chapter["compareCardTimerId"])
        chapter['toToTalSettlementTime'] = -1
        self.delTimer(chapter["toToTalSettlementTime"])
        self.disband_timer = -1
        self.delTimer(self.disband_timer)

    # 总结算
    def total_settlement(self):
        if self.total_settlement_ed:   # TODO total_settlement_ed 总结算标志位  False未结算 True已结算
            return
        self.close_all_timer()
        self.changeChapterState(3)
        self.total_settlement_ed = True  # TODO 设置已经结算
        chapter = self.chapters[self.cn]
        # self.started = False
        # 抽奖

        if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
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
        if len((self.player_leave_info)) >0:
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
        game_type = '炸金花'
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
