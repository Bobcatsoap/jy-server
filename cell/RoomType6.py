# -*- coding: utf-8 -*-
import copy
import datetime
import json
import random
import re
import sys
import time

import Const

import RoomType6AiMain as R6AM
import RoomType6Calculator
import KBEngine
import RoomType6InitiativeCardSplit as R6Split
import RoomType6CardsScore as R6Score
import  RoomType6AiUtil as R6Util

import Util
from KBEDebug import DEBUG_MSG
from RoomBase import RoomBase
import Account

# 准备倒计时时间
_timeReady = 5

# 发牌动画时间
_timeDealCardToPlayer = 3

# 叫地主时间
grab_dealer_time = 10

# 出牌时间
play_card_time = 30

# 机器人出牌时间
bot_play_card_time_min = 2
bot_play_card_time_max = 8

# 机器人叫分时间限制
bot_call_dealer_time_min = 0
bot_call_dealer_time_max = 2

# 机器人叫地主、抢地主时间限制
bot_grab_dealer_time_min = 0
bot_grab_dealer_time_max = 2

# 押注倒计时时间
_timeStake = 20
# 结算时间
settlement_time = 6
# 解散房间倒计时
time_disband = 30
# 总结算清理玩家倒计时
settlement_clear_players_time = 30

# 春天倍数
spring_multiple = 2


