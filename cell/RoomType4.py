# -*- coding: utf-8 -*-
import copy
from random import shuffle

import KBEngine

import Const
from KBEDebug import *
from RoomBase import *
import json
import time
import datetime
import NiuNiuCalculator
import Account

# 准备倒计时时间
_timeReady = 0
# 给一个玩家发牌动画时间
_timeDealCardToPlayer = 0.3
# 结算时间
_timeSettlement = 5
# 开始游戏动画时间
_timeStart = 1
# 切锅倒计时
_timeSwitchPot = 5
# 投票解散房间
time_disband = 30
# 总结算清理玩家倒计时
settlement_clear_players_time = 30
# 房间中的玩家
PLAYER_IN_GAME = "playerInGame"
# 观战玩家
PLAYER_OUT_GAME = 'playerOutGame'

_sanPai = 0
_niuYi = 1
_niuEr = 2
_niuSan = 3
_niuSi = 4
_niuWu = 5
_niuLiu = 6
_niuQi = 7
_niuBa = 8
_niuJiu = 9
_niuNiu = 10
_siHuaNiu = 11
_wuHuaNiu = 12
_shunZiNiu = 13
_tongHuaNiu = 14
_huLuNiu = 15
_zhaDanNiu = 16
_tongHuaShun = 17
_wuXiaoNiu = 18

# 普通模式
_play_mode0 = {_sanPai: 1, _niuYi: 1, _niuEr: 1, _niuSan: 1, _niuSi: 1, _niuWu: 1, _niuLiu: 1, _niuQi: 2, _niuBa: 2,
               _niuJiu: 3, _niuNiu: 4,
               _siHuaNiu: 4, _wuHuaNiu: 5, _shunZiNiu: 6, _tongHuaNiu: 6, _huLuNiu: 6, _zhaDanNiu: 6,
               _tongHuaShun: 7, _wuXiaoNiu: 8}
# 激情模式
_play_mode1 = {_sanPai: 1, _niuYi: 1, _niuEr: 1, _niuSan: 1, _niuSi: 1, _niuWu: 1, _niuLiu: 1, _niuQi: 2, _niuBa: 3,
               _niuJiu: 4, _niuNiu: 5,
               _siHuaNiu: 6, _wuHuaNiu: 6, _shunZiNiu: 6, _tongHuaNiu: 7, _huLuNiu: 7, _zhaDanNiu: 8,
               _tongHuaShun: 10, _wuXiaoNiu: 9}

# 疯狂模式
_play_mode2 = {_sanPai: 1, _niuYi: 1, _niuEr: 2, _niuSan: 3, _niuSi: 4, _niuWu: 5, _niuLiu: 6, _niuQi: 7, _niuBa: 8,
               _niuJiu: 9, _niuNiu: 10,
               _siHuaNiu: 10, _wuHuaNiu: 11, _shunZiNiu: 11, _tongHuaNiu: 12, _huLuNiu: 12, _zhaDanNiu: 13,
               _tongHuaShun: 15, _wuXiaoNiu: 14}

# 普通模式
_play_mode3 = {_sanPai: 1, _niuYi: 1, _niuEr: 1, _niuSan: 1, _niuSi: 1, _niuWu: 1, _niuLiu: 1, _niuQi: 2, _niuBa: 2,
               _niuJiu: 2, _niuNiu: 3,
               _siHuaNiu: 4, _wuHuaNiu: 5, _shunZiNiu: 6, _tongHuaNiu: 6, _huLuNiu: 6, _zhaDanNiu: 6,
               _tongHuaShun: 7, _wuXiaoNiu: 8}

# 普通模式
_play_mode4 = {_sanPai: 1, _niuYi: 1, _niuEr: 1, _niuSan: 1, _niuSi: 1, _niuWu: 1, _niuLiu: 1, _niuQi: 1, _niuBa: 2,
               _niuJiu: 2, _niuNiu: 3,
               _siHuaNiu: 4, _wuHuaNiu: 5, _shunZiNiu: 6, _tongHuaNiu: 6, _huLuNiu: 6, _zhaDanNiu: 6,
               _tongHuaShun: 7, _wuXiaoNiu: 8}


