# -*- coding: utf-8 -*-
import random

import KBEngine

import Const

import ChallengeRoomDefaultParam
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


class ChallengeAreaManager(Manger):
    """
    挑战赛管理器
    """
    challenge_areas = {}

    def __init__(self):
        Manger.__init__(self)

        # 创建
        self.get_challenge_area_from_db()

    def get_challenge_area_from_db(self):
        """
        从数据库检出赛区
        :param call_back:
        :return:
        """
        def query_success(result, rows, insertid, error):
            session_id = []
            for i in result:
                session_id.append(int(i[0]))
            self.create_challenge_area_from_db(session_id)

        _command = "select id,sm_sessionLevel from tbl_challengearea"
        KBEngine.executeRawDatabaseCommand(_command, query_success)

    def create_challenge_area_from_db(self, id_s):
        """创建挑战赛各赛区"""
        DEBUG_MSG('create_challenge_area_from_db:id_s:%s' % id_s)

        # 创建实体成功加入字典
        def on_create_challenge_success(baseRef, databaseID, wasActive):
            if baseRef:
                self.challenge_areas[baseRef.sessionLevel] = baseRef
                baseRef.init()
        # 从数据库创建实体到内存
        for i in id_s:
            KBEngine.createEntityFromDBID("ChallengeArea", i, on_create_challenge_success)

        # 如果没有某个场次，创建场次
        for v in range(1, 7):
            if v not in id_s:
                area_entity = KBEngine.createEntityLocally('ChallengeArea', {})
                area_entity.create(v)
                self.challenge_areas[area_entity.sessionLevel] = area_entity

    def start_reload_config_timer(self):
        self.add_timer(1, 20, 0)

        # # 测试数据
        # def callback(baseRef, databaseID, wasActive):
        #     if baseRef:
        #         account_mgr().add(baseRef)
        # KBEngine.createEntityFromDBID("Account", 565003, callback)
        # self.enter_challenge_area(1, 565003)

    def on_timer(self, _id, arg):
        """
        计时器回调，暂作为重新加载配置的计时器
        :param _id:
        :param arg:
        :return:
        """
        self.reload_config()

        # 测试数据


    def reload_config(self):
        """
        重新加载内存里的配置（const）
        在json文件被加载后，goldSessionManager的计时器会每20秒调用一次此函数
        :return:
        """
        for k, v in self.challenge_areas.items():
            # 获取到指定等级的配置
            _config = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(v.sessionLevel)]
            v.reload_config(_config)

    def get_challenge_area_by_level(self, challenge_level: int):
        """
        获取指定等级的赛场
        :param challenge_level:
        :return:
        """
        return self.challenge_areas[challenge_level]

    def get_challenge_result_control(self, databaseId, pyDic):
        challenge_level = int(pyDic["challengeLevel"])
        area = self.challenge_areas[challenge_level]
        DEBUG_MSG("get_challenge_result_control %s %s" % (challenge_level, area))
        return area.get_challenge_result_control(databaseId)

    def setChallengeResult(self, databaseId, pyDic):
        challenge_level = int(pyDic["challengeLevel"])
        challenge_result = int(pyDic["win"])
        pai_count = int(pyDic["controlCount"])
        area = self.challenge_areas[challenge_level]
        DEBUG_MSG("setChallengeResult %s %s %s" % (challenge_level, pai_count, challenge_result))
        area.get_member(databaseId).set_challenge_result(challenge_result, pai_count)

    def enter_challenge_area(self, challenge_level, player_databaseID):
        """
        进入赛场
        :return:
        """
        challenge_area = self.get_challenge_area_by_level(challenge_level)
        if challenge_area:
            challenge_area.join_and_open(player_databaseID)
        else:
            player = get_account_entity_with_db_id(player_databaseID)
            player.call_client_func('Notice', ['此挑战赛不存在'])

    def exit_challenge_area(self, challenge_level, player_databaseID):
        """
        离开赛场
        :return:
        """
        try:
            challenge_area = self.get_challenge_area_by_level(challenge_level)
            challenge_area.exit_and_close(player_databaseID)
        except AttributeError:
            player = get_account_entity_with_db_id(player_databaseID)
            player.call_client_func('Notice', ['此金币场不存在'])

    def get_challenge_ticket_info(self, account_db_id):
        ticket = []
        for k, v in self.challenge_areas.items():
            # 获取到指定等级的配置
            _config = Const.ServerGameConfigJson.config_json['ChallengeArea'][str(k)]
            ticket.append(_config["roomRate"])
        player = get_account_entity_with_db_id(account_db_id)
        # param = {"ticketInfo": ticket, "headImg": player.headImageUrl, "name": player.name, "gold": player.gold, "diamond": round(player.roomCard, 2)}
        param = {"ticketInfo": ticket}
        player.call_client_func('GetChallengeTicketInfo', param)

    def change_challenge_room_config(self, account_db_id, _args):
        """
        修改房间规则
        :param _args: 新房间参数
        :param account_db_id:修改者
        :return:
        """
        account_entity = get_account_entity_with_db_id(account_db_id)
        challenge_area = self.get_challenge_area_by_level(_args["level"])
        if not challenge_area:
            account_entity.call_client_func("Notice", ["当前金币场不存在"])
            return
        change_room = None
        room_config = _args['roomConfig']
        # 通过id找出想要修改的房间
        for room in challenge_area.rooms.values():
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
        challenge_area.change_room_config(change_room, room_config)

    def update_single_room_info_to_client(self, session_level, room_info):
        """
        更新客户端单个房间信息
        :param room_info: 房间信息
        :param session_level:
        :return:
        """
        try:
            challenge_area = self.get_challenge_area_by_level(session_level)
            challenge_area.update_single_room_info_to_client(room_info)
        except AttributeError as e:
            DEBUG_MSG(e)

    def update_single_room_state_to_client(self, session_level, room_entity):
        """
        更新客户端单个房间状态
        :param session_level:
        :param room_entity:
        :return:
        """
        try:
            challenge_area = self.get_challenge_area_by_level(session_level)
            challenge_area.update_single_room_state_to_client(room_entity)
        except AttributeError as e:
            DEBUG_MSG(e)




    # def auto_create_room_with_judgement(self, room_info, is_fake=False, ignore_judge=False):
    #     """
    #     通过room_info自动创建新房间
    #     :param room_info: 触发自动创建房间的房间的信息
    #     :param is_fake:是否是假房间
    #     :return:
    #     """
    #     # 深拷贝上个房间的信息
    #     new_room_info = room_info.copy()
    #     if not new_room_info:
    #         return
    #     challenge_area = self.get_challenge_area_by_level(room_info['level'])
    #     if not ignore_judge:
    #         # 自动创建房间时判断有没有没有人的并且没开始的房间，如果有，则不创建新的房间
    #         for roomId, roomEntity in challenge_area.rooms.items():
    #             if not roomEntity.info["started"] and len(roomEntity.info["playerInGame"]) == 0 and \
    #                     roomEntity.info["type"] == new_room_info["type"] and \
    #                     roomEntity.info["anonymity"] == new_room_info["anonymity"]:
    #                 return
    #
    #     self.create_gold_session_room(room_info['level'], room_info, is_fake=is_fake)
    #




    # def get_gold_session_hall_info(self):
    #     """
    #     获取金币场首页信息，底分、在线人数、金币范围
    #     :return:
    #     """
    #     info = []
    #     for k, v in self.challenge_areas.items():
    #         info.append({'level': v.sessionLevel,
    #                      'baseScore': v.baseScore,
    #                      'roomRate': v.roomRate,
    #                      'goldLimit': v.goldLimit,
    #                      'playerCount': len(v.memberInfo)})
    #     return info
    #
    # def player_in_gold_session(self, account_db_id, level):
    #     """
    #     指定玩家是否在该金币场
    #     :param account_db_id:
    #     :param level:
    #     :return:
    #     """
    #     challenge_area = self.get_challenge_area_by_level(level)
    #     if challenge_area:
    #         if account_db_id in challenge_area.memberInfo.keys():
    #             return True
    #         else:
    #             return False
    #     else:
    #         return False


# class GoldSessionLevel:
#     # 高级场
#     advanced = 3
#     # 中级场
#     normal = 2
#     # 初级场
#     junior = 1