class RoomType6(RoomBase):
    _chapterInfos = {}
    is_manual_disband = False
    disband_from_creator = False
    # 1 总结算设置位    刚开始设置为False
    total_settlement_ed = False
    settlement_count = 0
    started = False

    def __init__(self):
        RoomBase.__init__(self)
        self.emptyLocationIndex = list(range(0, 3))
        self.base.cellToBase({"func": "reqCutRatio", "gameType": "roomType1"})
        self.luck_user = 0

    def newChapter(self, maxPlayerCount):
        """
        新牌局
        :param maxPlayerCount:
        :return:
        """
        _chapter = {}
        # 是否存在特殊牌型
        # _chapter["SpacrCardType"] = self.info["SpacrCardType"]
        # 房间时间
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
        _chapter["currentState"] = 0
        # 当前操作玩家位置
        _chapter["currentLocationIndex"] = -1
        # 房间总注
        _chapter["totalBet"] = 0
        # 解散清除玩家倒计时
        _chapter["settlementClearPlayers"] = -1
        # 轮询是否可以开始牌局计时器
        _chapter["mainTimerId"] = -1
        # 牌局开始倒计时计时器
        _chapter["chapterStartTimerId"] = 0
        # 发牌计时器
        _chapter["dealCardAnimationTimerId"] = -1
        # 抢地主计时器
        _chapter["grabDealerTimer"] = -1
        # 出牌计时器
        _chapter["playCardTimer"] = -1
        # 机器人地主叫分计时器
        _chapter["botCallDealerTimer"] = -1
        # 机器人抢地主、叫地主计时器
        _chapter['botGrabDealerTimer'] = -1
        # 结算计时器
        _chapter["settlementTimer"] = -1
        # 位置交换计时器
        _chapter["seatAnimationTimerId"] = -1
        # 机器人出牌计时器
        _chapter["botPlayCardTimer"] = -1
        # 当前计时时刻点
        _chapter["deadline"] = -1
        # 游戏内玩家
        _chapter["playerInGame"] = {}
        # 游戏外玩家
        _chapter["playerOutGame"] = {}
        # 房间内所有玩家
        _chapter["playerInRoom"] = {}
        # 牌库
        _chapter["cardsLib"] = []
        # 底牌
        _chapter["coverCards"] = []
        # 地主id
        _chapter["dealer"] = -1
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
        # 当前操作玩家
        _chapter["currentPlayer"] = -1
        # 胜者
        _chapter["winner"] = -1
        # 底分
        # _chapter["baseScore"] = self.info["baseScore"]
        # 炸弹封顶
        _chapter["bombCaps"] = self.info["bombCaps"]
        # 炸弹个数
        _chapter["bombCount"] = 0
        # 倍数
        _chapter["multiple"] = 1
        # 抽奖
        _chapter["accountLottery"] = -1
        # 聊天记录
        _chapter["chatHistory"] = []
        # 战绩
        _chapter["roomRecord"] = {}
        # 可以叫地主的玩家，欢乐模式
        _chapter["canCallLandLordPlayers"] = []
        # 可以抢地主的玩家，欢乐模式
        _chapter["canGrabLandLordPlayers"] = []
        #  1 玩牌类型LandlordGameType   0   叫分场  1 欢乐场
        _chapter["LandlordGameType"] = self.info["LandlordGameType"]
        # operationType:1，地主相关，2，出牌相关  0, 发牌相关
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
        _player = {}
        # 准备
        _player["ready"] = False
        # 实体
        _player["entity"] = accountEntity
        # 牌
        _player["cards"] = []
        # 出过的牌
        _player["playedCards"] = []
        # 玩家叫地主结果,不抢：0,1,2,3，未操作：-1
        _player["grabResult"] = -1
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
        # 钻石场默认为0，金币场使用的是大厅金币，比赛分场使用的是账户再朋友圈的比赛分
        if self.info["roomType"] == "gameCoin":
            # _player["gold"] = accountEntity.accountMutableInfo["gameCoin"]
            # 比赛分场修改使用比赛分为使用金币
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        elif self.info["roomType"] in ['normalGameCoin', 'card', 'gold', 'challenge']:
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 1 同意解散
        _player["agreeDisband"] = False
        # 出牌次数
        _player["playCount"] = 0
        # 身份 无：-1，农民：0，地主：1
        _player["identity"] = 0
        # 叫地主，欢乐模式  后台逻辑判断使用
        _player["callLandLord"] = -1
        # 抢地主,欢乐模式
        _player["grabLandLord"] = -1
        # 1 是好友   0不是好友
        _player["isFriend"] = -1
        # 玩家的操作参数  0默认不操作
        _player["operation_args"] = 0
        _player["delegate_play_card"] = False
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
        # 1 当前账户
        _account = KBEngine.entities[accountEntityId]
        _account.viewing_hall = False
        # 存入账户实体列表，相同实体不能重复登入房间
        if _account.id not in self.accountEntities.keys():
            self.accountEntities[_account.id] = _account
            DEBUG_MSG("on_enter account_entities:%s" % self.accountEntities)
        # 1 调用创建新玩家
        _player = self.newPlayer(_account)

        # 1 如果不在玩家列表里  说明是新玩家
        if accountEntityId not in _chapter["playerInRoom"]:
            _chapter["playerInRoom"][accountEntityId] = _player
            self.base.cellToBase({"func": "playersCount", "count": len(_chapter["playerInRoom"])})
        else:
            # 1 玩家进入 但是已经存在此玩家
            DEBUG_MSG("onEnter-------> account %s on Enter room, but _player already exits" % accountEntityId)
            _chapter["playerInRoom"][accountEntityId]["delegate_play_card"] = False
            return
        _chapter["playerOutGame"][accountEntityId] = _player
        if _account.info["isBot"] == 1:
            self.set_seat(accountEntityId, self.emptyLocationIndex[0])
            self.player_ready(accountEntityId)
            return
        self.retRoomBaseInfo(accountEntityId)
        # # 1 广播房间玩家状态
        # self.ret_player_in_room_info()
        # 1 发送在房间的当前座位
        self.sendChapterState(accountEntityId)
        # 如果比赛已经开始不自动坐下
        if _chapter["currentState"] == 0 and not self.started and len(self.emptyLocationIndex) != 0:
            if len(_chapter["playerInGame"]) < self.info["maxPlayersCount"]:
                self.set_seat(accountEntityId, self.emptyLocationIndex[0])
                _account.update_player_stage(Account.PlayerStage.NO_READY)
                self.notify_viewing_hall_players_room_info()
                self.player_ready(accountEntityId, False)
        # 有观战玩家进入
        else:
            # 给坐下玩家发送观战玩家信息
            for k, v in _chapter["playerInGame"].items():
                self.retOutGamePlayerInfo(k)
            # 1 给进入的玩家发送所有玩家信息
            self.ret_player_in_room_info(accountEntityId)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.retOutGamePlayerInfo(k)
            # 给进入的玩家发送牌局信息
            self.ret_chapter_info(accountEntityId)
            _account.update_player_stage(Account.PlayerStage.WATCHING)

    def ret_player_in_room_info(self, accountId=None):
        """
        广播房间内所有玩家状态
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInGameNotEntity = {}
        _playerOutGameNotEntity = {}
        player_in_game_to_base = {}

        for k, v in _chapter["playerInGame"].items():
            _player = {"cards": self.parse_card_to_client(v["cards"]),
                       "playedCards": self.parse_card_to_client(v["playedCards"]),
                       "gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       "onLine": not v['entity'].client_death,
                       "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                       "addOn": v["entity"].info["addOn"],
                       "ready": v["ready"],
                       'totalGoldChange': v['totalGoldChange']
                       }
            player_in_game_to_base[int(v["locationIndex"])] = {"name": v["entity"].info["name"],
                                                               "databaseId": v["entity"].info["dataBaseId"],
                                                               "headImageUrl": v["entity"].info["headImageUrl"]}
            _playerInGameNotEntity[int(k)] = _player
        for k, v in _chapter["playerOutGame"].items():
            _player = {"cards": self.parse_card_to_client(v["cards"]),
                       "playedCards": self.parse_card_to_client(v["playedCards"]),
                       "gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       "onLine": not v['entity'].client_death,
                       "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                       "addOn": v["entity"].info["addOn"],
                       'totalGoldChange': v['totalGoldChange'],
                       "ready": v["ready"]}
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerInGame": _playerInGameNotEntity, "playerOutGame": _playerOutGameNotEntity}

        for k, v in _chapter['playerInGame'].items():
            if accountId is not None and k != accountId:
                continue
            args_copy = copy.deepcopy(_args)
            for k2, v2 in args_copy['playerInGame'].items():
                if k == k2:
                    continue
                for x in range(len(v2['cards'])):
                    v2['cards'][x] = 1
            self.callClientFunction(k, 'RetPlayerInRoomInfos', args_copy)

        tea_house_id = -1
        if self.is_tea_house_room:
            tea_house_id = self.info['teaHouseId']
        self.base.cellToBase({"func": "refreshPlayerInGame", "playerInGame": player_in_game_to_base,
                              "teaHouseId": tea_house_id})

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
        # if _func == "StartGame":
        #     self.start_game()
        if _func == "GrabDealer":
            self.call_dealer(account_entity_id, _data["result"])
        # 1 欢乐模式玩家叫地主
        elif _func == "CallLandLord":
            self.grab_dealer(account_entity_id, _data["result"])
        elif _func == "LeaveRoom":
            self.onLeave(account_entity_id, _data)
        elif _func == "ChallengeContinue":
            self.challenge_continue(account_entity_id)
        elif _func == "ChallengeLeaveRoom":
            self.player_delegate(account_entity_id)
        elif _func == "PlayCards":
            self.player_play_cards(account_entity_id, _data["cards"])
        elif _func == "Ready":
            self.player_ready(account_entity_id)
            if self.get_seat_player_by_entity_id(account_entity_id)["ready"]:
                self.get_player_entity(account_entity_id).update_player_stage(Account.PlayerStage.READY)
                self.notify_viewing_hall_players_room_info()
            
            _chapter = self.chapters[self.cn]
            all_ready = True
            for k, v in _chapter["playerInGame"].items():
                if not v["ready"]:
                    all_ready = False
                    break
            if all_ready and len(_chapter["playerInGame"]) >= 3:
                # 只有阶段0可以通过准备开始
                if _chapter['currentState'] != 0:
                    return
                self.start_game()

        elif _func == "GetRemainCards":
            self.send_remain_cards()
        elif _func == "GetRoomRecord":
            # 发送玩家战绩信息
            self.send_room_score(account_entity_id)
        elif _func == "GetChatHistory":
            self.send_chat_history(account_entity_id)
        # 1 斗地主表情
        elif _func == "SendEmotion":
            self.Send_emotion(account_entity_id, _data["index"])
        elif _func == "SendChat":
            self.send_chat(account_entity_id, _data["content"])
        # 1 快捷语广播
        elif _func == "SendCommonChat":
            self.send_common_chat(account_entity_id, _data["index"])
        elif _func == "Reconnect":
            self.reconnect(account_entity_id)
        elif _func == "ChangeTable":
            self.change_table(account_entity_id)
        elif _func == "GetPlayersRemainCards":
            self.send_players_remain_cards(account_entity_id)
        #  1 玩家点击祈福动画
        elif _func == "Bless":
            self.bless(account_entity_id, _data["type"])
        elif _func == 'FreeBlessCount':
            self.free_bless_count(account_entity_id)
        # 解散房间相关操作
        elif _func == "DisbandRoom":
            if self.is_forbid_disband_room():
                self.callClientFunction(account_entity_id, 'Notice', ['该房间禁止中途解散'])
                return
            self.disband_room_broadcast(account_entity_id)
        elif _func == "DisbandRoomOperation":
            self.response_disband(account_entity_id, _data["result"])
        elif _func == "VoiceChat":
            self.voiceChat(account_entity_id, _data["url"])
        # 1 分享到微信
        elif _func == 'ShareToWX':
            self.share_to_wx(account_entity_id)
        elif _func == 'distanceFromEveryone':
            self.get_distance_relation(account_entity_id)

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
        _chapter["playerInGame"][accountId] = _chapter["playerOutGame"][accountId]
        _chapter["playerOutGame"].pop(accountId)
        _chapter["playerInGame"][accountId]["locationIndex"] = locationIndex
        _player = _chapter["playerInGame"][accountId]
        _args = {"accountId": accountId, "locationIndex": locationIndex,
                 "name": _player["entity"].info["name"], "gold": _player["gold"]}
        # self.callOtherClientsFunction("SetSeat", _args)
        self.emptyLocationIndex.remove(locationIndex)
        self.ret_player_in_room_info()
        self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 每人满时，创建新的房间(onRoomEnd为true时插入在当前房间后面)
        if len(_chapter['playerInGame']) == self.info['maxPlayersCount'] and self.info["roomType"] != "challenge":
            self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})

    # 站起
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
        _chapter["playerOutGame"][accountId] = _chapter["playerInGame"][accountId]
        _chapter["playerInGame"].pop(accountId)
        _args = {"accountId": accountId, "locationIndex": locationIndex}
        self.callOtherClientsFunction("StandUp", _args)
        self.emptyLocationIndex.append(locationIndex)
        _chapter["playerOutGame"][accountId]["locationIndex"] = -1
        self.ret_player_in_room_info()

    def ret_account_score(self, account_id, gold):
        """
        广播玩家积分
        :param account_id:
        :param score:
        :return:
        """
        _args = {"accountId": account_id, "gold": gold}
        self.callOtherClientsFunction("RetAccountScore", _args)

    def start_game(self):
        """
        开始游戏
        :param:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>startGame ' % self.id)

        _playerCount = self.get_player_in_game_count()
        if _playerCount >= 3:
            self.chapter_start()

    def player_ready(self, account_id, ready = True):
        chapter = self.chapters[self.cn]
        _player = chapter["playerInGame"][account_id]
        # 如果是比赛场,准备时金币不能小于设定值
        if self.info["roomType"] == "gameCoin" and _player['gold'] < self.info['readyGoldLimit'] and ready:
            self.callClientFunction(account_id, 'Notice', ['您的比赛分不足,请您立即充值.'])
            info_args = {"accountId": account_id}
            self.callOtherClientsFunction("ScoreIsLess", info_args)
            if self.ready_gold_disband_timer == -1 and not self.is_forbid_disband_room():
                self.debug_msg("addTimer ready_gold_disband_timer")
                self.ready_gold_disband_timer = self.addTimer(120, 0, 0)
            return

        if (self.is_gold_session_room() or self.is_challenge_room()) and \
                _player['gold'] < self.info['roomRate']  and ready:
            return
        chapter["playerInGame"][account_id]["ready"] = ready
        _args = {"accountId": account_id, "ready": ready}
        self.callOtherClientsFunction("Ready", _args)

        # # 金币场三个人准备自动开始
        # if self.info["roomType"] == "gold":
        #     if len(self.get_ready_player()) >= 3:
        #         self.start_game()

    def get_ready_player(self):
        chapter = self.chapters[self.cn]
        ready_players = []
        for k, v in chapter["playerInGame"].items():
            if v["ready"]:
                ready_players.append(k)
        return ready_players

    def chapter_ready(self):
        """
        牌局准备
        :return:
        """
        DEBUG_MSG('[Room id %i]------>chapterReady ' % self.id)
        _chapter = self.chapters[self.cn]
        _args = {"Timer": _timeReady}
        self.callOtherClientsFunction("ChapterReady", _args)
        _chapter["chapterStartTimerId"] = self.addTimer(_timeReady, 0, 0)
        _chapter["deadline"] = time.time() + _timeReady

    def chapter_start(self):
        """
        牌局开始
        :return:
        """
        DEBUG_MSG('[Room id %i]------>chapterStart ' % self.id)
        # if self.cn < 1:
        self.started = True
        self.info["started"] = True
        chapter = self.chapters[self.cn]
        _playerInGame = chapter["playerInGame"]
        # 金币场扣除房费
        if self.is_gold_session_room():
            for k, v in _playerInGame.items():
                v['gold'] -= self.info['roomRate']
                self.set_base_player_gold(k)
        if len(self.get_ready_player()) < 2:
            # _args = {"startGameResult": False, "error": "准备人数不足"}
            # self.callClientFunction(self.info["creatorAccountId"], "StartGame", _args)
            return
        _args = {"startGameResult": True, "error": ""}
        # self.callClientFunction(self.info["creatorAccountId"], "StartGame", _args)
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
        # 给可以叫地主的玩家List赋值
        if self.info["LandlordGameType"] == 1:
            chapter["canCallLandLordPlayers"].clear()
            chapter["canGrabLandLordPlayers"].clear()
            for k, v in chapter["playerInGame"].items():
                chapter["canCallLandLordPlayers"].append(k)
                chapter["canGrabLandLordPlayers"].append(k)
        self.changeChapterState(1)
        self.set_current_round(self.cn + 1)
        self.deal_cards()
        self.base.cellToBase({"func": "changeRoomState", "roomState": 1})
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

        if self.info['roomType'] == 'challenge':
            true_player = self.get_true_player()
            self.debug_msg('challenge control result%s' % true_player['entity'].get_challenge_control(self.cn))

    def set_base_player_challenge(self, account, is_win, control_pai_count):
        """
        设置玩家金币数量,通知base
        :param account:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _player = _playerInRoom[account]
        _player["entity"].base.cellToBase(
            {"func": "setChallengeInfo", "challengeLevel": self.get_level(), "win": is_win,
             "controlCount": control_pai_count})

    def random_cards_with_time(self, _chapter_lib):
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
        DEBUG_MSG("len %s,chapter lib%s" % (len(_chapter_lib), _chapter_lib))

    # 发牌
    def deal_cards(self):
        """
        发牌
        :return:
        """
        self.ret_player_in_room_info()
        DEBUG_MSG('[Room id %i]------>dealCards ' % self.id)
        _chapter = self.chapters[self.cn]
        _player_in_game = _chapter["playerInGame"]
        if len(_player_in_game) != 3:
            DEBUG_MSG('player count is error: % i' % len(_player_in_game))
            return

        # 有人输的太多的话，需要发好牌
        is_in_rand_range = self.is_need_rand_score_control("RoomType6")
        luck_player = None
        if is_in_rand_range:
            luck_player = self.select_max_loser(_player_in_game.values())
            # if luck_player:
            #     self.callClientFunction(luck_player['entity'].id, 'Notice', ['发好牌'])

        if not luck_player:
            # 获得应该拿到最大牌的玩家
            luck_player, max_lose_count = self.get_max_losing_streak_player(_player_in_game.values())
            if max_lose_count < 5:
                luck_player = None
            DEBUG_MSG('最大连输 %s %s' % (max_lose_count, luck_player['entity'].id if luck_player else luck_player))

        if not luck_player:
            # 幸运数字玩家
            is_in_rand_range = self.is_need_rand_score_control("RoomType6")
            if is_in_rand_range:
                luck_player = self.select_luck_max_loser(_player_in_game.values())

        # 每日发好牌次数控制
        day_player = self.select_day_good_pai_player(_player_in_game.values(), 4)
        if day_player:
            luck_player = day_player
            self.player_entity(luck_player).increase_day_pai_control_count()

        luck_player_id = -1
        if luck_player:
            luck_player_id = luck_player['entity'].id

        # 挑战赛不进行分数控制
        if self.info["roomType"] == "challenge":
            luck_player_id = -1
            true_player = self.get_true_player()
            if true_player:
                control_count = true_player['entity'].get_challenge_control(self.cn)
                self.debug_msg('control_count:%s' % control_count)
                if control_count > 0:
                    if true_player['entity'].get_control_percent() > 15:
                        bots = []
                        for k, v in _chapter['playerInGame'].items():
                            if v['entity'].info['isBot'] == 1:
                                bots.append(k)
                        if bots:
                            random.shuffle(bots)
                            luck_player_id = bots[0]
                            self.luck_user = 2
                            self.debug_msg('bots id:%s，luck_player%s' % (bots, luck_player_id))
                else:
                    if true_player['entity'].get_control_percent() < 20:
                        luck_player_id = true_player['entity'].id
                        self.luck_user = 1
                        self.debug_msg('给玩家发好牌，luck_player %s' % luck_player_id)

        # 获取生成的手牌和底牌
        all_cards, cover_cards = self.generate_cards()
        player_cards_data = []
        dic_index = 0
        # 玩家手牌赋值
        for k in _player_in_game:
            cards = all_cards[dic_index]
            _player_in_game[k]["cards"] = cards
            dic_index += 1

        # 计算玩家手牌权值
        max_cards_value = -1000
        max_player_id = -1
        for k, v in _player_in_game.items():
            cards_value = R6Util.convert_cards_to_value(v['cards'])
            dic = R6Split.split(cards_value)[1]
            score = R6Score.get_score(dic)
            DEBUG_MSG('deal cards_values %s,%s,%s' % (k, v['entity'].info["name"], score))
            if max_cards_value < score:
                max_cards_value = score
                max_player_id = k
        DEBUG_MSG('deal max_id:%s,luck_player_id:%s' % (max_player_id, luck_player_id))

        if max_player_id != -1 and luck_player_id != -1 and max_player_id != luck_player_id:
            luck_player_cards = _player_in_game[luck_player_id]['cards']
            max_player_cards = _player_in_game[max_player_id]['cards']
            _player_in_game[max_player_id]['cards'] = luck_player_cards
            _player_in_game[luck_player_id]['cards'] = max_player_cards

        # 转化为客户端牌值
        for k in _player_in_game:
            cards = _player_in_game[k]["cards"]
            # 转化为客户端牌值
            client_cards = self.parse_card_to_client(cards)
            player_cards_data.append({"accountId": int(k), "cards": client_cards})

        # 牌局底牌赋值
        _chapter["coverCards"] = cover_cards
        # 转化为客户端牌值
        client_cover_cards = self.parse_card_to_client(cover_cards)
        all_cards_data = {"playerCards": player_cards_data, "coverCards": client_cover_cards}
        # 记录发牌
        record = {}
        # 1 出牌相关置为 0
        record["operationType"] = 0
        # 操作  存储玩家的牌和底牌
        record["operationArgs"] = {"playerCards": player_cards_data, "coverCards": client_cover_cards}
        # 1 将发牌相关数据存到操作回放流程里
        _chapter["operationRecord"].append(record)
        self.send_cards_info_with_encryption(all_cards_data)
        _chapter["dealCardAnimationTimerId"] = self.addTimer(_timeDealCardToPlayer, 0, 0)
        _chapter["deadline"] = time.time() + _timeDealCardToPlayer

    def send_cards_info_with_encryption(self, all_cards_data):
        chapter = self.chapters[self.cn]
        self.debug_msg('cards%s' % all_cards_data)
        for k, v in chapter['playerInGame'].items():
            all_cards_copy = copy.deepcopy(all_cards_data)
            for cards_info in all_cards_copy['playerCards']:
                account_id = cards_info['accountId']
                cards = cards_info['cards']
                if account_id == k:
                    continue
                for x in range(len(cards)):
                    cards[x] = 1
            self.debug_msg('after encryption accountId:%s cards:%s' % (k, all_cards_data))
            self.callClientFunction(k, 'DealCards', all_cards_copy)

    # 获取坐下玩家数量
    def get_player_in_game_count(self):
        """
        返回游戏内玩家数量
        :return:
        """
        _chapter = self.chapters[self.cn]
        return len(_chapter["playerInGame"])

    def get_card_count(self, number, cards):
        count = 0
        for n in cards:
            if str(number) in n:
                count += 1
        return count

        # 生成牌

    def generate_cards(self):
        # 黑红梅方
        card_type = ["a", "b", "c", "d"]
        # 14,A
        # 15,2
        # 16，小王
        # 17，大王
        card_num = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        card_pairs = []
        player1_cards = []
        player2_cards = []
        player3_cards = []
        cover_cards = []
        for card_color in card_type:
            for num in card_num:
                card_pairs.append(card_color + str(num))

        card_pairs.append(str(16))
        card_pairs.append(str(17))

        random.shuffle(card_pairs)
        random.shuffle(card_pairs)

        # 洗牌
        self.random_cards_with_time(card_pairs)

        # 底牌数量
        cover_card_num = 3
        for index in range(0, len(card_pairs) - cover_card_num):
            card_pair = card_pairs[index]
            if index % 3 == 0:
                player1_cards.append(card_pair)
            if index % 3 == 1:
                player2_cards.append(card_pair)
            if index % 3 == 2:
                player3_cards.append(card_pair)

        # 双王不能在一个人手中
        def is_have_two_joke(_cards):
            return ('16' in _cards) and ('17' in _cards)

        def swap_joke(_cards1, _cards2):
            _index = _cards1.index('16')
            _cards1[_index] = _cards2[_index]
            _cards2[_index] = '16'
            DEBUG_MSG("swap_joke %s %s" % (_cards1, _cards2))

        if is_have_two_joke(player1_cards):
            swap_joke(player1_cards, player2_cards)
        elif is_have_two_joke(player2_cards):
            swap_joke(player2_cards, player3_cards)
        elif is_have_two_joke(player3_cards):
            swap_joke(player3_cards, player1_cards)

        # 底牌
        # player1_cards = ["b7", "c7", "d7", "b8", "c8", "d8", "b6", "a6"]
        # player2_cards = ["a3", "b3", "c3", "c4", "a4", "b4", "a7", "a8"]
        cover_cards = card_pairs[-cover_card_num:]
        all_cards = [player1_cards, player2_cards, player3_cards]
        return all_cards, cover_cards

    # 设置回合数
    def set_current_round(self, current_round):
        """
        设置当前轮数
        :param current_round:
        :return:
        """
        DEBUG_MSG('[Room id %i]------>setCurrentRound currentRound %s' % (self.id, current_round))
        _chapter = self.chapters[self.cn]
        _chapter["currentRound"] = current_round
        _args = {"currentRound": _chapter["currentRound"]}
        self.callOtherClientsFunction("RetCurrentRound", _args)

    # 计时器
    def onTimer(self, timer_handle, user_data):
        """
        计时器回调
        :param timer_handle:
        :param user_data:
        :return:
        """
        RoomBase.onTimer(self, timer_handle, user_data)
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]

        if timer_handle == _chapter["chapterStartTimerId"]:
            # 游戏开始计时器
            DEBUG_MSG('[Room id %s]------>onTimer chapterStartTimerId %s' % (self.id, timer_handle))
            self.delTimer(timer_handle)
            _chapter["chapterStartTimerId"] = -1
            self.chapter_start()

        elif timer_handle == _chapter["dealCardAnimationTimerId"]:
            # 发牌动画计时器
            DEBUG_MSG('[Room id %s]------>onTimer dealCardAnimationTimerId %s' % (self.id, timer_handle))
            self.delTimer(timer_handle)
            _chapter["dealCardAnimationTimerId"] = -1
            # 1 发牌动画定时器结束，更改状态为改变牌局状态为叫地主模式
            self.changeChapterState(2)
        # elif timer_handle == _chapter["accountLottery"]:
        #     DEBUG_MSG('[Room id %s]------>onTimer accountLottery %s' % (self.id, timer_handle))
        #     _chapter["accountLottery"] = -1
        #     self.Lottery()
        # 叫地主计时器
        elif timer_handle == _chapter["grabDealerTimer"]:
            DEBUG_MSG('[Room id %s]------>onTimer grabDealerTimer %s' % (self.id, timer_handle))
            self.delTimer(timer_handle)
            _chapter["grabDealerTimer"] = -1
            account_id = self.get_account_id_with_location_index(_chapter["currentLocationIndex"])
            player_cards = _chapter["playerInGame"][account_id]["cards"]
            # 1 叫分场
            if self.info["LandlordGameType"] == 0:
                if self.info["doubleKingGrab"] and str(16) in player_cards and str(17) in player_cards:
                    self.call_dealer(account_id, 3)
                else:
                    self.call_dealer(account_id, 0)
            # 1 欢乐场
            elif self.info["LandlordGameType"] == 1:
                if account_id in _chapter['canCallLandLordPlayers']:
                    DEBUG_MSG("ontimer grabDealerTimer player_cards:%s" % player_cards)
                    # 双王必叫
                    if self.info["doubleKingGrab"] and str(16) in player_cards and str(17) in player_cards:
                        self.grab_dealer(account_id, 1)
                    else:
                        self.grab_dealer(account_id, 2)
                elif account_id in _chapter['canGrabLandLordPlayers']:
                    self.grab_dealer(account_id, 4)

        elif timer_handle == _chapter["botCallDealerTimer"]:
            DEBUG_MSG('[Room id %s]------>onTimer botCallDealerTimer %s' % (self.id, timer_handle))
            self.delTimer(timer_handle)
            _chapter["botCallDealerTimer"] = -1
            # 机器人叫分
            self.bot_call_dealer(_chapter["currentPlayer"])
        elif timer_handle == _chapter['botGrabDealerTimer']:
            self.delTimer(timer_handle)
            _chapter['botGrabDealerTimer'] = -1
            # 机器人抢地主,开启计时器时传入的参数 user_data 为当前操作类型，0 叫地主，1 抢地主
            self.bot_grab_dealer(_chapter['currentPlayer'], user_data)
        # 出牌计时器
        elif timer_handle == _chapter["playCardTimer"]:
            DEBUG_MSG('[Room id %s]------>onTimer playCardTimer %s' % (self.id, timer_handle))
            self.delTimer(timer_handle)
            _chapter["playCardTimer"] = -1
            account_id = self.get_account_id_with_location_index(_chapter["currentLocationIndex"])
            # 时间到出空牌，出空牌等于不出。如果上个玩家是自己则出最小牌
            if _chapter["prePlayer"] == account_id or _chapter["prePlayer"] == -1:
                player_cards = _chapter["playerInGame"][account_id]["cards"]
                player_cards = self.parse_card_to_client(player_cards)
                player_cards.sort()
                self.player_play_cards(account_id, [player_cards[0]])
            else:
                # if _chapter["playerInRoom"][account_id]["delegate_play_card"]:
                #     pass
                # else:
                self.player_play_cards(account_id, [])
        elif timer_handle == _chapter["settlementTimer"]:
            # 下局开始计时器
            DEBUG_MSG('[Room id %s]------>onTimer settlementTimer %s' % (self.id, timer_handle))
            self.delTimer(timer_handle)
            _chapter["settlementTimer"] = -1
            # 如果时间到了就不开始
            DEBUG_MSG(
                '[Room id %s]------>onTimer cn+1 %s,maxChapterCount %s' % (
                    self.id, self.cn + 1, self.info["maxChapterCount"]))
            # 输2局或赢两局,则直接判断为赢或输
            if self.info["roomType"] == "challenge":
                chapter = self.chapters[self.cn]
                playerInGame = chapter["playerInGame"]
                for k, v in playerInGame.items():
                    if not v['entity'].info["isBot"]:
                        if v["totalGoldChange"] >= 2 or (self.cn == 1 and v["totalGoldChange"] == 0) or self.cn + 1 >= \
                                self.info["maxChapterCount"]:
                            self.challenge_total_settlement()
                            self.write_chapter_info_to_db()
                            return

            # 总结算
            if self.cn + 1 >= self.info["maxChapterCount"]:
                self.total_settlement()
                self.write_chapter_info_to_db()
                return
            # 如果有人钱为负数，总结算
            # for k, v in _chapter["playerInGame"].items():
            #     if v["gold"] <= 0:
            #         self.total_settlement()
            #         self.write_chapter_info_to_db()
            #         return
            self.chapter_clear()
            self.changeChapterState(0)
        elif timer_handle == _chapter["botPlayCardTimer"]:
            DEBUG_MSG('[Room id %s]------>onTimer botPlayCardTimer %s' % (self.id, timer_handle))
            self.delTimer(timer_handle)
            _chapter["botPlayCardTimer"] = -1
            # todo：测试代码
            self.bot_play_card()
        elif timer_handle == self.disband_timer:
            DEBUG_MSG('[Room id %s]------>onTimer disbandTime %s' % (self.id, timer_handle))
            self.disband_timer = -1
            self.delTimer(timer_handle)
            self.is_disbanding = False
            self.total_settlement()
            self.write_chapter_info_to_db()
        # 1 轮询是否可以开始牌局计时器
        elif timer_handle == _chapter["mainTimerId"]:
            all_ready = True
            for k, v in _chapter["playerInGame"].items():
                if not v["ready"]:
                    all_ready = False
                    break
            if all_ready and len(_chapter["playerInGame"]) >= 3:
                self.delTimer(timer_handle)
                _chapter["mainTimerId"] = -1
                self.start_game()
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
                    self.total_settlement()
                    self.write_chapter_info_to_db()

    # 改变当前牌局状态
    def changeChapterState(self, state):
        """
        改变游戏状态
        :param state:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _chapter["currentState"] = state
        if state == 0:
            # 准备
            _args = {"state": state, "Timer": 0}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.bots_ready()

            # 第二局开始自动准备
            #if self.cn > 0:
            #    for k, v in _chapter["playerInGame"].items():
            #        if v["entity"].info["isBot"] == 0:
            #            self.player_ready(k)

            #_chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)

        elif state == 1:
            # 牌局开始、发牌
            _args = {"state": state, "Timer": _timeDealCardToPlayer}
            self.callOtherClientsFunction("changeChapterState", _args)
        elif state == 2:
            # 叫地主
            _args = {"state": state}
            self.callOtherClientsFunction("changeChapterState", _args)
            random_index = 0
            # 1 第一局  随机先叫
            if self.cn == 0:
                random_index = random.randint(0, 2)
            else:
                # 1 callLandlordType   抢地主的方式（叫地主）
                # 随机先叫,2:为随机先叫,1:为赢家先叫
                if self.info["callLandlordType"] == 2:
                    random_index = random.randint(0, 2)
                # 赢家先叫
                elif self.info["callLandlordType"] == 1:
                    _chapter = self.chapters[self.cn - 1]
                    for k, v in _chapter["playerInGame"].items():
                        if len(v["cards"]) == 0:
                            location_index = v["locationIndex"]
                            random_index = location_index
                            break
            # 玩牌类型LandlordGameType   0   叫分场  1 欢乐场
            if self.info["LandlordGameType"] == 0:
                self.notice_call_dealer(random_index)
            # 1 欢乐场
            elif self.info["LandlordGameType"] == 1:
                self.notice_grab_dealer_in_joy_mode(random_index)

        elif state == 3:
            # 比赛开始
            # 关闭叫地主计时器
            self.delTimer(_chapter["grabDealerTimer"])
            _chapter["grabDealerTimer"] = -1
            _args = {"state": state}
            self.callOtherClientsFunction("changeChapterState", _args)
            # 设置身份
            self.set_player_identity()
            # # 设置倍数信息
            # self.set_chapter_multiple()
            # 设置底分
            self.set_base_score()
            # 广播玩家身份信息
            identity_data = []
            for k, v in _chapter["playerInGame"].items():
                player_identity = {"accountId": int(k), "identity": v["identity"]}
                identity_data.append(player_identity)
            DEBUG_MSG("[Room6]----------> Change chapter 3 identity_data:%s" % identity_data)
            _args = {"identityInfo": identity_data}
            self.callOtherClientsFunction("PlayerIdentityInfo", _args)
            # 给地主添加底牌
            self.add_cover_cards()
            # 通知地主操作
            self.change_play_card_operation(_chapter["dealer"])
        elif state == 4:
            # 结算
            _args = {"state": state, "Timer": settlement_time}
            self.callOtherClientsFunction("changeChapterState", _args)
            if self.is_challenge_room():
                self.challenge_settlement()
            else:
                self.settlement()
            for k, v in _chapter["playerInGame"].items():
                self.player_ready(k, False)
                
        elif state == 5:
            # 总结算
            # 关闭所有计时器
            _args = {"state": state, "Timer": 0}
            self.callOtherClientsFunction("changeChapterState", _args)

    def notice_call_dealer(self, location_index):
        """
        叫分模式，通知玩家叫地主分
        :param location_index:
        :return:
        """
        chapter = self.chapters[self.cn]
        account_id = self.get_account_id_with_location_index(location_index)
        # 当前操作位置
        chapter["currentLocationIndex"] = location_index
        # 叫地主计时器
        chapter["grabDealerTimer"] = self.addTimer(grab_dealer_time, 0, 0)
        chapter["deadline"] = time.time() + grab_dealer_time
        _args = {"accountId": account_id, "Timer": grab_dealer_time}
        chapter["currentPlayer"] = account_id
        self.callOtherClientsFunction("ChangeOperation", _args)

        if chapter["playerInGame"][account_id]["entity"].info["isBot"] == 1:
            grab_timer = random.randint(bot_call_dealer_time_min, bot_call_dealer_time_max)
            # 添加机器人叫地主计时器
            chapter["botCallDealerTimer"] = self.addTimer(grab_timer, 0, 0)
            chapter["deadline"] = time.time() + grab_timer

    def notice_grab_dealer_in_joy_mode(self, location_index):
        """
        抢地主模式，通知玩家抢地主 v
        ];
        ]
        :param location_index: 
        :return: 
        """
        chapter = self.chapters[self.cn]
        account_id = self.get_account_id_with_location_index(location_index)
        chapter["currentLocationIndex"] = location_index
        # 叫地主计时器
        chapter["grabDealerTimer"] = self.addTimer(grab_dealer_time, 0, 0)
        chapter["deadline"] = time.time() + grab_dealer_time
        operation_type = -1
        if account_id in chapter["canCallLandLordPlayers"]:
            # 0 叫地主
            operation_type = 0
        elif account_id in chapter["canGrabLandLordPlayers"]:
            # 1 抢地主
            operation_type = 1
        _args = {"accountId": account_id, "operationType": operation_type, "Timer": grab_dealer_time}
        chapter["currentPlayer"] = account_id
        self.callOtherClientsFunction("ChangeOperation", _args)

        # 机器人叫地主、抢地主
        if chapter["playerInGame"][account_id]["entity"].info["isBot"] == 1:
            grab_timer = random.randint(bot_grab_dealer_time_min, bot_grab_dealer_time_max)
            # 添加机器人叫地主计时器
            chapter["botGrabDealerTimer"] = self.addTimer(grab_timer, 0, operation_type)
            chapter["deadline"] = time.time() + grab_timer

    # 叫分场抢地主广播
    def call_dealer(self, account_id, result):
        """
         玩家叫地主广播
        :param account_id:
        :param result:
        :return:
        """
        DEBUG_MSG("grab_dealer accountId:%s" % account_id)
        chapter = self.chapters[self.cn]
        if chapter['currentState'] != 2:
            DEBUG_MSG("grab_dealer is not state 2")
            return
        grab_player = chapter["playerInGame"][account_id]
        if grab_player["grabResult"] != -1:
            return
        grab_player["grabResult"] = result
        args = {"accountId": account_id, "result": result}
        self.callOtherClientsFunction("GrabDealer", args)
        # 记录叫地主
        record = {}
        record["accountId"] = account_id
        record["operationType"] = 1
        record["operationArgs"] = {"result": result}
        chapter["operationRecord"].append(record)
        # 关闭叫地主计时器
        self.delTimer(chapter["grabDealerTimer"])
        chapter["grabDealerTimer"] = -1
        if result == 2:
            chapter["multiple"] *= 2
            args = {"multiple": chapter["multiple"]}
            self.callOtherClientsFunction("RetMultiple", args)
        # 有人叫三分，进入阶段 3
        if result >= 3:
            chapter["multiple"] = 1
            chapter["multiple"] *= 3
            args = {"multiple": chapter["multiple"]}
            self.callOtherClientsFunction("RetMultiple", args)
            self.changeChapterState(3)
        # 还有未操作玩家提醒下一位叫地主
        elif len(self.get_un_grab_players()) > 0:
            self.notice_call_dealer(self.get_next_location_index())
        else:
            if self.need_refresh():
                # 重新发牌，清除玩家抢地主信息
                self.clear_player_grab_result()
                self.chapter_start()
            else:
                self.changeChapterState(3)

    # 欢乐模式，叫地主，抢地主操作
    def grab_dealer(self, account_entity_id, result):
        chapter = self.chapters[self.cn]
        if chapter['currentState'] != 2:
            DEBUG_MSG("grab_dealer is not state 2")
            return
        self.callOtherClientsFunction("PlayerOperation", {"operationResult": result, "accountId": account_entity_id})
        # 记录叫地主
        record = {}
        record["accountId"] = account_entity_id
        record["operationType"] = 1
        record["operationArgs"] = {"result": result}
        chapter["operationRecord"].append(record)
        # 1：叫 2：不叫 3：抢 4：不抢
        if result == 1:
            if len(chapter["canCallLandLordPlayers"]) == 1:
                chapter["dealer"] = account_entity_id
                chapter["multiple"] *= 2
                args = {"multiple": chapter["multiple"]}
                self.callOtherClientsFunction("RetMultiple", args)
                self.changeChapterState(3)
                return
            # 是否叫地主置为1
            chapter["playerInGame"][account_entity_id]["callLandLord"] = 1
            chapter["playerInGame"][account_entity_id]["grabLandLord"] = 1
            chapter["canCallLandLordPlayers"].clear()
            chapter["multiple"] *= 2
            args = {"multiple": chapter["multiple"]}
            self.callOtherClientsFunction("RetMultiple", args)
        elif result == 2:
            chapter["playerInGame"][account_entity_id]["callLandLord"] = 0
            chapter["canCallLandLordPlayers"].remove(account_entity_id)
            chapter["canGrabLandLordPlayers"].remove(account_entity_id)
            all_called_0 = True
            for k, v in chapter["playerInGame"].items():
                if v["callLandLord"] != 0:
                    all_called_0 = False
                    break
            # 都不叫，重新发牌
            if all_called_0:
                self.clear_call_grab_info_in_joy_mode()
                self.chapter_start()
                return
        elif result == 3:
            chapter["playerInGame"][account_entity_id]["grabLandLord"] = 1
            chapter["canGrabLandLordPlayers"].remove(account_entity_id)
            chapter["multiple"] *= 2
            args = {"multiple": chapter["multiple"]}
            self.callOtherClientsFunction("RetMultiple", args)
            if len(chapter["canGrabLandLordPlayers"]) == 0:
                chapter["dealer"] = account_entity_id
                self.changeChapterState(3)
                return
        elif result == 4:
            chapter["playerInGame"][account_entity_id]["grabLandLord"] = 0
            chapter["canGrabLandLordPlayers"].remove(account_entity_id)
            # 所有人都进行过抢地主操作
            if len(chapter["canGrabLandLordPlayers"]) == 0:
                # 找到上个抢地主的人
                pre_grab_account_id = self.find_pre_grab_dealer_player(chapter["currentLocationIndex"])
                chapter["dealer"] = pre_grab_account_id
                DEBUG_MSG("grab_dealer delaer:%s" % pre_grab_account_id)
                self.changeChapterState(3)
                return
            #
            if len(chapter["canGrabLandLordPlayers"]) == 1:
                # 其他人都不抢地主
                grab_0_player = []
                for k, v in chapter["playerInGame"].items():
                    if v["grabLandLord"] == 0 or v["grabLandLord"] == -1:
                        grab_0_player.append(k)
                if len(grab_0_player) == 2:
                    for k, v in chapter["playerInGame"].items():
                        if k not in grab_0_player:
                            chapter["dealer"] = k
                            self.changeChapterState(3)
                            return

        # 通知下个人操作
        next_location = self.get_next_location_index()
        # todo:适用于三人斗地主
        if len(chapter["canCallLandLordPlayers"]) == 0:
            next_account_id = self.get_account_id_with_location_index(next_location)
            if next_account_id not in chapter["canGrabLandLordPlayers"]:
                next_location = (next_location + 1) % 3
        self.notice_grab_dealer_in_joy_mode(next_location)

    # 找到上个抢地主的人,递归，谨慎使用
    def find_pre_grab_dealer_player(self, current_location_index):
        chapter = self.chapters[self.cn]
        DEBUG_MSG("current_location_index%s" % current_location_index)
        pre_player_location = self.get_previous_location_index(current_location_index)
        for k, v in chapter["playerInGame"].items():
            DEBUG_MSG("pre_player_location%s" % pre_player_location)
            DEBUG_MSG("player index:%s,grab:%s" % (v["locationIndex"], v["grabLandLord"]))
            if v["locationIndex"] == pre_player_location and v["grabLandLord"] == 1:
                return k

        return self.find_pre_grab_dealer_player(pre_player_location)

    # 清空欢乐模式叫地主、抢地主信息
    def clear_call_grab_info_in_joy_mode(self):
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            v["callLandLord"] = -1
            v["grabLandLord"] = -1

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

    def voiceChat(self, accountId, url):
        """
        语音聊天
        :param accountId:
        :param url:
        :return:
        """
        _args = {"accountId": accountId, "url": url}
        self.callOtherClientsFunction("VoiceChat", _args)

    # 分配身份
    def set_player_identity(self):
        """
        设置玩家身份
        :return:
        """
        chapter = self.chapters[self.cn]
        # 1 叫分斗地主玩法
        if self.info["LandlordGameType"] == 0:
            max_result = 0

            for k, v in chapter["playerInGame"].items():
                if v["grabResult"] > max_result:
                    max_result = v["grabResult"]

            # 与最高分相同的第一个玩家是地主
            for k, v in chapter["playerInGame"].items():
                if v["grabResult"] == max_result:
                    v["identity"] = 1
                    chapter["dealer"] = k
                    return
        # 1 欢乐场叫地主玩法
        elif self.info["LandlordGameType"] == 1:
            DEBUG_MSG("dealer:%s" % chapter["dealer"])
            for k, v in chapter["playerInGame"].items():
                if k == chapter["dealer"]:
                    v["identity"] = 1
                    break

    # 1 设置房间的倍数 叫分场
    def set_chapter_multiple(self):
        # 1 获取当前局数
        chapter = self.chapters[self.cn]
        max_grab_result = 1
        for k, v in chapter["playerInGame"].items():
            if v["grabResult"] > max_grab_result:
                max_grab_result = v["grabResult"]
        chapter["multiple"] = max_grab_result
        args = {"multiple": chapter["multiple"]}
        self.callOtherClientsFunction("RetMultiple", args)

    # 设置底分  新的需求不用 设置底分  使用的是前端传过来的底分数据
    def set_base_score(self):
        pass

    # 获得没有进行叫地主操作的玩家
    def get_un_grab_players(self):
        """
        获取未进行叫地主操作的玩家
        :return:
        """
        chapter = self.chapters[self.cn]
        un_grab_players = []
        for k, v in chapter["playerInGame"].items():
            if v["grabResult"] == -1:
                un_grab_players.append(k)
        return un_grab_players

    # 获得剩余卡牌
    def get_remain_cards(self):
        remain_cards = []
        for k, v in self.chapters[self.cn]["playerInGame"].items():
            remain_cards.extend(v["cards"])
        return remain_cards

    # 向客户端发送所有剩余卡牌
    def send_remain_cards(self):
        remain_cards = self.get_remain_cards()
        args = {"remainCards": self.parse_card_to_client(remain_cards)}
        self.callOtherClientsFunction("RemainCards", args)

    def send_players_remain_cards(self, accountId):
        chapter = self.chapters[self.cn]
        if chapter["playerInGame"][accountId]["entity"].info["addOn"] != 1:
            return
        player_cards = {}
        for k, v in chapter["playerInGame"].items():
            player_cards[k] = self.parse_card_to_client(v["cards"])
        self.callClientFunction(accountId, "PlayersRemainCards", player_cards)

    # 向客户端发送战绩信息
    def send_room_score(self, account_id):
        chapter = {}
        args = {}
        if len(self.chapters) > 1:
            chapter = self.chapters[self.cn - 1]
            args = {"roomRecord": chapter["roomRecord"]}
        self.callClientFunction(account_id, "RoomRecord", args)

    # 向客户端发送聊天记录
    def send_chat_history(self, account_id):
        chapter = self.chapters[self.cn]
        chat_history = chapter["chatHistory"]
        arg = {"chatHistory": chat_history}
        self.callClientFunction(account_id, "ChatHistory", arg)

    # 获得下个玩家位置
    def get_next_location_index(self):
        """
        获取下一个玩家位置
        :return:
        """
        chapter = self.chapters[self.cn]
        current = chapter["currentLocationIndex"]
        return (current + 1) % 3

    def get_previous_location_index(self, current_location_index):
        """
        获取上一个玩家位置
        :return:
        """
        chapter = self.chapters[self.cn]
        current = current_location_index
        current -= 1
        if current < 0:
            current += len(chapter["playerInGame"])
        return current

    # 清除叫地主结果
    def clear_player_grab_result(self):
        player_in_game = self.chapters[self.cn]["playerInGame"]
        for k, v in player_in_game.items():
            v["grabResult"] = -1

    # 是否需要重新发牌
    def need_refresh(self):
        """
        是否需要重新发牌
        :return:
        """
        # 不叫地主的玩家数量
        zero_operation_count = 0
        chapter = self.chapters[self.cn]

        for k, v in chapter["playerInGame"].items():
            if v["grabResult"] == 0:
                zero_operation_count += 1

        return zero_operation_count >= 3

    # 将底牌加入玩家手牌
    def add_cover_cards(self):
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if v["identity"] == 1:
                v["cards"] += chapter["coverCards"]
                return

    # 改变当前出牌玩家
    def change_play_card_operation(self, account_id):
        """
        改变当前出牌玩家
        :param account_id:
        :return:
        """
        # 获取当前牌局信息
        chapter = self.chapters[self.cn]
        # 检测牌局是否结束
        if self.check_chapter_over():
            self.changeChapterState(4)
            return
        # 遍历游戏中的玩家
        for k, v in chapter["playerInGame"].items():
            # 找到要出牌的玩家
            if account_id == k:
                # 将当前操作玩家位置设置成当前玩家
                chapter["currentLocationIndex"] = v["locationIndex"]
                # 判断出牌玩家是否在线
                # if self.is_offline(account_id):
                #     # 出牌计时器
                #     chapter["playCardTimer"] = self.addTimer(bot_play_card_time_min, 0, 0)
                #     chapter["deadline"] = time.time() + bot_play_card_time_min
                #     args = {"accountId": int(k), "Timer": bot_play_card_time_min}
                # else:
                if self.info['timeDown'] > 0:
                    if chapter["playerInGame"][account_id]["entity"].info["isBot"] == 1:
                        play_card_timer = random.randint(bot_play_card_time_min, bot_play_card_time_max)
                        # 添加机器人叫地主计时器
                        chapter["botPlayCardTimer"] = self.addTimer(play_card_timer, 0, 0)
                    else:
                        # 玩家在线时出牌计时器
                        chapter["playCardTimer"] = self.addTimer(self.info['timeDown'], 0, 0)
                    args = {"accountId": int(k), "Timer": self.info['timeDown']}
                    chapter["deadline"] = time.time() + self.info['timeDown']

                else:
                    args = {"accountId": int(k), "Timer": 20}
                    chapter['deadLine'] = time.time() + 20

                chapter["currentPlayer"] = int(k)
                self.callOtherClientsFunction("ChangeOperation", args)
                return

    # 检查牌局是否结束
    def check_chapter_over(self):
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if len(v["cards"]) == 0:
                chapter["winner"] = k
                return True
        return False

    # 玩家出牌
    def player_play_cards(self, account_id, client_cards):
        """
        该方法实现出牌大小判断及是否广播
        :param account_id:
        :param client_cards:
        :return:
        """
        DEBUG_MSG('[player_play_cards] cards is %s' % client_cards)
        chapter = self.chapters[self.cn]
        # 只有出牌阶段可以出牌
        if chapter['currentState'] != 3:
            self.debug_msg("player_play_cards is not state 3")
            return

        server_cards = self.parse_card_to_server(client_cards)
        server_cards_type = RoomType6Calculator.play_card_correct(server_cards, self.info["SiDaiEr"])
        # 如果当前操作玩家不是自己，出牌失败
        if chapter["playerInGame"][account_id]["locationIndex"] != chapter["currentLocationIndex"]:
            self.send_player_cards(account_id, -1, client_cards, server_cards_type)
            return

        # -1：出牌失败、不符合规则，0：不出，1：出牌成功
        # 出牌数是零，不出牌
        if len(client_cards) == 0:
            # 如果上个出牌人是自己或没有出牌人，不出失败
            if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
                self.send_player_cards(account_id, -1, client_cards, RoomType6Calculator.CardType.invalid)
            else:
                self.send_player_cards(account_id, 0, client_cards, RoomType6Calculator.CardType.invalid)
            return

        # self.info["SiDaiEr"] = self.info["SiDaiEr"] or False
        # 如果不符合基本规则，出牌失败
        if server_cards_type == RoomType6Calculator.CardType.invalid:
            self.send_player_cards(account_id, -1, client_cards, server_cards_type)
            return

        # 如果手中没有此牌出牌失败
        for s_card in server_cards:
            if s_card not in chapter["playerInGame"][account_id]["cards"]:
                self.send_player_cards(account_id, -1, client_cards, server_cards_type)
                return

        # 如果上个出牌人是自己或没有出牌人，出牌成功
        if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
            self.send_player_cards(account_id, 1, client_cards, server_cards_type)
        # 如果之前有别人出牌
        else:
            # 如果比之前出牌大，出牌成功；否则失败
            if self.play_card_compare(server_cards, chapter["prePlayerPlayCards"]):
                self.send_player_cards(account_id, 1, client_cards, server_cards_type)
            else:
                self.send_player_cards(account_id, -1, client_cards, server_cards_type)

    # 广播出牌结果
    def send_player_cards(self, account_id, result, client_cards, cards_type):
        """
        广播出牌结果
        :param account_id:
        :param result:
        :param client_cards:
        :param cards_type:
        :return:
        """
        args = {"accountId": account_id, "result": result, "cards": client_cards, "cards_type": cards_type.value}
        self.callOtherClientsFunction("PlayCards", args)
        if result == -1:
            return

        chapter = self.chapters[self.cn]
        player_cards = chapter["playerInGame"][account_id]["cards"]
        player_played_cards = chapter["playerInGame"][account_id]["playedCards"]
        server_cards = self.parse_card_to_server(client_cards)
        if result == 1:
            # 如果出牌成功为上个玩家出牌赋值，移除玩家手牌
            chapter["prePlayer"] = account_id
            chapter["prePlayerPlayCards"] = self.parse_card_to_server(client_cards)
            for i in server_cards:
                player_cards.remove(i)
                player_played_cards.append(i)
            # 记录出牌次数
            chapter["playerInGame"][account_id]["playCount"] += 1
            # 1 新的需求  根据前端传过来的炸弹封顶的倍数 来判断
            # 判断翻倍的最大数量 大于倍以后就不再翻倍
            if cards_type == RoomType6Calculator.CardType.zhadan or cards_type == RoomType6Calculator.CardType.wangzha:
                # -1 不封顶
                if self.info["bombCaps"] == -1 or chapter['bombCount'] < self.info["bombCaps"]:
                    chapter["bombCount"] += 1
                    chapter["multiple"] *= 2
                    args = {"multiple": chapter["multiple"]}
                    DEBUG_MSG('bomb,multiple:%s' % chapter['multiple'])
                    self.callOtherClientsFunction("RetMultiple", args)

            # 发送剩余卡牌
            self.send_remain_cards()
        # 关闭出牌计时器
        self.delTimer(chapter["playCardTimer"])
        chapter["playCardTimer"] = -1
        # 记录出牌步骤
        record = {}
        record["accountId"] = account_id
        # 1 相关类型置为 2
        record["operationType"] = 2
        # 操作  存储玩家发的牌   牌得类型
        record["operationArgs"] = {"clientCards": client_cards,
                                   "cardsType": RoomType6Calculator.play_card_correct(server_cards,
                                                                                      self.info["SiDaiEr"]).value}
        chapter["operationRecord"].append(record)

        # 切换下个出牌玩家
        self.change_play_card_operation(self.get_next_player_with_account_id(account_id))

    # 通过 accountId 获取下个玩家
    def get_next_player_with_account_id(self, account_id):
        location_index = -1
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if account_id == k:
                location_index = v["locationIndex"]
                break

        if location_index != -1:
            location_index = (location_index + 1) % 3
            return self.get_player_with_location_index(location_index)
        else:
            return -1

    #  通过accountid获取玩家位置
    # def get_location_index(self,account_id):
    #     chapter = self.chapters[self.cn]
    #     for k, v in chapter["playerInGame"].items():
    #         if account_id == k:
    #             location_index = v["locationIndex"]

    # 通过 location_index 获取玩家
    def get_player_with_location_index(self, location_index):
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if location_index == v["locationIndex"]:
                return k

    # 出牌是否比上家大
    def play_card_compare(self, current_cards, pre_cards):
        return RoomType6Calculator.compare_cards(current_cards, pre_cards, self.info["SiDaiEr"])

    # 结算
    def settlement(self):
        chapter = self.chapters[self.cn]
        # 1 底分*倍数
        settlement_gold = self.info["baseScore"] * chapter["multiple"]
        dealer = chapter["playerInGame"][chapter["dealer"]]
        # 玩家可以输的钱的上限
        lose_limit = 100
        # 如果没开启比赛币
        if not self.have_gold_limit:
            lose_limit = sys.maxsize
        farmers_id = []
        farmers = []
        # winner = []
        # 0 农民，1 地主
        # winner_identity = -1
        # args = {}
        gold_change = {}
        total_gold_change = {}
        remain_cards = {}
        # 1 牌型是否是春天
        spring = False
        # 后台抽成比例
        proportion = self.cutRatio
        playerInGame = chapter["playerInGame"]
        # 1 循环判断游戏内玩家的身份
        for k, v in playerInGame.items():
            if v["identity"] == 0:
                farmers.append(v)
                farmers_id.append(k)
        # 地主获胜
        # 1 判断房间赢者是地主
        if chapter["winner"] == chapter["dealer"]:
            # 判断地主是否春天
            if len(farmers[0]["cards"]) == len(farmers[1]["cards"]) == 17:
                spring = True
            if spring:
                settlement_gold *= spring_multiple
                chapter["multiple"] *= spring_multiple
            farmers1_lose = settlement_gold
            farmers2_lose = settlement_gold
            # 1 判断农民1 的金币数小于要扣的时候
            if farmers[0]["gold"] + lose_limit < settlement_gold:
                # 1 把农民的钱全部给地主
                farmers1_lose = farmers[0]["gold"] + lose_limit
            if farmers[1]["gold"] + lose_limit < settlement_gold:
                farmers2_lose = farmers[1]["gold"] + lose_limit
            farmers[0]["goldChange"] = -farmers1_lose
            farmers[1]["goldChange"] = -farmers2_lose
            farmers[0]["gold"] += farmers[0]["goldChange"]
            farmers[1]["gold"] += farmers[1]["goldChange"]
            # 设置金币总改变
            farmers[0]["totalGoldChange"] += farmers[0]["goldChange"]
            farmers[1]["totalGoldChange"] += farmers[1]["goldChange"]
            dealer["goldChange"] = (farmers1_lose + farmers2_lose) * (1 - proportion)
            dealer["gold"] += dealer["goldChange"]
            dealer["totalGoldChange"] += dealer["goldChange"]
            winner = [chapter["dealer"]]
            winner_identity = 1
        #  1 如果是农民赢
        else:
            if chapter["playerInGame"][chapter["dealer"]]["playCount"] == 1:
                spring = True
            if spring:
                settlement_gold *= spring_multiple
                chapter["multiple"] *= spring_multiple
            # 1 赢的钱为计算的结果  因为钻石场是根据分来计算
            farmers1_win = settlement_gold
            farmers2_win = settlement_gold
            if dealer["gold"] + lose_limit < farmers1_win + farmers2_win:
                farmers1_win = dealer["gold"] / 2 + lose_limit / 2
                farmers2_win = dealer["gold"] / 2 + lose_limit / 2
            farmers[0]["goldChange"] = farmers1_win * (1 - proportion)
            farmers[1]["goldChange"] = farmers2_win * (1 - proportion)
            farmers[0]["gold"] += farmers[0]["goldChange"]
            farmers[1]["gold"] += farmers[1]["goldChange"]
            farmers[0]["totalGoldChange"] += farmers[0]["goldChange"]
            farmers[1]["totalGoldChange"] += farmers[1]["goldChange"]

            dealer["goldChange"] = -(farmers1_win + farmers2_win)
            dealer["gold"] += dealer["goldChange"]
            dealer["totalGoldChange"] += dealer["goldChange"]
            winner = [farmers_id[0], farmers_id[1]]
            winner_identity = 0
        for k, v in playerInGame.items():
            # 获得金币改变数据
            gold_change[k] = v["goldChange"]
            total_gold_change[k] = v['totalGoldChange']
            # 剩余手牌
            remain_cards[k] = self.parse_card_to_client(v["cards"])
            # 修改玩家房间内积分
            self.ret_account_score(k, v["gold"])
            # 修改玩家金币
            if self.info["roomType"] == "gameCoin":
                self.set_base_player_game_coin(k)
            else:
                self.set_base_player_gold(k)
            # 更新分数控制
            v["entity"].update_score_control(v['goldChange'])

        # 统计输牌玩家,计入连输统计
        for k, v in playerInGame.items():
            is_lose = False
            if v['goldChange'] < 0:
                is_lose = True
            elif v['goldChange'] == 0:
                continue
            self.set_losing_streak_history(v, is_lose)

        _args = {"winner": winner, "timer": settlement_time, "goldChange": gold_change, "remainCards": remain_cards,
                 'totalGoldChange': total_gold_change,
                 "spring": spring, 'multiple': chapter["multiple"]}
        self.callOtherClientsFunction("Settlement", _args)

        player_record = {}
        for k, v in playerInGame.items():
            record = {"preGoldChange": v["goldChange"], "totalGoldChange": v["totalGoldChange"],
                      "name": v["entity"].info["name"]}
            player_record[k] = record
        chapter["roomRecord"] = player_record
        # 清理、下局开始倒计时
        chapter["settlementTimer"] = self.addTimer(settlement_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_time
        self.settlement_count += 1
        if self.settlement_count == 1:
            self.base.cellToBase({'func': 'addTodayRoom'})
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

    def challenge_settlement(self):
        chapter = self.chapters[self.cn]
        # 1 底分*倍数
        dealer = chapter["playerInGame"][chapter["dealer"]]
        farmers_id = []
        farmers = []
        gold_change = {}
        total_gold_change = {}
        remain_cards = {}
        # 1 牌型是否是春天
        spring = False
        # 后台抽成比例
        proportion = self.cutRatio
        playerInGame = chapter["playerInGame"]
        # 1 循环判断游戏内玩家的身份
        for k, v in playerInGame.items():
            if v["identity"] == 0:
                farmers.append(v)
                farmers_id.append(k)
        # 地主获胜
        # 1 判断房间赢者是地主
        if chapter["winner"] == chapter["dealer"]:
            farmers[0]["goldChange"] = 0
            farmers[1]["goldChange"] = 0
            dealer["goldChange"] = 1
            # 设置金币总改变
            farmers[0]["totalGoldChange"] += farmers[0]["goldChange"]
            farmers[1]["totalGoldChange"] += farmers[1]["goldChange"]
            dealer["totalGoldChange"] += dealer["goldChange"]
            winner = [chapter["dealer"]]
        #  1 如果是农民赢
        else:
            farmers[0]["goldChange"] = 1
            farmers[1]["goldChange"] = 1
            dealer["goldChange"] = 0
            farmers[0]["totalGoldChange"] += farmers[0]["goldChange"]
            farmers[1]["totalGoldChange"] += farmers[1]["goldChange"]
            dealer["totalGoldChange"] += dealer["goldChange"]
            winner = [farmers_id[0], farmers_id[1]]

        for k, v in playerInGame.items():
            # 获得金币改变数据
            gold_change[k] = v["goldChange"]
            total_gold_change[k] = v['totalGoldChange']
            # 剩余手牌
            remain_cards[k] = self.parse_card_to_client(v["cards"])
        _args = {"winner": winner, "timer": settlement_time, "goldChange": gold_change, "remainCards": remain_cards,
                 'totalGoldChange': total_gold_change,
                 'multiple': chapter["multiple"]}
        self.callOtherClientsFunction("Settlement", _args)

        player_record = {}
        for k, v in playerInGame.items():
            record = {"preGoldChange": v["goldChange"], "totalGoldChange": v["totalGoldChange"],
                      "name": v["entity"].info["name"]}
            player_record[k] = record
        chapter["roomRecord"] = player_record
        # 清理、下局开始倒计时
        chapter["settlementTimer"] = self.addTimer(settlement_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_time
        self.settlement_count += 1
        # 统计玩家挑战赛输赢
        if self.is_challenge_room():
            self.debug_msg("feedback_challenge_control1")
            for k, v in playerInGame.items():
                self.debug_msg("feedback_challenge_control2")
                if v['entity'].info['isBot'] == 0:
                    self.debug_msg("feedback_challenge_control3")
                    v['entity'].feedback_challenge_control(self.cn, int(v['goldChange'] > 0))
        # if self.settlement_count == 1:
        #     # 通知BASE，此次挑战次数加1
        #     # self.base.cellToBase({'func': 'addTodayRoom'})
        #     self.base.cellToBase({'func': 'addChallengeCount'})

    def total_settlement(self):
        if self.total_settlement_ed:
            return
        # 1 关闭所有定时器
        self.close_all_timer()
        # 1 更改房间状态
        self.changeChapterState(5)
        # 1 设置总结算为True
        self.total_settlement_ed = True
        if self.is_challenge_room():
            # 挑战赛另外处理
            self.challenge_total_settlement()
            return
        # 1 当前牌局
        chapter = self.chapters[self.cn]

        if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
            self.normal_lottery()

        player_settlement_info = []
        for k, v in chapter["playerInGame"].items():
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
        # 忽略判断，创建一个房间
        self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info, 'ignoreJudge': True, 'onRoomEnd': True})
        self.save_record_str()
        # 清理观战的玩家
        _playerOutGameCopy = chapter["playerOutGame"].copy()
        for k, v in _playerOutGameCopy.items():
            self.kick_out(k)
        # 同步局数
        if self.is_tea_house_room and self.settlement_count >= 1:
            self.set_base_player_chapter_count()
        # 输牌次数同步到base
        self.set_losing_streak_count_in_base(chapter["playerInGame"])
        self.set_day_good_pai_count_in_base(chapter["playerInGame"])

        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(settlement_clear_players_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_clear_players_time

    @staticmethod
    def is_bot_player(_player):
        return True if _player["entity"].info["isBot"] == 1 else False

    def challenge_total_settlement(self):
        """挑战赛总结算"""
        # if self.total_settlement_ed:
        #     return
        # # 1 关闭所有定时器
        # self.close_all_timer()
        # # 1 更改房间状态
        # self.changeChapterState(5)
        # # 1 设置总结算为True
        # self.total_settlement_ed = True
        # 1 当前牌局
        chapter = self.chapters[self.cn]
        prizeName = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(self.get_level())]['prizeName']
        prizeType = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(self.get_level())]['prizeType']
        prizePrice = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(self.get_level())]['prizePrice']

        # 找玩家
        player_id = 0
        is_player_win = False
        for k, v in chapter["playerInGame"].items():
            if not v["entity"].info["isBot"]:
                player_id = k
                is_player_win = True if v["totalGoldChange"] >= 2 else False
                self.set_base_player_challenge(k, is_player_win, v["entity"].control_pai_count)
                break

        # 计算玩家是否得奖
        winner_id = 0
        if is_player_win:
            winner_pirze = dict()
            winner_pirze["prize"] = prizeName
            winner_pirze["prizeType"] = prizeType
            winner_pirze["prizePrice"] = prizePrice
            self.set_base_player_prize(k, winner_pirze)
            winner_id = player_id

        player_settlement_info = []
        for k, v in chapter["playerInGame"].items():
            player_settlement_info.append(
                {"accountId": k, "totalGoldChange": v["totalGoldChange"], "name": v["entity"].info["name"],
                 "overBilling": v["overBilling"], "otherBilling": v["otherBilling"],
                 "winnerBilling": v["winnerBilling"], 'gold': v['gold'], 'prize': prizeName if k == winner_id else None,
                 "prizeType": prizeType if k == winner_id else -1})
        args = {"settlementInfo": player_settlement_info}
        self.callOtherClientsFunction("TotalSettlement", args)
        # 忽略判断，创建一个房间
        # self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info, 'ignoreJudge': True, 'onRoomEnd': True})
        # self.save_record_str()
        # 清理观战的玩家
        _playerOutGameCopy = chapter["playerOutGame"].copy()
        for k, v in _playerOutGameCopy.items():
            self.kick_out(k)
        # # 同步局数
        # if self.is_tea_house_room:
        #     self.set_base_player_chapter_count()

        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(settlement_clear_players_time, 0, 0)
        chapter["deadline"] = time.time() + settlement_clear_players_time

    def set_base_player_prize(self, account_dbId, winner_pirze):
        _chapter = self.chapters[self.cn]
        player = _chapter["playerInGame"][account_dbId]
        winner_pirze["challengeLevel"] = self.get_level()
        player["entity"].base.cellToBase({"func": "AddPrize", "dic": winner_pirze})

    # 1 发送在房间的当前座位位置
    def sendChapterState(self, accountEntityId):
        _chapter = self.chapters[self.cn]
        self.callClientFunction(accountEntityId, "ChapterState", {"state": _chapter["currentState"]})

    # 1 关闭所有的定时器
    def close_all_timer(self):
        chapter = self.chapters[self.cn]
        chapter["mainTimerId"] = -1
        self.delTimer(chapter["mainTimerId"])
        chapter["chapterStartTimerId"] = -1
        self.delTimer(chapter["chapterStartTimerId"])
        chapter["dealCardAnimationTimerId"] = -1
        self.delTimer(chapter["dealCardAnimationTimerId"])
        chapter["grabDealerTimer"] = -1
        self.delTimer(chapter["grabDealerTimer"])
        chapter["playCardTimer"] = -1
        self.delTimer(chapter["playCardTimer"])
        chapter["botCallDealerTimer"] = -1
        self.delTimer(chapter["botCallDealerTimer"])
        chapter['botGrabDealerTimer'] = -1
        self.delTimer(chapter['botGrabDealerTimer'])
        chapter["settlementTimer"] = -1
        self.delTimer(chapter["settlementTimer"])
        chapter["seatAnimationTimerId"] = -1
        self.delTimer(chapter["seatAnimationTimerId"])
        chapter["botPlayCardTimer"] = -1
        self.delTimer(chapter["botPlayCardTimer"])
        self.disband_timer = -1
        self.delTimer(self.disband_timer)

    def chapter_clear(self):
        """
        清理牌局信息
        :return:
        """
        _chapter = self.chapters[self.cn]
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
            v["grabResult"] = -1
            v["grabLandLord"] = -1
            v["callLandLord"] = -1
            v["cardType"] = -1
            v["stake"] = -1
            v["cardType"] = -1
            v["goldChange"] = 0
            v["identity"] = 0
            v["playCount"] = 0
        _playerInGameCopy = _newChapter["playerInGame"].copy()
        # 金币场最小入场金额  暂时没有这个需求
        min = 0
        if _chapter["level"] == 1:
            min = 1
        elif _chapter["level"] == 2:
            min = 301
        elif _chapter["level"] == 3:
            min = 1001
        elif _chapter["level"] == 4:
            min = 5001
        elif _chapter["level"] == 5:
            min = 20001

    def write_chapter_info_to_db(self):
        """
        牌局信息写入库
        :return:
        """

        # 至少打一局才写入库中
        if self.settlement_count < 1:
            return
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        _playerData = {}
        _playerInfo = []
        _history_record = {}
        # 牌局的回放
        chapter_replays = {}
        # 存储回放数据
        replay_data = {"chapterInfo": {}}
        # 判断如果最后一局未到结算状态，不计入战绩
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        # 1 循环所有局数
        for c in range(0, chapter_record_max_count):
            chapter_info = self.chapters[c]
            chapter_players_data = []
            # 循环牌局中的玩家信息
            for k, v in chapter_info["playerInGame"].items():
                _playerData = {"accountId": k, "name": v["entity"].info["name"],
                               "goldChange": v["goldChange"], "userId": v["entity"].info["userId"],
                               "identity": v["identity"], "locationIndex": int(v["locationIndex"]),
                               "databaseId": v["entity"].info["dataBaseId"], "gold": v["gold"]
                               }
                # 存储玩家信息  base端的显示的总战绩
                chapter_players_data.append(_playerData)
            # 1  存放所有的牌局数据
            _history_record[c] = chapter_players_data
            _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                     "maxChapterCount": self.info["maxChapterCount"],
                     "playerInfo": chapter_players_data, "historyRecord": _history_record
                     }

            # 存储每局的步骤信息和玩家信息
            chapter_replay = chapter_info["operationRecord"]
            chapter_replays[c] = {"playerInfo": chapter_players_data, "operationReplay": chapter_replay}

        # 存储房间信息以及步骤信息
        replay_data["chapterInfo"] = chapter_replays
        # 记录战绩的玩家
        record_players = []
        for k, v in _playerInGame.items():
            _playerData = {"accountId": k, "accountName": v["entity"].info["name"], "winnerBilling": v["winnerBilling"],
                           "overBilling": v["overBilling"],
                           "otherBilling": v["otherBilling"], "totalGoldChange":
                               v["totalGoldChange"], "userId": v["entity"].info["userId"]}
            # 1 玩家数据
            _playerInfo.append(_playerData)
            record_players.append(v['entity'].info['userId'])

        challenge_control = dict()
        if self.info["roomType"] == "challenge":
            true_player = self.get_true_player()
            challenge_control["winPercent"] = true_player['entity'].get_control_percent()
            challenge_control["winControl"] = true_player['entity'].get_win_control()
            challenge_control["luckUser"] = self.luck_user

        _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                 "maxChapterCount": self.info["maxChapterCount"], "challengeControl": challenge_control,
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

    def _onLeave(self, account_entity_id, leave_param=None):
        """
        离开房间实现过程
        :param account_entity_id:
        :return:
        """
        player_online = True
        DEBUG_MSG('[Room id %i]------>onLeave accountId %s, emptyLocationIndex %s' % (
            self.id, account_entity_id, self.emptyLocationIndex))
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _currentState = _chapter["currentState"]
        if account_entity_id in _playerInGame:
            # 1 判断游戏是否处于刚开始阶段 不是结算  也不是总结算
            if _currentState != 0 and _currentState != 5:
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
                self.retOutGamePlayerInfo(k)
            # 给观战玩家发送观战玩家信息
            for k, v in _chapter["playerOutGame"].items():
                self.retOutGamePlayerInfo(k)
            self.ret_player_in_room_info()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_playerInGame)})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})

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
            self.ret_player_in_room_info()
            DEBUG_MSG('[Room]------>onLeave len(_playerInGame) %s' % (
                len(_playerInGame)))
            self.base.cellToBase({"func": "playersCount", "count": len(_playerInGame)})
            self.base.cellToBase({"func": "seatPlayersCount", "count": len(_chapter["playerInGame"])})
        # 从实体列表中移除
        if account_entity_id in self.accountEntities.keys():
            self.accountEntities.pop(account_entity_id)
            self.base.cellToBase({"func": "LogoutRoom", "accountId": account_entity_id})

        self.notify_viewing_hall_players_room_info()

    def onLeave(self, account_entity_id, leave_param=None):
        """
        离开房间
        :param account_entity_id:
        :return:
        """
        self._onLeave(account_entity_id, leave_param)
        self.autoDestroy()

    def player_delegate(self, account_entity_id):
        """托管账号"""
        _chapter = self.chapters[self.cn]
        _playerInGame = _chapter["playerInGame"]
        if account_entity_id in _playerInGame:
            _player = _playerInGame[account_entity_id]
            _player["delegate_play_card"] = True
        self.callClientFunction(account_entity_id, "ChallengeLeaveRoom", {})

    def challenge_continue(self, account_entity_id):
        """继续挑战"""
        self._onLeave(account_entity_id, None)
        _chapter = self.chapters[self.cn]
        self.base.cellToBase(
            {"func": "continueNextChallenge", "challengeLevel": self.get_level(), "accountId": account_entity_id})
        self.autoDestroy()

    #
    def retOutGamePlayerInfo(self, accountId=-1):
        _chapter = self.chapters[self.cn]
        _playerOutGameNotEntity = {}
        for k, v in _chapter["playerOutGame"].items():
            _player = {"cards": self.parse_card_to_client(v["cards"]),
                       "playedCards": self.parse_card_to_client(v["playedCards"]),
                       "gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       "name": v["entity"].info["name"], "headImageUrl": v["entity"].info["headImageUrl"],
                       "addOn": v["entity"].info["addOn"],
                       "ready": v["ready"]}
            _playerOutGameNotEntity[int(k)] = _player
        _args = {"playerOutGame": _playerOutGameNotEntity}
        self.debug_msg('retOutGamePlayerInfo %s' % _args)
        if accountId == -1:
            self.callOtherClientsFunction("RetOutGamePlayerInfo", _args)
        else:
            self.callClientFunction(accountId, "RetOutGamePlayerInfo", _args)

    def onPlayerClientDeath(self, accountEntity):
        DEBUG_MSG("RoomType8 onPlayerClientDeath accountId:%s" % accountEntity)
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
            for k, v in copy.deepcopy(chapter["playerInGame"]).items():
                self.kick_out(k, player_online=False)

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

    def parse_card_to_client(self, cards):
        if len(cards) == 0:
            return []
        card_nums = []
        for card in cards:
            card_type = -1
            # 黑红梅方
            # a b c d
            if card.startswith('a'):
                card_type = 1
            elif card.startswith('b'):
                card_type = 2
            elif card.startswith('c'):
                card_type = 3
            elif card.startswith('d'):
                card_type = 0

            if card_type != -1:
                card_value = int(re.sub('[a-z]', '', card))
                card_num = (card_value - 3) * 4 + card_type
                card_nums.append(card_num)
            else:
                if int(card) == 16:
                    card_nums.append(52)
                if int(card) == 17:
                    card_nums.append(53)
        return card_nums

    # 转为服务端牌值
    def parse_card_to_server(self, cards):
        if len(cards) == 0:
            return []
        card_nums = []
        for card in cards:
            card_type = card % 4
            card_value = int(card / 4) + 3
            card_color = ''
            if card_type == 0:
                card_color = 'd'
            elif card_type == 1:
                card_color = 'a'
            elif card_type == 2:
                card_color = 'b'
            elif card_type == 3:
                card_color = 'c'

            if card == 52:
                card_nums.append(str(16))
            elif card == 53:
                card_nums.append(str(17))
            else:
                card_nums.append(str(card_color) + str(card_value))

        return card_nums

    # 斗地主表情
    def Send_emotion(self, account_id, index):
        """
        表情聊天
        :param emotion_type:
        :param account_id:
        :param index:
        :return:
        """
        _args = {"accountId": account_id, "index": index}
        self.callOtherClientsFunction("SendEmotion", _args)

    # 1 分享到微信   邀请
    def share_to_wx(self, account_id):
        if self.info['roomType'] == 'card':
            title = '斗地主房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '斗地主房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '斗地主房间'
        max_chapter_count = '最大局数：' + str(self.info['maxChapterCount'])
        base_score = '底分' + str(self.info['baseScore'])
        land_lord_game_type = '玩法:' + '叫分' if self.info['LandlordGameType'] == 0 else '抢地主'
        if 'canVoice' in self.info:
            can_voice = '语音开启' if self.info['canVoice'] else '禁用语音'
        else:
            can_voice = ''
        con = str('%s,%s,%s,%s' % (max_chapter_count, base_score, land_lord_game_type, can_voice))
        self.callClientFunction(account_id, 'ShareToWX', {'title': title, 'content': con})

    # 快捷语广播
    def send_common_chat(self, accountEntityId, index):
        args = {"accountId": accountEntityId, "index": index}
        self.callOtherClientsFunction("SendCommonChat", args)

    def send_chat(self, accountEntityId, content):
        chapter = self.chapters[self.cn]
        player_chat_data = {accountEntityId: content}
        if len(chapter["chatHistory"]) > 10:
            del chapter["chatHistory"][0]
        chapter["chatHistory"].append(player_chat_data)
        args = {"accountId": accountEntityId, "content": content}
        self.callOtherClientsFunction("SendChat", args)

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

    # 重连时发送当前牌桌信息
    def ret_chapter_info(self, account_id):
        chapter = self.chapters[self.cn]
        play_in_game = chapter["playerInGame"]
        chapter_info = {}
        chapter_info["currentRound"] = int(chapter["currentRound"])
        chapter_info["currentState"] = int(chapter["currentState"])
        chapter_info["deadline"] = int(chapter["deadline"]) - int(time.time())
        chapter_info["deadline"] = 0 if chapter_info["deadline"] < 0 else chapter_info["deadline"]
        chapter_info["dealer"] = int(chapter["dealer"])
        chapter_info["coverCards"] = self.parse_card_to_client(chapter["coverCards"])
        chapter_info["prePlayer"] = int(chapter["prePlayer"])
        chapter_info["prePlayerPlayCards"] = self.parse_card_to_client(chapter["prePlayerPlayCards"])
        chapter_info["SiDaiEr"] = self.info["SiDaiEr"]
        chapter_info["prePlayerPlayCardsType"] = RoomType6Calculator.play_card_correct(
            chapter["prePlayerPlayCards"], self.info["SiDaiEr"]).value
        chapter_info["baseScore"] = int(self.info["baseScore"])
        chapter_info["bombCaps"] = int(self.info["bombCaps"])
        chapter_info["multiple"] = int(chapter["multiple"])
        chapter_info["currentPlayer"] = int(chapter["currentPlayer"])
        chapter_info["started"] = self.info["started"]
        chapter_info["doubleKingGrab"] = self.info["doubleKingGrab"]
        chapter_info["canVoice"] = self.info["canVoice"]
        chapter_info["clcCardSwitch"] = self.info["clcCardSwitch"]
        chapter_info["LandlordGameType"] = self.info["LandlordGameType"]
        chapter_info["canCallLandLordPlayers"] = chapter["canCallLandLordPlayers"]
        chapter_info["canGrabLandLordPlayers"] = chapter["canGrabLandLordPlayers"]
        chapter_info["disbandSender"] = self.disband_sender
        chapter_info["isDisbanding"] = self.is_disbanding
        _playerData = {}
        for k, v in play_in_game.items():
            _playerData[k] = {"goldChange": v["goldChange"], "cards": self.parse_card_to_client(v["cards"]),
                              "identity": v["identity"],
                              "grabResult": v["grabResult"],
                              "name": v["entity"].info["name"],
                              "totalGoldChange": v["totalGoldChange"],
                              "ready": v["ready"],
                              "callLandLord": v["callLandLord"],
                              "grabLandLord": v["grabLandLord"],
                              "agreeDisband": v["agreeDisband"]
                              }
        chapter_info["playerData"] = _playerData

        # 加密其他人的牌

        self.callClientFunction(account_id, "Reconnect", chapter_info)

    # 换桌
    def change_table(self, account_id):
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _playerInGame = _chapter["playerInGame"]
        _playerOutGame = _chapter["playerOutGame"]
        _currentState = _chapter["currentState"]
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
            {"func": "changeTable", "accountId": account_id, "type": self.info["type"], "level": self.get_level()})

    def get_a_bot(self, accountId):
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if v["entity"].info["isBot"] == 1 and k == accountId:
                return k

    # 机器人出牌
    def bot_play_card(self):
        chapter = self.chapters[self.cn]
        bot = self.get_a_bot(chapter["currentPlayer"])
        if bot is None:
            return
        true_player = self.get_true_player()
        control_count = 0
        if true_player:
            control_count = true_player['entity'].get_challenge_control(self.cn)
            # 换牌
            if true_player['entity'].get_control_percent() > 20:
                R6AM.exchange_cards(chapter, bot, control_count)

        cards = R6AM.bot_play_card_ai(chapter, bot, control_count)
        DEBUG_MSG("[Room6]::bot_play_card::cards:%s" % cards)
        convert_client_cards = self.parse_card_to_client(cards)
        self.player_play_cards(bot, convert_client_cards)

    # 1 机器人准备
    def bots_ready(self):
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if v["entity"].info["isBot"] == 1:
                self.player_ready(k)

    def bot_call_dealer(self, accountId):
        """
        机器人叫分
        :param accountId:
        :return:
        """
        max_result = 0
        chapter = self.chapters[self.cn]
        for k, v in chapter["playerInGame"].items():
            if v["grabResult"] > max_result:
                max_result = v["grabResult"]
        self.call_dealer(accountId, random.randint(max_result + 1, 3))

    def bot_grab_dealer(self, accountId, operation_type):
        """
        机器人抢地主
        :param accountId:
        :return:
        """
        result = 0
        if operation_type == 0:
            # 如果当前为叫地主模式，随机值为1、2
            result = random.randint(1, 2)
        elif operation_type == 1:
            # 如果当前为叫地主模式，随机值为3,4
            result = random.randint(3, 4)
        self.grab_dealer(accountId, result)

    def get_true_player(self):
        """
        获得一个真实玩家
        :return:
        """
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['entity'].info['isBot'] == 0:
                return v

    def tea_house_disband_room_by_creator(self):
        """
        群主解散房间
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

        if self.chapters[self.cn]["currentState"] != 5:
            self.total_settlement()
            self.write_chapter_info_to_db()

    def get_distance_relation(self, account_id):
        """
        获取玩家之间的距离
        :param account_id:
        :return:
        """
        _chapter = self.chapters[self.cn]
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

    def is_offline(self, account_id):
        """
        玩家是否离线
        :return:
        """
        chapter = self.get_current_chapter()
        for k, v in chapter["playerInGame"].items():
            if k == account_id:
                if v['entity'].client_death:
                    return True
                else:
                    return False

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

    def set_losing_streak_history(self, _player, is_loser):
        """
        设置玩家全局输赢数据
        :param _player:
        :param is_loser:
        :return:
        """
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

    def get_farmer(self):
        chapter = self.chapters[self.cn]
        farmer = []
        for k, v in chapter['playerInGame'].items():
            if v['identity'] == 0:
                farmer.append(v)
        return farmer

    def save_record_str(self):
        game_type = '斗地主'
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

    def baseToCell(self, pyDic):
        """
        :param pyDic:
        :return:
        """
        _func_name = pyDic["func"]
        DEBUG_MSG("[baseToCell] RoomType6 _func_name %s" % _func_name)
        if _func_name == "RollNoticeInRoom":
            self.callOtherClientsFunction("RollNoticeInRoom", pyDic["content"])

        RoomBase.baseToCell(self, pyDic)

    def is_challenge_room(self):
        """
        判断此房间是否是金币场房间
        :return:
        """
        return True if self.info["roomType"] == "challenge" else False

    def autoDestroy(self):
        """
        自动销毁房间
        :return:
        """
        chapter = self.chapters[self.cn]
        # 如果坐下玩家不存在真实玩家则自动解散
        for k, v in chapter['playerInGame'].items():
            if v["entity"].info["isBot"] == 0:
                return

        if self.is_challenge_room():
            self.destroySpace()
        else:
            RoomBase.autoDestroy(self)

    def get_level(self):
        _chapter = self.chapters[self.cn]
        return _chapter["level"]

    def is_forbid_disband_room(self):
        """
        禁止中途解散房间
        """
        return self.info["canNotDisbandOnPlay"]