class RoomType4(RoomBase):
    _chapterInfos = {}
    waiGuaPlayer = None
    settlement_count = 0
    disband_from_creator = False
    total_settlement_ed = False
    is_manual_disband = False
    started = False

    emptyLocationIndex = []

    # 持续当庄次数
    keep_banker_count = 0

    # 进入顺序
    enter_list = []

    def __init__(self):
        RoomBase.__init__(self)
        # 牌型倍数
        self._cardTypeMultiple = _play_mode0
        # 房间内玩家集合
        self.player_list = []
        # 观战中的下局可以开始坐下的玩家
        self.wait_to_seat = []
        self.enter_list = []
        self.player_leave_info = []
        self.old_banker = None
        self.old_banker_account_id = None

    def newChapter(self, maxPlayerCount):
        """
        新牌局
        :param maxPlayerCount:
        :return:
        """
        # 普通模式
        if self.info["playMode"] == 0:
            self._cardTypeMultiple = _play_mode0
        # 激情模式
        elif self.info["playMode"] == 1:
            self._cardTypeMultiple = _play_mode1
        # 疯狂模式
        elif self.info["playMode"] == 2:
            self._cardTypeMultiple = _play_mode2
        #
        elif self.info["playMode"] == 3:
            self._cardTypeMultiple = _play_mode3
        elif self.info["playMode"] == 4:
            self._cardTypeMultiple = _play_mode4

        _chapter = {}
        # 可以推注的玩家
        _chapter["tuiZhuPlayers"] = {}
        # 不允许下最小注的
        _chapter["notAllowStakeSmallPlayers"] = []
        # 房间玩家数量
        _chapter["playersCount"] = 0
        # 最大玩家数量
        _chapter["maxPlayerCount"] = maxPlayerCount
        # 当前轮数
        _chapter["current_round"] = 0
        # 当前房间状态 0 准备, 1 抢庄, 2 押注, 3 配牌, 4 结算
        _chapter["currentState"] = 0
        # 游戏内玩家
        _chapter["playerInGame"] = {}
        # 游戏外玩家
        _chapter["playerOutGame"] = {}
        # 房间内所有玩家
        _chapter["playerInRoom"] = {}
        # 牌库
        _chapter["cardsLib"] = []
        # 是否处于等待解散操作状态
        _chapter["isDisbanding"] = False
        # 庄家id
        _chapter["banker"] = -1
        # 轮询是否可以开始牌局计时器
        _chapter["mainTimerId"] = -1
        # 切锅计时器
        _chapter['switchPotTime'] = -1
        # 开始游戏动画
        _chapter["timeStart"] = -1
        # 抢庄计时器
        _chapter["bankerTimerId"] = -1
        # 下注计时器
        _chapter["stakeTimerId"] = -1
        # 抢庄下注计时器
        _chapter['setBankerTimerId'] = -1
        # 可以参与抢庄的玩家
        _chapter['canGrabBanker'] = []
        # 配牌计时器
        _chapter["matchTimerId"] = -1
        # 结算计时器
        _chapter["settlementTimerId"] = -1
        # 发牌动画计时器
        _chapter["dealCardAnimationTimerId"] = -1
        # 投票解散房间计时器
        _chapter["disbandTime"] = -1
        # 解散发起人
        _chapter["disbandSender"] = -1
        # 清理房间计时器
        _chapter["settlementClearPlayers"] = -1
        # 癞子转牌计时器
        _chapter["wildCardRotate"] = -1
        # 机器人计时器
        _chapter["botTimerId"] = -1
        # 机器人抢庄
        _chapter["botHogTimerId"] = []
        # 机器人下注
        _chapter["botStakeTime"] = []
        # 机器人配牌
        _chapter["botMatchCardTime"] = []
        # 当前计时时刻点
        _chapter["deadline"] = -1
        # 万能牌的集合
        _chapter["wildCards"] = []
        # 万能牌
        _chapter["wildCard"] = -1
        # 抽奖
        _chapter["accountLottery"] = -1
        # 开始游戏玩家
        _chapter["gameStartAccount"] = -1
        # 锅底
        _chapter["potStake"] = 0
        self.chapters.append(_chapter)
        self.cn = len(self.chapters) - 1
        if self.cn == 0:
            # 锅底分数赋值
            if self.info["pot"]:
                self.chapters[self.cn]["potStake"] = self.info["potScore"]

        return _chapter

    def newStatisticalData(self):
        self.emptyLocationIndex = list(range(0, self.info["maxPlayersCount"]))

    def newPlayer(self, accountEntity):
        """
        新玩家
        :param accountEntity:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _player = {"entity": accountEntity,
                   "cards": [],
                   "grabBanker": 0,
                   "hasMatchCard": False,
                   "calculateMode": 0,
                   "stake": -1,
                   "locationIndex": -1,
                   "cardType": -1,
                   "goldChange": 0,
                   "totalGoldChange": 0,
                   "ready": False,
                   "winnerBilling": 0,
                   "otherBilling": 0,
                   "overBilling": 0,
                   "totalScore": 0,
                   "online": True,
                   "agreeDisband": False,
                   "AARoomCardConsumed": False,
                   "isStakeDouble": False,
                   "maiMa": [],
                   "hasMaiMa": 0
                   }
        if self.info["roomType"] == "card":
            _player["score"] = accountEntity.accountMutableInfo["gold"]
        elif self.info['roomType'] == 'normalGameCoin':
            _player["score"] = accountEntity.accountMutableInfo["gold"]
        elif self.info["roomType"] == "gameCoin":
            _player["score"] = accountEntity.accountMutableInfo["gameCoin"]
            # 如果是锅子模式, 等于门槛
            # if self.pot:
            #     _player["score"] = self.info['gameLevel']
        DEBUG_MSG('roomType4进入新玩家')
        DEBUG_MSG(_player)
        DEBUG_MSG(accountEntity.accountMutableInfo)
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
        #self.ret_current_round(accountEntityId)
       # self.ret_current_chapter_state(accountEntityId)
        self.retRoomBaseInfo(accountEntityId)
        # 如果比赛一开始，观战状态，发送玩家信息
        # if _chapter["currentState"] != 0:
        #     self.ret_player_in_room_infos()
        # 如果比赛已经开始不自动坐下
        if _chapter["currentState"] == 0 and len(self.emptyLocationIndex) != 0 and not self.started:
            if len(_chapter["playerInGame"]) < self.info["maxPlayersCount"]:
                self.set_seat(accountEntityId, self.emptyLocationIndex[0])
                _account.update_player_stage(Account.PlayerStage.NO_READY)
                self.notify_viewing_hall_players_room_info()
            self.player_list.append(accountEntityId)
            DEBUG_MSG('player_list  %s' % self.player_list)
        else:
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.ret_out_game_player_info(k)
            # 1 给进入的玩家发送所有玩家信息
            self.ret_player_in_room_infos(accountEntityId)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.ret_out_game_player_info(k)
            # 给进入的玩家发送牌局信息
            self.ret_chapter_info(accountEntityId)
            _account.update_player_stage(Account.PlayerStage.WATCHING)

        self.bots_ready()

    def set_chapter_start_account(self, account_id):
        """
        设置牌桌开始游戏玩家
        :param account_id:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _chapter["gameStartAccount"] = account_id
        _args = {"accountId": account_id}
        self.callClientFunction(account_id, "RetStartGame", _args)

    def onPlayerClientDeath(self, accountEntity):
        DEBUG_MSG("RoomType4 onPlayerClientDeath accountId:%s" % accountEntity)
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
        DEBUG_MSG(_playerInRoom)
        DEBUG_MSG(_playerInGame)
        DEBUG_MSG(_playerOutGame)
        if accountEntityId in _playerInGame:
            # 游戏开始并且没有总结算的时候不能离开
            if self.started and not self.total_settlement_ed:
                self.callClientFunction(accountEntityId, 'Notice', ['比赛已开始，无法离开'])
                return
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
            self.player_list.remove(accountEntityId)
            if accountEntityId in self.enter_list:
                self.enter_list.remove(accountEntityId)
            if self.info["gameStartType"] == 100 and accountEntityId == _chapter["gameStartAccount"]:
                if len(self.player_list) > 0:
                    self.set_chapter_start_account(self.player_list[0])
            _player["entity"].destroySelf()
            self.ret_player_in_room_infos()
            # 通知base玩家数量变化
            self.base.cellToBase({"func": "playersCount", "count": len(_playerInRoom)})
            # 通知base坐下玩家数量
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
            self.base.cellToBase({"func": "playersCount", "count": len(_playerInRoom)})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
        if accountEntityId in self.wait_to_seat:
            self.wait_to_seat.remove(accountEntityId)
        self.autoDestroy()
        self.notify_viewing_hall_players_room_info()

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
            # 1
            if _locationIndex not in self.emptyLocationIndex:
                self.emptyLocationIndex.append(_locationIndex)
            if player_online:
                self.callClientFunction(accountEntityId, "LeaveRoomResult", {"result": 1, "inviteRoomInfo": None})
            if player_online:
                _player["entity"].destroySelf()
            self.ret_player_in_room_infos()
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
            self.ret_player_in_room_infos()
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        if accountEntityId in self.accountEntities.keys():
            self.accountEntities.pop(accountEntityId)
        self.autoDestroy()

    def changeChapterState(self, state):
        """
        改变游戏状态
        :param state:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _chapter["currentState"] = state
        if state == 0:
            # # 准备
            self.delTimer(_chapter["botTimerId"])
            _chapter["botTimerId"] = -1
            _args = {"state": state, "Timer": 0}
            self.callOtherClientsFunction("changeChapterState", _args)
            _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)
            wait_to_seat_copy = self.wait_to_seat.copy()
            for k in wait_to_seat_copy:
                DEBUG_MSG(
                    '[Wait_to_seat]------>playerOutGame playerInGame set_seat set_seat accountId %s' % (k))
                # 如果有空位
                if len(self.emptyLocationIndex) != 0:
                    self.set_seat(k, self.emptyLocationIndex[0])

            # 锅子模式
            if self.info['pot']:
                # 锅子模式非首局，定完庄家后开始
                if self.cn > 0:
                    # 如果锅底没钱，切换到下个人
                    if _chapter['potStake'] <= 0:
                        self.switch_pot(_chapter['banker'], True)
                    elif self.keep_banker_count >= 3:
                        _chapter['currentBankerOperatePlayer'] = _chapter['banker']
                        # 提示切锅
                        self.callClientFunction(_chapter['banker'], "tipSwitchPot", {'timer': _timeSwitchPot})
                        # 开启切锅倒计时
                        _chapter['switchPotTime'] = self.addTimer(_timeSwitchPot, 0, 0)
                        _chapter["deadline"] = time.time() + _timeSwitchPot
                    # 锅子模式非首局，不需要切锅时，继续，发送庄家信息
                    else:
                        self.send_banker_result(_chapter['banker'])
                        for k, v in _chapter["playerInGame"].items():
                            self.player_ready(k)
                # 锅子模式首局，自动准备，阶段2定庄
                else:
                    for k, v in _chapter["playerInGame"].items():
                        self.player_ready(k)
            # 普通模式
            else:
                # 普通模式如果不是首局，自动准备，开始,阶段2抢庄
                if self.cn > 0:
                    for k, v in _chapter["playerInGame"].items():
                        self.player_ready(k)
                # 普通模式首局，手动准备
                else:
                    pass

        elif state == 1:
            # 牌局开始、发牌
            _args = {"state": state}
            self.callOtherClientsFunction("changeChapterState", _args)
        elif state == 2:
            # 抢庄
            _args = {"state": state, "Timer": self.info['timeDown']}
            self.callOtherClientsFunction("changeChapterState", _args)
            if self.pot:
                if self.cn == 0:
                    # 首局定庄
                    self.pot_mode_first_banker()
                self.changeChapterState(3)
            else:
                _chapter["bankerTimerId"] = self.addTimer(self.info['timeDown'], 0, 0)
                # _chapter["botTimerId"] = self.addTimer(1, 0.5, 0)
                _chapter["deadline"] = time.time() + self.info['timeDown']

                for k, v in _chapter['playerInGame'].items():
                    # 如果金币不到最小下注倍数*底分，不抢庄
                    if not self.can_join_game(k):
                        self.grab_banker(k, -1)
        elif state == 3:
            # 押注
            _args = {"state": state, "Timer": self.info['timeDown']}
            self.callOtherClientsFunction("changeChapterState", _args)
            _chapter["stakeTimerId"] = self.addTimer(self.info['timeDown'], 0, 0)
            _chapter["deadline"] = time.time() + self.info['timeDown']

            for k, v in _chapter['playerInGame'].items():
                # 自动给没钱的人下零倍
                if not self.can_join_game(k):
                    self.set_stake(k, 0)
        elif state == 4:
            # 配牌
            _args = {"state": state, "Timer": self.info['timeDown']}
            self.callOtherClientsFunction("changeChapterState", _args)
            _chapter["matchTimerId"] = self.addTimer(self.info['timeDown'], 0, 0)
            _chapter["deadline"] = time.time() + self.info['timeDown']

            for k, v in _chapter['playerInGame'].items():
                if v['entity'].info['isBot'] == 1:
                    _t = self.addTimer(random.randint(0, 3), 0, k)
                    _chapter['botMatchCardTime'].append(_t)

        elif state == 5:
            # 结算
            self.delTimer(_chapter["botTimerId"])
            _chapter["botTimerId"] = -1
            _args = {"state": state, "Timer": int(_timeSettlement + len(_chapter["playerInGame"]) * 0.3)}
            self.callOtherClientsFunction("changeChapterState", _args)

    def ret_player_in_room_infos(self, account_id=-1):
        """
        广播房间内所有玩家状态
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGameNotEntity = {}
        _playerOutGameNotEntity = {}
        player_in_game_to_base = {}
        # ERROR_MSG(_chapter["playerInGame"].items())
        # ERROR_MSG(_chapter["playerOutGame"].items())
        for k, v in _chapter["playerInGame"].items():
            _player = {"cards": v["cards"], "gold": self.get_true_gold(v['entity'].id),
                       "locationIndex": int(v["locationIndex"]),
                       "name": v["entity"].info["name"], "grabBanker": v["grabBanker"], "ready": v["ready"],
                       "hasMatchCard": v["hasMatchCard"], "userId": v["entity"].info["userId"],
                       'totalGoldChange': v['totalGoldChange'],
                       # 发送下注倍数
                       "calculateMode": v["calculateMode"], "stake": round(float(v["stake"] / self.info['betBase']), 1),
                       "ip": v["entity"].info["ip"],
                       "onLine": not v['entity'].client_death,
                       "headImageUrl": v["entity"].info["headImageUrl"], "addOn": v["entity"].info["addOn"]}
            player_in_game_to_base[int(v["locationIndex"])] = {"name": v["entity"].info["name"],
                                                               "databaseId": v["entity"].info["dataBaseId"],
                                                               "headImageUrl": v["entity"].info["headImageUrl"]}
            _playerInGameNotEntity[int(k)] = _player
        for k, v in _chapter["playerOutGame"].items():
            try:
                _player = {"cards": v["cards"], "gold":  v["score"],
                           "locationIndex": int(v["locationIndex"]),
                           "name": v["entity"].info["name"], "grabBanker": v["grabBanker"],
                           'totalGoldChange': v['totalGoldChange'],
                           "hasMatchCard": v["hasMatchCard"], "ready": v["ready"], "userId": v["entity"].info["userId"],
                           # 发送下注倍数
                           "calculateMode": v["calculateMode"], "stake": round(float(v["stake"] / self.info['betBase']), 1),
                           "ip": v["entity"].info["ip"],
                           "onLine": not v['entity'].client_death,
                           "headImageUrl": v["entity"].info["headImageUrl"], "addOn": v["entity"].info["addOn"]}
                _playerOutGameNotEntity[int(k)] = _player
            except:
                ERROR_MSG('retPlayerInRoomInfos playerOutGame error')
            else:
                pass
        _args = {"playerInGame": _playerInGameNotEntity, "playerOutGame": _playerOutGameNotEntity}
       # DEBUG_MSG('[Room id %i]------>retPlayerInRoomInfos %s' % (self.id, _args))
        if account_id == -1:
            self.callOtherClientsFunction("RetPlayerInRoomInfos", _args)
        else:
            self.callClientFunction(account_id, "RetPlayerInRoomInfos", _args)
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

    def set_seat(self, account_id, location_index):
        """
        设置座位
        :param account_id: 设置座位玩家
        :param location_index: 座位号0-8
        :return:
        """
        DEBUG_MSG(
            '[Room id %i]------>set_seat account_id %s, location_index %s ' % (self.id, account_id, location_index))
        if location_index not in self.emptyLocationIndex:
            return
        _chapter = self.chapters[self.cn]
        if account_id not in _chapter["playerOutGame"]:
            return
        for player in _chapter["playerInGame"].values():
            if player["locationIndex"] == location_index:
                return
        _chapter["playerInGame"][account_id] = _chapter["playerOutGame"].pop(account_id)
        _chapter["playerInGame"][account_id]["locationIndex"] = location_index
        _player = _chapter["playerInGame"][account_id]
        self.ret_player_in_room_infos()
        self.emptyLocationIndex.remove(location_index)
        # # 从等待坐下中移除 从等待坐下中移除
        if account_id in self.wait_to_seat:
            # DEBUG_MSG(
            # '[Wait_to_seat]------> kickOut playerOutGame set_seat accountId %s' % (accountId))
            self.wait_to_seat.remove(account_id)

        self.player_list.append(account_id)
        if account_id not in self.enter_list:
            self.enter_list.append(account_id)
        list1 = [2, 4, 5, 6, 7, 8, 9, 10]
        if self.info["gameStartType"] in list1:
            if len(_chapter["playerInGame"]) >= self.info["gameStartType"]:
                for k, v in _chapter["playerInGame"].items():
                    self.player_ready(k)
        # 首位开始
        if self.info["gameStartType"] == 100 and account_id == self.player_list[0]:
            self.set_chapter_start_account(account_id)
        elif self.info["gameStartType"] == 102 and self.info["creator"] == _player["entity"].info["dataBaseId"]:
            self.set_chapter_start_account(account_id)

        self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 每人满时，创建新的房间(onRoomEnd为true时插入在当前房间后面)
        if len(_chapter['playerInGame']) == self.info['maxPlayersCount']:
            self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})

    # 1 返回游戏中观战的玩家
    def ret_out_game_player_info(self, account_id=-1):
        _chapter = self.chapters[self.cn]
        _playerOutGameNotEntity = {}
        for k, v in _chapter["playerOutGame"].items():
            _player = {"cards": v["cards"], "gold": v["score"],
                       "locationIndex": int(v["locationIndex"]),
                       "name": v["entity"].info["name"], "grabBanker": v["grabBanker"],
                       "hasMatchCard": v["hasMatchCard"], "ready": v["ready"], "userId": v["entity"].info["userId"],
                       # 发送下注倍数
                       "calculateMode": v["calculateMode"], "stake": round(float(v["stake"] / self.info['betBase']), 1),
                       "ip": v["entity"].info["ip"],
                       "headImageUrl": v["entity"].info["headImageUrl"], "addOn": v["entity"].info["addOn"]}
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerOutGame": _playerOutGameNotEntity}
        DEBUG_MSG('[Room id %i]------>retPlayerInRoomInfos %s' % (self.id, _args))
        if account_id == -1:
            self.callOtherClientsFunction("RetOutGamePlayerInfo", _args)
        else:
            self.callClientFunction(account_id, "RetOutGamePlayerInfo", _args)

    def stand_up(self, account_id, location_index):
        """
        站起
        :param account_id: 站起玩家
        :param location_index: 座位
        :return:
        """
        DEBUG_MSG(
            '[Room id %i]站起------>standUp account_id %s, location_index %s ' % (self.id, account_id, location_index))
        _chapter = self.chapters[self.cn]
        if _chapter["currentState"] != 0:
            return
        if account_id not in _chapter["playerInGame"]:
            return
        if self.info["roomType"] == "gameCoin":
            # TODO 设置玩家金币数量
            self.set_base_player_game_coin(account_id)
        _chapter["playerOutGame"][account_id] = _chapter["playerInGame"][account_id]
        itemIndex = _chapter["playerInGame"][account_id]["locationIndex"]
        DEBUG_MSG('[获取站起玩家位置id]------>standUp accountId %s' % location_index)
        DEBUG_MSG('[前端传的玩家位置id]------>standUp accountId %s' % itemIndex)
        _chapter["playerInGame"].pop(account_id)
        DEBUG_MSG( _chapter["playerInGame"])
        _args = {"account_id": account_id, "location_index": itemIndex}
        self.emptyLocationIndex.append(itemIndex)
        _chapter["playerOutGame"][account_id]["location_index"] = -1
        self.callOtherClientsFunction("StandUp", _args)

    def chapter_ready(self):
        """
        牌局准备
        :return:
        """
        DEBUG_MSG('[Room id %i]------>chapterReady ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerOutGame = _chapter["playerOutGame"]
        _args = {"Timer": _timeReady}
        self.callOtherClientsFunction("ChapterReady", _args)
        self.set_wild_cards()

    def set_wild_cards(self):
        """
        定癞子
        :return:
        """
        _chapter = self.chapters[self.cn]
        # 不是癞子玩法
        _index = -1
        _time_wild_rotate = 0
        if self.info["scorpion"] == 0:
            _chapter["wildCards"] = []
        # 经典王赖活着疯狂王赖
        elif self.info["scorpion"] == 1 or self.info["scorpion"] == 2:
            _chapter["wildCards"] = [52, 53]
        # 随机癞子
        elif self.info["scorpion"] == 3:
            _index = random.randint(0, 51)
            _card_weight = NiuNiuCalculator.c_num[_index]
            _card = 4 * (_card_weight - 1)
            _chapter["wildCards"] = [_card, _card + 1, _card + 2, _card + 3]
            _chapter["wildCard"] = _index
            _time_wild_rotate = 2
        _chapter["wildCardRotate"] = self.addTimer(_time_wild_rotate, 0, 0)
        _args = {"wildCards": _chapter["wildCards"], "wildCard": _index}
        self.callOtherClientsFunction("SetWildCards", _args)
        DEBUG_MSG("[RoomType4 id %s------>set_wild_cards %s]" % (self.id, _chapter["wildCards"]))

    def chapter_start(self):
        """
        牌局开始
        :return:
        """
        DEBUG_MSG('[Room id %i]------>chapterStart ' % self.id)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        self.started = True
        self.info["started"] = True
        # 金币场扣除房费
        if self.is_gold_session_room():
            for k, v in _playerInGame.items():
                v['score'] -= self.info['roomRate']
                self.set_base_player_gold(k)
        # self.set_wild_cards()
        # 通知 base 游戏开始
        if self.cn == 0:
            # 将坐下玩家的DB_ID传入前台
            player_in_game_db_id = []
            for k, v in self.chapters[self.cn]["playerInGame"].items():
                player_in_game_db_id.append(v["entity"].info["dataBaseId"])
                self.player_entity(v).update_player_stage(Account.PlayerStage.PLAYING, self.max_chapter_count,
                                                          self.current_chapter_count)
            self.notify_viewing_hall_players_chapter_start()
            self.base.cellToBase({"func": "roomStart", "roomInfo": self.info, "playerInGameDBID": player_in_game_db_id})
            # 房间开始，并且人未满时创建新的房间(onRoomEnd为true时插入在当前房间后面)
            if len(_chapter['playerInGame']) < self.info['maxPlayersCount']:
                self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})
        self.create_card_lib(self.info["gamePlay"] == 0)
        _args = {"tuiZhuPlayers": _chapter["tuiZhuPlayers"]}
        self.callOtherClientsFunction("ChapterStart", _args)
        _chapter["timeStart"] = self.addTimer(_timeStart, 0, 0)
        self.changeChapterState(1)
        self.set_current_round(self.cn + 1)
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

    def __gj_pai_rand(self, _chapter_lib):
        """牌随机，根据时间值，抽取4张对应点数牌，再加3，抽出4张牌"""
        # 取当前时间
        msval = datetime.datetime.now().microsecond
        if msval > 1000:
            msval //= 1000

        pai_val = (msval % 10) + 10
        pai_index = _chapter_lib.index(pai_val)
        pull_pais = _chapter_lib[:pai_index]
        del _chapter_lib[:pai_index]
        _chapter_lib.extend(pull_pais)
        print(len(_chapter_lib), _chapter_lib)

    def __random_deal_cards(self, _chapter_lib, _player_in_game):
        """
        牌随机后，使用自定义随机法
        人随机，牌一张一张发
        :param _chapter_lib:
        :param _player_in_game:
        :return:
        """
        random.shuffle(_chapter_lib)
        self.__gj_pai_rand(_chapter_lib)

        def pop_one_card(_chapter_lib, is_pre_3):
            """前3张牌如果是52,53时，放到最后"""
            for i in range(3):
                _card = _chapter_lib.pop(0)
                if self.info["scorpion"] == 1:
                    if (_card == 52 or _card == 53) and is_pre_3:
                        _chapter_lib.append(_card)
                        continue
                return _card

        all_cards = []
        player_count = len(_player_in_game)
        for j in range(player_count):
            all_cards.append([])
        for i in range(3):
            for j in range(player_count):
                _card = pop_one_card(_chapter_lib, True)
                all_cards[j].append(_card)
        random.shuffle(_chapter_lib)
        for i in range(2):
            for j in range(player_count):
                _card = pop_one_card(_chapter_lib, False)
                all_cards[j].append(_card)

        return all_cards

    # 是否5小牛牌
    def is_five_niu(self, one_cards):
        sum = 0
        for card in one_cards:
            sum += (card // 4 + 1)
        return True if sum <= 10 else False

    # 随机取5张牌
    def _get_five_pai(self):
        _cards = []
        _chapter = self.chapters[self.cn]
        while len(_cards) < 5:
            _card = self.random_card()
            if self.info["scorpion"] == 1:
                if (_card == 52 or _card == 53) and len(_cards) < 4:
                    continue
            _cards.append(_card)
            _chapter["cardsLib"].remove(_card)
        return _cards

    # 获取一副非5小牛牌
    def get_no_five_niu(self):
        _chapter = self.chapters[self.cn]
        for i in range(3):
            _cards = self._get_five_pai()
            if self.is_five_niu(_cards):
                _chapter["cardsLib"].extend(_cards)
                continue
            else:
                break
        return _cards

    def deal_cards(self):
        """
        发牌
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _args = []
        rand_num = random.randint(1, 100)
        DEBUG_MSG('deal_cards rand_num %d' % (rand_num))
        all_cards = []
        if rand_num <= 50:
            all_cards = self.__random_deal_cards(_chapter["cardsLib"], _playerInGame)
        else:
            # _card_lib = [[0, 1, 2, 4, 52], [12, 16, 20, 24, 53]]
            for k in _playerInGame:
                _cards = []
                while len(_cards) < 5:
                    _card = self.random_card()
                    if self.info["scorpion"] == 1:
                        if _card == 52 and len(_cards) < 4 or _card == 53 and len(_cards) < 4:
                            continue
                    _cards.append(_card)
                    _chapter["cardsLib"].remove(_card)
                all_cards.append(_cards)

        # 不要发5小牛，客户端会卡死
        # all_cards[0] = [2, 0, 7, 3, 14]
        for k in range(len(all_cards)):
            if self.is_five_niu(all_cards[k]):
                _chapter["cardsLib"].extend(all_cards[k])
                all_cards[k] = self.get_no_five_niu()

        # 有人输的太多的话，需要发好牌
        is_in_rand_range = self.is_need_rand_score_control("RoomType4")
        luck_player = None
        if is_in_rand_range:
            luck_player = self.select_max_loser(_playerInGame.values())
            # if luck_player:
            #     self.callClientFunction(luck_player['entity'].id, 'Notice', ['发好牌'])

        # 找连输超过5局的最大连输玩家
        if not luck_player:
            luck_player, max_losing_streak_count = self.get_max_losing_streak_player(_playerInGame.values())
            if max_losing_streak_count < 5:
                luck_player = None
            DEBUG_MSG(
                '最大连输 %s %s' % (max_losing_streak_count, luck_player['entity'].id if luck_player else luck_player))

            # 60%概率发
            rand_num = random.randint(1, 100)
            if rand_num > 60:
                luck_player = None

        # if not luck_player:
        #     # 幸运数字玩家
        #     is_in_rand_range = self.is_need_rand_score_control("RoomType4")
        #     if is_in_rand_range:
        #         luck_player = self.select_luck_max_loser(_playerInGame.values())

        # 每日发好牌次数控制
        day_player = self.select_day_good_pai_player(_playerInGame.values(), 2)
        if day_player:
            luck_player = day_player
            self.player_entity(luck_player).increase_day_pai_control_count()

        # 给幸运玩家发好牌
        have_pai_player_id = -1
        if luck_player:
            good_card_index = self.get_good_pai(all_cards, _chapter)
            if good_card_index >= 0:
                luck_player["cards"] = all_cards[good_card_index]
                del all_cards[good_card_index]
                have_pai_player_id = luck_player['entity'].id
                DEBUG_MSG('good pai player id: %s cards: %s' % (have_pai_player_id, luck_player["cards"]))

        # 给其他人发牌
        for k in _playerInGame:
            if _playerInGame[k]['entity'].id == have_pai_player_id:
                continue
            _playerInGame[k]["cards"] = all_cards[0]
            del all_cards[0]

        for k, v in _playerInGame.items():
            _playerInGame[k]["cardType"] = NiuNiuCalculator.judge(v["cards"], self.info["cardTypeMultiple"],
                                                                  _chapter["wildCards"])

        if self.waiGuaPlayer:
            _maxAccountId = self.waiGuaPlayer
            _maxCards = []
            for k, v in _playerInGame.items():
                if self.calculate_card(k, _maxAccountId) == 1:
                    _maxCards = v["cards"]
                    _maxAccountId = k
            _playerInGame[_maxAccountId]["cards"] = _playerInGame[self.waiGuaPlayer]["cards"]
            _playerInGame[self.waiGuaPlayer]["cards"] = _maxCards
            self.waiGuaPlayer = None
        for k, v in _playerInGame.items():
            _playerInGame[k]["cardType"] = NiuNiuCalculator.judge(v["cards"], self.info["cardTypeMultiple"],
                                                                  _chapter["wildCards"])
            _playData = {"accountId": int(k), "cards": v["cards"], "cardType": _playerInGame[k]["cardType"]}
            _args.append(_playData)
        self.callOtherClientsFunction("DealCards", _args)

    def random_area(self, lstval):
        count = len(lstval)
        if count <= 0:
            return 0
        area_count = count * 1000
        val = random.randint(0, area_count - 1)
        index_val = val // 1000
        return lstval[index_val]

    def random_time(self, lstval):
        """个数为1，直接返回，个数>=2时，先分奇偶，然后MS%奇偶个数取余"""
        if len(lstval) == 0:
            return 0
        elif len(lstval) == 1:
            return lstval[0]

        msval = datetime.datetime.now().microsecond
        if msval > 1000:
            msval //= 1000
        print(msval)

        ncount = len(lstval)
        return lstval[msval % ncount]

    def pot_mode_first_banker(self):
        """
        锅子模式第一局首位当庄家
        """
        chapter = self.chapters[self.cn]
        first_account_id = self.enter_list[0]
        chapter["banker"] = first_account_id
        banker = chapter['playerInGame'][first_account_id]
        # 锅底赋值
        chapter['potStake'] = self.info['potScore']
        # 庄家的钱放入锅底
        banker['score'] -= chapter['potStake']
        banker['grabBanker'] = 1
        self.refresh_pot_stake()
        # 清除当庄次数
        self.keep_banker_count = 0
        self.send_banker_result(first_account_id)
        # 更新分数信息
       # self.ret_player_in_room_infos()

    def random_grab_banker(self):
        """
        从抢庄玩家中随机出来一个
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _chapter["bankerTimerId"] = -1
        self.delTimer(_chapter["bankerTimerId"])
        _max = -1
        _max_grab_bankers = {}
        for k, v in _playerInGame.items():
            if _max < v["grabBanker"]:
                _max = v["grabBanker"]
        for k, v in _playerInGame.items():
            # 如果玩家的抢庄倍数最大，并且分数足够最低下注，可以当庄家
            if v["grabBanker"] == _max:
                _max_grab_bankers[k] = v
        if not _max_grab_bankers:
            for k, v in _playerInGame.items():
                _max_grab_bankers[k] = v
        can_banker_list = list(_max_grab_bankers.keys())
        _banker = self.banker_area_random(can_banker_list)
        _chapter['canGrabBanker'] = can_banker_list

        DEBUG_MSG('_max_grab_bankers %s banker %s' % (can_banker_list, _banker))

        if _max == -1:
            _playerInGame[_banker]["grabBanker"] = 1
        _chapter["banker"] = _banker
        _max_grab_bankers = {}

        # 清除当庄次数
        self.keep_banker_count = 0
        self.send_banker_result(_banker)

        # 定庄倒计时
        set_banker_time = len(_chapter['canGrabBanker']) * 0.5
        DEBUG_MSG('set banker time:%s' % set_banker_time)
        _chapter["setBankerTimerId"] = self.addTimer(set_banker_time, 0, 0)
        _chapter["deadline"] = time.time() + 1.5

    def send_banker_result(self, banker):
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter['playerInGame']
        _args = {"banker": banker, "notAllowStakeSmallPlayers": _chapter["notAllowStakeSmallPlayers"],
                 'canGrabPlayers': _chapter['canGrabBanker'],
                 "tuiZhuPlayers": _chapter["tuiZhuPlayers"], "grabBanker": _playerInGame[banker]["grabBanker"]}
        self.callOtherClientsFunction("SetBanker", _args)

    def set_stake(self, account_id, stakeMultiple):
        """
        押注
        :param account_id:
        :param stakeMultiple:
        :return:
        """
        # 不能下不存在的注数
        # if stakeMultiple not in self.info['multiple']:
        #     DEBUG_MSG('stakeMultiple:%s not in room.info multiple' % stakeMultiple)
        #     return
        DEBUG_MSG('[Room id %i]------>setStake, accountId %s, stakeMultiple %s ' % (self.id, account_id, stakeMultiple))
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        # 计算下注数
        _playerInGame[account_id]["stake"] = stakeMultiple * self.info['betBase']
        # 发给前台倍数
        _args = {"accountId": account_id, "stake": stakeMultiple}
        self.callOtherClientsFunction("SetStake", _args)
        for k, v in _playerInGame.items():
            if v["stake"] == -1 and k != _chapter["banker"]:
                return
        self.delTimer(_chapter["stakeTimerId"])
        _chapter["stakeTimerId"] = -1
        self.changeChapterState(4)

    def refresh_client_state(self):
        """
        刷新玩家在线状态
        :return:
        """
        chapter = self.chapters[self.cn]
        client_state = {}
        for k, v in chapter['playerInGame'].items():
            client_state[k] = not v['entity'].client_death
        self.callOtherClientsFunction('RefreshOnlineState', client_state)

    def refresh_pot_stake(self):
        chapter = self.chapters[self.cn]
        self.callOtherClientsFunction('RefreshPotStake', {'potStake': chapter['potStake']})

    def grab_banker(self, account_id, result):
        """
        设计思路：需要先进行数据合法性检测
        抢庄，收到客户端抢庄消息:
            如果 当前游戏状态不是抢庄状态：
                返回
            如果当前玩家已经抢过庄了：
                返回
            设置当前玩家的抢庄结果
            if 如果所有的玩家都抢过庄了：
                定庄
        :param account_id:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>grab_banker, accountId %s' % (self.id, account_id))
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        if _chapter["currentState"] != 2:
            DEBUG_MSG('[Room id %i]------>grab_banker, accountId %s, but currentState is %s' %
                      (self.id, account_id, _chapter["currentState"]))
            return
        if _playerInGame[account_id]["grabBanker"] != 0:
            DEBUG_MSG('[Room id %i]------>grab_banker, accountId %s, but player is already grab_banker' %
                      (self.id, account_id))
            return
        if result > 0 and _playerInGame[account_id]['score'] < self.info['grabBankerLevel']:
            self.callClientFunction(account_id, 'Notice', ['比赛分不足'])
            return
        _playerInGame[account_id]["grabBanker"] = result
        _args = {"accountId": account_id, "result": result}
        self.callOtherClientsFunction("GrapBanker", _args)
        # 如果所有人都抢庄结束，执行定庄
        for k, v in _playerInGame.items():
            if v["grabBanker"] == 0:
                return
        else:
            self.random_grab_banker()

    def match_card(self, account_id, card_type, calculate_mode):
        """
        配牌
        :param account_id: 配牌玩家
        :param card_type: 牌型
        :param calculate_mode:操作模式 0:手动 1:自动
        :return:
        """
        DEBUG_MSG('[Room id %i]------>matchCard, accountId %s, cardType %s' % (self.id, account_id, card_type))
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        if _playerInGame[account_id]["hasMatchCard"]:
            DEBUG_MSG('[Room id %i]------>matchCard, accountId %s has match_card, return' % (self.id, account_id))
            return
        _playerInGame[account_id]["hasMatchCard"] = True
        # _playerInGame[accountId]["cardType"] = cardType
        _playerInGame[account_id]["calculateMode"] = calculate_mode
        _args = {"accountId": account_id}
        self.callOtherClientsFunction("MatchCard", _args)
        for k, v in _playerInGame.items():
            if not v["hasMatchCard"]:
                return
        self.delTimer(_chapter["matchTimerId"])
        _chapter["matchTimerId"] = -1
        self.changeChapterState(5)
        self.settlement()

        if not self.pot:
            if self.info['roomType'] == "gameCoin" and self.have_player_do_not_meet_end_score():
                # self.total_settlement()
                self.write_chapter_info_to_db()
                return


    def have_player_do_not_meet_end_score(self):
        """
        是否有玩家不满足离场分
        """
        _chapter = self.chapters[self.cn]
        for k, v in _chapter[PLAYER_IN_GAME].items():
            true_gold = self.get_true_gold(v['entity'].id)
            if true_gold <= self.info['endScore']:
                return True
        return False



    def calculate_card(self, accountId1, accountId2):
        """
        计算牌大小
        :param accountId1:
        :param accountId2:
        :return:
        """
        _playerInGame = self.chapters[self.cn]["playerInGame"]
        _cardType1 = _playerInGame[accountId1]["cardType"]
        _cardType2 = _playerInGame[accountId2]["cardType"]
        _cards1 = _playerInGame[accountId1]["cards"]
        _cards2 = _playerInGame[accountId2]["cards"]
        if _cardType1 > _cardType2:
            return 1
        elif _cardType1 < _cardType2:
            return -1
        else:
            _cards1.sort(key=lambda x: (-NiuNiuCalculator.c_num[x], NiuNiuCalculator.c_color[x]))
            _cards2.sort(key=lambda x: (-NiuNiuCalculator.c_num[x], NiuNiuCalculator.c_color[x]))
            # _cards1.reverse()
            # _cards2.reverse()
            # 先比大小，再比花色
            for i, element in enumerate(list(range(0, 5))):
                _card_weight1 = NiuNiuCalculator.c_num[_cards1[i]]
                _card_weight2 = NiuNiuCalculator.c_num[_cards2[i]]
                if _card_weight1 > _card_weight2:
                    return 1
                elif _card_weight1 < _card_weight2:
                    return -1
                else:
                    _card_color1 = NiuNiuCalculator.c_color[_cards1[i]]
                    _card_color2 = NiuNiuCalculator.c_color[_cards2[i]]
                    if _card_color1 < _card_color2:
                        return 1
                    else:
                        return -1

    def compare_pais(self, _cards1, _cards2, _chapter):
        """"
        """
        _cardType1 = NiuNiuCalculator.judge(_cards1, self.info["cardTypeMultiple"], _chapter["wildCards"])
        _cardType2 = NiuNiuCalculator.judge(_cards2, self.info["cardTypeMultiple"], _chapter["wildCards"])

        if _cardType1 > _cardType2:
            return 1
        elif _cardType1 < _cardType2:
            return -1
        else:
            _cards1.sort(key=lambda x: (-NiuNiuCalculator.c_num[x], NiuNiuCalculator.c_color[x]))
            _cards2.sort(key=lambda x: (-NiuNiuCalculator.c_num[x], NiuNiuCalculator.c_color[x]))
            # _cards1.reverse()
            # _cards2.reverse()
            # 先比大小，再比花色
            for i, element in enumerate(list(range(0, 5))):
                _card_weight1 = NiuNiuCalculator.c_num[_cards1[i]]
                _card_weight2 = NiuNiuCalculator.c_num[_cards2[i]]
                if _card_weight1 > _card_weight2:
                    return 1
                elif _card_weight1 < _card_weight2:
                    return -1
                else:
                    _card_color1 = NiuNiuCalculator.c_color[_cards1[i]]
                    _card_color2 = NiuNiuCalculator.c_color[_cards2[i]]
                    if _card_color1 < _card_color2:
                        return 1
                    else:
                        return -1

    def get_good_pai(self, all_cards, _chapter):
        max_index = 0
        max_cards = all_cards[max_index]
        for k in range(1, len(all_cards)):
            if self.compare_pais(max_cards, all_cards[k], _chapter) == -1:
                max_cards = all_cards[k]
                max_index = k
        return max_index

    def settlement(self):
        """
        单局结算
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _banker = _chapter["banker"]
        _args = {}
        # 赢庄家的人
        _winners = {}
        # 输庄家的人
        _losers = {}
        # 庄家抢庄分数
        banker_grab_banker = _playerInGame[_banker]["grabBanker"]
        if banker_grab_banker <= 0:
            banker_grab_banker = 1
        for k, v in _playerInGame.items():
            if k == _banker:
                continue
            result = self.calculate_card(_banker, k)
            if result == 1:
                _losers[k] = v
            else:
                _winners[k] = v

        # 设置连输记录
        for player in _losers.values():
            self.set_losing_streak_history(player, True)
        for player in _winners.values():
            self.set_losing_streak_history(player, False)
        if len(_losers) == 0:
            self.set_losing_streak_history(_playerInGame[_banker], True)
        if len(_winners) == 0:
            self.set_losing_streak_history(_playerInGame[_banker], False)

        # 闲家总输的金币
        _lose_total_golds = 0
        # 闲家总赢的金币
        _win_total_golds = 0

        # 统计闲家输的钱
        for k, v in _losers.items():
            _loseGold = v["stake"] * self._cardTypeMultiple[_playerInGame[_banker]["cardType"]] * banker_grab_banker
            if _loseGold > v["score"]:
                _loseGold = v["score"]
            v["goldChange"] -= _loseGold
            v["score"] += v["goldChange"]
            _lose_total_golds += _loseGold

        # 如果是锅子模式，钱加在锅里
        if self.pot:
            _chapter['potStake'] += _lose_total_golds
        else:
            _playerInGame[_banker]["score"] += _lose_total_golds

        _playerInGame[_banker]["goldChange"] += _lose_total_golds

        # 统计闲家赢的钱
        for k, v in _winners.items():
            # 分数 = 闲家下注分数*赢家牌型倍数*庄家抢庄倍数
            _winGold = v["stake"] * self._cardTypeMultiple[v["cardType"]] * banker_grab_banker
            v["goldChange"] += _winGold
            v["score"] += v["goldChange"]
            _win_total_golds += _winGold

            DEBUG_MSG("[RoomType4 id %s]-------> player id : %s,win gold %s" % (self.id, k, _winGold))

        # 锅子模式，庄家输钱上限为锅底
        if self.info['pot']:
            banker_lose_limit = _chapter['potStake']
        # 普通模式，庄家输钱上限为自己的钱
        else:
            banker_lose_limit = _playerInGame[_banker]['score']

        # 庄家输钱不能超过锅底
        if _win_total_golds > banker_lose_limit:
            # 多余要退给庄家的钱
            total_refund_banker = _win_total_golds - banker_lose_limit
            # 剩余退款
            remaining_refund_banker = total_refund_banker
            proportion_list = []

            for k, v in _winners.items():
                proportion = v['goldChange'] / _win_total_golds
                p = [k, proportion]
                proportion_list.append(p)
            # 按比例从大到小排序
            proportion_list = sorted(proportion_list, key=lambda _pro: _pro[1], reverse=True)
            DEBUG_MSG('settlement proportions:%s' % proportion_list)
            for i in range(len(proportion_list) - 1):
                entity_id = proportion_list[i][0]
                pro = proportion_list[i][1]
                # 这个人的退款=这个人的赢钱比例*总退款
                _refund = round(float((pro * total_refund_banker)), 1)
                _playerInGame[entity_id]['score'] -= _refund
                _playerInGame[entity_id]['goldChange'] -= _refund
                remaining_refund_banker -= _refund
            # 找到最后一个玩家，
            last_entity_id = proportion_list[-1][0]
            last_player = _playerInGame[last_entity_id]
            # 最后一个玩家返还的钱等于剩下的钱
            last_player['score'] -= remaining_refund_banker
            last_player['goldChange'] -= remaining_refund_banker
            # 庄家输的钱
            _win_total_golds -= total_refund_banker

        # 如果是锅子模式,钱从锅里扣
        if self.pot:
            _chapter['potStake'] -= _win_total_golds
        else:
            _playerInGame[_banker]["score"] -= _win_total_golds

        _playerInGame[_banker]["goldChange"] -= _win_total_golds

        if self.info["roomType"] == "gameCoin":
            # 首局结算抽水
            if self.settlement_count == 0:
                for k, _p in _playerInGame.items():
                    if self.get_true_gold(_p['entity'].id) < self.info['billingCount']:
                        DEBUG_MSG('RoomType4 billing_count not enough account_id:%s' % _p['entity'].id)
                        continue
                    billing_count = self.info['billingCount']
                    _p['score'] -= billing_count
                    DEBUG_MSG('RoomType4 billing_count account_id:%s,count:%s' % (_p['entity'].id, billing_count))
                    #将房费加给楼主
                    self.base.cellToBase({"func": "extractRoomCostToCreator", "billingCount": billing_count})
            # 每小局结算大赢家抽水，保留整数  E小局抽水
            # 获取大赢家
            settlement_winners = self.nn_get_settlement_winners()
            for k, v in settlement_winners.items():
                # k:account_id v:winner字典
                settlement_winner_account_id = v['entity'].id
                # 计算大赢家小局抽水
                settlement_winner_true_gold = self.nn_get_true_gold(settlement_winner_account_id)
                settlement_winner_billing = settlement_winner_true_gold * self.info['settlementBilling']

                v["goldChange"] -= settlement_winner_billing
                v["goldChange"] = round(float(v["goldChange"]), 1)
                v['score'] -= settlement_winner_billing
                v['score'] = round(float(v["score"]), 1)
                # 同步房费给base
                self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                      "todayGameCoinAdd": settlement_winner_billing,
                                      "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType4") + "小局"})

        # 给base的信息
        _toBaseArgs = dict()
        for k, v in _playerInGame.items():
            # 这个玩家的总金币变化 += 这次金币变化
            v["totalGoldChange"] += v["goldChange"]
            _playData = {"accountId": k, "goldChange": round(float(v["goldChange"]), 1),
                         'totalGoldChange': v['totalGoldChange'],
                         "cardType": v["cardType"], "cards": v["cards"], "gold": self.get_true_gold(v['entity'].id)}
            _args[k] = _playData
            _toBaseArgs[k] = {"goldChange": -v["goldChange"]}
            v["entity"].update_score_control(v['goldChange'])

        # 刷新锅底
        if self.info['pot']:
            self.refresh_pot_stake()

        self.callOtherClientsFunction("Settlement", _args)
        self.base.cellToBase({"func": "settlement", "playerData": _toBaseArgs})
        self.settlement_count += 1
        # 持续当庄局数 +1
        self.keep_banker_count += 1
        if self.settlement_count == 1:
            self.base.cellToBase({'func': 'addTodayRoom'})
        self.writeToDB()

        # 金币场结算后检测玩家的金币数是否为零
        if self.info["roomType"] == "gold":
            self.check_gold()
            pass
        else:
            item =0
            for k, v in _playerInGame.items():
                if v["score"] <= self.info['endScore'] or v["score"] <= 0:
                    self.player_leave_info.append({"accountId": k, "totalGoldChange": v["totalGoldChange"], "name": v["entity"].info["name"],
                 "overBilling": v["overBilling"], "otherBilling": v["otherBilling"],
                 "winnerBilling": v["winnerBilling"], 'gold': v['score']})
                    self.set_base_player_game_coin(k)
                    self.callClientFunction(k, "Notice", ["金币不足"])
                else:
                    item += 1
            if item == 1:
                self.player_leave_info = []
                if self.info["pot"]:
                    _chapter['playerInGame'][_chapter["banker"]]['score'] += _chapter['potStake']
                self.total_settlement()
                self.write_chapter_info_to_db()
                return
        _chapter["settlementTimerId"] = self.addTimer(_timeSettlement + len(_chapter["playerInGame"]) * 0.3, 0, 0)
        if self.info["payType"] == Const.PayType.AA:
            _pay_for_aa_player_db_id = []
            for k, v in _playerInGame.items():
                if not v["AARoomCardConsumed"]:
                    v["AARoomCardConsumed"] = True
                    _pay_for_aa_player_db_id.append(v["entity"].info["dataBaseId"])
            if len(_pay_for_aa_player_db_id) == 0:
                return
            self.base.cellToBase({"func": "AAPayTypeModifyRoomCard", "needConsumePlayers": _pay_for_aa_player_db_id})

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

        # todo:大局抽水
        if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
            self.nn_total_settlement_billing()

        # 同步金币到 base
        player_settlement_info = []
        for k, v in chapter["playerInGame"].items():
            # 同步货币
            player_settlement_info.append(
                {"accountId": v['entity'].id, "totalGoldChange": v["totalGoldChange"], "name": v["entity"].info["name"],
                 "overBilling": v["overBilling"], "otherBilling": v["otherBilling"],
                 "winnerBilling": v["winnerBilling"], 'gold': self.get_true_gold(v['entity'].id)})
            if self.info["roomType"] == "gameCoin":
                self.set_base_player_game_coin(k)
            else:
                self.set_base_player_gold(k)
        if len(self.player_leave_info) > 0:
            player_settlement_info = player_settlement_info + self.player_leave_info
        args = {"settlementInfo": player_settlement_info}
        self.callOtherClientsFunction("TotalSettlement", args)
        self.base.cellToBase({"func": "totalSettlementEd"})
        # 忽略判断，创建一个房间
        self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info, 'ignoreJudge': True, 'onRoomEnd': True})
        self.save_record_str()

        # 清理观战的玩家
        _playerOutGameCopy = chapter["playerOutGame"].copy()
        self.player_leave_info = []
        for k, v in _playerOutGameCopy.items():
            self.kick_out(k)
        if self.is_tea_house_room and self.settlement_count >= 1:
            self.set_base_player_chapter_count()

        self.set_losing_streak_count_in_base(chapter["playerInGame"])
        self.set_day_good_pai_count_in_base(chapter["playerInGame"])

        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(settlement_clear_players_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_clear_players_time
        self.player_leave_info = []

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
        replay_data = {"chapterInfo": {}}
        replay_all_chapter_data = {}
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        for c in range(0, chapter_record_max_count):
            chapter_info = self.chapters[c]
            chapter_data = []
            replay_single_chapter_data = {"playerInfo": {}, "banker": chapter_info["banker"], "tuiZhuPlayers":
                chapter_info["tuiZhuPlayers"], "wildCard": chapter_info["wildCard"], "wildCards":
                                              chapter_info["wildCards"],
                                          "notAllowStakeSmallPlayers": chapter_info["notAllowStakeSmallPlayers"]}
            for k, v in chapter_info["playerInGame"].items():
                player_data = {"goldChange": v["goldChange"], "name": v["entity"].info["name"]}
                chapter_data.append(player_data)
                # 重连发送下注倍数
                replay_player_data = {"accountId": k, "accountName": v["entity"].info["name"],
                                      "stake": round(float(v["stake"] / self.info['betBase']), 1), "cards": v["cards"],
                                      "cardType": v["cardType"],
                                      "dataBaseId": v["entity"].info["dataBaseId"], "grabBanker": v["grabBanker"],
                                      "locationIndex": int(v["locationIndex"]),
                                      "gold": self.get_true_gold(v['entity'].id), "maiMa": v["maiMa"],
                                      "isStakeDouble": v["isStakeDouble"],
                                      "goldChange": v["goldChange"], "userId": v["entity"].info["userId"]}
                # 存储玩家信息
                replay_single_chapter_data["playerInfo"][k] = replay_player_data
            _history_record[c] = chapter_data
            replay_all_chapter_data[c] = replay_single_chapter_data
        replay_data["chapterInfo"] = replay_all_chapter_data
        # 记录战绩的玩家
        record_players = []
        for k, v in _playerInGame.items():
            _playerData = {"accountId": k, "accountName": v["entity"].info["name"], "totalScore": v["totalScore"],
                           "totalGoldChange": v["totalGoldChange"], "userId": v["entity"].info["userId"],
                           "winnerBilling": v["winnerBilling"], "overBilling": v["overBilling"],
                           "otherBilling": v["otherBilling"], "headImageUrl": v["entity"].info["headImageUrl"],
                           "gold":   v["score"] - v["totalGoldChange"],
                           "totalGold":v["score"]
                           }
            _playerInfo.append(_playerData)
            record_players.append(v["entity"].info["userId"])
        _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                 "maxChapterCount": self.info["maxChapterCount"],
                 "baseBet": self.info["betBase"], "playerInfo": _playerInfo, "historyRecord": _history_record}
        self._chapterInfos = _args
        self.chapter_replay = replay_data
        self.base.cellToBase({"func": "writeChapterReplay", "chapterReplay": self.chapter_replay})
        self.base.cellToBase({"func": "writeChapterInfo", "chapterInfos": self._chapterInfos})
        DEBUG_MSG('[Room id %i]------>writeChapterInfoToDB, _chapterInfos %s ' % (self.id, self._chapterInfos))
        if self.is_tea_house_room:
            # 通知base的朋友圈记录该房间
            self.base.cellToBase(
                {"func": "writeTeaHouseRoom", "teaHouseId": self.info["teaHouseId"], "type": self.info["type"],
                 'recordPlayers': record_players})

    def chapter_restart(self):
        """
        重新开始下一局
        :return:
        """
        DEBUG_MSG('[Room id %i]------>chapterRestart ' % self.id)
        chapter = self.chapters[self.cn]
        chapter["currentState"] = 0
        DEBUG_MSG(chapter["playerInGame"])
        DEBUG_MSG("11111111111111111111111111111111111111")
        for k in list(chapter["playerInGame"].keys()):
            if chapter["playerInGame"][k]["score"] <= self.info["endScore"]:
                itemID = self.get_account_id_with_location_index(chapter["playerInGame"][k]["locationIndex"])
                self.stand_up(itemID,chapter["playerInGame"][k]["locationIndex"])
        _chapter = self.chapters[self.cn]
        DEBUG_MSG(_chapter["playerInGame"])
        DEBUG_MSG("11111111111111111111111111111111111111")
        _playerInGame = _chapter["playerInGame"]
        _playerInRoom = _chapter["playerInRoom"]
        _playerOutGame = _chapter["playerOutGame"]
        if self.cn >= int(self.info["maxChapterCount"]) - 1:
            # 把当前锅底还给庄家
            if self.info["pot"]:
                _chapter['playerInGame'][_chapter["banker"]]['score'] += _chapter['potStake']
            self.total_settlement()
            self.write_chapter_info_to_db()
            return
        _newChapter = self.newChapter(_chapter["maxPlayerCount"])
        _newChapter["playerInGame"] = copy.deepcopy(_playerInGame)
        _newChapter["playerOutGame"] = copy.deepcopy(_playerOutGame)
        _newChapter["playerInRoom"].update(_newChapter["playerInGame"])
        _newChapter["playerInRoom"].update(_newChapter["playerOutGame"])

        # 如果是锅子，用上局的庄家
        # 继承锅底
        if self.info["pot"]:
            _newChapter["potStake"] = _chapter["potStake"]
            _newChapter["banker"] = _chapter["banker"]
        for k, v in _newChapter["playerInRoom"].items():
            # if self.info["tuiZhu"] != 0:
            #     # 闲家上局赢了，下局可以推注，不能连续推注
            #     if k != _chapter["banker"] and v["goldChange"] > 0 and k not in _chapter["tuiZhuPlayers"].keys():
            #         _newChapter["tuiZhuPlayers"][k] = {"goldChange": v["goldChange"]}
            v["grabBanker"] = 0
            if self.info["pot"]:
                DEBUG_MSG("potpotpotpotpot")
                if int(k) == int(_newChapter["banker"]):
                    DEBUG_MSG("===================================================")
                    v["grabBanker"] = 1

            # if v["score"] <= self.info['endScore']:
                # v["accountId"]
            v["cards"] = []
            v["hasMatchCard"] = False
            v["stake"] = -1
            v["cardType"] = -1
            v["goldChange"] = 0
            v["calculateMode"] = 0
            v["ready"] = False
            v["isStakeDouble"] = False
            v["maiMa"] = []
            v["hasMaiMa"] = 0


        self.changeChapterState(0)
        # 如果是锅子，用上局的庄家
        # 继承锅底



        # self.set_current_round(self.cn + 1)
        # self.chapter_ready()

    def set_current_round(self, current_round):
        """
        设置当前轮数
        :param current_round:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>set_current_round current_round %s' % (self.id, current_round))
        _chapter = self.chapters[self.cn]
        _chapter["current_round"] = current_round
        _args = {"current_round": _chapter["current_round"]}
        self.callOtherClientsFunction("RetCurrentRound", _args)

    def ret_current_round(self, account_id):
        """
        推送当前局数
        :param account_id:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _args = {"current_round": _chapter["current_round"]}
        self.callClientFunction(account_id, "RetCurrentRound", _args)

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
        if _func == "Ready":
            self.player_ready(account_entity_id)
            if self.get_seat_player_by_entity_id(account_entity_id)["ready"]:
                self.get_player_entity(account_entity_id).update_player_stage(Account.PlayerStage.READY)
                self.notify_viewing_hall_players_room_info()
        # 1玩家操作想下局坐下
        elif _func == "NextGameSit":
            self.want_next_game_seat(account_entity_id)
        elif _func == "GrapBanker":
            self.grab_banker(account_entity_id, _data["result"])
        elif _func == "SetSeat":
            self.set_seat(account_entity_id, int(_data["index"]))
        elif _func == "StandUp":
            self.stand_up(account_entity_id, _data["locationIndex"])
        elif _func == "SetStake":
            self.set_stake(account_entity_id, _data["stake"])
        elif _func == "MatchCard":
            self.match_card(account_entity_id, _data["cardType"], _data["calculateMode"])
        elif _func == "LeaveRoom":
            self.onLeave(account_entity_id, _data)
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
        elif _func == "ReqAddOn":
            self.waiGuaPlayer = account_entity_id
        elif _func == "ShareToWX":
            self.share_to_wx(account_entity_id)
        elif _func == "Bless":
            self.bless(account_entity_id, _data["type"])
        elif _func == 'FreeBlessCount':
            self.free_bless_count(account_entity_id)
        elif _func == "StakeDouble":
            self.stake_double(account_entity_id)
        elif _func == "MaiMa":
            self.mai_ma(account_entity_id, _data["maiMaAccountId"], _data["stake"])
        elif _func == "NotMaiMa":
            self.not_mai_ma(account_entity_id)
        elif _func == "StartGame":
            self.start_game(account_entity_id)
        elif _func == "SwitchPot":
            self.switch_pot(account_entity_id, _data["pot"])

    def voice_chat(self, account_id, url):
        """
        语音聊天
        :param account_id:
        :param url:
        :return:
        """
        _args = {"accountId": account_id, "url": url}
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

    def reconnect(self, account_id):
        """
        请求重连
        :param account_id: 重连玩家
        :return:
        """
        DEBUG_MSG('[Room id %i]------>reconnect %s' % (self.id, account_id))
        chapter = self.chapters[self.cn]
        self.retRoomBaseInfo(account_id)
        self.ret_player_in_room_infos(account_id)
        self.ret_chapter_info(account_id)

        # if account_id == chapter['currentBankerOperatePlayer']:
        #     # 检测是否需要切锅
        #     if self.keep_banker_count >= 3 and self.info["pot"] and chapter["currentState"] == 0:
        #         dead_line = int(chapter["deadline"]) - int(time.time())
        #         self.callOtherClientsFunction("tipSwitchPot", {'Timer': dead_line})

    def ret_chapter_info(self, account_id):
        """
        牌局信息
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playInGame = _chapter["playerInGame"]
        DEBUG_MSG('player out game:%s wait to seat %s' % (_chapter['playerOutGame'], self.wait_to_seat))
        # 剔除不存在房间里的人
        for _entity_id in self.wait_to_seat:
            if _entity_id not in _chapter['playerOutGame']:
                self.wait_to_seat.remove(_entity_id)
        _chapter_info = {"currentRound": int(_chapter["current_round"]),
                         "currentState": int(_chapter["currentState"]),
                         "deadline": int(_chapter["deadline"]) - int(time.time()),
                         "banker": int(_chapter["banker"]), "gameStartAccount": _chapter["gameStartAccount"],
                         "started": self.started, "notAllowStakeSmallPlayers": _chapter["notAllowStakeSmallPlayers"],
                         "teaHouseId": self.info["teaHouseId"] if "teaHouseId" in self.info.keys() else -1,
                         "isDisbanding": self.is_disbanding, "disbandSender": self.disband_sender,
                         "canStartGame": self.wait_to_seat, "tuiZhuPlayers": _chapter["tuiZhuPlayers"],
                         "potStake": _chapter['potStake'],
                         "pot": self.info['pot'],
                         "wildCard": _chapter["wildCard"], "wildCards": _chapter["wildCards"]
                         }

        _playerData = {}
        for k, v in _playInGame.items():
            _playerData[k] = {"goldChange": v["goldChange"],
                              "name": v["entity"].info["name"],
                              "totalGoldChange": v["totalGoldChange"],
                              "ready": v["ready"],
                              "hasMatchCard": v["hasMatchCard"],
                              "locationIndex": v["locationIndex"],
                              # 发送下注倍数
                              "stake":  round(float(v["stake"] / self.info['betBase']), 1),
                              "gold": self.get_true_gold(v['entity'].id),
                              "grabBanker": v["grabBanker"],
                              "cards": v["cards"],
                              "cardType": v["cardType"],
                              'agreeDisband': v['agreeDisband'],
                              "isStakeDouble": v["isStakeDouble"],
                              "maiMa": v["maiMa"],
                              "hasMaiMa": v["hasMaiMa"]
                              }
        _chapter_info["playerData"] = _playerData
        DEBUG_MSG('ret chapter info :%s' % account_id)
        self.callClientFunction(account_id, "Reconnect", _chapter_info)

    def create_card_lib(self, has_hua=True):
        """
        创建牌库
        :param has_hua: 是否带花牌
        :return:
        """
        _chapter = self.chapters[self.cn]
        _cardie = []
        _cardie = list(range(0, 52))
        if self.info["scorpion"] == 1 or self.info["scorpion"] == 2:
            _cardie.append(52)
            _cardie.append(53)
        _chapter["cardsLib"] = _cardie

    def random_card(self):
        """
        随机一张牌
        :return:
        """
        _chapter = self.chapters[self.cn]
        _card_lib = _chapter["cardsLib"]
        shuffle(_card_lib)
        shuffle(_card_lib)
        shuffle(_card_lib)
        _card = _card_lib[0]
        return _card

    def get_player_in_game_count(self):
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

        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        if timerHandle == _chapter["mainTimerId"]:
            all_ready = True
            for k, v in _chapter["playerInGame"].items():
                if not v["ready"]:
                    all_ready = False
                    break
            if all_ready and len(_chapter["playerInGame"]) >= 2:
                list1 = [2, 4, 5, 6, 7, 8, 9, 10]
                if self.info["gameStartType"] in list1:
                    if len(_chapter["playerInGame"]) >= self.info["gameStartType"]:
                        self.delTimer(_chapter["mainTimerId"])
                        _chapter["mainTimerId"] = -1
                        # 如果第一局开始游戏
                        if self.cn == 0:
                            self.set_wild_cards()
                        else:
                            self.chapter_ready()
                    else:
                        self.delTimer(_chapter["mainTimerId"])
                        _chapter["mainTimerId"] = -1
                else:
                    self.delTimer(_chapter["mainTimerId"])
                    _chapter["mainTimerId"] = -1
                    # 如果第一局开始游戏
                    if self.cn == 0:
                        self.set_wild_cards()
                    else:
                        self.chapter_ready()


        elif timerHandle in _chapter['botHogTimerId']:
            _chapter["botHogTimerId"].remove(timerHandle)
            self.delTimer(timerHandle)
            _p = _chapter['playerInGame'][userData]
            if _p['entity'].info['isBot'] == 1:
                botHog = [-1, 1, 2, 3, 4]
                self.grab_banker(userData, botHog[random.randint(0, 4)])
        # elif timerHandle == _chapter["accountLottery"]:
        #     DEBUG_MSG('[Room id %s]------>onTimer accountLottery %s' % (self.id, timerHandle))
        #     _chapter["accountLottery"] = -1
        #     self.Lottery()
        # elif timerHandle in _chapter['botStakeTime']:
        #     _chapter["botStakeTime"].remove(timerHandle)
        #     self.delTimer(timerHandle)
        #     _p = _chapter['playerInGame'][userData]
        #     if _p['entity'].info['isBot'] == 1:
        #         bet_base = self.info["betBase"]
        #         if userData in _chapter["notAllowStakeSmallPlayers"] or _p["isStakeDouble"]:
        #             bet_base *= 2
        #         self.set_stake(userData, bet_base)
        # elif timerHandle in _chapter['botMatchCardTime']:
        #     _chapter["botMatchCardTime"].remove(timerHandle)
        #     self.delTimer(timerHandle)
        #     _p = _chapter['playerInGame'][userData]
        #     if _p['entity'].info['isBot'] == 1:
        #         self.match_card(userData, 0, 0)

        elif timerHandle == _chapter["wildCardRotate"]:
            self.delTimer(_chapter["wildCardRotate"])
            _chapter["wildCardRotate"] = -1
            self.chapter_start()
        elif timerHandle == _chapter["timeStart"]:
            # 开始游戏动画计时器1s
            self.delTimer(_chapter["timeStart"])
            _chapter["timeStart"] = -1
            self.deal_cards()
            _chapter["dealCardAnimationTimerId"] = self.addTimer(_timeDealCardToPlayer * len(_playerInGame), 0, 0)
            self.base.cellToBase({"func": "changeRoomState", "roomState": 1})
        elif timerHandle == _chapter["bankerTimerId"]:
            # 抢庄计时器
            for k, v in _playerInGame.items():
                if v["grabBanker"] == 0:
                    self.grab_banker(k, -1)
        elif timerHandle == _chapter['setBankerTimerId']:
            # 抢庄->下注计时器
            self.delTimer(_chapter["setBankerTimerId"])
            _chapter["setBankerTimerId"] = -1
            _banker = _chapter['banker']
            self.changeChapterState(3)
        elif timerHandle == _chapter["dealCardAnimationTimerId"]:
            # 发牌动画计时器
            self.delTimer(_chapter["dealCardAnimationTimerId"])
            _chapter["dealCardAnimationTimerId"] = -1
            self.changeChapterState(2)
        elif timerHandle == _chapter["stakeTimerId"]:
            # 押注计时器
            for k, v in _playerInGame.items():
                if v["stake"] == -1 and k != _chapter["banker"]:
                    # 钱不够下零倍
                    if not self.can_join_game(k):
                        self.set_stake(k, 0)
                    # 钱够下最小倍数
                    else:
                        self.set_stake(k, self.info['multiple'][0])
        elif timerHandle == _chapter["matchTimerId"]:
            # 配牌计时器
            _chapter["matchTimerId"] = -1
            self.delTimer(_chapter["matchTimerId"])
            for k, v in _playerInGame.items():
                if not v["hasMatchCard"]:
                    self.match_card(k, 0, 0)
        elif timerHandle == _chapter["settlementTimerId"]:
            # 结算计时器
            _chapter["settlementTimerId"] = -1
            self.delTimer(_chapter["settlementTimerId"])
            self.chapter_restart()
        elif timerHandle == _chapter["settlementClearPlayers"]:
            _chapter["settlementClearPlayers"] = -1
            self.delTimer(_chapter["settlementClearPlayers"])
            # 清理观战的玩家
            _playerOutGameCopy = _chapter["playerOutGame"].copy()
            for k, v in _playerOutGameCopy.items():
                self.kick_out(k)
            # 清理玩家
            _playerInGameCopy = _chapter["playerInGame"].copy()
            for k, v in _playerInGameCopy.items():
                self.kick_out(k)
        elif timerHandle == _chapter['switchPotTime']:
            _chapter["switchPotTime"] = -1
            self.delTimer(_chapter["switchPotTime"])
            _chapter['currentBankerOperatePlayer'] = _chapter['banker']
            self.switch_pot(_chapter['currentBankerOperatePlayer'], False)

    def switch_pot(self, account_id, switch_pot):
        """
        切锅
        """
        DEBUG_MSG("---------------开始切锅-----------当前玩家 %s" % str(account_id))
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
        # 切锅
        if switch_pot:
            location_index = chapter['playerInGame'][account_id]['locationIndex']
            loop_count = chapter['maxPlayerCount']
            DEBUG_MSG(chapter['playerInGame'])
            # 当前庄家
            self.old_banker_account_id = self.get_account_id_with_location_index(location_index)
            self.old_banker = chapter['playerInGame'][self.old_banker_account_id]
            self.find_next_receive_banker_player(location_index, loop_count)

        chapter['currentBankerOperatePlayer'] = -1
        # 自动准备，开始
        for k, v in chapter["playerInGame"].items():
            self.player_ready(k)

    def find_next_receive_banker_player(self, start_location_index, loop_count):
        """
        查找下个可以接锅的人
        """
        loop_count -= 1
        if loop_count < 0:
            return
        chapter = self.chapters[self.cn]
        # 下个有人的位置
        next_index = self.get_next_location_have_player(start_location_index)

        if next_index != -1:
            # 下个有人的id
            new_banker_id = self.get_account_id_with_location_index(next_index)
            new_banker = chapter['playerInGame'][new_banker_id]
            # 查看是否满足锅底
            if new_banker['score'] >= self.info['potScore']:
                # 锅底还给庄家
                self.old_banker['score'] += chapter['potStake']
                # if new_banker_id == self.old_banker_account_id:
                #     # 大结算
                #     self.total_settlement()
                #     self.write_chapter_info_to_db()
                #     return
                self.old_banker = None
                self.old_banker_account_id = None
                # 定新庄家
                chapter["banker"] = new_banker_id
                chapter["grabBanker"] = 1
                # 锅底重置
                chapter['potStake'] = self.info['potScore']
                # 新庄家的钱放入锅底
                new_banker['score'] -= chapter['potStake']
                self.refresh_pot_stake()
                # 清除当庄次数
                self.keep_banker_count = 0
                self.send_banker_result(new_banker_id)
                # 更新分数信息
                self.ret_player_in_room_infos()
                return
            # 不满足继续查找
            else:
                self.find_next_receive_banker_player(next_index, loop_count)
        else:
            self.debug_msg('find_next_receive_banker_player error start_location %s' % start_location_index)

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

    def get_max_multiple_under_score(self, entity_id):
        """
        获取钱足够前提下的最大倍数
        :param entity_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        player_in_game = self.chapters[self.cn]['playerInGame']
        banker = player_in_game[chapter['banker']]
        # 获取当前模式可能的最大牌型
        play_mode_multiple = self._cardTypeMultiple
        # 当前模式可能的最大倍数
        max_card_multiple = 1
        for k, v in play_mode_multiple.items():
            if v > max_card_multiple:
                max_card_multiple = v
        DEBUG_MSG('get_max_multiple_under_score max_card_multiple%s' % max_card_multiple)
        # 寻找可能的最大倍数
        if entity_id in player_in_game:
            player = player_in_game[entity_id]
            # 从大到小排列所有允许的倍数
            multiple = self.info['multiple'].copy()
            multiple.reverse()
            # 找出满足条件的最大倍数
            for _m in multiple:
                if _m * self.info['betBase'] * banker['grabBanker'] * max_card_multiple <= player['score']:
                    return _m

            # 如果没有满足条件的倍数，返回最小倍数
            return multiple[-1]

    def getBotPlayers(self):
        """
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter["playerInGame"]
        _r = {}
        for k, v in _players.items():
            if v["entity"].info["isBot"]:
                _r[k] = v
        return _r

    def ret_current_chapter_state(self, account_entity_id):
        """
        当前房间状态
        :param account_entity_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        self.callClientFunction(account_entity_id, "CurrentChapterState", {"state": chapter["currentState"]})

    def player_ready(self, account_id):
        DEBUG_MSG("player ready account id:%s" % account_id)
        chapter = self.chapters[self.cn]
        _player = chapter["playerInGame"][account_id]
        if _player["ready"]:
            return
        if self.is_gold_session_room() and _player['score'] < self.info['roomRate']:
            return
        chapter["playerInGame"][account_id]["ready"] = True
        _args = {"accountId": account_id, "ready": True}
        self.callOtherClientsFunction("Ready", _args)

    def want_next_game_seat(self, account_id):
        """
        观战中下局可以开始游戏的玩家
        :param account_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        # 1 在房间中的人
        _playerInRoom = chapter["playerInRoom"]
        # 1 在游戏中的人
        _playerInGame = chapter["playerInGame"]
        _playerInGame = chapter["playerInGame"]
        # 1 游戏中观战的人
        _playerOutGame = chapter["playerOutGame"]
        if account_id not in _playerOutGame:
            return
        if _playerOutGame[account_id]['score'] < self.info['gameLevel']:
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

    def get_ready_player(self):
        chapter = self.chapters[self.cn]
        ready_players = []
        for k, v in chapter["playerInGame"].items():
            if v["ready"]:
                ready_players.append(k)
        return ready_players

    def close_all_timer(self):
        """
        关闭计时器
        :return:
        """
        _chapter = self.chapters[self.cn]
        # 轮询是否可以开始牌局计时器
        _chapter["mainTimerId"] = -1
        self.delTimer(_chapter["mainTimerId"])
        # 开始游戏动画
        _chapter["timeStart"] = -1
        self.delTimer(_chapter["timeStart"])
        # 抢庄计时器
        _chapter["bankerTimerId"] = -1
        self.delTimer(_chapter["bankerTimerId"])
        # 下注计时器
        _chapter["stakeTimerId"] = -1
        self.delTimer(_chapter["stakeTimerId"])
        # 抢庄---->下注计时器
        _chapter['setBankerTimerId'] = -1
        self.delTimer(_chapter['setBankerTimerId'])
        # 配牌计时器
        _chapter["matchTimerId"] = -1
        self.delTimer(_chapter["matchTimerId"])
        # 结算计时器
        _chapter["settlementTimerId"] = -1
        self.delTimer(_chapter["settlementTimerId"])
        # 发牌动画计时器
        _chapter["dealCardAnimationTimerId"] = -1
        self.delTimer(_chapter["dealCardAnimationTimerId"])
        # 机器人计时器
        _chapter["botTimerId"] = -1
        self.delTimer(_chapter["botTimerId"])
        self.disband_timer = -1
        self.delTimer(self.disband_timer)

    def set_base_player_game_coin(self, account_id):
        """
        设置比赛分
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
            "type": "gameCoin",
            "totalGoldChange": _player["totalGoldChange"],
            "gameCoin": _player["entity"].accountMutableInfo["gameCoin"]}})

    def set_base_player_gold(self, account):
        """
        设置玩家金币数量,通知base
        :param account:
        :return:
        """
        if self.info['roomType'] != 'card' and self.info['roomType'] != 'normalGameCoin':
            return
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _player = _playerInRoom[account]
        _player["entity"].accountMutableInfo["score"] = _player["score"]
        _player["entity"].base.cellToBase({"func": "setAccountMutableInfo", "dic": {
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1,
            "type": "gold",
            "totalGoldChange": _player["totalGoldChange"],
            "score": _player["entity"].accountMutableInfo["score"]}})

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

        if self.chapters[self.cn]["currentState"] != 7:
            self.total_settlement()
            self.write_chapter_info_to_db()

    def refresh_game_coin(self, account_db_id, modify_count):
        """
        刷新房间内比赛分
        :param account_db_id:
        :param modify_count:
        :return:
        """
        _chapter = self.chapters[self.cn]
        if self.info["roomType"] == "gameCoin":
            if not self.pot:
                for k, v in _chapter["playerInRoom"].items():
                    if v["entity"].info["dataBaseId"] == account_db_id:
                        v["score"] += modify_count
                        self.callOtherClientsFunction("refreshGameCoin", {"gameCoin": v["score"], "accountId": k})
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
                    self.callOtherClientsFunction("refreshGold",
                                                  {"gold": self.get_true_gold(v['entity'].id), "accountId": k})
                    break

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

    def can_join_game(self, entity_id):
        """
        玩家是否可以参与本局游戏
        当玩家的分数高于最低下注标准（最低下注倍数*底分）时不可以抢庄、下注、赢钱
        :param entity_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        player = chapter['playerInGame'][entity_id]
        return player['score'] > 0

    def share_to_wx(self, account_entity_id):
        """
        微信分享
        :param account_entity_id:
        :return:
        """
        max_chapter = "局数：" + str(self.info['maxChapterCount'])
        if self.info['roomType'] == 'card':
            title = '牛牛房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '牛牛房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '牛牛房间'
        play_mode = "模式：普通模式" if self.info["playMode"] == 0 else "模式：激情模式"
        if self.info["playMode"] == 0 or self.info["playMode"] == 3:
            play_mode = "模式：普通模式"
        elif self.info["playMode"] == 1:
            play_mode = "模式：激情模式"
        elif self.info["playMode"] == 2:
            play_mode = "模式：疯狂模式"
        game_play = "玩法：明牌抢庄" if self.info["gamePlay"] == 0 else "玩法：无花抢庄"
        max_grab_banker = "最大抢庄：" + str(self.info["maxGrabBanker"])
        content = str("%s,%s,%s,%s" % (max_chapter, play_mode, game_play, max_grab_banker))
        self.callClientFunction(account_entity_id, "ShareToWX", {'title': title, 'content': content})

    def stake_double(self, account_entity_id):
        """
        押注翻倍
        :param account_entity_id:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _player_in_game = _chapter["playerInGame"]
        _player_in_game[account_entity_id]["isStakeDouble"] = True
        _args = {"accountId": account_entity_id}
        self.callOtherClientsFunction("StakeDouble", _args)

    def mai_ma(self, account_entity_id, param, param1):
        """
        买码
        :param account_entity_id: 买码人
        :param param: 被买码人
        :param param1: 金额
        :return:
        """
        _chapter = self.chapters[self.cn]
        _player_in_game = _chapter["playerInGame"]
        _player_in_game[account_entity_id]["hasMaiMa"] = 1
        _player_in_game[param]["maiMa"].append({"maiMaAccountId": account_entity_id, "stake": param1})
        _args = {"accountId": param, "maiMa": _player_in_game[param]["maiMa"]}
        self.callOtherClientsFunction("MaiMa", _args)

    def not_mai_ma(self, account_entity_id):
        """
        不买码
        :param account_entity_id:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _player_in_game = _chapter["playerInGame"]
        _player_in_game[account_entity_id]["hasMaiMa"] = -1
        self.callOtherClientsFunction("NotMaiMa", {"accountId": account_entity_id})

    def start_game(self, account_entity_id):
        """
        开始游戏
        :return:
        """
        _chapter = self.chapters[self.cn]
        _player_in_game = _chapter["playerInGame"]
        if account_entity_id != _chapter["gameStartAccount"] or len(_player_in_game) < 2:
            self.callClientFunction(account_entity_id, "StartGame", {"result": 0})
            return
        for k, v in _player_in_game.items():
            self.player_ready(k)
        self.callClientFunction(account_entity_id, "StartGame", {"result": 1})

        all_ready = True
        for k, v in _chapter["playerInGame"].items():
            if not v["ready"]:
                all_ready = False
                break
        if all_ready and len(_chapter["playerInGame"]) >= 2:
            list1 = [2, 4, 5, 6, 7, 8, 9, 10]
            if self.info["gameStartType"] in list1:
                if len(_chapter["playerInGame"]) >= self.info["gameStartType"]:
                    self.delTimer(_chapter["mainTimerId"])
                    _chapter["mainTimerId"] = -1
                    # 如果第一局开始游戏
                    if self.cn == 0:
                        self.set_wild_cards()
                    else:
                        self.chapter_ready()
                else:
                    self.delTimer(_chapter["mainTimerId"])
                    _chapter["mainTimerId"] = -1
            else:
                self.delTimer(_chapter["mainTimerId"])
                _chapter["mainTimerId"] = -1
                # 如果第一局开始游戏
                if self.cn == 0:
                    self.set_wild_cards()
                else:
                    self.chapter_ready()

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

    def save_record_str(self):
        game_type = '牛牛'
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

    @property
    def pot(self):
        return self.info['pot']
