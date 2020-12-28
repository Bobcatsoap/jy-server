# -*- coding: utf-8 -*-
import copy
import datetime
import json
import math
import random
import time

import KBEngine
from KBEDebug import *
import collections
import Const
import DBCommand
from KBEDebug import DEBUG_MSG, ERROR_MSG


def get_account_entity_with_db_id(account_db_id):
    return KBEngine.globalData["AccountMgr"].mgr.get_account(account_db_id)


def room_manager():
    return KBEngine.globalData["RoomManager"].mgr


def account_manager():
    return KBEngine.globalData["AccountMgr"].mgr


def tea_house_config():
    return Const.ServerGameConfigJson.config_json['TeaHouse']


class TeaHouse(KBEngine.Entity):
    # 冠名赛通知
    notice = ""
    teaHouseLevel = 0
    # 冠名赛联系方式
    contactWay = ""
    # 冠名赛名字
    name = ""
    # 冠名赛id
    teaHouseId = -1
    # 冠名赛创建者DBId
    creatorDBID = -1
    # 冠名赛头像
    headImage = ""
    # 冠名赛成员信息
    memberInfo = {}
    # 冠名赛房间信息
    rooms = {}
    # 加入申请列表
    applicationList = {}
    # 退出申请列表
    exitApplicationList = {}
    # 创建时间
    createTime = 0
    # 历史房间
    historyRooms = {}
    # 今天开的房间
    todayRooms = []
    #
    todayGameCoinBilling = []
    #
    todayLuckyCardConsume = []
    # 成员信息字符串
    memberInfoJson = ""
    # {"accountDBID": 玩家id, "accountName": 玩家名称, "time": 操作时间, "type": 操作类型：1 进入，2 离开，3 踢出}
    joinAndExitHistory = []
    # 是否打烊 0 不打烊 1 打烊
    isSnoring = 0
    # 是否 0 不审核 1 审核
    isReview = 0
    # 业绩详情
    performance_detail = {}
    # 冠名赛类型 0：比赛场， 1：普通场
    teaHouseType = 0
    # 打烊的游戏
    snoring_games = []
    # 可以减少比赛分
    canReduceGameCoin = 0
    # 有兑换商城
    haveExchangeMall = 1
    # 福卡系统开关
    luckyCardSwitch = 0
    # TODO 比赛分开关   0关闭 1开启
    gameCoinSwitch = 1
    # 福卡
    luckyCard = 0
    # 茶楼排行榜,rank = {'data':{'myself':[id,reward],'rank':[{'head_img':img,'nickname':nickname}],'reward':[]}}
    rank = {}
    # 战队排行榜
    teamRank = {}
    # 重启后保存的房间
    saveRooms = []
    # 手动创建的房间
    manualRooms = []
    # 母桌
    baseRooms = []
    # 空桌位置,默认最后
    empty_location = -1
    # 满桌隐藏
    full_disappear = False
    # 冻结成员
    freezePlayers = {}

    def __init__(self):
        KBEngine.Entity.__init__(self)

        # 茶楼输赢平均分
        self.win_avg_score = 0
        self.lose_avg_score = 0

        # 随机对低于平均输分的玩家发好牌
        self.last_rand_time = 0
        self.rand_num = []
        self.manualRooms = []
        self.baseRooms = []
        self.get_rand_luck_num()

    def set_frezz_state(self, account_db_id, freeze_state):
        if freeze_state:
            if account_db_id in self.memberInfo:
                self.freezePlayers[account_db_id] = 1
                return True
        elif account_db_id in self.freezePlayers:
            self.freezePlayers.pop(account_db_id)
            return True
        return False

    def is_freeze_player(self, account_db_id):
        if account_db_id in self.freezePlayers:
            return True
        else:
            return False

    @property
    def creator_dbid(self):
        return self.creatorDBID

    def init_save_rooms(self):
        """
        初始化上次重启保存的房间
        :return:
        """

        def callback(baseRef, databaseID, wasActive):
            """
            楼主实体创建成功回调
            :param baseRef:
            :param databaseID:
            :param wasActive:
            :return:
            """
            _copy = self.saveRooms.copy()
            self.saveRooms.clear()
            room_card_consume = 0
            # 统计重建房间钻石消耗量
            for info in _copy:
                if 'payType' in info and info['payType'] == 0:
                    if 'roomCardConsume' in info:
                        room_card_consume += info['roomCardConsume']
            DEBUG_MSG('init_save_rooms roomCardConsume:%s' % room_card_consume)
            # 创建时扣除房主钻石
            if room_card_consume > 0:
                account_manager().modify_room_card(databaseID, room_card_consume, consume_type='saveRooms',
                                                   record_sql=False)
            for info in _copy:
                # TODO 报错
                baseRef.create_tea_house_room(info, creator_entity=baseRef, record_sql=False)

        KBEngine.createEntityFromDBID("Account", self.creatorDBID, callback)

    def init_other(self):
        """初始化茶楼其他信息"""

        def func(tea_house_id, win_score, lose_score):
            self.lose_avg_score = lose_score
            self.win_avg_score = win_score
            DEBUG_MSG('load_tea_house_avg_score %s %s %s %s' % (
                self.teaHouseId, self.id, self.lose_avg_score, self.win_avg_score))

        DBCommand.load_tea_house_avg_score(self.teaHouseId, func)

        # 旧数据可能没有分数控制的几个属性，这里给加上；
        DEBUG_MSG('init_other %s' % self.memberInfo)
        for k, player in self.memberInfo.items():
            if not hasattr(player, 'recent_score'):
                player.score_control = False
                player.recent_score = 0
                player.lose_score_threshold = 0
                player.win_score_threshold = 0

            player.luck_score_control = False

    def create(self, creator_db_id, tea_house_id, creator_head_image, tea_house_head_image, tea_house_name,
               tea_house_type, gold, creator_name, on_success, on_fail):
        """
        创建
        :param creator_db_id:
        :param tea_house_id:
        :param creator_head_image:
        :param tea_house_head_image:
        :param tea_house_name:
        :param tea_house_type:
        :param creator_name:
        :param on_success:
        :param on_fail:
        :return:
        """

        def callback(boolean, entity):
            if boolean:
                KBEngine.globalData["TeaHouseManager"].mgr.teaHouse_dic[entity.databaseID] = entity
                self.update_tea_house_info_to_client()
                on_success(entity)
            else:
                on_fail("数据库写入失败")

        self.creatorDBID = creator_db_id
        self.teaHouseId = tea_house_id
        self.name = tea_house_name
        self.teaHouseType = tea_house_type
        self.teaHouseLevel = 1
        self.headImage = tea_house_head_image
        self.createTime = int(time.time())
        self.canReduceGameCoin = 1
        self.haveExchangeMall = 1

        tea_house_player = TeaHousePlayer(TeaHousePlayerLevel.Creator, creator_db_id, creator_name, creator_head_image,
                                          creator_db_id, self.random_invitation_code(), gold)
        self.luckyCard = tea_house_config()['receiveLuckyCard']
        self.memberInfo[creator_db_id] = tea_house_player
        self.memberInfoJson = self.get_member_info_json()
        self.writeToDB(callback)

    def modify_table_set(self, modifier, empty_location, full_disappear):
        # TODO 冠名赛成员判断
        if modifier not in self.memberInfo:
            self.notice_player(modifier, '修改失败，你不是此冠名赛成员')
            return
        modifier_player = self.memberInfo[modifier]
        if modifier_player.level == TeaHousePlayerLevel.Admin or modifier_player.level == TeaHousePlayerLevel.Creator:
            self.empty_location = empty_location
            self.full_disappear = full_disappear
            self.notice_player(modifier, '修改成功')
            self.update_tea_house_info_to_client()
        else:
            self.notice_player(modifier, '修改失败，没有权限')

    def destroy_tea_house(self):
        # todo：待优化，解散冠名赛并解散冠名赛内房间
        new_dic = copy.deepcopy(self.rooms)
        for k, v in new_dic.items():
            def disband_success(room_entity):
                if room_entity.cell:
                    room_entity.destroyCellEntity()

            self.disband_room(v.info["roomId"], self.teaHouseId, on_success=disband_success)
        KBEngine.globalData["TeaHouseManager"].mgr.teaHouse_dic.pop(self.databaseID)

        for k, v in self.memberInfo.items():
            account_entity = KBEngine.globalData["AccountMgr"].mgr.get_account(k)
            if account_entity and account_entity.client_open_tea_house_state == self.teaHouseId:
                account_entity.call_client_func("DestroyTeaHouseSuccess", {})
                account_entity.get_joined_tea_house_list()

        self.destroy(True, True)

    def clear_join_history(self):
        self.joinAndExitHistory.clear()
        self.update_tea_house_info_to_client()

    def modify_tea_house_info(self, tea_house_name, tea_house_notice, tea_house_head_image, is_snoring, is_review,
                              lucky_card_switch, game_coin_switch,
                              on_success=None, on_fail=None):
        """
        修改冠名赛信息
        :param tea_house_name:
        :param tea_house_notice:
        :param tea_house_head_image:
        :param is_snoring:
        :param is_review:
        :param on_success:
        :param on_fail:
        :return:
        """
        self.name = tea_house_name
        self.headImage = tea_house_head_image
        self.notice = tea_house_notice
        self.isSnoring = is_snoring
        self.isReview = is_review
        self.luckyCardSwitch = lucky_card_switch
        if Const.ServerGameConfigJson.config_json['TeaHouse']["GameCoinSwitch"] == 1:
            self.gameCoinSwitch = game_coin_switch
        self.refresh_tea_house_info_to_room_cell()

        self.update_tea_house_info_to_client()
        if on_success:
            on_success(self)

    def change_tea_house_level(self, level, on_success, on_fail):
        """
        修改冠名赛等级
        :param level:
        :param on_success:
        :param on_fail:
        :return:
        """
        if level <= self.teaHouseLevel:
            on_fail("升级失败，升级等级需要大于当前等级")
            return
        self.teaHouseLevel = level
        self.memberInfoJson = self.get_member_info_json()

        self.update_tea_house_info_to_client()
        on_success(self)

    # 兼容老版本，新加接口
    def modify_performance_new(self, operate_player_db_id, modify_player_db_id, performance_change, on_success,
                               on_fail):
        """
         修改业绩
         :param modify_player_db_id:被修改玩家
         :param operate_player_db_id:
         :param performance_change:
         :param on_success:
         :param on_fail:
         :return:
         """
        # 不能修改比自己等级高的
        if self.memberInfo[operate_player_db_id].level <= self.memberInfo[modify_player_db_id].level:
            on_fail("修改失败，权限不足")
            return

        if modify_player_db_id not in self.memberInfo.keys():
            on_fail("修改失败，该玩家不是冠名赛成员")
            return
        if abs(performance_change) > self.memberInfo[modify_player_db_id].performance:
            on_fail("修改失败，余额不足")
            return
        self.memberInfo[modify_player_db_id].performance += performance_change
        round(self.memberInfo[modify_player_db_id].performance, 2)
        self.memberInfoJson = self.get_member_info_json()
        on_success(self)
        self.get_partner_single_member_info(modify_player_db_id, operate_player_db_id)

    def modify_performance(self, operate_player_db_id, modify_player_db_id, performance_change, on_success, on_fail):
        """
        修改业绩
        :param modify_player_db_id:被修改玩家
        :param operate_player_db_id:
        :param performance_change:
        :param on_success:
        :param on_fail:
        :return:
        """
        # 不能修改比自己等级高的
        if self.memberInfo[operate_player_db_id].level <= self.memberInfo[modify_player_db_id].level:
            on_fail("修改失败，权限不足")
            return

        if modify_player_db_id not in self.memberInfo.keys():
            on_fail("修改失败，该玩家不是冠名赛成员")
            return
        if abs(performance_change) > self.memberInfo[modify_player_db_id].performance:
            on_fail("修改失败，余额不足")
            return
        self.memberInfo[modify_player_db_id].performance += performance_change
        round(self.memberInfo[modify_player_db_id].performance, 2)
        self.memberInfoJson = self.get_member_info_json()
        on_success(self)

    def auto_create_room_with_judgement(self, room_info, ignore_judge=False, room_end=False):
        """
        通过room_info自动创建新房间
        :param ignore_judge:忽略判断，此值为True时，必定会创建房间,默认不忽略
        :param room_info: 触发自动创建房间的房间的信息
        :return:
        """
        # 深拷贝上个房间的信息
        if not room_info:
            return

        DEBUG_MSG('[TeaHouse Id %s] auto_create_room_with_judgement %s' % (self.teaHouseId, room_end))
        # 如果是房间开始自动创建的房间，判断有没有空房间
        if not room_end:
            DEBUG_MSG('not ignore judge')
            # 自动创建房间时判断有没有，没有人、没开始、规则相同的房间，如果有，则不创建新的房间
            for roomId, roomEntity in self.rooms.items():
                if not roomEntity.info["started"] and len(roomEntity.info["playerInGame"]) == 0 and \
                        roomEntity.info["type"] == room_info["type"] and \
                        self.is_same_room_config(room_info, roomEntity.info):
                    return
        # 如果是房间销毁时自动创建的房间，判断同规则的空房间有几个
        # 如果同规则房间数大于手动创建房间数，不再自动创建
        else:
            same_blank_count = self.get_same_blank_room_config_count(room_info)
            start = time.time()
            same_manual_count = self.get_same_manual_room_config_count(room_info)
            end = time.time()
            DEBUG_MSG('get_same_manual_room_config_count teahouseId:%s,blank_count:%s,manual_count:%s' % (
                self.teaHouseId,
                same_blank_count,
                same_manual_count))
            if same_blank_count >= same_manual_count:
                return

        old_room_id = room_info['roomId']
        DEBUG_MSG('[TeaHouse Id %s] auto_create_room_with_judgement create room' % self.teaHouseId)
        new_room_info = copy.deepcopy(room_info)

        def callback(baseRef, databaseID, wasActive):
            baseRef.create_tea_house_room(new_room_info, auto_create=True, room_end=room_end,
                                          old_room_id=old_room_id, creator_entity=baseRef)

        KBEngine.createEntityFromDBID("Account", self.creatorDBID, callback)

    def get_same_blank_room_config_count(self, room_info):
        """
        查看有多少个空房间规则和这个房间相同
        :param room_info:
        :return:
        """
        count = 0
        for roomId, roomEntity in self.rooms.items():
            if not roomEntity.info["started"] and len(roomEntity.info["playerInGame"]) == 0:
                if self.is_same_room_config(room_info, roomEntity.info):
                    count += 1

        return count

    def get_same_manual_room_config_count(self, room_info: object) -> object:
        """
        查看手动创建的房间中有多少和这个房间规则相同
        :param room_info:
        :return:
        """
        count = 0
        for info_dict in self.manualRooms:
            if self.is_same_room_config(room_info, info_dict['roomInfo']):
                count = info_dict['count']
                return count

        return count

    def get_same_manual_room_config(self, room_info):
        """
        查看手动创建的房间中有多少和这个房间规则相同
        :param room_info:
        :return:
        """
        for info_dict in self.manualRooms:
            if self.is_same_room_config(room_info, info_dict['roomInfo']):
                return info_dict['roomInfo'], info_dict['count']
        return None, None

    def is_same_room_config(self, room1_info, room2_info):
        """
        游戏规则是否相同
        :param room1_info:
        :param room2_info:
        :return:
        """
        if room1_info['type'] != room2_info['type']:
            return False
        for k, v in room1_info.items():
            if k == 'started':
                continue
            if k == 'roomId':
                continue
            if k == 'createRoomTime':
                continue
            if k == 'currentChapterCount':
                continue
            if k == 'gameCoinSwitch':
                continue
            if k == 'playerInGame':
                continue
            if k == 'roomName':
                continue
            if room1_info[k] != room2_info[k]:
                return False
        return True

    def add_manual_room(self, room_info):
        """
        增加手动创建房间
        :param room_info:
        :return:
        """
        self.add_base_rooms(room_info['roomId'])
        have = False
        for info_dict in self.manualRooms:
            if self.is_same_room_config(info_dict['roomInfo'], room_info):
                info_dict['count'] += 1
                have = True
                break

        if not have:
            self.manualRooms.append({'roomInfo': room_info, 'count': 1})

        if len(self.manualRooms) > 1000:
            self.manualRooms.pop(0)

        DEBUG_MSG('add_manual_room %s' % self.manualRooms)

    def add_base_rooms(self, room_id):
        """
        增加母桌
        :param room_id:
        :return:
        """
        if room_id not in self.baseRooms:
            self.baseRooms.append(room_id)
        if len(self.baseRooms) > 1000:
            self.baseRooms.pop(0)
        DEBUG_MSG('add_base_rooms %s' % self.baseRooms)

    def remove_manual_room(self, room_info):
        """
        移除手动创建房间
        :param room_info:
        :return:
        """
        self.remove_base_room(room_info['roomId'])
        delete_index = -1
        for _index, info_dict in enumerate(self.manualRooms):
            if self.is_same_room_config(info_dict['roomInfo'], room_info):
                info_dict['count'] -= 1
                if info_dict['count'] == 0:
                    delete_index = _index
                break

        if delete_index != -1:
            self.manualRooms.pop(delete_index)
        DEBUG_MSG('remove_manual_room %s' % self.manualRooms)

    def remove_base_room(self, room_id):
        """
        移除母桌
        :param room_id:
        :return:
        """
        if room_id in self.baseRooms:
            self.baseRooms.remove(room_id)
        DEBUG_MSG('remove_base_room %s' % self.baseRooms)

    def add_room(self, room_entity, on_success=None, on_fail=None,
                 room_end=False, old_room_index=-1, auto_create=False,
                 create_room_args=None):
        """
        增加房间
        :param room_entity:
        :param room_end:是否是房间结束时自动创建的房间
        :param old_room_index:旧房间的索引，-1时，新房间默认插在最后;否则新房间跟随在旧房间之后
        :return:
        """
        DEBUG_MSG('room_end:%s,old_room_index%s' % (room_end, old_room_index))
        self.sort_rooms()
        # 如果不是房间结束后的自动创建，插入到最后
        if not room_end:
            self.rooms[len(self.rooms.keys())] = room_entity
        # 如果时房间结束后的自动创建，插入到老房间后面
        else:
            if old_room_index == -1:
                self.rooms[len(self.rooms.keys())] = room_entity
            else:
                rooms_copy = self.rooms.copy()
                indexes = list(self.rooms.keys())
                indexes.append(len(self.rooms))
                DEBUG_MSG('indexes %s' % indexes)
                for i in indexes:
                    if i >= old_room_index + 2:
                        self.rooms[i] = rooms_copy[i - 1]
                self.rooms[old_room_index + 1] = room_entity
        self.sort_rooms()
        DEBUG_MSG('add_room rooms:%s' % self.rooms)
        # 刷新存储房间
        self.refresh_save_rooms()
        # 增加手动创建房间
        if not auto_create:
            self.add_manual_room(room_entity.info)
        self.insert_single_room_info_to_client(room_entity, old_room_index=old_room_index)
        if on_success:
            on_success(room_entity.info)

    def refresh_save_rooms(self):
        self.saveRooms.clear()
        for k, v in self.rooms.items():
            info = v.info.copy()
            info.pop('playerInGame')
            self.saveRooms.append(info)
        DEBUG_MSG('refresh_save_rooms saveRooms count:%s' % len(self.saveRooms))

    def sort_rooms(self):
        """
        给房间排序
        """
        sort_keys = sorted(self.rooms.keys())
        sort_rooms = {}
        for k in sort_keys:
            sort_rooms[k] = self.rooms[k]

        self.rooms = sort_rooms

    def write_history_room(self, room_type, room_db_id, record_players):
        for _p_id in record_players:
            # 找到玩家
            if _p_id not in self.historyRooms:
                self.historyRooms[_p_id] = {}
            if room_type not in self.historyRooms[_p_id]:
                self.historyRooms[_p_id][room_type] = []
            self.historyRooms[_p_id][room_type].append(room_db_id)
            if len(self.historyRooms[_p_id][room_type]) > Const.Record.record_limit:
                del self.historyRooms[_p_id][room_type][0]

    def is_base_room(self, room_id):
        """
        是否是母桌
        :param room_id:
        :return:
        """
        return room_id in self.baseRooms

    def create_and_join_like_base_room(self, joiner, room_id):
        """
        创建一个跟母桌相同的房间并加入
        1.通过茶楼创建房间
        2.通过新创建房间的id让加入者加入房间
        :param joiner: 加入房间的人
        :param room_id:房间id
        :return:
        """

        room_entity = self.get_room_by_id(room_id)
        if room_entity and self.is_base_room(room_id):
            base_room_info = copy.deepcopy(room_entity.info)

            def on_success(room_info):
                DEBUG_MSG("join baseRoom base_roomId:%s,account_db_id:%s" % (room_id, joiner))
                DEBUG_MSG("join baseRoom new_roomId:%s,account_db_id:%s" % (room_info['roomId'], joiner))
                # 创建成功后，让申请者加入房间
                joiner_entity = account_manager().get_account(joiner)
                # 告诉客户端加入新房间
                joiner_entity.call_client_func('JoinLikeBaseRoom', {
                    'type': room_info['type'],
                    'roomId': room_info['roomId'],
                    'anonymity': room_info['anonymity'],
                    'teaHouseId': room_info['teaHouseId'],
                    'roomType': room_info['roomType']
                })

            def on_fail(content):
                joiner_entity = account_manager().get_account(joiner)
                joiner_entity.call_client_func('Notice', [content])

            def callback(creator_entity, databaseID, wasActive):
                # 用楼主的实体创建房间
                self.create_room(creator_entity.databaseID, base_room_info,
                                 auto_create=True, on_success=on_success,
                                 on_fail=on_fail,
                                 creator_entity=creator_entity)

            # 创建楼主的实体
            KBEngine.createEntityFromDBID("Account", self.creatorDBID, callback)

    def get_member_history_rooms(self, room_type, player_db_id):
        if player_db_id not in self.historyRooms:
            return []
        if room_type not in self.historyRooms[player_db_id]:
            return []
        DEBUG_MSG('player_id:%s,get_member_history_rooms%s' % (player_db_id,
                                                               self.historyRooms[player_db_id][room_type]))

        return self.historyRooms[player_db_id][room_type]

    def get_all_history_rooms(self, room_type):
        room_ids = []
        for db_id, rooms in self.historyRooms.items():
            room_id_list = []
            if room_type in rooms:
                room_id_list = rooms[room_type]
            for room_id in room_id_list:
                if room_id not in room_ids:
                    room_ids.append(room_id)
        DEBUG_MSG('teahouseId:%s,get_member_history_rooms all %s' % (self.teaHouseId,
                                                                     room_ids))
        # 不是id越大，时间越靠后；
        room_ids.sort(reverse=True)
        room_ids = room_ids[:Const.Record.record_limit * 7]
        DEBUG_MSG('teahouseId:%s,get_member_history_rooms sorted %s' % (self.teaHouseId,
                                                                        room_ids))
        return room_ids

    def change_room_config(self, new_room, old_room, on_success, on_fail=None):
        """
        修改房间配置，使用新房间替换旧房间
        :param new_room:
        :param old_room:
        :param on_success:
        :param on_fail:
        :return:
        """
        for k, room in self.rooms.items():
            if room == old_room:
                self.rooms[k] = new_room
                break
        #
        self.remove_manual_room(old_room.info)
        self.add_manual_room(new_room.info)
        # 解散之前的房间
        # 通知房间解散
        if old_room.cell:
            old_room.cell.baseToCell({"func": "disbandTeaHouseRoomByCreator"})
            on_success(self)

    def disband_room(self, room_id, tea_house_id, delete_manual=True, on_success=None, on_fail=None):
        """
        手动解散时调用
        :param delete_manual: 是否从手动创建房间中移除
        :param room_id:
        :param tea_house_id:
        :param on_success:
        :param on_fail:
        :return:
        """
        # 获取桌号
        table_index = -1
        room_entity = None
        for k, v in self.rooms.items():
            if v.info["teaHouseId"] == tea_house_id and v.info["roomId"] == room_id:
                table_index = k
                room_entity = v
                break
        if table_index == -1 and not room_entity:
            return
        # 移除房间并重新排序
        for t in range(table_index, len(self.rooms) - 1):
            self.rooms[t] = self.rooms[t + 1]
        self.rooms.pop(len(self.rooms) - 1)
        self.refresh_save_rooms()
        self.delete_single_room_info_to_client(room_entity)
        if delete_manual:
            self.remove_manual_room(room_entity.info)
        if room_entity and room_entity.cell:
            room_entity.cell.baseToCell({"func": "disbandTeaHouseRoomByCreator"})
        # 如果房间少于一个，自动创建一个新的房间
        # self.auto_create_room_with_judgement(room_entity.info)
        if on_success:
            on_success(room_entity)

    def remove_room(self, room_id, tea_house_id, on_success, on_fail=None):
        """
        # 从列表中移除房间,通常为从cell端解散房间后调用，on_success 通常为通知cell调用destroySpace
        :param room_id:
        :param tea_house_id:
        :param on_success:
        :param on_fail:
        :return:
        """
        table_count = -1
        room_entity = None
        for k, v in self.rooms.items():
            if v.info["teaHouseId"] == tea_house_id and v.info["roomId"] == room_id:
                table_count = k
                room_entity = v
                break
        if table_count == -1 and not room_entity:
            return
        for t in range(table_count, len(self.rooms) - 1):
            self.rooms[t] = self.rooms[t + 1]
        self.rooms.pop(len(self.rooms) - 1)
        self.refresh_save_rooms()
        self.delete_single_room_info_to_client(room_entity)
        on_success()

    def add_today_rooms(self, room_db_id, room_create_time, game_type):
        """
        增加今日开房
        :param room_db_id:
        :param room_create_time:
        :param game_type:
        :return:
        """
        today_date = datetime.date.today()
        # 今天的最后一秒
        today_end = int(time.mktime(today_date.timetuple()) + 86399)
        # 最后一次统计的时间
        if len(self.todayRooms) == 0 or room_create_time > self.todayRooms[len(self.todayRooms) - 1]["date"]:
            # 插入一个新的日期
            self.todayRooms.append(
                {"date": today_end,
                 "roomList": [{"roomDBID": room_db_id, "createTime": room_create_time, "type": game_type}]})
        else:
            self.todayRooms[len(self.todayRooms) - 1]["roomList"].append(
                {"roomDBID": room_db_id, "createTime": room_create_time, "type": game_type})
        if len(self.todayRooms) > 2:
            del self.todayRooms[0]

    def add_today_game_coin_billing(self, account_db_id, add, roomType=None):
        """
        增加今日抽成
        :param account_db_id:抽成的玩家
        :param add:抽成的数量
        :return:
        """
        DEBUG_MSG("account_db_id %s  add %s " % (str(account_db_id), str(add)))
        def callback():
            self.update_tea_house_info_to_client()

        origin_player = self.get_tea_house_player(account_db_id)
        DEBUG_MSG("origin_player")
        DEBUG_MSG(origin_player)
        self.today_game_coin_calculate(origin_player, add, roomType, callback)

    def today_game_coin_calculate(self, origin_player, add, roomType, call_back):
        """
        计算所有上级需要的抽成
        组员->组员(50%)->队长(80%)->战队长(80%)->群主
        假设组员贡献100

        群主收取100
        战队长比例80%，贡献值增加80
        队长比例80%，贡献值增加64
        组长比例50%，贡献值增加32

        :param origin_player: 被抽取的起始玩家
               add: 抽成的数量
        :return:
        """

        def find_belong_to_recursive(_origin_player, _up_players: []):
            """
            查找所有上级，到楼主为止
            :param _origin_player: 起始玩家
            :param _up_players: 上级列表
            :return:
            """
            # 找到上级玩家
            up = self.get_tea_house_player(_origin_player.belong_to)
            if not up:
                return

            # 如果有非楼主玩家的上级是自己直接返回，防止死循环
            if up.db_id == up.belong_to and up.level != TeaHousePlayerLevel.Creator:
                return

            _up_players.append(up)

            # 上级玩家加入队列
            # 加入到楼主为止
            if up.db_id == self.creatorDBID:
                return

            find_belong_to_recursive(up, _up_players)

        up_players = []
        # up_players 存储从楼主顺序往下的所有上级，楼主没有上级玩家列表
        # if origin_player.level != TeaHousePlayerLevel.Creator:
        if origin_player.level != TeaHousePlayerLevel.Creator:
            find_belong_to_recursive(origin_player, up_players)
        # 如果是战队长，上级里加上自己
        #if origin_player.level == TeaHousePlayerLevel.Partner:
        #    up_players.append(origin_player)
        # 从大到小排列
        up_players.reverse()

        today_date = datetime.date.today()
        today_start = int(time.mktime(today_date.timetuple()))
        today_end = int(time.mktime(today_date.timetuple()) + 86399)

        _add = add
        # 计入该玩家上交抽成
        origin_player.turn_in_performance += _add
        # 遍历上级列表
        for _index, player in enumerate(up_players):
            # 抽成等于上级
            next_performance = 0
            # 该上级是否还有下级，如果有先计算应该给下级的分成
            if _index + 1 < len(up_players):
                next_player = up_players[_index + 1]
                next_performance = next_player.proportion / 100 * _add
            # 该上级分成等于分成减去下级应得分成
            _performance = _add - next_performance
            _add = next_performance
            # DEBUG_MSG('index%s,player_db_id:%s,performance:%s,_add:%s' % (_index, player.db_id, _performance, _add))
            # 保留两位小数，减少长度
            _performance = round(_performance, 2)

            player.performance += _performance
            # 上级的抽成集合 [{"time": 时间, "count": count, "accountDBID": DBID}]
            _performance_detail = []
            if player.db_id in self.performance_detail.keys():
                _performance_detail = self.performance_detail[player.db_id]
            _performance_detail.append({"count": _performance, "time": int(time.time()),
                                        "accountDBID": origin_player.db_id})
            # 去除抽成中除了今天的、昨天的数据
            _performance_detail = self.performance_detail_remove(_performance_detail)

            self.performance_detail[player.db_id] = _performance_detail
            tea_house_performance = KBEngine.createEntityLocally("TeaHousePerformance", {})
            # DEBUG_MSG('roomType--------------------%s' % roomType)
            tea_house_performance.create_one_item(origin_player.db_id, player.db_id, int(time.time()),
                                                  _add, _performance, player.proportion, self.teaHouseId, roomType)

            DBCommand.modify_total_commssion(player.db_id, player.db_id,self.teaHouseId,int(time.time()), _add, _performance)

            tea_house_performance.destroy(False, False)

            if player.level == TeaHousePlayerLevel.Creator:
                # 楼主的抽成算入今日茶楼收取
                if len(self.todayGameCoinBilling) == 0 or today_start > \
                        self.todayGameCoinBilling[len(self.todayGameCoinBilling) - 1]["date"]:
                    self.todayGameCoinBilling.append({"date": today_end, "gameCoinBilling": _performance})
                else:
                    self.todayGameCoinBilling[len(self.todayGameCoinBilling) - 1]["gameCoinBilling"] += _performance

                # 只存两天的记录
                # DEBUG_MSG("[TeaHouse]------>add_today_game_coin_billing %s:" % self.todayGameCoinBilling)
                if len(self.todayGameCoinBilling) > 2:
                    del self.todayGameCoinBilling[0]
                call_back()

    def performance_detail_remove(self, performance_detail):
        """
        移除除了今天、昨天之外的数据
        :param performance_detail:
        :return:
        """
        performance_detail = [_p for _p in performance_detail if self.yesterday_start <= _p['time'] <= self.today_end]
        return performance_detail

    def random_invitation_code(self):
        """
        设计思路：
        随机邀请码,给每个合伙人随机一个邀请码，这个邀请码既要指向固定冠名赛，又要指向固定合伙人
        这个6位的邀请码，前三位指向某个冠名赛，后三位指向某个合伙人
        前三位就取冠名赛的数据库ID，后三位就随机一个跟其他合伙人邀请码不重复的三位数
        拼接成一个6位的邀请码
        通过邀请码加入冠名赛，邀请码/1000取商就是冠名赛DBID，
        邀请码/1000取余就是某个合伙人
        伪代码：
        for k, v in 冠名赛玩家集合：
            把所有冠名赛玩家的邀请码存在集合里
        while True:
            随机一个邀请码
            如果 这个邀请码已经存在了：
                继续循环
            如果 这个邀请码不存在：
                返回这个邀请码
        :return:
        """
        invitation_codes = []
        for k, v in self.memberInfo.items():
            invitation_codes.append(int(v.invitation_code % 1000))
        for i in range(50000):
            _invitation_code = random.randint(1, 999)
            if _invitation_code in invitation_codes:
                continue
            else:
                _invitation_code = self.databaseID * 1000 + _invitation_code
                return _invitation_code

    def modify_can_reduce_game_coin(self, can_reduce):
        """
        修改茶楼减少比赛分权限
        :param can_reduce:
        :return:
        """
        self.canReduceGameCoin = can_reduce
        self.update_tea_house_info_to_client()

    def modify_have_exchange_mall(self, have_exchange_mall):
        """
        修改茶楼兑换商城权限
        :param have_exchange_mall:
        :return:
        """
        self.haveExchangeMall = have_exchange_mall
        self.update_tea_house_info_to_client()

    # ----------------------------------操作会员的函数-----------------------------------#

    def join(self, joiner_db_id, on_success, on_fail):
        """
        冠名赛加入新的成员
        :param joiner_db_id:
        :param on_success:
        :param on_fail:
        :return:
        """

        # 创建实体成功，添加好友
        def on_success_callback(baseRef, databaseID, wasActive):
            if baseRef:
                baseRef.add_friend({"accountDBID": joiner_db_id}, is_invite_add=True)
                self.insert_single_member_info_to_client(joiner_db_id)
                self.update_tea_house_info_to_client()

        if len(self.memberInfo) >= tea_house_config()['maxMemberCount']:
            on_fail("加入失败，超出冠名赛成员数量")
            return

        joiner_head_image = self.applicationList[joiner_db_id]["headImage"]
        joiner_name = self.applicationList[joiner_db_id]["playerName"]
        joiner_belong_to = self.applicationList[joiner_db_id]["inviterDBID"]
        joiner_gold = self.applicationList[joiner_db_id]["gold"]
        if joiner_belong_to == -1:
            joiner_belong_to = self.creatorDBID
        # 玩家初始化
        tea_house_player = TeaHousePlayer(TeaHousePlayerLevel.Normal, joiner_db_id, joiner_name, joiner_head_image,
                                          joiner_belong_to, self.random_invitation_code(), joiner_gold)
        self.memberInfo[joiner_db_id] = tea_house_player
        self.memberInfoJson = self.get_member_info_json()
        self.joinAndExitHistory.append(
            {"accountDBID": joiner_db_id, "accountName": joiner_name, "time": int(time.time()), "type": 1})
        if len(self.joinAndExitHistory) > tea_house_config()['joinExitHistoryLimit']:
            self.joinAndExitHistory.pop(0)
        if joiner_db_id in self.applicationList:
            self.applicationList.pop(joiner_db_id)

        # 加入冠名赛的人自动成为楼主好友
        KBEngine.createEntityFromDBID("Account", self.creatorDBID, on_success_callback)
        on_success(self)

    def get_single_member_info(self, account_db_id):
        """
        E获取成员信息
        获取单个玩家的成员信息
        :return:
        """
        # DEBUG_MSG("1111111111111111")
        # DEBUG_MSG( self.memberInfo.items())
        for k, v in self.memberInfo.items():
            if account_db_id == k:
                # 如果玩家实体有客户端，视为在线
                account_entity = get_account_entity_with_db_id(k)
                up_entity = get_account_entity_with_db_id(v.belong_to)
                online_state = bool(account_entity and account_entity.client)
                members_info = {"level": v.level, "name": v.name, "gameCoin":  round(v.game_coin, 1),
                                "accountDBId": k, "state": online_state,
                                "belongTo": v.belong_to,
                                "belongToName": up_entity.name if up_entity else "",
                                "chapterCounts": v.chapter_count,
                                "headImage": v.head_image,
                                'origin_game_coin': v.origin_game_coin,
                                'luckyCard': v.lucky_card,
                                'freeze': self.is_freeze_player(account_db_id),
                                "proportion": v.proportion
                                }
                return members_info
        # members_info = {}
        # yesterday = 0
        # today = 0
        # for k in self.performance_detail:
        #     if str(account_db_id) in self.performance_detail[k]:
        #         performance_detail = self.performance_detail[k][account_db_id]
        #         _time = performance_detail['time']
        #         count = performance_detail['count']
        #         if self.yesterday_start <= _time <= self.yesterday_end:
        #             yesterday = count
        #         elif self.today_start <= _time <= self.today_end:
        #             today = count
        #
        # if account_db_id in self.memberInfo:
        #     members_info = {
        #         "name": self.memberInfo[account_db_id].name, "headImageUrl": self.memberInfo[account_db_id].head_image,
        #         "belongTo": self.memberInfo[account_db_id].belong_to,
        #         "invitationCode": self.memberInfo[account_db_id].invitation_code,
        #         "proportion": self.memberInfo[account_db_id].proportion,
        #         "level": self.memberInfo[account_db_id].level,
        #         'userId': self.memberInfo[account_db_id].db_id,
        #         'todayData': yesterday,
        #         'yesterdayData': today,
        #         "performance": self.memberInfo[account_db_id].performance,
        #         "turnInPerformance": round(self.memberInfo[account_db_id].turn_in_performance, 2)
        #     }
        # return members_info

    def search_tea_house_single_member_info(self, searcher, key_word):
        """
        搜索冠名赛中的某个成员
        :param searcher: 搜索者数据库id
        :param key_word: 关键字
        :return:
        """
        key_word = key_word.encode('utf-8').decode()
        DEBUG_MSG('key_word:%s' % key_word)
        searcher_info = self.memberInfo[searcher]
        member_info = []
        for k, v in self.memberInfo.items():
            if key_word == str(k) or key_word in v.name:
                # 可以搜自己，搜自己下级；楼主、助理可以搜所有
                if (searcher == k) or (searcher_info.level == 100) or (searcher_info.level == 10) \
                        or (searcher_info.level >= v.level and self.is_down_player(k, searcher)):
                    # 如果玩家实体有客户端，视为在线
                    account_entity = get_account_entity_with_db_id(k)
                    up_entity = get_account_entity_with_db_id(v.belong_to)
                    online_state = bool(account_entity and account_entity.client)
                    _m = {"level": v.level, "name": v.name, "gameCoin": v.game_coin,
                          "accountDBId": k, "state": online_state,
                          "belongTo": v.belong_to,
                          "belongToName": up_entity.name if up_entity else "",
                          'luckyCard': v.lucky_card,
                          "proportion": v.proportion,
                          "chapterCounts": v.chapter_count,
                          "headImage": v.head_image,
                          "freeze": self.is_freeze_player(k)
                          }
                    member_info.append(_m)

        return member_info

    def search_tea_house_member_info(self, operator, key_word):
        """
        搜索冠名赛中的匹配成员
        :param operator: 搜索者数据库id
        :param key_word: 关键字
        :return:
        """
        key_word = key_word.encode('utf-8').decode()
        DEBUG_MSG('key_word:%s' % key_word)
        operator_info = self.memberInfo[operator]
        member_info = []
        count = 0
        for k, v in self.memberInfo.items():
            if (not key_word) or (key_word == str(k)) or (key_word in v.name):
                # 可以搜自己，搜自己下级；楼主、助理可以搜所有
                if (operator == k) or (operator_info.level == 100) or (operator_info.level == 10):
                    _m = {"name": v.name,
                          "id": k,
                          "headImage": v.head_image
                          }
                    member_info.append(_m)
                    count += 1
                    if count >= 50:
                        break

        return member_info

    def set_game_coin(self, modify_player, game_coin):
        """
        设置玩家比赛分
        :param modify_player:
        :param game_coin:
        :return:
        """
        if modify_player not in self.memberInfo.keys():
            return
        self.memberInfo[modify_player].game_coin = round(float(game_coin),1)
        self.memberInfoJson = self.get_member_info_json()
        self.update_single_member_info_to_client(modify_player)

    def set_player_chapter_count(self, modify_player, chapter_count):
        """
        设置玩家局数
        :param modify_player:
        :param chapter_count:
        :return:
        """
        if modify_player not in self.memberInfo.keys():
            return
        self.memberInfo[modify_player].chapter_count = chapter_count
        self.memberInfoJson = self.get_member_info_json()
        self.update_single_member_info_to_client(modify_player)

    def application_join(self, joiner_db_id, name, head_image, inviter_db_id, gold, on_success=None, on_fail=None):
        """
        申请列表
        :param joiner_db_id:
        :param name:
        :param head_image:
        :param inviter_db_id:
        :param on_success:
        :param on_fail:
        :return:
        """
        self.applicationList[joiner_db_id] = {"accountDBID": joiner_db_id, "playerName": name,
                                              "headImage": head_image, "inviterDBID": inviter_db_id, "gold": gold}
        self.update_tea_house_info_to_client()
        on_success()

    def application_exit(self, exit_db_id, name, head_image, gold, on_success=None, on_fail=None):
        self.exitApplicationList[exit_db_id] = {"accountDBID": exit_db_id, "playerName": name,
                                                "headImage": head_image, "gold": gold}
        self.update_tea_house_info_to_client()
        if on_success:
            on_success()

    def refuse_join_application(self, joiner_db_id, on_success=None, on_fail=None):
        """
        拒绝加入申请
        :param joiner_db_id:
        :param on_success:
        :param on_fail:
        :return:
        """
        self.applicationList.pop(joiner_db_id)
        self.update_tea_house_info_to_client()
        on_success()

    def refuse_exit_application(self, exit_db_id, on_success=None, on_fail=None):
        """
        拒绝加入申请
        :param exit_db_id:
        :param on_success:
        :param on_fail:
        :return:
        """
        self.exitApplicationList.pop(exit_db_id)
        self.update_tea_house_info_to_client()
        on_success()

    def kick_out(self, account_db_id, operator_id, on_success=None, on_fail=None):
        # 不是群主不能踢人
        if operator_id != self.creatorDBID:
            return

        # 不能自己踢自己
        if operator_id == account_db_id:
            return

        account_name = self.memberInfo[account_db_id].name
        self.joinAndExitHistory.append(
            {"accountDBID": account_db_id, "accountName": account_name, "time": int(time.time()), "type": 3})
        if len(self.joinAndExitHistory) > tea_house_config()['joinExitHistoryLimit']:
            self.joinAndExitHistory.pop(0)
        exit_player_level = self.memberInfo[int(account_db_id)].level
        # 如果退出的不是楼主，并且有职位,将其直属和间接所属降级后归为楼主
        if exit_player_level != TeaHousePlayerLevel.Creator and exit_player_level != TeaHousePlayerLevel.Normal:
            for k in self.get_all_members_belong_to_account(account_db_id):
                down_player = self.get_tea_house_player(k)
                if down_player:
                    # 名下成员降级并切归为原来的上级
                    down_player.level = TeaHousePlayerLevel.Normal
                    down_player.belong_to = self.creatorDBID
            """
            for k, v in self.memberInfo.items():
                if v.belong_to == account_db_id:
                    v.belong_to = self.creatorDBID
            """
        self.memberInfo.pop(account_db_id)
        self.memberInfoJson = self.get_member_info_json()

        self.del_rank_info_from_db_id(account_db_id)
        self.del_team_rank_info_from_db_id(account_db_id, exit_player_level)
        self.delete_single_member_info_to_client(account_db_id, requester=operator_id)
        if on_success():
            on_success()

    """
    # 获取当前玩家的所有下级成员,返回数据是个链表
    def fine_down_players(self,account_Id):
        players = []
        for k, v in self.memberInfo:
            if self.is_down_player(k, account_Id):
              players.append(k)
        return players
    """

    def get_member_info_json(self):
        """
        获取成员信息的Json字符串，用来给外部读取
        :return:
        """
        json_info = {}
        for k, v in self.memberInfo.items():
            info = {"g": v.game_coin, "l": v.level}
            json_info[k] = info
        return json.dumps(json_info)

    def get_tea_house_player(self, account_db_id):
        """
        获取冠名赛玩家
        :param account_db_id:
        :return:
        """
        if account_db_id in self.memberInfo:
            return self.memberInfo[account_db_id]

    def update_player_score_control(self, account_db_id):
        # 如果玩家最近输分达到茶楼平均输分的一定倍数，则需要干预给发好牌；干预到玩家赢到一定阈值时停止干预
        # 如果玩家牌局不到30局，则不进行干预
        if account_db_id in self.memberInfo:
            player = self.memberInfo[account_db_id]
            if player.chapter_count < 30:
                DEBUG_MSG("update_player_score_control %s chapter_count:%s" % (account_db_id, player.chapter_count))
                return

            if not player.score_control:
                if player.recent_score < (player.lose_score_threshold * self.lose_avg_score):
                    player.score_control = True
            else:
                if player.recent_score > (player.win_score_threshold * self.win_avg_score):
                    player.score_control = False

            # 幸运数字玩家分数控制
            if self.is_luck_player(account_db_id):
                # if player.recent_score < self.lose_avg_score:
                #     player.luck_score_control = True
                if player.recent_score >= self.win_avg_score:
                    player.luck_score_control = False
                else:
                    player.luck_score_control = True
            else:
                player.luck_score_control = False

            DEBUG_MSG("update_player_score_control2 %s score_control:%s %s %s %s" %
                      (account_db_id, player.score_control, player.lose_score_threshold, player.win_score_threshold,
                       player.recent_score))

    @staticmethod
    def update_tea_house_player_score_control(account_db_id, tea_house_id, score):
        """
        登陆时，更新玩家分数控制信息
        从数据库中获取分数，这里初始化控制信息
        """
        tea_house = KBEngine.globalData["TeaHouseManager"].mgr.get_tea_house_with_id(tea_house_id)
        if tea_house and account_db_id in tea_house.memberInfo:
            player = tea_house.memberInfo[account_db_id]
            # 输分开始干预阈值,赢分停止干预阈值，倍数
            v1, v2 = tea_house_config()['scoreControlMin']
            if 0 <= v1 <= 100 and 0 <= v2 <= 100:
                pass
            else:
                v1, v2 = 1.8, 2.5
            player.lose_score_threshold = random.uniform(v1, v2)

            v1, v2 = tea_house_config()['scoreControlMax']
            if 0 <= v1 <= 100 and 0 <= v2 <= 100:
                pass
            else:
                v1, v2 = 0.3, 0.7
            player.win_score_threshold = random.uniform(v1, v2)

            player.recent_score = score
            # 如果已经在控制，还继续控制
            # player.score_control = False

            tea_house.update_player_score_control(account_db_id)

    def update_tea_house_score_control(self, players_score):
        """
        根据牌局信息，更新茶楼和玩家的分数
        更新是否需要对玩家进行干预
        """
        win_score = 0
        lose_score = 0
        for k, v in players_score.items():
            if k in self.memberInfo:
                recent_score = self.memberInfo[k].recent_score
                self.memberInfo[k].recent_score += v

                # 算茶楼平均分，一个赢家加上本次分之后还是赢家直接加V；一个赢家加上本次分之后变为输家，则赢分清零，输分增加
                # 一个输家加上本次分之后还是输家直接加V；一个输家加上本次分之后变为赢家，则输分清零；赢分增加
                if recent_score > 0:
                    if recent_score + v >= 0:
                        win_score += v
                    else:
                        win_score -= recent_score
                        lose_score += (recent_score + v)
                else:
                    if recent_score + v <= 0:
                        lose_score += v
                    else:
                        lose_score -= recent_score
                        win_score += (recent_score + v)

        self.win_avg_score = (self.win_avg_score * 50 + win_score) / 51
        if self.win_avg_score <= 0:
            self.win_avg_score = 0
        self.lose_avg_score = (self.lose_avg_score * 50 + lose_score) / 51
        if self.lose_avg_score >= 0:
            self.lose_avg_score = 0
        DEBUG_MSG("update_tea_house_score_control %s %s %s %s %s" % (
            self.teaHouseId, self.id, self.win_avg_score, self.lose_avg_score, players_score))

        # 干预发好牌
        for k in players_score.keys():
            self.update_player_score_control(k)

    def get_need_control_score(self, account_db_id):
        if account_db_id in self.memberInfo:
            player = self.memberInfo[account_db_id]
            if player.chapter_count > 30:
                return player.lose_score_threshold * self.lose_avg_score, \
                       player.win_score_threshold * self.win_avg_score, \
                       player.recent_score, \
                       player.score_control, \
                       self.lose_avg_score, \
                       self.win_avg_score, \
                       player.luck_score_control

        return 0, 0, 0, False, 0, 0, False

    def change_player_proportion_new(self, operate_player_db_id, modify_player_db_id, proportion, on_success, on_fail):
        """
        修改抽成比例
        :param operate_player_db_id:
        :param modify_player_db_id:
        :param proportion:
        :param on_success:
        :param on_fail:
        :return:
        """
        if modify_player_db_id not in self.memberInfo.keys():
            on_fail("修改失败，该玩家不是冠名赛成员")
            return

        # 不能修改比自己等级高的
        if self.memberInfo[operate_player_db_id].level <= self.memberInfo[modify_player_db_id].level:
            on_fail("修改失败，权限不足")
            return
        _player = self.get_tea_house_player(modify_player_db_id)
        if proportion < _player.proportion:
            on_fail("修改失败，抽水比例不能小于当前比例")
            return
        _player.proportion = proportion
        self.memberInfoJson = self.get_member_info_json()
        on_success(self)
        self.get_partner_single_member_info(modify_player_db_id, operate_player_db_id)

    def change_player_proportion(self, operate_player_db_id, modify_player_db_id, proportion, on_success, on_fail):
        """
        修改抽成比例
        :param operate_player_db_id:
        :param modify_player_db_id:
        :param proportion:
        :param on_success:
        :param on_fail:
        :return:
        """
        if modify_player_db_id not in self.memberInfo.keys():
            on_fail("修改失败，该玩家不是冠名赛成员")
            return

        # 不能修改比自己等级高的
        if self.memberInfo[operate_player_db_id].level <= self.memberInfo[modify_player_db_id].level:
            on_fail("修改失败，权限不足")
            return

        _player = self.get_tea_house_player(modify_player_db_id)
        _player.proportion = proportion
        self.memberInfoJson = self.get_member_info_json()
        on_success(self)
        self.get_partner_single_member_info(modify_player_db_id, operate_player_db_id)

    def modify_game_coin(self, modifier, operator_entity, game_coin_change, on_success, on_fail):
        """
        修改玩家比赛分
        :param modifier:被修改者数据库id
        :param operator_entity:操作者实体
        :param game_coin_change:
        :param on_success:
        :param on_fail:
        :return:
        """
        operation_db_id = operator_entity.databaseID
        operator_player = self.get_tea_house_player(operation_db_id)
        DEBUG_MSG('modify_game_coin operator_player level:%s' % operator_player.level)
        DEBUG_MSG('modify_game_coin modifier level:%s' % self.memberInfo[modifier].level)

        # 茶楼开启减少比赛分权限才能减少
        if game_coin_change < 0 and not self.canReduceGameCoin:
            on_fail('输入不合法')
            return

        # 管理员以上才能上下比赛分
        if self.memberInfo[operation_db_id].level < TeaHousePlayerLevel.Admin:
            on_fail("修改失败，权限不足")
            return

        if self.memberInfo[operation_db_id].level == TeaHousePlayerLevel.Admin:
            #
            if self.memberInfo[modifier].level == TeaHousePlayerLevel.Creator:
                # 管理员只能给除了群主之外的人上下分
                on_fail('修改失败，权限不足')
                return

            if operation_db_id == modifier:
                # 管理员不能修改自己
                on_fail('修改失败，权限不足')
                return
        else:
            # 被修改者不是修改者的下级,且修改者不是楼主，则修改失败
            if not self.is_down_player(modifier, operation_db_id) and \
                    self.memberInfo[operation_db_id].level != TeaHousePlayerLevel.Creator:
                on_fail('修改失败，权限不足')
                return
            # 不能给比自己等级高的或者同等级的人上下
            if self.memberInfo[operation_db_id].level <= self.memberInfo[modifier].level and \
                    self.memberInfo[operation_db_id].level != TeaHousePlayerLevel.Creator:
                on_fail("修改失败，权限不足")
                return

        # 如果玩家在线并且在游玩并且修改比赛分小于0，不能修改
        player = KBEngine.globalData["AccountMgr"].mgr.get_account(modifier)
        if game_coin_change < 0 and player and player.scene and player.cell:
            if 'teaHouseId' in player.scene.info:
                if player.scene.info['teaHouseId'] == self.teaHouseId:
                    on_fail("修改失败，玩家正在游戏中")
                    return

        if game_coin_change < 0:
            if abs(game_coin_change) > self.memberInfo[modifier].game_coin:
                on_fail("修改失败，超过该成员已有比赛分")
                return
            # 如果操作者是群主，什么也不做
            elif self.memberInfo[operation_db_id].level == TeaHousePlayerLevel.Creator:
                pass
            else:
                # 给别人下比赛币时不会给操作者增加
                self.memberInfo[operation_db_id].game_coin -= game_coin_change
                self.refresh_game_coin_in_room(operation_db_id, -game_coin_change)


        else:
            # 如果操作者是群主，什么也不做
            if self.memberInfo[operation_db_id].level == TeaHousePlayerLevel.Creator:
                pass
            # 如果操作者比赛分不足
            elif self.memberInfo[operation_db_id].game_coin < game_coin_change:
                on_fail("比赛分不足")
                return
            else:
                # 给别人上比赛币时会给自己减少
                self.memberInfo[operation_db_id].game_coin -= game_coin_change
                self.refresh_game_coin_in_room(operation_db_id, -game_coin_change)

        DEBUG_MSG('modifier gameCoin before add :%s' % self.memberInfo[modifier].game_coin)
        self.memberInfo[modifier].game_coin += game_coin_change
        # 初始分增加
        if not game_coin_change < 0:
            self.memberInfo[modifier].origin_game_coin += game_coin_change
        # if self.memberInfo[modifier].game_coin < 0:
        #     self.memberInfo[modifier].game_coin = 0
        self.memberInfoJson = self.get_member_info_json()
        # DEBUG_MSG("|||||||||||||||||||||||||||||||||||||||||||||||||create_charge_item2")
        self.create_charge_item(modifier, operator_entity,
                                game_coin_change, self.memberInfo[modifier].game_coin)

        DEBUG_MSG('modifier gameCoin after add :%s' % self.memberInfo[modifier].game_coin)

        # 如果玩家在游戏中通知
        self.refresh_game_coin_in_room(modifier, game_coin_change)

        # 通知被修改者和操作者刷新比赛分
        self.update_single_member_info_to_client(modifier)
        self.update_single_member_info_to_client(operator_entity.databaseID)
        if operator_entity.databaseID == self.creatorDBID or operator_player.level == TeaHousePlayerLevel.Partner:
            date = time.strftime("%Y%m", time.localtime(int(time.time())))
            self.update_team_rank_origin_coin(date, modifier, game_coin_change)
        on_success()

    def modify_game_coin_to_public(self, modifier, game_coin_change, on_fail=None, on_success=None):
        """
        提供给后台的修改比赛分接口
        :param on_success:
        :param on_fail:
        :param modifier:被修改者
        :param game_coin_change:
        :return:
        """
        if modifier in self.memberInfo.keys():
            # 群主不涉及比赛分回收
            self.memberInfo[modifier].game_coin += game_coin_change
            # 玩家比赛分不能为负数
            # if self.memberInfo[modifier].game_coin < 0:
            #     self.memberInfo[modifier].game_coin = 0
            self.memberInfoJson = self.get_member_info_json()

            self.update_single_member_info_to_client(modifier)
            # 生成充值记录
            DEBUG_MSG("|||||||||||||||||||||||||||||||||||||||||||||||||create_charge_item")
            self.create_charge_item(modifier,account_manager().get_account(modifier), game_coin_change, self.memberInfo[modifier].game_coin,
                                    from_public=True)
            # 如果玩家在游戏中通知
            self.refresh_game_coin_in_room(modifier, game_coin_change)
            # DEBUG_MSG("----------------------------------%s" % str(modifier))

            if on_success:
                on_success()
        else:
            if on_fail:
                on_fail()

    def create_charge_item(self, modify_player_db_id, operator, modify_count, modified_game_coin, from_public=False):
        """
        生成比赛分充值记录
        :param modify_player_db_id:
        :param operator:
        :param modify_count:
        :param modified_game_coin:
        :param from_public:
        :return:
        """

        def callback(modifier_entity, modifier_db_id, wasActive):
            # 比赛分修改成功,生成一条充值记录
            charge_item = KBEngine.createEntityLocally("GameCoinChargeHistory", {})
            # DEBUG_MSG(operator)
            # DEBUG_MSG("|||||||||||||||||||||||||||||||||||||||||||||||||")
            charge_item.create_one_item(self.teaHouseId, modifier_db_id, modifier_entity.name, modifier_entity.phone,
                                        operator.databaseID, operator.name, operator.phone, operator.proxyType,
                                        modify_count, modified_game_coin)

            # if not wasActive:
            #     modifier_entity.destroy()

            # # 如果是后台创建，销毁创建者实体
            # if from_public:
            #     operator.destroy()

        # 创建被修改者的实体
        KBEngine.createEntityFromDBID("Account", modify_player_db_id, callback)

    def refresh_game_coin_in_room(self, member_db_id, modify_count):
        """
        刷新 cell 端房间的玩家的比赛分
        :param member_db_id:
        :param modify_count:
        :return:
        """
        if member_db_id in self.memberInfo.keys():
            def callback(modifier_entity, modifier_db_id, wasActive):
                # 如果玩家实体存在，cell存在，房间存在，房间的cell存在
                if modifier_entity and modifier_entity.cell:
                    if modifier_entity.scene and modifier_entity.scene.cell:
                        info = modifier_entity.scene.info
                        if info and 'teaHouseId' in info and info['teaHouseId'] == self.teaHouseId:
                            modifier_entity.scene.cell.baseToCell(
                                {"func": "refreshGameCoin", "databaseId": member_db_id, "modifyCount": modify_count})

            KBEngine.createEntityFromDBID("Account", member_db_id, callback)

            # for room_key, room in self.rooms.items():
            #     for k, v in room.info["playerInGame"].items():
            #         if member_db_id == v["databaseId"]:
            #             room.cell.baseToCell(
            #                 {"func": "refreshGameCoin", "databaseId": member_db_id, "modifyCount": modify_count})
            #             return

    def add_player_chapter_count(self, modify_player, chapter_count):
        """
        增加玩家局数
        :param modify_player:
        :param chapter_count:
        :return:
        """
        self.memberInfo[modify_player].chapter_count += chapter_count
        self.memberInfoJson = self.get_member_info_json()

        # 跟新排行榜的玩家局数
        self.update_team_rank_chapter_count(modify_player, chapter_count)

        self.update_single_member_info_to_client(modify_player)

    def player_exit(self, exit_player_db_id, on_success, on_fail):
        """
        玩家退出冠名赛
        :param exit_player_db_id:
        :param on_success:
        :param on_fail:
        :return:
        """

        if exit_player_db_id not in self.memberInfo.keys():
            return
        exit_player_name = self.memberInfo[exit_player_db_id].name
        self.joinAndExitHistory.append(
            {"accountDBID": exit_player_db_id, "accountName": exit_player_name, "time": int(time.time()), "type": 2})
        if len(self.joinAndExitHistory) > tea_house_config()['joinExitHistoryLimit']:
            self.joinAndExitHistory.pop(0)
        if exit_player_db_id in self.exitApplicationList:
            self.exitApplicationList.pop(exit_player_db_id)
        tea_house_player = self.memberInfo[exit_player_db_id]
        exit_level = tea_house_player.level
        # 如果下级用户的上级改为楼主，分成比例为0，身份将为普通人
        if TeaHousePlayerLevel.SmallTeamLeader <= tea_house_player.level <= TeaHousePlayerLevel.Partner:
            # 找到合伙人下面的所有人员，越级判断
            for k in self.get_all_members_belong_to_account(tea_house_player.db_id):
                down_player = self.get_tea_house_player(k)
                if down_player:
                    down_player.level = TeaHousePlayerLevel.Normal
                    down_player.proportion = 0
                    down_player.belong_to = self.creatorDBID
        self.memberInfo.pop(exit_player_db_id)
        self.memberInfoJson = self.get_member_info_json()
        # 从茶楼排行榜中移除该成员信息
        self.del_rank_info_from_db_id(exit_player_db_id)
        self.del_team_rank_info_from_db_id(exit_player_db_id, exit_level)
        self.delete_single_member_info_to_client(exit_player_db_id)
        self.update_tea_house_info_to_client()
        on_success()

    def change_player_level(self, operate_player_db_id, modify_player_db_id, new_level, on_success, on_fail):
        """
        修改冠名赛玩家级别
        :param modify_player_db_id:
        :param modify_player_db_id:
        :param operate_player_db_id:
        :param new_level:
        :param on_success:
        :param on_fail:
        :return:
        """
        if modify_player_db_id not in self.memberInfo.keys():
            on_fail("修改失败，该玩家不是冠名赛成员")
            return

        # 不能修改非直属下级成员
        if self.memberInfo[modify_player_db_id].belong_to != self.memberInfo[operate_player_db_id].db_id:
            on_fail("修改失败，该成员不是你的下级")
            return

        # 不能修改比自己等级高的
        if self.memberInfo[operate_player_db_id].level <= self.memberInfo[modify_player_db_id].level:
            on_fail("修改失败，权限不足")
            return

        # 不能升为比自己等级高的或者同级的
        if new_level >= self.memberInfo[operate_player_db_id].level:
            on_fail("修改失败，权限不足")
            return

        # 如果要修改的玩家的身份是合伙人
        if self.memberInfo[modify_player_db_id].level == TeaHousePlayerLevel.Partner:
            # 如果要修改为合伙人
            if new_level == TeaHousePlayerLevel.Partner:
                on_fail("添加失败，该玩家已是合伙人")
                return
        # 如果是战队长名下有职务的人
        if self.memberInfo[modify_player_db_id].belong_to != self.creatorDBID:
            if self.memberInfo[modify_player_db_id].level != TeaHousePlayerLevel.Normal:
                if new_level == TeaHousePlayerLevel.Partner:
                    on_fail("不能添加战队长名下的成员为战队长")
                    return
        # 助理以上的人不能设为助理
        if self.memberInfo[modify_player_db_id].level > TeaHousePlayerLevel.Admin:
            if new_level == TeaHousePlayerLevel.Admin:
                on_fail("管理者不能设为助理")
                return
        # DEBUG_MSG('----------------------new_level1 %s ' % str(new_level))
        # 如果要把合伙人以下级别的人升为合伙人，则此人上级为楼主，并移除战队数据
        if self.memberInfo[modify_player_db_id].level < TeaHousePlayerLevel.Partner and \
                new_level == TeaHousePlayerLevel.Partner:
            # 被修改者原来的上级
            origin_up = self.get_tea_house_player(self.memberInfo[modify_player_db_id].belong_to)
            # 如果原来的上级是合伙人，首先移除战队贡献
            if origin_up.level == TeaHousePlayerLevel.Partner:
                # 移除新合伙人在原来战队的贡献
                self.remove_player_in_team_rank(modify_player_db_id, origin_up.db_id)
            # 新合伙人上级为楼主
            self.memberInfo[modify_player_db_id].belong_to = self.creatorDBID

        modify_player = self.get_tea_house_player(modify_player_db_id)
        origin_level = modify_player.level
        # 如果小组长以上被取消，则名下所有成员归为楼主
        if modify_player.level >= TeaHousePlayerLevel.SmallTeamLeader:
            if modify_player.level == TeaHousePlayerLevel.Partner and new_level == TeaHousePlayerLevel.Normal:
                self.del_team_rank_info_from_db_id(modify_player.db_id, modify_player.level)
            if new_level == TeaHousePlayerLevel.Normal:
                # 找到合伙人下面的所有人员，越级判断
                for k in self.get_all_members_belong_to_account(modify_player.db_id):
                    down_player = self.get_tea_house_player(k)
                    if down_player:
                        # 名下成员降级并切归为原来的上级
                        down_player.level = TeaHousePlayerLevel.Normal
                        down_player.belong_to = modify_player.belong_to
        # DEBUG_MSG('----------------------new_level2 %s ' % str(new_level))
        modify_player.level = new_level
        modify_player.proportion = 0
        #modify_player. = 0
        self.memberInfoJson = self.get_member_info_json()

        self.update_single_member_info_to_client(modify_player_db_id)
        # 如果修改等级，刷新修改者的合伙人面板信息
        operate_player = get_account_entity_with_db_id(operate_player_db_id)
        if operate_player and operate_player.hasClient:
            operate_player.send_partner_tea_house_partner_info_to_client(self.teaHouseId, operate_player_db_id)
        # 如果修改了等级，刷新被修改者的会员列表
        self.refresh_member_list_to_client(modify_player_db_id)
        # 如果原等级是普通成员现在等级为合伙人，则跟新排行榜
        if origin_level == TeaHousePlayerLevel.Normal and new_level == TeaHousePlayerLevel.Partner:
            self.new_team_rank(modify_player_db_id)
        on_success(self)

    def get_rooms_with_page(self, room_type, anonymity, page_index, started_disappear=False):
        """
        获取指定页码房间信息
        :param started_disappear: 隐藏开始房间
        :param room_type:
        :param anonymity:
        :param page_index:
        :return:
        """
        _room_ids = []
        _rooms = collections.OrderedDict()
        # 开始位置
        page_start = page_index * Const.room_list_page_item
        # 结束位置
        page_end = page_start + Const.room_list_page_item
        for k, v in self.rooms.items():
            if started_disappear and v.info['started']:
                continue
            try:
                # 没有房间类型筛选时显示所有房间
                if not room_type:
                    if v.info["anonymity"] == anonymity:
                        _room_ids.append(k)
                elif v.info["type"] == room_type and v.info["anonymity"] == anonymity:
                    _room_ids.append(k)

            except AttributeError as e:
                ERROR_MSG('TeaHouse get_rooms_with_page %s' % e)
            except KeyError as e:
                ERROR_MSG('TeaHouse get_rooms_with_page %s' % e)

        _room_ids = self.rooms_sort(_room_ids)
        # DEBUG_MSG('roomIds after sorted:%s' % _room_ids)

        index = 0
        for _id in _room_ids:
            if page_start <= index < page_end:
                _info = self.rooms[_id].info.copy()
                if 'currentChapterCount' not in _info:
                    _info['currentChapterCount'] = 0
                # 是否是母桌
                _info['isBaseRoom'] = self.is_base_room(_info['roomId'])
                _rooms[_id] = _info
            index += 1
        return _rooms


    def rooms_sort(self, room_ids):
        # 根据房间是否满员排序
        # 如果开启空桌在后，反转排序，满员在前
        items = sorted(room_ids, key=lambda i:
        (self.rooms[i].info['maxPlayersCount'] == len(self.rooms[i].info['playerInGame'])),
                       reverse=self.empty_location == -1)

        items = sorted(items, key=lambda i: self.is_base_room(self.rooms[i].info['roomId']),
                       reverse=self.empty_location == 0)

        # for i in items:
            # DEBUG_MSG(self.rooms[i].info)

        return items

    def get_rooms_with_room_type(self, room_type, anonymity, started_disappear=False, score_level=0):
        """
        获取类型的所有房间
        :param started_disappear: 隐藏已开始房间
        :param room_type:
        :param anonymity:
        :return:
        """
        _rooms = {}
        for k, v in self.rooms.items():
            if started_disappear and v.info['started']:
                continue
            try:
                # 没有房间类型筛选时显示所有房间
                if not room_type:
                    if v.info["anonymity"] == anonymity:
                        if score_level > 0:
                            if v.info['type'] == "RoomType1" or v.info['type'] == "RoomType4":
                                base_score = v.info["betBase"]
                            else:
                                base_score = v.info["baseScore"]
                            if float(base_score) == float(score_level):
                                _rooms[k] = v
                        else:
                            _rooms[k] = v
                elif v.info["type"] == room_type and v.info["anonymity"] == anonymity:
                    if score_level > 0:
                        if v.info['type'] == "RoomType1" or v.info['type'] == "RoomType4":
                            base_score = v.info["betBase"]
                        else:
                            base_score = v.info["baseScore"]
                        if base_score == float(score_level):
                            _rooms[k] = v
                    else:
                        _rooms[k] = v
            except AttributeError as e:
                ERROR_MSG('TeaHouse get_rooms_with_room_type %s' % e)
            except KeyError as e:
                ERROR_MSG('TeaHouse get_rooms_with_room_type %s' % e)
        return _rooms

    def get_rooms_total_page(self, room_type, anonymity, started_disappear=False):
        """
        获取房间信息总页数
        :param started_disappear: 隐藏开始房间
        :param room_type:
        :param anonymity:
        :return:
        """
        _rooms = self.get_rooms_with_room_type(room_type, anonymity, started_disappear)
        member_count = len(_rooms)
        if member_count % Const.room_list_page_item == 0:
            total_pages = member_count / Const.room_list_page_item
            if total_pages != 0:
                total_pages -= 1
        else:
            total_pages = math.floor(member_count / Const.room_list_page_item)
        return int(total_pages)

    def get_room_by_id(self, room_id):
        """
        获取类型的所有房间
        :param room_id:
        :return:
        """
        for k, v in self.rooms.items():
            if v.info["roomId"] == room_id:
                return v
        return None

    # ----------------------------------会员信息分页相关函数----------------------------------#
    def get_members_with_page(self, page_index, request_db_id=-1):
        """
        获取指定页码成员信息
        :param request_db_id: 请求者数据库id
        :param page_index: 页码，从0开始
        :return:
        """

        members_info = []
        online_count = 0
        for k, v in self.memberInfo.items():
            # 如果玩家实体有客户端，视为在线
            account_entity = get_account_entity_with_db_id(k)
            up_entity = get_account_entity_with_db_id(v.belong_to)
            online_state = bool(account_entity and account_entity.client)
            if online_state:
                online_count += 1
            members_info.append({"level": int(v.level), "name": v.name, "gameCoin": v.game_coin,
                                 "accountDBId": k, "state": online_state,
                                 "belongTo": v.belong_to,
                                 "belongToName": up_entity.name if up_entity else "",
                                 "chapterCounts": v.chapter_count,
                                 "headImage": v.head_image,
                                 'luckyCard': v.lucky_card,
                                 'freeze': self.is_freeze_player(k)
                                 # 'winner':v.winner,
                                 # 'luckCardConsume':v.luckyCardConsume,
                                 })

        # 排序优先级,权限>在线状态,权限大的在前，在线状态为True的在前
        members_info.sort(key=lambda x: (-x['level'], -x['state']))
        # INFO_MSG('[base TeaHouse] request_db_id request_db_id %s' % str(request_db_id))
        # 如果是客户端请求
        if request_db_id != -1:
            request_entity = get_account_entity_with_db_id(request_db_id)
            if request_entity:
                if request_db_id in self.memberInfo.keys():
                    request_level = self.memberInfo[request_db_id].level
                    # 普通成员只能看到自己和群主
                    if request_level == TeaHousePlayerLevel.Normal:
                        members_info = [x for x in members_info if
                                        x['level'] == TeaHousePlayerLevel.Creator or
                                        x['accountDBId'] == request_db_id]
                    # 合伙人、队长、组长能看到自己、群主和名下成员
                    elif request_level >= TeaHousePlayerLevel.SmallTeamLeader:
                        # 获取指定 id 下的所有成员 id，越级判断，A-->B-->C 则，A 也是 C 的下级
                        down_members_id = self.get_all_members_belong_to_account(request_db_id)

                        members_info = [x for x in members_info if
                                        x['level'] == TeaHousePlayerLevel.Creator or
                                        x['accountDBId'] == request_db_id or
                                        x['accountDBId'] in down_members_id
                                        ]
        # 计算总页数
        total_pages = math.ceil(len(members_info) / Const.member_list_page_item)

        # 按页码切片
        page_start = page_index * Const.member_list_page_item
        page_end = page_start + Const.member_list_page_item
        members_info = members_info[page_start:page_end]

        return members_info, total_pages, len(self.memberInfo), online_count

    # ----------------------------------战队信息分页相关函数----------------------------------#

    def get_partner_info_with_page(self, account_id, page_index, level_filter):
        """
        通过页码获取指定战队信息
        :param level_filter: 等级过滤
        :param account_id:
        :param page_index:
        :return:
        """
        partner_info_list = self.get_partner_all_info(account_id, level_filter)

        member_count = len(partner_info_list)
        # 计算总页数
        total_pages = math.ceil(len(partner_info_list) / Const.partner_list_page_item)

        # 排序优先级,权限>在线状态,权限大的在前，在线状态为True的在前
        partner_info_list.sort(key=lambda x: -x['level'])

        # 按页码切片
        page_start = page_index * Const.partner_list_page_item
        page_end = page_start + Const.partner_list_page_item
        partner_info_list = partner_info_list[page_start:page_end]

        return partner_info_list, total_pages, member_count

    def get_partner_info_with_page2(self, account_id, page_index, level_filter):
        """
        通过页码获取指定战队信息
        :param level_filter: 等级过滤
        :param account_id:
        :param page_index:
        :return:
        """
        partner_info_list = self.get_partner_all_info2(account_id, level_filter)

        member_count = len(partner_info_list)
        # 计算总页数
        total_pages = math.ceil(len(partner_info_list) / Const.partner_list_page_item)

        # 排序优先级,权限>在线状态,权限大的在前，在线状态为True的在前
        partner_info_list.sort(key=lambda x: -x['level'])

        # 按页码切片
        page_start = page_index * Const.partner_list_page_item
        page_end = page_start + Const.partner_list_page_item
        partner_info_list = partner_info_list[page_start:page_end]

        return partner_info_list, total_pages, member_count

    def get_partner_single_member_info(self, account_db_id, operator_db_id):
        """
        更新战队个人分成信息
        :param account_db_id:
        :param operator_db_id:
        :return:
        """
        partner_info = {}
        yesterday = 0
        today = 0
        for k in self.performance_detail:
            if str(account_db_id) in self.performance_detail[k]:
                performance_detail = self.performance_detail[k][account_db_id]
                _time = performance_detail['time']
                count = performance_detail['count']
                if self.yesterday_start <= _time <= self.yesterday_end:
                    yesterday = count
                elif self.today_start <= _time <= self.today_end:
                    today = count

        if account_db_id in self.memberInfo:
            partner_info[account_db_id] = {
                "name": self.memberInfo[account_db_id].name, "headImageUrl": self.memberInfo[account_db_id].head_image,
                "belongTo": self.memberInfo[account_db_id].belong_to,
                "invitationCode": self.memberInfo[account_db_id].invitation_code,
                "proportion": self.memberInfo[account_db_id].proportion,
                "level": self.memberInfo[account_db_id].level,
                'userId': self.memberInfo[account_db_id].db_id,
                'todayData': yesterday,
                'yesterdayData': today,
                "performance": self.memberInfo[account_db_id].performance,
                "turnInPerformance": round(self.memberInfo[account_db_id].turn_in_performance, 2)
            }
        account_entity = get_account_entity_with_db_id(operator_db_id)
        if account_entity:
            account_entity.call_client_func('UpdatePartnerSingleMemberInfo', partner_info)

    def get_partner_all_info(self, account_db_id, level_filter):
        """
        获取合伙人名下的抽成信息
        :param level_filter: 等级过滤
        :param account_db_id:
        :return:
        """
        partner_info = []
        for k, v in self.memberInfo.items():
            if k == self.creatorDBID:
                continue
            # 如果有等级过滤器，只查看对应等级的成员
            if level_filter != 0:
                if v.level != level_filter:
                    continue

            if v.belong_to == account_db_id or k == account_db_id:
                performance_detail = []
                if k in self.performance_detail.keys():
                    performance_detail = self.performance_detail[k]

                # 如果玩家实体有客户端，视为在线
                account_entity = get_account_entity_with_db_id(k)
                status = 0
                if account_entity:
                    status = 1

                yesterday_performance, today_performance = self.get_today_and_yesterday(performance_detail)
                p = {"name": v.name, "headImageUrl": v.head_image, "belongTo": v.belong_to,
                     "invitationCode": v.invitation_code, "proportion": v.proportion,
                     "level": v.level,
                     'userId': v.db_id,
                     "myGold": v.game_coin,
                     "performance": round(v.performance, 2),
                     'todayData': round(today_performance, 2),
                     'yesterdayData': round(yesterday_performance, 2),
                     "turnInPerformance": round(v.turn_in_performance, 2),
                     "status": status
                     }
                partner_info.append(p)

        return partner_info

    def get_partner_all_info2(self, account_db_id, level_filter):
        """
        获取合伙人名下的抽成信息
        :param level_filter: 等级过滤
        :param account_db_id:
        :return:
        """
        level_filter = 50
        partner_info = []
        for k, v in self.memberInfo.items():
            if k == self.creatorDBID:
                continue
            # 如果有等级过滤器，只查看对应等级的成员
            if level_filter != 0:
                if v.level != level_filter:
                    continue

            if v.belong_to == account_db_id or k == account_db_id:
                performance_detail = []
                if k in self.performance_detail.keys():
                    performance_detail = self.performance_detail[k]

                # 如果玩家实体有客户端，视为在线
                account_entity = get_account_entity_with_db_id(k)
                status = 0
                if account_entity:
                    status = 1

                yesterday_performance, today_performance = self.get_today_and_yesterday(performance_detail)
                p = {"name": v.name, "headImageUrl": v.head_image, "belongTo": v.belong_to,
                     "invitationCode": v.invitation_code, "proportion": v.proportion,
                     "level": v.level,
                     'userId': v.db_id,
                     "myGold": v.game_coin,
                     "performance": round(v.performance, 2),
                     'todayData': round(today_performance, 2),
                     'yesterdayData': round(yesterday_performance, 2),
                     "turnInPerformance": round(v.turn_in_performance, 2),
                     "status": status
                     }
                partner_info.append(p)

        return partner_info

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

    # ----------------------------------通知客户端房间信息的函数----------------------------------#

    def update_single_room_state_to_client(self, room_entity):
        """
        更新客户端单个房间状态
        :param room_entity:
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
                    _response = {room_entity.info["roomId"]: room_entity.info["started"]}
                    account_entity.call_client_func('UpdateSingleRoomState', _response)

    def update_single_room_info_to_client(self, room_info):
        """
        更新客户端单个房间信息
        :param room_info: 房间信息
        :return:
        """
        not_exit = True
        # 如果不存在返回
        for k, v in self.rooms.items():
            if room_info['roomId'] == v.info['roomId']:
                not_exit = False
                break
        if not_exit:
            return
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
                    _response = {room_info["roomId"]: room_info["playerInGame"]}
                    account_entity.call_client_func('UpdateSingleRoomInfo', _response)

    def update_chapter_count_info(self, roomId, chapter_count):
        """
        更新客户端单个房间信息
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
                    _response = {'roomId': roomId, 'chapterCount': chapter_count}
                    account_entity.call_client_func('UpdateChapterCount', _response)

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
                if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
                    _response = {"oldRoom": old_room_entity.info, "newRoom": new_room_entity.info}
                    account_entity.call_client_func('ChangeSingleRoomInfo', _response)

    def insert_single_room_info_to_client(self, room_entity, old_room_index=-1):
        """
        插入客户端单个房间信息
        :param room_entity:
        :return:
        """
        if old_room_index != -1:
            old_room_index += 1
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
                    _total_page = self.get_rooms_total_page(room_entity.info["type"], room_entity.info["anonymity"])
                    _rooms = self.get_rooms_with_room_type(room_entity.info["type"], room_entity.info["anonymity"])
                    _info = room_entity.info.copy()
                    _info['isBaseRoom'] = self.is_base_room(_info['roomId'])
                    _response = {"room": _info, "totalPage": _total_page, "roomCount": len(_rooms),
                                 'insertIndex': old_room_index}
                    account_entity.call_client_func('InsertSingleRoomInfo', _response)

    def delete_single_room_info_to_client(self, room_entity):
        """
        删除单个房间信息
        :param room_entity:
        :return:
        """
        for k, v in self.memberInfo.items():
            account_entity = get_account_entity_with_db_id(k)
            if account_entity:
                if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
                    _total_rooms = self.get_rooms_with_room_type(room_entity.info["type"],
                                                                 room_entity.info["anonymity"])
                    _total_pages = self.get_rooms_total_page(room_entity.info["type"], room_entity.info["anonymity"])
                    _response = {"roomId": room_entity.info["roomId"], "totalCount": len(_total_rooms), "totalPage":
                        _total_pages}
                    account_entity.call_client_func('DeleteSingleRoomInfo', _response)

    def create_room(self, creator, _args, auto_create=False, on_success=None, on_fail=None,
                    room_end=False, old_room_id=-1, creator_entity=None, record_sql=True):
        """
        创建茶楼房间
        :param record_sql: 是否计入数据库统计
        :param old_room_id: 旧房间id
        :param room_end: 房间结束标识
        :param creator_entity:创建者实体
        :param creator:创建者dbid
        :param _args:参数
        :param auto_create:是否是自动创建的房间
        :param on_success:
        :param on_fail:
        :return:
        """
        old_room_index = -1

        # 筛选出所有同类型的房间
        filter_rooms = [room for room in self.rooms.values() if room.info['type'] == _args['type']]

        # 同类房间手动不能超过上限
        if len(filter_rooms) >= tea_house_config()['roomLimit']:
            if not auto_create:
                on_fail('该游戏房间数量已达上限')
                return

        for index, room_entity in self.rooms.items():
            if room_entity.info['roomId'] == old_room_id:
                old_room_index = index
                break

        # DEBUG_MSG('create_room old_room_index:%s' % old_room_index)

        creator_id = self.creatorDBID
        creator_name = self.get_tea_house_player(creator_id).name
        room_entity = room_manager().create_room(creator, _args, is_auto=True, creator_id=creator_id,
                                                 creator_name=creator_name, creator_entity=creator_entity,
                                                 record_sql=record_sql)
        if room_entity:
            self.add_room(room_entity, room_end=room_end, old_room_index=old_room_index,
                          on_success=on_success, auto_create=auto_create)
        else:
            on_fail("创建房间失败，楼主钻石不足")

    # ----------------------------------通知客户端会员信息的函数----------------------------------#

    def update_single_member_info_to_client(self, update_account):
        """
        更新客户端单个玩家信息
        :return:
        """
        updater = self.get_single_member_info(update_account)
        for k in self.memberInfo.keys():
            try:
                if k == update_account:
                    self.in_tea_house(k).call_client_func('UpdateSingleMemberInfo', {'memberInfo': updater})
            except AttributeError as e:
                pass

    def refresh_member_list_to_client(self, refresh_account):
        """
        通知客户端更新会员列表
        :param refresh_account:
        :return:
        """
        try:
            self.in_tea_house(refresh_account).call_client_func('RefreshMemberList', {})
        except AttributeError:
            ERROR_MSG('refresh_member_list_to_client 找不到玩家%s' % refresh_account)

    def insert_single_member_info_to_client(self, insert_account):
        """
        插入客户端单个玩家信息
        :param insert_account:
        :return:
        """
        # 添加暂不做处理
        # insert = self.get_single_member_info(insert_account)
        # for k, v in self.memberInfo.items():
        #     account_entity = get_account_entity_with_db_id(k)
        #     if account_entity:
        #         if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
        #             account_entity.call_client_func('InsertSingleMemberInfo', {'memberInfo': insert,
        #                                                                        'memberCount': len(self.memberInfo)})
        pass

    def delete_single_member_info_to_client(self, delete_account, requester=-1):
        """
        删除客户端单个玩家信息
        :param requester: 请求者DBID
        :param delete_account:删除账户DBID
        :return:
        """
        if requester != -1:
            account_entity = get_account_entity_with_db_id(requester)
            if account_entity:
                if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
                    account_entity.call_client_func('DeleteSingleMemberInfo', {'deleteDBID': delete_account,
                                                                               'memberCount': len(self.memberInfo)})

    # ----------------------------------排行榜相关----------------------------------#

    def update_tea_house_info_to_client(self, single_send_account=-1):
        """
        将冠名赛最新信息发送给请求者
        :param single_send_account: 单独发送给某个成员
        :return:
        """
        tea_house_info = {"headImage": self.headImage, "name": self.name,
                          "teaHouseId": self.teaHouseId,
                          "creator": self.creatorDBID,
                          "applicationList": self.applicationList,
                          'exitApplicationList': self.exitApplicationList,
                          "createTime": self.createTime,
                          "teaHouseNotice": self.notice,
                          "teaHouseLevel": self.teaHouseLevel,
                          "contactWay": self.contactWay,
                          "teaHouseDBID": self.databaseID,
                          "isSnoring": self.isSnoring,
                          "isReview": self.isReview,
                          "teaHouseType": self.teaHouseType,
                          'canReduceGameCoin': self.canReduceGameCoin,
                          'haveExchangeMall': self.haveExchangeMall,
                          'gameCoinSwitch': self.gameCoinSwitch,
                          'luckyCardSwitch': self.luckyCardSwitch,
                          'luckyCard': self.luckyCard,
                          'emptyLocation': self.empty_location,
                          'fullDisappear': self.full_disappear
                          }
        # 指定发送
        if single_send_account in self.memberInfo.keys():
            account_entity = get_account_entity_with_db_id(single_send_account)
            if account_entity:
                if account_entity.client:
                    if int(account_entity.client_open_tea_house_state) == int(self.teaHouseId):
                        account_entity.call_client_func("RefreshTeaHouseInfo", {"teaHouseInfo": tea_house_info})
        # 全体发送
        else:
            for k, v in self.memberInfo.items():
                account_entity = get_account_entity_with_db_id(k)
                if account_entity:
                    if account_entity.client:
                        if account_entity.client_open_tea_house_state == self.teaHouseId:
                            account_entity.call_client_func('RefreshTeaHouseInfo', {'teaHouseInfo': tea_house_info})

    # ----------------------------------茶楼排行榜函数----------------------------------#
    # 上报，将上报的ID排序存入dict
    def add_player_to_rank(self, player_db_id, date):
        def success():
            pass

        def fail(content):
            player_entity = account_manager().get_account(player_db_id)
            if player_entity:
                player_entity.call_client_func('Notice', [str(content)])

        player = self.get_single_member_info(player_db_id)
        if not player:
            return
        try:
            rank_list = self.rank[date]['rankList']
        except KeyError:
            self.rank[date] = {'rankList': []}
            rank_list = self.rank[date]['rankList']
        try:
            rewards = self.rank[date]['rewards']
        except KeyError:
            self.rank[date]['rewards'] = []
        _game_coin = player['gameCoin']
        game_coin = 0
        for i, m in enumerate(rank_list):
            if m['player_db_id'] == player_db_id:
                if m['rankScore'] >= _game_coin:
                    game_coin = m['rankScore']
                else:
                    game_coin = _game_coin
                del rank_list[i]
                break
        if game_coin == 0:
            game_coin = _game_coin
        self.modify_game_coin(player_db_id, account_manager().get_account(self.creatorDBID), 0 - _game_coin,
                              on_success=success, on_fail=fail)
        arr = {'player_db_id': player_db_id, 'headImg': player['headImage'], 'nickName': player['name'],
               'rankScore': game_coin}
        # 如果排行榜为空，增加一条排行信息
        rank_list.append(arr)
        # 按照分数排序,大的在前面
        rank_list.sort(key=lambda x: -x['rankScore'])
        # DEBUG_MSG(self.rank[date]['rankList'])
        return

    def get_tea_house_rank(self, date, account_id, current_page):
        """
        获取冠名赛排行榜信息（分页处理）
        :param date: 冠名赛时间
        :param account_id: ID列表
        :param current_page: 当前页
        :return:
        """
        account = get_account_entity_with_db_id(account_id)
        page_start = (current_page - 1) * 10
        page_end = current_page * 10 - 1
        my_info = {'player_db_id': account_id, 'headImg': account.headImageUrl, 'nickName': account.name,
                   'rankScore': -1, 'rankLevel': -1, 'origin_game_coin': 0}
        try:
            rank_list = self.rank[date]['rankList']
        except KeyError:
            self.rank[date] = {}
            self.rank[date]['rankList'] = []
            rank_list = self.rank[date]['rankList']
        try:
            rewards = self.rank[date]['rewards']
        except KeyError:
            self.rank[date]['rewards'] = []
        # 计算排名
        for i, r in enumerate(rank_list):
            if r['player_db_id'] == account_id:
                my_info['rankLevel'] = i + 1
                my_info['rankScore'] = r['rankScore']
                break
        x, y = divmod(len(self.rank[date]['rankList']), 10)
        if not y == 0:
            x = x + 1
        return {'rankList': self.rank[date]['rankList'][page_start:page_end],
                'rankRewards': self.rank[date]['rewards'],
                'myInfo': my_info, 'totalPage': x}

    @staticmethod
    def get_rewards_count(rewards):
        diamond_count = 0
        gold_count = 0
        for i, val in enumerate(rewards):
            reward_name = val['name']
            reward_count = val['count']
            if reward_name == '_diamond_reward_':
                diamond_count += reward_count
            elif reward_name == '_gold_reward_':
                gold_count += reward_count
        return diamond_count, gold_count

    def set_rewards(self, date, rewards, callback=None):
        diamond_count, gold_count = self.get_rewards_count(rewards)

        def on_success(baseRef, databaseID, wasActive):
            if baseRef.gold < gold_count or baseRef.roomCard < diamond_count:
                if callback:
                    callback(0)
            else:
                account_manager().modify_room_card(databaseID, - diamond_count)
                account_manager().modify_gold(databaseID, - gold_count)
                try:
                    last_rewards = self.rank[date]['rewards']
                    last_diamond_count, last_gold_count = self.get_rewards_count(last_rewards)
                    account_manager().modify_room_card(databaseID, last_diamond_count)
                    account_manager().modify_gold(databaseID, last_gold_count)
                    self.rank[date]['rewards'] = rewards
                except KeyError:
                    self.rank[date] = {'rewards': rewards}
                if callback:
                    callback(1)
            # 按照奖品的级别从小到大排序，1等奖在最前面
            self.rank[date]['rewards'].sort(key=lambda x: x['level'])
            DEBUG_MSG('set rewards rewards%s' % self.rank[date]['rewards'])

        KBEngine.createEntityFromDBID('Account', self.creatorDBID, on_success)

    def set_team_rewards(self, date, rewards, callback=None):
        diamond_count, gold_count = self.get_rewards_count(rewards)

        def on_success(baseRef, databaseID, wasActive):
            if baseRef.gold < gold_count or baseRef.roomCard < diamond_count:
                if callback:
                    callback(0)
            else:
                account_manager().modify_room_card(databaseID, - diamond_count)
                account_manager().modify_gold(databaseID, - gold_count)
                try:
                    # 重设奖励，将原来的奖励还给楼主
                    last_rewards = self.teamRank[date]['rewards']
                    last_diamond_count, last_gold_count = self.get_rewards_count(last_rewards)
                    account_manager().modify_room_card(databaseID, last_diamond_count)
                    account_manager().modify_gold(databaseID, last_gold_count)
                    self.teamRank[date]['rewards'] = rewards
                except:
                    self.teamRank[date] = {'rewards': rewards}
                if callback:
                    callback(1)

        KBEngine.createEntityFromDBID('Account', self.creatorDBID, on_success)

    def del_rank_info_from_db_id(self, dataBaseId):
        date = time.strftime('%Y%m%d', time.localtime(int(time.time())))
        # DEBUG_MSG(date)
        if date not in self.rank.keys():
            return
        for i, rankifo in enumerate(self.rank[date]['rankList']):
            if int(rankifo['player_db_id']) == int(dataBaseId):
                del self.rank[date]['rankList'][i]

    def del_team_rank_info_from_db_id(self, dataBaseId, exit_player_level):
        """
        从数据库删除排行榜分
        :param dataBaseId:
        :param exit_player_level:
        :return:
        """
        # DEBUG_MSG('del_rank_info_from_db_id %s' % dataBaseId)
        date = time.strftime('%Y%m', time.localtime(int(time.time())))
        if date not in self.teamRank.keys():
            return
        if exit_player_level == TeaHousePlayerLevel.Partner:
            del self.teamRank[date][dataBaseId]

    def update_team_rank_winner(self, account_db_id, performance_count):
        '''
        :param:account_db_id 用户ID
        :param:performance_count 抽成房费  对应大赢家字段
        :return:
        '''
        self.get_tea_house_player(account_db_id).winner += performance_count
        date = time.strftime("%Y%m", time.localtime(int(time.time())))
        if self.memberInfo[account_db_id].level == TeaHousePlayerLevel.Partner:
            leader_db_id = account_db_id
        else:
            if self.find_Partner(account_db_id):
                leader_db_id = self.find_Partner(account_db_id)
            else:
                return
        if date not in self.teamRank.keys():
            return

        # 如果没有本月数据，初始化数据
        if date not in self.teamRank or leader_db_id not in self.teamRank[date]:
            self.new_team_rank(leader_db_id)

        self.teamRank[date][leader_db_id]['winner'] = 0
        for k, v in self.memberInfo.items():
            if not k == leader_db_id and not v.belong_to == leader_db_id:
                continue
            self.teamRank[date][leader_db_id]['winner'] += v.winner

    def update_team_rank_lucky_card(self, account_db_id, change_lucky_card):
        '''
        更新排行榜福卡信息
        :param account_db_id:
        :param change_lucky_card:
        :return:
        '''
        self.get_tea_house_player(account_db_id).lucky_card_consume += change_lucky_card
        date = time.strftime("%Y%m", time.localtime(int(time.time())))
        if self.memberInfo[account_db_id].level == TeaHousePlayerLevel.Partner:
            leader_db_id = account_db_id
        else:
            if self.find_Partner(account_db_id):
                leader_db_id = self.find_Partner(account_db_id)
            else:
                return
        if date not in self.teamRank.keys():
            return
        # DEBUG_MSG('队长ID%s' % leader_db_id)

        # 如果没有本月数据，初始化数据
        if date not in self.teamRank or leader_db_id not in self.teamRank[date]:
            self.new_team_rank(leader_db_id)

        self.teamRank[date][leader_db_id]['luckyCard'] = 0
        for k, v in self.memberInfo.items():
            if not k == leader_db_id and not v.belong_to == leader_db_id:
                continue
            self.teamRank[date][leader_db_id]['luckyCard'] += v.lucky_card_consume

    def update_team_rank_chapter_count(self, account_db_id, chapter_count):
        '''
        更新排行榜牌局总数
        :param account_db_id:
        :param chapter_count:
        :return:
        '''
        date = time.strftime("%Y%m", time.localtime(int(time.time())))
        if self.memberInfo[account_db_id].level == TeaHousePlayerLevel.Partner:
            leader_db_id = account_db_id
        else:
            if self.find_Partner(account_db_id):
                leader_db_id = self.find_Partner(account_db_id)
            else:
                return
        if date not in self.teamRank.keys():
            return
        # 如果没有本月数据，初始化数据
        if date not in self.teamRank or leader_db_id not in self.teamRank[date]:
            self.new_team_rank(leader_db_id)
        self.teamRank[date][leader_db_id]['chapterCount'] = 0
        for k, v in self.memberInfo.items():
            if not k == leader_db_id and not v.belong_to == leader_db_id:
                continue
            self.teamRank[date][leader_db_id]['chapterCount'] += v.chapter_count

    def update_team_rank_origin_coin(self, date, account_db_id, add_game_coin):
        if self.memberInfo[account_db_id].level == TeaHousePlayerLevel.Partner:
            leader_db_id = account_db_id
        else:
            if self.find_Partner(account_db_id):
                leader_db_id = self.find_Partner(account_db_id)
            else:
                return
        if date not in self.teamRank.keys():
            return
        # 如果没有本月数据，初始化数据
        if (date not in self.teamRank or leader_db_id not in self.teamRank[date]) and \
                self.memberInfo[account_db_id].level == TeaHousePlayerLevel.Partner:
            self.new_team_rank(leader_db_id)
        self.teamRank[date][leader_db_id]['originGameCoin'] = 0
        for k, v in self.memberInfo.items():
            if not k == leader_db_id and not v.belong_to == leader_db_id:
                continue
            self.teamRank[date][leader_db_id]['originGameCoin'] += v.origin_game_coin

    def find_Partner(self, accoutid):
        """
          寻找上级，直到合伙人
          accoutid:不是楼主，合伙人
        """
        while True:
            try:
                if self.memberInfo[accoutid].level == TeaHousePlayerLevel.Creator or \
                        self.memberInfo[accoutid].level == TeaHousePlayerLevel.Partner:
                    return 0
                if self.memberInfo[self.memberInfo[accoutid].belong_to].level == TeaHousePlayerLevel.Creator:
                    return 0
                if self.memberInfo[self.memberInfo[accoutid].belong_to].level == TeaHousePlayerLevel.Partner:
                    return self.memberInfo[accoutid].belong_to
                else:
                    accoutid = self.memberInfo[accoutid].belong_to
            except:
                DEBUG_MSG("find_Partner==>DEBUG_MSG", None)
                return 0

    def new_team_rank(self, leader_db_id):
        """
        新建一个战队数据
        :param leader_db_id:
        :return:
        """
        date = time.strftime('%Y%m', time.localtime(int(time.time())))
        leader_player = self.get_tea_house_player(leader_db_id)
        if date not in self.teamRank.keys():
            self.teamRank[date] = {}
        self.teamRank[date][leader_db_id] = {'winner': leader_player.winner,
                                             'luckyCard': leader_player.lucky_card_consume,
                                             'chapterCount': leader_player.chapter_count,
                                             'originGameCoin': leader_player.origin_game_coin
                                             }

    def remove_player_in_team_rank(self, remove_player_id, team_leader):
        """
        将某位成员的数据从战队中移除
        :param remove_player_id:
        :param team_leader:
        :return:
        """
        remove_player = self.get_tea_house_player(remove_player_id)
        date = time.strftime('%Y%m', time.localtime(int(time.time())))
        if date in self.teamRank and team_leader in self.teamRank[date]:
            team_rank = self.teamRank[date][team_leader]
            team_rank['winner'] -= remove_player.winner
            team_rank['luckyCard'] -= remove_player.lucky_card_consume
            team_rank['chapterCount'] -= remove_player.chapter_count
            team_rank['originGameCoin'] -= remove_player.origin_game_coin

    def get_team_rank(self, date):
        """
        发送战队排名信息
        :param date:那个月
        :return:
        """
        _dict = {}
        if date not in self.teamRank.keys():
            self.teamRank[date] = {}
        else:
            for k, v in self.teamRank[date].items():
                if k == 'rewards':
                    continue
                if 'winner' not in v.keys():
                    v['winner'] = 0
                if 'luckCard' not in v.keys():
                    v['luckCard'] = 0
                if 'chapterCount' not in v.keys():
                    v['chapterCount'] = 0
                if 'originGameCoin' not in v.keys():
                    v['originGameCoin'] = 0
                _dict[k] = v['winner']
        _dict = sorted(_dict.items(), key=lambda d: d[1], reverse=True)
        returnArr = []
        for i, val in enumerate(_dict):
            dataBaseId = val[0]
            returnArr.append({
                'playerId': val[0],
                'nickName': self.memberInfo[dataBaseId].name,
                'headImg': self.memberInfo[dataBaseId].head_image,
                'winner': self.teamRank[date][dataBaseId]['winner'],
                'luckCard': self.teamRank[date][dataBaseId]['luckyCard'],
                'chapterCount': self.teamRank[date][dataBaseId]['chapterCount'],
                'originCoin': self.teamRank[date][dataBaseId]['originGameCoin'],
            })
        if 'rewards' not in self.teamRank[date].keys():
            self.teamRank[date]['rewards'] = []

        return {'rewards': self.teamRank[date]['rewards'], 'teamRankInfo': returnArr}

    # ----------------------------------通用函数----------------------------------#
    def in_tea_house(self, account):
        """
        某位用户是否需要收到该冠名赛信息
        :param account:
        :return:
        """
        account_entity = get_account_entity_with_db_id(account)
        # 玩家实体存在
        if account_entity:
            # 玩家客户端存在，玩家打开的是此冠名赛面板
            if account_entity.client and account_entity.client_open_tea_house_state == self.teaHouseId:
                return account_entity
        return None

    def get_all_members_belong_to_account(self, account_db_id: int):
        """
        获取指定 id 下的所有成员 id，越级判断，A-->B-->C 则，A 也是 C 的下级
        :param account_db_id:
        :return:
        """
        belong_members_id = []
        for k, v in self.memberInfo.items():
            if self.is_down_player(k, account_db_id):
                # INFO_MSG('[base is_down_player] account_db_id %s  k %s' % (str(account_db_id), str(k)))
                belong_members_id.append(k)

        return belong_members_id

    def is_down_player(self, down: int, up: int):
        """
        判断 up 是不是 down 的上级，越级判断，A-->B-->C 则，A 也是 C 的下级
        :param down: 下级id
        :param up: 上级id
        :return:
        """

        def get_belong_recursive(_down, _up):
            player = self.get_tea_house_player(_down)
            if not player:
                return False

            # 如果没有上级，则找不到目标上级
            elif player.belong_to == 0:
                return False

            # 找到目标上级
            elif player.belong_to == _up:
                return True

            # 如果上级是自己，则找不到目标上级
            elif player.belong_to == player.db_id:
                return False

            elif player.belong_to != _up:
                # 找到上级玩家
                return get_belong_recursive(player.belong_to, _up)

            else:
                return False

        return get_belong_recursive(down, up)

    # ----------------------------------茶楼设置----------------------------------#

    def refresh_tea_house_info_to_room_cell(self, room_id=-1):
        """
        将一些茶楼信息发送到茶楼房间
        :return:
        """
        tea_house_info = {'luckyCardSwitch': self.luckyCardSwitch, 'gameCoinSwitch': self.gameCoinSwitch}
        # 如果没有id发给所有房间
        if room_id == -1:
            for k, v in self.rooms.items():
                if v.cell:
                    v.cell.baseToCell({'func': 'refreshTeaHouseInfo', 'info': tea_house_info})
        # 如果有id发给指定房间
        else:
            for k, v in self.rooms.items():
                if v.info['roomId'] == room_id and v.cell:
                    v.cell.baseToCell({'func': 'refreshTeaHouseInfo', 'info': tea_house_info})
                    return

    # ----------------------------------福卡相关----------------------------------#
    def receive_lucky_card(self, receiver, on_success, on_fail):
        """
        福卡领取
        :param on_success:
        :param on_fail:
        :param receiver:领取者
        :return:
        """
        if not self.luckyCardSwitch:
            on_fail('此功能暂未开启')
            return

        player = self.get_tea_house_player(receiver)
        if not player:
            on_fail('茶楼没有此玩家')
            return

        if player.level != TeaHousePlayerLevel.Creator:
            on_fail('权限不足')
            return

        if self.luckyCard > Const.ServerGameConfigJson.config_json['TeaHouse']['minReceiveLuckyCardStandard']:
            on_fail('福卡数过多，无法领取')
            return

        gift_lucky_card = tea_house_config()['receiveLuckyCard']
        self.luckyCard += gift_lucky_card
        # new_record = {'count': gift_lucky_card, 'time': int(time.time()),
        #               'operatorDBID': receiver, 'operatorName': player.name,
        #               'modifier': receiver, 'modifierName': player.name,
        #               'type': 'receive'}
        # player.lucky_modify_history.append(new_record)
        self.update_tea_house_info_to_client()
        on_success()

    def modify_lucky_card(self, operator_db_id, modifier_db_id, lucky_card_change, on_success, on_fail):
        """
        修改福卡
        :param operator_db_id: 操作者
        :param modifier_db_id: 被修改者
        :param lucky_card_change:
        :param on_success:
        :param on_fail:
        :return:
        """
        modifier_player = self.get_tea_house_player(modifier_db_id)
        operate_player = self.get_tea_house_player(operator_db_id)
        operator_entity = get_account_entity_with_db_id(operator_db_id)
        if not self.luckyCardSwitch:
            on_fail('此功能暂未开启')
            return

        if lucky_card_change < 0:
            if abs(lucky_card_change) > modifier_player.lucky_card:
                on_fail("修改失败，超过已有福卡")
                return
            if operator_db_id == self.creatorDBID:
                self.luckyCard += abs(lucky_card_change)
            else:
                operate_player.lucky_card -= lucky_card_change
        else:
            # 如果楼主，扣茶楼福卡
            if operator_db_id == self.creatorDBID:
                if self.luckyCard < lucky_card_change:
                    on_fail("冠名赛福卡不足")
                    return
                self.luckyCard -= lucky_card_change
            # 如果是合伙人，扣合伙人福卡
            else:
                if operate_player.lucky_card < lucky_card_change:
                    on_fail("福卡不足")
                    return
                operate_player.lucky_card -= lucky_card_change

        modifier_player.lucky_card += lucky_card_change
        # 如果是奖励的福卡，不存储进修改记录
        # 存储记录
        new_record = {'count': lucky_card_change, 'time': int(time.time()),
                      'operatorDBID': operator_db_id, 'operatorName': operator_entity.name,
                      'modifier': modifier_db_id, 'modifierName': modifier_player.name,
                      'modifiedCount': modifier_player.lucky_card,
                      'type': 'modify'}
        modifier_player.lucky_modify_history.append(new_record)
        operate_player.lucky_modify_history.append(new_record)
        self.memberInfoJson = self.get_member_info_json()

        # 如果玩家在游戏中通知
        self.refresh_lucky_card_in_room(modifier_db_id, lucky_card_change)
        # 通知被修改者和操作者福卡
        self.update_single_member_info_to_client(modifier_db_id)
        self.update_single_member_info_to_client(operator_db_id)

        self.update_tea_house_info_to_client()
        on_success()

    def add_today_lucky_card_consume(self, add):
        """
        增加今日福卡消耗记录
        :param add:
        :return:
        """
        today_date = datetime.date.today()
        today_start = int(time.mktime(today_date.timetuple()))
        today_end = int(time.mktime(today_date.timetuple()) + 86399)

        length = len(self.todayLuckyCardConsume)
        if len(self.todayLuckyCardConsume) == 0 or today_start > self.todayLuckyCardConsume[length - 1]['date']:
            self.todayLuckyCardConsume.append({'date': today_end, 'luckyCardConsume': add})
        else:
            self.todayLuckyCardConsume[-1]['luckyCardConsume'] += add

        # 只存两天的记录
        if len(self.todayLuckyCardConsume) > 2:
            del self.todayLuckyCardConsume[0]

    def consume_lucky_card(self, modifier_db_id, lucky_card_change):
        """
        消耗福卡
        :param modifier_db_id:
        :param lucky_card_change:
        :return:
        """
        modifier_player = self.get_tea_house_player(modifier_db_id)
        modifier_player.lucky_card -= lucky_card_change
        # 不把楼主的福卡消耗计入今日福卡消耗和排行榜
        if modifier_db_id != self.creatorDBID:
            # 记录福卡消耗
            self.add_today_lucky_card_consume(lucky_card_change)
            # 将福卡消耗计入排行榜
            self.update_team_rank_lucky_card(modifier_db_id, lucky_card_change)

        # 如果玩家在游戏中通知
        self.refresh_lucky_card_in_room(modifier_db_id, lucky_card_change)
        self.update_single_member_info_to_client(modifier_db_id)

    def refresh_lucky_card_in_room(self, member_db_id, modify_count):
        """
        刷新 cell 端房间的玩家的比赛分
        :param member_db_id:
        :param modify_count:
        :return:
        """
        if member_db_id in self.memberInfo.keys():
            for room_key, room in self.rooms.items():
                for k, v in room.info["playerInGame"].items():
                    if member_db_id == v["databaseId"]:
                        room.cell.baseToCell(
                            {"func": "refreshLuckyCard", "databaseId": member_db_id, "modifyCount": modify_count})
                        return

    def get_lucky_card_history(self, member, on_fail):
        """
        获取成员福卡记录
        :param member:会员id
        :param on_fail:
        :return:
        """
        if not self.luckyCardSwitch:
            on_fail('此功能暂未开启')
            return

        player = self.get_tea_house_player(member)
        if not player:
            on_fail('茶楼没有此玩家')
            return

        return player.lucky_modify_history

    def get_online_members(self, account_db_id):
        """获取在线成员列表"""

        # 获取在线玩家，排序，分页
        def get_online_member(self):
            online_info = {}
            account_mgr = KBEngine.globalData["AccountMgr"].mgr
            for k, v in self.memberInfo.items():
                account_entity = account_mgr.get_account(k)
                if account_entity:
                    if account_entity.client:
                        online_info[k] = {"databaseId": account_entity.userId,
                                          'state': account_entity.playing_stage.value,
                                          'maxChapterCount': account_entity.room_chapter_count,
                                          'curChapterCount': account_entity.cur_chapter_count,
                                          'nickName': account_entity.name,
                                          'headImg': account_entity.headImageUrl}
            return online_info

        online_list = get_online_member(self)
        DEBUG_MSG("get_online_member_list %s" % online_list)

        page_size = 20
        pos_start = 0

        # 随机取是随机开始位置，不够一页时再从头取
        key_list = list(online_list.keys())
        ret_list = []
        total_count = len(key_list)
        if page_size > total_count:
            ret_list = key_list
        else:
            pos_start = random.randint(0, total_count)
            ret_list = key_list[pos_start:]
            tmpcount = page_size - len(ret_list)
            ret_list.extend(key_list[:tmpcount])

        ret_data = []
        for k in ret_list:
            if k == account_db_id:
                continue
            if k in online_list:
                ret_data.append(online_list[k])
        return ret_data

    def get_exclude_room_members(self, account_db_id):
        """获取不能同房间的成员列表"""
        # 获取茶楼该成员排斥列表
        members = []
        remove_list = []
        if account_db_id in self.memberInfo:
            player = self.memberInfo[account_db_id]
            for v in player.exclude_players:
                if v in self.memberInfo:
                    player2 = self.memberInfo[v]
                    item = dict()
                    item["id"] = player2.db_id
                    item["name"] = player2.name
                    item["headImage"] = player2.head_image
                    members.append(item)
                else:
                    remove_list.append(v)
            if remove_list:
                for v in remove_list:
                    player.exclude_players.remove(v)
        return members

    def add_exclude_room_members(self, account_db_id, exclude_list):
        """添加不能同房间的成员"""

        if account_db_id in self.memberInfo:
            player = self.memberInfo[account_db_id]
            cur_count = len(player.exclude_players)
            if cur_count > 6:
                return -1
            if len(exclude_list) + cur_count > 6:
                return 6 - cur_count
            if account_db_id in exclude_list:
                return -3
            for exclude_db_id in exclude_list:
                if exclude_db_id in player.exclude_players:
                    return -4
            for exclude_db_id in exclude_list:
                if exclude_db_id in self.memberInfo:
                    if not player.exclude_players:
                        player.exclude_players = []
                    player.exclude_players.append(exclude_db_id)
            return 0
        return -2

    def remove_exclude_room_members(self, account_db_id, exclude_db_id):
        """删除不能同房间的成员"""
        if account_db_id in self.memberInfo:
            player = self.memberInfo[account_db_id]
            if exclude_db_id in player.exclude_players:
                player.exclude_players.remove(exclude_db_id)
        return True

    def luck_num_rand(self):
        """幸运数字随机算法
        从0-999范围中随机，
        每100代表一个数
        """
        return random.randint(0, 999) // 100

    def get_rand_luck_num(self):
        """
        每24小时随机一次，得到3个随机幸运数字
        """
        if time.time() - self.last_rand_time > 24 * 60 * 60:
            self.last_rand_time = time.time()
            self.rand_num.clear()
            tmp_set = set()
            for i in range(5):
                tmp_set.add(self.luck_num_rand())
            tmp_lst = list(tmp_set)
            self.rand_num = tmp_lst[:3]
        return self.rand_num

    def is_luck_player(self, db_id):
        """取玩家账号最后一位数，看是否为幸运数字
        """
        val = db_id % 10
        luck_num = self.get_rand_luck_num()
        if val in luck_num:
            return True
        return False

    def on_room_player_all_leave(self, room_info):
        """
        当一个房间的玩家全部离开
        :return:
        """
        DEBUG_MSG('teaHouse on_room_player_all_leave')
        player_in_game = room_info['playerInGame']
        room_id = room_info['roomId']
        # 如果是未开始的空房间
        if len(player_in_game) == 0 and not room_info['started']:
            same_blank_count = self.get_same_blank_room_config_count(room_info)
            same_manual_count = self.get_same_manual_room_config_count(room_info)
            if same_blank_count > same_manual_count:
                # 解散这个多余房间，并且不会减少手动创建房间数
                self.disband_room(room_id, self.teaHouseId, delete_manual=False)

    def notice_player(self, db_id, content):
        account_entity = account_manager().get_account(db_id)
        if account_entity:
            account_entity.call_client_func('Notice', [content])

    def is_exclude_same_room(self, accountid, otherids):
        account = KBEngine.entities[accountid]
        account_db_id = account.userId
        other_list = []
        for v in otherids:
            if v == accountid:
                continue
            account = KBEngine.entities[v]
            other_list.append(account.userId)
        if not other_list:
            return False
        tea_house_player = self.memberInfo[account_db_id]
        # DEBUG_MSG("is_exclude_same_room %s %s %s %s" % (accountid, otherids, account_db_id, other_list))
        if tea_house_player.is_exclude_others(other_list):
            return True
        for db_id in other_list:
            tea_house_player = self.memberInfo[db_id]
            if tea_house_player.is_exclude_other(account_db_id):
                return True
        return False

    def is_administrator(self, db_id):
        if db_id in self.memberInfo:
            searcher_info = self.memberInfo[db_id]
            return (searcher_info.level == 100) or (searcher_info.level == 10)
        return False

    def is_member(self, db_id):
        return db_id in self.memberInfo

    def get_player_team_game_coin(self, account_id_list):
        team_game_coin_dict = {}
        for account_id in account_id_list:
            DEBUG_MSG("get_player_team_game_coin:%s" % account_id)
            player = self.get_tea_house_player(account_id)
            if player:
                team_game_coin = 0
                # 楼主自动加上楼主的分
                for k, v in self.memberInfo.items():
                    if self.is_down_player(k, account_id):
                        team_game_coin += v.game_coin
                # 楼主之外的人单独加上自己的分
                if TeaHousePlayerLevel.Creator > player.level >= TeaHousePlayerLevel.SmallCaptain:
                    team_game_coin += player.game_coin
                team_game_coin_dict[account_id] = team_game_coin
        DEBUG_MSG("get_player_team_game_coin ss:")
        DEBUG_MSG("get_player_team_game_coin:%s" % team_game_coin_dict)

        return team_game_coin_dict

    def get_player_game_coin(self, account_id_list):
        player_game_coin_dict = {}
        for account_id in account_id_list:
            player = self.get_tea_house_player(account_id)
            if player:
                player_game_coin_dict[account_id] = player.game_coin
        DEBUG_MSG("get_player_game_coin:%s" % player_game_coin_dict)

        return player_game_coin_dict

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


