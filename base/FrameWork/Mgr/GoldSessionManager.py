# -*- coding: utf-8 -*-
import random

import KBEngine

import Const

import GoldSessionRoomDefaultConst
from KBEDebug import *

from FrameWork.Mgr import Manger


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


def get_gold_session_from_db(call_back=None):
    """
    从数据库检出金币场
    :param call_back:
    :return:
    """

    def query_success(result, rows, insertid, error):
        session_id = []
        session_level = []
        for i in result:
            session_id.append(int(i[0]))
            session_level.append(int(i[1]))
        if call_back:
            call_back(session_level, session_id)

    _command = "select id,sm_sessionLevel from tbl_goldsession"
    KBEngine.executeRawDatabaseCommand(_command, query_success)


class GoldSessionManager(Manger):
    """
    金币场管理器
    """
    gold_sessions = {}

    def __init__(self):
        Manger.__init__(self)

        def on_get_session_level_and_id(level_s, id_s):

            DEBUG_MSG('level_s:%s,id_s:%s' % (level_s, id_s))

            # 创建实体成功加入字典
            def on_create_gold_session_success(baseRef, databaseID, wasActive):
                if baseRef:
                    self.gold_sessions[databaseID] = baseRef
                    # 自动创建房间
                    # self.auto_create_rooms_on_start(baseRef.sessionLevel)

            # 从数据库创建实体到内存
            for i in id_s:
                KBEngine.createEntityFromDBID("GoldSession", i, on_create_gold_session_success)

            # 如果没有某个场次，创建场次
            if GoldSessionLevel.junior not in level_s:
                self.create(GoldSessionLevel.junior)
            if GoldSessionLevel.normal not in level_s:
                self.create(GoldSessionLevel.normal)
            if GoldSessionLevel.advanced not in level_s:
                self.create(GoldSessionLevel.advanced)

        # 创建
        get_gold_session_from_db(call_back=on_get_session_level_and_id)

    def start_reload_config_timer(self):
        self.add_timer(1, 20, 0)

    def create(self, gold_session_level):
        """
        创建,创建时加载json配置
        :param gold_session_level:
        :return:
        """

        def success(entity):
            self.gold_sessions[entity.databaseID] = entity
            # 创建成功时自动创建房间
            # self.auto_create_rooms_on_start(entity.sessionLevel)

        gold_session_entity = KBEngine.createEntityLocally('GoldSession', {})
        gold_session_entity.create(gold_session_level, on_success=success)

    def auto_create_rooms_on_start(self, session_level):
        """
        自动创建房间
        :return:
        """
        room_default = GoldSessionRoomDefaultConst.RoomDefault
        _config = Const.ServerGameConfigJson.config_json['GoldSession'][str(session_level)]
        # 读取配置表中每个游戏要创建的房间数量
        per_game_room_count = _config['perGameRoomCount']
        # 读取配置表种每个游戏要创建的假房间数量
        per_game_fake_room_count = _config['perGameFakeRoomCount']
        # 每个游戏创建一个
        for k2, args in room_default.items():
            # 创建指定数量的假房间
            for i in range(per_game_fake_room_count):
                self.create_gold_session_room(session_level, args, is_fake=True)

            # 创建指定数量的真房间
            for i in range(per_game_room_count - per_game_fake_room_count):
                self.create_gold_session_room(session_level, args)

    def auto_create_room_with_judgement(self, room_info, is_fake=False, ignore_judge=False):
        """
        通过room_info自动创建新房间
        :param room_info: 触发自动创建房间的房间的信息
        :param is_fake:是否是假房间
        :return:
        """
        # 深拷贝上个房间的信息
        new_room_info = room_info.copy()
        if not new_room_info:
            return
        gold_session = self.get_gold_session_with_level(room_info['level'])
        if not ignore_judge:
            # 自动创建房间时判断有没有没有人的并且没开始的房间，如果有，则不创建新的房间
            for roomId, roomEntity in gold_session.rooms.items():
                if not roomEntity.info["started"] and len(roomEntity.info["playerInGame"]) == 0 and \
                        roomEntity.info["type"] == new_room_info["type"] and \
                        roomEntity.info["anonymity"] == new_room_info["anonymity"]:
                    return

        self.create_gold_session_room(room_info['level'], room_info, is_fake=is_fake)

    def create_gold_session_room(self, session_level, args, is_fake=False):
        """
        创建金币场房间
        :param is_fake: 是否是假房间，假房间会加满机器人
        :param session_level:
        :param args:
        :return:
        """
        # 获取金币场实体、配置
        session = self.get_gold_session_with_level(session_level)
        session_config = Const.ServerGameConfigJson.config_json['GoldSession'][str(session.sessionLevel)]
        # 读取配置文件中的房间数量上限
        room_count_limit = session_config['roomCountLimit']
        session_rooms = session.rooms
        # 筛选出所有同类型的房间
        filter_rooms = [room for room in session_rooms.values() if room.info['type'] == args['type']]

        # 同类房间不能超过上限
        if len(filter_rooms) >= room_count_limit:
            return

        session.create_room(args, is_fake=is_fake)

    def change_gold_session_room_config(self, account_db_id, _args):
        """
        修改房间规则
        :param _args: 新房间参数
        :param account_db_id:修改者
        :return:
        """

        account_entity = get_account_entity_with_db_id(account_db_id)
        gold_session = self.get_gold_session_with_level(_args["level"])
        if not gold_session:
            account_entity.call_client_func("Notice", ["当前金币场不存在"])
            return
        change_room = None
        room_config = _args['roomConfig']
        # 通过id找出想要修改的房间
        for room in gold_session.rooms.values():
            if room.info['roomId'] == room_config['roomId']:
                change_room = room
                break
        if not change_room:
            account_entity.call_client_func("Notice", ["修改失败，房间不存在"])
            return
        if change_room and 'playerInGame' in change_room.info and len(change_room.info["playerInGame"]) != 0:
            account_entity.call_client_func("Notice", ["无法修改，房间中还有玩家"])
            return
        # 修改配置标识
        room_config["changeConfig"] = True
        gold_session.change_room_config(change_room, room_config)

    def update_single_room_info_to_client(self, session_level, room_info):
        """
        更新客户端单个房间信息
        :param room_info: 房间信息
        :param session_level:
        :return:
        """
        try:
            gold_session = self.get_gold_session_with_level(session_level)
            gold_session.update_single_room_info_to_client(room_info)
        except AttributeError as e:
            DEBUG_MSG(e)

    def reload_config(self):
        """
        重新加载内存里的配置（const）
        在json文件被加载后，goldSessionManager的计时器会每20秒调用一次此函数
        :return:
        """
        for k, v in self.gold_sessions.items():
            # 获取到指定等级的配置
            _config = Const.ServerGameConfigJson.config_json['GoldSession'][str(v.sessionLevel)]
            v.reload_config(_config)

    def on_timer(self, _id, arg):
        """
        计时器回调，暂作为重新加载配置的计时器
        :param _id:
        :param arg:
        :return:
        """
        self.reload_config()

    def update_single_room_state_to_client(self, session_level, room_entity):
        """
        更新客户端单个房间状态
        :param session_level:
        :param room_entity:
        :return:
        """
        try:
            gold_session = self.get_gold_session_with_level(session_level)
            gold_session.update_single_room_state_to_client(room_entity)
        except AttributeError as e:
            DEBUG_MSG(e)



    def join_and_open(self, gold_session_level, player_databaseID):
        """
        加入、打开金币场
        :return:
        """
        try:
            gold_session = self.get_gold_session_with_level(gold_session_level)
            gold_session.join_and_open(player_databaseID)
        except AttributeError:
            player = get_account_entity_with_db_id(player_databaseID)
            player.call_client_func('Notice', ['此金币场不存在'])

    def exit_and_close(self, gold_session_level, player_databaseID):
        """
        关闭、离开金币场
        :return:
        """
        try:
            gold_session = self.get_gold_session_with_level(gold_session_level)
            gold_session.exit_and_close(player_databaseID)
        except AttributeError:
            player = get_account_entity_with_db_id(player_databaseID)
            player.call_client_func('Notice', ['此金币场不存在'])

    def get_gold_session_with_level(self, gold_session_level: int):
        """
        获取指定等级的金币场
        :param gold_session_level:
        :return:
        """
        for k, v in self.gold_sessions.items():
            if v.sessionLevel == gold_session_level:
                return v

    def get_gold_session_hall_info(self):
        """
        获取金币场首页信息，底分、在线人数、金币范围
        :return:
        """
        info = []
        for k, v in self.gold_sessions.items():
            info.append({'level': v.sessionLevel,
                         'baseScore': v.baseScore,
                         'roomRate': v.roomRate,
                         'goldLimit': v.goldLimit,
                         'playerCount': len(v.memberInfo)})
        return info

    def player_in_gold_session(self, account_db_id, level):
        """
        指定玩家是否在该金币场
        :param account_db_id:
        :param level:
        :return:
        """
        gold_session = self.get_gold_session_with_level(level)
        if gold_session:
            if account_db_id in gold_session.memberInfo.keys():
                return True
            else:
                return False
        else:
            return False


class GoldSessionLevel:
    # 高级场
    advanced = 3
    # 中级场
    normal = 2
    # 初级场
    junior = 1
