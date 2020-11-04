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
import GoldSessionRoomDefaultConst

from KBEDebug import DEBUG_MSG, ERROR_MSG


def get_account_entity_with_db_id(account_db_id):
    return KBEngine.globalData["AccountMgr"].mgr.get_account(account_db_id)


def account_mgr():
    """
    获取accountMgr
    :return:
    """
    return KBEngine.globalData["AccountMgr"].mgr


def room_mgr():
    """
    获取roomMgr
    :return:
    """
    return KBEngine.globalData["RoomManager"].mgr


def gold_session_manager():
    """
    获取goldSessionMgr
    :return:
    """
    return KBEngine.globalData["GoldSessionManager"].mgr


class GoldSession(KBEngine.Entity):
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
        创建金币场
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

        session_config = Const.ServerGameConfigJson.config_json['GoldSession'][str(gold_session_level)]
        self.sessionLevel = gold_session_level
        self.baseScore = session_config['baseScore']
        self.goldLimit = session_config['goldLimit']
        self.anonymityButton = session_config['showAnonymityButton']
        self.changeRoomConfigButton = session_config['showChangeRoomConfigButton']
        self.roomRate = session_config['roomRate']
        self.writeToDB(callback)

    def join_and_open(self, player_databaseID):
        """
        加入并打开金币场
        :return:
        """
        # if player_databaseID in self.memberInfo:
        #     return
        player = get_account_entity_with_db_id(player_databaseID)
        _config = Const.ServerGameConfigJson.config_json['GoldSession'][str(self.sessionLevel)]
        min_gold_limit = _config['goldLimit'][0]
        max_gold_limit = _config['goldLimit'][1]
        if max_gold_limit == -1:
            max_gold_limit = sys.maxsize

        if player.gold > max_gold_limit or player.gold < min_gold_limit:
            player.call_client_func('Notice', ['金币不符合入场限制'])
            return

        player.client_open_gold_session_state = self.sessionLevel
        # 添加玩家
        self.memberInfo[player_databaseID] = GoldSessionPlayer(player_databaseID, player.name, player.headImageUrl)
        # 发送成功回调
        player.call_client_func('JoinGoldSessionSuccess', {})
        # 发送金币场信息
        self.update_gold_session_info_to_client(single_send_account=player_databaseID)

    def exit_and_close(self, player_databaseID):
        """
        关闭并退出金币场
        :return:
        """
        try:
            player = get_account_entity_with_db_id(player_databaseID)
            player.client_open_gold_session_state = -1
            self.memberInfo.pop(player_databaseID)
            # 发送成功回调
            player.call_client_func('ExitGoldSessionSuccess', {})
            # self.update_gold_session_info_to_client()
        except AttributeError as e:
            DEBUG_MSG(e)

    # ----------------------------------通知客户端冠名赛信息的函数----------------------------------#

    def update_gold_session_info_to_client(self, single_send_account=-1):
        """
        将冠名赛最新信息发送给请求者
        :param single_send_account: 单独发送给某个成员
        :return:
        """
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
                if int(player.client_open_gold_session_state) == int(self.sessionLevel):
                    player.call_client_func("RefreshSessionInfo", {"goldSessionInfo": gold_session_info})
        # 全体发送
        else:
            for k, v in self.memberInfo.items():
                player = get_account_entity_with_db_id(k)
                if player and player.client:
                    if int(player.client_open_gold_session_state) == int(self.sessionLevel):
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
    def create_room(self, args, call_back=None, is_modify=False, is_fake=False):
        """
        创建房间并加入金币场
        :param args: 创建房间参数
        :param call_back: 回调
        :param is_modify: 是否是修改房间
        :param is_fake: 是否是假房间
        :return:
        """
        # todo:楼主指定为某人
        creator = 565076
        args = args.copy()
        # 初始化金币场默认创建房间配置
        self.init_default_config(args)

        def callback(baseRef, databaseID, wasActive):
            account_mgr().add(baseRef)
            room_entity = room_mgr().create_room(creator, args, is_fake=is_fake)
            # 通知金币场增加房间
            if room_entity:
                self.add_room(room_entity, is_modify)
                if call_back:
                    call_back(room_entity)

        KBEngine.createEntityFromDBID("Account", creator, callback)

    def init_default_config(self, args):
        """
        初始化金币场默认配置
        :param args:
        :return:
        """
        # 所有底分取自配置文件，房卡消耗为房主支付
        args['payType'] = 0
        args['gameLevel'] = self.goldLimit[0]
        args['level'] = self.sessionLevel
        args['roomRate'] = self.roomRate
        args['witness'] = Const.ServerGameConfigJson.config_json['GoldSession'][str(self.sessionLevel)]['witness']
        _config = {}
        # todo:初始化房间规则
        if args['type'] == 'RoomType1':
            _config = GoldSessionRoomDefaultConst.RoomDefault['room1']
            args['betBase'] = _config['betBase'][self.sessionLevel - 1]
        elif args['type'] == 'RoomType4':
            _config = GoldSessionRoomDefaultConst.RoomDefault['room4']
            args['betBase'] = _config['betBase'][self.sessionLevel - 1]
        elif args['type'] == 'RoomType6':
            _config = GoldSessionRoomDefaultConst.RoomDefault['room6']
            args['baseScore'] = _config['baseScore'][self.sessionLevel - 1]
        elif args['type'] == 'RoomType7':
            _config = GoldSessionRoomDefaultConst.RoomDefault['room7']
            args['baseScore'] = _config['baseScore'][self.sessionLevel - 1]
        elif args['type'] == 'RoomType8':
            _config = GoldSessionRoomDefaultConst.RoomDefault['room8']
            args['potBase'] = _config['potBase'][self.sessionLevel - 1]
            args['minStake'] = _config['minStake'][self.sessionLevel - 1]
        elif args['type'] == 'RoomType10':
            _config = GoldSessionRoomDefaultConst.RoomDefault['room10']
            args['potBase'] = _config['potBase'][self.sessionLevel - 1]
            args['minStake'] = _config['minStake'][self.sessionLevel - 1]
        elif args['type'] == 'RoomType11':
            _config = GoldSessionRoomDefaultConst.RoomDefault['room11']
            args['minStake'] = _config['minStake'][self.sessionLevel - 1]

    def add_room(self, room_entity, is_modify=False):
        """
        增加房间
        :param is_modify: 是否是修改规则
        :param room_entity:
        :return:
        """
        DEBUG_MSG('GoldSession add_room new_room:%s,room_id:%s' % (room_entity, room_entity.info['roomId']))

        self.rooms[room_entity.info['roomId']] = room_entity
        DEBUG_MSG('GoldSession add_room new_room:%s self.rooms:%s' % (room_entity, self.rooms))
        # 如果是修改规则，不发送插入消息
        if not is_modify:
            self.insert_single_room_info_to_client(room_entity)

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
            gold_session_manager().auto_create_room_with_judgement(room_entity.info, room_entity.is_fake,ignore_judge=True)
            on_success()
            self.delete_single_room_info_to_client(room_entity)
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
                if account_entity.client and account_entity.client_open_gold_session_state == self.sessionLevel:
                    _response = {"oldRoom": old_room_entity.info, "newRoom": new_room_entity.info}
                    account_entity.call_client_func('ChangeGoldSessionSingleRoomInfo', _response)

    # 修改房间配置
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

    def insert_single_room_info_to_client(self, room_entity):
        """
        插入客户端单个房间信息
        :param room_entity:
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_gold_session_state == self.sessionLevel:
                    _total_page = self.get_rooms_total_page(room_entity.info["type"], room_entity.info["anonymity"])
                    _rooms = self.get_rooms_with_room_type(room_entity.info["type"], room_entity.info["anonymity"])
                    _response = {"room": room_entity.info, "totalPage": _total_page, "roomCount": len(_rooms)}
                    account_entity.call_client_func('GoldSessionInsertSingleRoomInfo', _response)

    def delete_single_room_info_to_client(self, room_entity):
        """
        删除单个房间信息
        :param room_entity:
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_gold_session_state == self.sessionLevel:
                    _total_rooms = self.get_rooms_with_room_type(room_entity.info["type"],
                                                                 room_entity.info["anonymity"])
                    _total_pages = self.get_rooms_total_page(room_entity.info["type"], room_entity.info["anonymity"])
                    _response = {"roomId": room_entity.info["roomId"], "totalCount": len(_total_rooms),
                                 "totalPage": _total_pages}
                    account_entity.call_client_func('DeleteSingleRoomInfo', _response)

    def update_single_room_info_to_client(self, room_info):
        """
        更新客户端单个房间信息
        :param room_info:
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_gold_session_state == self.sessionLevel:
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
                if account_entity.client and account_entity.client_open_gold_session_state == self.sessionLevel:
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
        _config = Const.ServerGameConfigJson.config_json['GoldSession'][str(self.sessionLevel)]
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


class GoldSessionPlayer:
    # 数据库id
    db_id = -1
    # 名称
    name = ""
    head_image = ""

    def __init__(self, db_id: int, name: str, head_image: str):
        self.db_id = db_id
        self.name = name
        self.head_image = head_image