class TeaHousePlayer:
    # 冠名赛玩家级别
    level = -1
    # 数据库id
    db_id = -1
    # 名称
    name = ""
    # TODO E比赛分
    game_coin = 0
    # 福卡数
    lucky_card = 0
    # 福卡修改记录
    lucky_modify_history = []
    # 头像
    head_image = ""
    # 局数统计
    chapter_count = 0
    # 在线状态
    online_state = False
    # 上次查询比赛分时间
    start_query_game_coin_history_time = 0
    # 分成比例
    proportion = 100
    # 邀请码
    invitation_code = 0
    # 历史房间
    historyRooms = {}
    # 属于谁
    belong_to = 0
    # 总收取房费
    performance = 0
    # 总上交房费
    turn_in_performance = 0
    # 加入时间
    join_time = 0
    # 初始分
    origin_game_coin = 0
    # 福卡消耗
    lucky_card_consume = 0
    # 大赢家
    winner = 0
    # 不能同桌
    exclude_players = []

    def __init__(self, level, db_id, name, head_image, belong_to, invitation_code, gold=0):
        self.level = level
        self.db_id = db_id
        self.name = name
        self.head_image = head_image
        self.belong_to = belong_to
        self.invitation_code = invitation_code
        self.lucky_card = 0
        self.lucky_modify_history = []
        self.join_time = int(time.time())
        self.origin_game_coin = 0
        self.lucky_card_consume = 0
        self.winner = 0
        self.historyRooms = {}
        # 输赢分控制
        self.game_coin = round(float(gold),1)
        self.score_control = False
        self.recent_score = 0
        # 输分开始干预阈值,赢分停止干预阈值，倍数
        self.lose_score_threshold = 0
        self.win_score_threshold = 0
        self.luck_score_control = False
        self.exclude_players = []

    def del_game_coin(self):
        self.game_coin = 0

    def add_game_coin(self, count):
        self.game_coin = self.game_coin + count
        self.origin_game_coin = self.origin_game_coin + count

    def is_exclude_others(self, others):
        """
        自己不能和others中任何人同桌
        """
        DEBUG_MSG("is_exclude_others %s %s" % (others, self.exclude_players))
        for v in others:
            if v in self.exclude_players:
                return True
        return False

    def is_exclude_other(self, other):
        """
        自己不能和other同桌
        """
        DEBUG_MSG("is_exclude_other %s %s" % (other, self.exclude_players))
        return other in self.exclude_players

