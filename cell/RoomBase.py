# -*- coding: utf-8 -*-
import time

import KBEngine

import Const
import Util
from KBEDebug import *
import random
import json
import Account

join_bots_time = 10
time_disband = 30
bot_disband_time_max = 10
PLAYER_IN_GAME = "players"
# 观战玩家
PLAYER_OUT_GAME = 'playerOutGame'


class RoomBase(KBEngine.Entity):
    """
    Room实体的cell部分
    """
    gold_name = ''
    is_tea_house_room = False
    # 1 是否开始标志位
    started = False
    # 1 结算次数
    settlement_count = 0
    # 1 创建者解散
    disband_from_creator = False
    # 1 是否正常解散
    is_manual_disband = False
    # 1 总结算标志位
    total_settlement_ed = False

    # 解散计时器
    disband_timer = -1
    # 正在解散状态
    is_disbanding = False
    # 解散发起者
    disband_sender = -1

    # 没钱解散倒计时
    ready_gold_disband_timer = -1

    #
    gifts = []

    # 战绩字符串
    record_str = ''

    # 服务端配置
    server_config = {}

    # base发给cell的房间所在茶楼配置
    lucky_card_switch = False
    game_coin_switch = False

    # 同意少人模式的玩家
    agree_less_person_mode_players = []

    # 同意少人模式
    def __init__(self):
        KBEngine.Entity.__init__(self)
        # 房间所有用户实体
        self.accountEntities = {}
        # 牌局信息
        self.chapters = []
        # 当前局数下标
        self.cn = 0
        # 房间属性信息 在initRoom中从base获取信息
        self.info = None
        # 全局统计数据
        self.statisticalData = None
        # 抽成比例
        self.cutRatio = 0
        self.chapter_replay = {}
        # 房费
        self.roomRate = -1
        self.chapterInfo = {}
        self.record_str = ''
        self.total_settlement_ed = False
        self.agree_less_person_mode_players = []
        # self.gifts = Const.ServerGameConfigJson.config_json["Lottery"]["giftList"]

    # --------------------------------------------------------------------------------------------
    #                              牌局主要逻辑实现
    # --------------------------------------------------------------------------------------------
    def newChapter(self, maxPlayerCount):
        """
        创建牌局
        :param maxPlayerCount:最大人数
        :return:
        """
        _empty_location = list(range(1, maxPlayerCount + 1))
        chapter = {
            # 所有玩家
            "players": {},
            # 最大玩家数
            "maxPlayerCount": maxPlayerCount,
            # 当前玩家数
            "playersCount": 0,
            # 庄家位置
            "bankerLocation": 0,
            # 所有空座
            "emptyLocation": _empty_location,
            # 当前牌库
            "cardsLib": None,
            # 当前牌局阶段
            "chapterState": -1,
        }
        if len(self.chapters) > 30:
            self.chapters = []
            self.cn = 0
        self.chapters.append(chapter)
        self.cn = len(self.chapters) - 1
        DEBUG_MSG('[Room id %s] newChapter %s maxPlayerCount %s' % (self.info['roomId'], self.cn, maxPlayerCount))
        return chapter

    def newPlayer(self, accountEntity):
        """
        添加本局玩家，并分配位置
        :param accountEntity:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _empty_location = _chapter["emptyLocation"]
        _players = _chapter["players"]
        # 没有空位 结束方法 对于要有观战的游戏可以把此玩家添加到观战表中
        if len(_empty_location) == 0:
            return
        # 此用户如果已在牌局内 结束方法
        for i in _players.values():
            if i["entity"].id == accountEntity.id:
                return None
        # 创建牌局玩家 并分配一个座位
        _locationIndex = _empty_location[0]
        # 玩家牌局中的初始金币数 默认为玩家账户中的总金币数
        _gold = 0
        if self.info["roomType"] == "card":
            _gold = 0
        elif self.info["roomType"] == "gameCoin":
            _gold = accountEntity.accountMutableInfo["gameCoin"]
        _player = {
            # 玩家位置
            "locationIndex": _locationIndex,
            # 玩家entity
            "entity": accountEntity,
            # 玩家金币数
            "gold": _gold,
            # 玩家准备状态
            "isReady": False,
            # 玩家手牌
            "cards": [],
        }
        _empty_location.pop(0)
        _players[_locationIndex] = _player
        _chapter["playersCount"] += 1
        # 通知base房间玩家人数变化
        self.base.cellToBase({"func": "playersCount", "count": _chapter["playersCount"]})
        return _player

    def is_player_in_players(self, player, players):
        """
        根据实体id判断玩家是否在玩家集合里
        """
        for v in players:
            if player["entity"].id == v["entity"].id:
                return True
        return False

    def is_same_player(self, player1, player2):
        """
        根据实体id判断两个玩家是否是同一个
        """
        if player1["entity"].id == player2["entity"].id:
            return True
        return False

    def get_entity_id(self, player):
        return player["entity"].id

    def getPlayer(self, entityId):
        """
        :param entityId:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter["players"]
        for _player in _players.values():
            DEBUG_MSG('entity_id:%s,for entityid%s' % (entityId, _player['entity'].id))
            if _player["entity"].id == entityId:
                return _player

    def removePlayer(self, entityId):
        """
        移除本局中一个玩家，并归还位置
        :param entityId:实体id
        :return:
        """
        _chapter = self.chapters[self.cn]
        _empty_location = _chapter["emptyLocation"]
        _player = self.getPlayer(entityId)
        _players = _chapter["players"]
        if _player is None:
            return
        else:
            _locationIndex = _player["locationIndex"]
            _empty_location.append(_locationIndex)
            _empty_location.sort()
            _players.pop(_locationIndex)
            _chapter["playersCount"] -= 1
            # 通知base房间玩家人数变化
            self.base.cellToBase({"func": "playersCount", "count": _chapter["playersCount"]})
            DEBUG_MSG('[Room id:%s] removePlayer locationIndex %s' % (self.info['roomId'], _locationIndex))

    def newStatisticalData(self):
        """
        全局统计数据
        :return:
        """

    def addPlayerInSD(self, _player):
        """
        :param _player:
        :return:
        """

    def romovePlayerFromSD(self, _player):
        """
        :param _player:
        :return:
        """

    def changeChapterState(self, state):
        """
        流程控制
        :param state:
        :return:
        """

    def getBotPlayers(self):
        """
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter["players"]
        _r = []
        for p in _players.values():
            if p["entity"].info["isBot"]:
                _r.append(p)
        return _r

    def banker_area_random(self, lstval):
        """
        当只有一个用户时，直接返回；
        当有多个用户时，连庄次数不能大于2； 当没有找到连庄次数小于2的用户时，随机一个
        :param lstval:玩家ID列表
        :return:
        """
        count = len(lstval)
        if count <= 0:
            return 0
        elif count == 1:
            return lstval[0]

        lst_pre_random = []
        chapter = self.chapters[self.cn]
        plyers_dict = chapter['playerInGame']
        for k in lstval:
            player = plyers_dict[k]
            if player:
                bankerHistory = player['entity'].info['bankerHistory']
                if bankerHistory is None or sum(bankerHistory[-2:]) < 2:
                    lst_pre_random.append(k)
        if lst_pre_random:
            count = len(lst_pre_random)
            area_count = count * 1000
            val = random.randint(0, area_count - 1)
            index_val = val // 1000
            return lst_pre_random[index_val]
        else:
            area_count = count * 1000
            val = random.randint(0, area_count - 1)
            index_val = val // 1000
            return lstval[index_val]

    # --------------------------------------------------------------------------------------------
    #                            CELL中定义的方法
    # --------------------------------------------------------------------------------------------

    def baseToCell(self, pyDic):
        """
        :param pyDic:
        :return:
        """
        DEBUG_MSG("[baseToCell] basetocell pydic%s" % pyDic)
        _func_name = pyDic["func"]
        if _func_name == "initRoom":
            _dic = pyDic["dic"]
            self.initRoom(_dic)
        elif _func_name == 'initRoomRate':
            _dic = pyDic['dic']
            self.initRoomRate(_dic['roomRate'])
        elif _func_name == 'initServerConfig':
            _dic = pyDic['dic']
            self.init_server_config(_dic)
        elif _func_name == "onEnter":
            _id = pyDic["id"]
            self.onEnter(_id)
        elif _func_name == "roomDestroy":
            self.callOtherClientsFunction("roomDestroy", [self.info["type"]])
            self.destroySpace()
        elif _func_name == "destroySpace":
            self.destroySpace()
        elif _func_name == "retCutRatio":
            self.cutRatio = round(float(pyDic["ratio"]), 3)
        elif _func_name == "disbandTeaHouseRoomByCreator":
            self.tea_house_disband_room_by_creator()
        elif _func_name == "refreshGameCoin":
            self.refresh_game_coin(int(pyDic["databaseId"]), int(pyDic["modifyCount"]))
        elif _func_name == 'refreshLuckyCard':
            self.refresh_lucky_card(int(pyDic["databaseId"]), int(pyDic["modifyCount"]))
        elif _func_name == 'refreshGold':
            self.refresh_gold(int(pyDic['databaseId']), int(pyDic['count']), isModify=bool(pyDic['isModify']))
        elif _func_name == 'refreshTeaHouseInfo':
            self.refresh_tea_house_info(pyDic['info'])
        elif _func_name == 'OnAccountCellDestroy':
            self.on_account_cell_destroy(pyDic['accountDBID'])
        elif _func_name == 'clientStateChange':
            self.refresh_client_state()
        elif _func_name == 'JoinAnotherRoom':
            # 离开老房间
            self.onLeave(pyDic['accountDBID'], {'inviteRoomInfo': pyDic['inviteRoomInfo'], 'JoinAnotherRoom': True})

    #
    def refresh_client_state(self):
        """
        刷新玩家在线状态
        :return:
        """
        pass

    def on_account_cell_destroy(self, account_db_id):
        pass

    def refresh_tea_house_info(self, tea_house_info):
        if 'luckyCardSwitch' in tea_house_info:
            self.lucky_card_switch = tea_house_info['luckyCardSwitch']
        if 'gameCoinSwitch' in tea_house_info:
            if self.started:
                return
            self.game_coin_switch = tea_house_info['gameCoinSwitch']
            self.info['gameCoinSwitch'] = self.game_coin_switch

    def initRoomRate(self, room_rate):
        self.roomRate = room_rate

    def init_server_config(self, config):
        self.server_config = config

    def initRoom(self, dic):
        """
        base--->cell
        :return:
        """
        # 全局记录
        KBEngine.setSpaceData(self.spaceID, "owner", str(self.id))
        # if "roomName" in dic:
        #     del dic["roomName"]
        # if 'gps' in dic:
        #     del dic['gps']
        self.info = dic
        self.gold_name = '金币' if self.info['roomType'] == 'gameCoin' else '金币'
        # 是否是茶楼房间
        if self.info['roomType'] == 'gameCoin' or self.info['roomType'] == 'normalGameCoin':
            if 'teaHouseId' in self.info.keys() and self.info['teaHouseId'] != -1:
                self.is_tea_house_room = True
            else:
                self.is_tea_house_room = False
        else:
            self.is_tea_house_room = False
        # 创建牌局
        _max_players_count = dic["maxPlayersCount"]
        self.newStatisticalData()
        self.newChapter(_max_players_count)
        self.changeChapterState(0)
        self.base.cellToBase({"func": "onRoomInit"})

    def onEnter(self, accountEntityId):
        """
        all--->cell
        进入房间
        允许观战随便进；不允许观战时，游戏已开始或玩家数量已满不可以进外，其他都可以进
        """
        # 如果不允许观战
        if ('witness' in self.info.keys() and not self.info['witness']) or \
                self.info["type"] not in Const.CanWatchGame.can_watch_game or \
                self.total_settlement_ed:
            DEBUG_MSG('Can not witness')
            # 如果游戏开始，踢出此时加进来的玩家
            if 'playerInRoom' in self.chapters[0].keys():
                player_in_room_count = len(self.chapters[0]['playerInRoom'])
            else:
                player_in_room_count = len(self.chapters[0]['players'])
            if self.info['started'] or player_in_room_count >= self.info['maxPlayersCount']:
                DEBUG_MSG('RoomBase started')
                try:
                    account = KBEngine.entities[accountEntityId]
                    if account.id not in self.accountEntities.keys():
                        tea_house_id = -1
                        if 'teaHouseId' in self.info.keys():
                            tea_house_id = self.info['teaHouseId']
                        self.callClientFunction(accountEntityId, 'CanNotWatchGame', {'teaHouseId': tea_house_id})
                        # account.cellToClient('CanNotWatchGame', {'args': {'teaHouseId': tea_house_id}})
                        account.destroy()
                        return False
                except KeyError as e:
                    ERROR_MSG('RoomBase onEnter%s' % e)
                except AttributeError as e:
                    ERROR_MSG('RoomBase onEnter%s' % e)
        DEBUG_MSG('roomBase onenter account entity.info:%s' % KBEngine.entities[accountEntityId].info)

        # 如果有真人加入，那么开启自动加入机器人计时器
        # if KBEngine.entities[accountEntityId].info["isBot"] == 0:
        #     if self.info['type'] in Const.have_bot_game:
        #         max_player_count = self.info['maxPlayersCount']
        #         player_in_game_count = len(self.chapters[0]['playerInGame'])
        #         for i in range(max_player_count - player_in_game_count - 1):
        #             _time = random.randint(join_bots_time, join_bots_time + 5)
        #             # 100代表加入机器人计时器
        #             _t = self.addTimer(_time, 0, 100)
        return True

    def onLeave(self, accountEntityId, leave_param=None):
        """
        all--->cell
        离开房间
        """
        # 检测参数合法性
        _accountEntities = self.accountEntities
        if accountEntityId not in _accountEntities.keys():
            return
        # 如果是玩家就移除此玩家
        _player = self.getPlayer(accountEntityId)
        if _player:
            self.removePlayer(accountEntityId)
            # 从统计数据中移除
            self.romovePlayerFromSD(accountEntityId)
            # 通知所有客户端座位信息
            self.retLocations()
            # 广播金币
            self.retGolds()
        # 移出房间
        _accountEntity = _accountEntities[accountEntityId]
        _accountEntities.pop(accountEntityId)
        self.base.cellToBase({"func": "LogoutRoom", "accountId": accountEntityId})
        _accountEntity.destroySelf()
        self.autoDestroy()
        DEBUG_MSG('[Room id:%i]------->onLeave account = %i.' % (self.info['roomId'], accountEntityId))

    def onPlayerClientDeath(self, accountEntity):
        """
        玩家非正常离开
        :return:
        """
        ""

    def onPlayerReady(self, entityId):
        """
        client---->cell
        :param entityId:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter["players"]
        _player = self.getPlayer(entityId)
        _playersCount = _chapter["playersCount"]
        _chapterState = _chapter["chapterState"]
        # 准备操作只在0状态下有效
        if _chapterState != 0:
            return
        if _player is not None:
            _player["isReady"] = True
        else:
            return
        # 判断牌局是否可以开始
        if _playersCount <= 1:
            return
        _flag = True
        for i in _players.values():
            if not i["isReady"]:
                _flag = False
                break
        if _flag:
            self.changeChapterState(1)

    def get_distance_from_everyone(self, account_id):
        account_entity = self.accountEntities[account_id]
        distance_info = {}
        # 1 循环所有用户文件实体
        for player_entity_id, player_entity in self.accountEntities.items():
            if player_entity.id == account_id:
                continue
            # 如果两个玩家都有经纬度
            if player_entity.info["latitude"] and player_entity.info["longitude"] and \
                    account_entity.info["longitude"] and account_entity.info["latitude"]:
                # 获取两个玩家距离  E距离
                distance = Util.getdistance(account_entity.info["longitude"], account_entity.info["latitude"],
                                            player_entity.info["longitude"], player_entity.info["latitude"])
                distance_info[player_entity.id] = round(distance * 1000, 2)
        self.callClientFunction(account_id, "distanceFromEveryone", distance_info)

    def get_distance_from_other(self, account_id, distance_info):

        def get_distance(player_entity1, player_entity2):
            if player_entity1.info["latitude"] and player_entity1.info["longitude"] and \
                    player_entity2.info["longitude"] and player_entity2.info["latitude"]:
                distance = Util.getdistance(player_entity1.info["longitude"], player_entity1.info["latitude"],
                                            player_entity2.info["longitude"], player_entity2.info["latitude"])
                return round(distance * 1000, 2)
            return 0

        def is_exist(id1, id2, distance_info2):
            for v in distance_info2:
                if id1 in v["member"] and id2 in v["member"]:
                    return True
            return False

        # 1 循环所有用户文件实体
        account_entity = self.accountEntities[account_id]
        for player_entity_id, player_entity in self.accountEntities.items():
            if player_entity.id == account_id:
                continue
            if not is_exist(account_id, player_entity.id, distance_info):
                temp_distance = get_distance(account_entity, player_entity)
                item = {}
                item["member"] = [account_id, player_entity.id]
                item["distance"] = temp_distance
                distance_info.append(item)

    def get_distance_everyone(self, account_id):
        distance_info = []
        # 1 循环所有用户文件实体
        all_players = []
        for player_entity_id, player_entity in self.accountEntities.items():
            self.get_distance_from_other(player_entity_id, distance_info)
            player = {}
            player["name"] = player_entity.info["name"]
            player["id"] = player_entity.info["id"]
            player["headImage"] = player_entity.info["headImageUrl"]
            all_players.append(player)
        self.callClientFunction(account_id, "GetPlayersDistance", {"members": all_players, "distance": distance_info})

    def reqRoomBaseInfo(self, accountEntityId):
        """
        client--->cell
        :param accountEntityId:
        :return:
        """
        self.retRoomBaseInfo(accountEntityId)

    def playerOperation(self, accountEntityId, jsonData):
        """
        :param accountEntityId:
        :param jsonData:
        :return:
        """
        _py_dic = json.loads(jsonData)
        _player = self.getPlayer(accountEntityId)
        if not _player:
            return
        _operation_name = _py_dic["func"]
        _args = _py_dic["args"]
        return _player, _operation_name, _args

    def clientReq(self, accountEntityId, jsonData):
        """
        client---->cell
        :param accountEntityId:
        :param jsonData:
        :return:
        """
        _py_dic = json.loads(jsonData)
        if accountEntityId not in self.accountEntities:
            return
        _accountEntity = self.accountEntities[accountEntityId]
        if not _accountEntity:
            return
        _func_name = _py_dic["func"]
        _args = _py_dic["args"]
        if _func_name == "distanceFromEveryone":
            self.get_distance_from_everyone(accountEntityId)
        # if _func_name == "GetPlayersDistance":
        #     self.get_distance_everyone(accountEntityId)
        elif _func_name == 'totalSettlementStr':
            self.send_record_str(accountEntityId)
        elif _func_name == 'changeLessPersonModeSwitch':
            self.change_less_person_mode_switch(accountEntityId, _args)
        return _accountEntity, _func_name, _args

    # --------------------------------------------------------------------------------------------
    #                            与Client通信的方法
    # --------------------------------------------------------------------------------------------

    def retGolds(self):
        """
        广播当前所有玩家金币数
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter["players"]
        # 广播金币变化
        _l = []
        for p in _players.values():
            _l.append(p["locationIndex"])
            _l.append(p["gold"])
        self.callOtherClientsFunction("goldsChange", _l)

    def retLocations(self):
        """
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter["players"]
        _entityIds = []
        _locationIndexs = []
        _location_info = {}
        for i in _players.keys():
            _entityId = _players[i]["entity"].id
            _entityIds.append(_entityId)
            _locationIndexs.append(i)
        _location_info["entityIds"] = _entityIds
        _location_info["locationIndexs"] = _locationIndexs
        _json_data = json.dumps(_location_info)
        if self.otherClients is None:
            return
        DEBUG_MSG('[Room id%s]---------->retLocationIndexs info %s' % (self.info['roomId'], _json_data))
        self.otherClients.retLocationIndexs(_json_data)

    def retRoomBaseInfo(self, accountEntityId):
        """
        单独通知指定实体
        :param accountEntityId:
        :return:
        """
        client_info = self.info.copy()
        # 不向客户端发送房间名
        if "roomName" in client_info:
            del client_info["roomName"]
        # 不向客户端发送房间名
        if "gps" in client_info:
            del client_info["gps"]
        _json_data = json.dumps(client_info)
        # self.entitiesInView()
        player_entity = KBEngine.entities[accountEntityId]
        if player_entity and player_entity.client:
            player_entity.clientEntity(self.id).retRoomBaseInfo(_json_data)

    def dealCardsToPlayer(self, locationIndex, cards):
        """
        :param locationIndex:
        :param cards:
        :return:
        """
        if self.otherClients is None:
            return
        self.retChapterSysPrompt("给玩家" + str(locationIndex) + "发牌")
        self.otherClients.dealCardsToPlayer(locationIndex, cards)

    def retChapterSysPrompt(self, content):
        """
        牌局系统提示
        :param content 内容
        :return:
        """
        if self.otherClients is None:
            return
        self.otherClients.retChapterSysPrompt(content)

    def callOtherClientsFunction(self, funcName, args):
        """
        :param funcName:
        :param args:
        :return:
        """
        if "RollNoticeInRoom" != funcName:
            self.debug_msg("callOtherClientsFunction func=%s, args=%s" % (funcName, args))
        py_dic = {"args": args}
        _json_data = json.dumps(py_dic)
        if self.otherClients is None:
            return
        self.otherClients.cellToClient(funcName, _json_data)
        replay_data = {"funcType": "callOtherClientsFunction", "funcName": funcName,
                       "args": args}
        if self.cn not in self.chapter_replay.keys():
            self.chapter_replay[self.cn] = []
        self.chapter_replay[self.cn].append(replay_data)

    def callClientFunction(self, accountEntityId, funcName, args):
        """
        :param accountEntityId:
        :param funcName:
        :param args:
        :return:
        """
        self.debug_msg("callClientFunction func=%s, args=%s" % (funcName, args))
        py_dic = {"args": args}
        _json_data = json.dumps(py_dic)
        _entity = KBEngine.entities[accountEntityId]
        if not _entity:
            return
        if 'isBot' in _entity.info and _entity.info["isBot"] == 1:
            return
        if _entity.clientEntity is None:
            return
        try:
            _entity.clientEntity(self.id).cellToClient(funcName, _json_data)
        except:
            ERROR_MSG('RoomBase::callClientFunction error')
        else:
            pass

    def tea_house_disband_room_by_creator(self):
        pass

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
                    v["gold"] += modify_count
                    self.callOtherClientsFunction("refreshGameCoin", {"gameCoin": v["gold"], "accountId": k})
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

    def refresh_lucky_card(self, account_db_id, modify_count):
        """
        刷新房间内福卡
        :param account_db_id:
        :param modify_count:
        :return:
        """
        _chapter = self.chapters[self.cn]
        if self.info["roomType"] == "gameCoin":
            for k, v in _chapter["playerInRoom"].items():
                if v["entity"].info["dataBaseId"] == account_db_id:
                    v['entity'].lucky_card += modify_count
                    self.callOtherClientsFunction("refreshLuckyCard",
                                                  {"luckyCard": v["entity"].lucky_card, "accountId": k})
                    break

    def refresh_gold(self, account_db_id, count, isModify=False):
        """
        刷新房间内金币
        :param isModify: 是否是修改金币
        :param account_db_id:
        :param count:
        :return:
        """
        _chapter = self.chapters[self.cn]
        if self.info["roomType"] == "normalGameCoin" or self.info["roomType"] == "card":
            for k, v in _chapter["playerInRoom"].items():
                if v["entity"].info["dataBaseId"] == account_db_id:
                    if isModify:
                        v["gold"] += count
                    else:
                        v["gold"] = count
                    self.callOtherClientsFunction("refreshGold", {"gold": v["gold"], "accountId": k})
                    break

    def set_base_player_game_coin(self, accountId):
        """
        设置玩家比赛分数量,通知base
        :param accountId:
        :return:
        """
        if self.info['roomType'] != 'gameCoin':
            return
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter["playerInRoom"]
        _player = _playerInRoom[accountId]
        _player["entity"].accountMutableInfo["gameCoin"] = _player["gold"]
        _player["entity"].base.cellToBase({"func": "setAccountMutableInfo", "dic": {
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1,
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
        _player["entity"].accountMutableInfo["gold"] = _player["gold"]
        _player["entity"].base.cellToBase({"func": "setAccountMutableInfo", "dic": {
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1,
            "gold": _player["entity"].accountMutableInfo["gold"]}})

    # 统计局数
    def set_base_player_chapter_count(self):
        _chapter = self.chapters[self.cn]
        for k, v in _chapter["playerInGame"].items():
            v["entity"].base.cellToBase({"func": "AddChapterCount", "teaHouseId": self.info["teaHouseId"]})

    def bless(self, account_entity_id, bless_type):
        """
        祈福
        :param bless_type:
        :param account_entity_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        account = chapter['playerInRoom'][account_entity_id]
        account_entity = account['entity']
        # 如果超过了免费次数
        if account_entity.today_bless_count > Const.GameConfigJson.config_json['Hall']['blessRoomCardStandard']:
            remain_room_card = account_entity.room_card
            # 如果没有支付AA支付钻石，预先扣除AA支付钻石
            if self.info['payType'] == Const.PayType.AA and not account['AARoomCardConsumed']:
                remain_room_card -= self.info['roomCardConsume']
            DEBUG_MSG('remain_room_card:%s' % remain_room_card)

            if remain_room_card < Const.GameConfigJson.config_json['Hall']['blessRoomCardConsume']:
                self.callClientFunction(account_entity_id, 'Notice', ['钻石不足'])
                return
            else:
                account_entity.base.cellToBase({'func': 'bless'})
                self.callClientFunction(account_entity_id, 'blessSuccess', {'type': bless_type})
        else:
            account_entity.base.cellToBase({'func': 'bless'})
            self.callClientFunction(account_entity_id, 'blessSuccess', {'type': bless_type})

    def free_bless_count(self, account_entity_id):
        """
        免费祈福次数
        :param account_entity_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        account = chapter['playerInRoom'][account_entity_id]
        account_entity = account['entity']

        free_count = Const.GameConfigJson.config_json['Hall'][
                         'blessRoomCardStandard'] - account_entity.today_bless_count
        if free_count < 0:
            free_count = 0
        self.callClientFunction(account_entity_id, 'freeBlessCount', {
            'count': free_count, 'roomCardConsume': Const.GameConfigJson.config_json['Hall']['blessRoomCardConsume']})

    def is_gold_session_room(self):
        """
        是否是金币场房间
        :return:
        """
        return self.info['level'] != 0

    # --------------------------------------------------------------------------------------------
    #                              System Callbacks
    # --------------------------------------------------------------------------------------------

    def total_settlement(self):
        """
        总结算
        :return:
        """
        pass

    def write_chapter_info_to_db(self):
        """
        写入战绩
        :return:
        """
        pass

    def autoDestroy(self):
        """
        自动销毁房间
        :return:
        """
        chapter = self.chapters[self.cn]
        # 如果坐下玩家不存在真实玩家则自动解散
        for k, v in chapter["playerInGame"].items():
            if v["entity"].info["isBot"] == 0:
                return

        # 比赛场手动解散通知 base 解散房间
        if self.is_tea_house_room:

            # 手动解散
            if self.is_manual_disband:
                self.base.cellToBase({"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                                      "teaHouseId": self.info["teaHouseId"]})
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                return

            # 群主解散,会先从冠名赛房间列表移除，所以可以直接摧毁
            if self.disband_from_creator:
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                self.destroySpace()
                return

            # 比赛场总结算，通知冠名赛移除房间并摧毁实体
            if self.total_settlement_ed:
                self.base.cellToBase(
                    {"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                     "teaHouseId": self.info["teaHouseId"]})
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                return

            # 如果房间中没有人，房间已开始，解散
            if self.started:
                self.base.cellToBase(
                    {"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                     "teaHouseId": self.info["teaHouseId"]})
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                return

        elif self.is_gold_session_room():
            # 如果是手动解散房间或者总结算，或者房间开始却没有人，解散房间
            if self.is_manual_disband or self.total_settlement_ed or self.started:
                self.base.cellToBase({"func": "disbandGoldSessionRoom", "roomId": self.info["roomId"],
                                      "level": self.info["level"]})

        # 普通房间正常解散
        elif self.info["roomType"] == "card":
            # 一局都没结算并且为房主支付，归还钻石
            if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                self.base.cellToBase({"func": "returnRoomCardToCreator"})
            # 代开房间先通知base从代开房间列表移除
            if "substitute" in self.info and self.info["substitute"]:
                self.base.cellToBase(
                    {"func": "disbandSubstituteRoom", "roomInfo": self.info, "creator": self.info["creator"]})
            else:
                self.destroySpace()

    def onDestroy(self):
        """
        KBEngine method.
        entity销毁
        """
        DEBUG_MSG("Account::onDestroy: %i." % self.id)

    def onTimer(self, timerHandle, userData):
        """
        定时器回调
        :param timerHandle:
        :param userData:
        :return:
        """
        if timerHandle == self.disband_timer:
            DEBUG_MSG('[Room id %s]------>onTimer disbandTime %s' % (self.info['roomId'], timerHandle))
            self.disband_timer = -1
            self.is_disbanding = False
            self.total_settlement()
            self.write_chapter_info_to_db()
        # 解散计时器
        elif str(6666) in str(userData):
            account_id = int(str(userData)[4:])
            DEBUG_MSG('room base userdata account_id:%s' % account_id)
            self.response_disband(account_id, 1)
        # 加机器人计时器
        # elif userData == 100:
        #     DEBUG_MSG('roomId:%s ontimer join bots timer' % self.info['roomId'])
        #     self.base.cellToBase({"func": "joinBots"})

    def player_ready(self, accountId):
        pass

    def disband_room_broadcast(self, accountId):
        """
        解散房间广播
        :param accountId:
        :return:
        """
        _chapter = self.chapters[self.cn]
        # 1 正在解散状态中
        if self.is_disbanding:
            return
        if self.total_settlement_ed:
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
            self.total_settlement()
            # 1 将牌局信息写入数据库
            self.write_chapter_info_to_db()
            return
        if accountId not in _chapter['playerInGame']:
            return
        _chapter["playerInGame"][accountId]["agreeDisband"] = True
        self.disband_sender = accountId
        self.is_disbanding = True
        args = {"accountId": accountId, "disbandTime": time_disband}
        self.callOtherClientsFunction("RequestDisbandRoom", args)

        # 解散房间倒计时
        self.disband_timer = self.addTimer(time_disband, 0, 0)
        _chapter["deadline"] = time.time() + time_disband

        # 机器人操作倒计时
        for k, v in _chapter['playerInGame'].items():
            if v['entity'].info['isBot'] == 1:
                user_data = int(str(6666) + str(k))
                DEBUG_MSG(['user_Data%s' % user_data])
                _t = self.addTimer(random.randint(2, bot_disband_time_max), 0, user_data)

    def response_disband(self, accountId, result):
        """
        解散房间回应
        :param accountId:
        :param result:
        :return:
        """
        chapter = self.chapters[self.cn]
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
            self.total_settlement()
            self.write_chapter_info_to_db()

    def bots_ready(self):
        """
        机器人准备
        :return:
        """
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['entity'].info['isBot'] == 1:
                self.player_ready(k)

    def gen_award(self):
        """
        生成奖品
        :return:
        """
        award = []
        gold = []
        while len(gold) < 3:
            _r = random.randint(0, 99)
            for item in self.server_config['giftList']:
                if item['appear'][0] <= _r <= item['appear'][1] and item['type'] == 0 and item['count'] not in gold:
                    gold.append(item['count'])
                    if len(gold) >= 3:
                        break

        diamond = []
        while len(diamond) < 1:
            _r = random.randint(0, 99)
            for item in self.server_config['giftList']:
                if item['appear'][0] <= _r <= item['appear'][1] and item['type'] == 1 and item['count'] not in diamond:
                    diamond.append(item['count'])
                    if len(diamond) >= 1:
                        break

        other = []
        while len(other) < 1:
            _r = random.randint(0, 99)
            for item in self.server_config['giftList']:
                if item['appear'][0] <= _r <= item['appear'][1] and item['type'] > 1 and item['count'] not in other:
                    other.append(item['count'])
                    if len(other) >= 1:
                        break

        gold_img = self.get_award_image(0)
        for g in gold:
            award.append({'type': 'gold', 'count': g, 'img': gold_img})

        diamond_img = self.get_award_image(1)
        for d in diamond:
            award.append({'type': 'diamond', 'count': d, 'img': diamond_img})

        for o in other:
            other_img = self.get_award_image(10 if o == 1 else 5)
            award.append({'type': 'other', 'count': o, 'img': other_img})

        DEBUG_MSG('roomBase award：%s' % award)
        return award

    def gen_selected(self, award):
        """
        生成概率
        :return:
        """
        while True:
            _r = random.choice(award)
            if _r['type'] != 'other':
                return _r

    def get_award_image(self, award_type):
        """
        获取奖品图片
        :return:
        """
        for item in self.server_config['giftList']:
            if item['type'] == award_type:
                return item['image_url']

    def have_gold_limit(self):
        """
        根据是否是比赛币场和比赛币开关判断是否有金币限制
        :return:
        """
        # if self.info['roomType'] == 'gameCoin' and not self.game_coin_switch:
        if self.info['roomType'] == 'gameCoin':
            return True
        return True

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

    def send_record_str(self, entity_id):
        if not self.total_settlement_ed:
            self.debug_msg('get_record_str not totalSettlement')
            return
        self.debug_msg('get_record_str final_str%s' % self.record_str)
        self.callClientFunction(entity_id, 'totalSettlementStr', {'str': self.record_str})

    def get_chapter_record_str(self, game_type: str, chapter_count: int, max_chapter_count: int, total_settlement):
        title = '大象互娱-%s\n' % str(game_type)
        start_time = self.get_readable_time(int(self.info['createRoomTime']))
        end_time = self.get_readable_time(int(time.time()))

        room_id = "房间号：%s\n" % self.info['roomId']
        chapter_info = "游戏局数：%s/%s\n" % (chapter_count, max_chapter_count)
        time_info = "时间：%s 至 %s\n" % (start_time, end_time)
        total_settlement_str = '成绩：\n'
        for player in total_settlement:
            name = player['name']
            total_gold_change = player['totalGoldChange']
            _str = '%s    %s 分\n' % (name, total_gold_change)
            total_settlement_str += _str

        final_str = title + room_id + chapter_info + time_info + total_settlement_str
        return final_str

    def get_readable_time(self, int_time: int) -> str:
        """
        获取可读时间字符串
        :param int_time:
        :return:
        """
        time_local = time.localtime(int_time)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_local)

    def debug_msg(self, message):
        try:
            if 'teaHouseId' in self.info:
                tea_house_id = self.info['teaHouseId']
            else:
                tea_house_id = -1
            DEBUG_MSG('[RoomType:%s RoomId %s,TeaHouseId:%s]------- %s' % (self.info['type'],
                                                                           self.info['roomId'],
                                                                           tea_house_id, message))
        except:
            DEBUG_MSG('debug_msg error')

    def is_need_rand_score_control(self, room_type):
        """
        随机区间为100000
        概率为20%，则概率区间为: 随机区间/5
        随机区间和概率区间各分20份，每一份概率区间对应一个随机区间
        """
        scoreControlPercent = Const.ServerGameConfigJson.config_json['TeaHouse']['scoreControlPercent']
        default_val = scoreControlPercent['default']
        if room_type in scoreControlPercent:
            rand_percent = scoreControlPercent[room_type]
        else:
            rand_percent = default_val

        DEBUG_MSG('is_need_rand_score_control %s' % rand_percent)
        if rand_percent < 0 or rand_percent > 1:
            return False

        rand_max = 100000
        rand_count = 20
        # rand_percent = 0.2
        rand_range = rand_max * rand_percent
        seg_val = rand_max // rand_count
        sub_seg_val = rand_range // rand_count

        is_in_rand_range = False
        tmp_num = random.randint(1, rand_max)
        for i in range(rand_count):
            one_seg_val = seg_val * i
            if one_seg_val <= tmp_num < one_seg_val + sub_seg_val:
                is_in_rand_range = True
                break
        return is_in_rand_range
        # return True

    def select_max_loser(self, room_players):
        """选择输分最多的人作为幸运玩家，发好牌"""
        maxloser = None
        maxlosescore = 0
        for p in room_players:
            losescore = p['entity'].get_need_control_score()
            if losescore > maxlosescore:
                maxlosescore = losescore
                maxloser = p
        DEBUG_MSG('最大输家 %s %s' % (maxlosescore, maxloser['entity'].id if maxloser else maxloser))
        return maxloser

    def select_luck_max_loser(self, room_players):
        """选择幸运玩家中输分最多人发好牌"""
        maxloser = None
        maxlosescore = 0
        for p in room_players:
            losescore = p['entity'].get_need_control_luck_score()
            if losescore > maxlosescore:
                maxlosescore = losescore
                maxloser = p
        DEBUG_MSG('最大幸运家 %s' % maxloser['entity'].id if maxloser else maxloser)
        return maxloser

    def get_current_chapter(self):
        """
        获取当前牌局
        :return:
        """
        _chapter = self.chapters[-1]
        return _chapter

    def get_seat_players(self):
        _chapter = self.get_current_chapter()
        _players = _chapter['players']
        return _players

    def get_seat_player_by_entity_id(self, entityId):
        """
        通过实体id获取坐下玩家
        :param entityId:
        :return:
        """
        _chapter = self.get_current_chapter()
        for k, v in _chapter['players'].items():
            if v['entity'].id == entityId:
                return v

    def notify_viewing_hall_players_room_info(self):
        """通知返回大厅玩家房间内状态
        """
        # 需要包含最大人数，当前人数，玩家名称，准备状态
        _plays = self.get_seat_players()

        def get_room_info(_plays):
            plays_info = dict()
            plays_info['maxPlayerCount'] = self.info['maxPlayersCount']
            plays_info['seatPlayerCount'] = len(_plays)
            plays_info["playerReadyInfo"] = []
            is_anonymity = self.info["anonymity"] if "anonymity" in self.info else False
            for _p2 in _plays.values():
                one_player2 = self.player_entity(_p2)
                _player = dict()
                _player['userId'] = one_player2.info['userId']
                _player['name'] = one_player2.info['name'] if not is_anonymity else "匿名"
                _player['state'] = one_player2.is_ready()
                plays_info["playerReadyInfo"].append(_player)
            return plays_info

        room_info = get_room_info(_plays)
        for _p in _plays.values():
            one_player = self.player_entity(_p)
            if one_player.viewing_hall:
                self.callClientFunction(one_player.id, "GetPlayerReadyInfoOnTeaHouse", room_info)

    def notify_viewing_hall_players_chapter_start(self):
        """通知客户端返回房间"""
        if self.info["roomType"] == "challenge":
            return
        _args = {"type": self.info["type"], "roomType": self.info["roomType"], "roomId": self.info["roomId"]}
        _plays = self.get_seat_players()
        for _p in _plays.values():
            one_player = self.player_entity(_p)
            if one_player.viewing_hall:
                one_player.base.cellToBase({"func": "reconnectRoom", "args": _args})

    def select_day_good_pai_player(self, room_players, max_good_count):
        """
        每日发好牌, 选择需要发好牌的玩家，随机选择
        """
        lst_rand = []
        for p in room_players:
            today_count = p['entity'].get_need_day_pai_control_count()
            if today_count < max_good_count:
                lst_rand.append(p)
        player = None
        if lst_rand:
            player = random.choice(lst_rand)
        DEBUG_MSG('每日好牌玩家 %s' % (player['entity'].id if player else player))
        return player

    def set_day_good_pai_count_in_base(self, dic_players):
        """
        每日发好牌次数同步到BASE
        总结算时同步一次，打牌时在account cell端统计
        """
        for k, v in dic_players.items():
            v["entity"].base.cellToBase(
                {"func": "setDayGoodPaiCount", "goodPaiCount": v['entity'].info['goodPaiCount']})
            # DEBUG_MSG('set_day_good_pai_count_in_base %s %s' % (k, v['entity'].info['goodPaiCount']))

    @staticmethod
    def player_entity(player):
        return player['entity']

    def get_player_entity(self, entity_id):
        if entity_id in self.accountEntities:
            return self.accountEntities[entity_id]
        return None

    @property
    def max_chapter_count(self):
        return self.info["maxChapterCount"]

    @property
    def current_chapter_count(self):
        return self.cn

    def mj_fu_ka_lottery(self):
        """
        福卡抽奖
        :return:
        判断玩家分数是否在区间内
        """
        lottery_in_fu_ka = []
        # 福卡、比赛币系统未启用时不能抽奖
        if not self.lucky_card_switch and not self.game_coin_switch:
            return lottery_in_fu_ka
        if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
            # 找到大赢家
            winner = self.mj_get_winner()
            # 扣大赢家费用
            if self.info["winnerRaffleInterval"]:
                account_lottery = []
                # 遍历大赢家
                for k, v in winner.items():
                    consume = 0
                    awards = self.gen_award()
                    select = self.gen_selected(awards)
                    for i in range(0, len(self.info["winnerRaffleInterval"])):
                        if self.info["winnerRaffleInterval"][i]['interval'][0] <= v["totalGoldChange"] <= \
                                self.info["winnerRaffleInterval"][i]['interval'][1]:
                            consume += self.info['winnerRaffleInterval'][i]['consume']
                            DEBUG_MSG('winnerRaffleInterval_____________%s' % {"awards": awards, 'selected': select,
                                                                               "consume": consume})

                            self.callClientFunction(v['entity'].id, 'Awards',
                                                    {"awards": awards, 'selected': select, "consume": consume,
                                                     "scoreVisible": self.server_config["scoreVisible"],
                                                     "WinnerConsume": 0})
                            lottery_in_fu_ka.append(v["entity"].info["userId"])
                            break
                    lottery_type = 0
                    if select["type"] == 'gold':
                        lottery_type = 0
                    elif select["type"] == 'diamond':
                        lottery_type = 1
                    account_lottery.append({"accountDBID": v["entity"].info["userId"], "consumeLuckyCard": consume,
                                            "count": select["count"], "type": lottery_type})
                self.base.cellToBase({"func": "Lottery", "args": account_lottery})

            # 扣其他玩家费用
            if self.info['allRaffleInterval']:
                account_lottery = []
                for k, v in self.chapters[self.cn][PLAYER_IN_GAME].items():
                    # 其他玩家不扣大赢家
                    # 如果大赢家开启，其他玩家不扣大赢家
                    if k in winner and self.info["winnerRaffleInterval"]:
                        continue
                    consume = 0
                    awards = self.gen_award()
                    select = self.gen_selected(awards)
                    random.shuffle(awards)
                    for i in range(0, len(self.info["allRaffleInterval"])):
                        if self.info["allRaffleInterval"][i]['interval'][0] <= v["totalGoldChange"] <= \
                                self.info["allRaffleInterval"][i]['interval'][1]:
                            consume += self.info['allRaffleInterval'][i]['consume']
                            DEBUG_MSG('allRaffleInterval_____________%s' % {"awards": awards, 'selected': select,
                                                                            "consume": consume})
                            self.callClientFunction(v['entity'].id, 'Awards',
                                                    {"awards": awards, 'selected': select, "consume": consume,
                                                     "scoreVisible": self.server_config["scoreVisible"],
                                                     "WinnerConsume": 0})
                            lottery_in_fu_ka.append(v["entity"].info["userId"])
                            break
                    lottery_type = -1
                    if select["type"] == 'gold':
                        lottery_type = 0
                    elif select["type"] == 'diamond':
                        lottery_type = 1
                    account_lottery.append({"accountDBID": v["entity"].info["userId"], "consumeLuckyCard": consume,
                                            "count": select["count"], "type": lottery_type})
                self.base.cellToBase({"func": "Lottery", "args": account_lottery})
        return lottery_in_fu_ka

    def normal_fu_ka_lottery(self):
        """
        福卡抽奖
        :return:
        判断玩家分数是否在区间内
        """
        lottery_in_fu_ka = []
        # 福卡、比赛币系统未启用时不能抽奖
        if not self.lucky_card_switch and not self.game_coin_switch:
            return lottery_in_fu_ka
        if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
            # 找到大赢家
            winner = self.normal_get_winner()
            # 扣大赢家费用
            if self.info["winnerRaffleInterval"]:
                account_lottery = []
                # 遍历大赢家
                for k, v in winner.items():
                    consume = 0
                    awards = self.gen_award()
                    select = self.gen_selected(awards)
                    for i in range(0, len(self.info["winnerRaffleInterval"])):
                        if self.info["winnerRaffleInterval"][i]['interval'][0] <= v["totalGoldChange"] <= \
                                self.info["winnerRaffleInterval"][i]['interval'][1]:
                            consume += self.info['winnerRaffleInterval'][i]['consume']
                            DEBUG_MSG('winnerRaffleInterval_____________%s' % {"awards": awards, 'selected': select,
                                                                               "consume": consume})

                            self.callClientFunction(v['entity'].id, 'Awards',
                                                    {"awards": awards, 'selected': select, "consume": consume,
                                                     "scoreVisible": self.server_config["scoreVisible"],
                                                     "WinnerConsume": 0})
                            lottery_in_fu_ka.append(v["entity"].info["userId"])
                            break
                    lottery_type = 0
                    if select["type"] == 'gold':
                        lottery_type = 0
                    elif select["type"] == 'diamond':
                        lottery_type = 1
                    account_lottery.append({"accountDBID": v["entity"].info["userId"], "consumeLuckyCard": consume,
                                            "count": select["count"], "type": lottery_type})
                self.base.cellToBase({"func": "Lottery", "args": account_lottery})

            # 扣其他玩家费用
            if self.info['allRaffleInterval']:
                account_lottery = []
                for k, v in self.chapters[self.cn]['playerInGame'].items():
                    # 其他玩家不扣大赢家
                    # 如果大赢家开启，其他玩家不扣大赢家
                    if k in winner and self.info["winnerRaffleInterval"]:
                        continue
                    consume = 0
                    awards = self.gen_award()
                    select = self.gen_selected(awards)
                    random.shuffle(awards)
                    for i in range(0, len(self.info["allRaffleInterval"])):
                        if self.info["allRaffleInterval"][i]['interval'][0] <= v["totalGoldChange"] <= \
                                self.info["allRaffleInterval"][i]['interval'][1]:
                            consume += self.info['allRaffleInterval'][i]['consume']
                            DEBUG_MSG('allRaffleInterval_____________%s' % {"awards": awards, 'selected': select,
                                                                            "consume": consume})
                            self.callClientFunction(v['entity'].id, 'Awards',
                                                    {"awards": awards, 'selected': select, "consume": consume,
                                                     "scoreVisible": self.server_config["scoreVisible"],
                                                     "WinnerConsume": 0})
                            lottery_in_fu_ka.append(v["entity"].info["userId"])
                            break
                    lottery_type = -1
                    if select["type"] == 'gold':
                        lottery_type = 0
                    elif select["type"] == 'diamond':
                        lottery_type = 1
                    account_lottery.append({"accountDBID": v["entity"].info["userId"], "consumeLuckyCard": consume,
                                            "count": select["count"], "type": lottery_type})
                self.base.cellToBase({"func": "Lottery", "args": account_lottery})
        return lottery_in_fu_ka

    def pdk_get_settlement_winners(self):
        """
        跑得快，获取小局的大赢家
        :return:
        """
        winners = {}
        max_win = 0
        for k, v in self.chapters[self.cn]["playerInGame"].items():
            if v['goldChange'] >= max_win:
                max_win = v['goldChange']

        for k, v in self.chapters[self.cn]["playerOutGame"].items():
            if v['goldChange'] == max_win:
                winners[k] = v
        return winners

    def pdk_get_winner(self):
        """
        跑得快，获取大赢家
        :return:
        """
        winner = {}
        max_win = 0
        for k, v in self.chapters[self.cn]["playerInGame"].items():
            if v['totalGoldChange'] >= max_win:
                max_win = v['totalGoldChange']

        for k, v in self.chapters[self.cn]["playerOutGame"].items():
            if v['totalGoldChange'] == max_win:
                winner[k] = v
        return winner
    def pdk_get_true_gold(self, account_id):
        """
        金花，获得玩家当前真实金币
        :param account_id:
        :return:
        """
        _chapter = self.get_current_chapter()
        for k, v in _chapter['playerInGame'].items():
            if v['entity'].id == account_id:
                return v['totalGoldChange']

        for k, v in _chapter["playerInGame"].items():
            if v['entity'].id == account_id:
                return v['totalGoldChange']

    # 跑得快总结算抽水
    def pdk_total_settlement_billing(self):
        chapter = self.chapters[self.cn]
        total_settlement_winner = self.jh_get_winner()
        # 获取大赢家
        for k, v in total_settlement_winner.items():
            # k:account_id v:winner字典
            DEBUG_MSG('jh total_settlement_winner%s' % k)
            # 计算大赢家小局抽水
            total_settlement_winner_true_gold = self.pdk_get_true_gold(k)
            total_settlement_winner_billing = total_settlement_winner_true_gold * self.info['totalSettlementBilling']
            DEBUG_MSG('RoomType1 settlement_winner billing%s' % total_settlement_winner_billing)
            v['totalGoldChange'] -= total_settlement_winner_billing
            v['totalGoldChange'] = int(v['totalGoldChange'])
            # 同步房费给base
            self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                  "todayGameCoinAdd": total_settlement_winner_billing,
                                  "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType13")})



    def jh_get_settlement_winners(self):
        """
       炸金花，获取小局的大赢家
       :return:
       """
        winners = {}
        max_win = 0
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['goldChange'] >= max_win:
                max_win = v['goldChange']

        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['goldChange'] == max_win:
                winners[k] = v
        return winners

    def jh_get_winner(self):
        """
        金花，获取大赢家
        :return:
        """
        winner = {}
        max_win = 0
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['totalGoldChange'] >= max_win:
                max_win = v['totalGoldChange']

        for k, v in self.chapters[self.cn]['playerOutGame'].items():
            if v['totalGoldChange'] == max_win:
                winner[k] = v
        return winner

    def jh_get_true_gold(self, account_id):
        """
        金花，获得玩家当前真实金币
        :param account_id:
        :return:
        """
        _chapter = self.get_current_chapter()
        for k, v in _chapter['playerInGame'].items():
            if v['entity'].id == account_id:
                return v['totalGoldChange']

        for k, v in _chapter["playerInGame"].items():
            if v['entity'].id == account_id:
                return v['totalGoldChange']


    # 炸金花总结算抽水
    def jh_total_settlement_billing(self):
        chapter = self.chapters[self.cn]
        total_settlement_winner = self.jh_get_winner()
        # 获取大赢家
        for k, v in total_settlement_winner.items():
            # k:account_id v:winner字典
            DEBUG_MSG('jh total_settlement_winner%s' % k)
            # 计算大赢家小局抽水
            total_settlement_winner_true_gold = self.jh_get_true_gold(k)
            total_settlement_winner_billing = total_settlement_winner_true_gold * self.info['totalSettlementBilling']
            DEBUG_MSG('RoomType1 settlement_winner billing%s' % total_settlement_winner_billing)
            v['totalGoldChange'] -= total_settlement_winner_billing
            v['totalGoldChange'] = int(v['totalGoldChange'])
            # 同步房费给base
            self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                  "todayGameCoinAdd": total_settlement_winner_billing,
                                  "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType1")})



    def nn_get_settlement_winners(self):
        """
        牛牛，获取小局的大赢家
        :return:
        """
        winners = {}
        max_win = 0
        DEBUG_MSG('RoomType4 aaaaaaaaaaaaa')
        DEBUG_MSG(self.chapters[self.cn])
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['goldChange'] >= max_win:
                max_win = v['goldChange']

        for k, v in self.chapters[self.cn]['playerOutGame'].items():
            if v['goldChange'] == max_win:
                winners[k] = v
        return winners

    def nn_get_winner(self):
        """
        牛牛，获取大赢家
        :return:
        """
        winner = {}
        max_win = 0
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['totalGoldChange'] >= max_win:
                max_win = v['totalGoldChange']

        for k, v in self.chapters[self.cn]['playerOutGame'].items():
            if v['totalGoldChange'] == max_win:
                winner[k] = v
        return winner

    def nn_get_true_gold(self, account_id):
        """
       牛牛，获得玩家当前真实金币
       :param account_id:
       :return:
       """
        _chapter = self.get_current_chapter()
        for k, v in _chapter['playerInGame'].items():
            if v['entity'].id == account_id:
                # return v['gold'] + v['baseSyncGoldChange'] + v['totalGoldChange']
                return v['totalGoldChange']

        for k, v in _chapter["playerOutGame"].items():
            if v['entity'].id == account_id:
                # return v['gold'] + v['baseSyncGoldChange'] + v['totalGoldChange']
                return v['totalGoldChange']
    # 牛牛总结算抽水
    def nn_total_settlement_billing(self):
        chapter = self.chapters[self.cn]
        total_settlement_winner = self.nn_get_winner()
        # 获取大赢家
        for k, v in total_settlement_winner.items():
            # k:account_id v:winner字典
            DEBUG_MSG('nn total_settlement_winner%s' % k)
            # 计算大赢家小局抽水
            total_settlement_winner_true_gold = self.nn_get_true_gold(k)
            total_settlement_winner_billing = total_settlement_winner_true_gold * self.info['totalSettlementBilling']
            DEBUG_MSG('RoomType4 settlement_winner billing%s' % total_settlement_winner_billing)
            v['totalGoldChange'] -= total_settlement_winner_billing
            v['totalGoldChange'] = int(v['totalGoldChange'])
            # 同步房费给base
            self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                  "todayGameCoinAdd": total_settlement_winner_billing,
                                  "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType4")})


    def mj_get_settlement_winners(self):
        """
        麻将，获取小局的大赢家
        :return:
        """
        winners = {}
        max_win = 0
        for k, v in self.chapters[self.cn][PLAYER_IN_GAME].items():
            if v['goldChange'] >= max_win:
                max_win = v['goldChange']

        for k, v in self.chapters[self.cn][PLAYER_IN_GAME].items():
            if v['goldChange'] == max_win:
                winners[k] = v
        return winners

    def mj_get_winner(self):
        """
        麻将，获取大赢家
        :return:
        """
        winner = {}
        max_win = 0
        for k, v in self.chapters[self.cn][PLAYER_IN_GAME].items():
            if v['totalGoldChange'] >= max_win:
                max_win = v['totalGoldChange']

        for k, v in self.chapters[self.cn][PLAYER_IN_GAME].items():
            if v['totalGoldChange'] == max_win:
                winner[k] = v
        return winner

    def normal_get_winner(self):
        """
        获取大赢家
        :return:
        """
        winner = {}
        max_win = 0
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['totalGoldChange'] >= max_win:
                max_win = v['totalGoldChange']

        for k, v in self.chapters[self.cn]['playerInGame'].items():
            if v['totalGoldChange'] == max_win:
                winner[k] = v
        return winner

    def mj_get_true_gold(self, account_id):
        """
        获得玩家当前真实金币
        :param account_id:
        :return:
        """
        _chapter = self.get_current_chapter()
        for k, v in _chapter[PLAYER_IN_GAME].items():
            if v['entity'].id == account_id:
                return v['gold'] + v['baseSyncGoldChange'] + v['totalGoldChange']

        for k, v in _chapter[PLAYER_OUT_GAME].items():
            if v['entity'].id == account_id:
                return v['gold'] + v['baseSyncGoldChange'] + v['totalGoldChange']

    # 麻将总结算抽水
    def mj_total_settlement_billing(self):
        chapter = self.chapters[self.cn]
        total_settlement_winner = self.mj_get_winner()
        # 获取大赢家
        for location_index, v in total_settlement_winner.items():
            total_settlement_winner_account_id = v['entity'].id

            # k:account_id v:winner字典
            DEBUG_MSG('mj total_settlement_winner%s' % total_settlement_winner_account_id)
            # 计算大赢家小局抽水
            total_settlement_winner_true_gold = self.mj_get_true_gold(total_settlement_winner_account_id)
            total_settlement_winner_billing = total_settlement_winner_true_gold * self.info['totalSettlementBilling']
            DEBUG_MSG('RoomType12 settlement_winner billing%s' % total_settlement_winner_billing)
            v['totalGoldChange'] -= total_settlement_winner_billing
            v['totalGoldChange'] = int(v['totalGoldChange'])
            # 同步房费给base
            self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                  "todayGameCoinAdd": total_settlement_winner_billing,
                                  "userId": v["entity"].info["userId"], "roomType": Const.get_name_by_type("RoomType12")})

    def nn_lottery(self):
        chapter = self.chapters[self.cn]
        # 福卡抽奖
        lottery_in_fu_ka = self.mj_fu_ka_lottery()
        # 找到大赢家
        winner = self.mj_get_winner()

        # 给web使用的抽奖信息
        all_bill = {}
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            all_bill[k] = {"userId": v["entity"].info["userId"], "todayGameCoinAdd": 0,
                           'winner': 1 if k in winner else 0, "score": v['totalGoldChange']}

        # 大赢家比赛分抽奖
        if self.info["winnerBilling"]:
            for k, v in winner.items():
                for i in range(0, len(self.info["winnerBilling"])):
                    if self.info["winnerBilling"][i]['interval'][0] <= v["totalGoldChange"] <= \
                            self.info["winnerBilling"][i]['interval'][1]:
                        winner_billing_consume = self.info["winnerBilling"][i]['consume']
                        v["totalGoldChange"] -= winner_billing_consume
                        # v["gold"] -= winnerBillingConsume
                        v["winnerBilling"] = -winner_billing_consume

        # 其余玩家比赛分抽奖
        if self.info['otherBilling']:
            for k, v in chapter['playerInGame'].items():
                # 如果大赢家开启，其他玩家不扣大赢家
                if k in winner and self.info["winnerBilling"]:
                    continue
                for i in range(0, len(self.info["otherBilling"])):
                    if self.info["otherBilling"][i]['interval'][0] <= v["totalGoldChange"] <= \
                            self.info["otherBilling"][i]['interval'][1]:
                        other_billing_consume = self.info["otherBilling"][i]['consume']
                        v["totalGoldChange"] -= other_billing_consume
                        # v["gold"] -= otherBillingConsume
                        v["otherBilling"] = -other_billing_consume

        # 统计总房费
        total_billing = 0
        for k, v in chapter['playerInGame'].items():
            self.debug_msg('k:%s,otherBilling:%s,winnerBilling:%s' % (k, v['otherBilling'], v['winnerBilling']))
            total_billing += abs(v['otherBilling']) + abs(v['winnerBilling'])

        # 总房费不为 0
        if total_billing != 0:
            # 平均房费
            average_billing = total_billing / len(chapter['playerInGame'])
            # 发送给 base 的抽奖信息
            account_lottery = []
            self.debug_msg('total_billing:%s,average_billing:%s' % (total_billing, average_billing))
            for k, v in chapter['playerInGame'].items():
                # 同步房费给base
                self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                      "todayGameCoinAdd": average_billing, "userId": v["entity"].info["userId"]})

                # 统计要给 web 用到的房费信息
                all_bill[k]["todayGameCoinAdd"] += abs(v['otherBilling']) + abs(v['winnerBilling'])
                # 统计奖品
                # 如果该用户参加过福卡抽奖，不再参加比赛币抽奖
                # 如果用户抽奖消耗为0，不参与比赛比抽奖
                if v["entity"].info["userId"] not in lottery_in_fu_ka and \
                        (v['otherBilling'] + v['winnerBilling']) != 0:
                    # 发送奖品信息给客户端展示
                    awards = self.gen_award()
                    select = self.gen_selected(awards)
                    self.callClientFunction(v['entity'].id, 'Awards',
                                            {"awards": awards, 'selected': select, "consume": 0,
                                             "scoreVisible": self.server_config["scoreVisible"],
                                             "WinnerConsume": abs(v['otherBilling']) + abs(v['winnerBilling'])})
                    # 发送奖品信息给 base 发奖
                    lottery_type = -1
                    if select["type"] == 'gold':
                        lottery_type = 0
                    elif select["type"] == 'diamond':
                        lottery_type = 1
                    account_lottery.append({"accountDBID": v["entity"].info["userId"], "consumeLuckyCard": 0,
                                            "count": select["count"], "type": lottery_type})

            # 同步奖品信息给base
            self.base.cellToBase({"func": "Lottery", "args": account_lottery})


        # 同步 web 需要用到的房费信息
        self.base.cellToBase(
            {"func": "todayBillStatic", "teaHouseId": self.info["teaHouseId"], "bill": list(all_bill.values())})

    def mj_lottery(self):
        chapter = self.chapters[self.cn]
        # 福卡抽奖
        lottery_in_fu_ka = self.mj_fu_ka_lottery()
        # 找到大赢家
        winner = self.mj_get_winner()

        # 给web使用的抽奖信息
        all_bill = {}
        for k, v in self.chapters[self.cn][PLAYER_IN_GAME].items():
            all_bill[k] = {"userId": v["entity"].info["userId"], "todayGameCoinAdd": 0,
                           'winner': 1 if k in winner else 0, "score": v['totalGoldChange']}

        # 大赢家比赛分抽奖
        if self.info["winnerBilling"]:
            for k, v in winner.items():
                for i in range(0, len(self.info["winnerBilling"])):
                    if self.info["winnerBilling"][i]['interval'][0] <= v["totalGoldChange"] <= \
                            self.info["winnerBilling"][i]['interval'][1]:
                        winner_billing_consume = self.info["winnerBilling"][i]['consume']
                        v["totalGoldChange"] -= winner_billing_consume
                        # v["gold"] -= winnerBillingConsume
                        v["winnerBilling"] = -winner_billing_consume

        # 其余玩家比赛分抽奖
        if self.info['otherBilling']:
            for k, v in chapter[PLAYER_IN_GAME].items():
                # 如果大赢家开启，其他玩家不扣大赢家
                if k in winner and self.info["winnerBilling"]:
                    continue
                for i in range(0, len(self.info["otherBilling"])):
                    if self.info["otherBilling"][i]['interval'][0] <= v["totalGoldChange"] <= \
                            self.info["otherBilling"][i]['interval'][1]:
                        other_billing_consume = self.info["otherBilling"][i]['consume']
                        v["totalGoldChange"] -= other_billing_consume
                        # v["gold"] -= otherBillingConsume
                        v["otherBilling"] = -other_billing_consume

        # 统计总房费
        total_billing = 0
        for k, v in chapter[PLAYER_IN_GAME].items():
            self.debug_msg('k:%s,otherBilling:%s,winnerBilling:%s' % (k, v['otherBilling'], v['winnerBilling']))
            total_billing += abs(v['otherBilling']) + abs(v['winnerBilling'])

        # 总房费不为 0
        if total_billing != 0:
            # 平均房费
            average_billing = total_billing / len(chapter[PLAYER_IN_GAME])
            # 发送给 base 的抽奖信息
            account_lottery = []
            self.debug_msg('total_billing:%s,average_billing:%s' % (total_billing, average_billing))
            for k, v in chapter[PLAYER_IN_GAME].items():
                # 同步房费给base
                self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                      "todayGameCoinAdd": average_billing, "userId": v["entity"].info["userId"]})

                # 统计要给 web 用到的房费信息
                all_bill[k]["todayGameCoinAdd"] += abs(v['otherBilling']) + abs(v['winnerBilling'])
                # 统计奖品
                # 如果该用户参加过福卡抽奖，不再参加比赛币抽奖
                # 如果用户抽奖消耗为0，不参与比赛比抽奖
                if v["entity"].info["userId"] not in lottery_in_fu_ka and \
                        (v['otherBilling'] + v['winnerBilling']) != 0:
                    # 发送奖品信息给客户端展示
                    awards = self.gen_award()
                    select = self.gen_selected(awards)
                    self.callClientFunction(v['entity'].id, 'Awards',
                                            {"awards": awards, 'selected': select, "consume": 0,
                                             "scoreVisible": self.server_config["scoreVisible"],
                                             "WinnerConsume": abs(v['otherBilling']) + abs(v['winnerBilling'])})
                    # 发送奖品信息给 base 发奖
                    lottery_type = -1
                    if select["type"] == 'gold':
                        lottery_type = 0
                    elif select["type"] == 'diamond':
                        lottery_type = 1
                    account_lottery.append({"accountDBID": v["entity"].info["userId"], "consumeLuckyCard": 0,
                                            "count": select["count"], "type": lottery_type})

            # 同步奖品信息给base
            self.base.cellToBase({"func": "Lottery", "args": account_lottery})

        # 同步 web 需要用到的房费信息
        self.base.cellToBase(
            {"func": "todayBillStatic", "teaHouseId": self.info["teaHouseId"], "bill": list(all_bill.values())})

    def normal_lottery(self):
        chapter = self.chapters[self.cn]
        # 福卡抽奖
        lottery_in_fu_ka = self.normal_fu_ka_lottery()
        # 找到大赢家
        winner = self.normal_get_winner()

        # 给web使用的抽奖信息
        all_bill = {}
        for k, v in self.chapters[self.cn]['playerInGame'].items():
            all_bill[k] = {"userId": v["entity"].info["userId"], "todayGameCoinAdd": 0,
                           'winner': 1 if k in winner else 0, "score": v['totalGoldChange']}

        # 大赢家比赛分抽奖
        if self.info["winnerBilling"]:
            for k, v in winner.items():
                for i in range(0, len(self.info["winnerBilling"])):
                    if self.info["winnerBilling"][i]['interval'][0] <= v["totalGoldChange"] <= \
                            self.info["winnerBilling"][i]['interval'][1]:
                        winner_billing_consume = self.info["winnerBilling"][i]['consume']
                        v["totalGoldChange"] -= winner_billing_consume
                        v["gold"] -= winner_billing_consume
                        v["winnerBilling"] = -winner_billing_consume

        # 其余玩家比赛分抽奖
        if self.info['otherBilling']:
            for k, v in chapter['playerInGame'].items():
                # 如果大赢家开启，其他玩家不扣大赢家
                if k in winner and self.info["winnerBilling"]:
                    continue
                for i in range(0, len(self.info["otherBilling"])):
                    if self.info["otherBilling"][i]['interval'][0] <= v["totalGoldChange"] <= \
                            self.info["otherBilling"][i]['interval'][1]:
                        other_billing_consume = self.info["otherBilling"][i]['consume']
                        v["totalGoldChange"] -= other_billing_consume
                        v["gold"] -= other_billing_consume
                        v["otherBilling"] = -other_billing_consume

        # 统计总房费
        total_billing = 0
        for k, v in chapter['playerInGame'].items():
            self.debug_msg('k:%s,otherBilling:%s,winnerBilling:%s' % (k, v['otherBilling'], v['winnerBilling']))
            total_billing += abs(v['otherBilling']) + abs(v['winnerBilling'])

        # 总房费不为 0
        if total_billing != 0:
            # 平均房费
            average_billing = total_billing / len(chapter['playerInGame'])
            # 发送给 base 的抽奖信息
            account_lottery = []
            self.debug_msg('total_billing:%s,average_billing:%s' % (total_billing, average_billing))
            for k, v in chapter['playerInGame'].items():
                # 同步房费给base
                self.base.cellToBase({"func": "todayGameBilling", "teaHouseId": self.info["teaHouseId"],
                                      "todayGameCoinAdd": average_billing, "userId": v["entity"].info["userId"]})

                # 统计要给 web 用到的房费信息
                all_bill[k]["todayGameCoinAdd"] += abs(v['otherBilling']) + abs(v['winnerBilling'])

                # 统计奖品
                # 如果该用户参加过福卡抽奖，不再参加比赛币抽奖
                if v["entity"].info["userId"] not in lottery_in_fu_ka and \
                        (v['otherBilling'] + v['winnerBilling']) != 0:
                    # 发送奖品信息给客户端展示
                    awards = self.gen_award()
                    select = self.gen_selected(awards)
                    self.callClientFunction(v['entity'].id, 'Awards',
                                            {"awards": awards, 'selected': select, "consume": 0,
                                             "scoreVisible": self.server_config["scoreVisible"],
                                             "WinnerConsume": abs(v['otherBilling']) + abs(v['winnerBilling'])})
                    # 发送奖品信息给 base 发奖
                    lottery_type = -1
                    if select["type"] == 'gold':
                        lottery_type = 0
                    elif select["type"] == 'diamond':
                        lottery_type = 1
                    account_lottery.append({"accountDBID": v["entity"].info["userId"], "consumeLuckyCard": 0,
                                            "count": select["count"], "type": lottery_type})

            # 同步奖品信息给base
            self.base.cellToBase({"func": "Lottery", "args": account_lottery})

        # 同步 web 需要用到的房费信息
        self.base.cellToBase(
            {"func": "todayBillStatic", "teaHouseId": self.info["teaHouseId"], "bill": list(all_bill.values())})
