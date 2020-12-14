# -*- coding: utf-8 -*-
import copy
import json
import random
import time

import Const
import KBEngine
import Util
import math
from KBEDebug import DEBUG_MSG

import RoomType13Calculator
from RoomBase import RoomBase
import Account

# 准备倒计时时间
_timeReady = 5
# 发牌动画时间
_timeDealCardToPlayer = 3
# 定庄动画 or
_timeHadLocalPlans = 1
# 展示最后一张牌
_timeShowLastOne = 1
# 展示剩余手牌时间
_timeShowCard = 3
# 出牌时间
play_card_time = 15
# 离线出牌时间 or 过牌
# play_card_time_onKill = 1
WAIT_TIME_LEN_ON_PLAY_OFFLINE = 1
# 小结算时间
settlement_time = 2
# 大结算时间
total_settlement_time = 20
# 解散房间倒计时
time_disband = 30
# 总结算清理玩家倒计时
settlement_clear_players_time = 30


class RoomType13(RoomBase):
    # 牌局信息
    _chapterInfos = {}
    # 总结算设置位
    total_settlement_ed = False
    # 结算次数
    settlement_count = 0
    # 牌局是否开始
    started = False
    # 2人位剩下一个不操纵位手牌
    OtherCardPlan = []
    # 房间初始化
    InitRoom = -1
    # 房间座位
    emptyLocationIndex = []
    # 游戏获胜者
    gameWinner = -1
    disband_timer = -1

    # 初始化继承父类属性及自身属性
    def __init__(self):
        """
        # 房间所有用户实体
         ................
        # 全局统计数据
        """
        RoomBase.__init__(self)
        # 随机生成空位
        self.InitRoom = 1
        self.play_card_time = 15
        # 观战中的下局可以开始坐下的玩家
        self.wait_to_seat = []

    # =================================================================================================================
    #                                    牌局状态机和计时器驱动
    # =================================================================================================================

    # 牌局状态机，根据状态执行流程（待优化）
    def changeChapterState(self, state):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _chapter["currentState"] = state  # 当前房间状态
        # 牌局准备状态
        if state == 0:
            _args = {"state": state, "Timer": 0}
            if self.cn != 0:
                _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
            wait_to_seat_copy = self.wait_to_seat.copy()
            for k in wait_to_seat_copy:
                if len(self.emptyLocationIndex) != 0:
                    self.set_seat(k, self.emptyLocationIndex[0])
            self.callOtherClientsFunction("changeChapterState", _args)
            # 玩家自动准备
            self.auto_ready_for_player_in_game()
        # 牌局开始、发牌状态
        elif state == 1:
            self.set_current_round(self.cn + 1)  # self.cn 当前局数下标
            _args = {"state": state, "Timer": _timeDealCardToPlayer}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 发牌
            self.make_card_and_send_on_start()
        # 牌局定庄（先出牌的玩家）
        elif state == 2:
            _args = {"state": state}
            self.callOtherClientsFunction("changeChapterState", _args)
            call_type = self.get_first_out_card_pos()
            self.send_info_to_clients_fun(call_type)
        # 牌局出牌正常流程
        elif state == 3:
            _args = {"state": state}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 通知玩家出牌
            self.change_play_card_player(_chapter["startAccountId"])
        # 结算
        elif state == 4:
            _args = {"state": state}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 发送结算信息设置定时器
            self.settlement()
            # for k, v in _chapter["playerInGame"].items():
            #     DEBUG_MSG("%s 结算完毕 开始准备 " % str(k))
            #     self.player_ready(k)
                # 结算信息没有自动准备
            # 如果超过局数，总结算。锅子模式没有局数限制
            if not self.pot and self.settlement_count >= self.info["maxChapterCount"]:
                self.changeChapterState(5)
                return
            # 如果比赛场有人不满足离场分，结束游戏
            elif self.info["roomType"] == "gameCoin" and self.have_player_do_not_meet_end_score():
                self.changeChapterState(5)
                return
            else:
                # 整理结算信息
                self.cl_card_chapter()
               # self.chapter_clear()
        # 大结算
        elif state == 5:
            _args = {"state": state}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 结算
            self.set_time_for_total()

    # 计时器
    def onTimer(self, timer_handle, user_data):
        DEBUG_MSG(timer_handle)
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInGame = _chapter["playerInGame"]
        # 发牌动画完成以后切换牌局状态机状态
        if timer_handle == _chapter["dealCardAnimationTimerId"]:
            # 删除定时间
            self.delTimer(timer_handle)
            # 初始化发牌时间
            _chapter["dealCardAnimationTimerId"] = -1
            # 切换定庄状态
            self.changeChapterState(2)

        # 定庄计时器
        elif timer_handle == _chapter["setPosAnimationTimerId"]:
            # 删除定时间
            self.delTimer(timer_handle)
            # 初始化定庄时间
            _chapter["setPosAnimationTimerId"] = -1
            # 切换牌局流程状态
            self.changeChapterState(3)

        # 出牌计时器
        elif timer_handle == _chapter["playCardTimer"]:
            self.delTimer(timer_handle)
            _chapter["playCardTimer"] = -1

            # 自动托管
            account_id = _chapter["currentPlayer"]
            if _playerInGame[account_id]["allowAutoPlayCheck"]:
                self.start_auto_play(account_id)

            # 如果出牌倒计时结束（玩家手中可能有大于上家的牌，拖时间）
            self.get_info_and_change_player(_chapter["currentPlayer"])

        # 展示剩余手牌
        elif timer_handle == _chapter["showCardTime"]:
            self.delTimer(timer_handle)
            _chapter["showCardTime"] = -1
            # 切换牌局流程状态
            self.changeChapterState(4)

        # 小结算
        elif timer_handle == _chapter["settlementTimer"]:
            self.delTimer(timer_handle)
            _chapter["settlementTimer"] = -1
            if not self.pot and self.settlement_count >= self.info["maxChapterCount"]:  # self.cn 当前局数下标
                pass
            else:
                self.chapter_clear()
                self.changeChapterState(0)

        # 判断游戏是否开始
        elif timer_handle == _chapter["mainTimerId"]:
            if self.is_all_player_ready_ok():
                self.delTimer(timer_handle)
                _chapter["mainTimerId"] = -1
                self.chapter_start()
                # 改变牌局状态机状态(流程移交状态机)
                self.changeChapterState(1)

        elif timer_handle == _chapter["showLastTime"]:
            self.delTimer(timer_handle)
            _chapter["showLastTime"] = -1
            self.showCards()
        elif timer_handle == _chapter["settlementClearPlayers"]:
            _chapter["settlementClearPlayers"] = -1
            self.delTimer(_chapter["settlementClearPlayers"])
            # 清理游戏中的玩家
            _playerInGameCopy = _chapter["playerInGame"].copy()
            for k, v in _playerInGameCopy.items():
                self.kick_out(k)
            # 清理观战的玩家
            _playerOutGameCopy = _chapter["playerOutGame"].copy()
            for k, v in _playerOutGameCopy.items():
                self.kick_out(k)

        elif timer_handle == self.disband_timer:
            self.disband_timer = -1
            self.delTimer(timer_handle)
            self.changeChapterState(5)

        elif timer_handle == self.ready_gold_disband_timer:
            self.delTimer(self.ready_gold_disband_timer)
            self.ready_gold_disband_timer = -1
            if not self.is_forbid_disband_room():
                self.debug_msg('onTimer ready_gold_disband_timer %s' % timer_handle)
                all_can_ready = self.check_ready_gold_disband()
                # 如果有人仍不满足条件，解散房间
                if not all_can_ready:
                    self.debug_msg("not all_can_ready disband")

                    # 投票解散
                    self.is_manual_disband = True
                    self.disband_timer = -1
                    self.delTimer(self.disband_timer)
                    self.is_disbanding = False
                    args = {"result": 1}
                    self.callOtherClientsFunction("DisbandRoomResult", args)
                    self.changeChapterState(5)

    # ================================================================================================================
    #                                          游戏流程辅助函数
    # ================================================================================================================
    # 当有玩家进入房间
    def onEnter(self, accountEntityId):
        """
        E玩家进入
        """
        # 初始化位置
        if self.InitRoom == 1:
            self.emptyLocationIndex = list(range(0, self.info["maxPlayersCount"]))
            self.InitRoom = -1
            self.play_card_time = self.info["autoCompareTime"]

        # 判定牌局是否开始，是否允许观战
        if not RoomBase.onEnter(self, accountEntityId):
            return
        # 获取当前局数信息
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息 self.cn 当前局数下标
        # 如果当前人数已满，将玩家踢出
        # if len(_chapter["playerInRoom"]) >= self.info["maxPlayersCount"] and \
        #         accountEntityId not in _chapter["playerInRoom"] and accountEntityId not in _chapter["playerOutGame"]:
        #     DEBUG_MSG("have more player in the game")
        #     return
        # 获取此玩家的实体信息
        _account = KBEngine.entities[accountEntityId]
        _account.viewing_hall = False
        # 此玩家不在实体列表中
        if _account.id not in self.accountEntities.keys():
            # 将玩家加入列表
            self.accountEntities[_account.id] = _account
        # 生成一个玩家
        _player = self.newPlayer(_account)
        # 如果不在玩家列表里  说明是新玩家
        if accountEntityId not in _chapter["playerInRoom"]:
            # 将新玩家加入列表
            _chapter["playerInRoom"][accountEntityId] = _player
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
        else:
            # 玩家进入，返回
            DEBUG_MSG("have err have some accountEntityId had in：%s" % accountEntityId)
            return
        _chapter["playerOutGame"][accountEntityId] = _player
        # 向玩家发送房间信息（此方法客户端必须存在）
        self.retRoomBaseInfo(accountEntityId)
        # 向玩家发送当前的牌局状态
        self.send_chapter_state(accountEntityId)
        # 如果当前的牌局在准备状态，牌局还未开始，座位还未坐满
        if _chapter["currentState"] == 0 and not self.started and len(self.emptyLocationIndex) != 0:  # 当前房间状态
            if len(_chapter["playerInGame"]) < self.info["maxPlayersCount"]:
                self.set_seat(accountEntityId, self.emptyLocationIndex[0])
                _account.update_player_stage(Account.PlayerStage.NO_READY)
                self.notify_viewing_hall_players_room_info()
        # 有观战玩家进入
        else:
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.ret_out_game_player_info(k)
            # 1 给进入的玩家发送所有玩家信息
            self.ret_player_in_room_info(accountEntityId)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.ret_out_game_player_info(k)
            # 给进入的玩家发送牌局信息（或者重连玩家）
            self.ret_chapter_info(accountEntityId)
            # 更新玩家的游戏阶段 观战、未准备、已准备、游戏中
            _account.update_player_stage(Account.PlayerStage.WATCHING)

    # 玩家进入房间后点击准备
    def player_ready(self, account_id, bReady=True):
        """
        E玩家准备
        E准备
        """
        # 获取牌局信息
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 拿到牌局玩家信息
        _player = chapter["playerInGame"][account_id]
        # 如果是比赛场,准备时金币不能小于0
        if self.info["roomType"] == "gameCoin" and _player['gold'] < self.info['readyGoldLimit'] and bReady:
            self.callClientFunction(account_id, 'Notice', ['您的比赛分不足,请您立即充值.'])
            info_args = {"accountId": account_id}
            self.callOtherClientsFunction("ScoreIsLess", info_args)
            if self.ready_gold_disband_timer == -1 and not self.is_forbid_disband_room():
                self.debug_msg("addTimer ready_gold_disband_timer")
                self.ready_gold_disband_timer = self.addTimer(120, 0, 0)
            return
        # 判断房间限制
        # if self.have_gold_limit() and _player["gold"] < self.info["gameLevel"]:
        #     return
        if self.have_gold_limit() and _player['gold'] <= -100 and bReady:
            self.callClientFunction(account_id, 'Notice', ['比赛分不足'])
            return
        if self.is_gold_session_room() and _player['gold'] < self.info['roomRate'] and bReady:
            return
        # 玩家准备
        chapter["playerInGame"][account_id]["ready"] = bReady
        # 发送给房间内玩家准备消息
        _args = {"accountId": account_id, "ready": bReady}
        # 向客户端发送房间内玩家准备消息
        self.callOtherClientsFunction("Ready", _args)

    def want_next_game_seat(self, account_id):
        """
        观战中下局可以开始游戏的玩家
        :param account_id:
        :return:
        """
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息 self.cn 当前局数下标
        # 1 在房间中的人
        _playerInRoom = chapter["playerInRoom"]
        # 1 在游戏中的人
        _playerInGame = chapter["playerInGame"]
        # 1 游戏中观战的人
        _playerOutGame = chapter["playerOutGame"]
        if account_id not in _playerOutGame:
            return
        if _playerOutGame[account_id]['gold'] < self.info['gameLevel']:
            self.callClientFunction(account_id, 'Notice', ['比赛币不足，无法坐下'])
            return
        if self.have_gold_limit() and _playerOutGame[account_id]['gold'] <= 0:
            self.callClientFunction(account_id, 'Notice', ['比赛币不足，无法坐下'])
            return
        if account_id in _playerOutGame:
            # 已经坐下
            if account_id in self.wait_to_seat:
                _args = {"result": 1}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                self.callOtherClientsFunction("NextGameCanSit", self.wait_to_seat)
                return
            if len(self.emptyLocationIndex) > len(self.wait_to_seat):
                _args = {"result": 1}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                self.wait_to_seat.append(account_id)
                self.callOtherClientsFunction("NextGameCanSit", self.wait_to_seat)
                self.get_player_entity(account_id).update_player_stage(Account.PlayerStage.PLAYING,
                                                                       self.max_chapter_count,
                                                                       self.current_chapter_count)
            else:
                _args = {"result": 0}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                return

    # 游戏开始时信息处理（处理以后由状态机控制游戏流程）
    def chapter_start(self):
        # 将房间状态修正为开始
        self.started = True
        self.info["started"] = True
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息 self.cn 当前局数下标
        # 获取当前所有牌局玩家信息
        _playerInGame = chapter["playerInGame"]
        # 金币场扣除房费
        DEBUG_MSG("将房间状态修正为开始")
        DEBUG_MSG(self.is_gold_session_room())
        DEBUG_MSG(self.info['level'])
        if self.is_gold_session_room():
        # if self.info["roomType"] == "gameCoin":
            DEBUG_MSG("开始扣除房费----->")
            DEBUG_MSG(_playerInGame.items)
            for k, v in _playerInGame.items():
                DEBUG_MSG("--玩家 %s  gold %s 房费 %s" % (str(v['entity'].info['name']), v['gold'], self.info['roomRate']))
                v['gold'] -= self.info['roomRate']
                DEBUG_MSG("--玩家 %s  gold %s 房费 %s" % (str(v['entity'].info['name']), v['gold'], self.info['roomRate']))
                self.set_base_player_gold(k)  # 设置玩家金币数量

        # 起始局
        if self.cn == 0:  # self.cn 当前局数下标
            # 将坐下玩家的数据库ID发送到base用于更新房间状态给客户端
            player_in_game_db_id = []
            for k, v in self.chapters[self.cn]["playerInGame"].items():  # 遍历玩家
                player_in_game_db_id.append(v["entity"].info["dataBaseId"])  # 添加玩家id到列表
                # 游戏阶段 PLAYING 游戏开始
                self.player_entity(v).update_player_stage(Account.PlayerStage.PLAYING, self.max_chapter_count,
                                                          self.current_chapter_count)
            # 通知客户端返回房间
            self.notify_viewing_hall_players_chapter_start()
            self.base.cellToBase(
                {"func": "roomStart",
                 "roomInfo": self.info,
                 "playerInGameDBID": player_in_game_db_id}
            )
            # 房间开始，并且人未满时创建新的房间(onRoomEnd为true时插入在当前房间后面)
            if len(_playerInGame) < self.info['maxPlayersCount']:
                # 通知客户端自动创建房间
                self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})
        # 通知通知客户端创建牌局
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})  # self.cn 当前局数下标

    # 生成一个牌局内玩家信息
    def newPlayer(self, accountEntity):
        # 获取当前的游戏牌局信息
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息 self.cn 当前局数下标
        # 牌局玩家信息字典
        _player = {}
        # 准备
        _player["ready"] = False
        # 实体
        _player["entity"] = accountEntity
        # 牌
        _player["cards"] = []
        # 出过的牌
        _player["playedCards"] = []
        # 单局最高输赢
        _player["singMax"] = 0
        # 已出的全部牌
        _player["outCardList"] = {}
        # 座位
        _player["locationIndex"] = -1
        # 在线状态
        _player["online"] = True
        # 1 是否扣除钻石标志位
        _player['AARoomCardConsumed'] = False
        # 牌型
        _player["cardType"] = -1
        # 本局金币变化
        _player["goldChange"] = 0
        # 总金币变化
        _player["totalGoldChange"] = 0
        # 大赢家扣费
        _player["winnerBilling"] = 0
        # 其余玩家扣费
        _player["otherBilling"] = 0
        # 超额扣费
        _player["overBilling"] = 0
        # 总炸弹个数
        _player["totalBoomCounts"] = 0
        # 出的炸弹个数
        _player["boomCount"] = 0
        # 玩家基本输赢分
        _player["basicScore"] = 0
        # 玩家基本分小局
        _player["basicScoreChange"] = 0
        # 玩家炸弹分
        _player["boomScores"] = 0
        # 玩家炸弹分小局
        _player["boomScoresChange"] = 0
        # 是否全关
        _player["overCardLift"] = False
        # 钻石场默认为0，金币场使用的是大厅金币，比赛分场使用的是账户再朋友圈的比赛分
        if self.info["roomType"] == "card":
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        elif self.info["roomType"] == "gameCoin":
            _player["gold"] = accountEntity.accountMutableInfo["gameCoin"]
            # 如果是锅子模式，分数等于锅子分
            if self.pot:
                _player['gold'] = self.potScore
        elif self.info["roomType"] == "normalGameCoin":
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 1 同意解散
        _player["agreeDisband"] = False
        # 出牌次数
        _player["playCount"] = 0
        # 是否继续
        _player["goToNext"] = False
        # 身份 庄：1 普通：0
        _player["identity"] = 0
        # 1 是好友   0不是好友
        _player["isFriend"] = -1
        # 玩家的操作参数  0默认不操作
        _player["operation_args"] = 0
        _player["winCount"] = 0
        _player["lostCount"] = 0
        # 连败次数
        _player["losingstreak"] = 0
        # 自动出牌
        _player["autoPlayCard"] = False
        _player["allowAutoPlayCheck"] = False
        return _player

    # 生成一个新牌局
    def newChapter(self, maxPlayerCount):
        _chapter = {}
        # operationType:1，庄家相关，2，出牌相关  0, 发牌相关
        _chapter["operationRecord"] = []
        # 回放需要用到的剩余牌
        _chapter['recordCards'] = {}
        # 最大回合
        _chapter["maxChapterCount"] = self.info["maxChapterCount"]
        # 创建房间时刻
        _chapter["createRoomTime"] = self.info["createRoomTime"]
        # 金币场等级
        _chapter["level"] = self.info["level"]
        # 最大玩家数量
        _chapter["maxPlayerCount"] = maxPlayerCount
        # 当前轮数
        _chapter["currentRound"] = 0
        # 当前房间状态
        _chapter["currentState"] = 0  # 当前房间状态
        # 当前操作玩家位置
        _chapter["currentLocationIndex"] = -1
        # 解散清除玩家倒计时
        _chapter["settlementClearPlayers"] = -1
        # 轮询是否可以开始牌局计时器
        _chapter["mainTimerId"] = -1
        # 轮询是否继续计时器
        _chapter["goToNext"] = -1
        _chapter["showLastTime"] = -1
        # 牌局开始倒计时计时器
        _chapter["chapterStartTimerId"] = 0
        # 发牌计时器
        _chapter["dealCardAnimationTimerId"] = -1
        # 定庄动画计时器
        _chapter["setPosAnimationTimerId"] = -1
        # 出牌计时器
        _chapter["playCardTimer"] = -1
        # 展示剩余牌
        _chapter["showCardTime"] = -1
        # 结算计时器
        _chapter["settlementTimer"] = -1
        # 位置交换计时器
        _chapter["seatAnimationTimerId"] = -1
        # 当前计时时刻点
        _chapter["deadline"] = -1
        # 倍数
        _chapter["multiple"] = 1
        # 游戏内玩家
        _chapter["playerInGame"] = {}
        # 游戏外玩家
        _chapter["playerOutGame"] = {}
        # 房间内所有玩家
        _chapter["playerInRoom"] = {}
        # 牌库
        _chapter["cardsLib"] = []
        # 牌局历史
        _chapter["chapterHistory"] = {}
        # 开始玩家下标
        _chapter["startLocationIndex"] = -1
        # 开始玩家Id
        _chapter["startAccountId"] = -1
        # 上个出牌玩家 id
        _chapter["prePlayer"] = -1
        # 上个出牌玩家出的牌
        _chapter["prePlayerPlayCards"] = []
        # 抢庄结果
        _chapter["OverLocalOutCard"] = -1
        # 当前操作玩家
        _chapter["currentPlayer"] = -1
        # 胜者
        _chapter["winner"] = -1
        # 底分
        _chapter["baseScore"] = self.info["baseScore"]
        # 炸弹封顶
        _chapter["BoomScore"] = self.info["boomScore"]
        # 炸弹个数
        _chapter["boomCount"] = 0
        # 抽奖
        _chapter["accountLottery"] = -1
        # 聊天记录
        _chapter["chatHistory"] = []
        # 战绩
        _chapter["roomRecord"] = {}
        # 房间内最大炸弹玩家Id
        _chapter["max_boom_player"] = -1
        # 最大炸弹牌型
        _chapter["max_boom"] = []
        # 把赢家放走的人
        _chapter['letPlayer'] = -1
        self.chapters.append(_chapter)  # self.chapters 牌局信息
        self.cn = len(self.chapters) - 1  # self.chapters 牌局信息  self.cn 当前局数下标

        return _chapter

    @property
    def is_less_mode(self):
        """
        是否少人模式
        """
        if not self.info['fewPersonPattern']:  # fewPersonPattern 少人模式
            return False
        if self.started:  # 未开始
            return True
        chapter = self.get_current_chapter()  # 获取当前牌局
        players = chapter['playerInGame']  # 获取当前游戏玩家
        if len(players) == len(self.agree_less_person_mode_players):  # agree_less_person_mode_players 同意少人模式的玩家
            return True
        return False

    # 给坐下玩家发送观战玩家信息
    def ret_out_game_player_info(self, accountId=-1):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerOutGameNotEntity = {}
        for k, v in _chapter["playerOutGame"].items():
            _player = {
                "cards": v["cards"],
                "playedCards": v["playedCards"],
                "gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                "userId": v["entity"].info["userId"],
                "ip": v["entity"].info["ip"],
                "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                "addOn": v["entity"].info["addOn"],
                "ready": v["ready"]
            }
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerOutGame": _playerOutGameNotEntity}
        if accountId == -1:
            self.callOtherClientsFunction("RetOutGamePlayerInfo", _args)
        else:
            self.callClientFunction(accountId, "RetOutGamePlayerInfo", _args)

    # 重连时发送当前牌桌信息或者发送给观战玩家信息
    def ret_chapter_info(self, account_id):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        play_in_game = chapter["playerInGame"]
        # 剔除不存在房间里的人
        for _entity_id in self.wait_to_seat:
            if _entity_id not in chapter['playerOutGame']:
                self.wait_to_seat.remove(_entity_id)

        have_bigger = False
        if chapter["currentPlayer"] == account_id:
            have_bigger = self.have_big_in_player(account_id)
        chapter_info = {"currentRound": int(chapter["currentRound"]),
                        "prePlayerPlayCards": self.change_value_to_client(chapter["prePlayerPlayCards"]),
                        "deadline": int(chapter["deadline"]) - int(time.time()), "prePlayer": int(chapter["prePlayer"]),
                        "currentState": int(chapter["currentState"]), "currentPlayer": int(chapter["currentPlayer"]),
                        # 当前房间状态
                        "prePlayerPlayCardsType": RoomType13Calculator.get_cards_type(
                            chapter["prePlayerPlayCards"], self.info).value, "started": self.info["started"],
                        "disbandSender": self.disband_sender, "isDisbanding": self.is_disbanding,
                        "canStartGame": self.wait_to_seat, "banker": int(chapter["startAccountId"]),
                        "canOut": have_bigger,
                        "canPass": not self.info["haveCardMustCome"]
                        }
        _playerData = {}
        for k, v in play_in_game.items():
            _playerData[k] = {"cards": self.change_value_to_client(v["cards"]),
                              "ready": v["ready"],
                              "agreeDisband": v["agreeDisband"],
                              "name": v["entity"].info["name"]
                              }
        chapter_info["playerData"] = _playerData
        self.callClientFunction(account_id, "Reconnect", chapter_info)

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

    # 坐下
    def set_seat(self, accountId, locationIndex):
        """
        设置座位
        :param accountId: 设置座位玩家
        :param locationIndex: 座位号0-2或者0-3
        :return:
        """
        DEBUG_MSG('[Room id %i]------>setSeat accountId %s, locationIndex %s ' % (self.id, accountId, locationIndex))
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        if accountId not in _chapter["playerOutGame"]:
            return
        for player in _chapter["playerInGame"].values():
            if player["locationIndex"] == locationIndex:
                return
        _chapter["playerInGame"][accountId] = _chapter["playerOutGame"][accountId]
        _chapter["playerOutGame"].pop(accountId)
        _chapter["playerInGame"][accountId]["locationIndex"] = locationIndex
        _player = _chapter["playerInGame"][accountId]
        _args = {"accountId": accountId, "locationIndex": locationIndex,
                 "name": _player["entity"].info["name"], "gold": _player["gold"]}
        # self.callOtherClientsFunction("SetSeat", _args)
        self.emptyLocationIndex.remove(locationIndex)
        # # 从等待坐下中移除
        if accountId in self.wait_to_seat:
            self.wait_to_seat.remove(accountId)
        # 广播房间内所有玩家的信息
        self.ret_player_in_room_info()
        # 更新玩家数量
        self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 每人满时，创建新的房间(onRoomEnd为true时插入在当前房间后面)
        if len(_chapter['playerInGame']) == self.info['maxPlayersCount']:
            self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})

    # 广播房间内所有玩家状态
    def ret_player_in_room_info(self, accountId=None):
        """

        :return:广播房间内所有玩家状态
        """
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInGameNotEntity = {}
        _playerOutGameNotEntity = {}
        player_in_game_to_base = {}
        for k, v in _chapter["playerInGame"].items():
            _player = {"cards": self.change_value_to_client(v["cards"]),
                       "playedCards": self.change_value_to_client(v["playedCards"]),
                       "gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                       "addOn": v["entity"].info["addOn"],
                       "ready": v["ready"],
                       'agreeLessMode': v["entity"].id in self.agree_less_person_mode_players,
                       'totalGoldChange': v['totalGoldChange'],
                       "onLine": not v['entity'].client_death,
                       "startAutoPlay": v["autoPlayCard"]
                       }
            player_in_game_to_base[int(v["locationIndex"])] = {"name": v["entity"].info["name"],
                                                               "databaseId": v["entity"].info["dataBaseId"],
                                                               "headImageUrl": v["entity"].info["headImageUrl"]}
            _playerInGameNotEntity[int(k)] = _player
        for k, v in _chapter["playerOutGame"].items():
            _player = {"cards": self.change_value_to_client(v["cards"]),
                       "playedCards": self.change_value_to_client(v["playedCards"]),
                       "gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                       "addOn": v["entity"].info["addOn"],
                       'totalGoldChange': v['totalGoldChange'],
                       "ready": v["ready"]}
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerInGame": _playerInGameNotEntity, "playerOutGame": _playerOutGameNotEntity}
        if accountId is None:
            self.callOtherClientsFunction("RetPlayerInRoomInfos", _args)
        else:
            self.callClientFunction(accountId, "RetPlayerInRoomInfos", _args)
        tea_house_id = -1
        if self.is_tea_house_room:
            tea_house_id = self.info['teaHouseId']
        self.base.cellToBase({"func": "refreshPlayerInGame", "playerInGame": player_in_game_to_base,
                              "teaHouseId": tea_house_id})

    # 生成牌并且发送
    def make_card_and_send_on_start(self):
        """
        E发牌
        """
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # _playerInGame = _chapter["playerInGame"]
        # if len(_playerInGame) != self.info["maxPlayersCount"]:
        #     DEBUG_MSG('player count is error: % i' % len(_playerInGame))
        #     return
        self.send_shou_cards_to_player()
        # 播放发牌动画计时器
        _chapter["dealCardAnimationTimerId"] = self.addTimer(_timeDealCardToPlayer, 0, 0)
        _chapter["deadline"] = time.time() + _timeDealCardToPlayer

    def set_base_player_banker_history2(self, chapter):
        """
        坐庄信息也同步到BASE
        进入牌局定庄之后到结算完成之前调用
        因为这段时间chapter["playerInGame"]、chapter["banker"]才存在
        """
        # chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if k == chapter["startAccountId"]:
                v["entity"].base.cellToBase({"func": "AppendBankerHistory", "banker": 1})
                v['entity'].info['bankerHistory'].append(1)
            else:
                v["entity"].base.cellToBase({"func": "AppendBankerHistory", "banker": 0})
                v['entity'].info['bankerHistory'].append(0)

    # 获取第一个出牌玩家的accountid 并设置出牌身份
    def get_first_out_card_pos(self):
        self.base.cellToBase({"func": "changeRoomState", "roomState": 1})
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 牌局出牌的第一个玩家
        chapter["startAccountId"] = -1
        # 出牌玩家结果类型通知前端的值
        over_result = -1
        # 赢家先出
        if self.info["outCradType"] == 1:
            # 如果是第一局，随便拿到第一个人
            if self.cn == 0:  # self.cn 当前局数下标
                over_result = 0
                chapter["startAccountId"] = self.banker_area_random(list(chapter["playerInGame"].keys()))
                self.set_base_player_banker_history2(chapter)
            else:
                over_result = 100
                # 确保gameWinner真实存在
                chapter["startAccountId"] = self.gameWinner
                self.gameWinner = -1
        # 随机庄
        if self.info["outCradType"] == 20:
            # 随机第一个人
            over_result = 0
            chapter["startAccountId"] = self.banker_area_random(list(chapter["playerInGame"].keys()))
            self.set_base_player_banker_history2(chapter)
        # 红桃3先出
        if self.info["outCradType"] == 12:
            # 获取有红桃3的玩家id
            for k, v in chapter["playerInGame"].items():
                if self.get_card_value_for_want(v["cards"], 3.3):
                    chapter["startAccountId"] = k
                    over_result = 12
            # 找到最小牌玩家Id
            if chapter["startAccountId"] == -1:
                chapter["startAccountId"] = self.find_min_card()
                over_result = 22
        # 黑桃3先出
        if self.info["outCradType"] == 15:
            for k, v in chapter["playerInGame"].items():
                if self.get_card_value_for_want(v["cards"], 3.4):
                    chapter["startAccountId"] = k
                    over_result = 15
            if chapter["startAccountId"] == -1:
                chapter["startAccountId"] = self.find_min_card()
                over_result = 25

        # 设置身份
        for k, v in chapter["playerInGame"].items():
            if chapter["startAccountId"] == k:
                v["identity"] = 1
            else:
                v["identity"] = 0

        chapter["OverLocalOutCard"] = over_result
        return over_result

    # 播放定庄动画计时器
    def send_info_to_clients_fun(self, call_type):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInGame = _chapter["playerInGame"]
        _chapter["setPosAnimationTimerId"] = self.addTimer(_timeHadLocalPlans, 0, 0)
        _chapter["deadline"] = time.time() + _timeHadLocalPlans
        player_info = {"accountId": int(_chapter["startAccountId"]), "CallType": call_type}
        self.callOtherClientsFunction("setOutCardPos", player_info)

        # 记录定庄步骤
        record = {"accountId": int(_chapter["startAccountId"]), "operationType": 1,
                  "operationArgs": {'CallType': call_type}}
        _chapter["operationRecord"].append(record)

    # 设置回合数
    def set_current_round(self, current_round):
        """
        设置当前轮数
        :param current_round:
        :return:
        """
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _chapter["currentRound"] = current_round
        _args = {"currentRound": _chapter["currentRound"]}
        self.callOtherClientsFunction("RetCurrentRound", _args)

    # 手牌展示
    def showCards(self):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        chapter["showCardTime"] = self.addTimer(_timeShowCard, 0, 0)
        chapter["deadline"] = time.time() + WAIT_TIME_LEN_ON_PLAY_OFFLINE
        player_list_card = {}
        for k, v in chapter["playerInGame"].items():
            if len(v["cards"]) != 0:
                v["cards"].sort()
            if chapter["winner"] != k:
                player_list_card[k] = self.change_value_to_client(v["cards"])
            else:
                player_list_card[k] = self.change_value_to_client(v["cards"])
        if len(chapter["playerInGame"]) == 2:
            player_list_card[-1] = self.change_value_to_client(self.OtherCardPlan)
        args = {"cards": player_list_card, "timer": _timeShowCard}
        self.callOtherClientsFunction("ShowCardOnGameOver", args)

        # 记录回放信息
        chapter['recordCards'] = player_list_card.copy()

    # 改变出牌玩家
    def change_play_card_player(self, account_id) -> None:
        DEBUG_MSG("change_play_card_player process %s" % account_id)
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 遍历游戏中的玩家
        _player = None
        for k, v in chapter["playerInGame"].items():
            # 找到要出牌的玩家
            if account_id == k:
                _player = v
                break
        if not _player:
            return

        # 将当前操作玩家位置设置成当前玩家
        chapter["currentLocationIndex"] = _player["locationIndex"]
        chapter["currentPlayer"] = int(account_id)

        # 判断出牌玩家是否在线
        # 玩家掉线、打不住时计时变短
        wait_time_length = self.play_card_time
        have_bigger = self.have_big_in_player(account_id)  # 判断玩家手中是否有大过的牌
        add_server_timer = True
        _player["allowAutoPlayCheck"] = False
        if self.play_card_time != 0:
            if self.is_auto_play_card(account_id):
                wait_time_length = WAIT_TIME_LEN_ON_PLAY_OFFLINE  # 离线出牌时间
            elif self.is_player_offline(account_id):
                wait_time_length = WAIT_TIME_LEN_ON_PLAY_OFFLINE  # 离线出牌时间
            else:
                if have_bigger:
                    wait_time_length = self.play_card_time  # 出牌时间
                    _player["allowAutoPlayCheck"] = True
                else:
                    wait_time_length = WAIT_TIME_LEN_ON_PLAY_OFFLINE  # 离线出牌时间
        else:
            # 没开定时器
            wait_time_length = 60
            if have_bigger:
                add_server_timer = False
            else:
                wait_time_length = WAIT_TIME_LEN_ON_PLAY_OFFLINE  # 离线出牌时间

        if add_server_timer:
            chapter["playCardTimer"] = self.addTimer(wait_time_length, 0, 0)
        chapter["deadline"] = time.time() + wait_time_length
        args = {"accountId": int(account_id), "Timer": wait_time_length, "canOut": have_bigger,
                "canPass": not self.info["haveCardMustCome"]}
        self.callOtherClientsFunction("ChangeOperation", args)

        # 判断玩家是否为最后一手牌，如果是，并且出牌时机合适，系统将其自动打出
        bool_type, card_type = self.is_last_count_in_player(account_id)
        DEBUG_MSG("is_last_count_in_player %s - %s" % (bool_type, card_type))
        if bool_type:
            if card_type != RoomType13Calculator.CardType.Lin_FourWithThreeSingle and \
                    card_type != RoomType13Calculator.CardType.Lin_FourWithTwoSingle and \
                    card_type != RoomType13Calculator.CardType.Lin_MaxBoomForFour and \
                    card_type != RoomType13Calculator.CardType.Lin_MaxBoomWithSingle and \
                    card_type != RoomType13Calculator.CardType.Lin_FourBoomWithSingle:

                boom_list = RoomType13Calculator.get_boom_cards_value(chapter["playerInGame"][account_id]["cards"],
                                                                      self.info)
                if not boom_list:
                    # 替玩家打出合适的牌型(此处将玩家所有手牌打出)
                    self.send_player_cards(account_id, 1,
                                           self.change_value_to_client(
                                               chapter["playerInGame"][account_id]["cards"]),
                                           card_type)

    # 是不是最后一手牌
    def is_last_count_in_player(self, account_id):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 先判断是不是当前玩家出牌
        if chapter["playerInGame"][account_id]["locationIndex"] == chapter["currentLocationIndex"]:
            # 判断玩家是不是首发出牌
            if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
                # 获取当前玩家所有手牌的牌型
                card_type_for_player = RoomType13Calculator.get_cards_type(
                    chapter["playerInGame"][account_id]["cards"], self.info)
                # 剩余手牌如果是正常牌型
                if card_type_for_player != RoomType13Calculator.CardType.Com_Invalid:
                    card_type = card_type_for_player
                    return True, card_type
                # 剩余牌型为非正常牌型
                else:
                    if RoomType13Calculator.is_last_shou_cards(chapter["playerInGame"][account_id]["cards"],
                                                               chapter["playerInGame"][account_id]["cards"]):
                        if len(chapter["playerInGame"][account_id]["cards"]) > 3:
                            card_type = RoomType13Calculator.CardType.Spc_OnlyPlan
                        else:
                            return False, RoomType13Calculator.CardType.Com_Invalid
                        return True, card_type
            else:
                # 将玩家所有手牌与上家做比较
                if self.is_current_card_greater(chapter["playerInGame"][account_id]["cards"],
                                                chapter["prePlayerPlayCards"]):
                    # 获取当前玩家所有手牌的牌型
                    card_type_for_player = RoomType13Calculator.get_cards_type(
                        chapter["playerInGame"][account_id]["cards"], self.info)
                    card_type = card_type_for_player
                    return True, card_type
        card_type = RoomType13Calculator.CardType.Com_Invalid
        return False, card_type

    def have_big_in_player(self, account_id) -> bool:
        """
        判断玩家手中是否有大过的牌
        """
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        chapter["playerInGame"][account_id]["cards"].sort()
        #  获取card2中与card1牌型一样的牌或者大的牌型
        bigger_cards = RoomType13Calculator.find_greater_cards(chapter["prePlayerPlayCards"],
                                                               chapter["playerInGame"][account_id]["cards"], self.info)
        DEBUG_MSG("have_big_in_player %s" % bigger_cards)
        if bigger_cards:  # 如果有大过的牌
            return True
        if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
            return True
        return False

    # 玩家出牌
    def player_play_cards(self, account_id, client_cards):
        """
        E玩家出牌
        玩家请求出牌
        """
        # 阶段判断
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        if chapter['currentState'] != 3:  # 当前房间状态
            return
        # 转换成服务端的牌值
        this_play_cards = self.change_value_to_server(client_cards)
        # 玩家手牌
        player_cards = chapter["playerInGame"][account_id]["cards"]
        # 上家出牌
        pre_playa_cards = chapter["prePlayerPlayCards"]
        # 出的牌不是手中有的牌
        for s_card in this_play_cards:
            if s_card not in chapter["playerInGame"][account_id]["cards"]:
                DEBUG_MSG("failed to out card because there no these cards in player's cards")
                self.send_player_cards(account_id, -1, client_cards, RoomType13Calculator.CardType.Com_Invalid)
                # 并将玩家手牌刷新（需增加此函数）
                _args = {}
                self.callClientFunction(account_id, "RefreshPlayerCards", _args)
                return

        # 没有轮到自己，出牌失败
        if chapter["playerInGame"][account_id]["locationIndex"] != chapter["currentLocationIndex"]:
            DEBUG_MSG("failed to out card because this is other player out card time")
            return

        # 客户端发送不出请求
        # if not len(client_cards):
        #     # 上个出牌玩家是自己或者没有上个出牌玩家，不能不出
        #     if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
        #         self.send_player_cards(account_id, -1, client_cards, RoomType13Calculator.CardType.Com_Invalid)
        #         return
        #     # 如果是有牌必出并且能压住，不能不出
        #     if self.info["haveCardMustCome"]:
        #         if self.have_big_in_player(account_id):
        #             return
        #     # 不出成功；报单顶大只针对出的牌
        #     self.send_player_cards(account_id, 0, client_cards, RoomType13Calculator.CardType.Com_Invalid)
        #     return

        # 获取玩家出的牌型
        server_cards_type = RoomType13Calculator.get_cards_type(this_play_cards, self.info)

        # 无效牌，出牌失败
        if server_cards_type == RoomType13Calculator.CardType.Com_Invalid and this_play_cards:
            self.send_player_cards(account_id, -1, client_cards, server_cards_type)
            return
        DEBUG_MSG('======================================xxxxxxxxxxxxxxx')
        DEBUG_MSG(chapter)
        # 检测报单顶大
        if self.single_max and len(this_play_cards) == 1 and self.is_only_left_one_for_next_player(account_id, chapter):
            for cv in chapter["playerInGame"][account_id]["cards"]:
                if int(this_play_cards[-1]) < int(cv):
                    self.send_player_cards(account_id, -1, client_cards, server_cards_type)
                    self.callClientFunction(account_id, 'Notice', ["报单顶大"])
                    return
        DEBUG_MSG('======================================')
        DEBUG_MSG(chapter)
        DEBUG_MSG(account_id)
        DEBUG_MSG('======================================++')
        # 检测是否满足单A必出2
        if chapter["prePlayer"] != account_id:
            if not self.check_single_1_must_2(pre_playa_cards, this_play_cards, player_cards):
                self.send_player_cards(account_id, -1, client_cards, server_cards_type)
                self.callClientFunction(account_id, 'Notice', ["单A必出2"])
                return

        # 检测是否满足2必出炸弹
        DEBUG_MSG('======================================++prePlayer')
        DEBUG_MSG(chapter["prePlayer"])
        if chapter["prePlayer"] != account_id:
            if not self.check_2_must_bomb(pre_playa_cards, this_play_cards, player_cards):
                self.send_player_cards(account_id, -1, client_cards, server_cards_type)
                self.callClientFunction(account_id, 'Notice', ["2必出炸弹"])
                return

        DEBUG_MSG('======================================++prePlayer')
        DEBUG_MSG(chapter["prePlayer"])
        if chapter["prePlayer"] != account_id:
            # 检测是否满足大炸弹压小炸弹
            if not self.check_big_bomb_and_small_bomb(pre_playa_cards, this_play_cards, player_cards):
                self.send_player_cards(account_id, -1, client_cards, server_cards_type)
                self.callClientFunction(account_id, 'Notice', ["大炸弹必炸小炸弹"])
                return

        if chapter["prePlayer"] != account_id:
            # 检测是否满足单K必出A
            if self.single_k_must_a and not self.check_single_k_must_1(pre_playa_cards, this_play_cards, player_cards):
                self.send_player_cards(account_id, -1, client_cards, server_cards_type)
                self.callClientFunction(account_id, 'Notice', ["单K必出A"])
                return
        if chapter["prePlayer"] != account_id:
            # 检测是否满足对K必出对A
            if self.double_k_must_a and not self.check_double_k_must_1(pre_playa_cards, this_play_cards, player_cards):
                self.send_player_cards(account_id, -1, client_cards, server_cards_type)
                self.callClientFunction(account_id, 'Notice', ["对K必出对A"])
                return
        if chapter["prePlayer"] != account_id:
            # 检测是否满足A不能连
            if self.straight_not_a and not self.check_straight_not_a(pre_playa_cards, this_play_cards, player_cards):
                self.send_player_cards(account_id, -1, client_cards, server_cards_type)
                self.callClientFunction(account_id, 'Notice', ["A不能连"])
                return
        DEBUG_MSG("**********************************")
        DEBUG_MSG(client_cards)
        DEBUG_MSG("**********************************=======")
        DEBUG_MSG(self.info["haveCardMustCome"])
        if not len(client_cards):
            # 上个出牌玩家是自己或者没有上个出牌玩家，不能不出
            if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
                self.send_player_cards(account_id, -1, client_cards, RoomType13Calculator.CardType.Com_Invalid)
                return
            # 如果是有牌必出并且能压住，不能不出
            if self.info["haveCardMustCome"]:
                if self.have_big_in_player(account_id):
                    return
            # 不出成功；报单顶大只针对出的牌
            self.send_player_cards(account_id, 0, client_cards, RoomType13Calculator.CardType.Com_Invalid)
            return

        # 在炸弹不可拆模式下，如果玩家打出的牌不是四带，不是三带二，并且含有炸弹元素的牌型则出牌失败(出牌拆离)
        if self.is_split_boom(this_play_cards, chapter["playerInGame"][account_id]["cards"], server_cards_type) and \
                self.info["bombCannotSeparate"]:
            self.send_player_cards(account_id, 100, client_cards, server_cards_type)
            DEBUG_MSG("is_split_boom")
            return

        # 待优化--------------------------------------------------------------
        # 查看所带的牌是否是炸弹的一部分
        if (server_cards_type == RoomType13Calculator.CardType.Lin_FourBoomWithSingle or
            server_cards_type == RoomType13Calculator.CardType.Lin_MaxBoomWithSingle or
            server_cards_type == RoomType13Calculator.CardType.Lin_FourWithTwoSingle or
            server_cards_type == RoomType13Calculator.CardType.Lin_FourWithThreeSingle or
            server_cards_type == RoomType13Calculator.CardType.Lin_ThreeWithDouble or
            server_cards_type == RoomType13Calculator.CardType.Lin_ThreeWithTwo or
            server_cards_type == RoomType13Calculator.CardType.Com_ThreeWithSingle or
            server_cards_type == RoomType13Calculator.CardType.Spc_OnlyThree or
            server_cards_type == RoomType13Calculator.CardType.Lin_PlaneWithDouble or
            server_cards_type == RoomType13Calculator.CardType.Com_PlaneWithTwo or
            server_cards_type == RoomType13Calculator.CardType.Com_PlaneWithSingle
        ) and self.info["bombCannotSeparate"]:
            # 将玩家炸弹中的非炸弹牌拉出，判断其是否是炸弹中的一个
            if not self.is_dai_card_in_boom(this_play_cards, chapter["playerInGame"][account_id]["cards"]):
                self.send_player_cards(account_id, 100, client_cards, server_cards_type)
                DEBUG_MSG("is_dai_card_in_boom")
                return

        # 如果打出通过，判断剩下的牌，如果将炸弹拆离（四代一为炸弹：普通四代一，和AAA带一），那么出牌失败（剩余牌拆离）
        find_c_p_type = RoomType13Calculator.remove_c_list_from_p_list(this_play_cards,
                                                                       chapter["playerInGame"][account_id]["cards"])
        # 玩家手中无此牌，将刷新玩家手牌
        if find_c_p_type is None:
            # 此处添加刷新逻辑
            pass
        # 玩家剩余手牌长度存在，游戏没有结束
        elif len(find_c_p_type):
            # 判断当前模式是不是炸弹不可拆模式
            if self.info["bombCannotSeparate"]:
                # 判断当前炸弹类型，如果四带一是炸弹
                if self.info["boomType"] == 3:
                    # 统计手牌正常炸弹数量数量
                    boom_type, boom_number = RoomType13Calculator.get_boom_number(find_c_p_type, self.info)
                    # 没有AAA
                    if boom_type == 1:
                        # 此时的牌型组需要大于固定张数
                        if boom_number * 5 > len(find_c_p_type):
                            self.send_player_cards(account_id, 100, client_cards, server_cards_type)
                            DEBUG_MSG("get_boom_number NO AAA")
                            return
                    # 存在AAA
                    else:
                        # 此时牌型组需要满足大于固定张数
                        if (boom_number - 1) * 5 + 4 > len(find_c_p_type):
                            self.send_player_cards(account_id, 100, client_cards, server_cards_type)
                            DEBUG_MSG("get_boom_number AAA")
                            return

        # 如果是首发 或 上次自己出牌
        DEBUG_MSG("this is card_type:%s" % server_cards_type)
        if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
            # 刚开始出牌，必须包含抢庄的牌
            if chapter["prePlayer"] == -1:
                # 如果抢庄类型是红桃3，并且存在
                if chapter["OverLocalOutCard"] == 12:
                    if not this_play_cards.count(3.3):
                        self.send_player_cards(account_id, 12, client_cards, server_cards_type)
                        return
                # 如果是黑桃3，且存在
                if chapter["OverLocalOutCard"] == 15:
                    if not this_play_cards.count(3.4):
                        self.send_player_cards(account_id, 15, client_cards, server_cards_type)
                        return
            # 有效牌型出牌成功
            self.send_player_cards(account_id, 1, client_cards, server_cards_type)
            return

        # 如果比之前出牌大，出牌成功；否则失败
        if self.is_current_card_greater(this_play_cards, chapter["prePlayerPlayCards"]):
            self.send_player_cards(account_id, 1, client_cards, server_cards_type)
        else:
            self.send_player_cards(account_id, -1, client_cards, server_cards_type)

    def play_tips(self, account_id):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        bigger_cards = RoomType13Calculator.find_greater_cards_can_split_boom(chapter["prePlayerPlayCards"],
                                                                              chapter["playerInGame"][account_id][
                                                                                  "cards"], self.info)
        DEBUG_MSG("play_tips:%s" % bigger_cards)
        ncount = 1
        result = dict()
        if bigger_cards:
            cards = chapter["playerInGame"][account_id]["cards"]
            for one_cards in bigger_cards:
                new_val = RoomType13Calculator.change_to_card_for_one(one_cards, cards, self.info)
                if new_val:
                    new_val = self.change_value_to_client(new_val)
                    result[ncount] = new_val
                    ncount += 1
        self.callClientFunction(account_id, "PlayTips", {"cards": result})

    def is_split_boom(self, cards, card1, cards_type):
        """
        是否拆炸弹了
        """
        # 如果是炸弹返回未分割
        if cards_type == RoomType13Calculator.CardType.Lin_FourBoom or \
                cards_type == RoomType13Calculator.CardType.Lin_MaxBoomForFour or \
                cards_type == RoomType13Calculator.CardType.Lin_MaxBoomWithSingle or \
                cards_type == RoomType13Calculator.CardType.Lin_FourBoomWithSingle:
            return False

        # 将玩家手牌炸弹拿出
        itm_card_boom = RoomType13Calculator.get_boom_cards_value(card1, self.info)
        if RoomType13Calculator.is_both_have_same_card(itm_card_boom, cards):
            return True
        return False

    def is_dai_card_in_boom(self, card, cards):
        itm_list = RoomType13Calculator.convert_cards_to_value(card)
        card_singe = []
        for v in itm_list:
            if itm_list.count(v) <= 2:
                card_singe.append(v)
            else:
                if itm_list.count(v) == 3:
                    if v == 14 and self.info["boomType"] != 2:
                        pass
                    else:
                        card_singe.append(v)
        boom_list = RoomType13Calculator.get_boom_cards_value(cards, self.info)
        for c in card_singe:
            if c in boom_list:
                return False
        return True

    def send_player_cards(self, account_id, result, client_cards, cards_type):
        """
        发送玩家出牌
        """
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 不出
        if result == 0:
            client_cards = []
            cards_type = RoomType13Calculator.CardType.Com_Invalid
            # 炸者得分模式如果有人不出，当前最大炸弹玩家炸弹数+1
            if chapter['max_boom'] and self.info['boomSettlementType'] != 1:
                boom_player = chapter["max_boom_player"]
                chapter["playerInGame"][boom_player]["boomCount"] += 1
                self.debug_msg(
                    'boom_player:%s,bombCount:%s' % (boom_player, chapter["playerInGame"][boom_player]["boomCount"]))

                chapter['max_boom'] = []
                chapter["max_boom_player"] = -1

        # 将出牌状态发送给客户端
        args = {"accountId": account_id, "result": result, "cards": client_cards, "cards_type": cards_type.value}
        self.callOtherClientsFunction("PlayCards", args)

        # 如果出牌失败直接返回
        if result != 1 and result != 0:
            return
        # 获取当前玩家手牌信息
        player_cards = chapter["playerInGame"][account_id]["cards"]
        # 获取当前玩家已经打出的牌的信息
        player_played_cards = chapter["playerInGame"][account_id]["playedCards"]
        # 将此牌转化成服务端的牌
        server_cards = self.change_value_to_server(client_cards)
        # 如果玩家成功出牌
        if result == 1:
            # 如果开启空炸不算分并且是空炸，不调用炸弹算分
            if self.initiative_bomb_not_score and (chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id):
                DEBUG_MSG("initiative_bomb_not_score account_id:%s server_cards:%s" % (account_id, server_cards))
            else:
                self.boom_score_for_total(server_cards, cards_type, account_id)
            # 将上个出牌玩家置为当前玩家
            if chapter['prePlayer'] == account_id:
                chapter['letPlayer'] = -1
            else:
                chapter['letPlayer'] = chapter['prePlayer']
            chapter["prePlayer"] = account_id
            # 将上家出牌值置为当前玩家出牌值
            chapter["prePlayerPlayCards"] = server_cards
            # 将牌从玩家手中移除，添加到已出牌堆
            for i in server_cards:
                if i in player_cards:
                    player_cards.remove(i)
                player_played_cards.append(i)
            # 此玩家的出牌次数更新
            chapter["playerInGame"][account_id]["playCount"] += 1
            count_time = chapter["playerInGame"][account_id]["playCount"]
            chapter["playerInGame"][account_id]["outCardList"][count_time] = client_cards
        # 关闭出牌计时器
        self.delTimer(chapter["playCardTimer"])
        chapter["playCardTimer"] = -1

        # 回放记录出牌步骤
        record = {"accountId": account_id, "operationType": 2, "operationArgs": {"clientCards": client_cards.copy(),
                                                                                 "cardsType": cards_type.value}}
        chapter["operationRecord"].append(record)

        # 检测牌局是否结束
        if self.check_chapter_over():
            # 结束进入结算状态
            chapter["showLastTime"] = self.addTimer(_timeShowLastOne, 0, 0)
            chapter["deadline"] = time.time() + WAIT_TIME_LEN_ON_PLAY_OFFLINE
            return
        else:
            chapter['letPlayer'] = -1

        # 切换下一个玩家出牌
        nex_player_out_card_id = self.get_next_player_with_account_id(account_id)
        # 切换下个出牌玩家
        self.change_play_card_player(nex_player_out_card_id)

    def boom_score_for_total(self, server_cards, cards_type, account_id):
        """
        统计炸弹分
        """
        chapter = self.chapters[self.cn]
        if cards_type == RoomType13Calculator.CardType.Lin_FourBoom or \
                cards_type == RoomType13Calculator.CardType.Lin_MaxBoomForFour or \
                cards_type == RoomType13Calculator.CardType.Lin_MaxBoomWithSingle or \
                cards_type == RoomType13Calculator.CardType.Lin_FourBoomWithSingle:
            # 炸弹翻倍模式
            if self.info["boomSettlementType"] == 1:
                if self.info["boomScore"] == -1:
                    chapter["playerInGame"][account_id]["boomCount"] += 1
                    chapter["multiple"] *= 2
                if self.info["boomScore"] == 2 and chapter["boomCount"] < 1:
                    chapter["playerInGame"][account_id]["boomCount"] += 1
                    chapter["multiple"] *= 2
                if self.info["boomScore"] == 4 and chapter["boomCount"] < 2:
                    chapter["playerInGame"][account_id]["boomCount"] += 1
                    chapter["multiple"] *= 2
                if self.info["boomScore"] == 8 and chapter["boomCount"] < 4:
                    chapter["playerInGame"][account_id]["boomCount"] += 1
                    chapter["multiple"] *= 2
                chapter["boomCount"] += 1
            # 炸弹算分模式
            else:
                # chapter["playerInGame"][account_id]["boomCount"] += 1
                if not len(chapter["max_boom"]):
                    chapter["max_boom_player"] = account_id
                    chapter["max_boom"] = server_cards
                else:
                    # 比较炸弹牌型
                    if RoomType13Calculator.compare_cards(server_cards, chapter["max_boom"], self.info):
                        chapter["max_boom"] = server_cards
                        chapter["max_boom_player"] = account_id

    # 获取玩家手牌和上家做比较（待优化，优化牌型组的检出优化，统一打出,分块代码等）
    def get_info_and_change_player(self, account_id):
        """
        轮到玩家出牌，自动出牌
        """
        DEBUG_MSG("get_info_and_change_player: %s" % account_id)
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        send_card = []
        chapter["playerInGame"][account_id]["cards"].sort()
        # 判断当前出牌玩家的下一家手牌长度
        _is_only_one_in_player = False
        if self.is_only_left_one_for_next_player(account_id, chapter):
            _is_only_one_in_player = True
        # 首发
        if chapter["prePlayer"] == -1:
            # 如果是按花色3的一种定庄
            if chapter["OverLocalOutCard"] == 12:
                if self.info["bombCannotSeparate"]:
                    itm_boom_list = RoomType13Calculator.get_boom_cards_value(
                        chapter["playerInGame"][account_id]["cards"],
                        self.info)
                    if int(3.4) in itm_boom_list:
                        if self.info["boomType"] == 3:
                            itm_number = -1
                            for v in chapter["playerInGame"][account_id]["cards"]:
                                if int(v) not in itm_boom_list:
                                    itm_number = v
                                    break
                            if itm_number != -1:
                                # 此处待优化，将单张加入打出牌组
                                self.send_player_cards(account_id, 1,
                                                       self.change_value_to_client([3.1, 3.2, 3.3, 3.4, itm_number]),
                                                       RoomType13Calculator.CardType.Lin_FourBoomWithSingle)
                                return
                            else:
                                # 此处待优化，如果都是炸弹的话，将一组炸弹分离（此处为修正，确保游戏会正常进行）
                                self.send_player_cards(account_id, 1,
                                                       self.change_value_to_client([3.1, 3.2, 3.3, 3.4,
                                                                                    chapter["playerInGame"][account_id][
                                                                                        "cards"][5]]),
                                                       RoomType13Calculator.CardType.Lin_FourBoomWithSingle)
                                return
                        else:
                            # 此处为四张普通炸弹，直接将牌型代入（待优化）
                            self.send_player_cards(account_id, 1,
                                                   self.change_value_to_client([3.1, 3.2, 3.3, 3.4]),
                                                   RoomType13Calculator.CardType.Lin_FourBoom)
                            return
                    else:
                        # 将固定的牌打出
                        send_card.append(2)
                        self.send_player_cards(account_id, 1, send_card, RoomType13Calculator.CardType.Com_Single)
                    return
                else:
                    # 直接打出固定的牌型
                    send_card.append(2)
                    self.send_player_cards(account_id, 1, send_card, RoomType13Calculator.CardType.Com_Single)
                    return
            elif chapter["OverLocalOutCard"] == 15:
                # 另外一花色3首出，基本同上，可以合并优化
                if self.info["bombCannotSeparate"]:
                    itm_boom_list = RoomType13Calculator.get_boom_cards_value(
                        chapter["playerInGame"][account_id]["cards"],
                        self.info)
                    if int(3.4) in itm_boom_list:
                        if self.info["boomType"] == 3:
                            itm_number = -1
                            for v in chapter["playerInGame"][account_id]["cards"]:
                                if int(v) not in itm_boom_list:
                                    itm_number = v
                            if itm_number != -1:
                                self.send_player_cards(account_id, 1,
                                                       self.change_value_to_client([3.1, 3.2, 3.3, 3.4, itm_number]),
                                                       RoomType13Calculator.CardType.Lin_FourBoomWithSingle)
                                return
                            else:
                                self.send_player_cards(account_id, 1,
                                                       self.change_value_to_client([3.1, 3.2, 3.3, 3.4,
                                                                                    chapter["playerInGame"][account_id][
                                                                                        "cards"][6]]),
                                                       RoomType13Calculator.CardType.Lin_FourBoomWithSingle)
                                return
                        else:
                            self.send_player_cards(account_id, 1,
                                                   self.change_value_to_client([3.1, 3.2, 3.3, 3.4]),
                                                   RoomType13Calculator.CardType.Lin_FourBoom)
                            return
                    else:
                        send_card.append(1)
                        self.send_player_cards(account_id, 1, send_card, RoomType13Calculator.CardType.Com_Single)
                    return
                send_card.append(1)
                self.send_player_cards(account_id, 1, send_card, RoomType13Calculator.CardType.Com_Single)
                return
            else:
                # 正常首出区分不可拆
                if self.info["bombCannotSeparate"]:
                    itm_boom_list = RoomType13Calculator.get_boom_cards_value(
                        chapter["playerInGame"][account_id]["cards"],
                        self.info)
                    index = -1
                    for v in chapter["playerInGame"][account_id]["cards"]:
                        if int(v) not in itm_boom_list:
                            index = v
                            break
                    if index != -1:
                        self.send_player_cards(account_id, 1,
                                               self.change_value_to_client([index]),
                                               RoomType13Calculator.CardType.Com_Single)
                        return
                    else:
                        self.send_player_cards(account_id, 1,
                                               self.change_value_to_client([
                                                   chapter["playerInGame"][account_id]["cards"][-1]]),
                                               RoomType13Calculator.CardType.Com_Single)
                        return
                else:
                    # 可拆就随意打出
                    send_card.append(chapter["playerInGame"][account_id]["cards"][0])
                    send_card = self.change_value_to_client(send_card)
                    self.send_player_cards(account_id, 1, send_card, RoomType13Calculator.CardType.Com_Single)
                    return
        # 轮发
        elif chapter["prePlayer"] == account_id:
            # 判定是不是下家报单
            if _is_only_one_in_player:
                itm_list = RoomType13Calculator.find_no_single_cards(chapter["playerInGame"][
                                                                         account_id]["cards"], self.info)
                if len(itm_list):
                    self.send_player_cards(account_id, 1,
                                           self.change_value_to_client(itm_list),
                                           RoomType13Calculator.get_cards_type(itm_list, self.info))
                    return
                else:
                    self.send_player_cards(account_id, 1,
                                           self.change_value_to_client([chapter["playerInGame"][
                                                                            account_id]["cards"][-1]]),
                                           RoomType13Calculator.CardType.Com_Single)
                    return

            # 此处可与上不是花色首出合并
            if self.info["bombCannotSeparate"]:
                itm_boom_list = RoomType13Calculator.get_boom_cards_value(chapter["playerInGame"][account_id]["cards"],
                                                                          self.info)
                # 获取可以打出的牌，非炸弹
                index = -1
                for v in chapter["playerInGame"][account_id]["cards"]:
                    if int(v) not in itm_boom_list:
                        index = v
                        break
                if index != -1:
                    # 如果打出牌后，剩余牌不可拆(此代码块可以写成通用函数)
                    # 如果打出通过，判断剩下的牌，如果将炸弹拆离（四代一为炸弹：普通四代一，和AAA带一），那么出牌失败（剩余牌拆离）
                    find_c_p_type = RoomType13Calculator.remove_c_list_from_p_list([index],
                                                                                   chapter["playerInGame"][account_id][
                                                                                       "cards"])
                    client_cards = self.change_value_to_client([index])
                    # 判断当前炸弹类型，如果四带一是炸弹
                    if self.info["boomType"] == 3:
                        # 统计手牌正常炸弹数量数量
                        boom_type, boom_number = RoomType13Calculator.get_boom_number(find_c_p_type, self.info)
                        if boom_type == 1:
                            if boom_number * 5 > len(find_c_p_type):
                                # 随机打出一手炸弹
                                itm_boom_card = self.get_boom_by_lim(chapter["playerInGame"][account_id]["cards"],
                                                                     boom_type)
                                client_cards = self.change_value_to_client(itm_boom_card)
                                self.send_player_cards(account_id, 1, client_cards,
                                                       RoomType13Calculator.get_cards_type(
                                                           itm_boom_card, self.info))
                                return
                        elif boom_type == 10:
                            if (boom_number - 1) * 5 + 4 > len(find_c_p_type):
                                itm_boom_card = self.get_boom_by_lim(chapter["playerInGame"][account_id]["cards"],
                                                                     boom_type)
                                client_cards = self.change_value_to_client(itm_boom_card)
                                self.send_player_cards(account_id, 1, client_cards,
                                                       RoomType13Calculator.get_cards_type(
                                                           itm_boom_card, self.info))
                                return
                    self.send_player_cards(account_id, 1,
                                           client_cards,
                                           RoomType13Calculator.CardType.Com_Single)
                    return

                else:
                    self.send_player_cards(account_id, 1,
                                           self.change_value_to_client([
                                               chapter["playerInGame"][account_id]["cards"][-1]]),
                                           RoomType13Calculator.CardType.Com_Single)
                    return
            else:
                send_card.append(chapter["playerInGame"][account_id]["cards"][0])
                send_card = self.change_value_to_client(send_card)
                self.send_player_cards(account_id, 1, send_card, RoomType13Calculator.CardType.Com_Single)
                return
        # 压牌
        else:
            # 如果下家报单的情况下
            if _is_only_one_in_player:
                # 上次出了一张牌， 先用炸弹， 没有炸弹再找最大单
                if len(chapter["prePlayerPlayCards"]) == 1:
                    item_list = RoomType13Calculator.find_one_boom(chapter["playerInGame"][account_id]["cards"],
                                                                   self.info)
                    if len(item_list):
                        self.send_player_cards(account_id, 1,
                                               self.change_value_to_client(item_list),
                                               RoomType13Calculator.get_cards_type(item_list, self.info))
                        return

                    # 判断最大的单张
                    if int(chapter["prePlayerPlayCards"][-1]) < int(chapter["playerInGame"][account_id]["cards"][-1]):
                        self.send_player_cards(account_id, 1,
                                               self.change_value_to_client(
                                                   [chapter["playerInGame"][account_id]["cards"][-1]]),
                                               RoomType13Calculator.CardType.Com_Single)
                        return
                    else:
                        self.send_player_cards(account_id, 0,
                                               self.change_value_to_client(
                                                   [chapter["playerInGame"][account_id]["cards"][-1]]),
                                               RoomType13Calculator.CardType.Com_Single)
                        return

            # 找比所出牌更大的牌
            bigger_cards = RoomType13Calculator.find_greater_cards(chapter["prePlayerPlayCards"],
                                                                   chapter["playerInGame"][account_id]["cards"],
                                                                   self.info)
            DEBUG_MSG("this find cards over,this is cards:%s" % bigger_cards)
            send_card = []
            if not len(bigger_cards):
                self.send_player_cards(account_id, 0, send_card,
                                       RoomType13Calculator.get_cards_type(chapter["prePlayerPlayCards"],
                                                                           self.info))
                return

            # 修正返回牌组(将牌型寻找函数寻找得牌组修正，减少下面牌组解析的工作量)
            send_card = RoomType13Calculator.change_to_card(bigger_cards, chapter["playerInGame"][account_id]["cards"],
                                                            self.info)
            if not send_card:
                self.send_player_cards(account_id, 0, send_card, RoomType13Calculator.CardType.Com_Invalid)
                return

            # 检查是否把炸弹给拆了
            itm_send = send_card
            send_card = self.change_value_to_client(send_card)
            find_c_p_type = RoomType13Calculator.remove_c_list_from_p_list(itm_send,
                                                                           chapter["playerInGame"][account_id]["cards"])

            if self.info["bombCannotSeparate"]:
                if self.info["boomType"] == 3:
                    boom_type, boom_number = RoomType13Calculator.get_boom_number(find_c_p_type, self.info)
                    if boom_type == 1:
                        if boom_number * 5 > len(find_c_p_type):
                            self.send_player_cards(account_id, 0, send_card, RoomType13Calculator.CardType.Com_Invalid)
                            return
                    else:
                        if (boom_number - 1) * 5 + 4 > len(find_c_p_type):
                            self.send_player_cards(account_id, 0, send_card, RoomType13Calculator.CardType.Com_Invalid)
                            return

            self.send_player_cards(account_id, 1, send_card,
                                   RoomType13Calculator.get_cards_type(self.change_value_to_server(send_card),
                                                                       self.info))
            return

    # 发送小局结算处理(待优化)
    def settlement(self):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 结算信息
        settlement_info = {}
        # 输分统计
        lost_source_all = 0
        dealer = chapter["playerInGame"][chapter["winner"]]
        # 炸弹翻倍
        if self.bomb_multiple and chapter['boomCount'] >= 1:
            chapter['multiple'] *= 2

        let_player = None
        if chapter['letPlayer'] != -1 and chapter['letPlayer'] in chapter['playerInGame'] and self.lose_all:
            let_player = chapter['playerInGame'][chapter['letPlayer']]

        self.debug_msg('settlement chapter multiple: %s' % chapter['multiple'])
        self.debug_msg('settlement let player: %s' % chapter['letPlayer'])

        for k, v in chapter["playerInGame"].items():
            if self.info['boomSettlementType'] == 1:
                if k != chapter["winner"]:
                    lose_gold = 0
                    basic_gold_change = 0
                    # 结算1:手牌*底分*倍数
                    if self.info["totalScore"] == 1:
                        if len(v["cards"]) != 1:
                            # 全关
                            if v["playCount"] == 0 and v["identity"] != 1:

                                v["overCardLift"] = True
                                lose_gold = -self.info["baseScore"] * chapter["multiple"] * len(v["cards"]) * 2
                                DEBUG_MSG(RoomType13Calculator.convert_cards_to_value(v["cards"]))
                                if 15 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                    lose_gold -= 10
                                basic_gold_change = - self.info["baseScore"] * len(v["cards"]) * 2
                            # 非全关
                            else:
                                lose_gold = -self.info["baseScore"] * chapter["multiple"] * len(v["cards"])
                                if 15 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                    lose_gold -=10
                                basic_gold_change = - self.info["baseScore"] * len(v["cards"])
                    # 结算2:固定牌数*低分*倍数
                    else:
                        if len(v["cards"]) < 5:
                            lose_gold = - chapter["multiple"] * len(v["cards"]) * self.info["baseScore"]
                            basic_gold_change = - len(v["cards"]) * self.info["baseScore"]
                        else:
                            # 全关
                            if v["playCount"] == 0 and v["identity"] != 1:
                                v["overCardLift"] = True
                                lose_gold = - chapter["multiple"] * len(v["cards"]) * self.info["baseScore"] * 2 * 2
                                if 15 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                    lose_gold -=10
                                basic_gold_change = - len(v["cards"]) * self.info["baseScore"] * 2 * 2
                            # 不全关
                            else:
                                lose_gold = - chapter["multiple"] * len(v["cards"]) * self.info["baseScore"] * 2
                                if 15 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                    lose_gold -=10
                                basic_gold_change = - len(v["cards"]) * self.info["baseScore"] * 2

                    self.debug_msg('settlement player:%s lose_gold:%s basic_gold_change%s' % (v["entity"].info["name"],
                                                                                              lose_gold,
                                                                                              basic_gold_change))

                    # 如果有放走包赔玩家
                    if let_player:
                        lose_player = let_player
                    else:
                        lose_player = v

                    basic_gold_change *= self.info["baseMultiple"]
                    lose_gold *= self.info["baseMultiple"]

                    if lose_player["gold"] < lose_gold * -1:
                        lose_player["basicScoreChange"] -= lose_player["gold"]
                        lose_player["basicScore"] -= lose_player["gold"]
                        lose_player["boomScoresChange"] -= lose_player["gold"]
                        lose_player["boomScores"] -= lose_player["gold"]
                        lose_player["goldChange"] -= lose_player["gold"]
                        lose_player["totalGoldChange"] -= lose_player["gold"]
                        lose_player["gold"] -= lose_player["gold"]
                    else:
                        lose_player["basicScoreChange"] += basic_gold_change
                        lose_player["basicScore"] += basic_gold_change
                        lose_player["boomScoresChange"] += lose_gold - basic_gold_change
                        lose_player["boomScores"] += lose_gold - basic_gold_change
                        lose_player["goldChange"] += lose_gold
                        lose_player["totalGoldChange"] += lose_gold
                        lose_player["gold"] += lose_gold
                    if abs(lose_player["singMax"]) < abs(lose_player["goldChange"]):
                        lose_player["singMax"] = lose_player["goldChange"]
                    dealer["basicScore"] += abs(basic_gold_change)
                    dealer["boomScores"] += abs(lose_gold - basic_gold_change)
                    v["lostCount"] += 1
                    v["totalBoomCounts"] += v["boomCount"]
            else:
                # 炸弹数量
                boom_count = v['boomCount']
                # 扣其他玩家炸弹分玩家炸弹
                for other_k, other_v in chapter['playerInGame'].items():
                    other_boom_count = other_v['boomCount']
                    true_boom_count = boom_count - other_boom_count
                    boom_score = self.info['boomScoreSize'] * true_boom_count * self.info["baseMultiple"]
                    if self.bomb_multiple:
                        boom_score *= 2
                    if len(v["cards"]) > 0:
                        if v["gold"] < boom_score * -1:
                            v['goldChange'] -= v['gold']
                            v["totalGoldChange"] -= v['gold']
                            v['boomScoresChange'] -= v['gold']
                            v['boomScores'] -= v['gold']
                            v['gold'] -= v['gold']
                        else:
                            v['goldChange'] += boom_score
                            v["totalGoldChange"] += boom_score
                            v['boomScoresChange'] += boom_score
                            v['boomScores'] += boom_score
                            v['gold'] += boom_score
                    self.debug_msg('player22222 %s, goldChange: %s boomScore %s  totalGoldChange %s' % (other_v["entity"].info["name"],other_v['goldChange'], boom_score, other_v["totalGoldChange"]))

                if k != chapter["winner"]:
                    basic_gold_change = 0
                    # 1方式结算 手牌*底分*倍数
                    if self.info["totalScore"] == 1:
                        if len(v["cards"]) != 1:
                            # 全关
                            if v["playCount"] == 0 and v["identity"] != 1:
                                v["overCardLift"] = True
                                basic_gold_change = - self.info["baseScore"] * len(v["cards"]) * 2
                                # TODO
                                if 15 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                    basic_gold_change -= 10
                            else:
                                basic_gold_change = - self.info["baseScore"] * len(v["cards"])
                                if 15 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                    basic_gold_change -= 10
                    else:
                        if len(v["cards"]) < 5:
                            basic_gold_change = - self.info["baseScore"] * len(v["cards"])
                            if 15.3 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                basic_gold_change -= 10

                        else:
                            if v["playCount"] == 0 and v["identity"] != 1:
                                v["overCardLift"] = True
                                basic_gold_change = - self.info["baseScore"] * len(v["cards"]) * 2 * 2
                                if 15 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                    basic_gold_change -= 10
                            else:
                                basic_gold_change = - self.info["baseScore"] * len(v["cards"]) * 2
                                if 15 in RoomType13Calculator.convert_cards_to_value(v["cards"]):
                                    basic_gold_change -= 10


                    # 如果有放走包赔玩家
                    if let_player:
                        lose_player = let_player
                    else:
                        lose_player = v

                    basic_gold_change *= self.info["baseMultiple"]
                    if lose_player["gold"] < basic_gold_change * -1:
                        lose_player["goldChange"] -= lose_player["gold"]
                        lose_player["totalGoldChange"] -= lose_player["gold"]
                        lose_player["basicScoreChange"] -= lose_player["gold"]
                        lose_player["basicScore"] -= lose_player["gold"]
                        dealer["basicScore"] -= lose_player["gold"]
                        lose_player["gold"] -= lose_player["gold"]
                    else:
                        lose_player["goldChange"] += basic_gold_change
                        lose_player["totalGoldChange"] += basic_gold_change
                        lose_player["basicScoreChange"] += basic_gold_change
                        lose_player["basicScore"] += basic_gold_change
                        lose_player["gold"] += basic_gold_change
                        dealer["basicScore"] += abs(basic_gold_change)
                    if abs(lose_player["singMax"]) < abs(lose_player["goldChange"]):
                        lose_player["singMax"] = lose_player["goldChange"]

                    v["lostCount"] += 1
                    v["totalBoomCounts"] += v["boomCount"]

            # 统计输赢
            for k2, v2 in chapter['playerInGame'].items():
                if k2 != chapter['winner']:
                    lost_source_all = v2["goldChange"]

        # 获胜的玩家的分成
        dealer["goldChange"] += -lost_source_all
        dealer["gold"] += -lost_source_all
        dealer["totalGoldChange"] += -lost_source_all
        dealer["winCount"] += 1
        dealer["totalBoomCounts"] += dealer["boomCount"]
        if abs(dealer["singMax"]) < abs(dealer["goldChange"]):
            dealer["singMax"] = dealer["goldChange"]



        if self.info["roomType"] == "gameCoin":
            # 首局结算抽水
            if self.settlement_count == 0:
                for k,_p in chapter["playerInGame"].items():
                    if self.get_true_gold(_p['entity'].id) < self.info['billingCount']:
                        DEBUG_MSG('RoomType12 billing_count not enough---account_id:%s' % _p['entity'].id)
                        continue
                    billing_count = self.info['billingCount']
                    # _p['totalGoldChange'] -= billing_count  # TODO 原扣房费
                    _p['gold'] -= billing_count

            # 每小局结算大赢家抽水,保留整数
            # 获取大赢家
            settlement_winners = self.pdk_get_settlement_winners()
            for location_index, v in settlement_winners.items():
                settlement_winner_account_id = v['entity'].id
                # 计算大赢家小局抽水
                settlement_winner_true_gold = self.pdk_get_true_gold(settlement_winner_account_id)
                settlement_winner_billing = settlement_winner_true_gold * self.info['settlementBilling']
                v['totalGoldChange'] -= settlement_winner_billing
                v['totalGoldChange'] = round(float(v['totalGoldChange']), 1)
                v["goldChange"] -= settlement_winner_billing
                v["goldChange"] = round(float(v['goldChange']), 1)
                v['gold'] -= settlement_winner_billing
                v['gold'] = round(float(v['gold']), 1)
                # 同步房费给base
                self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                      "todayGameCoinAdd": settlement_winner_billing,
                                      "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType13") + "小局"})

        # 整理发送信息(待优化，特定数值赋值)
        for k, v in chapter["playerInGame"].items():
            if len(v["cards"]) != 0:
                v["cards"].sort()
            if k == chapter["winner"]:
                settlement_info[k] = {"winner": 1, "surplusCard": self.change_value_to_client(v["cards"]),
                                      "outCard": v["outCardList"],
                                      "boomCount": v["boomCount"], "surplusLen": len(v["cards"]),
                                      "settlementGold": v["goldChange"], "notAllOut": v["overCardLift"],
                                      "totalGoldChange": v["totalGoldChange"], "gold": v["gold"]}
                continue
            if chapter["playerInGame"][k]["playCount"]:
                settlement_info[k] = {"winner": 0, "surplusCard": self.change_value_to_client(v["cards"]),
                                      "outCard": v["outCardList"],
                                      "boomCount": v["boomCount"], "surplusLen": len(v["cards"]),
                                      "settlementGold": v["goldChange"], "notAllOut": v["overCardLift"],
                                      "totalGoldChange": v["totalGoldChange"], "gold": v["gold"]}
            else:
                settlement_info[k] = {"winner": 0, "surplusCard": self.change_value_to_client(v["cards"]),
                                      "outCard": v["outCardList"],
                                      "boomCount": v["boomCount"], "surplusLen": len(v["cards"]),
                                      "settlementGold": v["goldChange"], "notAllOut": v["overCardLift"],
                                      "totalGoldChange": v["totalGoldChange"], "gold": v["gold"]}
        # 连续失败次数
        for k, v in chapter["playerInGame"].items():
            if k == chapter["winner"]:
                v["losingstreak"] = 0
            else:
                v["losingstreak"] += 1
            # 更新分数控制
            v["entity"].update_score_control(v['goldChange'])


        # 添加小局结算计时器
        chapter["settlementTimer"] = self.addTimer(settlement_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_time
        self.callOtherClientsFunction("Settlement", settlement_info)
        self.settlement_count += 1
        if self.settlement_count == 1:
            self.base.cellToBase({'func': 'addTodayRoom'})
        # 记录牌局结果

        player_record = {}
        DEBUG_MSG('记录牌局结果-----------------------------')
        DEBUG_MSG(chapter["playerInGame"])
        for k, v in chapter["playerInGame"].items():
            record = {"preGoldChange": v["goldChange"], "totalGoldChange": v["totalGoldChange"],
                      "name": v["entity"].info["name"]}
            player_record[k] = record
        chapter["roomRecord"] = player_record

    def get_true_gold(self, account_id):
        """
        跑得快，获得玩家当前真实金币
        :param account_id:
        :return:
        """
        _chapter = self.get_current_chapter()
        # 开锅时分数=锅底+base上分+牌局输赢
        if self.pot:
            for k, v in _chapter['playerInGame'].items():
                if v['entity'].id == account_id:
                    return self.potScore + v['totalGoldChange']
        # 不开锅时分数=玩家分数+base上分+牌局输赢
        else:
            for k, v in _chapter['playerInGame'].items():
                if v['entity'].id == account_id:
                    return v['gold'] + v['totalGoldChange']

    # 总结算
    def total_settlement(self, is_disband=False):
        """
        总结算
        """
        if self.total_settlement_ed:  # 总结算设置位
            return
        DEBUG_MSG("is_disband:%s" % is_disband)
        # 1 关闭所有定时器
        self.close_all_timer()
        # 1 设置总结算为True
        self.total_settlement_ed = True
        # 1 当前牌局
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        player_settlement_info_s = {}
        # 抽奖
        max_winner_id = -1
        max_win_gold = -1
        # 整理大结算数据
        if self.info["roomType"] == "gameCoin" and self.settlement_count >= 0:
            # self.normal_lottery()
            self.pdk_total_settlement_billing()
        # 寻找大赢家
        DEBUG_MSG('chapter["playerInGame"]--------------')
        DEBUG_MSG(chapter["playerInGame"])
        for k, v in chapter["playerInGame"].items():
            v["totalGoldChange"] = round(float(v["totalGoldChange"]), 1)
            if v["totalGoldChange"] > max_win_gold:
                max_win_gold = v["totalGoldChange"]
                max_winner_id = k
        for k, v in chapter["playerInGame"].items():
            if k == max_winner_id:
                player_settlement_info_s[k] = {
                    "isWinner": True, "baseScore": self.info["baseScore"], "totalBoomNum": v["boomScores"],
                    "totalRoundNum": v["basicScore"], "singleRoundMax": v["singMax"],
                    "winOrLoseNum": [v["winCount"], v["lostCount"]], "totalScore": v["totalGoldChange"]
                }
            else:
                player_settlement_info_s[k] = {
                    "isWinner": False, "baseScore": self.info["baseScore"], "totalBoomNum": v["boomScores"],
                    "totalRoundNum": v["basicScore"], "singleRoundMax": v["singMax"],
                    "winOrLoseNum": [v["winCount"], v["lostCount"]], "totalScore": v["totalGoldChange"]
                }
        args = {"settlementInfo": player_settlement_info_s, "isDisband": is_disband}
        self.callOtherClientsFunction("TotalSettlement", args)


        for k, v in chapter["playerInGame"].items():
            # 同步玩家比赛分给base
            if self.info["roomType"] == "gameCoin":
                self.set_base_player_game_coin(k)
            else:
                self.set_base_player_gold(k)  # 设置玩家金币数量

        # 忽略判断，创建一个房间
        self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info, 'ignoreJudge': True, 'onRoomEnd': True})
        self.save_record_str()
        # 扣除额外积分，抽奖
        # if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
        #     # self.mj_lottery()
        #     self.pdk_total_settlement_billing()


        # 清理观战的玩家
        _playerOutGameCopy = chapter["playerOutGame"].copy()
        for k, v in _playerOutGameCopy.items():
            self.kick_out(k)
        # 同步局数
        if self.is_tea_house_room and self.settlement_count >= 1:
            self.set_base_player_chapter_count()
        # 写入数据库
        self.write_chapter_info_to_db()
        self.set_day_good_pai_count_in_base(chapter['playerInGame'])
        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(settlement_clear_players_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_clear_players_time

    # 找到大赢家
    def get_max_winner(self, chapter):
        winner = {}
        max_win = 0
        for k, v in self.chapters[self.cn]['playerInGame'].items():  # self.chapters 牌局信息  self.cn 当前局数下标
            if v['totalGoldChange'] >= max_win:
                max_win = v['totalGoldChange']

        for k, v in self.chapters[self.cn]['playerInGame'].items():  # self.chapters 牌局信息 self.cn 当前局数下标
            if v['totalGoldChange'] == max_win:
                winner[k] = v

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
                                      "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType13")})

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
                                      "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType13")})

    def get_boom_by_lim(self, cards, boom_type):
        itm_card = []
        single = RoomType13Calculator.find_single(0, RoomType13Calculator.convert_cards_to_value(cards), self.info)[-1][
            -1]
        DEBUG_MSG("single", single)
        DEBUG_MSG("boom_type", boom_type)
        boom = -1
        for v in cards:
            if int(v) == single:
                single = v
                break
        itm_list = copy.deepcopy(cards)
        if single in itm_list:
            itm_list.remove(single)
        if boom_type == 1:
            common_cards = RoomType13Calculator.convert_cards_to_value(itm_list)
            DEBUG_MSG("common_cards", common_cards)
            for cv in common_cards:
                if common_cards.count(cv) == 4:
                    boom = cv
                    break
            for value in cards:
                if int(value) == boom:
                    itm_card.append(value)
        else:
            common_cards = RoomType13Calculator.convert_cards_to_value(itm_list)
            for cv in common_cards:
                if common_cards.count(cv) == 3 and cv == 14:
                    boom = cv
                    break
            for value in cards:
                if int(value) == boom:
                    itm_card.append(value)
        itm_card.append(single)
        return itm_card

    def set_base_player_game_coin(self, accountId):
        """
        设置玩家比赛分数量,通知base
        :param accountId:
        :return:
        """
        if self.info['roomType'] != 'gameCoin':
            return
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInRoom = _chapter["playerInRoom"]
        _player = _playerInRoom[accountId]
        # 如果是锅子模式，恢复比赛分
        if self.pot:
            remain_score = _player["entity"].accountMutableInfo["gameCoin"] - self.potScore
            _player["entity"].accountMutableInfo["gameCoin"] = remain_score + round(float(_player['gold']), 1)
        else:
            _player["entity"].accountMutableInfo["gameCoin"] = round(float(_player['gold']), 1)
        _player["entity"].base.cellToBase({"func": "setAccountMutableInfo", "dic": {
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1,
            "gameCoin": _player["entity"].accountMutableInfo["gameCoin"]}})

    # 结算统计
    def cl_card_chapter(self):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 1 通知base端是AA支付扣除钻石扣除钻石
        if self.info['payType'] == Const.PayType.AA:
            need_consume = []
            # 1 循环判断在游戏中还没被收取钻石
            for k, v in chapter["playerInGame"].items():
                if not v["AARoomCardConsumed"]:
                    v['AARoomCardConsumed'] = True
                    need_consume.append(v["entity"].info["userId"])
                    # 1 通知base端扣除钻石
            if len(need_consume) != 0:
                self.base.cellToBase({"func": "AAPayTypeModifyRoomCard", "needConsumePlayers": need_consume})

    # 清理房间
    def chapter_clear(self):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInGame = _chapter["playerInGame"]
        _playerInRoom = _chapter["playerInRoom"]
        _playerOutGame = _chapter["playerOutGame"]
        _newChapter = self.newChapter(_chapter["maxPlayerCount"])
        _newChapter["playerInGame"] = copy.deepcopy(_playerInGame)
        _newChapter["playerOutGame"] = copy.deepcopy(_playerOutGame)
        _newChapter["playerInRoom"].update(_newChapter["playerInGame"])
        _newChapter["playerInRoom"].update(_newChapter["playerOutGame"])
        for k, v in _newChapter["playerInRoom"].items():
            v["cards"] = []
            v["playedCards"] = []
            v["ready"] = False
            v['goToNext'] = False
            v["identity"] = 0
            v["playCount"] = 0
            v["goldChange"] = 0
            v["boomCount"] = 0
            v["basicScoreChange"] = 0
            v["boomScoresChange"] = 0
            # 清空出牌牌组
            v["outCardList"] = {}
            v["overCardLift"] = False
        # _playerInGameCopy = _newChapter["playerInGame"].copy()

    # 确定大结算方式
    def set_time_for_total(self):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 如果是正常大结算
        if not self.pot and self.settlement_count >= self.info["maxChapterCount"]:
            self.total_settlement()
        # 如果比赛场有人不满足离场分，结束游戏
        elif self.info["roomType"] == "gameCoin" and self.have_player_do_not_meet_end_score():
            self.total_settlement()
        else:
            self.total_settlement(is_disband=True)

    def is_only_left_one_for_next_player(self, account_id, _cp) -> bool:
        """
        下家的手牌数是否为1
        """
        # 获取下个玩家的id
        next_account = self.get_next_player_with_account_id(account_id)
        # DEBUG_MSG("is_only_left_one_for_next_player %s %s %s" % (account_id, next_account, len(_cp["playerInGame"])))
        if len(_cp["playerInGame"][next_account]["cards"]) == 1:
            return True
        return False

    def check_single_1_must_2(self, pre_play_cards, this_play_cards, cards):
        """
        检测是否满足单A必出2
        """
        return RoomType13Calculator.check_single_1_must_2(pre_play_cards, this_play_cards, cards, self.info)

    def check_2_must_bomb(self, pre_play_cards, this_play_cards, cards):
        """
        检测是否满足2必出炸弹
        """
        return RoomType13Calculator.check_2_must_bomb(pre_play_cards, this_play_cards, cards, self.info)

    def check_big_bomb_and_small_bomb(self, pre_play_cards, this_play_cards, cards):
        """
        检测是否满足大炸弹压小炸弹
        """
        return RoomType13Calculator.check_big_bomb_and_small_bomb(pre_play_cards, this_play_cards, cards, self.info)

    def check_single_k_must_1(self, pre_play_cards, this_play_cards, cards):
        """
        检测是否满足单K必出A
        """
        return RoomType13Calculator.check_single_k_must_1(pre_play_cards, this_play_cards, cards, self.info)

    def check_double_k_must_1(self, pre_play_cards, this_play_cards, cards):
        """
        检测是否满足对K必出对A
        """
        return RoomType13Calculator.check_double_k_must_1(pre_play_cards, this_play_cards, cards, self.info)

    def check_straight_not_a(self, pre_play_cards, this_play_cards, cards):
        """
        检测是否满足A不能连
        """
        return RoomType13Calculator.check_straight_not_a(pre_play_cards, this_play_cards, cards, self.info)

    # ==================================================================================================================
    #                                                通用方法
    # ==================================================================================================================
    # 向玩家发送当前的牌局状态
    def send_chapter_state(self, accountEntityId):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息   self.cn 当前局数下标
        self.callClientFunction(accountEntityId, "ChapterState", {"state": _chapter["currentState"]})  # 当前房间状态

    # 获取玩家准备数量
    def get_player_in_game_count(self):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        return len(_chapter["playerInGame"])

    # todo:临时方案，6.28修改
    # 洗牌
    def wash_cards(self):
        player_card1 = []
        player_card2 = []
        player_card3 = []
        game_card = RoomType13Calculator.CreateCards_new(self.info)
        # random.shuffle(game_card)
        for index in range(0, len(game_card)):
            card_pair = game_card[index]
            if index % 3 == 0:
                player_card1.append(card_pair)
            elif index % 3 == 1:
                player_card2.append(card_pair)
            elif index % 3 == 2:
                player_card3.append(card_pair)
        all_cards = [player_card1, player_card2, player_card3]
        return all_cards

    def have_fei_ji(self, target_cards):
        target_cards = RoomType13Calculator.convert_cards_to_value(target_cards)
        length = 2
        three = []
        lianduis = []
        cards = copy.deepcopy(target_cards)
        for i in cards:
            if cards.count(i) >= 3:
                if i not in three:
                    three.append(i)
        three.sort()
        for i in three:
            liandui = []
            num = i
            liandui.append(num)
            liandui.append(num)
            liandui.append(num)
            can_make_up_liandui = True
            for count in range(0, length - 1):
                num += 1
                liandui.append(num)
                liandui.append(num)
                liandui.append(num)
                if num not in three or num >= 15:
                    can_make_up_liandui = False
                    break
            if can_make_up_liandui:
                if liandui not in lianduis:
                    lianduis.append(liandui)
        return lianduis != []

    # 如果有玩家手里有飞机，重新洗牌
    def init_deal_cards(self):
        all_cards = self.wash_cards()  # 洗牌
        # # 如果开启了三带一对或者
        # if self.info['threeAndDouble'] or self.info['threeAndTwoSingle']:
        #     for i in range(200):
        #         all_cards = self.wash_cards()
        #         card1 = all_cards[0]
        #         card2 = all_cards[1]
        #         card3 = all_cards[2]
        #         # 都没有飞机
        #         if not self.have_fei_ji(card1) and not self.have_fei_ji(card2) and not self.have_fei_ji(card3):
        #             break

        return all_cards

    # todo：临时解决方案结束

    # 发牌
    def send_shou_cards_to_player(self):
        """
        TODO E发牌
        """
        all_cards = self.init_deal_cards()

        # todo:测试发牌
        # all_cards[0] = [3.1,3.3,3.1,3.4, 5.1,5.2,6.3, 6.1,6.2,6.4, 7.1, 7.4,7.3, 7.2, 14.4,14.3,14.1]
        # all_cards[1] = [3.1,3.3,3.1,3.4, 5.1,5.2,6.3, 6.1,6.2,6.4, 7.1, 7.4,7.3, 7.2, 14.4,14.3,14.1]
        # all_cards[2] = [3.1,3.3,3.1,3.4, 5.1,5.2,6.3, 6.1,6.2,6.4, 7.1, 7.4,7.3, 7.2, 14.4,14.3,14.1]
        # #####################################################################
        # A多的牌为好牌
        def find_good_cards(all_cards):
            good_index = 0
            good_count = -1
            for cards_index in range(len(all_cards)):
                temp_count = all_cards[cards_index].count(14.1) + all_cards[cards_index].count(14.2) + all_cards[
                    cards_index].count(14.3)
                if temp_count > good_count:
                    good_count = temp_count
                    good_index = cards_index
            return good_index

        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInGame = _chapter["playerInGame"]
        player_cards_data = []

        # 有人输的太多的话，需要发好牌
        is_in_rand_range = self.is_need_rand_score_control("RoomType13")
        luck_player = None  # 幸运玩家
        if is_in_rand_range:
            luck_player = self.select_max_loser(_playerInGame.values())  # 选择输分最多的人作为幸运玩家
            # if luck_player:
            #     self.callClientFunction(luck_player['entity'].id, 'Notice', ['发好牌'])

        if not luck_player:
            def get_max_losing_streak_player(players):
                max_losing_streak_count = 0
                max_losing_streak_player = None
                for p in players:
                    if p['losingstreak'] > max_losing_streak_count:
                        max_losing_streak_count = p['losingstreak']
                        max_losing_streak_player = p
                return max_losing_streak_player, max_losing_streak_count

            luck_player, max_lose_count = get_max_losing_streak_player(_playerInGame.values())
            # 如果有连续输3次的人，每次找好牌发给他
            if max_lose_count < 3:
                luck_player = None
            DEBUG_MSG('最大连输 %s %s' % (max_lose_count, luck_player['entity'].id if luck_player else luck_player))

        if not luck_player:
            # 幸运数字玩家
            is_in_rand_range = self.is_need_rand_score_control("RoomType13")
            if is_in_rand_range:
                luck_player = self.select_luck_max_loser(_playerInGame.values())

        # 每日发好牌次数控制
        day_player = self.select_day_good_pai_player(_playerInGame.values(), 4)
        if day_player:
            luck_player = day_player
            self.player_entity(luck_player).increase_day_pai_control_count()

        max_loser = -1
        if luck_player:
            max_loser = luck_player['entity'].id

        #  给幸运玩家发好牌
        if max_loser > 0:
            good_index = find_good_cards(all_cards)  # A多的牌为好牌
            _playerInGame[max_loser]["cards"] = all_cards[good_index]
            del all_cards[good_index]
            player_cards_data.append(
                {"accountId": int(max_loser), "cards": self.change_value_to_client(_playerInGame[max_loser]["cards"])})
            DEBUG_MSG('good pai player id: %s cards: %s' % (max_loser, _playerInGame[max_loser]["cards"]))

        for k in _playerInGame:
            if max_loser == k:
                continue
            _playerInGame[k]["cards"] = all_cards[0]
            del all_cards[0]
            player_cards_data.append(
                {"accountId": int(k), "cards": self.change_value_to_client(_playerInGame[k]["cards"])})

        # 每局发牌时将系统自留的一手牌置空
        self.OtherCardPlan.clear()
        if len(_playerInGame) == 2:
            self.OtherCardPlan = all_cards[-1]
            self.OtherCardPlan.sort()
            player_cards_data.append({"accountId": int(-1), "cards": self.change_value_to_client(self.OtherCardPlan)})
        all_cards_data_info = {"playerCards": player_cards_data}
        self.callOtherClientsFunction("DealCards", all_cards_data_info)

        # 记录发牌回放
        record = {"operationType": 0, "operationArgs": {"playerCards": player_cards_data}}
        _chapter["operationRecord"].append(record)

    # 获取准备玩家信息
    def get_ready_player(self):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        ready_players = []
        for k, v in chapter["playerInGame"].items():
            if v["ready"]:
                ready_players.append(k)
        return ready_players

    def is_all_player_ready_ok(self):
        """
        判断所有玩家是否准备完毕
        """
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        if self.is_less_mode:  # 少人模式
            if len(chapter["playerInGame"]) < 2:
                return False
        elif len(chapter["playerInGame"]) != self.info["maxPlayersCount"]:
            return False
        for k, v in chapter["playerInGame"].items():
            if not v["ready"]:
                return False
        return True

    # 玩家自动准备
    def auto_ready_for_player_in_game(self):
        # 第二局以后开始自动准备不超过最大局数
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        if self.cn >= 0:  # self.cn 当前局数下标
            for k, v in _chapter["playerInGame"].items():
                self.player_ready(k)

    # 判断玩家手中是有指定的牌
    def get_card_value_for_want(self, ScoureCard, FindCard):
        """
        params: ScoureCard list
                FindCard   int
        """
        if ScoureCard.count(FindCard):
            return True
        return False

    # 获取手牌最小的玩家
    def find_min_card(self):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        min_card = 15.1
        min_account_id = -1
        for k, v in _chapter["playerInGame"].items():
            v["cards"].sort()
            if v["cards"][0] < min_card:
                min_card = v["cards"][0]
                min_account_id = k
        return min_account_id

    # 检查牌局是否结束
    def check_chapter_over(self):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        for k, v in chapter["playerInGame"].items():
            if len(v["cards"]) == 0:
                chapter["winner"] = k
                self.gameWinner = k
                return True
        return False

    # 转换成客户端的值
    def change_value_to_client(self, cards):
        if len(cards) == 0:
            return []
        card_nums = []
        type_card = -1
        for card in cards:
            Type, value = math.modf(card)
            if round(Type, 1) == 0.1:
                type_card = 0
            if round(Type, 1) == 0.2:
                type_card = 3
            if round(Type, 1) == 0.3:
                type_card = 2
            if round(Type, 1) == 0.4:
                type_card = 1
            card_nums.append(int((value - 3) * 4 + type_card))
        return card_nums

    # 转换成服务器的值
    def change_value_to_server(self, cards):
        """
        前端传入的牌
        把前端转入的牌 转换成服务器的值
        """
        if len(cards) == 0:
            return []
        card_nums = []
        card_color = -1
        for card in cards:
            card_type = card % 4
            card_value = int(card / 4) + 3
            if card_type == 3:
                card_color = 0.2
            if card_type == 2:
                card_color = 0.3
            if card_type == 1:
                card_color = 0.4
            if card_type == 0:
                card_color = 0.1
            card_nums.append(card_value + card_color)
        return card_nums

    # 判断客户端是否在线
    def is_player_offline(self, account_id):
        """
        获取离线玩家ID
        :return:
        """
        chapter = self.get_current_chapter()
        for k, v in chapter["playerInGame"].items():
            DEBUG_MSG("Is del:%s" % chapter["playerInGame"][account_id]['entity'].client_death)
            if k == account_id:
                if v['entity'].client_death:
                    return True
                else:
                    return False

    def is_auto_play_card(self, account_id):
        """
        自动出牌
        """
        chapter = self.get_current_chapter()
        for k, v in chapter["playerInGame"].items():
            if k == account_id:
                return v["autoPlayCard"]
        return False

    def start_auto_play(self, account_entity_id):
        """
        开始自动出牌
        """
        chapter = self.get_current_chapter()
        for k, v in chapter["playerInGame"].items():
            if k == account_entity_id:
                if not v["autoPlayCard"]:
                    v["autoPlayCard"] = True
                    self.callClientFunction(account_entity_id, 'AutoPlayStart', {})
                break

    def cancel_auto_play(self, account_entity_id):
        chapter = self.get_current_chapter()
        for k, v in chapter["playerInGame"].items():
            if k == account_entity_id:
                v["autoPlayCard"] = False
                break

    # 出牌是否比上家大
    def is_current_card_greater(self, current_cards, pre_cards):
        # 同牌型比较 必须是同牌型，同长度
        return RoomType13Calculator.compare_cards(current_cards, pre_cards, self.info)

    # 获取下一个玩家id
    def get_next_player_with_account_id(self, account_id) -> int:
        """
        获取下一个游戏玩家id
        """
        location_index = -1
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        for k, v in chapter["playerInGame"].items():
            if account_id == k:
                location_index = v["locationIndex"]
                break

        max_player_count = self.info["maxPlayersCount"]
        if location_index != -1:
            for i in range(1, max_player_count):
                new_location_index = (location_index + i) % max_player_count
                find_result = self.get_player_with_location_index(new_location_index)
                if find_result is not None:
                    return find_result
        else:
            return -1

    # 根据玩家位置获取玩家
    def get_player_with_location_index(self, location_index):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息
        for k, v in chapter["playerInGame"].items():
            if location_index == v["locationIndex"]:
                return k

    # 1 关闭所有的定时器
    def close_all_timer(self):
        DEBUG_MSG("************************stop all timer*********************************************")
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        chapter["goToNext"] = -1
        self.delTimer(chapter["goToNext"])
        chapter["showLastTime"] = -1
        self.delTimer(chapter["showLastTime"])
        chapter["chapterStartTimerId"] = -1
        self.delTimer(chapter["chapterStartTimerId"])
        chapter["mainTimerId"] = -1
        self.delTimer(chapter["mainTimerId"])
        chapter["chapterStartTimerId"] = -1
        self.delTimer(chapter["chapterStartTimerId"])
        chapter["dealCardAnimationTimerId"] = -1
        self.delTimer(chapter["dealCardAnimationTimerId"])
        chapter["setPosAnimationTimerId"] = -1
        self.delTimer(chapter["setPosAnimationTimerId"])
        chapter["playCardTimer"] = -1
        self.delTimer(chapter["playCardTimer"])
        chapter["settlementTimer"] = -1
        self.delTimer(chapter["settlementTimer"])
        chapter["seatAnimationTimerId"] = -1
        self.delTimer(chapter["seatAnimationTimerId"])
        self.disband_timer = -1
        self.delTimer(self.disband_timer)

    # 玩家点击继续
    def start_next_chapter(self, account_id):
        if self.total_settlement_ed:  # 总结算设置位
            return
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        if account_id not in chapter['playerInGame']:
            return

        _player = chapter["playerInGame"][account_id]
        # 如果是比赛场,准备时金币不能小于0
        if self.info["roomType"] == "gameCoin" and _player['gold'] < self.info['readyGoldLimit']:
            self.callClientFunction(account_id, 'Notice', ['您的比赛分不足,请您立即充值.'])
            # 设置玩家准备状态为False
            return
        chapter["playerInGame"][account_id]["goToNext"] = True
        for k, v in chapter["playerInGame"].items():
            if not v["goToNext"]:
                return
        self.delTimer(chapter["settlementTimer"])
        chapter["settlementTimer"] = -1
        # self.chapter_clear()
        self.changeChapterState(0)

    # 写入数据库
    def write_chapter_info_to_db(self):
        """
        牌局信息写入库
        :return:
        """

        # 8.7 改为每局都写入战绩，即使未完成
        # 至少打一局才写入库中
        # if self.settlement_count < 1:
        #     return
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInGame = _chapter["playerInGame"]
        _playerData = {}
        _playerInfo = []
        _history_record = {}
        # 1 牌局的回放
        chapter_replays = {}
        # 存储回放数据
        replay_data = {"chapterInfo": {}}
        # 判断如果最后一局未到结算状态，不计入战绩
        chapter_record_max_count = self.cn + 1  # self.cn 当前局数下标
        # 1 循环所有局数
        for c in range(0, chapter_record_max_count):
            chapter_info = self.chapters[c]  # self.chapters 牌局信息
            chapter_players_data = []
            # 循环牌局中的玩家信息
            for k, v in chapter_info["playerInGame"].items():
                # 战绩玩家信息
                _playerData = {"accountId": k, "name": v["entity"].info["name"],
                               "goldChange": v["goldChange"], "userId": v["entity"].info["userId"],
                               "identity": v["identity"], "locationIndex": int(v["locationIndex"]),
                               "databaseId": v["entity"].info["dataBaseId"], "gold": round(float(v['gold']), 1)
                               }
                # 存储玩家信息  base端的显示的总战绩
                chapter_players_data.append(_playerData)

            # 存放所有的牌局数据
            _history_record[c] = chapter_players_data
            _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                     "maxChapterCount": self.info["maxChapterCount"],
                     "playerInfo": chapter_players_data, "historyRecord": _history_record
                     }
            # 存储每局的步骤信息和玩家信息
            chapter_replay = chapter_info["operationRecord"]
            chapter_replays[c] = {"playerInfo": chapter_players_data, "operationReplay": chapter_replay,
                                  'recordCards': chapter_info['recordCards']}

        # 存储房间信息以及步骤信息
        replay_data["chapterInfo"] = chapter_replays

        # 记录战绩的玩家
        record_players = []
        for k, v in _playerInGame.items():
            _playerData = {"accountId": k, "accountName": v["entity"].info["name"], "winnerBilling": v["winnerBilling"],
                           "overBilling": v["overBilling"],
                           "otherBilling": v["otherBilling"], "totalGoldChange":
                            v["totalGoldChange"], "userId": v["entity"].info["userId"],
                           "headImageUrl": v["entity"].info["headImageUrl"],
                           "gold": v['gold'] - v['totalGoldChange'],
                           "totalGold": v["gold"]
                           }
            # 1 玩家数据
            _playerInfo.append(_playerData)
            record_players.append(v["entity"].info["userId"])

        _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                 "maxChapterCount": self.info["maxChapterCount"],
                 "playerInfo": _playerInfo, "historyRecord": _history_record}
        self._chapterInfos = _args
        self.base.cellToBase({"func": "writeChapterInfo", "chapterInfos": self._chapterInfos})
        # 通知base存储入数据库
        self.chapter_replay = replay_data
        self.base.cellToBase({"func": "writeChapterReplay", "chapterReplay": self.chapter_replay})
        if self.is_tea_house_room:
            # 通知base的朋友圈记录该房间
            self.base.cellToBase(
                {"func": "writeTeaHouseRoom", "teaHouseId": self.info["teaHouseId"], "type": self.info["type"],
                 'recordPlayers': record_players})
        DEBUG_MSG('[Room id %i]------>writeChapterInfoToDB, _chapterInfos %s ' % (self.id, self._chapterInfos))

    # 玩家离开房间
    def onLeave(self, account_entity_id, leave_param=None):
        """
        离开房间
        :param account_entity_id:
        :return:
        """
        player_online = True
        DEBUG_MSG('[Room id %i]------>onLeave accountId %s, emptyLocationIndex %s' % (
            self.id, account_entity_id, self.emptyLocationIndex))
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _currentState = _chapter["currentState"]  # 当前房间状态
        if account_entity_id in _playerInGame:
            # 判断游戏是否处于刚开始阶段,总结算阶段
            if _currentState != 0 and _currentState != 5:  # 当前房间状态
                self.callClientFunction(account_entity_id, "Notice", ["游戏正在游戏中,请等待游戏结束"])
                return

            _player = _playerInGame[account_entity_id]
            _playerInGame.pop(account_entity_id)
            _playerInRoom.pop(account_entity_id)
            if _player["locationIndex"] not in self.emptyLocationIndex:
                self.emptyLocationIndex.append(_player["locationIndex"])
            if player_online:
                if leave_param is None:
                    leave_param = {"inviteRoomInfo": None}
                leave_param.update({"result": 1})
                another_room = {}
                if 'JoinAnotherRoom' in leave_param:
                    del leave_param['JoinAnotherRoom']
                    another_room = leave_param['inviteRoomInfo']
                    del leave_param['inviteRoomInfo']
                self.callClientFunction(account_entity_id, "LeaveRoomResult", leave_param)
                if another_room:
                    self.callClientFunction(account_entity_id, "JoinAnotherRoom", another_room)
                _player["entity"].destroySelf()
            if account_entity_id in _playerOutGame:
                _player = _playerOutGame[account_entity_id]
                _playerOutGame.pop(account_entity_id)
                _playerInRoom.pop(account_entity_id)
                if player_online:
                    if leave_param is None:
                        leave_param = {"inviteRoomInfo": None}
                    leave_param.update({"result": 1})
                    another_room = {}
                    if 'JoinAnotherRoom' in leave_param:
                        del leave_param['JoinAnotherRoom']
                        another_room = leave_param['inviteRoomInfo']
                        del leave_param['inviteRoomInfo']
                    self.callClientFunction(account_entity_id, "LeaveRoomResult", leave_param)
                    if another_room:
                        self.callClientFunction(account_entity_id, "JoinAnotherRoom", another_room)
                if player_online:
                    _player["entity"].destroySelf()
            # 有观战玩家离开
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.ret_out_game_player_info(k)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.ret_out_game_player_info(k)
            self.ret_player_in_room_info()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_playerInGame)})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

        if account_entity_id in _playerOutGame and account_entity_id in self.wait_to_seat:
            self.callClientFunction(account_entity_id, 'Notice', ['已坐下，暂时无法离开房间'])
            return

        if account_entity_id in _playerOutGame:
            _player = _playerOutGame[account_entity_id]
            _playerOutGame.pop(account_entity_id)
            _playerInRoom.pop(account_entity_id)
            if player_online:
                if leave_param is None:
                    leave_param = {"inviteRoomInfo": None}
                leave_param.update({"result": 1})
                another_room = {}
                if 'JoinAnotherRoom' in leave_param:
                    del leave_param['JoinAnotherRoom']
                    another_room = leave_param['inviteRoomInfo']
                    del leave_param['inviteRoomInfo']
                self.callClientFunction(account_entity_id, "LeaveRoomResult", leave_param)
                if another_room:
                    self.callClientFunction(account_entity_id, "JoinAnotherRoom", another_room)
            if player_online:
                _player["entity"].destroySelf()
            self.ret_out_game_player_info()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_playerInGame)})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 从实体列表中移除
        if account_entity_id in self.accountEntities.keys():
            self.accountEntities.pop(account_entity_id)
            self.base.cellToBase({"func": "LogoutRoom", "accountId": account_entity_id})
        if account_entity_id in self.wait_to_seat:
            self.wait_to_seat.remove(account_entity_id)
        if account_entity_id in self.agree_less_person_mode_players:
            self.agree_less_person_mode_players.remove(account_entity_id)
        self.autoDestroy()
        self.notify_viewing_hall_players_room_info()

    def change_less_person_mode_switch(self, entity_id, _args):
        """
        玩家同意/不同意少人模式
        :param entity_id:
        :param _args:
        :return:
        """
        state = _args['state']
        if state:
            if entity_id not in self.agree_less_person_mode_players:
                self.agree_less_person_mode_players.append(entity_id)
        else:
            if entity_id in self.agree_less_person_mode_players:
                self.agree_less_person_mode_players.remove(entity_id)
        self.callOtherClientsFunction('agreeLessPersonModePlayers', {'players': self.agree_less_person_mode_players})
        if self.is_all_player_ready_ok():
            # 只有初始阶段可以通过同意少人模式开始
            chapter = self.get_current_chapter()
            if chapter['currentState'] != 0:  # 当前房间状态
                return
            if self.total_settlement_ed:  # 总结算设置位
                return
            self.chapter_start()
            # 改变牌局状态机状态(流程移交状态机)
            self.changeChapterState(1)

    # 客户端进程死亡
    def onPlayerClientDeath(self, accountEntity):
        DEBUG_MSG("RoomType13 onPlayerClientDeath accountId:%s" % accountEntity)
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标

        for k, v in chapter["playerInGame"].items():
            if v["entity"] == accountEntity:
                v["online"] = False
                # 总结算或者准备阶段掉线，自动踢出
                if chapter["currentState"] == 0 or chapter["currentState"] == 7:  # 当前房间状态
                    self.kick_out(k, player_online=False)
                break

        all_offline = True
        for k, v in chapter["playerInGame"].items():
            if v["online"]:
                all_offline = False
                break

        if all_offline:
            for k, v in copy.deepcopy(chapter["playerInGame"]).items():
                self.kick_out(k, player_online=False)

    # 检测玩家离开房间
    def kick_out(self, accountEntityId, isBot=False, player_online=True):
        """
                离开房间
                :param accountEntityId:
                :return:
                """
        DEBUG_MSG('[Room id %i]------>onLeave accountId %s' % (self.id, accountEntityId))
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _currentState = _chapter["currentState"]  # 当前房间状态
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
            self.ret_player_in_room_info()
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
            self.ret_player_in_room_info()
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 从实体列表中移除
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
            DEBUG_MSG("onLeave account_entities:%s" % self.accountEntities)
        self.autoDestroy()

    # 重连
    def reconnect(self, account_id):
        """
        请求重连
        :param account_id: 重连玩家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>reconnect %s' % (self.id, account_id))
        self.retRoomBaseInfo(account_id)
        self.ret_player_in_room_info(account_id)
        self.ret_chapter_info(account_id)

    # 换桌
    def change_table(self, account_id):
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _currentState = _chapter["currentState"]  # 当前房间状态
        if account_id in _playerInGame:
            _player = _playerInGame[account_id]
            _playerInGame.pop(account_id)
            _playerInRoom.pop(account_id)
            _player["entity"].destroySelf()
            self.ret_player_in_room_info()
        if account_id in _playerOutGame:
            _player = _playerOutGame[account_id]
            _playerOutGame.pop(account_id)
            _playerInRoom.pop(account_id)
            _player["entity"].destroySelf()
            self.ret_player_in_room_info()
        self.base.cellToBase(
            {"func": "changeTable", "accountId": account_id, "type": self.info["type"], "level": self.info["level"]})

    # 群主解散房间
    def tea_house_disband_room_by_creator(self):
        """
        群主解散房间
        :return:
        """
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        player_in_game = _chapter["playerInGame"].copy()
        self.disband_from_creator = True
        if not self.started:
            for k, v in player_in_game.items():
                self.kick_out(k)
            else:
                self.autoDestroy()
            return
        # self.chapters 牌局信息
        if self.chapters[self.cn]["currentState"] != 5:  # 当前房间状态  self.cn 当前局数下标
            self.changeChapterState(5)

    # 获取玩家距离
    def get_distance_relation(self, account_id):
        """
        获取玩家之间的距离
        :param account_id:
        :return:
        """
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        player_entity_id_s = []
        player_in_game = _chapter["playerInGame"]
        distance_info = {}
        for k, v in _chapter["playerInGame"].items():
            player_entity_id_s.append(k)
        if len(_chapter["playerInGame"]) == 1:
            self.callClientFunction(account_id, "distanceFromEveryone", distance_info)
        if len(_chapter["playerInGame"]) == 2:
            # 玩家 id
            _player_1 = player_entity_id_s[0]
            _player_2 = player_entity_id_s[1]
            # 玩家实体
            _player_1_entity = player_in_game[_player_1]['entity']
            _player_2_entity = player_in_game[_player_2]['entity']
            longitude_1 = int(_player_1_entity.info["longitude"])
            longitude_2 = int(_player_2_entity.info["longitude"])
            latitude_1 = int(_player_1_entity.info["latitude"])
            latitude_2 = int(_player_2_entity.info["latitude"])
            # 玩家之间的距离为-1
            _distance_1 = Util.getdistance(longitude_1, latitude_1, longitude_2, latitude_2)

            if _distance_1 != -1:
                relation_1 = str(_player_1) + ',' + str(_player_2)
                distance_info[relation_1] = round(_distance_1, 2)

            self.callClientFunction(account_id, "distanceFromEveryone", distance_info)
        if len(_chapter["playerInGame"]) == 3:
            # 玩家 id
            _player_1 = player_entity_id_s[0]
            _player_2 = player_entity_id_s[1]
            _player_3 = player_entity_id_s[2]
            # 玩家实体
            DEBUG_MSG("player_distance:%s" % len(_chapter["playerInGame"]))
            _player_1_entity = player_in_game[_player_1]['entity']
            _player_2_entity = player_in_game[_player_2]['entity']
            _player_3_entity = player_in_game[_player_3]['entity']
            long_1 = _player_1_entity.info["longitude"]
            long_2 = _player_2_entity.info["longitude"]
            long_3 = _player_3_entity.info["longitude"]
            lat_1 = _player_1_entity.info["latitude"]
            lat_2 = _player_2_entity.info["latitude"]
            lat_3 = _player_3_entity.info["latitude"]
            # 玩家之间的距离
            _distance_1 = Util.getdistance(long_1, lat_1, long_2, lat_2)
            _distance_2 = Util.getdistance(long_1, lat_1, long_3, lat_3)
            _distance_3 = Util.getdistance(long_2, lat_2, long_3, lat_3)

            if _distance_1 != -1:
                relation_1 = str(_player_1) + ',' + str(_player_2)
                distance_info[relation_1] = round(_distance_1, 2)

            if _distance_2 != -1:
                relation_2 = str(_player_1) + ',' + str(_player_3)
                distance_info[relation_2] = round(_distance_2, 2)

            if _distance_3 != -1:
                relation_3 = str(_player_2) + ',' + str(_player_3)
                distance_info[relation_3] = round(_distance_3, 2)

            # 玩家之间的关系
            # 距离信息
            self.callClientFunction(account_id, "distanceFromEveryone", distance_info)

    # 刷新客户端状态
    def refresh_client_state(self):
        """
        刷新玩家在线状态
        :return:
        """
        DEBUG_MSG("This value can get the Client'status del or hadon")
        chapter = self.get_current_chapter()
        client_state = {}
        for k, v in chapter["playerInGame"].items():
            client_state[v['entity'].id] = not v['entity'].client_death
        self.callOtherClientsFunction('RefreshOnlineState', client_state)

    # 聊天
    def send_chat(self, accountEntityId, content):
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        player_chat_data = {accountEntityId: content}
        if len(chapter["chatHistory"]) > 10:
            del chapter["chatHistory"][0]
        chapter["chatHistory"].append(player_chat_data)
        args = {"accountId": accountEntityId, "content": content}
        self.callOtherClientsFunction("SendChat", args)

    # 快捷语广播
    def send_common_chat(self, accountEntityId, index):
        args = {"accountId": accountEntityId, "index": index}
        self.callOtherClientsFunction("SendCommonChat", args)

    # 1 分享到微信   邀请
    def share_to_wx(self, account_id):
        if self.info['roomType'] == 'card':
            title = '跑得快房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '跑得快房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '跑得快房间'
        max_chapter_count = '最大局数：' + str(self.info['maxChapterCount'])
        base_score = '底分' + str(self.info['baseScore'])
        if 'canVoice' in self.info:
            can_voice = '语音开启' if self.info['canVoice'] else '禁用语音'
        else:
            can_voice = ''
        con = str('%s,%s,%s,%s' % (max_chapter_count, base_score, 1, can_voice))
        self.callClientFunction(account_id, 'ShareToWX', {'title': title, 'content': con})

    # 跑的快表情
    def send_emotion(self, account_id, index):
        """
        表情聊天
        :param emotion_type:
        :param account_id:
        :param index:
        :return:
        """
        _args = {"accountId": account_id, "index": index}
        self.callOtherClientsFunction("SendEmotion", _args)

    def quest_disband_room(self, accountId):
        """
        解散房间请求
        :param accountId:
        :return:
        """
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 1 正在解散状态中
        if self.is_disbanding:
            return
        if self.total_settlement_ed:  # 总结算设置位
            return
        # 1 牌局中游戏玩家
        if len(_chapter["playerInGame"]) == 1:
            # 投票解散
            self.is_manual_disband = True
            self.disband_timer = -1
            self.delTimer(self.disband_timer)
            self.is_disbanding = False
            args = {"result": 1}
            # 1 解散房间广播
            self.callOtherClientsFunction("DisbandRoomResult", args)
            # 1 总结算
            self.changeChapterState(5)
            return
        if accountId not in _chapter["playerInGame"]:
            return
        _chapter["playerInGame"][accountId]["agreeDisband"] = True
        self.disband_sender = accountId
        self.is_disbanding = True
        args = {"accountId": accountId, "disbandTime": time_disband}
        self.callOtherClientsFunction("RequestDisbandRoom", args)

        # 解散房间倒计时
        self.disband_timer = self.addTimer(time_disband, 0, 0)
        DEBUG_MSG(self.disband_timer)
        _chapter["deadline"] = time.time() + time_disband

    def response_disband_room(self, accountId, result):
        """
        解散房间回应
        :param accountId:
        :param result:
        :return:
        """

        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 有一人拒绝就解散失败
        if result == 0:
            args = {"accountId": accountId, "result": result}
            self.callOtherClientsFunction("DisbandRoomOperation", args)
            self.disband_timer = -1
            self.delTimer(self.disband_timer)
            for k, v in chapter["playerInGame"].items():
                v["agreeDisband"] = False
            args = {"result": 0}
            self.callOtherClientsFunction("DisbandRoomResult", args)
            self.is_disbanding = False
            return
        if result == 1:
            chapter["playerInGame"][accountId]["agreeDisband"] = True
            args = {"accountId": accountId, "result": result}
            self.callOtherClientsFunction("DisbandRoomOperation", args)
            for k, v in chapter["playerInGame"].items():
                if not v["agreeDisband"]:
                    return
            # 投票解散
            self.is_manual_disband = True
            self.disband_timer = -1
            self.delTimer(self.disband_timer)
            self.is_disbanding = False
            args = {"result": 1}
            self.callOtherClientsFunction("DisbandRoomResult", args)
            self.changeChapterState(5)

    # 发送表情
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

    def voiceChat(self, accountId, url):
        """
        语音聊天
        :param accountId:
        :param url:
        :return:
        """
        _args = {"accountId": accountId, "url": url}
        self.callOtherClientsFunction("VoiceChat", _args)

    def have_player_do_not_meet_end_score(self):
        """
        是否有玩家不满足离场分
        """
        chapter = self.chapters[self.cn]
        for k, v in chapter['playerInGame'].items():
            if v['gold'] <= self.info['endScore']:
                return True
        return False

    # ==================================================================================================================
    #                                                 玩家操作
    # ==================================================================================================================
    def playerOperation(self, account_entity_id, jsonData):
        DEBUG_MSG('[Room id %i]------>playerOperation accountId %s ,jsonData %s' %
                  (self.info["roomId"], account_entity_id, jsonData))
        _py_dic = json.loads(jsonData)
        _func = _py_dic["func"]
        _data = _py_dic["args"]
        _playerInGame = self.chapters[self.cn]["playerInGame"]  # self.chapters 牌局信息  self.cn 当前局数下标
        # 玩家准备
        if _func == "Ready":
            self.player_ready(account_entity_id)  # 玩家准备
            if self.get_seat_player_by_entity_id(account_entity_id)["ready"]:
                self.get_player_entity(account_entity_id).update_player_stage(Account.PlayerStage.READY)
                self.notify_viewing_hall_players_room_info()
            if self.is_all_player_ready_ok():  # 所有玩家准备完毕
                # 只有初始阶段、或者小局结算阶段可以通过准备开始游戏
                chapter = self.get_current_chapter()  # 获取当前牌局
                if chapter['currentState'] != 0 and chapter['currentState'] != 4:  # E当前房间状态
                    return
                if self.total_settlement_ed:  # 总结算设置位
                    return
                self.chapter_start()  # 修改房间状态为开始
                # 改变牌局状态机状态(流程移交状态机)
                self.changeChapterState(1)  # 牌局开始、发牌状态
        # 观战中下局可以开始游戏的玩家
        elif _func == "NextGameSit":
            self.want_next_game_seat(account_entity_id)
        # 玩家出牌
        elif _func == "PlayCards":
            self.player_play_cards(account_entity_id, _data["cards"])
        elif _func == "PlayTips":
            self.play_tips(account_entity_id)
        # 玩家离开房间
        elif _func == "LeaveRoom":
            self.onLeave(account_entity_id, _data)
        # 玩家点击继续
        elif _func == "ContinueNextChapter":
            self.start_next_chapter(account_entity_id)
        # 1 表情
        elif _func == "SendEmotion":
            self.send_emotion(account_entity_id, _data["index"])
        # 聊天
        elif _func == "SendChat":
            self.send_chat(account_entity_id, _data["content"])
        # 1 快捷语广播
        elif _func == "SendCommonChat":
            self.send_common_chat(account_entity_id, _data["index"])
        # 重连
        elif _func == "Reconnect":
            self.reconnect(account_entity_id)
        # 换桌
        elif _func == "ChangeTable":
            self.change_table(account_entity_id)
        elif _func == "GetPlayersRemainCards":
            self.send_players_remain_cards(account_entity_id)
        #  1 玩家点击祈福动画
        elif _func == "Bless":
            self.bless(account_entity_id, _data["type"])
        elif _func == 'FreeBlessCount':
            self.free_bless_count(account_entity_id)
        # 发送表情
        elif _func == "EmotionChat":
            self.emotion_chat(account_entity_id, _data["index"], _data["type"])
        # 解散房间相关操作
        elif _func == "DisbandRoom":
            if self.is_forbid_disband_room():
                self.callClientFunction(account_entity_id, 'Notice', ['该房间禁止中途解散'])
                return
            self.quest_disband_room(account_entity_id)
        # 解散房间回应
        elif _func == "DisbandRoomOperation":
            self.response_disband_room(account_entity_id, _data["result"])
        # 语音聊天
        elif _func == "VoiceChat":
            self.voiceChat(account_entity_id, _data["url"])
            # 1 分享到微信
        elif _func == 'ShareToWX':
            self.share_to_wx(account_entity_id)
        # 获取玩家距离
        elif _func == 'distanceFromEveryone':
            self.get_distance_relation(account_entity_id)
        elif _func == 'CancelAutoPlay':
            self.cancel_auto_play(account_entity_id)
            self.callClientFunction(account_entity_id, 'CancelAutoPlay', {"result": True})

    def save_record_str(self):
        game_type = '跑得快'
        current_chapter = self.settlement_count
        max_chapter_count = self.info['maxChapterCount']
        chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标
        _plays = chapter['playerInGame']
        total_settlement_info = []
        for p in _plays.values():
            _dict = {'name': p['entity'].info['name'], 'totalGoldChange': p['totalGoldChange']}
            total_settlement_info.append(_dict)
        self.record_str = self.get_chapter_record_str(game_type, current_chapter,
                                                      max_chapter_count, total_settlement_info)

    def refresh_game_coin(self, account_db_id, modify_count):
        """
        刷新房间内比赛分
        :param account_db_id:
        :param modify_count:
        :return:
        """
        _chapter = self.chapters[self.cn]  # self.chapters 牌局信息  self.cn 当前局数下标  self.cn 当前局数下标
        if self.info["roomType"] == "gameCoin":
            for k, v in _chapter["playerInRoom"].items():
                if v["entity"].info["dataBaseId"] == account_db_id:
                    v["gold"] += modify_count
                    self.callOtherClientsFunction("refreshGameCoin", {"gameCoin": v["gold"], "accountId": k})
                    self.reconnect(k)
                    break

        # 如果都满足准备条件，关闭倒计时
        all_can_ready = self.check_ready_gold_disband()
        if all_can_ready:
            self.delTimer(self.ready_gold_disband_timer)
            self.ready_gold_disband_timer = -1

    def check_ready_gold_disband(self):
        chapter = self.get_current_chapter()
        # 所有人都
        all_can_ready = True
        if self.info["roomType"] == "gameCoin":
            for k, v in chapter['playerInGame'].items():
                if v['gold'] < self.info['readyGoldLimit']:
                    all_can_ready = False
                    break

        return all_can_ready

    def is_forbid_disband_room(self):
        """
        禁止中途解散房间
        """
        return self.info["canNotDisbandOnPlay"]

    def round_int(self, v):
        if v > 0:
            return int(v + 0.51)
        return int(v)

    # 锅子开关
    @property
    def pot(self):
        return self.info['pot']

    # 锅子分数
    @property
    def potScore(self):
        return self.info['potScore']

    @property
    def single_max(self):
        """
        报单顶大
        :return:
        """
        return 'singleMax' in self.info and self.info['singleMax']

    @property
    def bomb_multiple(self):
        """
        炸弹翻倍
        :return:
        """
        return 'bombMultiple' in self.info and self.info['bombMultiple']

    @property
    def three_and_two_single(self):
        """
        三代两单
        :return:
        """
        return 'threeAndTwoSingle' in self.info and self.info['threeAndTwoSingle']

    @property
    def lose_all(self):
        """
        放走包赔
        :return:
        """
        return 'loseAll' in self.info and self.info['loseAll']

    @property
    def initiative_bomb_not_score(self):
        """
        空炸不算分
        """
        return self.info['initiativeBombNotScore']

    @property
    def single_k_must_a(self):
        """
        单K必出A
        """
        return self.info['singleKMustA']

    @property
    def double_k_must_a(self):
        """
        对K必出A
        """
        return self.info['doubleKMustA']

    @property
    def straight_not_a(self):
        """
        A不能连
        """
        return self.info['straightNotA']
