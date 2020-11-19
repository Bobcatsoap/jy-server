# -*- coding: utf-8 -*-
import copy
import math
import socket
import struct

from KBEDebug import *
import random
import json
import datetime
import time
import Bots
import Const
import DBCommand
import KBEngine

from HTTPServer import HttpRequest
from TeaHouse import TeaHousePlayerLevel
import TeaHouse
from enum import IntEnum
import re
import collections


def account_config():
    return Const.ServerGameConfigJson.config_json['Account']


# 玩游戏的阶段
class PlayerStage(IntEnum):
    FREE = 0
    NO_READY = 1
    WATCHING = 2
    READY = 3
    PLAYING = 4


def remove_emoji(str):
    try:
        highpoints = re.compile(u'[\U00010000-\U0010ffff]')
        return highpoints.sub('*', str)
    except:
        DEBUG_MSG("del_emoji fail: %s" % str)
    return "*"


class Account(KBEngine.Proxy):
    """
    账号实体
    客户端登陆到服务端后，服务端将自动创建这个实体，通过这个实体与客户端进行账户相关交互
    """

    # 是否是机器人
    isBot = 0
    # 名字
    name = ""
    # 账号id
    userId = 0
    # 金币数
    gold = 0
    # 参与过的房间
    rooms = {}
    # 头像地址
    headImageUrl = ""
    # 性别
    gender = 0
    # 钻石数量
    roomCard = 10
    # 元宝
    goldIngot = 10
    # 经度
    longitude = 0
    # 纬度
    latitude = 0
    # 是否开外挂
    addOn = 0
    # 签到时间
    attendanceDataTime = 0
    # 日分享次数
    dayShareCount = 0
    dayShareDateTime = 0
    # 代理类型
    # 1：群主 2：高级代理 3：总代理
    proxyType = 0
    # 是否冻结
    frozen = 0
    # 位置
    address = ""
    # 邀请码
    invitation_code = 0
    # 上级
    belong_to = 0
    # =========================================
    account_info = {}
    # 代开房间
    substituteRooms = []
    # 今天祈福次数
    blessCountToday = 0
    security_code = ""
    phone = ""
    # room base 实体
    scene = None
    destroy_on_lose_cell = False
    ip = "0"
    account_mgr = None
    room_mgr = None
    tea_house_mgr = None
    create_cell_cb = None
    client_open_tea_house_state = -1
    client_open_gold_session_state = -1
    client_open_challenge_state = -1
    want_binding_phone = -1
    # 粉丝列表
    friends = []
    # 赠送金币记录列表
    giveGoldRecords = []
    todoList = []
    chats = {}
    chat_log = {}
    sys_notice = {}
    #
    bankerHistory = []
    # 玩家在游戏中的状态
    playing_stage = PlayerStage.FREE
    room_chapter_count = 0
    cur_chapter_count = 0
    losing_streak_count = 0
    # 一天发几手好牌控制
    good_pai_count = 0
    last_good_pai_tick = 0
    online_state = False
    myPrize = {0: 0, 1: 0}
    log_filter = set()
    # 定义一个类变量，存放查询用的房间实体
    history_room = {}
    partnerSwitch = 0
    gpsLocation = False
    today_commission = 0
    history_commission = 0
    surplus_commission = 0


    def __init__(self):
        KBEngine.Proxy.__init__(self)
        # self.databaseID = 500000 + self.databaseID   # TODO 自添加
        self.account_mgr = KBEngine.globalData["AccountMgr"].mgr
        self.room_mgr = KBEngine.globalData["RoomManager"].mgr
        self.tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
        self.gold_session_mgr = KBEngine.globalData['GoldSessionManager'].mgr
        self.challenge_mgr = KBEngine.globalData['ChallengeAreaManager'].mgr
        if self.is_new_account():
            self.account_init()
            # 进行微信登陆修正
            # self.wx_login_correct_find_old_account()
        else:
            self.account_update()
        self._timer = -1
        self._join_verification_failed = -1
        self.get_account_info()
        self.redeem_code = 0
        self.redeem_ticket = 0

    def wx_login_correct_find_old_account(self):
        """
        修正微信登陆。如果这个登陆的微信用户之前已经用另一个app id登陆，则将这个微信app id对应到原账户上
        """

        def query_name_callback(result, rows, insertid, error):
            if not result:
                return
            id_s = []
            for info in result:
                id = int(info[0])
                if id != self.databaseID:
                    id_s.append(id)
            DEBUG_MSG('query_name_callback id_s%s' % id_s)
            # 如果找到了多个同名用户，则不处理
            if len(id_s) > 2:
                return
            old_db_id = id_s[0]
            # 通过
            self.wx_login_correct_find_old_account_login_info(old_db_id)

        command = 'select id from tbl_account where sm_name="%s"' % self.name
        DEBUG_MSG('wx_login_correct query name command%s' % command)
        KBEngine.executeRawDatabaseCommand(command, query_name_callback)
        pass

    def wx_login_correct_find_old_account_login_info(self, old_account_db_id):
        """
        查找绑定了旧帐户的微信信息

        """

        def query_name_callback(result, rows, insertid, error):
            if not result:
                return
            other_login_name_s = []
            for info in result:
                login_name = info[0]
                if login_name == self.__ACCOUNT_NAME__:
                    continue
                other_login_name_s.append(login_name)
            DEBUG_MSG('query_name_callback other_login_name%s' % other_login_name_s)
            if len(other_login_name_s) > 2:
                return
            other_login_name = str(other_login_name_s[0], encoding='utf-8')
            if 'w*' not in other_login_name:
                return
            self.wx_login_correct_delete_other_login(other_login_name, self.__ACCOUNT_NAME__, old_account_db_id)

        command = 'select accountName,entityDBID from kbe_accountinfos where entityDBID=%s' % old_account_db_id
        DEBUG_MSG('wx_login_correct_find_old_account_login_info command%s' % command)
        KBEngine.executeRawDatabaseCommand(command, query_name_callback)
        pass

    def wx_login_correct_delete_other_login(self, other_login, new_login, old_account_db_id):
        def delete_callback(result, rows, insertid, error):
            DEBUG_MSG('wx_login_correct_delete_other_login success')
            self.wx_login_correct_new_login_mapping_to_old_account(old_account_db_id)

        # 删除旧的微信登录信息
        command = 'DELETE FROM kbe_accountinfos WHERE accountName="%s"' % other_login
        DEBUG_MSG('wx_login_correct_delete_other_login command%s' % command)
        KBEngine.executeRawDatabaseCommand(command, delete_callback)

    def wx_login_correct_new_login_mapping_to_old_account(self, old_account_db_id):
        def mapping_callback(result, rows, insertid, error):
            DEBUG_MSG('wx_login_correct_new_login_mapping_to_old_account success')
            self.call_client_func('pleaseRestartClient', {})

        command = 'UPDATE kbe_accountinfos SET entityDBID=%s where accountName="%s"' % (
            old_account_db_id, self.__ACCOUNT_NAME__)
        DEBUG_MSG('wx_login_correct_new_login_mapping_to_old_account command%s' % command)
        KBEngine.executeRawDatabaseCommand(command, mapping_callback)

    def req_wx_name(self, _open_id):
        """
        请求微信ID,必须登录时调用
        """
        _access_token = self.getClientDatas()[0].decode()
        DEBUG_MSG('Account id %s wx_token = %s' % (self.id, _access_token))
        if _access_token != "":
            try:
                _user_info = HttpRequest.req_wx_user_info(_access_token, _open_id)
                INFO_MSG("[Account %i] __init__: wx_user_info=%s" % (self.id, _user_info))
                _dic = json.loads(_user_info)
                self.name = _dic["nickname"]
                self.headImageUrl = _dic["headimgurl"]
                self.name = remove_emoji(self.name)
                unionid = _dic["unionid"]

                def _fun(result, rows, insertid, error):
                    if len(result) != 0:
                        _user_id = int(str(result[0][2], 'utf-8'))
                        self.binding_proxy_by_user_id(_user_id)

                _command = "SELECT * FROM `invite_code_relations` WHERE `unionid`='%s'" % unionid
                DEBUG_MSG(_command)
                KBEngine.executeRawDatabaseCommand(_command, _fun)
            except Exception as e:
                self.name = ""
                self.headImageUrl = ""
                DEBUG_MSG('req_wx_name id %s except = %s' % (self.id, e))

    def account_init(self):
        """
        登录
        """
        DEBUG_MSG("account_init-eeeeeeeee------> userId %s" % self.databaseID)
        if not hasattr(self, '__ACCOUNT_NAME__'):
            return
        _name = self.__ACCOUNT_NAME__
        INFO_MSG("[Account %i] name=%s" % (self.id, _name))
        if '*' in _name:
            _l = list()
            _l.append(_name[0])
            _l.append(_name[2:len(_name)])
            if _l[0] == 'w':
                # 微信
                self.req_wx_name(_l[1])
        # 游客登陆
        else:
            # self.name = "游客" + self.databaseID
            self.name = "游客" + str(self.databaseID)
            self.headImageUrl = Const.AccountInfo.HeadImageUrl
        self.gold = int(Const.GameConfigJson.config_json['Hall']['giftGoldCount'])
        self.roomCard = float(Const.GameConfigJson.config_json['Hall']['giftDiamondCount'])
        self.goldIngot = float(Const.ServerGameConfigJson.config_json["Hall"]['giftGoldIngotCount'])
        self.userId = self.databaseID
        DEBUG_MSG("account_init-------> userId %s" % self.userId)
        self.writeToDB()

    def account_update(self):
        """
        没有名字时，获取名字
        """
        if self.name:
            return
        if not hasattr(self, '__ACCOUNT_NAME__'):
            return
        _name = self.__ACCOUNT_NAME__
        INFO_MSG("[Account %i] name=%s" % (self.id, _name))
        if '*' in _name:
            _l = list()
            _l.append(_name[0])
            _l.append(_name[2:len(_name)])
            if _l[0] == 'w':
                # 微信
                self.req_wx_name(_l[1])

    def is_new_account(self):
        if not self.isBot and not self.userId:
            return True
        return False

    @staticmethod
    def set_control_param(_entity_id, good_pai_count, last_tick):
        account_entity = KBEngine.entities[_entity_id]
        account_entity.good_pai_count = good_pai_count
        account_entity.last_good_pai_tick = last_tick
        # DEBUG_MSG("Account::set_control_param: %s %s %s." % (_entity_id, good_pai_count, last_tick))

    def check_update_good_pai_control(self):
        """检查并更新好牌控制参数
        检查玩家发好牌时间是否是今天，如果不是今天就清空好牌计数，并设为今天
        """
        current_time = time.localtime(self.last_good_pai_tick)
        player_time = time.localtime(time.time())
        if current_time.tm_yday != player_time.tm_yday:
            self.last_good_pai_tick = time.time()
            self.good_pai_count = 0
        DEBUG_MSG("check_update_good_pai_control: %s %s %s." % (
            self.databaseID, self.good_pai_count, self.last_good_pai_tick))

    def get_account_info(self):
        """
        :return:
        """
        # 实体id
        self.account_info["id"] = self.id
        # 用户uID
        self.account_info["userId"] = self.userId
        # 游戏中的名字
        self.account_info["name"] = self.name
        # 是否是机器人
        self.account_info["isBot"] = self.isBot
        # !--玩家头像地址 -->
        self.account_info["headImageUrl"] = self.headImageUrl
        # !--玩家性别 -->
        self.account_info["gender"] = self.gender
        # 玩家的dataBaseId
        self.account_info["dataBaseId"] = self.databaseID
        # 玩家的外挂状态
        self.account_info["addOn"] = self.addOn
        # 金币数量
        self.account_info["gold"] = self.gold
        # 经纬度
        self.account_info["longitude"] = self.longitude
        self.account_info["latitude"] = self.latitude
        # ip
        if self.isBot and self.ip == '0':
            self.ip = self.rand_ip()
        self.account_info["ip"] = self.ip
        # 坐庄记录
        self.account_info["bankerHistory"] = self.bankerHistory
        self.account_info["losingstreak"] = self.losing_streak_count
        # 好牌控制
        self.account_info["goodPaiCount"] = self.good_pai_count

        return self.account_info

    def on_login(self):
        self.account_mgr.add(self)

    def on_offline(self):
        self.account_mgr.remove(self)

    # --------------------------------------------------------------------------------------------
    #                              BASE中定义的方法
    # --------------------------------------------------------------------------------------------

    def createCell(self, roomEntity, cb=None):
        """
        创建cell部分
        :param roomEntity:所在房间的roomEntity
        """
        # 如果房间不存在，返回
        if not roomEntity or not roomEntity.cell:
            return
        DEBUG_MSG("Account func:on createCell")
        self.create_cell_cb = cb
        # API：创建该实体的cell部分
        self.createCellEntity(roomEntity.cell)
        self.scene = roomEntity

    def onCellInit(self):
        """
        Account的CELL实体创建成功,账号基本信息也已传送过去
        :return:
        """

        if self.isBot == 1:
            self.scene.cell.baseToCell({"func": "onEnter", "id": self.id})
            return
        self.cell.baseToCell({"func": "retRoomCard", "roomCard": self.roomCard})
        self.cell.baseToCell({'func': 'retTodayBlessCount', 'todayBlessCount': self.blessCountToday})
        # 如果此时房间被销毁，不再通知进入房间
        if self.create_cell_cb and self.cell and self.scene and self.scene.cell:
            self.create_cell_cb()

    def writeRooms(self, room_entity):
        """
        所参与的游戏房间号，按游戏类型分类
        {'RoomType12': [239, 238, 237, 236]}
        """
        if room_entity.info["type"] not in self.rooms:
            _room_ids = []
        else:
            _room_ids = self.rooms[room_entity.info["type"]]
        if int(room_entity.databaseID) == 0:
            return
        if room_entity.databaseID in _room_ids:
            return
        if room_entity.is_tea_house_room():
            return
        _room_ids.insert(0, room_entity.databaseID)
        if len(_room_ids) >= Const.Record.record_limit:
            _room_ids.pop(-1)
        self.rooms[room_entity.info["type"]] = _room_ids
        # self.writeToDB()

    def reqAccountMutableInfo(self, pyList):
        """
        :param pyList: 请求的字段列表
        :return:
        """
        _dic = {}
        DEBUG_MSG('base Account.py line 226  pylist value:%s pylist type %s' % (pyList, type(pyList)))
        for i in pyList:
            if i == "gold":
                _dic["gold"] = self.gold
            # 比赛分场发送玩家比赛分数额
            elif i == "gameCoin" and "teaHouseId" in self.scene.info and self.scene.info['teaHouseId'] != -1:
                tea_house_id = self.scene.info["teaHouseId"]
                game_coin = self.get_game_coin(tea_house_id)
                _dic["gameCoin"] = game_coin

                _dic["controlScore"] = [0, 0, 0, False]
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
                if tea_house_entity:
                    control_val = tea_house_entity.get_need_control_score(self.databaseID)
                    _dic["controlScore"] = list(control_val)
                    DEBUG_MSG('reqAccountMutableInfo %s' % _dic["controlScore"])

        self.cell.baseToCell({"func": "retAccountMutableInfo", "dic": _dic})

    def refresh_lucky_card_to_room(self):
        """
        发送福卡信息到cell
        :return:
        """
        try:
            if self.scene and 'teaHouseId' in self.scene.info:
                tea_house_id = self.scene.info['teaHouseId']
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
                if tea_house_entity:
                    t_player = tea_house_entity.get_tea_house_player(self.databaseID)
                    lucky_card = t_player.lucky_card
                    self.cell.baseToCell({'func': 'refreshLuckyCard', 'luckyCardCount': lucky_card})
        except AttributeError as e:
            ERROR_MSG('Account::refresh_gold_to_room %s' % e)

    def add_chapter_count(self, tea_house_id, count):
        """
        一般是游戏结束，统计玩家的游戏局数，增1
        """
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            tea_house_entity.add_player_chapter_count(self.databaseID, count)

    def setChallengeResult(self, pyDic):
        """
        cell---->base
        :param pyDic:
        :return:
        """
        self.challenge_mgr.setChallengeResult(self.databaseID, pyDic)

    def setAccountMutableInfo(self, pyDic):
        """
        cell---->base
        :param pyDic:
        :return:
        """
        for key in pyDic.keys():
            DEBUG_MSG('[setAccountMutableInfo key %s]------>cellToBase jsonData %s' % (str(key), str(pyDic)))
            if key == "gold":
                self.gold = int(pyDic["gold"])
                self.ret_gold()
                self.ret_gold()
            elif key == 'score':
                self.gold = int(pyDic["score"])
                self.ret_gold()
            elif key == "gameCoin":
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(int(pyDic["teaHouseId"]))
                # 如果比赛币功能没开，不同步比赛币
                if tea_house_entity:
                    # if not tea_house_entity.gameCoinSwitch:
                    #     return
                    self.gold = int(pyDic["gameCoin"])
                    DEBUG_MSG('[setAccountMutableInfo]------>cellToBase self.gold %s' % str(self.gold))
                    tea_house_entity.set_game_coin(self.databaseID, int(pyDic["gameCoin"]))
                    self.ret_gold()

    def set_account_total_gold_change(self, pyDic):
        """
        同步房间内分数改变
        cell---->base
        :param pyDic:
        :return:
        """
        _type = pyDic['type']
        _tea_house_id = pyDic['teaHouseId']
        _total_gold_change = pyDic['totalGoldChange']
        DEBUG_MSG('[set_account_total_gold_change type %s]------>cellToBase jsonData %s %s' % (str(_type), _tea_house_id, _total_gold_change))
        if _type == 'gold':
            self.gold += _total_gold_change
            self.ret_gold()
        elif _type == 'gameCoin':
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_tea_house_id)
            DEBUG_MSG('[set_account_total_gold_change]------>tea_house_entity.gameCoinSwitch %s' % (str(tea_house_entity.gameCoinSwitch)))
            if tea_house_entity:
                # 如果比赛币功能没开，不同步比赛币
                # if not tea_house_entity.gameCoinSwitch:
                #     return
                player = tea_house_entity.get_tea_house_player(self.databaseID)
                _game_coin = player.game_coin + _total_gold_change
                # TODO 修改 同步比赛分到大厅金币
                self.gold = _game_coin
                tea_house_entity.set_game_coin(self.databaseID, _game_coin)
                self.ret_gold()

    # --------------------------------------------------------------------------------------------
    #                              通信相关的方法
    # --------------------------------------------------------------------------------------------

    def cellToBase(self, pyDic):
        """
        :param pyDic:
        :return:
        """
        _func_name = pyDic["func"]
        DEBUG_MSG('[Account id %s]------>cellToBase jsonData %s %s' % (self.id, _func_name, pyDic))
        if _func_name == "onCellInit":
            self.onCellInit()
        elif _func_name == "reqAccountMutableInfo":
            _l = pyDic["list"]
            self.reqAccountMutableInfo(_l)
        # TODO 设置玩家金币数量
        elif _func_name == "setAccountMutableInfo":
            _p = pyDic["dic"]
            self.setAccountMutableInfo(_p)
        elif _func_name == "setChallengeInfo":
            self.setChallengeResult(pyDic)
        elif _func_name == "AddChapterCount":
            self.add_chapter_count(int(pyDic["teaHouseId"]), 1)
        elif _func_name == 'bless':
            self.bless()
        elif _func_name == 'syncGameCoin':
            self.sync_game_coin(int(pyDic['teaHouseId']))
        elif _func_name == 'setAccountTotalGoldChange':
            # 同步房间内金币变化
            self.set_account_total_gold_change(pyDic["dic"])
        elif _func_name == 'AppendBankerHistory':
            # 追加本局是否坐庄,最多20条
            self.bankerHistory.append(pyDic["banker"])
            if len(self.bankerHistory) > 20:
                del self.bankerHistory[:-20]
        elif _func_name == 'setLosingStreakCount':
            self.losing_streak_count = int(pyDic["count"])
            DEBUG_MSG('setLosingStreakCount account_db_id %s count %s' % (self.databaseID, self.losing_streak_count))
        elif _func_name == 'reqTeaHouseChapterCount':
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(int(pyDic["teaHouseId"]))
            if tea_house_entity:
                player = tea_house_entity.get_tea_house_player(self.databaseID)
                if player:
                    self.cell.baseToCell({"func": "retTeaHouseChapterCount", "dic": player.chapter_count})
        elif _func_name == 'updatePlayingStage':
            self.playing_stage = PlayerStage(pyDic["stage"])
            self.room_chapter_count = pyDic["maxChapterCount"]
            self.cur_chapter_count = pyDic["curChapterCount"]
            DEBUG_MSG("updatePlayingStage %s" % pyDic)
        elif _func_name == 'reconnectRoom':
            # 通知客户端返回房间
            self.call_client_func("reconnectRoom", pyDic['args'])
        elif _func_name == 'setDayGoodPaiCount':
            good_pai_count = int(pyDic['goodPaiCount'])
            if self.good_pai_count != good_pai_count:
                self.good_pai_count = good_pai_count
                DBCommand.update_good_pai_count(self.databaseID, good_pai_count, self.last_good_pai_tick)
            # DEBUG_MSG("setDayGoodPaiCount: %s %s %s." % (self.databaseID, self.good_pai_count, self.last_good_pai_tick))
        elif _func_name == 'AddPrize':
            _p = pyDic["dic"]
            _p["player_id"] = self.databaseID
            _p["player_name"] = self.name
            DBCommand.add_challenge_prize(_p)
        elif _func_name == 'reqChallengeWinControl':
            data = self.challenge_mgr.get_challenge_result_control(self.databaseID, pyDic)
            self.cell.baseToCell({"func": "retChallengeWinControl", "dic": data})

    def clientToBase(self, jsonData):
        """
        TODO E创建房间函数
        :param jsonData:
        :return:
        """
        DEBUG_MSG('[Account id %s]------>clientReq jsonData %s' % (self.id, jsonData))
        _py_dic = json.loads(jsonData)
        _func_name = _py_dic["func"]
        _args = _py_dic["args"]
        if _func_name == "CreateRoom":
            # 创建房间
            # 准备关服维护
            if self.room_mgr.is_snoring_all_room():
                self.call_client_func("Notice", [self.room_mgr.snoring_msg])
                return

            if self.check_have_challenge_room(-1):
                return
            # TODO 开始创建房间
            self.room_mgr.create_room(self.databaseID, _args)
        elif _func_name == "JoinRoom":
            # 准备关服维护
            if self.room_mgr.is_snoring_all_room():
                self.call_client_func("Notice", [self.room_mgr.snoring_msg])
                return

            if self.check_have_challenge_room(-1):
                return

            # TODO E加入房间
            if _args["roomType"] == "card":
                self.room_mgr.join_card_room(self, int(_args["number"]))
            # 加入冠名赛房间
            elif _args["roomType"] == "gameCoin":
                if self.scene:
                    # 已在房间，直接重连
                    if self.scene.roomId == int(_args["number"]):
                        _args = {"type": self.scene.info["type"], "roomType": self.scene.info["roomType"],
                                 "roomId": self.scene.info["roomId"]}
                        self.call_client_func("reconnectRoom", _args)
                        return
                    else:
                        # 准备进另外一个房间,提示退出房间
                        room_info = dict()
                        room_info["number"] = _args["number"]
                        room_info["anonymity"] = _args["anonymity"]
                        room_info["roomType"] = _args["roomType"]
                        room_info["type"] = _args["type"]
                        room_info["teaHouseId"] = _args["teaHouseId"]
                        room_info["quickJoin"] = _args["quickJoin"]
                        self.call_client_func("HaveAnotherRoom", room_info)
                        return

                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
                room_id = int(_args["number"])
                if room_id > 0:
                    if not tea_house_entity.get_room_by_id(room_id):
                        self.call_client_func("Notice", ["无法加入此房间，房间已销毁"])
                        return

                # 验证是否在此茶楼中
                if self.userId not in tea_house_entity.memberInfo:
                    self.call_client_func("Notice", ["无法加入此房间，你已不在此茶楼中"])
                    return
                if tea_house_entity.is_freeze_player(self.userId):
                    self.call_client_func("Notice", ["无法加入此房间，你已被冻结"])
                    return
                # 如果冠名赛已经打烊，提示冠名赛打烊，进入房间失败
                if tea_house_entity and tea_house_entity.isSnoring == 1:
                    self.call_client_func("join_room_failed", [_args["type"], "gameCoin", int(_args["number"])])
                    self.call_client_func("Notice", ["冠名赛已打烊，请联系群主"])
                    return
                if tea_house_entity and _args["type"] in tea_house_entity.snoring_games:
                    self.call_client_func("join_room_failed", [_args["type"], "gameCoin", int(_args["number"])])
                    self.call_client_func("Notice", ["游戏已关闭"])
                    return

                self.room_mgr.join_game_coin_room(self, _args["type"], int(_args["number"]),
                                                  anonymity=_args["anonymity"],
                                                  quick_join=_args["quickJoin"], teaHouseId=_args["teaHouseId"])
            # 加入普通冠名赛房间
            elif _args['roomType'] == 'normalGameCoin':
                if self.scene:
                    # 已在房间，直接重连
                    if self.scene.roomId == int(_args["number"]):
                        _args = {"type": self.scene.info["type"], "roomType": self.scene.info["roomType"],
                                 "roomId": self.scene.info["roomId"]}
                        self.call_client_func("reconnectRoom", _args)
                        return
                    else:
                        # 准备进另外一个房间,提示退出房间
                        room_info = dict()
                        room_info["number"] = _args["number"]
                        room_info["anonymity"] = _args["anonymity"]
                        room_info["roomType"] = _args["roomType"]
                        room_info["type"] = _args["type"]
                        room_info["teaHouseId"] = _args["teaHouseId"]
                        room_info["quickJoin"] = _args["quickJoin"]
                        self.call_client_func("HaveAnotherRoom", room_info)
                        return

                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
                room_id = int(_args["number"])
                if room_id > 0:
                    if not tea_house_entity.get_room_by_id(room_id):
                        self.call_client_func("Notice", ["无法加入此房间，房间已销毁"])
                        return

                # 验证是否在此茶楼中
                if self.userId not in tea_house_entity.memberInfo:
                    self.call_client_func("Notice", ["无法加入此房间，你已不在此茶楼中"])
                    return
                if tea_house_entity.is_freeze_player(self.userId):
                    self.call_client_func("Notice", ["无法加入此房间，你已被冻结"])
                    return
                # 如果冠名赛已经打烊，提示冠名赛打烊，进入房间失败
                if tea_house_entity and tea_house_entity.isSnoring == 1:
                    self.call_client_func("join_room_failed", [_args["type"], "gameCoin", int(_args["number"])])
                    self.call_client_func("Notice", ["冠名赛已打烊，请联系群主"])
                    return

                self.room_mgr.join_normal_game_coin_room(self, _args["type"], int(_args["number"]),
                                                         anonymity=_args["anonymity"],
                                                         quick_join=_args["quickJoin"], teaHouseId=_args["teaHouseId"])

            elif _args['roomType'] == 'gold':
                self.join_gold_room(_args)
        elif _func_name == 'ModifyTableSet':
            modify_result = self.tea_house_mgr.modify_table_set(self.databaseID, _args)
        elif _func_name == "JoinAnotherRoom":
            # 准备关服维护
            if self.room_mgr.is_snoring_all_room():
                self.call_client_func("Notice", [self.room_mgr.snoring_msg])
                return

            # 只处理冠名赛房间
            if self.scene:
                if self.scene.roomId == int(_args["number"]):
                    # 已在房间，重连
                    _args = {"type": self.scene.info["type"], "roomType": self.scene.info["roomType"],
                             "roomId": self.scene.info["roomId"]}
                    self.call_client_func("reconnectRoom", _args)
                    return
                else:
                    if not self.scene.cell:
                        return
                    # 需要先离开房间，客户端收到离开结果后，直接连接新房间
                    room_info = dict()
                    room_info["number"] = int(_args["number"])
                    room_info["anonymity"] = int(_args["anonymity"])
                    room_info["roomType"] = _args["roomType"]
                    room_info["type"] = _args["type"]
                    room_info["teaHouseId"] = int(_args["teaHouseId"])
                    room_info["quickJoin"] = _args["quickJoin"]
                    self.scene.cell.baseToCell(
                        {"func": "JoinAnotherRoom", 'accountDBID': self.id, 'inviteRoomInfo': room_info})
        elif _func_name == "reconnectRoom":
            # 已在房间，不做准备关服维护
            # 请求重连，发送所在房间信息
            if self.scene:
                _args = {"type": self.scene.info["type"], "roomType": self.scene.info["roomType"],
                         "roomId": self.scene.info["roomId"]}
                self.call_client_func("reconnectRoom", _args)
        elif _func_name == "queryRecord":
            self.query_record(_args)
        elif _func_name == "queryDetailRecord":

            def on_success_callback(baseRef, databaseID, wasActive):
                if baseRef:
                    if baseRef.chapterInfos:
                        # 取出历史战绩
                        history_record = baseRef.chapterInfos['historyRecord']
                        if 'challengeControl' in history_record:
                            del history_record['challengeControl']
                        self.call_client_func("queryDetailRecordResult", {_room: {'historyRecord': history_record}})
                    else:
                        self.call_client_func("queryDetailRecordResult", {})
                    if not wasActive:
                        Account.history_room[baseRef.roomId] = baseRef
                    baseRef.last_query_tick = time.time()
                else:
                    self.call_client_func('Notice', ['暂无数据'])

            _room = _args["roomDBID"]
            _roomType = _args["roomType"]
            # 创建对应房间实体
            KBEngine.createEntityFromDBID(_args["roomType"], int(_room), on_success_callback)

        # 查询回放
        elif _func_name == "queryChapterReplay":
            #  第几局
            chapter_index = int(_args["chapterIndex"])

            def on_success_callback(baseRef, databaseID, wasActive):
                if baseRef:
                    if baseRef.chapterReplay:
                        replay_data = baseRef.chapterReplay
                        replay_chapter_data = replay_data["chapterInfo"]
                        if int(chapter_index) in replay_chapter_data.keys():
                            _replay_data = replay_chapter_data[chapter_index]
                            _replay_data["roomInfo"] = baseRef.info
                            if 'gps' in _replay_data["roomInfo"]:
                                del _replay_data["roomInfo"]['gps']
                            self.call_client_func("queryChapterReplayResult", _replay_data)
                        else:
                            self.call_client_func("queryChapterReplayResult", {})
                    else:
                        self.call_client_func("queryChapterReplayResult", {})
                else:
                    self.call_client_func('Notice', ['暂无数据'])

                    if not wasActive:
                        Account.history_room[baseRef.roomId] = baseRef
                    baseRef.last_query_tick = time.time()

            _room = _args["roomDBID"]
            _roomType = _args["roomType"]
            KBEngine.createEntityFromDBID(_args["roomType"], int(_room), on_success_callback)
        elif _func_name == "queryAccountHeadImageUrl":
            def on_success_callback(baseRef, databaseID, wasActive):
                if baseRef:
                    self.call_client_func("queryAccountHeadImageUrl",
                                          {"headImageUrl": baseRef.headImageUrl, "databaseId": databaseID, "name":
                                              baseRef.name})
                    if not wasActive:
                        baseRef.destroy()
                else:
                    self.call_client_func("queryAccountHeadImageUrl",
                                          {"headImageUrl": None, "databaseId": int(_args["dataBaseId"]), "name": ""})

            KBEngine.createEntityFromDBID("Account", int(_args["dataBaseId"]), on_success_callback)
        # 第二个查询头像的方法
        elif _func_name == 'queryAccountHeadImageUrl2':
            def on_success_callback(baseRef, databaseID, wasActive):
                if baseRef:
                    self.call_client_func("queryAccountHeadImageUrl2",
                                          {"headImageUrl": baseRef.headImageUrl, "databaseId": databaseID, "name":
                                              baseRef.name})
                    if not wasActive:
                        baseRef.destroy()
                else:
                    self.call_client_func("queryAccountHeadImageUrl2",
                                          {"headImageUrl": None, "databaseId": int(_args["dataBaseId"]), "name": ""})

            KBEngine.createEntityFromDBID("Account", int(_args["dataBaseId"]), on_success_callback)
        # 请求公告
        elif _func_name == "queryPlacardReq":
            _data = []

            def callback(result):

                for r in result:
                    _data.append({"title": str(r[0], 'utf-8'), "content": str(r[1], 'utf-8')})
                self.call_client_func("QueryPlacardResp", _data)

            DBCommand.checkOutPlacard(callback)


        # 请求滚动公告
        elif _func_name == "queryScrollAnnouncement":
            _data = []

            def callback(result):

                for r in result:
                    _data.append({"content": str(r[2], 'utf-8')})
                self.call_client_func("queryScrollAnnouncement", _data)

            DBCommand.checkOutScrollAnnouncement(callback)
        elif _func_name == "reqLocation":

            # 上传经纬度
            self.longitude = _args["longitude"]
            self.latitude = _args["latitude"]
            self.address = _args["address"]
            if 'isGPS' in _args:
                self.gpsLocation = _args['isGPS']
        elif _func_name == "GPSSwitch":
            self.gpsLocation = _args['gpsSwitch']
        elif _func_name == "reqWxServer":
            # 获取客服列表
            wx_servers = []

            def callback(result):
                # print(result)
                if len(result) != 0:
                    for i, r in enumerate(result):
                        wx_servers.append({"contact": str(r[1], "utf8"), "description": str(r[2], 'utf-8')})
                        if i == len(result) - 1:
                            self.call_client_func("reqWxServerResult", wx_servers)

            DBCommand.checkOutCustomerService(callback, _args["location"])
        elif _func_name == "attendanceHall":
            if time.time() > int(self.attendanceDataTime):
                today = datetime.date.today()
                self.attendanceDataTime = int(time.mktime(today.timetuple()) + 86399)
                self.roomCard += Const.GameConfigJson.config_json['Hall']['shareGiftDiamondCount']
                self.retRoomCard()
            self.call_client_func("Notice", ["分享成功"])
        elif _func_name == "attendanceChallenge":
            if time.time() > int(self.dayShareDateTime):
                self.dayShareCount = 1
                today = datetime.date.today()
                self.dayShareDateTime = int(time.mktime(today.timetuple()) + 86399)
                self.goldIngot += Const.GameConfigJson.config_json['Hall']['shareChallengeGiftDiamondCount']
                self.retGoldIngot()
            elif self.dayShareCount < 2:
                self.dayShareCount += 1
                self.goldIngot += Const.GameConfigJson.config_json['Hall']['shareChallengeGiftDiamondCount']
                self.retGoldIngot()
            self.call_client_func("Notice", ["分享成功"])
        elif _func_name == "attendanceInRoom":
            def prize_callback(prize_type, prize_price):
                DEBUG_MSG("attendanceInRoom %s %s" % (prize_type, prize_price))
                self.change_prize(prize_type, prize_price)
                self.retPrize(prize_type)

            DBCommand.change_prize_state_for_share(self.databaseID, prize_callback)
            # self.call_client_func("Notice", ["领奖成功，可去大奖赛大厅顶部话费处查看或点击“输入手机号”按钮进行兑换"])
        elif _func_name == "GetCode":
            self.security_code = str(random.randint(100000, 999999))
            self.want_binding_phone = _args["phoneNumber"]
            security_code_result = HttpRequest.sendVerificationCode(str(_args["phoneNumber"]), self.security_code)
        elif _func_name == "BindingPhone":

            def write_account_call_back(boolean, entity):
                # 回调
                if not boolean:
                    self.phone = ""
                    self.security_code = ""
                else:
                    self.retAccountInfo()
                args = {"result": boolean, "content": "数据库写入失败" if not boolean else ""}
                self.call_client_func("bindingResult", args)

            if _args["code"] == self.security_code and self.want_binding_phone == _args["phoneNumber"]:
                self.phone = _args["phoneNumber"]
                self.want_binding_phone = -1
                self.writeToDB(write_account_call_back)
            else:
                args = {"result": False, "content": "验证码或手机不正确"}
                self.call_client_func("bindingResult", args)
        # TODO 创建冠名赛
        elif _func_name == "createTeaHouse":
            self.create_tea_house(_args)
        # 请求冠名赛列表
        elif _func_name == "HallTeaHouseInfoReq":
            self.get_joined_tea_house_list()
        # 请求单个冠名赛信息
        elif _func_name == "SingleTeaHouseInfo":
            self.get_tea_house_info(_args["teaHouseId"])
        elif _func_name == "OnOpenTeaHousePanel":
            # 更新冠名赛中玩家的金币

            # 如果冠名赛不存在
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            if not tea_house_entity:
                self.call_client_func("Notice", ["冠名赛已解散"])
                self.call_client_func("DestroyTeaHouseSuccess", {})
                self.get_joined_tea_house_list()
                return

            # 同步大厅金币到冠名赛
            tea_house_entity.set_game_coin(self.databaseID, self.gold)

            player = tea_house_entity.get_tea_house_player(self.databaseID)
            # 如果玩家不在冠名赛里，返回大厅
            if not player:
                self.call_client_func("Notice", ["你已不是此冠名赛的成员"])
                self.call_client_func("DestroyTeaHouseSuccess", {})
                self.get_joined_tea_house_list()
                return
            DEBUG_MSG('OnOpenTeaHousePanel self.client_open_tea_house_state 修改前%s' % self.client_open_tea_house_state)
            self.client_open_tea_house_state = _args["teaHouseId"]
            DEBUG_MSG('OnOpenTeaHousePanel self.client_open_tea_house_state 修改后%s' % self.client_open_tea_house_state)
            self.call_client_func("OpenTeaHousePanelSuccess", {"teaHouseId": _args["teaHouseId"],
                                                               'teaHouseType': tea_house_entity.teaHouseType})
        elif _func_name == "OnCloseTeaHousePanel":
            self.client_open_tea_house_state = -1
        elif _func_name == "BackToHallInRoom":
            # 从房间返回大厅,返回房间所在茶楼
            if self.scene is None:
                return
            if "teaHouseId" in self.scene.info:
                tea_house_id = self.scene.info["teaHouseId"]
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
                if tea_house_entity:
                    self.call_client_func("BackToHallInRoomResp",
                                          {"teaHouseId": tea_house_id, 'teaHouseType': tea_house_entity.teaHouseType})
        elif _func_name == "LeaveTeaHouseBackToHall":
            """客户端询问是否可以离开茶楼，已加入房间时，不允许离开
            挑战赛进来查看时，可以返回
            """
            if self.scene and self.scene.info["roomType"] == "challenge":
                self.call_client_func("LeaveTeaHouseBackToHallResp", {"result": True})
            else:
                self.call_client_func("LeaveTeaHouseBackToHallResp", {"result": True if self.scene is None else False})
        elif _func_name == "GetRoomCellInfo":
            if self.scene:
                # 已在房间，直接重连
                _args = {"haveScene": True, "type": self.scene.info["type"], "roomType": self.scene.info["roomType"],
                         "roomId": self.scene.info["roomId"], "anonymity": self.scene.info["anonymity"],
                         'teaHouseId': self.scene.info["teaHouseId"] if "teaHouseId" in self.scene.info else -1}
            else:
                _args = {"haveScene": False}
            self.call_client_func("GetRoomCellInfoResp", _args)
        # 加入冠名赛
        elif _func_name == "JoinTeaHouseReq":
            self.join_tea_house_request(_args)
        elif _func_name == "JoinTeaHouseByInvitationCode":
            # 通过邀请码进入冠名赛
            # 申请成功，通知客户端
            def application_success():
                # 如果不需要审核，直接同意，处理掉, 返回
                if tea_house_entity.isReview == 0:
                    # 通知客户端
                    def write_db_success(entity):
                        joiner_entity = self.account_mgr.get_account(self.databaseID)
                        if joiner_entity:
                            joiner_entity.call_client_func("JoinTeaHouseSuccess",
                                                           {"teaHouseId": tea_house_entity.teaHouseId})
                            joiner_entity.get_joined_tea_house_list()

                    # 申请失败，通知客户端
                    def write_db_fail():
                        pass

                    tea_house_entity.join(self.databaseID, on_success=write_db_success, on_fail=write_db_fail)
                    return
                # 通知创建者
                creator = tea_house_entity.creatorDBID
                creator_entity = self.account_mgr.get_account(creator)
                if creator_entity:
                    # 创建者在线
                    creator_entity.call_client_func("NewApplication", {"list": tea_house_entity.applicationList})

            tea_house_entity = self.tea_house_mgr.get_tea_house_by_invitation_code(_args["invitationCode"])
            # 如果冠名赛存在，提示客户端等待同意
            if tea_house_entity:
                # 如果已经加入，直接返回
                if self.databaseID in tea_house_entity.memberInfo.keys():
                    self.call_client_func("JoinTeaHouseResp", ["你已加入此冠名赛"])
                    return
                self.call_client_func("JoinTeaHouseResp", ["申请已提交,请等待老板同意"])
                # 加入冠名赛申请列表
                inviter_db_id = int(_args["invitationCode"])
                for k, v in tea_house_entity.memberInfo.items():
                    if v.invitation_code == inviter_db_id:
                        inviter_db_id = v.db_id
                tea_house_entity.application_join(self.databaseID, self.name, self.headImageUrl, inviter_db_id, self.gold,
                                                  on_success=application_success)
            else:
                self.call_client_func("JoinTeaHouseResp", ["找不到此冠名赛"])
                return

        elif _func_name == "TeaHousePartnerInfoReq":
            # 楼主请求合伙人信息
            self.send_partner_tea_house_partner_info_to_client(_args["teaHouseId"], self.databaseID)
        elif _func_name == 'TeaHousePartnerInfoReq_upData':
            self.send_partner_tea_house_partner_info_to_client_light(_args["teaHouseId"], self.databaseID)
        elif _func_name == "PartnerTeaHouseInfoReq":
            # 合伙人请求合伙人信息
            if 'levelFilter' in _args:
                self.send_partner_tea_house_partner_info_to_client(_args["teaHouseId"], _args["accountDBID"],
                                                                   _args['levelFilter'])
            else:
                self.send_partner_tea_house_partner_info_to_client(_args["teaHouseId"], _args["accountDBID"])
        elif _func_name == 'PartnerTeaHouseInfoReq_upData':
            self.send_partner_tea_house_partner_info_to_client_light(_args["teaHouseId"], _args["accountDBID"])
        elif _func_name == 'GetTeamBilling':
            self.get_team_billing(_args['accountDBID'], _args['teaHouseId'])
        elif _func_name == 'GetTeamBilling_new':
            self.get_team_billing_with_page_index(_args['accountDBID'], _args['teaHouseId'], _args['pageIndex'])
        elif _func_name == "GetTeamTollInfo":
            self.get_team_toll_info(_args['accountDBID'], _args['teaHouseId'])
        # 新增
        elif _func_name == "ChangeTeaHoseProportion_new":
            # 通知客户端
            def write_db_success(entity):
                _resp = {"result": 1}
                self.call_client_func("ChangeTeaHoseProportionResp_new", _resp)

            # 申请失败，通知客户端
            def write_db_fail(content):
                _resp = {"result": 0}
                self.call_client_func("ChangeTeaHoseProportionResp_new", _resp)
                self.call_client_func('Notice', [str(content)])

            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            tea_house_entity.change_player_proportion_new(self.databaseID, _args["modifyPlayerDBId"],
                                                          _args["proportion"],
                                                          on_success=write_db_success, on_fail=write_db_fail)
        # 修改合伙人抽成比例
        elif _func_name == "ChangeTeaHoseProportion":

            # 通知客户端
            def write_db_success(entity):
                _resp = {"result": 1}
                self.call_client_func("ChangeTeaHoseProportionResp", _resp)
                # 新加接口弃置此函数
                self.send_partner_tea_house_partner_info_to_client(_args["teaHouseId"], self.databaseID)

            # 申请失败，通知客户端
            def write_db_fail(content):
                _resp = {"result": 0}
                self.call_client_func("ChangeTeaHoseProportionResp", _resp)
                self.call_client_func('Notice', [str(content)])

            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            tea_house_entity.change_player_proportion(self.databaseID, _args["modifyPlayerDBId"], _args["proportion"],
                                                      on_success=write_db_success, on_fail=write_db_fail)
        # 调整合伙人业绩
        elif _func_name == "ModifyTeaHousePerformance":
            # 通知客户端
            def write_db_success(entity):
                _resp = {"result": 1}
                self.call_client_func("ChangeTeaHosePerformanceResp", _resp)
                self.send_partner_tea_house_partner_info_to_client(_args["teaHouseId"], self.databaseID)

            # 申请失败，通知客户端
            def write_db_fail(content):
                _resp = {"result": 0}
                self.call_client_func("ChangeTeaHosePerformanceResp", _resp)
                self.call_client_func('Notice', [content])

            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            tea_house_entity.modify_performance(self.databaseID, _args["modifyPlayerDBId"], _args["performanceChange"],
                                                on_success=write_db_success, on_fail=write_db_fail)
        # 新加抽成比例接口
        elif _func_name == "ModifyTeaHousePerformance_new":
            # 通知客户端
            def write_db_success(entity):
                _resp = {"result": 1}
                self.call_client_func("ChangeTeaHosePerformanceResp_new", _resp)

            # 申请失败，通知客户端
            def write_db_fail(content):
                _resp = {"result": 0}
                self.call_client_func("ChangeTeaHosePerformanceResp_new", _resp)
                self.call_client_func('Notice', [content])

            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            tea_house_entity.modify_performance_new(self.databaseID, _args["modifyPlayerDBId"],
                                                    _args["performanceChange"],
                                                    on_success=write_db_success, on_fail=write_db_fail)

        # 邀请加入冠名赛
        elif _func_name == "InviteJoinTeaHouseReq":
            self.invite_join_tea_house_req(_args)
        elif _func_name == "AgreeJoinTeaHouse":
            self.agree_join_tea_house(_args)
        elif _func_name == "RefuseJoinTeaHouse":
            self.refuse_join_tea_house(_args)
        elif _func_name == "AgreeExitTeaHouse":
            self.agree_exit_tea_house(_args)
        elif _func_name == "RefuseExitTeaHouse":
            self.refuse_exit_tea_house(_args)
        elif _func_name == 'ModifyLuckyCard':
            self.modify_lucky_card(_args)
        elif _func_name == 'ReceiveLuckyCard':
            self.receive_lucky_card(_args)
        elif _func_name == 'GetLuckyCardHistory':
            self.get_lucky_card_history(_args)

        # 邀请进入房间
        elif _func_name == "InviteJoinRoomReq":
            self.invite_join_room_req(_args)
        elif _func_name == "InviteJoinRoomResponse":
            self.invite_join_room_response(_args)
        elif _func_name == 'GetFreeMemberList':
            tea_house_id = _args["teaHouseId"]
            # current_page = _args['currentPage']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            args = []
            if tea_house_entity:
                args = tea_house_entity.get_online_members(self.databaseID)
            self.call_client_func('GetFreeMemberList', {'membersInfo': args})

        elif _func_name == 'GetCanNotSameTablePlayers':
            tea_house_id = _args["teaHouseId"]
            account_db_id = _args["accountDbid"]
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            args = []
            if tea_house_entity:
                args = tea_house_entity.get_exclude_room_members(account_db_id)
            self.call_client_func('GetCanNotSameTablePlayers', {'players': args})

        elif _func_name == 'AddCanNotSameTablePlayer':
            tea_house_id = _args["teaHouseId"]
            account_db_id = _args["accountDbid"]
            exclude_list = _args["addAccountDbid"]
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            if tea_house_entity:
                result = tea_house_entity.add_exclude_room_members(account_db_id, exclude_list)
                if result == 0:
                    self.call_client_func("Notice", ["添加成功"])
                    args = tea_house_entity.get_exclude_room_members(account_db_id)
                    self.call_client_func('GetCanNotSameTablePlayers', {'players': args})
                    pass
                elif result < 0:
                    if result == -3:
                        self.call_client_func("Notice", ["不能添加本人"])
                    elif result == -4:
                        self.call_client_func("Notice", ["不能重复添加"])
                    else:
                        self.call_client_func("Notice", ["添加失败"])
                else:
                    self.call_client_func("Notice", ["只能添加 %s 人" % result])

        elif _func_name == 'RemoveSameTablePlayer':
            tea_house_id = _args["teaHouseId"]
            account_db_id = _args["accountDbid"]
            remove_db_id = _args["removeAccountDbid"]
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            if tea_house_entity:
                tea_house_entity.remove_exclude_room_members(account_db_id, remove_db_id)
                self.call_client_func("Notice", ["删除成功"])
                args = tea_house_entity.get_exclude_room_members(account_db_id)
                self.call_client_func('GetCanNotSameTablePlayers', {'players': args})

        elif _func_name == "ModifyGameCoinSwitch":
            _right = Const.ServerGameConfigJson.config_json['TeaHouse']["modifyGameCoinSwitch"]
            self.call_client_func('ModifyGameCoinSwitch', {'gameCoinSwitch': bool(_right)})

        # 修改比赛分
        elif _func_name == "ModifyGameCoin":
            # 申请成功，通知客户端
            def write_db_success():
                self.call_client_func("ModifyCoinSuccess", {})

            def write_db_fail(content):
                self.call_client_func("Notice", [str(content)])

            if Const.ServerGameConfigJson.config_json['TeaHouse']["modifyGameCoinSwitch"] == 0:
                self.call_client_func("Notice", ["此功能暂未开放"])
                return
            modify_player_db_id = _args["modifyPlayer"]
            tea_house_id = _args["teaHouseId"]
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            tea_house_entity.modify_game_coin(modify_player_db_id, self, _args["gameCoinChange"],
                                              on_success=write_db_success, on_fail=write_db_fail)
        # 修改冠名赛信息
        elif _func_name == "ModifyTeaHouseInfo":
            # 申请成功，通知客户端
            def write_db_success(entity):
                self.call_client_func("ModifyTeaHouseInfoSuccess", {})

            # 申请失败，通知客户端
            def write_db_fail(content):
                self.call_client_func("ModifyTeaHouseInfoFail", {"content": content})

            tea_house_name = _args["teaHouseName"]
            tea_house_head_image = _args["teaHouseHeadImage"]
            tea_house_notice = _args["teaHouseNotice"]
            tea_house_snoring = _args["teaHouseSnoring"]
            tea_house_review = _args["teaHouseReview"]
            lucky_card_switch = _args['luckyCardSwitch']
            game_coin_switch = _args['gameCoinSwitch']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            if self.databaseID in tea_house_entity.memberInfo:
                if tea_house_entity.memberInfo[self.databaseID].level > TeaHousePlayerLevel.Normal:
                    tea_house_entity.modify_tea_house_info(tea_house_name, tea_house_notice, tea_house_head_image,
                                                           tea_house_snoring, tea_house_review, lucky_card_switch,
                                                           game_coin_switch,
                                                           on_success=write_db_success, on_fail=write_db_fail)
        # 升级冠名赛
        elif _func_name == "ChangeTeaHouseLevel":

            # 申请成功，通知客户端
            def write_db_success(entity):
                self.roomCard -= Const.UpgradeTeaHouseRoomCardConsume.RoomCardConsume[_args["teaHouseLevel"]]
                self.retAccountInfo()
                self.call_client_func("ChangeTeaHouseLevelSuccess", {})

            # 申请成功，通知客户端
            def write_db_fail(content):
                self.call_client_func("ChangeTeaHouseLevelFail", {"content": content})

            tea_house_level = _args["teaHouseLevel"]
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            if self.databaseID in tea_house_entity.memberInfo:
                if tea_house_entity.memberInfo[self.databaseID].level > TeaHousePlayerLevel.Normal:
                    room_card_consume = Const.UpgradeTeaHouseRoomCardConsume.RoomCardConsume[_args["teaHouseLevel"]]
                    if self.roomCard < room_card_consume:
                        self.call_client_func("ChangeTeaHouseLevelFail", {"content": "升级失败,钻石不足"})
                        return
                    tea_house_entity.change_tea_house_level(tea_house_level, on_success=write_db_success,
                                                            on_fail=write_db_fail)
        # 修改冠名赛成员身份等级
        elif _func_name == "ChangeTeaHouseMemberLevel":
            # 申请成功，通知客户端
            def write_db_success(entity):
                self.call_client_func("ChangePlayerLevelSuccess", {})
                DBCommand.change_player_level(_args["teaHouseId"], player_db_id, player_level)

            # 申请成功，通知客户端
            def write_db_fail(content):
                self.call_client_func("ChangePlayerLevelFail", {"content": content})

            player_level = _args["playerLevel"]
            player_db_id = _args["playerDBId"]
            if player_level == 50 and Const.ServerGameConfigJson.config_json['TeaHouse']["AddTeamSwitch"] == 0:
                write_db_fail(" ")
                return

            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            # if player_db_id in tea_house_entity.memberInfo.keys():
            #        if tea_house_entity.memberInfo[tea_house_entity.memberInfo].belong_to!=tea_house_entity.creatorDBID and /
            #                 tea_house_entity.memberInfo[tea_house_entity.memberInfo].level!=TeaHousePlayerLevel.Normal:
            #              return
            #         else:
            #              if player_level==TeaHousePlayerLevel.Partner:
            #                  tea_house_entity.memberInfo[tea_house_entity.memberInfo].belong_to=tea_house_entity.creatorDBID
            # original_player_level = tea_house_entity.get_tea_house_player(player_db_id).level
            tea_house_entity.change_player_level(self.databaseID, player_db_id, player_level,
                                                 on_success=write_db_success, on_fail=write_db_fail)

        # 退出冠名赛
        elif _func_name == "ExitTeaHouse":
            self.exit_tea_house_request(_args)
        # 解散冠名赛
        elif _func_name == "DestroyTeaHouse":
            def write_db_success():
                pass

            def write_db_fail(content):
                self.call_client_func("DestroyTeaHouseFail", {"content": content})
                self.call_client_func("Notice", [content])

            tea_house_id = _args["teaHouseId"]
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            if self.databaseID in tea_house_entity.memberInfo:
                if tea_house_entity.memberInfo[self.databaseID].level > TeaHousePlayerLevel.Normal:
                    self.tea_house_mgr.destroy_tea_house_with_id(tea_house_id, on_success=write_db_success,
                                                                 on_fail=write_db_fail)
        elif _func_name == "CreateTeaHouseRoom":
            self.create_tea_house_room(_args)
        elif _func_name == "ChangeTeaHouseRoomConfig":
            # 修改房间规则
            self.change_tea_house_room_config(_args)
        elif _func_name == "QueryTeaHouseMemberOnlineState":
            self.query_online_state(_args)
        elif _func_name == "disbandTeaHouseRoom":
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            tea_house_entity.disband_room(_args["roomId"], _args["teaHouseId"])
        # 代开房
        elif _func_name == "substituteCreateRoom":
            # 准备关服维护
            if self.room_mgr.is_snoring_all_room():
                self.call_client_func("Notice", [self.room_mgr.snoring_msg])
                return

            _args["substitute"] = True
            self.room_mgr.create_room(self.databaseID, _args)
        # 代开房列表
        elif _func_name == "substituteRoomsList":
            self.send_substitute_room_list()
        # 请求钻石价值
        elif _func_name == "getCardValue":
            if self.proxyType > 0:
                self.call_client_func("getCardValueResult",
                                      Const.GameConfigJson.config_json['Hall']['proxydiamondValue'])
            else:
                self.call_client_func("getCardValueResult", Const.GameConfigJson.config_json['Hall']['diamondValue'])
        elif _func_name == "GetGoldIngotValueAndUrl":
            dic = collections.OrderedDict()
            _map = Const.ServerGameConfigJson.config_json["Hall"]["goldIngotValue"]
            sort_lst = sorted(zip(_map.values(), _map.keys()))
            for v in sort_lst:
                dic[v[1]] = v[0]
            info = {"goldIngotValue": dic,
                    "url": Const.ServerGameConfigJson.config_json["Hall"]["goldIngotUrl"]}
            self.call_client_func("GetGoldIngotValueAndUrl", info)
        elif _func_name == "GetGoldIngotByHf":
            dic = collections.OrderedDict()
            _map = Const.ServerGameConfigJson.config_json["Hall"]["goldIngotByHf"]
            sort_lst = sorted(zip(_map.values(), _map.keys()))
            for v in sort_lst:
                dic[v[1]] = v[0]
            info = {"goldIngotValue": dic}
            self.call_client_func("GetGoldIngotByHf", info)
        elif _func_name == "BuyGoldIngotByHf":
            _map = Const.ServerGameConfigJson.config_json["Hall"]["goldIngotByHf"]
            gold_ingot_num = str(_args["count"])
            if gold_ingot_num in _map:
                hf_num = _map[gold_ingot_num]
            else:
                self.call_client_func("Notice", ["兑换失败"])
                return
            if hf_num > self.get_prize(0):
                self.call_client_func("Notice", ["话费余额不足"])
                return
            self.goldIngot += float(gold_ingot_num)
            self.change_prize(0, 0 - hf_num)
            self.retGoldIngot()
            self.retPrize(0)
            self.call_client_func("Notice", ["兑换成功"])
        elif _func_name == "agentInput":
            application_proxy = KBEngine.createEntityLocally("ApplicationProxyList", {})
            application_proxy.create_one_item(self.databaseID, _args["phone"])
            self.call_client_func("Notice", ["申请成功"])
        elif _func_name == "getTeaHouseTodayRooms":
            self.get_tea_house_today_rooms(_args)
        elif _func_name == "getTeaHouseTodayGameCoinBilling":
            self.get_tea_house_today_game_coin_billing(_args)
        elif _func_name == 'getTeaHouseTodayLuckyCardConsume':
            self.get_tea_house_lucky_card_consume(_args)
        elif _func_name == "queryGameCoinHistory":
            account_db_id = _args["accountDBID"]
            tea_house_id = _args["teaHouseId"]
            self.query_game_coin_history(account_db_id, tea_house_id)
        elif _func_name == "startTimeChange":
            start_time = int(time.time())
            account_db_id = _args["accountDBID"]
            tea_house_id = _args["teaHouseId"]
            self.change_start_time(start_time, tea_house_id, self.databaseID)
            self.query_game_coin_history(account_db_id, tea_house_id)
        elif _func_name == "KickOutTeaHouseMember":
            self.kick_out_tea_house_member(_args)
        elif _func_name == "queryTeaHouseJoinAndExitHistory":
            tea_house_id = _args["teaHouseId"]
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            if tea_house_entity:
                if tea_house_entity.joinAndExitHistory is None:
                    tea_house_entity.joinAndExitHistory = []
                self.call_client_func("queryTeaHouseJoinAndExitHistory", tea_house_entity.joinAndExitHistory)
        elif _func_name == "modifyTeaHousePlayerChapterCount":
            tea_house_id = _args["teaHouseId"]
            modify_player_db_id = _args["modifyPlayerDBID"]
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            if tea_house_entity:
                tea_house_entity.set_player_chapter_count(modify_player_db_id, 0)
        elif _func_name == "getRoomCardConsume":
            self.get_room_card_consume_switch()
        elif _func_name == "addFriendsRequest":
            self.add_friend_request(_args)
        elif _func_name == 'addFriendsResponse':
            self.add_friend_response(_args)
        elif _func_name == "removeFriends":
            self.remove_friend(_args)
            self.remove_friend(_args)
        elif _func_name == "getFriends":
            self.get_friend()
        elif _func_name == "giveGold":  # 赠送金币
            self.give_gold(_args)
        elif _func_name == "giveGoldRecord":  # 赠送金币记录
            self.give_gold_record(_args)  # 赠送金币记录
        elif _func_name == "commission":  # 我的佣金
            self.get_commission(_args)
        elif _func_name == "historyCommission":  # 历史佣金
            self.get_history_commission_record(_args)
        elif _func_name == "extractCommission":  # 提取佣金
            self.extract_commission(_args)
        elif _func_name == "extractCommissionRecord":  # 佣金提取记录
            self.extract_commission_record(_args)
        elif _func_name == "isFriend":
            people_relation = self.is_friend(_args["people"])
            self.call_client_func("isFriend", people_relation)
        # 清除加入记录
        elif _func_name == "clearJoinAndExitHistory":
            tea_house_id = _args['teaHouseId']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            # 群主才可以清除出入记录
            if tea_house_entity and self.userId == tea_house_entity.creatorDBID:
                tea_house_entity.clear_join_history()
                self.call_client_func("clearJoinAndExitHistorySuccess", {})
        elif _func_name == "GetGameConfigJson":
            self.send_game_config_json()
        # 请求微信分享内容
        elif _func_name == 'GetWxShareContent':
            self.send_wx_share_content()
        elif _func_name == "BindingProxy":
            self.binding_proxy(_args)
        elif _func_name == "ReqBelongTo":
            self.call_client_func("BelongToResp", {"belongTo": self.belong_to})
        elif _func_name == 'GetSingleMemberInfo':
            self.get_single_member_info(_args['teaHouseId'], _args['accountDBID'])
        elif _func_name == 'GetMembersWithPageIndex':  # TODO GetMembersWithPageIndex
            self.get_members_with_page_index(_args['teaHouseId'], _args['accountDBID'],
                                             _args['pageIndex'])
        elif _func_name == 'SearchMember':
            self.search_member(_args['teaHouseId'], _args['keyWord'])
        elif _func_name == 'GetCanAddSameTablePlayers':
            tea_house_id = _args['teaHouseId']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            members = []
            if tea_house_entity:
                members = tea_house_entity.search_tea_house_member_info(self.databaseID, _args['keyword'])
            self.call_client_func('GetCanAddSameTablePlayers', {'memberInfo': members})
            if not members:
                self.call_client_func("Notice", ["找不到此玩家"])
        elif _func_name == 'GetPartnerInfoWithPageIndex':  # 通过页数获取成员信息
            self.get_partner_info_with_page_index(_args['teaHouseId'], _args['accountDBID'],
                                                  _args['pageIndex'], _args['levelFilter']),
        elif _func_name == "GetPartnerInfoWithPageIndex2":  # 通过页数获取合伙人信息
            self.get_partner_info_with_page_index2(_args['teaHouseId'], _args['accountDBID'],
                                                  _args['pageIndex'], _args['levelFilter']),

        # 增加查询战绩函数
        elif _func_name == 'GetPlayerBattleScore':
            self.get_player_battle_score(_args['teaHouseId'], _args['accountDBID'], _args['pageIndex'])
        elif _func_name == "GetTeaHouseRoomsWithPageIndex":
            self.tea_house_mgr.get_tea_house_rooms_with_page_index(self.databaseID, _args)
        elif _func_name == 'GetUrlAddress':
            url_type = None
            if _args and 'urlType' in _args.keys():
                url_type = _args['urlType']
            self.send_url_address(url_type=url_type)
        elif _func_name == 'GetDiamondToGoldRate':
            self.get_diamond_to_gold_rate()
        elif _func_name == 'DiamondConvertToGold':
            self.diamond_convert_to_gold(_args)
            pass
        elif _func_name == 'GetToDoList':
            self.get_to_do_list()
        elif _func_name == 'ToDoListOperation':
            self.to_do_list_operation(_args)
        elif _func_name == 'JoinAndOpenGoldSession':
            self.join_and_open_gold_session(_args)
        elif _func_name == 'ExitAndCloseGoldSession':
            self.exit_and_close_gold_session(_args)
        elif _func_name == 'EnterChallenge':
            if self.check_have_challenge_room(_args['challengeLevel']):
                return

            # 准备关服维护
            if self.room_mgr.is_snoring_all_room():
                self.call_client_func("Notice", [self.room_mgr.snoring_msg])
                return

            self.challenge_mgr.enter_challenge_area(_args['challengeLevel'], self.databaseID)
        elif _func_name == 'BackToChallengeRoom':
            if self.scene:
                # 返回需要重连的服务器信息
                _args = {"type": self.scene.info["type"], "roomType": self.scene.info["roomType"],
                         "roomId": self.scene.info["roomId"]}
                self.call_client_func("reconnectRoom", _args)
                return
        elif _func_name == 'ExitChallenge':
            self.challenge_mgr.exit_challenge_area(_args['challengeLevel'], self.databaseID)
        elif _func_name == 'GetChallengeTicketInfo':
            self.challenge_mgr.get_challenge_ticket_info(self.databaseID)
        elif _func_name == 'GetMyPrize':
            self.get_my_prize()
        elif _func_name == 'GetChallengeAwardsRank':
            self.get_all_prize()
        elif _func_name == 'GetChallengeRollNotice':
            self.get_challenge_roll_notice()

        elif _func_name == "GetShareOutRoomImgUrl":
            self.call_client_func("GetShareOutRoomImgUrl",
                                  {"url": Const.ServerGameConfigJson.config_json["Hall"]["roomOuterShareImgUrl"]})
        elif _func_name == "GetShareInRoomImgUrl":
            self.call_client_func("GetShareInRoomImgUrl",
                                  {"url": Const.ServerGameConfigJson.config_json["Hall"]["roomInnerShareImgUrl"]})
        elif _func_name == "GetChallengeConvertUrl":
            self.redeem_code = random.randint(100000, 999999)
            self.redeem_ticket = time.time()
            url = "%s/prize/redeem/?userid=%s&prizecode=%s" % (
            Const.ServerGameConfigJson.config_json["Hall"]["challengeRedeemUrl"],
            self.databaseID, self.redeem_code)
            self.call_client_func("GetChallengeConvertUrl", {"url": url})
        elif _func_name == "GetRedeemCode":
            # self.redeem_code = random.randint(100000, 999999)
            # self.redeem_ticket = time.time()
            self.call_client_func("GetRedeemCode", self.redeem_code)
        elif _func_name == 'GetChats':
            self.get_chats(_args['databaseID'], _args['num'])
        elif _func_name == 'Chat':
            self.chat(_args)
        elif _func_name == 'ReadChat':
            self.read_chats(_args['databaseID'])
        elif _func_name == 'GetGoldSessionHallInfo':
            self.get_gold_session_hall_info()
        elif _func_name == "GetGoldSessionRoomsWithPageIndex":
            self.get_gold_session_rooms_with_page_index(_args["level"], _args["roomType"], _args["anonymity"],
                                                        _args["pageIndex"])
        elif _func_name == "ChangeGoldSessionRoomConfig":
            # 修改房间规则
            self.change_gold_session_room_config(_args)
        elif _func_name == "ChangeChallengeRoomConfig":
            # 修改房间规则
            self.challenge_mgr.change_challenge_room_config(self.databaseID, _args)
        elif _func_name == "GetRedemptionList":
            self.get_redemption_list()
        elif _func_name == 'GetUnRead':
            self.get_un_read()
        elif _func_name == 'WelcomeNotice':
            self.welcome_notice()
        elif _func_name == 'HallVideoButton':
            self.hall_video_button()
        elif _func_name == 'addPayerToRank':
            # 获取茶楼实体
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            date = str(_args['date'])
            players_db_id = []
            all_selected = _args['allSelected']
            # 如果全选  则这个茶楼内所有的人都要上报,否则不管
            if all_selected == 1:
                for k, v in tea_house_entity.memberInfo.items():
                    if k in _args["playerDBId"]:
                        continue
                    players_db_id.append(k)
            elif all_selected == 0:
                players_db_id = _args['playerDBId']
            for player_db_id in players_db_id:
                # 如果玩家在茶楼中游戏，则不能给玩家下分
                player = self.account_mgr.get_account(player_db_id)
                try:
                    if player.in_tea_house_room(_args['teaHouseId']):
                        self.call_client_func('addPayerToRank',
                                              {'state': 0, 'content': '上报失败，{}正在游戏中'.format(player.name)})
                        return
                except Exception as e:
                    DEBUG_MSG('player:%s error%s' % (player, e))
                    pass
            for player_db_id in players_db_id:
                tea_house_entity.add_player_to_rank(player_db_id, date)
            self.call_client_func('addPayerToRank', {'state': 1, 'content': '上报成功'})
        elif _func_name == 'GetTeahouseRank':
            tea_house = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            rank = tea_house.get_tea_house_rank(_args['date'], _args['playerDBId'], _args['currentPage'])
            self.call_client_func('GetTeahouseRank', rank)
        elif _func_name == 'SetRewards':
            # 获取茶楼实体
            reward_type = _args['rewardType']
            def callback(state):
                content = '设置成功' if state else '设置失败'
                self.call_client_func('SetRewards', {'state': state, 'content': content})

            if reward_type == 0:
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
                tea_house_entity.set_rewards(_args['date'], _args['rewards'], callback=callback)
            elif reward_type == 1:
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
                tea_house_entity.set_team_rewards(_args['date'], _args['rewards'], callback=callback)
        elif _func_name == 'getMemberList':
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            # 获取请求者ID，实体，请求者等级
            account_db_id = self.databaseID
            account = self.account_mgr.get_account(account_db_id)
            memberinfo = tea_house_entity.get_single_member_info(account_db_id)
            player_level = memberinfo['level']
            current_page = _args['currentPage']
            page_start = (current_page - 1) * 10
            page_end = current_page * 10 - 1
            flag = 0
            if player_level == TeaHousePlayerLevel.Partner:
                flag = 1
            memberinfo = tea_house_entity.memberInfo
            arr = {}
            count = 0
            if flag == 0:
                for k, v in memberinfo.items():
                    count = count + 1
                    if count < page_start:
                        continue
                    elif count > page_end:
                        continue
                    nickName = v.name
                    headImg = v.head_image
                    game_coin = v.game_coin
                    origin_game_coin = v.origin_game_coin
                    chapter_count = v.chapter_count
                    arr[k] = {'nickName': nickName, 'gameCoin': game_coin, 'chapterCount': chapter_count,
                              'rankScore': 0,
                              'headImg': headImg, 'origin_game_coin': origin_game_coin}
                date = time.strftime('%Y%m%d', time.localtime(int(time.time())))
                try:
                    for i in tea_house_entity.rank[date]['rankList']:
                        arr[i['player_db_id']]['rankScore'] = i['rankScore']
                except Exception as e:
                    DEBUG_MSG('getMemberList%s' % e)
                    pass
                x, y = divmod(count, 10)
                if not y == 0:
                    x = x + 1
                self.call_client_func('getMemberList', {'membersInfo': arr, 'totalPage': x})
            elif flag == 1:
                for k, v in memberinfo.items():
                    count = count + 1
                    if not v.belong_to == account_db_id:
                        continue
                    nickName = v.name
                    headImg = v.head_image
                    game_coin = v.game_coin
                    origin_game_coin = v.origin_game_coin
                    chapter_count = v.chapter_count
                    arr[k] = {'nickName': nickName, 'gameCoin': game_coin, 'chapterCount': chapter_count,
                              'rankScore': 0,
                              'headImg': headImg, 'origin_game_coin': origin_game_coin}
                date = time.strftime('%Y%m%d', time.localtime(int(time.time())))
                try:
                    for i in tea_house_entity.rank[date]['rankList']:
                        arr[i['player_db_id']]['rankScore'] = i['rankScore']
                except Exception as e:
                    DEBUG_MSG('getMemberList%s' % e)
                    pass
                self.call_client_func('getMemberList', {'membersInfo': arr, 'totalPage': 1})

        elif _func_name == 'getSysNotice':
            self.get_sys_notice()
        elif _func_name == 'GetUnReadSysNotice':
            self.get_un_read_sys_notice()
        elif _func_name == 'setOriginGameCoin':
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            # 获取上报者信息，如果是楼主则无所谓，如果是队长则要扣队长身上的比赛分
            account_db_id = self.databaseID
            account = self.account_mgr.get_account(account_db_id)
            memberinfo = tea_house_entity.get_single_member_info(account_db_id)
            player_level = memberinfo['level']
            partner_game_coin = 0
            date = time.strftime('%Y%m', time.localtime(int(time.time())))
            flag = 0
            if player_level == TeaHousePlayerLevel.Creator:
                pass
            elif player_level == TeaHousePlayerLevel.Partner:
                partner_game_coin = memberinfo['gameCoin']
                flag = 1
                if date not in tea_house_entity.teamRank.keys():
                    tea_house_entity.teamRank[date] = {}
                if account_db_id not in tea_house_entity.teamRank[date]:
                    tea_house_entity.teamRank[date] = {'winner': 0, 'luckCard': 0, 'chapterCount': 0,
                                                       'originGameCoin': 0}
            else:
                return self.call_client_func('setOriginGameCoin', {'state': 0, 'content': '设置失败,该玩家权限不足'})
            # 如果勾选全选，则玩家为茶楼内所有玩家
            all_selected = _args['allSelected']
            account_db_id_s = []
            if all_selected == 1:
                for k, v in tea_house_entity.memberInfo.items():
                    if k in _args["playerDBId"]:
                        continue
                    account_db_id_s.append(k)
            elif all_selected == 0:
                account_db_id_s = _args['playerDBId']
            add_game_coin = int(_args['game_coin'])
            # 如果合伙人比赛币这个字段存在，则证明是合伙人上分，判断合伙人分数是否足够
            if flag == 1:
                if not partner_game_coin >= len(account_db_id_s) * add_game_coin:
                    return self.call_client_func('setOriginGameCoin', {'state': 0, 'content': '设置失败,比赛分不足'})
            def success():
                pass

            def fail():
                pass

            for i in account_db_id_s:
                try:
                    tea_house_entity.modify_game_coin(i, account, add_game_coin, on_success=success, on_fail=fail)
                    tea_house_entity.update_team_rank_origin_coin(date, account_db_id, add_game_coin)
                except Exception as e:
                    DEBUG_MSG('setOriginGameCoin error%s%s%s%s a' % (e, i, account_db_id, date))
                    self.call_client_func('setOriginGameCoin', {'state': 0, 'content': '设置失败'})
                    return
            self.call_client_func('setOriginGameCoin', {'state': 1, 'content': '设置成功'})
        elif _func_name == 'getSingleMemberInfoFromRank':
            account_db_id = _args['playerDBId']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            leader_db_id = self.databaseID
            if tea_house_entity.memberInfo[leader_db_id].level == TeaHousePlayerLevel.Partner:
                if not tea_house_entity.memberInfo[account_db_id].belong_to == leader_db_id:
                    return self.call_client_func('getSingleMemberInfoFromRank', {'state': 0, 'content': '该玩家不存在'})
            try:
                info = tea_house_entity.get_single_member_info(account_db_id)
                arr = {'nickName': info['name'], 'gameCoin': info['gameCoin'], 'chapterCount': info['chapterCounts'],
                       'rankScore': 0, 'headImg': info['headImage'], 'origin_game_coin': info['origin_game_coin']}
                self.call_client_func('getSingleMemberInfoFromRank', {'memberInfo': {account_db_id: arr}, 'state': 1})
            except Exception as e:
                DEBUG_MSG('排行榜获取单个玩家信息%s' % e)
                self.call_client_func('getSingleMemberInfoFromRank', {'state': 0, 'content': '该玩家不存在'})
        elif _func_name == 'getSingleMemberRankInfoFromRank':
            account_db_id = _args['playerDBId']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
            date = _args['date']
            for i, val in enumerate(tea_house_entity.rank[date]['rankList']):
                if i < 3:
                    try:
                        reward = tea_house_entity.rank[date]['rewards'][i]
                    except Exception as e:
                        DEBUG_MSG('获取单个成员排行榜信息reward%s' % e)
                        reward = {'name': '', 'count': 0}
                else:
                    reward = {'name': '', 'count': 0}
                if val['player_db_id'] == account_db_id:
                    myinfo = {'player_db_id': val['player_db_id'], 'headImg': val['headImg'],
                              'nickName': val['nickName'], 'rankScore': val['rankScore'],
                              }
                    return self.call_client_func('getSingleMemberRankInfoFromRank', {'rankInfo': myinfo,
                                                                                     'rank': i,
                                                                                     'state': 1,
                                                                                     'reward': reward})
            return self.call_client_func('getSingleMemberRankInfoFromRank', {'state': 0, 'content': '此玩家不存在'})
        elif _func_name == 'getTeamRank':
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args['teaHouseId'])
            team_rank = tea_house_entity.get_team_rank(_args['date'])
            self.call_client_func('getTeamRank', team_rank)
        elif _func_name == 'getTeamRankMemberInfo':
            account_db_id = _args['playerDBId']
            tea_house_id = _args['teaHouseId']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            arr = {}
            for k, v in tea_house_entity.memberInfo.items():
                if k == account_db_id or v.belong_to == account_db_id:
                    arr[k] = {'name': v.name, 'ID': k, 'winner': v.winner, 'luckCard': v.lucky_card_consume
                        , 'chapterCount': v.chapter_count, 'originCoin': v.origin_game_coin, 'headImg': v.head_image}
                elif self.get_VulueById(k, tea_house_entity, account_db_id):
                    arr[k] = {'name': v.name, 'ID': k, 'winner': v.winner, 'luckCard': v.lucky_card_consume
                        , 'chapterCount': v.chapter_count, 'originCoin': v.origin_game_coin, 'headImg': v.head_image}
            return self.call_client_func('getTeamRankMemberInfo', {'membersInfo': arr})
        elif _func_name == 'GetTeaHosuePartnerSwitch':
            return self.call_client_func('GetTeaHosuePartnerSwitch',
                                         {'partnerSwitch': True if self.partnerSwitch == 1 else False})
        elif _func_name == 'clearEntity':
            self.clear_entity()
        elif _func_name == 'joinVerification':
            self.join_verification()
        elif _func_name == 'FreezeTeaHousePlayer':
            account_db_id = _args['accountDbid']
            tea_house_id = _args['teaHouseId']
            freeze_state = _args['freeze']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            if tea_house_entity:
                if tea_house_entity.is_administrator(self.userId):
                    if tea_house_entity.set_frezz_state(account_db_id, freeze_state):
                        tea_house_entity.update_single_member_info_to_client(account_db_id)
                        self.call_client_func("Notice", ["%s成功" % ("冻结" if freeze_state else "解冻")])
                    else:
                        self.call_client_func("Notice", ["冻结操作失败"])
        elif _func_name == 'GetPlayerInRoom':
            tea_house_id = _args['teaHouseId']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            if tea_house_entity:
                is_admin = tea_house_entity.is_administrator(self.userId)
                self.room_mgr.get_player_in_room(self, _args, is_admin)
        elif _func_name == 'KickOutPlayerInRoom':
            tea_house_id = _args['teaHouseId']
            user_id = _args['userId']
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            if tea_house_entity:
                if tea_house_entity.is_administrator(self.userId) and tea_house_entity.is_member(user_id):
                    account = self.account_mgr.get_account(user_id)
                    if account.cell and account.scene:
                        if account.scene.info["teaHouseId"] == tea_house_id:
                            account.cell.baseToCell({"func": "KickOutPlayerInRoom"})
                            self.call_client_func('KickOutPlayerInRoom', {"userId": user_id})
                            return
                    else:
                        self.call_client_func('Notice', ["该玩家已被踢出"])
                        return
            self.call_client_func('Notice', ["不能踢出此玩家"])
        else:
            ERROR_MSG("[Account id %s] clientToBase------>func: %s not exit" % (self.id, _func_name))

    def join_gold_room(self, _args):
        if self.scene:
            # 已在房间，直接重连
            if self.scene.roomId == int(_args["number"]):
                _args = {"type": self.scene.info["type"], "roomType": self.scene.info["roomType"],
                         "roomId": self.scene.info["roomId"]}
                self.call_client_func("reconnectRoom", _args)
                return
            else:
                # 准备进另外一个房间,提示退出房间
                room_info = dict()
                room_info["number"] = _args["number"]
                room_info["anonymity"] = _args["anonymity"]
                room_info["roomType"] = _args["roomType"]
                room_info["type"] = _args["type"]
                room_info["teaHouseId"] = _args["teaHouseId"]
                room_info["quickJoin"] = _args["quickJoin"]
                self.call_client_func("HaveAnotherRoom", room_info)
                return

        self.room_mgr.join_gold_room(self, _args["type"], int(_args["number"]),
                                     anonymity=_args["anonymity"],
                                     quick_join=_args["quickJoin"])

    def join_verification(self):
        """
        加入房间验证
        :param
        :return:
        """
        if self.cell and self.scene and self.scene.cell:
            if self._join_verification_failed > 0:
                self.delTimer(self._join_verification_failed)
                self._join_verification_failed = -1
            self.call_client_func('joinVerification', {'result': True})
        else:
            self.call_client_func('joinVerification', {'result': False})

    def get_room_card_consume_switch(self):
        """
        获取房卡消耗开关信息
        :return:
        """
        consume_config = Const.ServerGameConfigJson.config_json['CreateRoomConsumeSwitch']
        self.call_client_func("getRoomCardConsume", {"rSwitch": consume_config})

    def get_VulueById(self, get_id, tea_house_entity, find_id):
        for i in range(100):
            try:
                if get_id not in tea_house_entity.memberInfo:
                    return False
                if tea_house_entity.memberInfo[get_id].belong_to == tea_house_entity.creatorDBID:
                    return False
                if tea_house_entity.memberInfo[get_id].belong_to == find_id:
                    return True
                else:
                    get_id = tea_house_entity.memberInfo[get_id].belong_to
            except:
                return False

    def get_tea_house_today_game_coin_billing(self, _args):
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        if tea_house_entity:
            today_date = datetime.date.today()
            today_end = int(time.mktime(today_date.timetuple()) + 86399)
            yesterday_end = today_end - 86400
            today_game_coin_billing = 0.0
            yesterday_game_coin_billing = 0.0
            DEBUG_MSG('get_tea_house_today_game_coin_billing %s' % tea_house_entity.todayGameCoinBilling)
            for date_game_billing in tea_house_entity.todayGameCoinBilling:
                # 如果日期等于今天加在最后
                if date_game_billing["date"] == today_end:
                    today_game_coin_billing = date_game_billing['gameCoinBilling']
                # 如果日期等于昨天加在最前
                elif date_game_billing["date"] == yesterday_end:
                    yesterday_game_coin_billing = date_game_billing['gameCoinBilling']
            self.call_client_func("teaHouseTodayGameCoinBilling", {'today': round(today_game_coin_billing, 2),
                                                                   'yesterday': round(yesterday_game_coin_billing, 2)})
        else:
            self.call_client_func("Notice", ["找不到此冠名赛"])

    def get_tea_house_today_rooms(self, _args):
        """
        获取茶楼今日开房数
        """
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        if tea_house_entity:
            today_date = datetime.date.today()
            today_end = int(time.mktime(today_date.timetuple()) + 86399)
            yesterday_end = today_end - 86400
            today_total_count = 0
            yesterday_total_count = 0
            today_room_detail = {}
            DEBUG_MSG('get_tea_house_today_rooms todayRooms:%s' % tea_house_entity.todayRooms)
            for date_room in tea_house_entity.todayRooms:
                room_list = date_room['roomList']
                # 今日房间
                if date_room["date"] == today_end:
                    for room_info in room_list:
                        today_total_count += 1
                        # 计算今日房间详情
                        _type = room_info['type']
                        if _type not in today_room_detail:
                            today_room_detail[_type] = 1
                        else:
                            today_room_detail[_type] += 1
                elif date_room["date"] == yesterday_end:
                    for _ in room_list:
                        yesterday_total_count += 1
            self.call_client_func("teaHouseTodayRooms", {'today': today_total_count, 'yesterday': yesterday_total_count,
                                                         'todayDetail': today_room_detail})
        else:
            self.call_client_func("Notice", ["查询失败，该冠名赛不存在"])

    def welcome_notice(self):
        """
        获取欢迎页图片
        :return:
        """
        _url = Const.ServerGameConfigJson.config_json['Hall']['welcomeImageUrl']
        _switch = Const.ServerGameConfigJson.config_json['Hall']['welcomeSwitch']

        self.call_client_func('WelcomeNotice', {'url': _url, 'welcomeSwitch': _switch})

    def hall_video_button(self):
        """
        获取首页视频按钮
        :return:
        """
        _url = Const.ServerGameConfigJson.config_json['Hall']['videoButtonUrl']
        _visible = Const.ServerGameConfigJson.config_json['Hall']['videoButtonVisible']
        _imgUrl = Const.ServerGameConfigJson.config_json['Hall']['videoButtonImgUrl']

        self.call_client_func('HallVideoButton', {'url': _url, 'visible': _visible, 'imgUrl': _imgUrl})

    def receive_lucky_card(self, _args):
        """
        领取福卡
        :param _args:
        :return:
        """

        # 申请成功，通知客户端
        def write_db_success():
            self.call_client_func("ReceiveLuckyCardSuccess", {})

        def write_db_fail(content):
            self.call_client_func("Notice", [str(content)])

        tea_house_id = _args['teaHouseId']
        try:
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            tea_house_entity.receive_lucky_card(self.databaseID, on_success=write_db_success, on_fail=write_db_fail)
        except AttributeError as e:
            DEBUG_MSG(e)

    def get_lucky_card_history(self, _args):
        """
        获取福卡历史
        :return:
        """

        # 申请成功，通知客户端
        def write_db_success():
            pass

        def write_db_fail(content):
            self.call_client_func("Notice", [str(content)])

        tea_house_id = _args['teaHouseId']
        account_db_id = _args['accountDBID']
        try:
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            history = tea_house_entity.get_lucky_card_history(account_db_id, on_fail=write_db_fail)
            self.call_client_func('GetLuckyHistory', {'history': history})
        except AttributeError as e:
            DEBUG_MSG(e)

    def modify_lucky_card(self, _args):
        """
        修改福卡
        :param _args:
        :return:
        """

        # 申请成功，通知客户端
        def write_db_success():
            self.call_client_func("ModifyLuckyCardSuccess", {})

        def write_db_fail(content):
            self.call_client_func("Notice", [str(content)])

        modify_player_db_id = _args["modifyPlayer"]
        operator_db_id = _args['operatePlayer']
        tea_house_id = _args["teaHouseId"]
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        tea_house_entity.modify_lucky_card(operator_db_id, modify_player_db_id, _args["luckyCardChange"],
                                           on_success=write_db_success, on_fail=write_db_fail)

    def change_gold_session_room_config(self, _args):
        """
        修改金币场房间规则，无权限限制
        :param _args:
        :return:
        """
        self.gold_session_mgr.change_gold_session_room_config(self.databaseID, _args)

    def get_gold_session_rooms_with_page_index(self, level, room_type, anonymity, page_index):
        """
        获取指定金币场指定页码的房间信息
        :param level:
        :param room_type:
        :param anonymity:
        :param page_index:
        :return:
        """
        gold_session = self.gold_session_mgr.get_gold_session_with_level(level)
        if gold_session:
            _rooms = gold_session.get_rooms_with_page(room_type, anonymity, page_index)
            _total_page = gold_session.get_rooms_total_page(room_type, anonymity)
            _total_room_count = len(gold_session.get_rooms_with_room_type(room_type, anonymity))
            _data = {"rooms": _rooms, "totalPage": _total_page, "roomCount": _total_room_count}
            self.call_client_func("GetGoldSessionRoomsWithPageIndex", _data)

    def get_gold_session_hall_info(self):
        """
        获取金币场基本信息
        :return:
        """
        info = self.gold_session_mgr.get_gold_session_hall_info()
        self.call_client_func('GetGoldSessionInfo', info)

    def join_and_open_gold_session(self, _args):
        """
        加入金币场
        :param _args:
        :return:
        """
        try:
            self.gold_session_mgr.join_and_open(_args['goldSessionLevel'], self.databaseID)
        except KeyError as e:
            DEBUG_MSG(e)

    def exit_and_close_gold_session(self, _args):
        """
        离开金币场
        :param _args:
        :return:
        """
        try:
            self.gold_session_mgr.exit_and_close(_args['goldSessionLevel'], self.databaseID)
        except KeyError as e:
            DEBUG_MSG(e)

    def join_tea_house_request(self, _args, on_success=None):

        # 申请成功，通知客户端
        def application_success():

            # 通知创建者
            creator = tea_house_entity.creatorDBID
            # 如果不需要审核或者是楼主邀请的，直接同意，处理掉, 返回
            if tea_house_entity.isReview == 0 or creator == _args["inviterDBID"]:
                # 通知客户端
                def write_db_success(entity):
                    joiner_entity = self.account_mgr.get_account(self.databaseID)
                    if joiner_entity:
                        joiner_entity.call_client_func("JoinTeaHouseSuccess", {"teaHouseId": _args["teaHouseId"]})
                        joiner_entity.get_joined_tea_house_list()
                        if on_success:
                            on_success()

                # 申请失败，通知客户端
                def write_db_fail():
                    pass

                tea_house_entity.join(self.databaseID, on_success=write_db_success, on_fail=write_db_fail)
                return

            creator_entity = self.account_mgr.get_account(creator)
            if creator_entity:
                # 创建者在线
                creator_entity.call_client_func("NewApplication", {"list": tea_house_entity.applicationList})

        # 找到冠名赛的 DBID
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        # 如果冠名赛存在，提示客户端等待同意
        if tea_house_entity:
            # 如果已经加入，直接返回

            if self.databaseID in tea_house_entity.memberInfo.keys():
                self.call_client_func("JoinTeaHouseResp", ["你已加入此冠名赛"])
                return
            self.call_client_func("JoinTeaHouseResp", ["申请已提交,请等待老板同意"])
            # 加入冠名赛申请列表
            tea_house_entity.application_join(self.databaseID, self.name, self.headImageUrl, _args["inviterDBID"], self.gold,
                                              on_success=application_success)
        else:
            self.call_client_func("JoinTeaHouseResp", ["找不到此冠名赛"])
            return

    def exit_tea_house_request(self, _args, on_success=None):
        # 找到冠名赛的 DBID
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        if not tea_house_entity:
            self.call_client_func("ExitTeaHouseResp", ["找不到此冠名赛"])
            return
        # 加入冠名赛申请列表
        tea_house_entity.application_exit(self.databaseID, self.name, self.headImageUrl, self.gold)
        self.call_client_func("ExitTeaHouseResp", [""])
        self.call_client_func('Notice', ['申请已提交，请等待老板同意'])

    def to_do_list_operation(self, args):
        """
        待办事项处理
        :param args:
        :return:
        """
        try:
            self.account_mgr.to_do_operation(args['operatorDBID'], args['flag'], args['result'])
        except AttributeError as e:
            ERROR_MSG('Account::to_do_list_operation %s' % e)
        except KeyError as e:
            ERROR_MSG('Account::to_do_list_operation %s' % e)

    def get_to_do_list(self):
        """
        获取待处理事项
        :return:
        """
        self.call_client_func('GetToDoList', {'toDoList': self.todoList})

    def diamond_convert_to_gold(self, args):
        """
        钻石兑换金币
        :param args:
        :return:
        """
        try:
            diamond = args['diamondCount']
            if diamond > self.roomCard:
                self.call_client_func('Notice', ['兑换失败，钻石不足'])
                return
            gold_add = diamond * Const.GameConfigJson.config_json['Hall']['diamondToGoldRate']
            # 修改钻石和金币数量
            self.account_mgr.modify_room_card(self.userId, -diamond, consume_type='convertToGold')
            self.account_mgr.modify_gold(self.userId, gold_add)
            self.call_client_func('Notice', ['兑换成功'])
        except KeyError as e:
            ERROR_MSG('Account::diamond_convert_to_gold %s' % e)

    def get_diamond_to_gold_rate(self):
        """
        获取最新钻石->金币汇率
        :return:
        """
        try:
            self.call_client_func('GetDiamondToGoldRate', {
                'rate': Const.GameConfigJson.config_json['Hall']['diamondToGoldRate']})
        except KeyError as e:
            ERROR_MSG('Account::get_diamond_to_gold_rate %s' % e)
        except AttributeError as e:
            ERROR_MSG('Account::get_diamond_to_gold_rate %s' % e)

    def invite_join_tea_house_req(self, _args):
        # 邀请进入冠名赛
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        invited_user_id_list = _args["invitedUseId"]
        # 不能邀请自己
        if len(invited_user_id_list) == 1 and invited_user_id_list[0] == self.userId:
            self.call_client_func("Notice", ["无法邀请自己"])
            return
        for invited_user_id in invited_user_id_list:
            if invited_user_id == self.userId:
                continue
            invited_entity = self.account_mgr.get_account(invited_user_id)
            if invited_entity and invited_entity.client:
                # 被邀请玩家在线
                invited_entity.call_client_func("InvitedJoinTeaHouse", {"inviterName": self.name,
                                                                        "teaHouseName": tea_house_entity.name,
                                                                        "teaHouseId": tea_house_entity.teaHouseId,
                                                                        "inviterDBID": self.databaseID})
            else:
                self.account_mgr.add_tea_house_invite_in_to_do_list(self.headImageUrl, self.name,
                                                                    invited_user_id,
                                                                    tea_house_entity.teaHouseId, self.databaseID)
        self.call_client_func("InviteJoinTeaHouseResp", ["邀请已发送"])

    def get_tea_house_info(self, tea_house_id):
        """
        通知单个人单个冠名赛信息
        :param tea_house_id:
        :return:
        """
        self.tea_house_mgr.update_tea_house_info_to_client(tea_house_id, self.userId)

    def search_member(self, tea_house_id, key_word):
        """
        搜索玩家
        :param key_word: 关键字
        :param tea_house_id:茶楼id
        :return:
        """
        member_info = self.tea_house_mgr.search_tea_house_single_member_info(tea_house_id, self.userId, key_word)
        if member_info:
            self.call_client_func('SearchMember', {'memberInfo': member_info})
        else:
            self.call_client_func('Notice', ['找不到此玩家'])
    def get_player_battle_score(self, tea_house_id, account_db_id, page_index):
        """
        E查询战绩记录
        """
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            self.call_client_func("playerBattleScoreRecord", {"partnerInfo": [], "totalPages": 0, "memberCount": 0})
            return
        player = tea_house_entity.get_tea_house_player(account_db_id)
        if not player:
            self.call_client_func("playerBattleScoreRecord", {"partnerInfo": [], "totalPages": 0, "memberCount": 0})
        def on_success(charge_info):
            if tea_house_entity:
                charge_record_list = []
                for item in charge_info:
                    charge_item = {}
                    charge_item["roomId"] = item["roomId"]
                    charge_item["accountDBID"] = item["accountDBID"]
                    charge_item["typeName"] = item["typeName"]
                    charge_item["totalGoldChange"] = item["totalGoldChange"]
                    charge_item["BringInGold"] = item["BringInGold"]
                    charge_item["SurPlusGold"] = item["SurPlusGold"]
                    charge_item["settleTime"] = item["settleTime"]
                    charge_item["accountName"] = item["accountName"]
                    charge_record_list.append(charge_item)
                member_count = len(charge_record_list)
                # 计算总页数
                total_pages = math.ceil(len(charge_record_list) / Const.partner_list_page_item)
                page_start = page_index * Const.partner_list_page_item
                page_end = page_start + Const.partner_list_page_item
                partner_info_list = charge_record_list[page_start:page_end]

                self.call_client_func("playerBattleScoreRecord", {
                    'partnerInfo': partner_info_list,
                    "totalPages": int(total_pages),
                    "memberCount": member_count
                })
        DBCommand.check_out_get_player_battle_score(account_db_id, tea_house_id, on_success=on_success)



    def get_partner_info_with_page_index(self, tea_house_id, account_db_id, page_index, level_filter=0):
        """
        通过页数获取成员信息
        :return:
        """
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            partner_info, total_pages, members_count = \
                tea_house_entity.get_partner_info_with_page(account_db_id, page_index, level_filter)
            if level_filter == 0:
                self.call_client_func('GetPartnerInfoWithPageIndex', {
                    'partnerInfo': partner_info,
                    'totalPages': int(total_pages),
                    'memberCount': members_count,
                })
            else:
                self.call_client_func('GetPartnerInfoWithPageIndexWithLevelFilter', {
                    'partnerInfo': partner_info,
                    'totalPages': int(total_pages),
                    'memberCount': members_count,
                })
    def get_partner_info_with_page_index2(self, tea_house_id, account_db_id, page_index, level_filter=0):
        """
        通过页数获取合伙人信息
        """
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            partner_info, total_pages, members_count = tea_house_entity.get_partner_info_with_page2(account_db_id, page_index, level_filter)
            self.call_client_func('GetPartnerInfoWithPageIndex2', {
                'partnerInfo': partner_info,
                'totalPages': int(total_pages),
                'memberCount': members_count,
            })


    def get_members_with_page_index(self, tea_house_id, account_db_id, page_index):
        """
        获取指定冠名赛指定页码的成员信息
        :param page_index:
        :param tea_house_id:
        :param account_db_id:
        :return:
        """
        member_info, total_pages, member_count, online_count = \
            self.tea_house_mgr.get_members_with_page(tea_house_id, account_db_id, page_index)
        if member_info and total_pages:
            self.call_client_func('GetMembersWithPageIndex', {
                'memberInfo': member_info,
                'totalPages': int(total_pages),
                'memberCount': member_count,
                'onlineCount': online_count})

    def get_single_member_info(self, tea_house_id, account_db_id):
        """
        E获取指定冠名赛指定用户的信息
        :param tea_house_id:
        :param account_db_id:
        :return:
        """
        member_info = self.tea_house_mgr.get_tea_house_single_member_info(tea_house_id, account_db_id)
        if member_info:
            self.call_client_func('UpdateSingleMemberInfo', {'memberInfo': member_info})
        else:
            self.call_client_func('Notice', ['没有找到指定冠名赛成员信息'])

    def send_game_config_json(self):
        for k, v in Const.GameConfigJson.config_json.items():
            self.call_client_func(str(k) + "JsonConfig", v)

    def query_game_coin_history(self, account_db_id, tea_house_id):
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            self.call_client_func("gameCoinRecord", {"chargeInfo": [], "startTime": -1})
            return
        player = tea_house_entity.get_tea_house_player(account_db_id)

        if not player or player.start_query_game_coin_history_time == -1:
            self.call_client_func("gameCoinRecord", {"chargeInfo": [], "startTime": -1})
            return

        def on_success(charge_info):
            if tea_house_entity:
                charge_record = []
                for item in charge_info:
                    charge_item = {}
                    charge_item["modifyTime"] = item["modifyTime"]
                    charge_item["accountDBID"] = item["accountDBID"]
                    charge_item["operatorDBID"] = item["operationDBID"]
                    charge_item["accountName"] = item["accountName"]
                    charge_item["operatorName"] = item["operationName"]
                    charge_item["modifyCount"] = item["modifyCount"]
                    charge_item["modifiedGameCoin"] = item["modifiedGameCoin"]
                    account_player = tea_house_entity.get_tea_house_player(charge_item["accountDBID"])
                    operator_player = tea_house_entity.get_tea_house_player(charge_item["operatorDBID"])
                    if account_player:
                        charge_item["accountTeaHouseLevel"] = account_player.level
                    else:
                        charge_item["accountTeaHouseLevel"] = -1

                    if operator_player:
                        charge_item["operatorTeaHouseLevel"] = operator_player.level
                    else:
                        charge_item["operatorTeaHouseLevel"] = -1
                    charge_record.append(charge_item)
                self.call_client_func("gameCoinRecord", {"chargeInfo": charge_record})

        DBCommand.check_out_game_coin_charge_history(account_db_id, tea_house_id,
                                                     start_time=player.start_query_game_coin_history_time,
                                                     on_success=on_success)

    def change_start_time(self, start_time, tea_house_id, account_db_id):
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            if account_db_id != tea_house_entity.creatorDBID:
                return
            for k, v in tea_house_entity.memberInfo.items():
                v.start_query_game_coin_history_time = start_time

    def send_substitute_room_list(self):
        self.call_client_func("substituteRoomsList", {"roomList": self.substituteRooms})

    def create_tea_house(self, _args):

        def on_create_success(entity):
            args = {"id": entity.teaHouseId, "name": entity.name, "headImage": entity.headImage,
                    "contactWay": entity.contactWay}
            self.call_client_func("createTeaHouseSuccess", args)
            self.get_joined_tea_house_list()
            # 修改房卡
            modify_count = Const.GameConfigJson.config_json['Hall']['teaHouseCreateDiamondConsume']
            self.account_mgr.modify_room_card(self.databaseID, -modify_count, consume_type='createTeaHouse')

        def on_create_fail(fail_content):
            args = {"content": fail_content}
            self.call_client_func("createTeaHouseFail", args)

        # todo:remove 暂时不能开启比赛场
        # if _args["teaHouseType"] == 0:
        #     self.call_client_func('Notice', ['当前无法创建比赛场茶楼'])
        #     return

        if self.roomCard < Const.GameConfigJson.config_json['Hall']['teaHouseCreateDiamondConsume']:
            args = {"content": "创建失败，钻石不足"}
            self.call_client_func("createTeaHouseFail", args)
            return

        self.tea_house_mgr.create(self.databaseID, self.headImageUrl, _args["headImage"], _args["name"],
                                  _args["teaHouseType"], self.name, self.proxyType, self.gold,
                                  on_create_success, on_create_fail)

    def create_tea_house_room(self, _args, auto_create=False, room_end=False, old_room_id=-1, creator_entity=None,
                              record_sql=True):
        # 客户端发过来的请求参数
        client_args = copy.deepcopy(_args)

        def on_success(room_info):
            pass

        def on_fail(content):
            self.call_client_func("Notice", [content])

        tea_house_id = _args["teaHouseId"]
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity and self.client:
            self.call_client_func("Notice", ["冠名赛已解散"])
            return

        tea_house_entity.create_room(self.databaseID, client_args, auto_create=auto_create, on_success=on_success,
                                     on_fail=on_fail, room_end=room_end, old_room_id=old_room_id,
                                     creator_entity=creator_entity, record_sql=record_sql)

    def change_tea_house_room_config(self, _args):
        """
        修改冠名赛房间规则，无权限限制
        :param _args:
        :return:
        """

        def write_db_success(tea_house_entity):
            tea_house_entity.change_single_room_info_to_client(change_room, room_entity)

        def write_db_fail(content):
            pass

        tea_house_id = _args["teaHouseId"]
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            self.call_client_func("Notice", ["当前冠名赛不存在"])
            return
        change_room = None
        # 通过id找出想要修改的房间
        for room in tea_house_entity.rooms.values():
            if room.info['roomId'] == _args['roomId']:
                change_room = room
                break
        if not change_room:
            self.call_client_func("Notice", ["修改失败，房间不存在"])
            return
        if change_room and 'playerInGame' in change_room.info and len(change_room.info["playerInGame"]) != 0:
            self.call_client_func("Notice", ["无法修改，房间中还有玩家"])
            return
        # 修改配置标识
        _args["changeConfig"] = True
        # 新房间的创建者为群主
        room_entity = self.room_mgr.create_room(tea_house_entity.creatorDBID, _args)
        if room_entity:
            tea_house_entity.change_room_config(room_entity, change_room, write_db_success)
        else:
            self.call_client_func('Notice', ['修改失败'])

    def ret_gold(self, isModify=False, modify_count=0):
        """
        通知金币
        :return:
        """
        _data = {"gold": self.gold}
        self.call_client_func("retGold", _data)
        self.refresh_gold_to_room(isModify, modify_count=modify_count)

    def refresh_gold_to_room(self, isModify=False, modify_count=0):
        """
        通知游戏内刷新金币
        :return:
        """
        try:
            self.scene.cell.baseToCell(
                {"func": "refreshGold", "databaseId": self.userId, "count": modify_count if isModify else self.gold,
                 'isModify': isModify})
        except AttributeError as e:
            ERROR_MSG('Account::refresh_gold_to_room %s' % e)

    def sync_game_coin(self, tea_house_id):
        """
        同步比赛币到房间内
        :param tea_house_id:
        :return:
        """
        try:
            tea_house = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
            player = tea_house.memberInfo[self.userId]
            self.scene.cell.baseToCell(
                {"func": "syncGameCoin", "databaseId": self.userId, "count": player.game_coin})
        except AttributeError as e:
            ERROR_MSG('Account::sync_game_coin %s' % e)

    def retRoomCard(self):
        """
        通知钻石
        :return:
        """
        # 告知cell钻石数
        if self.cell:
            self.cell.baseToCell({"func": "retRoomCard", "roomCard": round(self.roomCard, 2)})
        _data = {"roomCard": round(self.roomCard, 2)}
        self.call_client_func("retRoomCard", _data)

    def retGoldIngot(self):
        """
        通知元宝
        :return:
        """
        # 告知cell元宝数
        if self.cell:
            self.cell.baseToCell({"func": "retGoldIngot", "goldIngot": round(self.goldIngot, 2)})
        _data = {"goldIngot": round(self.goldIngot, 2)}
        self.call_client_func("retGoldIngot", _data)

    def retPrize(self, prize_type):
        if prize_type == 0:
            prize_info = {"hf": self.get_prize(prize_type)}
            self.call_client_func("retHf", prize_info)
        elif prize_type == 1:
            prize_info = {"shopCard": self.get_prize(prize_type)}
            self.call_client_func("retShopCard", prize_info)

    def retNickName(self):
        """
        通知昵称
        :return:
        """
        _data = {"nickName": self.name}
        self.call_client_func("retNickName", _data)

    def retHeadImageUrl(self):
        """
        通知头像
       :return:
        """
        _data = {"headImageUrl": self.headImageUrl}
        self.call_client_func("retHeadImageUrl", _data)

    def send_partner_tea_house_partner_info_to_client(self, tea_house_id, account_db_id, level_filter=0):
        """
        发送合伙人自己或者名下成员信息
        :param level_filter:
        :param tea_house_id:茶楼id
        :param account_db_id:请求哪个合伙人
        :return:
        """
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        tea_houses_info = {}
        for k, v in tea_house_entity.memberInfo.items():
            if k == tea_house_entity.creatorDBID:
                continue
            # 如果有等级过滤器，只查看对应等级的成员
            if level_filter != 0:
                if v.level != level_filter:
                    continue
            if v.belong_to == account_db_id or k == account_db_id:
                performance_detail = {}
                if k in tea_house_entity.performance_detail.keys():
                    performance_detail = tea_house_entity.performance_detail[k]
                tea_houses_info[k] = {"name": v.name, "headImageUrl": v.head_image, "belongTo": v.belong_to,
                                      "invitationCode": v.invitation_code, "proportion": v.proportion,
                                      "level": v.level,
                                      "performance": v.performance, "performanceDetail": performance_detail,
                                      "turnInPerformance": round(v.turn_in_performance, 2)}
        self.call_client_func("PartnerTeaHousePartnerInfoResp", tea_houses_info)

    def send_partner_tea_house_partner_info_to_client_light(self, tea_house_id, account_db_id):
        """
        发送合伙人自己或者名下成员信息(轻量化版)
        :param tea_house_id:茶楼id
        :param account_db_id:请求哪个合伙人
        :return:
        """
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        tea_houses_info = {}
        for k, v in tea_house_entity.memberInfo.items():
            if k == tea_house_entity.creatorDBID:
                continue
            # 如果有等级过滤器，只查看对应等级的成员
            # if level_filter != 0:
            #     if v.level != level_filter:
            #         continue
            if v.belong_to == account_db_id or k == account_db_id:
                performance_detail = []
                if k in tea_house_entity.performance_detail.keys():
                    performance_detail = tea_house_entity.performance_detail[k]
                yesterday_performance, today_performance = self.get_today_and_yesterday(performance_detail)
                tea_houses_info[k] = {"name": v.name, "headImageUrl": v.head_image, "belongTo": v.belong_to,
                                      "invitationCode": v.invitation_code, "proportion": v.proportion,
                                      "level": v.level,
                                      "performance": v.performance,
                                      'todayData': today_performance,
                                      'yesterdayData': yesterday_performance,
                                      "turnInPerformance": round(v.turn_in_performance, 2)}
        self.call_client_func("PartnerTeaHousePartnerInfoResp_upData", tea_houses_info)

    def get_today_and_yesterday(self, performance_detail):
        yesterday = 0
        today = 0
        for p in performance_detail:
            _time = p['time']
            count = p['count']
            if self.yesterday_start <= _time <= self.yesterday_end:
                yesterday += count
            elif self.today_start <= _time <= self.today_end:
                today += count
        return yesterday, today

    def get_team_billing_with_page_index(self, account_db_id, tea_house_id, page_index):
        """
        战队成员抽水统计
        account_db_id:战队长id
        tea_house_id：茶楼ID 冠名赛id
        :return:
        """
        # 通过茶楼ID获取茶楼实体
        performance_info = self.get_all_team_billing(account_db_id, tea_house_id)
        performance_count = len(performance_info)
        # 计算总页数
        total_pages = math.ceil(len(performance_info)) / Const.partner_list_page_item

        # 按页码切片
        page_start = page_index * Const.partner_list_page_item
        page_end = page_start + Const.partner_list_page_item
        performance_list = performance_info[page_start:page_end]
        self.call_client_func("GetTeamBilling_new", {
            'performanceInfo': performance_list,
            'totalPages': int(total_pages),
            'performanceCount': performance_count
        })

    def get_all_team_billing(self, account_db_id, tea_house_id):
        """
                战队成员抽水统计
                account_db_id:战队长ID
                tea_house_id：茶楼ID
                :return:
                """
        # 通过茶楼ID获取茶楼实体
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        # 储存茶楼信息变量
        performance_info = []
        # 当天的时间
        today_date = datetime.date.today()
        # 初始当天时间（时间戳）
        today_start = int(time.mktime(today_date.timetuple()))
        # 初始前天时间（时间戳）
        yesterday_start = today_start - 86400
        # 如果account_db_id在茶楼业绩表里
        if account_db_id in tea_house_entity.performance_detail:
            # 获取业绩表信息
            performance_detail = tea_house_entity.performance_detail[account_db_id]
        else:
            # 初始化
            performance_detail = []
        # tea_house_entity.memberInfo.items()：获取冠名赛成员信息

        for k, v in tea_house_entity.memberInfo.items():
            # 不看楼主
            if k == tea_house_entity.creatorDBID:
                continue
            # 只看名下成员
            if v.belong_to == account_db_id:
                # 初始化昨天和今天的业绩信息
                today_performance = 0
                yesterday_performance = 0
                # 找到合伙人相关的收取记录
                for detail in performance_detail:
                    # 如果收取记录是这个人的
                    DEBUG_MSG("This Value was detail：", detail)
                    if detail['accountDBID'] == k:
                        # 记录收取
                        if yesterday_start <= detail['time'] < today_start:
                            yesterday_performance += detail['count']
                        elif detail['time'] >= today_start:
                            today_performance += detail['count']
                        # 找到合伙人的每一条收取
                _p = {"name": v.name, "headImage": v.head_image,
                      "today": round(today_performance, 2),
                      'dbid': v.db_id,
                      "yesterday": round(yesterday_performance, 2),
                      "total": round(v.turn_in_performance, 2)}
                performance_info.append(_p)
        return performance_info

    def get_team_billing(self, account_db_id, tea_house_id):
        """
        战队成员抽水统计
        account_db_id:战队长ID
        tea_house_id：茶楼ID
        :return:
        """
        # 通过茶楼ID获取茶楼实体
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        # 储存茶楼信息变量
        performance_info = {}
        # 当天的时间
        today_date = datetime.date.today()
        # 初始当天时间（时间戳）
        today_start = int(time.mktime(today_date.timetuple()))
        # 初始前天时间（时间戳）
        yesterday_start = today_start - 86400
        # 如果account_db_id在茶楼业绩表里
        if account_db_id in tea_house_entity.performance_detail:
            # 获取业绩表信息
            performance_detail = tea_house_entity.performance_detail[account_db_id]
        else:
            # 初始化
            performance_detail = []
        # tea_house_entity.memberInfo.items()：获取冠名赛成员信息

        for k, v in tea_house_entity.memberInfo.items():
            # 不看楼主
            if k == tea_house_entity.creatorDBID:
                continue
            # 只看名下成员
            if v.belong_to == account_db_id:
                # 初始化昨天和今天的业绩信息
                today_performance = 0
                yesterday_performance = 0
                # 找到合伙人相关的收取记录
                for detail in performance_detail:
                    # 如果收取记录是这个人的
                    if detail['accountDBID'] == k:
                        # 记录收取
                        if yesterday_start <= detail['time'] < today_start:
                            yesterday_performance += detail['count']
                        elif detail['time'] >= today_start:
                            today_performance += detail['count']
                        # 找到合伙人的每一条收取
                performance_info[k] = {"name": v.name, "headImage": v.head_image,
                                       "today": round(today_performance, 2),
                                       'dbid': v.db_id,
                                       "yesterday": round(yesterday_performance, 2),
                                       "total": round(v.turn_in_performance, 2)}
        self.call_client_func("GetTeamBilling", performance_info)

    def get_team_toll_info(self, account_db_id, tea_house_id):
        today_all_performance = 0
        yesterday_all_performance = 0
        two_day_all_performance = 0
        performance_info = {}
        # 通过茶楼ID获取茶楼实体
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        # 当天的时间
        today_date = datetime.date.today()
        # 初始当天时间（时间戳）
        today_start = int(time.mktime(today_date.timetuple()))
        # 初始前天时间（时间戳）
        yesterday_start = today_start - 86400
        # 如果account_db_id在茶楼业绩表里
        if account_db_id in tea_house_entity.performance_detail:
            # 获取业绩表信息
            performance_detail = tea_house_entity.performance_detail[account_db_id]
        else:
            # 初始化
            performance_detail = []
        for k, v in tea_house_entity.memberInfo.items():
            # 不看楼主
            if k == tea_house_entity.creatorDBID:
                continue
            # 只看名下成员
            if v.belong_to == account_db_id:
                # 找到合伙人相关的收取记录
                for detail in performance_detail:
                    # 如果收取记录是这个人的
                    if detail['accountDBID'] == k:
                        # 记录收取
                        if yesterday_start <= detail['time'] < today_start:
                            yesterday_all_performance += detail['count']
                        elif detail['time'] >= today_start:
                            today_all_performance += detail['count']
                        two_day_all_performance += v.turn_in_performance
                performance_info[v.belong_to] = {
                    "todayToll": today_all_performance, "yesterdayToll": yesterday_all_performance,
                    "allToll": two_day_all_performance
                }
        self.call_client_func("GetTeamTollInfo", performance_info)

    # 向客户端发送冠名赛信息
    def get_joined_tea_house_list(self):
        tea_houses = self.tea_house_mgr.get_tea_houses_by_account_dbid(self.databaseID)
        tea_houses_info = {}
        for k, v in tea_houses.items():
            tea_houses_info[v.teaHouseId] = {"headImage": v.headImage, "name": v.name, "teaHouseId": v.teaHouseId,
                                             "creator": v.creatorDBID, "creatorName": v.memberInfo[v.creatorDBID].name,
                                             "teaHouseType": v.teaHouseType, "alreadyCreateRooms": len(v.rooms),
                                             "identity": v.memberInfo[self.databaseID].level}
        self.call_client_func("HallTeaHouseInfoResp", {"teaHouses": tea_houses_info})

    def query_online_state(self, args):
        """
        查询在线状态
        :param args:
        :return:
        """
        tea_house = self.tea_house_mgr.get_tea_house_with_id(args["teaHouseId"])
        online_info = {}
        for k, v in tea_house.memberInfo.items():
            online_info[k] = False
            account_entity = KBEngine.globalData["AccountMgr"].mgr.get_account(k)
            if account_entity:
                if account_entity.client:
                    online_info[k] = True
        self.call_client_func("QueryOnlineStateResult", {"onlineInfo": online_info})

    def call_client_func(self, func_name, args):
        """
        :param func_name:
        :param args:
        :return:
        """
        self.init_log_filter()
        _args = args
        if len(str(args)) > 1400:
            _args = '该数组过长，无法显示'
        py_dic = {"args": args}
        _json_data = json.dumps(py_dic, ensure_ascii=False)
        if self.client is not None:
            DEBUG_MSG('[Account id %s]------>call_client_func %s, args %s' % (
            self.id, func_name, "..." if func_name in self.log_filter else _args))
            self.client.baseToClient(func_name, _json_data)
        else:
            # 机器人进入
            if func_name == "JoinRoomSuccess" and self.isBot == 1:
                self.scene.cell.baseToCell({"func": "onEnter", "id": self.id})

    # --------------------------------------------------------------------------------------------
    #                              System Callbacks
    # --------------------------------------------------------------------------------------------
    def onGetCell(self):
        """
        entity的cell部分被创建成功
        """
        # 好牌控制处理
        self.check_update_good_pai_control()

        # 将账号基本信息发送给cell
        self.reqAccountMutableInfo(["gold"])
        self.reqAccountMutableInfo(["gameCoin"])
        self.refresh_lucky_card_to_room()
        self.cell.baseToCell({"func": "initAccountInfo", "dic": self.get_account_info()})
        DEBUG_MSG("[Account id %s]------> onGetCell" % self.id)
        # 创建成功后关闭计时器
        self.delTimer(self._join_verification_failed)
        self._join_verification_failed = -1

    def get_game_coin(self, tea_house_id):
        """
        获取用户在指定茶楼的比赛币数量
        :param tea_house_id:
        :return:
        """
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            return
        return tea_house_entity.get_tea_house_player(self.databaseID).game_coin

    def onTimer(self, id, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param id		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """
        if id == self._timer:
            self.clear_entity()
        elif id == self._join_verification_failed:
            self.delTimer(self._join_verification_failed)
            self._join_verification_failed = -1
            # 如果重连回来，房间不在了，通知客户端关闭房间面板
            self.call_client_func('joinVerification', {'result': False})

    def clear_entity(self):
        DEBUG_MSG('clear_entity databaseId:%s,entity_id:%s,name:%s' % (self.databaseID, self.id, self.name))
        # 如果玩家在房间里，在玩家cell销毁后再销毁base
        if self.cell is not None:
            return
        DEBUG_MSG('销毁用户实体 databaseId:%s,entity_id:%s,name:%s' % (self.databaseID, self.id, self.name))
        self.destroy(False, True)

    def retAccountInfo(self):
        """
        推送玩家信息
        :return:
        """
        if self.isBot and self.ip == '0':
            self.ip = self.rand_ip()
        _args = {"accountName": self.name, "userId": self.userId, "gold": self.gold,
                 "roomCard": round(self.roomCard, 2),
                 "goldIngot": round(self.goldIngot, 2),
                 "dataBaseId": self.databaseID,
                 "phone": self.phone,
                 "ip": self.ip,
                 "frozenState": self.frozen,
                 "proxyType": self.proxyType,
                 "headImageUrl": self.headImageUrl, "gender": self.account_info["gender"],
                 "invitationCode": self.invitation_code,
                 "hfValue": self.get_prize(0),
                 "shopCardValue": self.get_prize(1)}
        self.call_client_func("retAccountInfo", _args)

    def rand_ip(self):
        ip = "%s.%s.%s.%s" % (
        random.randint(1, 223), random.randint(1, 254), random.randint(0, 254), random.randint(1, 254))
        return ip

    def onClientEnabled(self):
        """
        KBEngine method.
        该entity被正式激活为可使用， 此时entity已经建立了client对应实体。
        """
        INFO_MSG("account[%i] entities enable. entityCall:%s" % (self.id, self.client))
        if self.userId == 0:
            self.userId = self.databaseID
        if not self.name:
            if hasattr(self, '__ACCOUNT_NAME__'):
                _name = self.__ACCOUNT_NAME__
                if '*' in _name:
                    _l = list()
                    _l.append(_name[0])
                    _l.append(_name[2:len(_name)])
                    if _l[0] == 'w':
                        # 微信
                        self.req_wx_name(_l[1])

        self.ip = socket.inet_ntoa(struct.pack('@I', self.clientAddr[0]))
        self.on_login()
        self.online_state = True
        if self._timer is not None:
            self.delTimer(self._timer)
            self._timer = -1
        if self.proxyType != 0 and self.invitation_code == 0:
            self.invitation_code = self.account_mgr.random_invitation_code()
            self.account_mgr.invitation_codes[self.invitation_code] = self.databaseID
        if self.databaseID not in self.friends:
            self.friends.append(self.databaseID)
        self.retAccountInfo()
        # 发送待办事项
        self.get_to_do_list()
        # 发送分享、代理后台网址
        self.send_url_address()
        # 初始化分数控制信息
        TeaHouse.init_tea_house_player_score_control(self.databaseID)
        DEBUG_MSG("init_tea_house_player_score_control1 %s" % self.databaseID)
        DBCommand.load_account_control(self.databaseID, self.id, Account.set_control_param)

        # 发送冠名赛信息
        if self.cell and self.scene and self.scene.cell:
            _room = self.scene
            _args = {"type": _room.info["type"], "roomType": _room.info["roomType"], "roomId": _room.info["roomId"]}
            self.cell.baseToCell({"func": "clientStateChange", "state": "enable"})
            if self.scene and self.scene.cell:
                self.scene.cell.baseToCell({"func": "clientStateChange"})
            self.call_client_func("reconnectRoom", _args)
        else:
            self._join_verification_failed = self.addTimer(2, 0, 0)

    def send_url_address(self, url_type=None):
        """
        发送数据中的网页地址
        :return:
        """

        def cb(result):
            if len(result) != 0:
                url_address_es = []
                for row in result:
                    url_address_es.append({'type': str(row[1] if row[1] else '', encoding='utf-8'),
                                           'address': str(row[2] if row[2] else '', encoding='utf-8'),
                                           'description': str(row[3] if row[3] else '', encoding='utf-8')})
                self.call_client_func('urlAddress', {'addresses': url_address_es})

        DBCommand.check_out_url_address(cb, url_type=url_type)

    def onClientDeath(self):
        """
        KBEngine method.
        客户端对应实体已经销毁
        """
        DEBUG_MSG("Account[%i].onClientDeath:" % self.id)
        self._timer = self.addTimer(7200, 0, 0)
        if self.cell is not None:
            self.cell.baseToCell({"func": "clientStateChange", "state": "death"})
            if self.scene and self.scene.cell:
                self.scene.cell.baseToCell({"func": "clientStateChange"})
        self.online_state = False

    def onLoseCell(self):
        """
        :return:
        """
        # if self.clientDeath:
        #     self.destroy(False, True)
        DEBUG_MSG('onLoseCell dbid:%s' % self.databaseID)
        self.updatePlayingStage(PlayerStage.FREE)
        self.scene = None
        self.create_cell_cb = None
        if self.client:
            self.call_client_func('joinVerification', {'result': False})
        # 如果玩家cell端销毁的时候不在线，销毁base端
        if not self.client and self.isBot == 0:
            DEBUG_MSG('onLoseCell destroy base dbid:%s' % self.databaseID)
            self.destroy(False, True)
        if self.isBot == 1:
            Bots.returnBotId(self.databaseID)
            self.destroy(False, True)

    def onDestroy(self):
        """
        KBEngine method.
        entity销毁
        """
        self.on_offline()
        DEBUG_MSG("Account::onDestroy: %i." % self.id)

    def onLogOnAttempt(self, ip, port, password):
        """
        KBEngine method.
        客户端登陆失败时会回调到这里C
        """
        INFO_MSG("Account[%i]::onLogOnAttempt: ip=%s, port=%s, selfClient=%s" % (self.id, ip, port, self.client))
        return KBEngine.LOG_ON_ACCEPT

    # --------------------------------------------------------------------------------------------
    #                              others
    # --------------------------------------------------------------------------------------------
    def generateOrderId(self):
        _now = str(time.time())
        _ret = "%s%s" % (str(self.databaseID), _now)
        if '.' in _ret:
            return _ret.replace('.', '')
        return _ret

    def testCharge(self, _order_id, _dic):
        _data = json.dumps(_dic)
        KBEngine.charge(_order_id, self.databaseID, _data.encode(), self.testOnChargeCB)

    def testOnChargeCB(self, orderID, dbID, success, datas):
        DEBUG_MSG('[Account id %s]------------->onChargeCB orderID %s dbID %s success %s datas %s' % (
            self.id, orderID, dbID, success, datas))

    def getAlipayCode(self, _amount, _subject):
        _order_id = self.generateOrderId()
        _code = HttpRequest.reqAlipayOI(_order_id, _amount, _subject=_subject, _type="app")
        DEBUG_MSG('[Account id %s]------------->testGetCode _order_id %s _code %s ' % (self.id, _order_id, _code))
        return _order_id, _code

    def kick_out_tea_house_member(self, _args):
        """
        踢出冠名赛玩家
        :param _args:
        :return:
        """
        account_db_id = _args["accountDBID"]
        tea_house_id = _args["teaHouseId"]
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            player = tea_house_entity.get_tea_house_player(account_db_id)
            account = self.account_mgr.get_account(account_db_id)
            if player:
                #
                if account and account.cell:
                    self.call_client_func("Notice", ["踢出失败，玩家正在游戏中"])
                    return
                else:
                    def callback():
                        self.call_client_func("Notice", ["踢出成员成功"])
                        # 如果该成员打开该冠名赛的面板，通知被踢成员
                        if account and account.client_open_tea_house_state == tea_house_id:
                            account.call_client_func("Notice", ["你已被踢出冠名赛"])
                            account.call_client_func("DestroyTeaHouseSuccess", {})
                        if account:
                            account.get_joined_tea_house_list()
                    # 踢出房间
                    tea_house_entity.kick_out(account_db_id, self.databaseID, on_success=callback)
            else:
                self.call_client_func("Notice", ["当前玩家不在本冠名赛中"])
        else:
            self.call_client_func("Notice", ["当前冠名赛不存在"])

    def agree_join_tea_house(self, _args):
        """
        群主同意玩家加入茶楼
        :param _args:
        :return:
        """

        # 通知客户端
        def write_db_success(entity):
            joiner = _args["joinerDBId"]
            joiner_entity = self.account_mgr.get_account(joiner)
            if joiner_entity:
                joiner_entity.call_client_func("JoinTeaHouseSuccess", {"teaHouseId": _args["teaHouseId"]})
                joiner_entity.get_joined_tea_house_list()

        # 申请失败，通知客户端
        def write_db_fail():
            pass

        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        tea_house_player = tea_house_entity.memberInfo[self.databaseID]
        if tea_house_player and tea_house_player.level >= TeaHousePlayerLevel.Admin:
            tea_house_entity.join(_args["joinerDBId"], on_success=write_db_success, on_fail=write_db_fail)

    def agree_exit_tea_house(self, _args):
        # 通知客户端
        def write_db_success():
            exit_entity = self.account_mgr.get_account(_args["exitDBID"])
            if exit_entity:
                exit_entity.call_client_func("ExitTeaHouseSuccess", {})
                exit_entity.get_joined_tea_house_list()

        # 申请失败，通知客户端
        def write_db_fail():
            pass

        _exit_player = self.account_mgr.get_account(_args["exitDBID"])
        if _exit_player and _exit_player.scene and _exit_player.cell:
            if 'teaHouseId' in _exit_player.scene.info:
                if _exit_player.scene.info['teaHouseId'] == _args["teaHouseId"]:
                    self.call_client_func('Notice', ['同意退出失败，玩家正在游戏中'])
                    return

        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        tea_house_player = tea_house_entity.get_tea_house_player(self.databaseID)
        if tea_house_player and tea_house_player.level >= TeaHousePlayerLevel.Creator:
            tea_house_entity.player_exit(_args['exitDBID'], on_success=write_db_success, on_fail=write_db_fail)

    def refuse_exit_tea_house(self, _args):
        """
        群主拒绝玩家加入茶楼
        :param _args:
        :return:
        """

        # 申请成功，通知客户端
        def write_db_success():
            exit_entity = self.account_mgr.get_account(_args["exitDBID"])
            if exit_entity:
                exit_entity.call_client_func("ExitTeaHouseRefuse", {"teaHouseId": _args["teaHouseId"]})

        # 申请失败，通知客户端
        def write_db_fail():
            pass

        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        tea_house_player = tea_house_entity.get_tea_house_player(self.databaseID)
        if tea_house_player and tea_house_player.level >= TeaHousePlayerLevel.Creator:
            tea_house_entity.refuse_exit_application(_args["exitDBID"], on_success=write_db_success,
                                                     on_fail=write_db_fail)

    def refuse_join_tea_house(self, _args):
        """
        群主拒绝玩家加入茶楼
        :param _args:
        :return:
        """

        # 申请成功，通知客户端
        def write_db_success():
            joiner = _args["joinerDBId"]
            joiner_entity = self.account_mgr.get_account(joiner)
            if joiner_entity:
                joiner_entity.call_client_func("JoinTeaHouseRefuse", {"teaHouseId": _args["teaHouseId"]})

        # 申请失败，通知客户端
        def write_db_fail():
            pass

        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        tea_house_player = tea_house_entity.memberInfo[self.databaseID]
        if tea_house_player and tea_house_player.level >= TeaHousePlayerLevel.Admin:
            tea_house_entity.refuse_join_application(_args["joinerDBId"], on_success=write_db_success,
                                                     on_fail=write_db_fail)

    def add_friend(self, _args, on_success=None, is_invite_add=False):
        """
        冠名赛添加好友功能
        具体实现
        查询好友列表是否已存要添加的好友
        :param is_invite_add: 是否是邀请茶楼添加的好友
        :param on_success:
        :param _args:
        :return:
        """
        account_db_id = _args["accountDBID"]
        if account_db_id in self.friends:
            # 只有当不是邀请添加的好友时才发送
            if not is_invite_add:
                self.call_client_func("Notice", ["添加好友失败,你们已是好友"])
            return

        def callback(result):
            if not result:
                self.call_client_func("addFriendFail", ["id不存在，请检查id"])
                return

            self.friends.append(account_db_id)
            # self.writeToDB()
            self.call_client_func("addFriendSuccess", ["添加好友成功"])
            self.get_friend()
            if on_success:
                on_success()

            def on_success_callback(baseRef, databaseID, wasActive):
                if baseRef:
                    baseRef.friends.append(self.databaseID)
                    baseRef.get_friend()
                    baseRef.writeToDB()
                    if not wasActive:
                        baseRef.destroy()
                else:
                    pass

            KBEngine.createEntityFromDBID("Account", account_db_id, on_success_callback)

        DBCommand.check_out_account_by_db_id(account_db_id, callback)

    def add_friend_request(self, _args):
        """
        添加玩家请求
        :param _args:
        :return:
        """
        add_account = _args['accountDBID']
        DEBUG_MSG('add_friend_request accountDBId:%s' % add_account)
        if add_account == self.userId:
            self.call_client_func("Notice", ["无法添加自己为好友"])
            return
        if add_account in self.friends:
            self.call_client_func("Notice", ["添加好友失败,你们已是好友"])
            return

        add_account_entity = self.account_mgr.get_account(add_account)
        if add_account_entity and add_account_entity.client:
            DEBUG_MSG('add_friend_request accountNameRequest')
            add_account_entity.call_client_func('addFriendRequest', {'requester': self.databaseID,
                                                                     'accountName': self.name})
        else:
            DEBUG_MSG('add_friend_request accountNamelist')
            self.account_mgr.add_add_friend_in_to_do_list(self.headImageUrl, self.name,
                                                          _args['accountDBID'], self.userId)

        self.call_client_func('Notice', ['申请成功，请等待该玩家同意'])

    def add_friend_response(self, _args):
        """
        添加玩家回应
        :param _args:
        :return:
        """
        requester = _args['requester']
        result = _args['result']
        DEBUG_MSG('add_friend_response requester:%s result:%s' % (requester, result))
        if result:
            # 同意
            if requester in self.friends:
                self.call_client_func("Notice", ["添加好友失败,你们已是好友"])
                return

            if len(self.friends) > account_config()['friendsCountLimit']:
                self.call_client_func('Notice', ['添加好友失败，好友数已达上限'])
                return

            self.friends.append(requester)
            self.call_client_func("Notice", ["添加好友成功"])
            self.get_friend()

            def on_success_callback(baseRef, databaseID, wasActive):
                if baseRef:
                    baseRef.friends.append(self.databaseID)
                    if not wasActive:
                        baseRef.destroy()
                    else:
                        self.call_client_func("Notice", ["添加%s成功" % requester])
                        baseRef.call_client_func("addFriendsResponse", {"result": result})
                        baseRef.get_friend()

            KBEngine.createEntityFromDBID("Account", requester, on_success_callback)
        else:
            # 不同意
            try:
                content = '%s 拒绝成为你的好友' % self.databaseID
                self.account_mgr.get_account(requester).call_client_func('Notice', [content])
                self.account_mgr.get_account(requester).call_client_func('addFriendsResponse', {"result": result})
            except AttributeError as e:
                ERROR_MSG('add_friend_response %s' % e)

    def remove_friend(self, _args):
        """
        冠名赛删除好友功能
        具体实现
            好友列表调用remove方法实现列表得删除
            删除好友功能实现后需要刷新好友列表
        :param _args:
        :return:
        """
        account_db_id = _args["accountDBID"]
        if account_db_id in self.friends:
            self.friends.remove(account_db_id)
            self.call_client_func("removeFriendSuccess", ["删除好友成功"])
            self.get_friend()

            def on_success_callback(baseRef, databaseID, wasActive):
                if baseRef:
                    if self.databaseID in baseRef.friends:
                        baseRef.friends.remove(self.databaseID)
                    account = self.account_mgr.get_account(account_db_id)
                    if account:
                        baseRef.get_friend()
                    if not wasActive:
                        baseRef.destroy()
                else:
                    pass

            KBEngine.createEntityFromDBID("Account", account_db_id, on_success_callback)
        else:
            self.call_client_func("removeFriendFail", ["删除好友失败"])

    def give_gold(self, _args):
        """
        赠送金币
        """
        give_gold = _args["gold"]
        if give_gold < 0:
            self.call_client_func('Notice', ['赠送金币不能为负数'])
        if give_gold == 0:
            self.call_client_func('Notice', ['赠送金币不能为0'])
        gold = self.gold
        playerId = _args["playerId"]
        tea_house_id = _args["teaHouseId"]
        DEBUG_MSG("change_player_give_gold %s " % str(give_gold))
        DEBUG_MSG("change_player_self_gold %s " % str(self.gold))
        if gold > self.gold:
            self.call_client_func('Notice', ['赠送金币大于你所有金币'])
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            self.call_client_func('Notice', ['冠名赛不存在'])

        def _db_callback_count(result, rows, insertid, error):
            if result:
                DEBUG_MSG("change_player_gold %s " % playerId)
                DEBUG_MSG("change_player_gold_length %s " % str(len(result)))
                self.account_mgr.give_gold_modify(self.databaseID, -give_gold, tea_house_id)
                self.account_mgr.give_gold_modify(playerId, give_gold, tea_house_id)
                DEBUG_MSG("change_player_playerId %s " % str(playerId))
                addtime = int(time.time())
                user_name = self.name
                DEBUG_MSG("change_user_name %s " % str(user_name))
                player_name = str(result[0][3], 'utf-8')
                DEBUG_MSG("change_player_name %s " % str(player_name))
                command_sql = "INSERT INTO give_gold_info(user_id,player_id,gold,user_name,player_name, addtime) VALUES (%s, %s, %s, '%s', '%s', %s)" % (self.databaseID, playerId, give_gold, user_name, player_name, addtime)
                DEBUG_MSG("change_command_sql %s " % str(command_sql))
                KBEngine.executeRawDatabaseCommand(command_sql)
                self.call_client_func("giveGoldSuccess", ["赠送金币成功"])
            else:
                self.call_client_func("Notice", ["玩家不存在"])
        sql = "select * from tbl_account WHERE id=%s" % playerId
        tea_house_entity.set_game_coin(self.databaseID, self.gold - give_gold)
        DEBUG_MSG("command_sql 执行----------------%s" % str(self.gold))
        KBEngine.executeRawDatabaseCommand(sql, _db_callback_count)
        DEBUG_MSG("command_sql 执行----------------")

    def give_gold_record(self, _args):
        """
        赠送金币记录
        """
        account_db_id = _args["accountDBID"]
        page_index = _args['pageIndex']
        def callback(result, rows, insertid, error):
            user_total_gold = 0
            give_gold_record_info_list = []
            for info in result:
                id = int(info[0])
                user_id = int(info[1])
                user_name = str(info[4], "utf-8")
                player_name = str(info[5], "utf-8")
                player_id = int(info[2])
                gold = int(info[3])
                user_total_gold += gold
                add_time = int(info[6])
                give_gold_record_info_item = {}
                give_gold_record_info_item["id"] = id
                give_gold_record_info_item["accountDBID"] = user_id
                give_gold_record_info_item["playerId"] = player_id
                give_gold_record_info_item["gold"] = gold
                give_gold_record_info_item["addTime"] = add_time
                give_gold_record_info_item["user_name"] = user_name
                give_gold_record_info_item["player_name"] = player_name
                give_gold_record_info_list.append(give_gold_record_info_item)
            member_count = len(give_gold_record_info_list)
            # 计算总页数
            total_pages = math.ceil(len(give_gold_record_info_list) / Const.partner_list_page_item)
            page_start = page_index * Const.partner_list_page_item
            page_end = page_start + Const.partner_list_page_item
            partner_info_list = give_gold_record_info_list[page_start:page_end]
            map ={'partnerInfo': partner_info_list,"totalPages": int(total_pages),"memberCount": member_count,"user_total_gold": user_total_gold,"player_total_gold": 0}
            try:
                self.get_total_gold(account_db_id, map)
            except:
                pass
            self.call_client_func("getGiveGoldRecords", map)
        command_sql = 'select id,user_id,player_id, gold, user_name, player_name, addtime from give_gold_info where user_id=%s' % account_db_id
        DEBUG_MSG("command_sql 执行----------------%s" % str(command_sql))
        KBEngine.executeRawDatabaseCommand(command_sql, callback)

    def get_history_commission_record(self, _args):
        account_db_id = _args["accountDBID"]
        tea_house_id = _args["teaHouseId"]
        page_index = _args["pageIndex"]
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            self.call_client_func('Notice', ['冠名赛不存在'])
        def callback(result, rows, insertid, error):
            record_info_list = []
            if not record_info_list:
                self.call_client_func("historyCommissionResult", {
                    'partnerInfo': record_info_list,
                    "totalPages": 0,
                    "memberCount": 0,
                })
                return
            for info in result:
                item = dict()
                item['accountDBID'] = int(info[0])
                self.select_user(item['accountDBID'], item)
                item['time'] = int(info[2])
                item['count'] = int(info[3])
                item['double_count'] = float(info[4])
                item['room_type'] = str(info[6], 'utf-8')
                record_info_list.append(item)
            member_count = len(record_info_list)
            # 计算总页数
            total_pages = math.ceil(len(record_info_list) / Const.partner_list_page_item)
            page_start = page_index * Const.partner_list_page_item
            page_end = page_start + Const.partner_list_page_item
            partner_info_list = record_info_list[page_start:page_end]
            self.call_client_func("historyCommissionResult", {
                'partnerInfo': partner_info_list,
                "totalPages": int(total_pages),
                "memberCount": member_count,
            })
        command_sql = "select sm_accountDBID, sm_superior, sm_time, sm_count, sm_performanceDetail, sm_proportion, sm_roomType from tbl_teahouseperformance " \
                      "where sm_superior=%s" % account_db_id

        DEBUG_MSG("[get_history_commission_record]command_sql 执行----------------%s" % str(command_sql))
        KBEngine.executeRawDatabaseCommand(command_sql, callback)


    def extract_commission_record(self, _args):
        """
        佣金提取记录
        """
        account_db_id = _args["accountDBID"]
        page_index = _args['pageIndex']
        def callback(result, rows, insertid, error):
            record_list = []
            if not result:
                self.call_client_func("extractCommissionRecordResult", {
                    'partnerInfo': record_list,
                    "totalPages": 0,
                    "memberCount": 0,
                })
                return
            for info in result:
                item = dict()
                item['count'] = float(info[0])
                item['addtime'] = int(info[1])
                record_list.append(item)
            member_count = len(record_list)
            # 计算总页数
            total_pages = math.ceil(len(record_list) / Const.partner_list_page_item)
            page_start = page_index * Const.partner_list_page_item
            page_end = page_start + Const.partner_list_page_item
            partner_info_list = record_list[page_start:page_end]
            self.call_client_func("extractCommissionRecordResult", {
                'partnerInfo': partner_info_list,
                "totalPages": int(total_pages),
                "memberCount": member_count,
            })

        command_sql = 'select count, addtime from extract_commission where accountDBID=%s' % account_db_id
        DEBUG_MSG("command_sql 执行----------------%s" % str(command_sql))
        KBEngine.executeRawDatabaseCommand(command_sql, callback)

    def select_user(self, accountDBID, item):
        command_sql = "select sm_headImageUrl,sm_name from tbl_account where sm_userId=%s" % accountDBID
        def callback(result, rows, insertid, error):
            headImageUrl = result[0][0]
            item['headImageUrl'] = headImageUrl
            item['name'] = result[0][1]
        DEBUG_MSG("[select_user]command_sql 执行----------------%s" % str(command_sql))
        KBEngine.executeRawDatabaseCommand(command_sql, callback)


    def extract_commission(self, _args):
        """
        提取佣金
        """
        account_db_id = _args["accountDBID"]
        tea_house_id = _args["teaHouseId"]
        extractMoney = _args["extractMoney"]
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            self.call_client_func('Notice', ['冠名赛不存在'])

        def callback(result, rows, insertid, error):
            if not result:
                self.call_client_func('Notice', ['无佣金记录'])
            try:
                update_count = float(result[0][0]) - extractMoney
                update_performanceDetail = float(result[0][1]) - extractMoney
                if float(extractMoney) > float(result[0][0]):
                    self.call_client_func('Notice', ['提取佣金不能大于当前佣金'])
                    return

                sql_command = "update commssion_total set addtime=%s, count=%s,  performanceDetail= %s where superior=%s" % (
                int(time.time()), update_count, update_performanceDetail)
                DEBUG_MSG('modify_total_commssion update_sql:%s' % sql_command)
                KBEngine.executeRawDatabaseCommand(sql_command, None)
                self.sava_extract_commission(account_db_id, extractMoney)
                self.call_client_func("extractCommissionResult", ["提取成功"])
                self.account_mgr.give_gold_modify(self.databaseID, extractMoney, tea_house_id)
                tea_house_entity.set_game_coin(self.databaseID, self.gold + extractMoney)
            except:
                self.call_client_func("extractCommissionResult", ["提取失败"])


        sql_command = "select count, performanceDetail from commssion_total where superior=%s" % account_db_id
        DEBUG_MSG('modify_total_commssion select_sql:%s' % sql_command)
        KBEngine.executeRawDatabaseCommand(sql_command, callback)

    def sava_extract_commission(self, account_db_id, extractMoney):
        sql_command = "INSERT INTO extract_commission(accountDBID, count, addtime)" % (account_db_id, extractMoney, int(time.time()))
        KBEngine.executeRawDatabaseCommand(sql_command, None)

    def get_commission(self, _args):
        """
        我的佣金 今日贡献
        """
        account_db_id = _args["accountDBID"]
        tea_house_id = _args["teaHouseId"]
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            self.call_client_func('Notice', ['冠名赛不存在'])
        self.get_today_commission(account_db_id)
        self.get_history_commission(account_db_id)
        self.get_surplus_commission(account_db_id)
        DEBUG_MSG("[todayCommission]+++++++++++++++++++ %s" % str(self.today_commission))
        DEBUG_MSG("[historyCommission]+++++++++++++++++++ %s" % str(self.history_commission))
        DEBUG_MSG("[surplusCommission]+++++++++++++++++++ %s" % str(self.surplus_commission))
        self.call_client_func("CommissionResult", {
            "todayCommission": float(self.today_commission),
            "historyCommission": float(self.history_commission),
            "surplusCommission": float(self.surplus_commission)
        })

    def get_today_commission(self, account_db_id):
        t = time.localtime(time.time())
        today_zero_time = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00', t), '%Y-%m-%d %H:%M:%S'))
        last_today_time = time.mktime(time.strptime(time.strftime('%Y-%m-%d 23:59:59', t), '%Y-%m-%d %H:%M:%S'))

        today_count_commission, today_double_commission = 0.0, 0.0

        def callback(result, rows, insertid, error):
            today_double_commission = 0
            for info in result:
                DEBUG_MSG("[get_today_commission] callback------------")
                DEBUG_MSG(info)
                item = dict()
                item["accountDBID"] = account_db_id
                item["superiorDBID"] = info[0]
                double_commission = float(info[3])
                today_double_commission += double_commission
            self.today_commission = today_double_commission
            DEBUG_MSG("[get_today_commission]self.history_commission------%s" % str(self.today_commission))
        command_sql = "select sm_accountDBID, sm_superior, sm_count,sm_performanceDetail,sm_proportion from " \
                      "tbl_teahouseperformance where sm_superior=%s and sm_time > %s and sm_time<%s " % (
                      account_db_id, today_zero_time, last_today_time)

        KBEngine.executeRawDatabaseCommand(command_sql, callback)
        return today_count_commission

    def get_history_commission(self, account_db_id):
        def callback(result, rows, insertid, error):
            total_commission = 0
            for info in result:
                DEBUG_MSG("[get_history_commission] callback------------")
                DEBUG_MSG(info)
                item = dict()
                item["accountDBID"] = account_db_id
                item["superiorDBID"] = info[0]
                double_commission = float(info[3])
                total_commission += double_commission
            self.history_commission = total_commission
            DEBUG_MSG("[get_history_commission]callback 执行返回----------------%s" % str(self.history_commission))
        command_sql = "select sm_accountDBID, sm_superior, sm_count,sm_performanceDetail,sm_proportion from " \
                      "tbl_teahouseperformance where sm_superior=%s" % (
                          account_db_id)
        KBEngine.executeRawDatabaseCommand(command_sql, callback)


    def get_surplus_commission(self, account_db_id):

        def callback(result, rows, insertid, error):
            total_commission = 0
            for info in result:
                DEBUG_MSG("[get_surplus_commission] callback------------")
                DEBUG_MSG(info)
                item = dict()
                item["accountDBID"] = account_db_id
                item["superiorDBID"] = info[0]
                double_commission = float(info[3])
                total_commission += double_commission
            self.surplus_commission = total_commission
            DEBUG_MSG("[get_surplus_commission]callback 执行返回----------------%s" % str(self.history_commission))

        command_sql = "select sm_accountDBID, sm_superior, sm_count,sm_performanceDetail,sm_proportion from " \
                      "tbl_teahouseperformance where sm_superior=%s" % (
                          account_db_id)

        DEBUG_MSG("[get_history_commission]command_sql 执行----------------%s" % str(command_sql))
        KBEngine.executeRawDatabaseCommand(command_sql, callback)



    def get_total_gold(self, player_id, map):
        def callback(result, rows, insertid, error):
            player_total_gold = 0
            for info in result:
                gold = info[3]
                player_total_gold += int(gold)
            map["player_total_gold"] = player_total_gold

        command_sql = 'select id,user_id,player_id, gold, user_name, player_name, addtime from give_gold_info where player_id=%s' % player_id
        KBEngine.executeRawDatabaseCommand(command_sql, callback)


    def is_friend(self, people):
        people_relation = {}
        for p in people:
            if p in self.friends:
                people_relation[p] = 1
            else:
                people_relation[p] = 0
        return people_relation

    def get_friend(self):

        if len(self.friends) == 0:
            return {}

        friends_info = {}

        def callback(result, rows, insertid, error):
            for info in result:
                friend_id = str(info[0], 'utf-8')
                name = str(info[1], 'utf-8')
                headImage = str(info[2], 'utf-8')
                friends_info[friend_id] = {"name": name, "headImage": headImage}
            self.call_client_func("getFriends", friends_info)

        id_str = '('
        for friend_id in self.friends:
            id_str += str(friend_id)
            id_str += ','
        # 舍弃最后一位逗号
        id_str = id_str[:-1]
        id_str += ')'
        command_sql = 'select id,sm_name,sm_headImageUrl from tbl_account where id in %s' % id_str
        KBEngine.executeRawDatabaseCommand(command_sql, callback)

    def frozen_account(self):
        self.call_client_func("FrozenAccount")
        pass

    def send_wx_share_content(self):
        pass

    def bless(self):
        """
        祈福
        :return:
        """
        self.blessCountToday += 1
        if self.cell:
            self.cell.baseToCell({'func': 'retTodayBlessCount', 'todayBlessCount': self.blessCountToday})

        # 超出免费标准
        if self.blessCountToday > Const.GameConfigJson.config_json['Hall']['blessRoomCardStandard']:
            room_card_consume = Const.GameConfigJson.config_json['Hall']['blessRoomCardConsume']
            self.account_mgr.modify_room_card(self.userId, - room_card_consume, consume_type='bless')

    def binding_proxy_by_user_id(self, user_id):
        """
        E绑定代理
        扫码绑定代理
        if 要绑定的人不是代理：
            找到要绑定人的上级
            if 绑定人的上级也不是代理：
                找到绑定人的上级的上级
                if 绑定人的上级的上级也不是代理：
                    找到定人的上级的上级的上级
                        ......
                else 上级的上级。。。是代理:
                    绑定自己的上级为这个人
        循环查找上级的过程采用递归，直至找到是代理的上级 return
        :param user_id:
        :return:
        """

        def on_success_callback(baseRef, databaseID, wasActive):
            if baseRef:
                # 如果要绑定人的邀请码是0,同时也不是代理
                if baseRef.invitation_code == 0 and baseRef.proxyType == 0:
                    # 找到上级绑定的邀请码
                    _belong_to = baseRef.belong_to
                    # 上级的user_id
                    if _belong_to != 0:
                        account_db_id = self.account_mgr.invitation_codes[_belong_to]
                        # 递归
                        self.binding_proxy_by_user_id(account_db_id)
                else:
                    self.belong_to = baseRef.invitation_code
                    self.call_client_func("BindingProxySuccess", ["绑定成功"])
                    self.roomCard += int(Const.GameConfigJson.config_json['Hall']['bindingProxyGiftDiamondCount'])
                    self.retRoomCard()
                    self.writeToDB()
                    if not wasActive:
                        baseRef.destroy()
                    return
            else:
                pass

        KBEngine.createEntityFromDBID("Account", user_id, on_success_callback)

    def binding_proxy(self, _args):
        """
        绑定代理
        :param _args:
        :return:
        """
        invitation_code = _args["invitationCode"]
        if invitation_code not in self.account_mgr.invitation_codes.keys():
            self.call_client_func("BindingProxyFail", ["绑定失败，邀请码不存在"])
            return
        if self.belong_to != 0:
            self.call_client_func("BindingProxyFail", ["绑定失败，已绑定代理"])
            return

        def on_success_callback(baseRef, databaseID, wasActive):
            if baseRef:
                if self.proxyType >= baseRef.proxyType and self.databaseID != databaseID:
                    self.call_client_func("BindingProxyFail", ["绑定失败"])
                    return
                self.belong_to = invitation_code
                self.call_client_func("BindingProxySuccess", ["绑定成功"])
                self.roomCard += int(Const.GameConfigJson.config_json['Hall']['bindingProxyGiftDiamondCount'])
                self.retRoomCard()
                self.writeToDB()
                if not wasActive:
                    baseRef.destroy()
            else:
                pass

        # 绑定人的userId
        account_db_id = self.account_mgr.invitation_codes[invitation_code]
        KBEngine.createEntityFromDBID("Account", account_db_id, on_success_callback)

    def query_record(self, _args):
        """
        查询战绩
        :param _args: 客户端发来的参数
        :return:
        """
        _data = {}
        _rooms = []
        is_tea_house_creator = False
        is_up = False

        def can_get_record(chapter_info):
            """
            判断玩家是否参与了此游戏(坐下、钓鱼),如果没有战绩为空
            :param chapter_info:
            :return:
            """
            DEBUG_MSG('query_record::chapter_info %s' % chapter_info)
            player_db_id_s = []
            if type(chapter_info['playerInfo']) == dict:
                player_db_id_s = [x['userId'] for x in chapter_info['playerInfo'].values()]
            elif type(chapter_info['playerInfo']) == list:
                player_db_id_s = [x['userId'] for x in chapter_info['playerInfo']]

            DEBUG_MSG('query_record::player_db_id_s %s' % player_db_id_s)
            if player_db_id_s and self.userId in player_db_id_s:
                return True
            return False

        chapter_infos_count = 0

        def on_success_callback(baseRef, databaseID, wasActive):
            nonlocal chapter_infos_count
            if baseRef:
                chapter_infos_count += 1
                baseRef.initFromDB()
                if len(baseRef.chapterInfos) != 0:
                    _data[databaseID] = {}
                    # 剔除历史战绩字段
                    for k1, v1 in baseRef.chapterInfos.items():
                        if k1 == 'historyRecord':
                            continue
                        if k1 == 'challengeControl':
                            continue
                        _data[databaseID][k1] = v1
                    # 过滤战绩，如果玩家只是观战，没有此房间战绩
                    # 如果是群主，不过滤
                    if not can_get_record(_data[databaseID]) and not is_up:
                        _data.pop(databaseID)
                if not wasActive:
                    Account.history_room[baseRef.roomId] = baseRef
                baseRef.last_query_tick = time.time()
            else:
                chapter_infos_count += 1
            DEBUG_MSG('_rooms:%s,chapter_count%s' % (len(_rooms), chapter_infos_count))
            if chapter_infos_count == len(_rooms):
                # 按时间倒序排序
                _new_data = collections.OrderedDict()
                _tmp_data = collections.OrderedDict(
                    sorted(_data.items(), key=lambda t: t[1]['createRoomTime'], reverse=True))
                ncount = 0
                for k, v in _tmp_data.items():
                    _new_data[k] = v
                    ncount += 1
                    if ncount >= Const.Record.record_limit:
                        break
                self.call_client_func("queryRecordResult", _new_data)
                chapter_infos_count = 0

        # 请求冠名赛战绩
        if "houseType" in _args and _args["houseType"] == 1:
            # houseType : 0: 大厅战绩  1：冠名赛战绩
            _tea_house_id = _args["teaHouseId"]
            _teaHouse = self.tea_house_mgr.get_tea_house_with_id(_tea_house_id)
            if not _teaHouse:
                self.call_client_func('Notice', ['此茶楼不存在'])
                return
            _rooms = []
            # 判断请求者是不是茶楼楼主
            if _teaHouse.creatorDBID == self.userId:
                is_tea_house_creator = True
            # 判断请求者是不是目标的上级
            is_up = _teaHouse.is_down_player(_args['accountDBID'], self.userId)
            if is_tea_house_creator:
                is_up = True
            # -1 默认查询所有人
            if _args['accountDBID'] == -1:
                _rooms = _teaHouse.get_all_history_rooms(_args['roomType'])
            else:
                _rooms = _teaHouse.get_member_history_rooms(_args['roomType'], _args['accountDBID'])
            DEBUG_MSG("query_record houseType = 1 rooms:%s" % _rooms)
        elif "houseType" in _args and _args["houseType"] == 0:
            DEBUG_MSG("query_record houseType = 0 self.rooms:%s" % self.rooms)

            if _args["roomType"] not in self.rooms:
                self.call_client_func("queryRecordResult", {})
                return
            _rooms = self.rooms[_args["roomType"]]
            DEBUG_MSG("query_record houseType = 0 rooms:%s" % _rooms)

        if len(_rooms) == 0:
            self.call_client_func("queryRecordResult", _data)
            return
        for _room in _rooms:
            DEBUG_MSG('_room%s' % _room)
            # 循环创建房间实体
            KBEngine.createEntityFromDBID(_args["roomType"], int(_room), on_success_callback)

    def get_chats(self, database_id, num=50):
        # 如果发送消息的不是本人好友
        # if database_id not in self.friends:
        # return
        if database_id not in self.chat_log.keys():
            self.chat_log[database_id] = {'is_read': 'false', 'log': []}
            self.call_client_func('GetAllChats', [])
            return
        if num == 50:
            num = len(self.chat_log[database_id]['log'])
            self.call_client_func('GetAllChats', self.chat_log[database_id]['log'][0:num])
        else:
            num = len(self.chat_log[database_id]['log'])
            self.call_client_func('GetOneChat', self.chat_log[database_id]['log'][num - 1:num])

    def read_chats(self, database_id):
        self.chat_log[database_id]['is_read'] = 'true'

    def get_un_read(self):
        un_read = []
        for k, v in self.chat_log.items():
            if v['is_read'] == 'false' and k in self.friends:
                un_read.append(k)
        self.call_client_func('GetUnRead', {'unRead': un_read})

    def chat(self, _args):
        # chat_log={1234:[{},{},{}]}
        def on_success(baseRef, databaseID, wasActive):
            receiver = baseRef
            if receiver_id not in self.chat_log.keys():
                self.chat_log[receiver_id] = {'is_read': 'false', 'log': []}
            # 长度50
            if len(self.chat_log[receiver_id]['log']) > 50:
                del self.chat_log[receiver_id]['log'][0]
            self.chat_log[receiver_id]['log'].append(chat)

            if self.databaseID not in receiver.chat_log.keys():
                receiver.chat_log[self.databaseID] = {'is_read': 'false', 'log': []}
            # 长度50
            if len(receiver.chat_log[self.databaseID]['log']) > 50:
                del receiver.chat_log[self.databaseID]['log'][0]
            receiver.chat_log[self.databaseID]['log'].append(chat)
            receiver.chat_log[self.databaseID]['is_read'] = 'false'

            if wasActive:
                receiver.get_chats(self.databaseID, 1)
                receiver.get_un_read()
            self.get_chats(receiver_id, 1)

        chat = {'sender': self.databaseID, 'content': _args['content'], 'time': int(time.time())}
        receiver_id = _args['receiver']

        KBEngine.createEntityFromDBID('Account', receiver_id, on_success)

    def updatePlayingStage(self, stage):
        """更新玩家玩游戏的阶段"""
        DEBUG_MSG("updatePlayingStage %s" % stage)
        self.playing_stage = stage
        self.room_chapter_count = 0
        self.cur_chapter_count = 0

    @property
    def today_start(self):
        today_date = datetime.date.today()
        today_stamp = time.mktime(today_date.timetuple())
        return int(today_stamp)

    @property
    def today_end(self):
        return self.today_start + 86399

    @property
    def yesterday_start(self):
        return self.today_start - 86400

    @property
    def yesterday_end(self):
        return self.today_end - 86400

    def get_redemption_list(self):
        """
        请求兑换榜
        :return:
        """
        _data = {}

        def callback(result, rows, insertid, error):
            if result is None:
                self.call_client_func("GetRedemptionList", {})
                return
            for info in result:
                _id = int(str(info[0], 'utf-8'))
                _userId = int(str(info[2], 'utf-8'))
                _time = int(str(info[3], 'utf-8'))
                _gift_id = int(str(info[4], 'utf-8'))
                _des = Const.RedeemGift[_gift_id]
                _data[_id] = {"accountDBID": _userId, "time": _time, "giftId": _gift_id, "des": _des, "id": _id}
                if len(_data) == len(result):
                    _vs = list(_data.values())
                    _vs.sort(key=lambda x: -x["giftId"])
                    self.call_client_func("GetRedemptionList", _vs)

        command_sql = 'SELECT * FROM tbl_redeemgift ORDER BY sm_giftID DESC;'
        KBEngine.executeRawDatabaseCommand(command_sql, callback)

    # 获取系统消息列表
    def get_sys_notice(self):
        self.sys_notice['read'] = 1
        try:
            notice = self.sys_notice['notice']
            notice.reverse()
            self.call_client_func('getSysNotice', notice)
        except Exception as e:
            DEBUG_MSG('err_msg%s' % e)
        self.get_un_read_sys_notice()

    # 获取未读系统消息,返回0为有未读消息 1为无未读消息
    def get_un_read_sys_notice(self):
        try:
            if self.sys_notice['read'] == 0:
                self.call_client_func('GetUnReadSysNotice', 0)
            elif self.sys_notice['read'] == 1:
                self.call_client_func('GetUnReadSysNotice', 1)
        except:
            self.call_client_func('GetUnReadSysNotice', 1)

    def get_tea_house_lucky_card_consume(self, _args):
        tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(_args["teaHouseId"])
        if tea_house_entity:
            today_date = datetime.date.today()
            today_end = int(time.mktime(today_date.timetuple()) + 86399)
            yesterday_end = today_end - 86400
            yesterday_count = 0
            today_count = 0
            DEBUG_MSG('get_tea_house_lucky_card_consume %s' % tea_house_entity.todayLuckyCardConsume)
            for date_lucky_card_consume in tea_house_entity.todayLuckyCardConsume:
                if date_lucky_card_consume["date"] == today_end:
                    today_count = date_lucky_card_consume['luckyCardConsume']
                elif date_lucky_card_consume["date"] == yesterday_end:
                    yesterday_count = date_lucky_card_consume['luckyCardConsume']
            self.call_client_func("teaHouseTodayLuckyCardConsume", {'today': int(today_count),
                                                                    'yesterday': int(yesterday_count)})
        else:
            self.call_client_func("Notice", ["找不到此冠名赛"])

    def in_tea_house_room(self, tea_house_id):
        if self.cell:
            DEBUG_MSG('in game')
            if 'teaHouseId' in self.scene.info.keys():
                return self.scene and self.scene.info['teaHouseId'] == tea_house_id and self.scene.cell
            else:
                return False
        else:
            return False

    def invite_join_room_req(self, _args):
        # 邀请进入房间
        invited_user_id = _args["invitedUserId"]
        if not self.scene:
            return

        game_type = self.scene.roomInfos["type"]
        room_id = self.scene.roomId
        room_type = self.scene.roomInfos["roomType"]
        tea_house_id = self.scene.roomInfos["teaHouseId"]
        anonymity = self.scene.roomInfos["anonymity"]

        # room = self.room_mgr.get_room(_args["type"], room_type, room_id),
        # if not room:
        #     return

        # 不能邀请自己
        if invited_user_id == self.userId:
            self.call_client_func("Notice", ["无法邀请自己"])
            return
        invited_entity = self.account_mgr.get_account(invited_user_id)
        if invited_entity and invited_entity.client and invited_entity.playing_stage != PlayerStage.PLAYING:
            if invited_entity.scene and invited_entity.scene.roomId == room_id:
                self.call_client_func("Notice", ["无法邀f请同房间玩家"])
                return

            # 被邀请玩家在线
            invited_entity.call_client_func("InviteJoinRoom", {"inviterName": self.name, "type": game_type,
                                                               "typeName": Const.
                                             get_name_by_type(game_type),
                                                               "roomType": room_type, "roomId": room_id,
                                                               "teaHouseId": tea_house_id,
                                                               "inviterDBID": self.databaseID, "anonymity": anonymity,
                                                               "haveCell": True if invited_entity.cell else False})

        # InviteJoinTeaHouseResp
        self.call_client_func("Notice", ["邀请已发送"])

    def invite_join_room_response(self, _args):
        """
        玩家拒绝进入房间
        :param _args:
        :return:
        """
        requester = _args['requester']
        result = _args['result']
        DEBUG_MSG('Invite_Join_Room_response requester:%s result:%s' % (requester, result))
        # if not result:
        # 不同意
        try:
            content = '%s 拒绝进入你的房间' % self.databaseID
            self.account_mgr.get_account(requester).call_client_func('Notice', [content])
            self.account_mgr.get_account(requester).call_client_func('InviteJoinRoomResponse', {"result": result})
        except AttributeError as e:
            ERROR_MSG('Invite_Join_Room_response %s' % e)

    def init_log_filter(self):
        if not Account.log_filter:
            Account.log_filter.add('RoomType1JsonConfig')
            Account.log_filter.add('RoomType4JsonConfig')
            Account.log_filter.add('RoomType5JsonConfig')
            Account.log_filter.add('RoomType6JsonConfig')
            Account.log_filter.add('RoomType7JsonConfig')
            Account.log_filter.add('RoomType8JsonConfig')
            Account.log_filter.add('RoomType10JsonConfig')
            Account.log_filter.add('RoomType11JsonConfig')
            Account.log_filter.add('RoomType12JsonConfig')
            Account.log_filter.add('RoomType13JsonConfig')
            Account.log_filter.add('RoomType14JsonConfig')
            Account.log_filter.add('RoomType15JsonConfig')
            Account.log_filter.add('RoomType16JsonConfig')
            Account.log_filter.add('RoomType18JsonConfig')
            Account.log_filter.add('RoomType21JsonConfig')
            Account.log_filter.add('RoomType22JsonConfig')
            Account.log_filter.add('RoomType23JsonConfig')
            Account.log_filter.add('TeaHouseJsonConfig')
            Account.log_filter.add('HallJsonConfig')
            Account.log_filter.add('GetChallengeRollNotice')

    @classmethod
    def clear_history_room(cls):
        """清除4个小时没有使用的战绩查询用的房间实体"""
        cur_tick = time.time()
        dellist = []
        for k, v in cls.history_room.items():
            if cur_tick - v.last_query_tick > 4 * 60 * 60:
                dellist.append(k)
        DEBUG_MSG("定时清除历史房间信息 %s" % dellist)
        for k in dellist:
            v = cls.history_room[k]
            del cls.history_room[k]
            v.destroy()

    def debug_msg(self, str):
        DEBUG_MSG('[Account--------DBID:%s,MSG:%s]' % (self.userId, str(str)))

    def get_my_prize(self):
        """从数据库中取出奖品，发给玩家"""

        def get_prize_callback(prizes):
            self.call_client_func("GetMyPrize", {"myPrize": prizes})

        DBCommand.get_my_prize(self.databaseID, get_prize_callback)

    def get_all_prize(self):
        """从数据库中取出所有玩家的奖品
        供客户端界面滚动
        假数据
        """

        def get_prize_callback(prizes):
            self.call_client_func("GetChallengeAwardsRank", {"allPrize": prizes})

        DBCommand.get_all_prize(get_prize_callback)

    def get_challenge_roll_notice(self):
        def get_prize_callback(prizes):
            data = []
            for v in prizes:
                str = "恭喜 %s 中了%s%s" % (v["userName"], v["prizeNum"], "元话费" if v["prizeType"] == 0 else "元京东购物卡")
                data.append(str)
            self.call_client_func("GetChallengeRollNotice", {"content": data})

        DBCommand.get_chapter_prize(get_prize_callback)

    def get_prize(self, prize_type):
        """奖品"""
        if prize_type in self.myPrize:
            return int(self.myPrize[prize_type])
        return 0

    def change_prize(self, prize_type, num):
        if prize_type not in self.myPrize:
            self.myPrize[prize_type] = num
        else:
            self.myPrize[prize_type] += num

    def get_challenge_prize(self, prize_code):
        """网页查看获奖信息，需要发送昵称
        需要验证码，30分钟过期
        """
        the_prize = {"telephone": 0, "shopCard": 0, "name": self.name, "code": 200}
        if hasattr(self, "redeem_ticket"):
            if time.time() - self.redeem_ticket < 30 * 60 and prize_code is not None and self.redeem_code == prize_code:
                the_prize["telephone"] = self.get_prize(0)
                the_prize["shopCard"] = self.get_prize(1)
                the_prize["name"] = self.name
        return json.dumps(the_prize)

    def redeem_prize(self, prize_code, prize_type, prize_num):
        """网页兑换奖品
        需要验证码，30分钟过期
        """
        redeem_result = False
        remain_num = 0
        DEBUG_MSG("redeem_prize %s %s %s" % (prize_code, prize_type, prize_num))
        if hasattr(self, "redeem_ticket"):
            if ((
                        time.time() - self.redeem_ticket < 30 * 60) and self.redeem_code == prize_code) or prize_code == 123456321:
                if prize_type == 0:
                    if self.get_prize(0) >= prize_num:
                        self.change_prize(0, 0 - prize_num)
                        remain_num = self.get_prize(0)
                        redeem_result = True
                elif prize_type == 1:
                    if self.get_prize(1) >= prize_num:
                        self.change_prize(1, 0 - prize_num)
                        remain_num = self.get_prize(1)
                        redeem_result = True

        return redeem_result, remain_num

    def check_have_challenge_room(self, challengeLevel):
        if self.scene and self.scene.info["roomType"] == "challenge":
            # 已在房间，直接重连
            if self.scene.info["level"] == challengeLevel:
                _args = {"type": self.scene.info["type"], "roomType": self.scene.info["roomType"],
                         "roomId": self.scene.info["roomId"]}
                self.call_client_func("reconnectRoom", _args)
                return True
            else:
                self.call_client_func("BackToChallengeRoomConfirm", {})
                return True
        return False