def init_tea_house_player_score_control(account_db_id):
    # DEBUG_MSG("init_tea_house_player_score_control %s" % account_db_id)
    DBCommand.load_tea_house_player_score(account_db_id, TeaHouse.update_tea_house_player_score_control)


class TeaHousePlayerLevel:
    # 创建者
    Creator = 100
    # 合伙人/战队长
    Partner = 50
    BigCaptain = 45   # 大队长
    # 队长
    Captain = 40
    # 中队长
    MediumCaptain = 30
    # 小队长
    SmallCaptain = 28
    BigTeamLeader = 25  # BigTeamLeader
    # 组长
    TeamLeader = 24
    # 中组长
    MediumTeamLeader = 20
    # 小组长
    SmallTeamLeader = 15
    BigAdmin = 14  # BigAdmin
    MediumAdmin = 13  # MediumAdmin
    # 助理
    Admin = 10
    SmallAdmin = 9  # SmallAdmin
    # 普通成员
    Normal = 1




# class TeaHousePlayerLevel:
#     # 创建者
#     Creator = 100
#     # 合伙人/战队长
#     Partner = 50
#     # 队长
#     Captain = 40
#     # 中队长
#     MediumCaptain = 30
#     # 小队长
#     SmallCaptain = 28
#     # 组长
#     TeamLeader = 24
#     # 中组长
#     MediumTeamLeader = 20
#     # 小组长
#     SmallTeamLeader = 15
#     # 助理
#     Admin = 10
#     # 普通成员
#     Normal = 1