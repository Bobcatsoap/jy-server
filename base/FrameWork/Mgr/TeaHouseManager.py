# -*- coding: utf-8 -*-
import datetime
import random
import time

import KBEngine
import DBCommand
import Const

import Utils
from FrameWork.Mgr import Manger
from KBEDebug import DEBUG_MSG, ERROR_MSG
import Functor
from TeaHouse import TeaHousePlayerLevel


def get_account_entity_with_db_id(account_db_id):
    return KBEngine.globalData["AccountMgr"].mgr.get_account(account_db_id)


def account_manager():
    return KBEngine.globalData["AccountMgr"].mgr


def get_db(cb=None):
    """
    检出所有冠名赛
    :param cb:
    :return:
    """

    def func(result, rows, insertid, error):
        ret = []
        if not result:
            return
        for i in result:
            ret.append(int(i[0]))
        if cb:
            cb(ret)

    _command = "select id from tbl_teahouse where sm_teahouseid != -1"
    KBEngine.executeRawDatabaseCommand(_command, func)


class TeaHouseManager(Manger):
    teaHouse_dic = {}
    need_permission = 1
    mainTimerId = -1
    tomorrowStartTimer = -1
    room1_robot_count = 0
    room4_robot_count = 0
    room12_robot_count = 0
    room13_robot_count = 0

    def __init__(self):
        Manger.__init__(self)

        def func(data):
            for i in data:
                KBEngine.createEntityFromDBID("TeaHouse", i, func1)

        def func1(baseRef, databaseID, wasActive):
            """
            茶楼检出成功回调
            :param baseRef:
            :param databaseID:
            :param wasActive:
            :return:
            """
            if baseRef:
                self.teaHouse_dic[baseRef.databaseID] = baseRef
                baseRef.init_save_rooms()
                baseRef.init_other()

        get_db(func)
        self.check_out_create_tea_house_permission_from_db()

    def clear_all_performance(self):
        """
        清除所有茶楼所有玩家携带、裁判数额
        :return:
        """
        for k, v in self.teaHouse_dic.items():
            v.clear_funded_modify_funded()

    def application_create_tea_house(self, creator_db_id, creator_head_image, tea_house_head_image, tea_house_name,
                                     tea_house_type, creator_name,
                                     creator_proxy_type, gold, on_success, on_fail):
        """
        申请创建茶楼
        :param creator_db_id:楼主数据库id
        :param creator_head_image:楼主头像地址
        :param tea_house_head_image:茶楼头像地址
        :param tea_house_name:茶楼名
        :param tea_house_type:茶楼类型
        :param creator_name:楼主名称
        :param creator_proxy_type:楼主代理等级
        :param gold:楼主带入金币
        :param on_success:成功回调
        :param on_fail:失败回调
        :return:
        """
        self.check_create_tea_house_record(creator_db_id, creator_head_image, tea_house_head_image, tea_house_name,
                                           tea_house_type, creator_name)

    def check_create_tea_house_record(self, creator_db_id, creator_head_image,
                                      tea_house_head_image,
                                      tea_house_name, tea_house_type, creator_name):
        """
        检查是否可以创建茶楼
        """
        # for k, v in self.teaHouse_dic.items():
        #     if v.creatorDBID == creator_db_id:
        #         on_fail("每个ID只能创建一个冠名赛")
        #         return
        # 申请创建者
        creator = get_account_entity_with_db_id(creator_db_id)
        # 如果创建冠名赛需要权限，检测是否是代理
        if self.need_permission == 1 and tea_house_type == 0:
            if creator.proxyType == 0:
                creator.call_client_func("Notice", ['您不是代理，无法创建茶楼'])
                return False

        # 检测是否有已存在的申请
        def callback(result, rows, insertid, error):
            if result:
                creator.call_client_func("Notice", ['您申请过创建茶楼，请等待审核'])
                return False

            while True:
                tea_house_id = random.randint(500000, 999999)
                if tea_house_id % 111111 == 0:
                    continue
                # 是否存在该随机ID
                exist = False
                for k, v in self.teaHouse_dic.items():
                    if v.teaHouseId == tea_house_id:
                        exist = True
                        break
                if not exist:
                    break

            self.insert_create_tea_house_record(creator_db_id, creator_head_image,
                                                tea_house_head_image,
                                                tea_house_name, tea_house_type, creator_name,
                                                tea_house_id)
            creator.call_client_func("Notice", ['创建成功，请等待审核'])

        command_sql = 'SELECT * FROM create_tea_house_record where creator_db_id=%s and result=-1' % creator_db_id
        KBEngine.executeRawDatabaseCommand(command_sql, callback)

    def insert_create_tea_house_record(self, creator_db_id, creator_head_image, tea_house_head_image,
                                       tea_house_name, tea_house_type, creator_name, tea_house_id):
        """
        插入创建茶楼记录，等待后台审核通过
        """
        result = -1
        add_time = int(time.time())
        update_time = int(time.time())
        command_sql = 'INSERT INTO create_tea_house_record ' \
                      '(creator_head_image,tea_house_head_image,tea_house_name,' \
                      'creator_name,creator_db_id,tea_house_type,tea_house_id,' \
                      'result,add_time,update_time) ' \
                      'VALUES ("%s","%s","%s","%s",%s,%s,%s,%s,%s,%s)' % (creator_head_image,
                                                                          tea_house_head_image, tea_house_name,
                                                                          creator_name,
                                                                          creator_db_id, tea_house_type,
                                                                          tea_house_id,
                                                                          result, add_time, update_time)

        KBEngine.executeRawDatabaseCommand(command_sql, None)

    def destroy_tea_house_with_id(self, tea_house_id, on_success=None, on_fail=None):
        """
        解散
        :param tea_house_id:
        :param on_success:
        :param on_fail:
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            if tea_house_entity.rooms:
                if on_fail:
                    on_fail("解散冠名赛必须先解散所有房间")
                return
            tea_house_entity.destroy_tea_house()
            if on_success:
                on_success()
        else:
            if on_fail:
                on_fail("找不到此冠名赛")

    def destroy_tea_house_with_creator(self, creator, on_success=None, on_fail=None):
        tea_house_entity = self.get_tea_house_with_creator(creator)
        if tea_house_entity:
            self.destroy_tea_house_with_id(tea_house_entity.teaHouseId)

    def add_account_gold(self, tea_house_dbid, operate_dbid, operated_dbid, sum, on_success, on_fail):
        """
        给玩家加金币
        :param tea_house_dbid:
        :param operate_dbid:
        :param operated_dbid:
        :param sum:
        :param on_success:
        :param on_fail:
        :return:
        """
        _tea_house = self.get_tea_house_with_db_id(tea_house_dbid)
        _tea_house.add_account_gold(operate_dbid, operated_dbid, sum, on_success, on_fail)

    def del_account_gold(self, tea_house_dbid, operate_dbid, operated_dbid, sum, on_success, on_fail):
        """
        给玩家减金币
        :param tea_house_dbid:
        :param operate_dbid:
        :param operated_dbid:
        :param sum:
        :param on_success:
        :param on_fail:
        :return:
        """
        _tea_house = self.get_tea_house_with_db_id(tea_house_dbid)
        _tea_house.del_account_gold(operate_dbid, operated_dbid, sum, on_success, on_fail)

    def snoring_all_tea_house(self, tea_house_type):
        """
        打烊同类型冠名赛
        :return:
        """
        for k, v in self.teaHouse_dic.items():
            if v.teaHouseType == int(tea_house_type):
                v.isSnoring = 1

    def cancel_snoring_all_tea_house(self, tea_house_type):
        """
        取消打烊同类型冠名赛
        :param tea_house_type:
        :return:
        """
        for k, v in self.teaHouse_dic.items():
            if v.teaHouseType == int(tea_house_type):
                v.isSnoring = 0

    def get_tea_houses_by_account_dbid(self, account_db_id):
        """
        找到account_db_id参与的冠名赛
        :param account_db_id:
        :return:
        """
        tea_houses = {}
        for k, v in self.teaHouse_dic.items():
            if v.get_tea_house_player(account_db_id):
                tea_houses[k] = v
        return tea_houses

    def player_in_tea_house(self, account_db_id, tea_house_id):
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            if account_db_id in tea_house_entity.memberInfo.keys():
                return True
            else:
                return False
        else:
            return False

    def get_tea_house_with_creator(self, creator_db_id):
        """
        通过创建者id找到冠名赛
        :param creator_db_id:
        :return:
        """
        for k, v in self.teaHouse_dic.items():
            if v.creatorDBID == creator_db_id:
                return v

    def get_tea_house_with_db_id(self, tea_house_db_id):
        """
        获取冠名赛
        :param tea_house_db_id:
        :return:
        """
        if tea_house_db_id in self.teaHouse_dic:
            return self.teaHouse_dic[tea_house_db_id]

    def get_tea_house_with_id(self, tea_house_id):
        """
        通过冠名赛id查找冠名赛
        :param tea_house_id:
        :return:
        """
        tea_house_db_id = self.get_db_id_with_tea_house_id(tea_house_id)
        return self.get_tea_house_with_db_id(tea_house_db_id)

    def get_db_id_with_tea_house_id(self, tea_house_id):
        """
        通过冠名赛数据库id查找冠名赛
        :param tea_house_id:
        :return:
        """
        for k, v in self.teaHouse_dic.items():
            if v.teaHouseId == tea_house_id:
                return k

    def check_out_create_tea_house_permission_from_db(self):
        """
        从数据库检出创建冠名赛权限信息
        :return:
        """

        def call_back(result, rows, insertid, error):
            if len(result) != 0:
                self.need_permission = int(result[0][0])
                DEBUG_MSG("check_out_create_tea_house_permission need_permission:%s" % self.need_permission)

        command = 'select %s from game_config where type = "%s"' % ('value', 'createTeaHousePermission')
        DEBUG_MSG("check_out_create_tea_house_permission sql:%s" % command)
        KBEngine.executeRawDatabaseCommand(command, call_back)

    def save_tea_house_permission_to_db(self, need_permission):
        """
        修改创建冠名赛需要的权限信息
        :param need_permission:
        :return:
        """

        def call_back(result, rows, insertid, error):
            DEBUG_MSG("save_tea_house_permission_to_db over")

        self.need_permission = need_permission
        command = 'update game_config set %s=%s where type = "%s"' % (
            'value', need_permission, 'createTeaHousePermission')
        DEBUG_MSG("save_tea_house_permission_to_db sql:%s" % command)
        KBEngine.executeRawDatabaseCommand(command, call_back)

    def get_tea_house_player_by_invitation_code(self, invitation_code):
        """
        通过邀请码获取冠名赛玩家
        :param invitation_code:
        :return:
        """
        tea_house = self.get_tea_house_by_invitation_code(invitation_code)
        for k, v in tea_house.memberInfo.items():
            if v.invitation_code == int(v.invitation_code % 1000):
                return v

    def get_tea_house_by_invitation_code(self, invitation_code):
        """
        通过邀请码获取冠名赛
        :param invitation_code:
        :return:
        """
        tea_house_db_id = int(invitation_code / 1000)
        return self.get_tea_house_with_db_id(tea_house_db_id)

    def get_tea_house_single_member_info(self, tea_house_id, account_db_id):
        """
        获取指定冠名赛指定玩家的信息
        :param tea_house_id:冠名赛id
        :param account_db_id:玩家数据库id
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            return tea_house_entity.get_single_member_info(account_db_id)

    def search_tea_house_single_member_info(self, tea_house_id, searcher, key_word):
        """
        搜索指定冠名赛指定玩家的信息
        :param target: 目标DBID
        :param searcher: 搜索者DBID
        :param tea_house_id: 冠名赛ID
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            return tea_house_entity.search_tea_house_single_member_info(searcher, key_word)

    def get_members_black_info_with_page(self, tea_house_id, account_db_id, page_index):
        """
        获取指定冠名赛指定页码的成员拉黑信息
        :param page_index: 页码，从0开始
        :param tea_house_id:冠名赛id
        :param account_db_id:用户数据库id
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        account_entity = get_account_entity_with_db_id(account_db_id)
        if account_entity and tea_house_entity:
            return tea_house_entity.get_members_black_info_with_page(page_index, request_db_id=account_db_id)

    def get_down_members(self, tea_house_id, account_db_id):
        """
        获取指定冠名赛指定页码的成员拉黑信息
        :param tea_house_id:冠名赛id
        :param account_db_id:用户数据库id
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            return tea_house_entity.get_down_members(account_db_id)
        return []

    def set_tea_house_member_block_score(self, tea_house_id, account_db_id, score):
        """
        设置茶楼玩家拉黑分数
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            result = tea_house_entity.set_member_block_score(account_db_id, score)
            return result
        return False

    def set_tea_house_proxy_block_score(self, tea_house_id, account_db_id, score):
        """
        设置茶楼代理拉黑分数
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            result = tea_house_entity.set_proxy_block_score(account_db_id, score)
            return result
        return False

    def member_score_sum(self, tea_house_id, account_db_id, total_gold_change):
        """
        统计茶楼玩家今日、昨日输赢
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            tea_house_entity.member_score_sum(account_db_id, total_gold_change)

    def set_tea_house_black_score(self, tea_house_id, score):
        """
        设置茶楼拉黑分数
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            result = tea_house_entity.set_tea_house_black_score(score)
            return result
        return False

    def set_tea_house_name(self, tea_house_id, name, notice):
        """
        设置茶楼名字
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            result = tea_house_entity.set_tea_house_name(name, notice)
            return result
        return False

    def unblock_tea_house_player(self, tea_house_id, account_db_id):
        """
        解封达到拉黑分数的玩家
        :param tea_house_id:
        :param account_db_id:
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            return tea_house_entity.unblock_tea_house_player(account_db_id)
        return False

    def get_members_with_page(self, tea_house_id, account_db_id, page_index):
        """
        获取指定冠名赛指定页码的成员信息
        :param page_index: 页码，从0开始
        :param tea_house_id:冠名赛id
        :param account_db_id:用户数据库id
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        account_entity = get_account_entity_with_db_id(account_db_id)
        if account_entity and tea_house_entity:
            return tea_house_entity.get_members_with_page(page_index, request_db_id=account_db_id)

    def update_tea_house_info_to_client(self, tea_house_id, request_db_id):
        """
       更新指定冠名赛信息给指定成员
        :param request_db_id:
       :param tea_house_id:冠名赛id
       :return:
       """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            tea_house_entity.update_tea_house_info_to_client(single_send_account=request_db_id)

    def get_rooms_with_page(self, tea_house_id, room_type, anonymity, page_index):
        """
        获取指定冠名赛指定页码的房间信息
        :param tea_house_id:
        :param room_type:
        :param anonymity:
        :param page_index:
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            return tea_house_entity.get_rooms_with_page(room_type, anonymity, page_index)

    def update_single_room_info_to_client(self, tea_house_id, room_info):
        """
        更新客户端单个房间信息
        :param room_info: 房间信息
        :param tea_house_id:
        :return:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            tea_house_entity.update_single_room_info_to_client(room_info)

    def update_chapter_count_info(self, tea_house_id, room_id, count):
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            tea_house_entity.update_chapter_count_info(room_id, count)

    def modify_can_reduce_game_coin(self, tea_house_id, can_reduce):
        """
        修改茶楼减少比赛分权限
        :param can_reduce:
        :return:
        """
        DEBUG_MSG('teaHouseId %s,canReduce %s' % (tea_house_id, can_reduce))
        try:
            self.get_tea_house_with_id(tea_house_id).modify_can_reduce_game_coin(can_reduce)
        except AttributeError as e:
            ERROR_MSG('tea_house_manager modify_can_reduce_game_coin %s' % e)

    def modify_can_reduce_game_coin_all(self, can_reduce):
        """
        修改茶楼减少比赛分权限
        :param can_reduce:
        :return:
        """
        DEBUG_MSG('modify_can_reduce_game_coin_all canReduce %s' % can_reduce)
        try:
            for v in self.teaHouse_dic.values():
                v.modify_can_reduce_game_coin(can_reduce)
        except AttributeError as e:
            ERROR_MSG('tea_house_manager modify_can_reduce_game_coin %s' % e)

    def modify_have_exchange_mall(self, tea_house_id, have_exchange_mall):
        """
        修改茶楼兑换商城权限
        :param tea_house_id:
        :param have_exchange_mall:
        :return:
        """
        DEBUG_MSG('teaHouseId %s,haveExchangeMall %s' % (tea_house_id, have_exchange_mall))

        try:
            self.get_tea_house_with_id(tea_house_id).modify_have_exchange_mall(have_exchange_mall)
        except AttributeError as e:
            ERROR_MSG('tea_house_manager modify_have_exchange_mall %s' % e)

    def addTimer(self):
        # 今天的最后一秒减去当前的时间
        initial_offset = self.today_end - time.time()
        self.mainTimerId = self.add_timer(initial_offset, 24 * 60 * 60, 0)

        tomorrow_distance = self.tomorrow_start - time.time()
        tomorrow_distance += 2
        self.tomorrowStartTimer = self.add_timer(tomorrow_distance, 24 * 60 * 60, 0)

    def save_tea_house_game_coin_data(self):
        for k, v in self.teaHouse_dic.items():
            tea_house = self.get_tea_house_with_db_id(k)
            tea_house_game_coin_info = {}
            for k2, v2 in tea_house.memberInfo.items():
                tea_house_game_coin_info[k2] = v2.game_coin
            write_time = time.time()
            DBCommand.save_tea_house_game_coin_info(write_time, tea_house.teaHouseId, tea_house_game_coin_info)

    def clear_member_block_score(self):
        """
        清除玩家拉黑分
        :return:
        """
        for k, v in self.teaHouse_dic.items():
            v.clear_member_block_score()

    def on_timer(self, _id, arg):
        # 每天23:59:59被调用
        if _id == self.mainTimerId:
            # 获取年月日
            date = time.strftime('%Y%m%d', time.localtime(int(time.time())))
            for k, v in self.teaHouse_dic.items():
                tea_house = self.get_tea_house_with_db_id(k)
                # 每月一号发送战队奖励
                if date[6:8] == '01':
                    self.give_team_reward(date[0:6], k)
                if date not in tea_house.rank:
                    continue
                DEBUG_MSG('TeaHouseMgr teaHouseId %s on_timer '
                          'tea_house rank %s' % (tea_house.teaHouseId, tea_house.rank))
                # 只保存一周之内的排行榜信息
                del_list = []
                for k2, v2 in tea_house.rank.items():
                    if int(k2) <= int(date) - 8:
                        del_list.append(k2)
                for val in del_list:
                    del tea_house.rank[val]
                DEBUG_MSG("tea_house rank after delete %s:" % tea_house.rank)
                if 'rankList' not in tea_house.rank[date]:
                    continue
                if 'rewards' not in tea_house.rank[date]:
                    continue
                # 如果没有设置奖励，或者没有排行榜信息，跳过
                rank_list = tea_house.rank[date]['rankList']
                rewards = tea_house.rank[date]['rewards']
                if not rewards or not rank_list:
                    continue
                DEBUG_MSG('TeaHouseMgr on_timer tea_house rank before reward%s' % tea_house.rank)
                # 已经奖励过的玩家
                rewarded_player_count = 0
                for index, val in enumerate(rewards):
                    # 名额
                    quota = val['quota']
                    for _ in range(quota):
                        if rewarded_player_count >= len(rank_list):
                            break
                        reward_name = val['name']
                        reward_count = int(val['count'])
                        reward_player = rank_list[rewarded_player_count]['player_db_id']
                        DEBUG_MSG('reward:%s,%s,%s' % (reward_name, reward_count, reward_player))
                        self.give_reward(reward_name, reward_count, reward_player,
                                         tea_house.teaHouseId, tea_house.name)
                        rewarded_player_count += 1
                DEBUG_MSG('reward count:%s,teaHouseId:%s' % (rewarded_player_count, tea_house.teaHouseId))

        elif _id == self.tomorrowStartTimer:
            # 存储茶楼
            self.save_tea_house_game_coin_data()
            # 清除拉黑分
            self.clear_member_block_score()

    def give_reward(self, reward_name, reward_count, account_db_id, tea_house_id, tea_house_name, reward_type='day'):
        """
        给前三名奖励
        :param tea_house_name:
        :param account_db_id:
        :param reward_name:
        :param reward_count:
        :param tea_house_id:
        :param reward_type:发送奖励的类型，每月战队奖励，每天排行榜奖励
        :return:
        """

        def on_success(baseRef, databaseID, wasActive):
            account = baseRef
            if reward_name == '钻石':
                account_manager().modify_room_card(databaseID, reward_count, consume_type='rankReward')
            elif reward_name == '金币':
                account_manager().modify_gold(databaseID, reward_count)
            if reward_type == 'day':
                date = time.strftime("%Y-%m-%d", time.localtime(int(time.time())))
            elif reward_type == 'month':
                date = time.strftime("%Y-%m", time.localtime(int(time.time())))
            try:
                account.sys_notice['notice'].append(
                    {'name': reward_name, 'count': reward_count,
                     'date': date,
                     'teaHouseId': tea_house_id, 'teaHouseName': tea_house_name}
                )
                account.sys_notice['read'] = 0
            except:
                account.sys_notice = {'notice': [], 'read': 0}
                account.sys_notice['notice'].append(
                    {'name': reward_name, 'count': reward_count,
                     'date': date,
                     'teaHouseId': tea_house_id, 'teaHouseName': tea_house_name}
                )
                if len(account.sys_notice['notice']) > 20:
                    del account.sys_notice['notice'][0]
                account.sys_notice['read'] = 0
            DEBUG_MSG('sys_notice%s' % account.sys_notice)
            # account.writeToDB()

        KBEngine.createEntityFromDBID('Account', account_db_id, on_success)

    def give_team_reward(self, date, teaHouseId):
        DEBUG_MSG('give_team_reward:date %s teaHouseId %s' % (date, teaHouseId))
        tea_house = self.get_tea_house_with_db_id(teaHouseId)
        if date not in tea_house.teamRank:
            return
        if 'rewards' not in tea_house.teamRank[date]:
            return
        rewards = tea_house.teamRank[date]['rewards']
        if not rewards:
            return
        # 只保存三个月的信息
        del_list = []
        for k, v in tea_house.teamRank.items():
            if int(k) <= int(date) - 3:
                del_list.append(k)
        for val in del_list:
            del tea_house.teamRank[val]
        DEBUG_MSG('tea_house team rank after delete %s:')
        team_rank_info = tea_house.get_team_rank(date)
        # 按比赛分大小从大到小排列
        team_rank_info.sort(key=lambda x: -x['originCoin'])
        # 已经奖励过的玩家
        rewarded_player_count = 0
        for index, val in enumerate(rewards):
            # 名额
            quota = val['quota']
            for _ in range(quota):
                if rewarded_player_count >= len(team_rank_info):
                    break
                reward_name = val['name']
                reward_count = int(val['count'])
                reward_player = team_rank_info[rewarded_player_count]['playerId']
                DEBUG_MSG('teamRank reward:%s,%s,%s' % (reward_name, reward_count, reward_player))
                self.give_reward(reward_name, reward_count, reward_player,
                                 tea_house.teaHouseId, tea_house.name, reward_type='month')
                rewarded_player_count += 1
        DEBUG_MSG('team rank reward count:%s,teaHouseId:%s' % (rewarded_player_count, tea_house.teaHouseId))

    def modify_table_set(self, modifier, _args):
        tea_house_id = -1
        empty_location = -1
        full_disappear = False
        if 'teaHouseId' in _args:
            tea_house_id = _args['teaHouseId']
        if 'emptyLocation' in _args:
            empty_location = _args['emptyLocation']
        if 'fullDisappear' in _args:
            full_disappear = _args['fullDisappear']
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if not tea_house_entity:
            return False
        else:
            tea_house_entity.modify_table_set(modifier, empty_location, full_disappear)

    def get_tea_house_rooms_with_page_index(self, requester, args):
        """
        获取指定冠名赛指定页码的房间信息
        :param args:
        :param requester:
        :return:
        """
        tea_house_id = args["teaHouseId"]
        room_type = args["roomType"]
        anonymity = args["anonymity"]
        page_index = args["pageIndex"]
        score_level = args.get("score_level")
        if not score_level:
            score_level = 0
        if float(score_level) <= 0:
            score_level = 0

        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            # 找到请求者
            requester_player = tea_house_entity.memberInfo[requester]
            if requester_player:
                # 如果开启隐藏开始房间并且不是楼主和助理，只发送未开始房间
                started_disappear = False
                if tea_house_entity.full_disappear:
                    if requester_player.level != TeaHousePlayerLevel.Creator and \
                            requester_player.level != TeaHousePlayerLevel.Admin:
                        started_disappear = True

                # 所有房间
                _rooms = tea_house_entity.get_rooms_with_page(room_type, anonymity, page_index, started_disappear)
                DEBUG_MSG("-------------rooms-------------------")
                import time
                start_time = time.time()
                room_robot_count = self.get_room_robot_count(room_type)
                DEBUG_MSG(room_type)
                if room_type == "" and (score_level <= 0 or score_level == 1):
                    room_robot_count4 = self.get_room_robot_count("RoomType4")
                    room_robot_count1 = self.get_room_robot_count("RoomType1")
                    room_robot_count12 = self.get_room_robot_count("RoomType12")
                    room_robot_count13 = self.get_room_robot_count("RoomType13")
                    _dataitem = {"RoomType4": room_robot_count4, "RoomType1": room_robot_count1,
                                 "RoomType12": room_robot_count12, "RoomType13": room_robot_count13}
                    DEBUG_MSG(_dataitem)
                end_time = time.time()
                DEBUG_MSG("耗时----%s秒" % str(end_time - start_time))
                room_robot_count_list = self.split_integer(room_robot_count, 7)
                if score_level < 0:
                    room_robot_count = room_robot_count_list[0]
                if score_level > 0 and score_level < 1:
                    room_robot_count = room_robot_count_list[1]
                if score_level >= 1 and score_level < 2:
                    room_robot_count = room_robot_count_list[2]
                if score_level >= 2 and score_level < 3:
                    room_robot_count = room_robot_count_list[3]
                if score_level >= 3 and score_level < 5:
                    room_robot_count = room_robot_count_list[4]
                if score_level >= 5 and score_level < 10:
                    room_robot_count = room_robot_count_list[5]
                if score_level >= 10:
                    room_robot_count = room_robot_count_list[6]
                if score_level > 0:
                    DEBUG_MSG("score_level")
                    import collections
                    new_rooms = collections.OrderedDict()
                    for k, v in _rooms.items():
                        if v['type'] != "RoomType23":
                            if v['type'] == "RoomType1" or v['type'] == "RoomType4":
                                base_score = v["betBase"]
                            else:
                                base_score = v["baseScore"]
                            DEBUG_MSG("-------------score_level-------------%s" % str(score_level))
                            DEBUG_MSG("-------------rooms----k----------%s" % str(k))
                            DEBUG_MSG("-------------rooms------gameLevel--------%s" % str(base_score))
                            DEBUG_MSG(v)
                            if float(base_score) == float(score_level):
                                new_rooms[k] = v
                    _rooms = new_rooms
                # 页数
                _total_page = tea_house_entity.get_rooms_total_page(room_type, anonymity, started_disappear)
                # 此类型的总房间数
                _total_room_count = len(
                    tea_house_entity.get_rooms_with_room_type(room_type, anonymity, started_disappear, score_level))
                _data = {"rooms": _rooms, "totalPage": _total_page, "roomCount": _total_room_count}
                _data['room_robot_count'] = room_robot_count
                DEBUG_MSG('----datas')
                DEBUG_MSG(_data)
                if room_type == "" and (score_level <= 0 or score_level == 1):
                    account_manager().get_account(requester).call_client_func("RobotRoomCount", _dataitem)
                account_manager().get_account(requester).call_client_func("GetTeaHouseRoomsWithPageIndex", _data)

            else:
                account_manager().get_account(requester).call_client_func("Notice", ['玩家不存在'])
        else:
            account_manager().get_account(requester).call_client_func("Notice", ['冠名赛不存在'])

    def get_room_robot_count(self, roomtype):
        room_robot_count = 0
        import pymysql
        conn = pymysql.connect('localhost', 'kbe', 'pwd12345603', 'kbe')
        # conn = pymysql.connect('localhost', 'root', '123456', 'game')
        cursor = conn.cursor()

        sql = "select * from room_robot where room_type='%s'" % str(roomtype)
        cursor.execute(sql)
        room_robot_record = cursor.fetchone()
        DEBUG_MSG('room_robot_record-----')
        DEBUG_MSG(room_robot_record)
        if not room_robot_record:
            pass
        else:
            room_robot_count = room_robot_record[2]
        DEBUG_MSG('room_robot_record-----%s' % str(room_robot_count))
        return room_robot_count

    def split_integer(self, m, n):
        assert n > 0
        quotient = int(m / n)
        remainder = m % n
        if remainder > 0:
            return [quotient] * (n - remainder) + [quotient + 1] * remainder
        if remainder < 0:
            return [quotient - 1] * -remainder + [quotient] * (n + remainder)
        return [quotient] * n

    def get_tea_house_player_team_game_coin(self, tea_house_id, account_dbid):
        DEBUG_MSG("get_tea_house_player_team_game_coin teaHouseId:%s,account_dbid:%s" % (tea_house_id, account_dbid))
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            return tea_house_entity.get_player_team_game_coin(account_dbid)
        else:
            return {}

    def get_tea_house_player_game_coin(self, tea_house_id, account_dbid):
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            return tea_house_entity.get_player_game_coin(account_dbid)
        else:
            return {}

    def process_create_tea_house(self, tea_house_id, agree):
        """
        根据网页后台发过来的结果创建茶楼
        """
        if not agree:
            self.update_create_tea_house_record(tea_house_id, 0)
            return
        command_sql = 'SELECT * FROM create_tea_house_record WHERE tea_house_id=%s and result=-1' % tea_house_id

        def create_success(tea_house_entity):
            """
            创建成功如果楼主在线，通知楼主
            """
            if tea_house_entity:
                self.update_create_tea_house_record(tea_house_entity.teaHouseId, 1)
                creator_entity = get_account_entity_with_db_id(tea_house_entity.creatorDBID)
                if creator_entity:
                    args = {"id": tea_house_entity.teaHouseId, "name": tea_house_entity.name,
                            "headImage": tea_house_entity.headImage,
                            "contactWay": tea_house_entity.contactWay}
                    creator_entity.call_client_func("createTeaHouseSuccess", args)
                    creator_entity.get_joined_tea_house_list()
                    # 修改房卡
                    modify_count = Const.GameConfigJson.config_json['Hall']['teaHouseCreateDiamondConsume']
                    account_manager().modify_room_card(creator_entity.userId, -modify_count,
                                                       consume_type='createTeaHouse')

        def create_fail(tea_house_entity, fail_content):
            """
            创建失败如果楼主在线，通知楼主
            """
            if tea_house_entity:
                creator_entity = get_account_entity_with_db_id(tea_house_entity.creatorDBID)
                if creator_entity:
                    args = {"content": fail_content}
                    creator_entity.call_client_func("createTeaHouseFail", args)

        def db_success(result, rows, insertid, error):
            """
            从数据库查找茶楼数据
            """
            if result:
                DEBUG_MSG('teaHouseManager process_create_tea_house %s' % result)
                info = result[0]
                creator_db_id = Utils.bytes_to_int(info[1])
                tea_house_id_db = Utils.bytes_to_int(info[2])
                creator_head_image = Utils.bytes_to_str(info[3])
                tea_house_head_image = Utils.bytes_to_str(info[4])
                name = Utils.bytes_to_str(info[5])
                tea_house_type = Utils.bytes_to_int(info[6])
                gold = 0
                creator_name = Utils.bytes_to_str(info[7])
                tea_house = KBEngine.createEntityLocally("TeaHouse", {'rank': {}})
                tea_house.create(creator_db_id, tea_house_id_db, creator_head_image,
                                 tea_house_head_image, name,
                                 tea_house_type, gold,
                                 creator_name, create_success, create_fail)

        KBEngine.executeRawDatabaseCommand(command_sql, db_success)

    def update_create_tea_house_record(self, tea_house_id, result):
        """
        更新数据库中的茶楼创建审核记录
        """
        command_sql = 'UPDATE create_tea_house_record SET result=%s ' \
                      'WHERE tea_house_id=%s and result=-1' % (result, tea_house_id)
        KBEngine.executeRawDatabaseCommand(command_sql, None)

    def get_tea_house_proxy_info(self, tea_house_id, requester):
        """
        获取茶楼代理信息
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            tea_house_entity.get_tea_house_proxy_info(requester)

    def recur_inning(self, tea_house_id, room_id):
        """
        再来一局
        @param room_id:
        @return:
        :param tea_house_id:
        """
        tea_house_entity = self.get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            return tea_house_entity.recur_inning(room_id)
        else:
            return -1

    @property
    def today_start(self):
        today_date = datetime.date.today()
        today_stamp = time.mktime(today_date.timetuple())
        return int(today_stamp)

    @property
    def today_end(self):
        return self.today_start + 86399

    @property
    def tomorrow_start(self):
        return self.today_start + 86400

    @property
    def yesterday_start(self):
        return self.today_start - 86400

    @property
    def yesterday_end(self):
        return self.today_end - 86400
