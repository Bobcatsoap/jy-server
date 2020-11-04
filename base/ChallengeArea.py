# -*- coding: utf-8 -*-
import copy
import datetime
import json
import math
import random
import sys
import time

import KBEngine
import math

import Const
import ChallengeRoomDefaultParam
from KBEDebug import DEBUG_MSG, ERROR_MSG


def get_account_entity_with_db_id(account_db_id):
    return KBEngine.globalData["AccountMgr"].mgr.get_account(account_db_id)


def account_mgr():
    """
    获取accountMgr 实例对象
    :return:
    """
    return KBEngine.globalData["AccountMgr"].mgr


def room_mgr():
    """
    获取roomMgr 实例对象
    :return:
    """
    return KBEngine.globalData["RoomManager"].mgr


def challenge_manager():
    """
    获取goldSessionMgr 实例对象
    :return:
    """
    return KBEngine.globalData["ChallengeAreaManager"].mgr


class ChallengeArea(KBEngine.Entity):
    # 金币场等级
    sessionLevel = 0
    # 金币场成员信息
    memberInfo = {}
    # 金币场房间
    rooms = {}
    # 金币限制
    goldLimit = []
    # 底分
    baseScore = 0
    # 匿名开关
    anonymityButton = False
    # 修改规则开关
    changeRoomConfigButton = False
    # 房费
    roomRate = 0

    def __init__(self):
        KBEngine.Entity.__init__(self)

    def create(self, gold_session_level: int, on_success=None, on_fail=None):
        """
        创建挑战赛场
        :param gold_session_level:金币场等级
        :param on_success:
        :param on_fail:
        :return:
        """

        def callback(boolean, entity):
            if boolean:
                if on_success:
                    on_success(entity)
            else:
                if on_fail:
                    on_fail("数据库写入失败")

        session_config = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(gold_session_level)]
        self.sessionLevel = gold_session_level
        self.baseScore = session_config['baseScore']
        self.goldLimit = session_config['goldLimit']
        self.anonymityButton = session_config['showAnonymityButton']
        self.changeRoomConfigButton = session_config['showChangeRoomConfigButton']
        self.roomRate = session_config['roomRate']
        self.writeToDB(callback)

    def init(self):
        pass

    def clear_challenge_count(self):
        for k, v in self.memberInfo:
            _player = self.memberInfo[k]
            _player.challenge_count = 0

    def join_and_open(self, player_databaseID):
        """
        加入并打开挑战赛场
        :return:
        """
        # if player_databaseID in self.memberInfo:
        #     return
        player = get_account_entity_with_db_id(player_databaseID)
        _config = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(self.sessionLevel)]
        min_gold_limit = _config['goldLimit'][0]
        max_gold_limit = _config['goldLimit'][1]
        if max_gold_limit == -1:
            max_gold_limit = sys.maxsize

        if player.goldIngot > max_gold_limit or player.goldIngot < min_gold_limit:
            player.call_client_func('Notice', ['金币不符合入场限制'])
            return

        if player_databaseID in self.memberInfo:
            challenge_player = self.memberInfo[player_databaseID]
        else:
            # 添加玩家
            challenge_player = ChallengePlayer(player_databaseID, player.name, player.headImageUrl)
            self.memberInfo[player_databaseID] = challenge_player

        # 开启挑战次数限制，并且小于最多挑战次数
        if (_config['maxChallengeCount'] > 0) and (challenge_player.challenge_count >= _config['maxChallengeCount']):
            player.call_client_func('Notice', ['已达到最大挑战次数'])
            return

        # if challenge_player.client_open_session_state == self.sessionLevel:
        #     return
        player.client_open_challenge_state = self.sessionLevel

        # 发送成功回调
        player.call_client_func('JoinChallengeSuccess', {})
        # 发送挑战赛场信息
        self.update_challenge_area_info_to_client(single_send_account=player_databaseID)
        # 创建挑战赛房间
        self.create_challenge_room(self.sessionLevel, player_databaseID)

    def exit_and_close(self, player_databaseID):
        """
        退出挑战赛
        :return:
        """
        try:
            player = get_account_entity_with_db_id(player_databaseID)
            player.client_open_challenge_state = -1
            # self.memberInfo.pop(player_databaseID)
            # 发送成功回调
            player.call_client_func('ExitChallengeSuccess', {})
        except AttributeError as e:
            DEBUG_MSG(e)



    # ----------------------------------通知客户端冠名赛信息的函数----------------------------------#

    def update_challenge_area_info_to_client(self, single_send_account=-1):
        """
        将挑战赛最新信息发送给请求者
        :param single_send_account: 单独发送给某个成员
        :return:
        """
        DEBUG_MSG("update_challenge_area_info_to_client")
        gold_session_info = {
            'sessionLevel': self.sessionLevel,
            'anonymityButton': self.anonymityButton,
            'changeRoomConfigButton': self.changeRoomConfigButton,
            'roomRate': self.roomRate
        }

        # # 指定发送
        if single_send_account in self.memberInfo.keys():
            player = get_account_entity_with_db_id(single_send_account)
            if player and player.client:
                if int(player.client_open_challenge_state) == int(self.sessionLevel):
                    player.call_client_func("RefreshSessionInfo", {"goldSessionInfo": gold_session_info})
        # 全体发送
        else:
            for k, v in self.memberInfo.items():
                player = get_account_entity_with_db_id(k)
                if player and player.client:
                    if int(player.client_open_challenge_state) == int(self.sessionLevel):
                        player.call_client_func("RefreshSessionInfo", {"goldSessionInfo": gold_session_info})

    # ----------------------------------重载配置函数----------------------------------#
    def reload_config(self, config):
        """
        重载配置
        :param config:
        :return:
        """
        # DEBUG_MSG('reload_config config%s,level%s' % (config, self.sessionLevel))
        self.baseScore = config['baseScore']
        self.goldLimit = config['goldLimit']
        self.anonymityButton = config['showAnonymityButton']
        self.changeRoomConfigButton = config['showChangeRoomConfigButton']
        self.roomRate = config['roomRate']

    # ----------------------------------房间函数----------------------------------#
    def create_challenge_room(self, session_level, creator_id, is_fake=False):
        """
        创建挑战赛房间
        :param is_fake: 是否是假房间，假房间会加满机器人
        :param session_level:
        :param args:
        :return:
        """
        DEBUG_MSG("create_challenge_room")
        room_default = ChallengeRoomDefaultParam.RoomDefault
        args = room_default['RoomType6']
        if args is None:
            return

        # 获取金币场实体、配置
        # session = self.get_challenge_area_by_level(session_level)
        session_config = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(self.sessionLevel)]
        # 读取配置文件中的房间数量上限
        room_count_limit = session_config['roomCountLimit']
        # 同类房间不能超过上限
        if len(self.rooms) >= room_count_limit:
            return

        self.create_room(args, creator_id, is_fake=is_fake)

    def create_room(self, args, creator_id, call_back=None, is_modify=False, is_fake=False):
        """
        创建房间并加入挑战赛
        :param args: 创建房间参数
        :param call_back: 回调
        :param is_modify: 是否是修改房间
        :param is_fake: 是否是假房间
        :return:
        """
        DEBUG_MSG("create_room")
        # todo:楼主指定为某人
        # creator = 565076
        args = args.copy()
        # 初始化金币场默认创建房间配置
        self.init_default_config(args)

        def callback(baseRef, databaseID, wasActive):
            account_mgr().add(baseRef)
            room_entity = room_mgr().create_room(creator_id, args, is_fake=is_fake)
            # 通知金币场增加房间
            if room_entity:
                self.add_room(room_entity, is_modify)
                if call_back:
                    call_back(room_entity)

        KBEngine.createEntityFromDBID("Account", creator_id, callback)

    def init_default_config(self, args):
        """
        初始化金币场默认配置
        :param args:
        :return:
        """
        DEBUG_MSG("create_room")
        # 所有底分取自配置文件，房卡消耗为房主支付
        args['payType'] = 0
        args['gameLevel'] = self.goldLimit[0]
        args['level'] = self.sessionLevel
        args['roomRate'] = self.roomRate
        args['witness'] = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(self.sessionLevel)]['witness']
        _config = {}
        # todo:初始化房间规则
        if args['type'] == 'RoomType6':
            _config = ChallengeRoomDefaultParam.RoomDefault['RoomType6']
            args['baseScore'] = _config['baseScore'][0]

    def add_room(self, room_entity, is_modify=False):
        """
        增加房间
        :param is_modify: 是否是修改规则
        :param room_entity:
        :return:
        """
        DEBUG_MSG('challenge add_room new_room:%s,room_id:%s' % (room_entity, room_entity.info['roomId']))

        self.rooms[room_entity.info['roomId']] = room_entity
        DEBUG_MSG('challenge add_room new_room:%s self.rooms:%s' % (room_entity, self.rooms))
        # 如果是修改规则，不发送插入消息
        # if not is_modify:
        #     self.insert_single_room_info_to_client(room_entity)

    def remove_room(self, room_id, on_success):
        """
        从列表中移除房间,通常为从cell端解散房间后调用，on_success 通常为通知cell调用destroySpace
        如果移除的是假房间，再次创建一个假房间
        :param room_id:
        :param on_success:
        :return:
        """
        try:
            room_entity = self.rooms[room_id]
            del self.rooms[room_id]
            # gold_session_manager().auto_create_room_with_judgement(room_entity.info, room_entity.is_fake,ignore_judge=True)
            on_success()
            # self.delete_single_room_info_to_client(room_entity)
        except KeyError:
            return

    def change_single_room_info_to_client(self, old_room_entity, new_room_entity):
        """
        修改客户端单个房间信息
        :param old_room_entity:
        :param new_room_entity:
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)

            if account_entity:
                if account_entity.client and account_entity.client_open_challenge_state == self.sessionLevel:
                    _response = {"oldRoom": old_room_entity.info, "newRoom": new_room_entity.info}
                    account_entity.call_client_func('ChangeGoldSessionSingleRoomInfo', _response)

    def change_room_config(self, old_room, _args):
        """
        修改房间配置，使用新房间替换旧房间
        :param _args: 新房间参数
        :param old_room:要修改的房间
        :return:
        """
        def call_back(new_room):
            for k, room in self.rooms.items():
                if room == old_room:
                    self.rooms.pop(k)
                    break
            # 解散之前的房间
            # 通知房间解散
            old_room.cell.baseToCell({"func": "disbandTeaHouseRoomByCreator"})
            self.change_single_room_info_to_client(old_room, new_room)

        self.create_room(_args, call_back=call_back, is_modify=True)

    # def insert_single_room_info_to_client(self, room_entity):
    #     """
    #     插入客户端单个房间信息
    #     :param room_entity:
    #     :return:
    #     """
    #     for k, v in self.memberInfo.items():
    #         account_entity = get_account_entity_with_db_id(k)
    #         if account_entity:
    #             if account_entity.client and account_entity.client_open_challenge_state == self.sessionLevel:
    #                 _total_page = self.get_rooms_total_page(room_entity.info["type"], room_entity.info["anonymity"])
    #                 _rooms = self.get_rooms_with_room_type(room_entity.info["type"], room_entity.info["anonymity"])
    #                 _response = {"room": room_entity.info, "totalPage": _total_page, "roomCount": len(_rooms)}
    #                 account_entity.call_client_func('GoldSessionInsertSingleRoomInfo', _response)
    #
    # def delete_single_room_info_to_client(self, room_entity):
    #     """
    #     删除单个房间信息
    #     :param room_entity:
    #     :return:
    #     """
    #     for k, v in self.memberInfo.items():
    #         account_entity = get_account_entity_with_db_id(k)
    #         if account_entity:
    #             if account_entity.client and account_entity.client_open_challenge_state == self.sessionLevel:
    #                 _total_rooms = self.get_rooms_with_room_type(room_entity.info["type"],
    #                                                              room_entity.info["anonymity"])
    #                 _total_pages = self.get_rooms_total_page(room_entity.info["type"], room_entity.info["anonymity"])
    #                 _response = {"roomId": room_entity.info["roomId"], "totalCount": len(_total_rooms),
    #                              "totalPage": _total_pages}
    #                 account_entity.call_client_func('DeleteSingleRoomInfo', _response)

    def update_single_room_info_to_client(self, room_info):
        """
        更新客户端单个房间信息
        :param room_info:
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_challenge_state == self.sessionLevel:
                    _response = {room_info["roomId"]: room_info["playerInGame"]}
                    account_entity.call_client_func('UpdateSingleRoomInfo', _response)

    def update_single_room_state_to_client(self, room_entity):
        """
        更新客户端单个房间状态
        :param room_entity:
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_challenge_state == self.sessionLevel:
                    _response = {room_entity.info["roomId"]: room_entity.info["started"]}
                    account_entity.call_client_func('UpdateSingleRoomState', _response)

    def get_rooms_total_page(self, room_type, anonymity):
        """
        获取房间信息总页数
        :param room_type:
        :param anonymity:
        :return:
        """
        _rooms = self.get_rooms_with_room_type(room_type, anonymity)
        room_count = len(_rooms)
        _config = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(self.sessionLevel)]
        if room_count % _config['roomListPageItem'] == 0:
            total_pages = room_count / Const.room_list_page_item
            if total_pages != 0:
                total_pages -= 1
        else:
            total_pages = math.floor(room_count / Const.room_list_page_item)
        return int(total_pages)

    def get_rooms_with_page(self, room_type, anonymity, page_index):
        """
        获取指定页码房间信息
        :param room_type:
        :param anonymity:
        :param page_index:
        :return:
        """
        _room_ids = []
        _rooms = {}
        # 开始位置
        page_start = page_index * Const.room_list_page_item
        # 结束位置
        page_end = page_start + Const.room_list_page_item
        for k, v in self.rooms.items():
            try:
                if v.info["type"] == room_type and v.info["anonymity"] == anonymity:
                    _room_ids.append(k)
            except AttributeError as e:
                ERROR_MSG('TeaHouse get_rooms_with_page %s' % e)
            except KeyError as e:
                ERROR_MSG('TeaHouse get_rooms_with_page %s' % e)
        index = 0
        for _room_id in _room_ids:
            if page_start <= index < page_end:
                _info = self.rooms[_room_id].info
                _rooms[_room_id] = _info
            index += 1
        return _rooms

    def get_rooms_with_room_type(self, room_type, anonymity):
        """
        获取类型的所有房间
        :param room_type:
        :param anonymity:
        :return:
        """
        _rooms = {}
        for k, v in self.rooms.items():
            try:
                if v.info["type"] == room_type and v.info["anonymity"] == anonymity:
                    _rooms[k] = v
            except AttributeError as e:
                ERROR_MSG('GoldSession get_rooms_with_room_type %s' % e)
            except KeyError as e:
                ERROR_MSG('GoldSession get_rooms_with_room_type %s' % e)
        return _rooms

    def get_member(self, databaseId):
        return self.memberInfo[databaseId]

    @staticmethod
    def fragment_rand(all_range, percent_range, fragment_num):
        """
        没选中：False
        选中：True
        """
        if fragment_num < 10:
            fragment_num = 10

        all_range_section = all_range / fragment_num
        percent_range_section = percent_range / fragment_num

        rand_num = random.randint(0, all_range)
        section_index = 0
        for i in range(1, fragment_num + 1):
            if rand_num < i * all_range_section:
                section_index = i - 1
                break

        # DEBUG_MSG("fragment_rand %s %s %s" % (all_range, percent_range, fragment_num))
        # DEBUG_MSG("fragment_rand %s %s %s" % (section_index * all_range_section, section_index * all_range_section + percent_range_section, rand_num))
        if rand_num > section_index * all_range_section + percent_range_section:
            return False
        return True

    def get_challenge_result_control(self, databaseId):
        """
        挑战赛输赢控制
         # 根据挑战赛等级，计算胜率 2:1/3； 5:1/4；
         # 10：1/4； 20:1/5； 100:1/5； 200:1/5
         # 10：1/1000； 20:1/1000； 100:1/1000； 200:1/1000
        # 已连输3大局，胜率为1/2
        # 已连赢2大局，胜率为1/6
        # 计算出胜或输的小局
        """
        win_percent = 0
        # Const.ServerGameConfigJson.config_json["ChallengeArea"][str(room.info['level'])]
        cfg = Const.ServerGameConfigJson.config_json["ChallengeArea"][str(self.sessionLevel)]
        win_percent = cfg["winPercent"]
        streak_win_percent = cfg["streakWinPercent"]
        streak_fail_percent = cfg["streakFailPercent"]
        if win_percent > 1 or win_percent < 0:
            win_percent = 0.16
        if streak_win_percent > 1 or streak_win_percent < 0:
            streak_win_percent = 0.001
        if streak_fail_percent > 1 or streak_fail_percent < 0:
            streak_fail_percent = 0.3
        win_range = 10000 * win_percent

        control = dict()
        player = self.get_member(databaseId)
        if len(player.challenge_result) >= 2 and player.challenge_result[-1] == 1:
            if player.challenge_result[-2] == 1:
                win_range = 10000 * streak_win_percent
        elif len(player.challenge_result) >= 3 and player.challenge_result[-1] == 0:
            if player.challenge_result[-2] == 0 and player.challenge_result[-3] == 0:
                win_range = 10000 * streak_fail_percent

        control["control"] = 0 if self.fragment_rand(10000, win_range, 10) else 1
        control["controlCount"] = player.control_pai_count
        control["controlPercent"] = player.challenge_result.count(1)*10
        DEBUG_MSG("get_challenge_result_control %s %s %s" % (win_range, control["control"], control["controlCount"]))
        return control


class ChallengePlayer:
    # 数据库id
    db_id = -1
    # 名称
    name = ""
    head_image = ""
    # client_open_challenge_state = -1
    # 挑战次数
    challenge_count = 0
    # 挑战结果
    challenge_result = []

    def __init__(self, db_id: int, name: str, head_image: str):
        self.db_id = db_id
        self.name = name
        self.head_image = head_image
        self.challenge_count = 0
        self.challenge_result = []
        # 剩余几张时开始换牌
        self.control_pai_count = 12
        # self.client_open_challenge_state = -1
        DEBUG_MSG("ChallengePlayer init %s" % self)

    def set_challenge_result(self, challenge_result, pai_count):
        self.challenge_count += 1
        if pai_count < 1:
            pai_count = 1
        elif pai_count > 17:
            pai_count = 17
        self.control_pai_count = pai_count
        self.challenge_result.append(challenge_result)
        if len(self.challenge_result) > 10:
            self.challenge_result.pop(0)


