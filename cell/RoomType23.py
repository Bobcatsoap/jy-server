# -*- coding: utf-8 -*-
import copy
from random import shuffle

import KBEngine

import Const
from KBEDebug import *

import RoomType23Calculator
from RoomBase import *
import json
import time
import datetime
import NiuNiuCalculator
import Account

# 准备倒计时时间
ready_time = 5

# 发牌动画时间
deal_card_to_player_time = 3

# 抢庄时间
grab_banker_time = 10

# 要牌时间
get_card_time = 10

# 押注倒计时时间
stake_time = 20

# 结算时间
settlement_time = 6

# 解散房间倒计时
time_disband = 30

# 总结算清理玩家倒计时
settlement_clear_players_time = 30


class RoomType23(RoomBase):
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
        # 剩余牌
        _chapter['remainCards'] = []
        # 房间总注
        _chapter["totalStake"] = 0
        # 解散清除玩家倒计时
        _chapter["settlementClearPlayers"] = -1
        # 轮询是否可以开始牌局计时器
        _chapter["mainTimerId"] = -1
        # 牌局开始倒计时计时器
        _chapter["chapterStartTimerId"] = 0
        # 发牌计时器
        _chapter["dealCardAnimationTimerId"] = -1
        # 要牌计时器
        _chapter["getCardTimer"] = -1
        # 结算计时器
        _chapter["settlementTimer"] = -1
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
        # 庄家 id
        _chapter["banker"] = -1
        # 牌局历史
        _chapter["chapterHistory"] = {}
        # 开始玩家下标
        _chapter["startLocationIndex"] = -1
        # 开始玩家Id
        _chapter["startAccountId"] = -1
        # 当前操作玩家
        _chapter["currentPlayer"] = -1
        # 胜者
        _chapter["winner"] = -1
        # 倍数
        _chapter["multiple"] = 1
        # 抽奖
        _chapter["accountLottery"] = -1
        # 聊天记录
        _chapter["chatHistory"] = []
        # 战绩
        _chapter["roomRecord"] = {}
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
        # 下注
        _player['stake'] = 0
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
            # 比赛分场修改使用比赛分为使用金币
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        elif self.info["roomType"] in ['normalGameCoin', 'card', 'gold', 'challenge']:
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 1 同意解散
        _player["agreeDisband"] = False
        # 出牌次数
        _player["playCount"] = 0
        # 身份 无：-1，闲家：0，庄家：1
        _player["identity"] = 0
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
                       "gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       'stake': v['stake'],
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
                       "gold": v["gold"], "locationIndex": int(v["locationIndex"]),
                       "userId": v["entity"].info["userId"],
                       'stake': v['stake'],
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
        if _func == "GrabBanker":
            pass
        elif _func == "LeaveRoom":
            self.onLeave(account_entity_id, _data)
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
        # 1 十点半表情
        elif _func == "SendEmotion":
            self.Send_emotion(account_entity_id, _data["index"])
        elif _func == "SendChat":
            self.send_chat(account_entity_id, _data["content"])
        # 1 快捷语广播
        elif _func == "SendCommonChat":
            self.send_common_chat(account_entity_id, _data["index"])
        elif _func == "Reconnect":
            self.reconnect(account_entity_id)
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

    def player_ready(self, account_id, ready=True):
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
                _player['gold'] < self.info['roomRate'] and ready:
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
        _args = {"Timer": ready_time}
        self.callOtherClientsFunction("ChapterReady", _args)
        _chapter["chapterStartTimerId"] = self.addTimer(ready_time, 0, 0)
        _chapter["deadline"] = time.time() + ready_time

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

        self.changeChapterState(1)
        self.set_current_round(self.cn + 1)
        self.deal_cards()
        self.base.cellToBase({"func": "changeRoomState", "roomState": 1})
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

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

        # 获取生成的手牌
        all_cards, remain_cards = RoomType23Calculator.generate_cards(len(_player_in_game))
        # 打印生成出来的牌
        self.debug_msg("all_cards:%s,remain_cards%s" % (all_cards, remain_cards))

        # 剩余牌赋值
        _chapter['remainCards'] = remain_cards

        # 玩家手牌赋值
        player_cards_data = []
        dic_index = 0
        for k in _player_in_game:
            cards = all_cards[dic_index]
            _player_in_game[k]["cards"] = cards
            dic_index += 1

        # 转化为客户端牌值
        for k in _player_in_game:
            cards = _player_in_game[k]["cards"]
            # 转化为客户端牌值
            client_cards = self.parse_card_to_client(cards)
            player_cards_data.append({"accountId": int(k), "cards": client_cards})

        # 转化为客户端牌值
        all_cards_data = {"playerCards": player_cards_data}
        # 记录发牌
        record = {}
        # 出牌相关置为 0
        record["operationType"] = 0
        # 操作  存储玩家的牌和底牌
        record["operationArgs"] = {"playerCards": player_cards_data}
        # 将发牌相关数据存到操作回放流程里
        _chapter["operationRecord"].append(record)
        self.send_cards_info_with_encryption(all_cards_data)
        _chapter["dealCardAnimationTimerId"] = self.addTimer(deal_card_to_player_time, 0, 0)
        _chapter["deadline"] = time.time() + deal_card_to_player_time

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
        elif timer_handle == _chapter["settlementTimer"]:
            # 下局开始计时器
            DEBUG_MSG('[Room id %s]------>onTimer settlementTimer %s' % (self.id, timer_handle))
            self.delTimer(timer_handle)
            _chapter["settlementTimer"] = -1
            # 如果时间到了就不开始
            DEBUG_MSG(
                '[Room id %s]------>onTimer cn+1 %s,maxChapterCount %s' % (
                    self.id, self.cn + 1, self.info["maxChapterCount"]))

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

            # 第二局开始自动准备
            # if self.cn > 0:
            #    for k, v in _chapter["playerInGame"].items():
            #        if v["entity"].info["isBot"] == 0:
            #            self.player_ready(k)

            # _chapter["mainTimerId"] = self.addTimer(1, 0.2, 0)

        elif state == 1:
            # 牌局开始、发牌
            _args = {"state": state, "Timer": deal_card_to_player_time}
            self.callOtherClientsFunction("changeChapterState", _args)
        elif state == 2:
            #
            _args = {"state": state}
            self.callOtherClientsFunction("changeChapterState", _args)
            random_index = 0


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
        elif state == 4:
            # 结算
            _args = {"state": state, "Timer": settlement_time}
            self.callOtherClientsFunction("changeChapterState", _args)
            self.settlement()
            for k, v in _chapter["playerInGame"].items():
                self.player_ready(k, False)

        elif state == 5:
            # 总结算
            # 关闭所有计时器
            _args = {"state": state, "Timer": 0}
            self.callOtherClientsFunction("changeChapterState", _args)

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
                if self.info['timeDown'] > 0:
                    # if chapter["playerInGame"][account_id]["entity"].info["isBot"] == 1:
                    #     play_card_timer = random.randint(bot_play_card_time_min, bot_play_card_time_max)
                    #     # 添加机器人叫地主计时器
                    #     chapter["botPlayCardTimer"] = self.addTimer(play_card_timer, 0, 0)
                    # else:
                    #     # 玩家在线时出牌计时器
                    #     chapter["playCardTimer"] = self.addTimer(self.info['timeDown'], 0, 0)
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
        pass
        # """
        # 该方法实现出牌大小判断及是否广播
        # :param account_id:
        # :param client_cards:
        # :return:
        # """
        # DEBUG_MSG('[player_play_cards] cards is %s' % client_cards)
        # chapter = self.chapters[self.cn]
        # # 只有出牌阶段可以出牌
        # if chapter['currentState'] != 3:
        #     self.debug_msg("player_play_cards is not state 3")
        #     return
        #
        # server_cards = self.parse_card_to_server(client_cards)
        # server_cards_type = RoomType6Calculator.play_card_correct(server_cards, self.info["SiDaiEr"])
        # # 如果当前操作玩家不是自己，出牌失败
        # if chapter["playerInGame"][account_id]["locationIndex"] != chapter["currentLocationIndex"]:
        #     self.send_player_cards(account_id, -1, client_cards, server_cards_type)
        #     return
        #
        # # -1：出牌失败、不符合规则，0：不出，1：出牌成功
        # # 出牌数是零，不出牌
        # if len(client_cards) == 0:
        #     # 如果上个出牌人是自己或没有出牌人，不出失败
        #     if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
        #         self.send_player_cards(account_id, -1, client_cards, RoomType6Calculator.CardType.invalid)
        #     else:
        #         self.send_player_cards(account_id, 0, client_cards, RoomType6Calculator.CardType.invalid)
        #     return
        #
        # # self.info["SiDaiEr"] = self.info["SiDaiEr"] or False
        # # 如果不符合基本规则，出牌失败
        # if server_cards_type == RoomType6Calculator.CardType.invalid:
        #     self.send_player_cards(account_id, -1, client_cards, server_cards_type)
        #     return
        #
        # # 如果手中没有此牌出牌失败
        # for s_card in server_cards:
        #     if s_card not in chapter["playerInGame"][account_id]["cards"]:
        #         self.send_player_cards(account_id, -1, client_cards, server_cards_type)
        #         return
        #
        # # 如果上个出牌人是自己或没有出牌人，出牌成功
        # if chapter["prePlayer"] == -1 or chapter["prePlayer"] == account_id:
        #     self.send_player_cards(account_id, 1, client_cards, server_cards_type)
        # # 如果之前有别人出牌
        # else:
        #     # 如果比之前出牌大，出牌成功；否则失败
        #     if self.play_card_compare(server_cards, chapter["prePlayerPlayCards"]):
        #         self.send_player_cards(account_id, 1, client_cards, server_cards_type)
        #     else:
        #         self.send_player_cards(account_id, -1, client_cards, server_cards_type)

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
        pass
        # chapter = self.chapters[self.cn]
        # # 1 底分*倍数
        # settlement_gold = self.info["baseScore"] * chapter["multiple"]
        # dealer = chapter["playerInGame"][chapter["dealer"]]
        # # 玩家可以输的钱的上限
        # lose_limit = 100
        # # 如果没开启比赛币
        # if not self.have_gold_limit:
        #     lose_limit = sys.maxsize
        # farmers_id = []
        # farmers = []
        # # winner = []
        # # 0 农民，1 地主
        # # winner_identity = -1
        # # args = {}
        # gold_change = {}
        # total_gold_change = {}
        # remain_cards = {}
        # # 1 牌型是否是春天
        # spring = False
        # # 后台抽成比例
        # proportion = self.cutRatio
        # playerInGame = chapter["playerInGame"]
        # # 1 循环判断游戏内玩家的身份
        # for k, v in playerInGame.items():
        #     if v["identity"] == 0:
        #         farmers.append(v)
        #         farmers_id.append(k)
        # # 地主获胜
        # # 1 判断房间赢者是地主
        # if chapter["winner"] == chapter["dealer"]:
        #     # 判断地主是否春天
        #     if len(farmers[0]["cards"]) == len(farmers[1]["cards"]) == 17:
        #         spring = True
        #     if spring:
        #         settlement_gold *= spring_multiple
        #         chapter["multiple"] *= spring_multiple
        #     farmers1_lose = settlement_gold
        #     farmers2_lose = settlement_gold
        #     # 1 判断农民1 的金币数小于要扣的时候
        #     if farmers[0]["gold"] + lose_limit < settlement_gold:
        #         # 1 把农民的钱全部给地主
        #         farmers1_lose = farmers[0]["gold"] + lose_limit
        #     if farmers[1]["gold"] + lose_limit < settlement_gold:
        #         farmers2_lose = farmers[1]["gold"] + lose_limit
        #     farmers[0]["goldChange"] = -farmers1_lose
        #     farmers[1]["goldChange"] = -farmers2_lose
        #     farmers[0]["gold"] += farmers[0]["goldChange"]
        #     farmers[1]["gold"] += farmers[1]["goldChange"]
        #     # 设置金币总改变
        #     farmers[0]["totalGoldChange"] += farmers[0]["goldChange"]
        #     farmers[1]["totalGoldChange"] += farmers[1]["goldChange"]
        #     dealer["goldChange"] = (farmers1_lose + farmers2_lose) * (1 - proportion)
        #     dealer["gold"] += dealer["goldChange"]
        #     dealer["totalGoldChange"] += dealer["goldChange"]
        #     winner = [chapter["dealer"]]
        #     winner_identity = 1
        # #  1 如果是农民赢
        # else:
        #     if chapter["playerInGame"][chapter["dealer"]]["playCount"] == 1:
        #         spring = True
        #     if spring:
        #         settlement_gold *= spring_multiple
        #         chapter["multiple"] *= spring_multiple
        #     # 1 赢的钱为计算的结果  因为钻石场是根据分来计算
        #     farmers1_win = settlement_gold
        #     farmers2_win = settlement_gold
        #     if dealer["gold"] + lose_limit < farmers1_win + farmers2_win:
        #         farmers1_win = dealer["gold"] / 2 + lose_limit / 2
        #         farmers2_win = dealer["gold"] / 2 + lose_limit / 2
        #     farmers[0]["goldChange"] = farmers1_win * (1 - proportion)
        #     farmers[1]["goldChange"] = farmers2_win * (1 - proportion)
        #     farmers[0]["gold"] += farmers[0]["goldChange"]
        #     farmers[1]["gold"] += farmers[1]["goldChange"]
        #     farmers[0]["totalGoldChange"] += farmers[0]["goldChange"]
        #     farmers[1]["totalGoldChange"] += farmers[1]["goldChange"]
        #
        #     dealer["goldChange"] = -(farmers1_win + farmers2_win)
        #     dealer["gold"] += dealer["goldChange"]
        #     dealer["totalGoldChange"] += dealer["goldChange"]
        #     winner = [farmers_id[0], farmers_id[1]]
        #     winner_identity = 0
        # for k, v in playerInGame.items():
        #     # 获得金币改变数据
        #     gold_change[k] = v["goldChange"]
        #     total_gold_change[k] = v['totalGoldChange']
        #     # 剩余手牌
        #     remain_cards[k] = self.parse_card_to_client(v["cards"])
        #     # 修改玩家房间内积分
        #     self.ret_account_score(k, v["gold"])
        #     # 修改玩家金币
        #     if self.info["roomType"] == "gameCoin":
        #         self.set_base_player_game_coin(k)
        #     else:
        #         self.set_base_player_gold(k)
        #     # 更新分数控制
        #     v["entity"].update_score_control(v['goldChange'])
        #
        # # 统计输牌玩家,计入连输统计
        # for k, v in playerInGame.items():
        #     is_lose = False
        #     if v['goldChange'] < 0:
        #         is_lose = True
        #     elif v['goldChange'] == 0:
        #         continue
        #     self.set_losing_streak_history(v, is_lose)
        #
        # _args = {"winner": winner, "timer": settlement_time, "goldChange": gold_change, "remainCards": remain_cards,
        #          'totalGoldChange': total_gold_change,
        #          "spring": spring, 'multiple': chapter["multiple"]}
        # self.callOtherClientsFunction("Settlement", _args)
        #
        # player_record = {}
        # for k, v in playerInGame.items():
        #     record = {"preGoldChange": v["goldChange"], "totalGoldChange": v["totalGoldChange"],
        #               "name": v["entity"].info["name"]}
        #     player_record[k] = record
        # chapter["roomRecord"] = player_record
        # # 清理、下局开始倒计时
        # chapter["settlementTimer"] = self.addTimer(settlement_time, 0, 0)
        # chapter["deadline"] = time.time() + settlement_time
        # self.settlement_count += 1
        # if self.settlement_count == 1:
        #     self.base.cellToBase({'func': 'addTodayRoom'})
        # # 1 通知base端是AA支付扣除钻石扣除钻石
        # if self.info['payType'] == Const.PayType.AA:
        #     need_consume = []
        #     # 1 循环判断在游戏中还没被收取钻石
        #     for k, v in chapter["playerInGame"].items():
        #         if not v["AARoomCardConsumed"]:
        #             v['AARoomCardConsumed'] = True
        #             need_consume.append(v["entity"].info["userId"])
        #             # 1 通知base端扣除钻石
        #     if len(need_consume) != 0:
        #         self.base.cellToBase({"func": "AAPayTypeModifyRoomCard", "needConsumePlayers": need_consume})

    def total_settlement(self):
        if self.total_settlement_ed:
            return
        # 1 关闭所有定时器
        self.close_all_timer()
        # 1 更改房间状态
        self.changeChapterState(5)
        # 1 设置总结算为True
        self.total_settlement_ed = True
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
                 "headImageUrl": v["entity"].info["headImageUrl"],
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

        chapter["settlementTimer"] = -1
        self.delTimer(chapter["settlementTimer"])
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
            v["ready"] = False
            v["grabResult"] = -1
            v["cardType"] = -1
            v["stake"] = 0
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
                               v["totalGoldChange"], "userId": v["entity"].info["userId"],
                           "headImageUrl": v["entity"].info["headImageUrl"]}
            # 1 玩家数据
            _playerInfo.append(_playerData)
            record_players.append(v['entity'].info['userId'])

        challenge_control = dict()

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

    #
    def retOutGamePlayerInfo(self, accountId=-1):
        _chapter = self.chapters[self.cn]
        _playerOutGameNotEntity = {}
        for k, v in _chapter["playerOutGame"].items():
            _player = {"cards": self.parse_card_to_client(v["cards"]),
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

    # 十点半表情
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
            title = '十点半房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '十点半房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '十点半房间'
        max_chapter_count = '最大局数：' + str(self.info['maxChapterCount'])
        base_score = '底分' + str(self.info['baseScore'])
        if 'canVoice' in self.info:
            can_voice = '语音开启' if self.info['canVoice'] else '禁用语音'
        else:
            can_voice = ''
        con = str('%s,%s,%s' % (max_chapter_count, base_score, can_voice))
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
        chapter_info["banker"] = int(chapter["banker"])
        chapter_info["multiple"] = int(chapter["multiple"])
        chapter_info["currentPlayer"] = int(chapter["currentPlayer"])
        chapter_info["started"] = self.info["started"]
        chapter_info["canVoice"] = self.info["canVoice"]
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
                              "agreeDisband": v["agreeDisband"]
                              }
        chapter_info["playerData"] = _playerData
        # 加密其他人的牌
        self.callClientFunction(account_id, "Reconnect", chapter_info)

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

    def baseToCell(self, pyDic):
        """
        :param pyDic:
        :return:
        """
        _func_name = pyDic["func"]
        DEBUG_MSG("[baseToCell] RoomType23 _func_name %s" % _func_name)
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
