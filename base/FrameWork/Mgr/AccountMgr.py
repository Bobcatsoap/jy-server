# -*- coding: utf-8 -*-
import copy
import datetime
import random
import time

import Const
import DBCommand
from KBEDebug import *
from .Manger import Manger
import Account


def account_config():
    return Const.ServerGameConfigJson.config_json['Account']


class AccountMgr(Manger):
    accounts_dic = {}

    invitation_codes = {}

    mainTimerId = 0

    def __init__(self):
        Manger.__init__(self)
        self.online_stat_timer = 0
        self.clear_timer = 0

        def callback(result):
            for r in result:
                database_id = int(str(r[0], 'utf-8'))
                invitation_code = int(str(r[1], 'utf-8'))
                if invitation_code != 0:
                    self.invitation_codes[invitation_code] = database_id

        check_out_invitation_code(callback)

    def addTimer(self):
        now = datetime.datetime.now()
        # 今天零点
        zero_today = now - datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                              microseconds=now.microsecond)
        # 今天的23点59分59秒
        last_today = zero_today + datetime.timedelta(hours=23, minutes=59, seconds=59)
        # 今天的最后一秒减去当前的时间
        initial_offset = time.mktime(last_today.timetuple()) - time.time()
        self.mainTimerId = self.add_timer(initial_offset, 86400, 0)

        # 清除战绩实体和数据库记录
        self.clear_timer = self.add_timer(3600, 3600, 0)

    def addOnlineStatTimer(self):
        # 从整点开始，每10分钟存一次
        now = datetime.datetime.now()
        cur_minute = now.minute % 10
        init_time = 10 - cur_minute
        self.online_stat_timer = self.add_timer(init_time * 60, 600, 0)
        DEBUG_MSG("addOnlineStatTimer %s" % init_time)

    def on_timer(self, _id, arg):
        if _id == self.mainTimerId:
            for account in self.accounts_dic.values():
                account.blessCountToday = 0
                if account.cell:
                    account.cell.baseToCell({'func': 'retTodayBlessCount', 'todayBlessCount': account.blessCountToday})
            DBCommand.reset_account_bless_count()
            # 每天凌晨清除数据库表player_battle_score多天以前的记录
            DEBUG_MSG("定时清除历史战绩信息")
            DBCommand.clear_history_battle_score()

        if _id == self.online_stat_timer:
            player_count = 0
            for v in self.accounts_dic.values():
                if v.online_state:
                    player_count += 1
            DBCommand.update_online_player_count(player_count)

        if _id == self.clear_timer:
            # 清除查询战绩用的房间实体
            Account.Account.clear_history_room()

    def random_invitation_code(self):
        """
        随机邀请码
        :return:
        """
        while True:
            _invitation_code = random.randint(100000, 999999)
            if _invitation_code in self.invitation_codes.keys():
                continue
            else:
                return int(_invitation_code)

    def add(self, account):
        if account.databaseID not in self.accounts_dic:
            self.accounts_dic[account.databaseID] = account

    def remove(self, account):
        if account.databaseID in self.accounts_dic:
            self.accounts_dic.pop(account.databaseID)

    def get_account(self, databaseID):
        if databaseID in self.accounts_dic:
            return self.accounts_dic[databaseID]

    def modify_account_frozen_state(self, account_db_id, frozen_state, on_success=None, on_fail=None):
        def callback(baseRef, databaseID, wasActive):
            baseRef.frozen = frozen_state

            def write_callback(boolean, entity):
                if boolean:
                    # 通知客户端
                    baseRef.call_client_func("frozenAccount", {"frozenState": 1})
                    if on_success:
                        on_success()

                else:
                    if on_fail:
                        on_fail("写入数据库失败")

                if wasActive:
                    pass
                else:
                    baseRef.destroy()

            baseRef.writeToDB(write_callback)

        KBEngine.createEntityFromDBID("Account", account_db_id, callback)

    def set_account_proxy_type(self, account_db_id, proxy_type, superior_id):
        """
        设置玩家代理等级
        :param account_db_id:
        :param proxy_type:
        :param superior_id:
        :return:
        """
        def callback(baseRef, databaseID, wasActive):
            baseRef.proxyType = proxy_type
            baseRef.belong_to = superior_id
            baseRef.writeToDB()
            if wasActive:
                # 如果在线，刷新身份状态
                baseRef.retAccountInfo()
            else:
                baseRef.destroy()

        KBEngine.createEntityFromDBID("Account", account_db_id, callback)

    def modify_account_proxy_type(self, account_db_id, proxy_type, invite_code=-1):
        """
        修改玩家代理等级
        :param invite_code:
        :param account_db_id:
        :param proxy_type:
        :return:
        """

        def callback(baseRef, databaseID, wasActive):
            baseRef.proxyType = proxy_type
            if proxy_type != 0 and baseRef.invitation_code == 0:
                baseRef.invitation_code = self.random_invitation_code()
                self.invitation_codes[baseRef.invitation_code] = databaseID

            # 绑定邀请码
            if invite_code != -1:
                baseRef.belong_to = invite_code

            baseRef.writeToDB()
            if wasActive:
                # 如果在线，刷新身份状态
                baseRef.retAccountInfo()
            else:
                baseRef.destroy()

        KBEngine.createEntityFromDBID("Account", account_db_id, callback)

    def unbind_proxy(self, account_db_id):
        """
        解绑代理
        :param account_db_id:
        :return:
        """

        def callback(baseRef, databaseID, wasActive):
            if baseRef:
                # 解绑定邀请码
                if baseRef.belong_to != 0:
                    baseRef.belong_to = 0
                    baseRef.writeToDB()
                    if wasActive:
                        # 如果在线，刷新身份状态
                        baseRef.retAccountInfo()

                if not wasActive:
                    baseRef.destroy()

        KBEngine.createEntityFromDBID("Account", account_db_id, callback)
    
    def rebinding_proxy(self, account_db_id, proxy_db_id):
        """
        解绑代理
        :param account_db_id:
        :return:
        """

        def callback(baseRef, databaseID, wasActive):
            if baseRef:
                # 解绑定邀请码
                if baseRef.belong_to != 0:
                    baseRef.belong_to = proxy_db_id
                    baseRef.writeToDB()
                    if wasActive:
                        # 如果在线，刷新身份状态
                        baseRef.retAccountInfo()

                if not wasActive:
                    baseRef.destroy()

        KBEngine.createEntityFromDBID("Account", account_db_id, callback)
        
    

    def modify_room_card(self, account_db_id, modify_count, teaHouseId=None, on_success=None, on_fail=None,
                         consume_type='createRoom',
                         record_sql=True):
        """
        修改玩家钻石数量
        :param record_sql: 是否计入数据库统计
        :param consume_type:修改钻石的用途
        :param account_db_id:修改者
        :param modify_count: 修改数量，正数为加，负数为减
        :param on_success: 成功回调
        :param on_fail: 失败回调
        :return:
        """

        def callback(entity, db_id, was_active):
            if entity:
                entity.roomCard += modify_count
                if entity.roomCard <= 0:
                    entity.roomCard = 0

                # 统计今日钻石数量
                # today_date = datetime.date.today()
                # today_end = int(time.mktime(today_date.timetuple()) + 86399)
                today_end = int(time.time())
                if record_sql:
                    DBCommand.modify_room_card_to_db(account_db_id, modify_count, today_end, entity.name, consume_type,
                                                     teaHouseId=teaHouseId)

                if not was_active:
                    entity.writeToDB()
                else:
                    entity.writeToDB()
                    entity.retRoomCard()

        KBEngine.createEntityFromDBID("Account", account_db_id, callback)

    def modify_goldIngot(self, account_db_id, modify_count, on_success=None, on_fail=None, consume_type='createRoom',
                         record_sql=True):
        """
        修改玩家元宝数量
        :param record_sql: 是否计入数据库统计
        :param consume_type:修改元宝的用途
        :param account_db_id:修改者
        :param modify_count: 修改数量，正数为加，负数为减
        :param on_success: 成功回调
        :param on_fail: 失败回调
        :return:
        """

        def callback(entity, db_id, was_active):
            if entity:
                entity.goldIngot += modify_count
                if entity.goldIngot <= 0:
                    entity.goldIngot = 0

                # 统计今日钻石数量
                # today_date = datetime.date.today()
                # today_end = int(time.mktime(today_date.timetuple()) + 86399)
                today_end = int(time.time())
                if record_sql:
                    DBCommand.modify_room_card_to_db(account_db_id, modify_count, today_end, entity.name, consume_type)

                if not was_active:
                    entity.writeToDB()
                else:
                    entity.writeToDB()
                    entity.retGoldIngot()

        KBEngine.createEntityFromDBID("Account", account_db_id, callback)

    def modify_gold(self, account, modify_count, on_success=None, on_fail=None):
        """
        修改玩家金币
        :param account:
        :param modify_count:
        :param on_success:
        :param on_fail:
        :return:
        """

        def callback(entity, db_id, was_active):
            if entity:
                entity.gold += modify_count
                if entity.gold <= 0:
                    entity.gold = 0

                if not was_active:
                    entity.writeToDB()
                else:
                    entity.ret_gold(isModify=True, modify_count=modify_count)

        KBEngine.createEntityFromDBID("Account", account, callback)

    def give_gold_modify(self, account, modify_count, tea_house_id, on_success=None, on_fail=None):
        """
        修改玩家金币
        :param account:
        :param modify_count:
        :param on_success:
        :param on_fail:
        :return:
        """

        def callback(entity, db_id, was_active):
            if entity:
                entity.gold += modify_count
                if entity.gold <= 0:
                    entity.gold = 0

                if not was_active:
                    entity.writeToDB()
                else:
                    # entity.sync_game_coin(tea_house_id)
                    entity.ret_gold(isModify=True, modify_count=modify_count)
                    entity.writeToDB()

        KBEngine.createEntityFromDBID("Account", account, callback)

    def call_all_client(self, func_name, args):
        for k, v in self.accounts_dic.items():
            v.call_client_func(func_name, args)

    def systemNotification(self, title, content):
        """
        系统通知
        :param title:
        :param content:
        :return:
        """
        _notification = {"title": title, "content": content, "datetime": int(time.time())}
        for k, v in self.accounts_dic.items():
            v.call_client_func("Notification", _notification)

    def add_tea_house_invite_in_to_do_list(self, sender_head_image: str, sender_name: str, adder: int,
                                           tea_house_id: int, sender: int):
        """
        将邀请进茶楼加入玩家的待处理事项
        :param sender_head_image:
        :param sender_name:
        :param adder: 需要添加的玩家
        :param tea_house_id:茶楼id
        :param sender:发送邀请的玩家
        :return:
        """

        def on_success_callback(baseRef, databaseID, wasActive):
            create_time = int(time.time())
            flag = Const.ToDoType.tea_house_invite + str(sender) + str(create_time)
            if baseRef:
                for todo in baseRef.todoList:
                    # 不可以多次添加
                    if todo['args']['sender'] == sender and todo['type'] == Const.ToDoType.tea_house_invite:
                        if not wasActive:
                            baseRef.destroy()
                        return

                to_do = {'teaHouseId': tea_house_id, 'sender': sender,
                         'inviterDBID': sender, 'headImage': sender_head_image, 'name': sender_name,
                         'time': create_time, 'description': '%s 邀请你进入 %s 茶楼' % (sender, tea_house_id)}
                if len(baseRef.todoList) >= account_config()['todoListCountLimit']:
                    return
                baseRef.todoList.append({'type': Const.ToDoType.tea_house_invite, 'args': to_do, 'flag': flag})
                baseRef.writeToDB()
                if not wasActive:
                    baseRef.destroy()

        KBEngine.createEntityFromDBID("Account", adder, on_success_callback)

    def add_add_friend_in_to_do_list(self, sender_head_image: str, sender_name: str, adder: int, sender: int):
        """
        将邀请成为好友加入玩家的待处理事项
        :param sender_name: 发送邀请的玩家数据库名字
        :param sender_head_image: 发送邀请的玩家头像
        :param adder:需要添加的玩家数据库id
        :param sender:发送邀请的玩家数据库id
        :return:
        """
        DEBUG_MSG('AccountMgr::add_add_friend_in_to_do_list adder:%s,sender:%s' % (adder, sender))

        def on_success_callback(baseRef, databaseID, wasActive):
            create_time = int(time.time())
            flag = Const.ToDoType.add_friend + str(sender) + str(create_time)
            if baseRef:
                for todo in baseRef.todoList:
                    # 不可以多次添加
                    if todo['args']['sender'] == sender and todo['type'] == Const.ToDoType.add_friend:
                        if not wasActive:
                            baseRef.destroy()
                        return

                to_do = {'sender': sender, 'time': create_time,
                         'headImage': sender_head_image, 'name': sender_name,
                         'description': '%s 邀请你成为好友' % sender}
                if len(baseRef.todoList) >= account_config()['todoListCountLimit']:
                    return
                baseRef.todoList.append({'type': Const.ToDoType.add_friend, 'args': to_do, 'flag': flag})
                baseRef.writeToDB()
                if not wasActive:
                    baseRef.destroy()

        KBEngine.createEntityFromDBID("Account", adder, on_success_callback)

    def add_notice_in_to_do_list(self, sender_head_image: str, sender_name: str, adder: int, sender: int, content: str):
        """
        将提醒加入待处理事项
        :param sender_name: 发送邀请的玩家数据库名字
        :param sender_head_image: 发送邀请的玩家头像
        :param adder:需要添加的玩家数据库id
        :param sender:发送邀请的玩家数据库id
        :return:
        """

        def on_success_callback(baseRef, databaseID, wasActive):
            create_time = int(time.time())
            flag = Const.ToDoType.notice + str(sender) + str(create_time)
            if baseRef:
                # for todo in baseRef.todoList:
                #     # 不可以多次添加
                #     if todo['args']['sender'] == sender and todo['type'] == Const.ToDoType.add_friend:
                #         if not wasActive:
                #             baseRef.destroy()
                #         return

                to_do = {'sender': sender, 'time': create_time,
                         'headImage': sender_head_image, 'name': sender_name,
                         'description': content}
                if len(baseRef.todoList) >= account_config()['todoListCountLimit']:
                    return
                baseRef.todoList.append({'type': Const.ToDoType.notice, 'args': to_do, 'flag': flag})
                baseRef.writeToDB()
                if not wasActive:
                    baseRef.destroy()

        KBEngine.createEntityFromDBID("Account", adder, on_success_callback)

    def to_do_operation(self, operator: int, flag: str, result: bool):
        """
        待办事项处理
        :param operator:操作者数据库id
        :param flag: 待办事项唯一标识
        :param result: 操作结果
        :return:
        """
        if result:
            self.agree_to_do(operator, flag)
        else:
            self.refuse_to_do(operator, flag)

    def agree_to_do(self, operator: int, flag: str):
        """
        同意待办事项
        :param operator:
        :param flag:
        :return:
        """
        operator_entity = self.get_account(operator)
        DEBUG_MSG('todolist:%s' % operator_entity.todoList)

        def on_success():
            # 成功后删除待办事项
            self.delete_to_do(operator, flag)

        if operator_entity:
            for to_do in operator_entity.todoList:
                if to_do['flag'] == flag:
                    if to_do['type'] == Const.ToDoType.add_friend:
                        operator_entity.add_friend({'accountDBID': to_do['args']['sender']}, on_success=on_success)
                        return
                    elif to_do['type'] == Const.ToDoType.tea_house_invite:
                        operator_entity.join_tea_house_request({'inviterDBID': to_do['args']['inviterDBID'],
                                                                'teaHouseId': to_do['args']['teaHouseId']},
                                                               on_success=on_success())
                        return

    def refuse_to_do(self, operator: int, flag: str):
        """
        拒绝待办事项
        :param operator: 操作者数据库id
        :param flag: 待办事项唯一标识
        :return:
        """
        self.delete_to_do(operator, flag)

    def delete_to_do(self, operator: int, flag: str):
        """
        删除待办事项
        :param flag:
        :param operator:
        :return:
        """
        operator_entity = self.get_account(operator)
        if operator_entity:
            for to_do in operator_entity.todoList:
                if to_do['flag'] == flag:
                    operator_entity.todoList.remove(to_do)
                    operator_entity.writeToDB()
                    # 刷新to_do
                    operator_entity.get_to_do_list()
                    return

    def process_binding_proxy(self, up: int, down: int, result):
        """
        处理绑定代理
        """
        DEBUG_MSG('process_binding_proxy %s:%s:%s' % (up, down, result))
        def callback(baseRef, databaseID, wasActive):
            # def write_callback(boolean, entity):
            # 如果从数据库创建成功并且后台同意绑定代理
            # 删除数据库记录
            # if boolean and result:
            baseRef.belong_to = up
            baseRef.writeToDB()
            DEBUG_MSG('baseRef %s:%s:%s' % (baseRef, baseRef.belong_to, baseRef.name))
            self.add_down_player(up, baseRef.userId, baseRef.name, baseRef.headImageUrl)
            self.update_binding_proxy_req(up, down, result)
            # else:
                # pass
            if wasActive:
                if result == 0:
                    baseRef.call_client_func('Notice', ['绑定代理失败, 绑定被拒绝'])
                else:
                    baseRef.call_client_func('Notice', ['绑定代理成功'])
            else:
                baseRef.destroy()

            # baseRef.writeToDB(write_callback)

        KBEngine.createEntityFromDBID("Account", int(down), callback)

    def insert_binding_proxy_req(self, up, down, result):
        """
        插入绑定代理记录
        """

        def down_callback(baseRef, databaseID, wasActive):
            if baseRef:
                def up_call_back(baseRef2, databaseID2, wasActive2):
                    up_name = baseRef2.name
                    down_name = baseRef.name
                    _time = int(time.time())
                    command_sql = 'INSERT INTO binding_proxy_record ' \
                                  '(up,down,up_nick_name,down_nick_name,result,add_time,update_time) ' \
                                  'VALUES (%s,%s,"%s","%s",%s,%s,%s)' \
                                  % (up, down, up_name, down_name, result, _time, _time)
                    KBEngine.executeRawDatabaseCommand(command_sql, None)
                    baseRef.call_client_func("BindingProxySuccess", ["绑定成功，等待代理审核"])

                KBEngine.createEntityFromDBID("Account", up, up_call_back)

        KBEngine.createEntityFromDBID("Account", down, down_callback)

    def update_binding_proxy_req(self, up, down, result):
        """
        更新数据库中的绑定代理申请记录
        """
        command_sql = "UPDATE binding_proxy_record SET result=%s WHERE up=%s and down=%s" % (result, up, down)
        DEBUG_MSG('AccountMgr delete_binding_proxy_req sql:%s' % command_sql)
        KBEngine.executeRawDatabaseCommand(command_sql, None)

    def send_down_players_info(self, up_player, requester):
        """
        发送名下玩家信息
        """
        def callback(baseRef, databaseID, wasActive):
            if baseRef:
                down_player = baseRef.downPlayer
                requester_entity = self.get_account(requester)
                if requester_entity:
                    requester_entity.call_client_func('GetDownPlayersInfo', down_player)
                if not wasActive:
                    baseRef.destroy()

        KBEngine.createEntityFromDBID('Account', up_player, callback)

    # def get_down_player(self, account_db_id):
    #     """
    #     获取下级玩家
    #     """
    #
    #     def callback(baseRef, databaseID, wasActive):
    #         if baseRef:
    #             down_player = copy.deepcopy(baseRef.downPlayer)
    #             if not wasActive:
    #                 baseRef.destroy()
    #             return down_player
    #         return []
    #
    #     KBEngine.createEntityFromDBID('Account', account_db_id, callback)

    def have_up_player(self, account_db_id):
        """
        是否有上级
        """

        def callback(baseRef, databaseID, wasActive):
            if baseRef:
                have = baseRef.belong_to != 0
                if not wasActive:
                    baseRef.destroy()
                return have
            return False

        KBEngine.createEntityFromDBID('Account', account_db_id, callback)

    def get_up_player(self, account_db_id, callback):
        """
        获取上级玩家
        """

        def callback(baseRef, databaseID, wasActive):
            if baseRef:
                up = baseRef.belong_to
                if not wasActive:
                    baseRef.destroy()
                return up

        KBEngine.createEntityFromDBID('Account', account_db_id, callback)

    def add_down_player(self, up_db_id, down_id, down_name, down_head_image):
        """
        给上级添加下级信息
        """

        def callback(baseRef, databaseID, wasActive):
            baseRef.downPlayer.append({'name': down_name, 'accountDBID': down_id,
                                       'headImage': down_head_image})

        KBEngine.createEntityFromDBID('Account', up_db_id, callback)


def check_out_invitation_code(callback=None):
    """
    检出邀请码
    :param callback:
    :return:
    """

    def func(result, rows, insertid, error):
        if callback:
            if result:
                callback(result)

    command = "SELECT id,sm_invitation_code FROM tbl_account;"
    KBEngine.executeRawDatabaseCommand(command, func)
