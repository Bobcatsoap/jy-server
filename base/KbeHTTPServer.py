# -*- coding: utf-8 -*-
import time
from urllib.parse import unquote

import Const
import kbemain
from KBEHTTPServer import MinHTTPServer
from KBEDebug import *
import DBCommand
import json


def get_tea_house_with_id(tea_house_id):
    return KBEngine.globalData["TeaHouseManager"].mgr.get_tea_house_with_id(tea_house_id)


def get_room_manager():
    return KBEngine.globalData['RoomManager'].mgr


def start():
    server = MinHTTPServer.MinHTTPServer()
    server.listen(56687)
    server.staticRes('html')
    server.route('/Notification', notification)
    server.route('/Recharge', reCharge)
    server.route('/WithdrawCash', withdraw_cash)
    server.route('/DisbandRoom', disband_room)
    server.route('/ratioChange', ratioChange)
    server.route('/ChangeAddOnState', change_account_add_on_state)
    server.route('/ModifyRoomCard', modify_room_card)
    server.route('/ModifyGoldIngot', modify_goldIngot)
    server.route('/ModifyGameCoin', modify_game_coin)
    server.route('/ModifyPlayerFrozenState', modify_player_frozen_state)
    server.route('/DisbandTeaHouse', disband_tea_house)
    # 修改代理等级
    server.route('/ModifyPlayerProxyType', modify_proxy_type)
    # 操作代理申请
    server.route('/ProxyApplicationOperation', proxy_operation)
    server.route('/ModifyScrollAnnouncement', modify_scroll_announcement)
    server.route('/ModifyCreateTeaHousePermission', modify_create_tea_house_permission)
    server.route('/SnoringTeaHouse', snoring_tea_house)
    server.route('/ReloadGameConfigJson', reload_game_config_json)
    server.route('/SnoringAllTeaHouseGame', snoring_all_tea_house_game)
    server.route('/SnoringTeaHouseGame', snoring_tea_house_game)
    server.route('/CancelSnoringAllTeaHouseGame', cancel_all_snoring_tea_house_game)
    server.route('/CancelSnoringTeaHouseGame', cancel_snoring_tea_house_game)
    server.route('/CanReduceGameCoin', can_reduce_game_coin)
    server.route('/CanReduceGameCoinAll', can_reduce_game_coin_all)
    server.route('/HaveExchangeMall', have_exchange_mall)
    server.route('/RedeemGift', redeem_gift)
    server.route('/ChangeServerner', Change_Serverner)
    server.route('/InsertServerner', Insert_Serverner)
    server.route('/DelServerner', Del_Serverner)
    server.route('/changeUrlAddress', change_Url_Address)
    server.route('/changePlacard', change_Placard)
    server.route('/changeMsg', change_Msg)
    server.route('/SnoringAllRoom', snoring_all_room)
    server.route('/ChallengePrize', challenge_prize)
    server.route('/RedeemPrize', redeem_prize)
    server.route('/GameCoinSwitch', change_game_coin_switch)
    server.route('/AddTeamSwitch', change_add_team_switch)
    server.route('/GetGameConfig', get_game_config)
    server.route('/ChangePartnerSwitch', change_partner_switch)
    server.route('/AllowChangeGameCoinSwitch', allow_change_game_coin_switch)
    server.route('/UnbindProxy', unbind_proxy)
    server.route('/RebindingProxy', rebinding_proxy)
    server.route('/GetTeaHousePlayerTeamGameCoin', get_tea_house_player_team_game_coin)
    server.route('/GetTeaHousePlayerGameCoin', get_tea_house_player_game_coin)
    server.route('/ProcessBindingProxy', process_binding_proxy)
    server.route('/ProcessCreateTeaHouse', process_create_tea_house)
    # 获取所有冠名赛
    server.route('/GetAllTeaHouse', get_all_tea_house)
    # 获取冠名赛成员
    server.route('/GetTeaHousePlayers', get_tea_house_players)
    # 设置茶楼拉黑分数
    server.route('/SetTeaHouseBlackScore', set_tea_house_black_score)
    # 设置茶楼成员拉黑分数
    server.route('/SetTeaHouseMemberBlackScore', set_tea_house_member_block_score)
    # 设置玩家代理类型
    server.route("/SetPlayerProxyType", set_player_proxy_type)
    # 查看玩家详情
    server.route("/GetPlayerInfo", get_player_info)
    # 修改玩家余额
    server.route("/UpdatePlayerBalance", update_player_balance)
    

def update_player_balance(req, resp):
    INFO_MSG('[interface KBEHttpServer] update_player_balance req.params=%s' % req.params)
    user_id = int(req.params.get('user_id', None))
    count = int(req.params.get('count', None))
    entity = KBEngine.globalData["AccountMgr"].mgr.get_account(user_id)
    if entity:
        entity.balance -= int(count)
        entity.writeToDB()
    else:
        def callback(baseRef, dataBaseID, wasActive):
            if  baseRef:
                baseRef.balance -= int(count)
                baseRef.writeToDB()
        
        KBEngine.createEntityFromDBID("Account", int(userId), callback)
    
    resp.body = 'success'.encode()
    resp.end()
    

def get_player_info(req, resp):
    INFO_MSG('[interface KBEHttpServer] get_player_info req.params=%s' % req.params)
    user_id = int(req.params.get('user_id', None))
    account = KBEngine.globalData["AccountMgr"].mgr.get_account(user_id)
    dic = dict()
    if account:
        dic['Online'] = 1
        dic['roomCard'] = account.roomCard
        dic['frozen'] = account.frozen
    else:
        dic['Online'] = 0
        dic['roomCard'] = 0
        dic['frozen'] = 0
    INFO_MSG(dic)
    str = json.dumps(dic)
    resp.body = str.encode()
    resp.end()

def set_player_proxy_type(req, resp):
    INFO_MSG('[interface KBEHttpServer] modify_proxy_type resp.params=%s' % req.params)
    account_db_id = int(req.params.get('accountDBID', None))
    proxy_type = int(req.params.get('proxyType', None))
    superior_id = int(req.params.get('superior_id', None))
    KBEngine.globalData["AccountMgr"].mgr.set_account_proxy_type(account_db_id, proxy_type,superior_id)
    resp.body = "success".encode()
    resp.end()


def set_tea_house_member_block_score(req, resp):
    """
    解封达到拉黑分数的玩家
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] set_tea_house_member_black_score resp.params=%s' % req.params)
    tea_house_database_id = int(req.params.get('tea_house_database_id', None))
    account_database_id = int(req.params.get('account_database_id', None))
    tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
    tea_house_entity = tea_house_mgr.get_tea_house_with_id(tea_house_database_id)
    if tea_house_entity:
        tea_house_entity.unblock_tea_house_player(account_database_id)
        resp.body = 'success'.encode()
    resp.body = 'fail'.encode()
    resp.end()


def set_tea_house_black_score(req, resp):
    tea_house_database_id = int(req.params.get('tea_house_database_id', None))
    score = int(req.params.get('score', None))
    tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
    if tea_house_database_id in tea_house_mgr.teaHouse_dic.keys():
        tea_house_entity = tea_house_mgr.teaHouse_dic[tea_house_database_id]
        tea_house_entity.set_tea_house_black_score(score)
        resp.body = 'success'.encode()
    resp.body = 'fail'.encode()
    resp.end()


def get_tea_house_players(req, resp):
    INFO_MSG('[interface KBEHttpServer] get_tea_house_players req.params=%s' % req.params)
    tea_house_database_id = int(req.params.get('tea_house_database_id', None))
    tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
    member_list = []
    if tea_house_database_id in tea_house_mgr.teaHouse_dic.keys():
        tea_house_entity = tea_house_mgr.teaHouse_dic[tea_house_database_id]
        member_list = tea_house_entity.get_member_info()
    dic = dict()
    dic["member_list"] = member_list
    INFO_MSG(dic)
    str = json.dumps(dic)
    resp.body = str.encode()
    resp.end()


def get_all_tea_house(req, resp):
    status = int(req.params.get('status', 0))
    account_db_id = int(req.params.get('account_db_id', None))
    INFO_MSG('[interface KBEHttpServer] get_all_tea_house req.params=%s' % req.params)
    tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
    tea_house_list = []
    for k, v in tea_house_mgr.teaHouse_dic.items():
        item = dict()
        item['name'] = v.name
        item['id'] = v.databaseID
        item['teaHouseId'] = v.teaHouseId
        item['creatorDBID'] = v.creatorDBID
        item['createTime'] = v.createTime
        item['freezeScore'] = v.block_score_standard
        item['member_count'] = len(v.memberInfo)
        if status != 1:  # 代理
            if account_db_id == v.creatorDBID:
                tea_house_list.append(item)
        else:
            tea_house_list.append(item)
    dic = dict()
    dic["tea_house_list"] = tea_house_list
    INFO_MSG(dic)
    str = json.dumps(dic)
    resp.body = str.encode()
    resp.end()


def change_Placard(req, resp):
    # flag 区别对Msg的操作，2为删除，1为添加，0为修改
    content = str(req.params.get('content', None))
    content = str(unquote(str(content)))
    title = str(req.params.get('title', None))
    title = str(unquote(str(title)))

    # 网页端传入参数，flag为 1 时执行插入语句，否则执行更新语句
    flag = str(req.params.get('flag', None))
    if flag == '1':
        comds = 'insert into placard (title,content,addtime) values ("%s","%s","%s")' % (
            title, content, str(int(time.time())))
    elif flag == '0':
        comds = 'update placard set title="%s",content="%s" where title="%s"' % (title, content, title)
    elif flag == '2':
        comds = 'delete from msg where user_name="%s"' % (title)
    DEBUG_MSG("推广管理修改公告Placard")
    DEBUG_MSG("This sql comd=====》%s", comds)
    KBEngine.executeRawDatabaseCommand(comds)
    resp.body = 'success'.encode()
    resp.end()


def change_Msg(req, resp):
    # flag 区别对Msg的操作，2为删除，1为添加，0为修改
    user_name = '滚动公告'
    content = str(req.params.get('content', None))
    content = str(unquote(str(content)))
    # 网页端传入参数，flag为 1 时执行插入语句，否则执行更新语句
    flag = str(req.params.get('flag', None))
    DEBUG_MSG("传入的flag:%s" % flag)
    if flag == '1':
        comds = 'insert into msg (user_name,body,dateTime) values ("%s","%s","%s")' % (
            user_name, content, int(time.time()))
    elif flag == '0':
        comds = 'update msg set body="%s" where user_name="%s"' % (content, user_name)
    elif flag == '2':
        comds = 'delete from msg where user_name="%s"' % (user_name)
    DEBUG_MSG("推广管理修改滚动公告Msg")
    DEBUG_MSG("This sql comd=====》%s", comds)
    KBEngine.executeRawDatabaseCommand(comds)
    resp.body = 'success'.encode()
    resp.end()


def change_Url_Address(req, resp):
    type = str(req.params.get('type', None))
    id = str(req.params.get('id', None))
    address = str(req.params.get('address', None))
    description = str(req.params.get('description', None))
    comds = 'UPDATE url_address set address="%s" WHERE id=%s' % (address, id)
    DEBUG_MSG("推广管理修改")
    DEBUG_MSG("This sql comd=====》%s", comds)
    KBEngine.executeRawDatabaseCommand(comds)
    resp.body = 'success'.encode()
    resp.end()


def Del_Serverner(req, resp):
    id = str(req.params.get('id', None))
    # description = str(req.params.get('description', None))
    # local_plan = str(req.params.get('local_plan', None))
    comds = "delete  from wx_server where id=%s" % (id)
    DEBUG_MSG("This sql comd=====》%s", comds)
    KBEngine.executeRawDatabaseCommand(comds)
    resp.body = 'success'.encode()
    resp.end()


def Insert_Serverner(req, resp):
    wx_server = str(req.params.get('wx_server', None))
    description = str(req.params.get('description', None))
    description = str(unquote(str(description)))
    local_plan = str(req.params.get('local_plan', None))
    local_plan = str(unquote(str(local_plan)))
    comds = 'insert into wx_server (wx_server , description, local ) values ("%s" , "%s" , "%s")' % (
        wx_server, description, local_plan)
    DEBUG_MSG("This sql comd=====》%s", comds)
    KBEngine.executeRawDatabaseCommand(comds)
    resp.body = 'success'.encode()
    resp.end()


def Change_Serverner(req, resp):
    id = str(req.params.get('id', None))
    wx_server = str(req.params.get('wx_server', None))
    description = str(req.params.get('description', None))
    description = str(unquote(str(description)))
    local_plan = str(req.params.get('local_plan', None))
    local_plan = str(unquote(str(local_plan)))
    comds = 'update wx_server set wx_server="%s",description="%s",local="%s" where id="%s"' % (
        wx_server, description, local_plan, id)
    DEBUG_MSG("This sql comd=====》%s", comds)
    KBEngine.executeRawDatabaseCommand(comds)
    resp.body = 'success'.encode()
    resp.end()


def redeem_gift(req, resp):
    """
    礼品兑换
    :param req:
    :param resp:
    :return:
    """
    gift_id = int(req.params.get('giftId', None))
    user_id = int(req.params.get('userId', None))
    charge_room_card_item = KBEngine.createEntityLocally("RedeemGift", {})
    charge_room_card_item.create_one_item(user_id, gift_id)
    resp.body = 'success'.encode()
    resp.end()


def proxy_operation(req, resp):
    """
    同意/拒绝代理
    :param req:
    :param resp:
    :return:
    """

    def delete_application_sql():
        """
        删除数据库记录
        :return:
        """
        command = 'DELETE FROM tbl_applicationproxylist where sm_accountDBID=%s' % account_db_id
        KBEngine.executeRawDatabaseCommand(command)

    # 1 同意，0 拒绝
    operation = int(req.params.get('operation', None))
    account_db_id = int(req.params.get('accountDBID', None))
    proxy_type = 10
    if operation == 1:
        KBEngine.globalData["AccountMgr"].mgr.modify_account_proxy_type(account_db_id, proxy_type)
    # 删除申请记录
    delete_application_sql()
    resp.body = 'success'.encode()
    resp.end()


def can_reduce_game_coin_all(req, resp):
    """
    修改所有茶楼是否可以减少比赛分权限
    :param req:
    :param resp:
    :return:
    """
    can_reduce = int(req.params.get('canReduce', None))
    KBEngine.globalData["TeaHouseManager"].mgr.modify_can_reduce_game_coin_all(can_reduce)
    resp.body = 'success'.encode()
    resp.end()


def can_reduce_game_coin(req, resp):
    """
    修改是否可以减少比赛分权限
    :param req:
    :param resp:
    :return:
    """
    can_reduce = int(req.params.get('canReduce', None))
    tea_house_id = int(req.params.get('teaHouseId', None))
    KBEngine.globalData["TeaHouseManager"].mgr.modify_can_reduce_game_coin(tea_house_id, can_reduce)
    resp.body = 'success'.encode()
    resp.end()


def have_exchange_mall(req, resp):
    """
    修改是否具有兑换商城功能
    :param req:
    :param resp:
    :return:
    """
    have_exchange = int(req.params.get('haveExchangeMall', None))
    tea_house_id = int(req.params.get('teaHouseId', None))
    KBEngine.globalData["TeaHouseManager"].mgr.modify_have_exchange_mall(tea_house_id, have_exchange)
    resp.body = 'success'.encode()
    resp.end()


def reload_game_config_json(req, resp):
    """
    重新加载游戏配置
    :param req:
    :param resp:
    :return:
    """
    kbemain.load_game_config()
    resp.body = 'success'.encode()
    resp.end()


def snoring_tea_house(req, resp):
    """
    打烊所有冠名赛
    :param req:
    :param resp:
    :return:
    """
    tea_house_type = req.params.get('teaHouseType', None)
    KBEngine.globalData["TeaHouseManager"].mgr.snoring_all_tea_house(tea_house_type)
    resp.body = 'success'.encode()
    resp.end()


def cancel_snoring_tea_house(req, resp):
    """
    取消打烊所有冠名赛
    :param req:
    :param resp:
    :return:
    """
    tea_house_type = req.params.get('teaHouseType', None)
    KBEngine.globalData["TeaHouseManager"].mgr.cancel_all_tea_house(tea_house_type)
    resp.body = 'success'.encode()
    resp.end()


def snoring_all_tea_house_game(req, resp):
    """
    打烊冠名赛内的某个类型游戏
    :param req:
    :param resp:
    :return:
    """
    room_type = req.params.get('roomType', None)
    tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
    for k, v in tea_house_mgr.teaHouse_dic.items():
        if room_type in v.snoring_games:
            continue
        if v.teaHouseType == 1:
            continue
        v.snoring_games.append(room_type)
    resp.body = 'success'.encode()
    resp.end()


def snoring_all_room(req, resp):
    """
    打烊冠名赛内的某个类型游戏
    :param req:
    :param resp:
    :return:
    """
    snoring_time = int(req.params.get('time', 0))
    cur_time = time.time()
    if abs(cur_time - snoring_time) > 300:
        tmptime = '%s' % cur_time
        resp.body = tmptime.encode()
        resp.end()
        return
    snoring_type = int(req.params.get('type', None))
    snoring_msg = req.params.get('msg', None)
    room_mgr = KBEngine.globalData["RoomManager"].mgr
    if snoring_type == 1:
        room_mgr.snoring_all_room = True
    else:
        room_mgr.snoring_all_room = False
    if snoring_msg:
        room_mgr.snoring_msg = unquote(snoring_msg)
    else:
        room_mgr.snoring_msg = "服务器维护中，大概需要10分钟，请稍等，感谢您的配合！"
    resp.body = 'success'.encode()
    resp.end()


def snoring_tea_house_game(req, resp):
    """
    打烊某个冠名赛的某个类型游戏
    :param req:
    :param resp:
    :return:
    """
    room_type = req.params.get('roomType', None)
    tea_house_id = req.params.get('teaHouseId', None)
    tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
    if tea_house_id in tea_house_mgr.teaHouse_dic.keys():
        tea_house_entity = tea_house_mgr.teaHouse_dic[tea_house_id]
        if room_type not in tea_house_entity.snoring_games:
            tea_house_entity.snoring_games.append(room_type)
    resp.body = 'success'.encode()
    resp.end()


def cancel_snoring_tea_house_game(req, resp):
    """
    取消打烊某个冠名赛的某个类型游戏
    :param req:
    :param resp:
    :return:
    """
    room_type = req.params.get('roomType', None)
    tea_house_id = req.params.get('teaHouseId', None)
    tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
    if tea_house_id in tea_house_mgr.teaHouse_dic.keys():
        tea_house_entity = tea_house_mgr.teaHouse_dic[tea_house_id]
        if room_type in tea_house_entity.snoring_games:
            tea_house_entity.snoring_games.remove(room_type)
    resp.body = 'success'.encode()
    resp.end()


def cancel_all_snoring_tea_house_game(req, resp):
    """
    取消打烊冠名赛内的某个类型游戏
    :param req:
    :param resp:
    :return:
    """
    room_type = req.params.get('roomType', None)
    tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
    for k, v in tea_house_mgr.teaHouse_dic.items():
        if room_type in v.snoring_games:
            v.snoring_games.remove(room_type)
    resp.body = 'success'.encode()
    resp.end()


def change_account_add_on_state(req, resp):
    """
    修改玩家外挂状态
    :param req:
    :param resp:
    :return:
    """
    userId = req.params.get('userId', None)
    state = req.params.get('state', None)

    def onCreateAccountEntityCB(baseRef, dataBaseID, wasActive):
        INFO_MSG('[KBEHttpServer] changeAccountAddOnState resp.params=%s' % req.params)
        if baseRef is not None:
            baseRef.addOn = int(state)
            if not wasActive:
                baseRef.destroy()

    KBEngine.createEntityFromDBID("Account", int(userId), onCreateAccountEntityCB)
    resp.body = 'success'.encode()
    resp.end()


def disband_room(req, resp):
    """
    后台解散房间
    :param req:
    :param resp:
    :return:
    """
    # 房间号
    _room_id = int(req.params.get('roomId', None))
    # 如果是 -1 则不是茶楼房间
    _tea_house_id = int(req.params.get('teaHouseId', None))
    INFO_MSG('[interface KBEHttpServer] disband_room resp.params=%s' % req.params)
    if _tea_house_id > 0:
        tea_house_entity = get_tea_house_with_id(_tea_house_id)
        if tea_house_entity:
            tea_house_entity.disband_room(_room_id, _tea_house_id)
    else:
        room_mgr = get_room_manager()
        if room_mgr:
            rooms = room_mgr.rooms
            for _type, value in rooms.items():
                if value.roominfos:
                    for _room_type, value2 in value.roominfos.items():
                        for _room_id2, room_entity in value2.items():
                            if _room_id2 == _room_id:
                                if room_entity.cell:
                                    room_entity.cell.baseToCell({"func": "disbandTeaHouseRoomByCreator"})

    resp.body = 'success'.encode()
    resp.end()


def reCharge(req, resp):
    """
    后台给玩家充值积分
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] reCharge resp.params=%s' % req.params)
    userId = req.params.get('userId', None)
    number = req.params.get('number', None)

    def onCreateAccountEntityCB(baseRef, dataBaseID, wasActive):
        if baseRef is not None:
            DEBUG_MSG("baseRef id=%s, gold=%s" % (baseRef.id, baseRef.gold))
            baseRef.gold += int(number)
            if baseRef.cell is not None:
                baseRef.cell.baseToCell({"func": "retAccountMutableInfo", "dic": {"gold": baseRef.gold}})
            baseRef.ret_gold()
            baseRef.writeToDB()
            if not wasActive:
                baseRef.destroy()

    KBEngine.createEntityFromDBID("Account", int(userId), onCreateAccountEntityCB)
    resp.body = 'success'.encode()
    resp.end()


def modify_room_card(req, resp):
    """
    修改玩家钻石数量
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] modify_room_card resp.params=%s' % req.params)
    user_id = int(req.params.get('userId', None))
    number = float(req.params.get('modifyRoomCardCount', None))
    operator_id = int(req.params.get('operatorDBID', None))
    if operator_id != -99:
        def on_create_operator_cb(operator_ref, dataBaseID, operator_active):
            INFO_MSG('[interface KBEHttpServer] modify_room_card [operator_ref]', operator_ref)
            if operator_ref is not None:

                def on_create_entity_cb(baseRef, dataBaseID, wasActive):
                    INFO_MSG('[interface KBEHttpServer] modify_room_card [baseRef]', baseRef)
                    if baseRef is not None:
                        if number > operator_ref.roomCard:
                            return
                        operator_ref.roomCard -= round(float(number), 1)
                        INFO_MSG('[interface KBEHttpServer] modify_room_card [operator_ref.roomCard]', operator_ref.roomCard)
                        INFO_MSG('[interface KBEHttpServer] modify_room_card [baseRef.roomCard]', baseRef.roomCard)
                        baseRef.roomCard += round(float(number), 1)
                        if baseRef.roomCard < 0:
                            baseRef.roomCard = round(float(0), 1)
                        if operator_ref.roomCard < 0:
                            operator_ref.roomCard = round(float(0), 1)

                        baseRef.writeToDB()
                        operator_ref.writeToDB()

                        if wasActive:
                            baseRef.retRoomCard()
                        if operator_active:
                            operator_ref.retRoomCard()

                        # 生成充值记录
                        charge_room_card_item = KBEngine.createEntityLocally("RoomCardChargeHistory", {})
                        charge_room_card_item.create_one_item(baseRef, operator_ref, number, baseRef.roomCard)

                KBEngine.createEntityFromDBID("Account", int(user_id), on_create_entity_cb)

        KBEngine.createEntityFromDBID("Account", int(operator_id), on_create_operator_cb)
    else:
        def on_create_entity_cb(baseRef, dataBaseID, wasActive):
            if baseRef is not None:
                count = number
                # 绑定代理充值额外赠送
                if baseRef.belong_to != 0:
                    # count *= (1 + float(Const.GameConfigJson.config_json['Hall']['bindingProxyRechargeOffer']))
                    pass
                baseRef.roomCard += count
                if baseRef.roomCard < 0:
                    baseRef.roomCard = 0

                baseRef.writeToDB()

                if wasActive:
                    baseRef.retRoomCard()

                # 生成充值记录
                charge_room_card_item = KBEngine.createEntityLocally("RoomCardChargeHistory", {})
                charge_room_card_item.create_one_item_with_none_operator(baseRef, count, baseRef.roomCard)

        KBEngine.createEntityFromDBID("Account", int(user_id), on_create_entity_cb)

    resp.body = 'modify_room_card success'.encode()
    resp.end()


def modify_goldIngot(req, resp):
    """
    修改玩家元宝数量
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] modify_goldIngot resp.params=%s' % req.params)
    user_id = int(req.params.get('userId', None))
    number = float(req.params.get('modifyGoldIngotCount', None))
    operator_id = int(req.params.get('operatorDBID', None))
    if operator_id != -99:
        def on_create_operator_cb(operator_ref, dataBaseID, operator_active):
            if operator_ref is not None:

                def on_create_entity_cb(baseRef, dataBaseID, wasActive):
                    if baseRef is not None:
                        if number > operator_ref.goldIngot:
                            return
                        operator_ref.goldIngot -= int(number)
                        baseRef.goldIngot += int(number)
                        if baseRef.goldIngot < 0:
                            baseRef.goldIngot = 0
                        if operator_ref.goldIngot < 0:
                            operator_ref.goldIngot = 0

                        baseRef.writeToDB()
                        operator_ref.writeToDB()

                        if wasActive:
                            baseRef.retGoldIngot()
                        if operator_active:
                            operator_ref.retGoldIngot()

                        # 生成充值记录
                        charge_room_card_item = KBEngine.createEntityLocally("RoomCardChargeHistory", {})
                        charge_room_card_item.create_one_item(baseRef, operator_ref, number, baseRef.goldIngot)

                KBEngine.createEntityFromDBID("Account", int(user_id), on_create_entity_cb)

        KBEngine.createEntityFromDBID("Account", int(operator_id), on_create_operator_cb)
    else:
        def on_create_entity_cb(baseRef, dataBaseID, wasActive):
            if baseRef is not None:
                count = number
                # 绑定代理充值额外赠送
                if baseRef.belong_to != 0:
                    # count *= (1 + float(Const.GameConfigJson.config_json['Hall']['bindingProxyRechargeOffer']))
                    pass
                baseRef.goldIngot += count
                if baseRef.goldIngot < 0:
                    baseRef.goldIngot = 0

                baseRef.writeToDB()

                if wasActive:
                    baseRef.retGoldIngot()

                # 生成充值记录
                charge_room_card_item = KBEngine.createEntityLocally("RoomCardChargeHistory", {})
                charge_room_card_item.create_one_item_with_none_operator(baseRef, count, baseRef.goldIngot)

        KBEngine.createEntityFromDBID("Account", int(user_id), on_create_entity_cb)

    resp.body = 'modify_goldIngot success'.encode()
    resp.end()


def modify_scroll_announcement(req, resp):
    """
    修改滚动公告
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] modify_scroll_announcement resp.params=%s' % req.params)

    def on_success(announcement):
        KBEngine.globalData["AccountMgr"].mgr.call_all_client("queryScrollAnnouncement", [{"content": announcement}])

    content = req.params.get('content', None)
    content = str(unquote(str(content)))
    DEBUG_MSG("content :%s" % content)
    DBCommand.modify_scroll_announcement(on_success, content)
    resp.body = 'success'.encode()
    resp.end()


def modify_game_coin(req, resp):
    """
    修改玩家比赛分
    :param req:
    :param resp:
    :return:
    """

    def on_success():
        # resp.body = '{"code":200}'.encode()
        # resp.end()
        pass

    def on_fail():
        # resp.body = '{"code":400}'.encode()
        # resp.end()
        pass

    player_db_id = int(req.params.get('userId', None))
    tea_house_id = int(req.params.get('teaHouseId', None))
    number = int(req.params.get('modifyGameCoinCount', None))
    DEBUG_MSG('player_id:%s,teaHouseId:%s,number:%s' % (player_db_id, tea_house_id, number))
    try:
        get_tea_house_with_id(tea_house_id).modify_game_coin_to_public(player_db_id, number,
                                                                       on_success=on_success,
                                                                       on_fail=on_fail)
    except AttributeError as e:
        ERROR_MSG("KBEHttpServer::modify_game_coin %s" % e)

    resp.body = '{"code":200}'.encode()
    resp.end()


# 修改创建冠名赛需要的权限
def modify_create_tea_house_permission(req, resp):  # 1 需要，0 不需要
    need_permission = int(req.params.get('needPermission', None))
    KBEngine.globalData["TeaHouseManager"].mgr.save_tea_house_permission_to_db(need_permission)
    resp.body = 'success'.encode()
    resp.end()


def modify_player_frozen_state(req, resp):
    """
    修改玩家冻结状态
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] modify_player_frozen_state resp.params=%s' % req.params)
    account_db_id = int(req.params.get('accountDBID', None))
    frozen_state = int(req.params.get('frozenState', None))
    KBEngine.globalData["AccountMgr"].mgr.modify_account_frozen_state(account_db_id, frozen_state)
    resp.body = "success".encode()
    resp.end()


def disband_tea_house(req, resp):
    """
    解散冠名赛
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] disband_tea_house resp.params=%s' % req.params)
    tea_house_id = int(req.params.get('teaHouseId', None))
    KBEngine.globalData["TeaHouseManager"].mgr.destroy_tea_house_with_id(tea_house_id)
    resp.body = "success".encode()
    resp.end()


def modify_proxy_type(req, resp):
    """
    修改玩家代理类型
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] modify_proxy_type resp.params=%s' % req.params)
    account_db_id = int(req.params.get('accountDBID', None))
    proxy_type = int(req.params.get('proxyType', None))
    invite_code = -1
    try:
        invite_code = int(req.params.get('inviteCode', None))
    except Exception as e:
        ERROR_MSG('KbeHttpServer modify_proxy_type %s' % e)
    KBEngine.globalData["AccountMgr"].mgr.modify_account_proxy_type(account_db_id, proxy_type, invite_code=invite_code)
    resp.body = "success".encode()
    resp.end()


def unbind_proxy(req, resp):
    """
    解绑玩家代理
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] unbind_proxy resp.params=%s' % req.params)
    account_db_id = int(req.params.get('userid', None))
    KBEngine.globalData["AccountMgr"].mgr.unbind_proxy(account_db_id)
    resp.body = "success".encode()
    resp.end()
    
def rebinding_proxy(req, resp):
    """
    重新绑定玩家代理
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] unbind_proxy resp.params=%s' % req.params)
    account_db_id = int(req.params.get('userid', None))
    proxy_id = int(req.params.get('proxy_id', None))
    KBEngine.globalData["AccountMgr"].mgr.rebinding_proxy(account_db_id, proxy_id)
    resp.body = "success".encode()
    resp.end()
    


def withdraw_cash(req, resp):
    """
    提现返回
    :param req:
    :param resp:
    :return:
    """
    INFO_MSG('[interface KBEHttpServer] withdrawCash resp.params=$s' % req.params)
    id = req.params.get('id', None)
    count = req.params.get('count', None)
    success = req.params.get('success', None)
    if int(success) == 1:
        # 提现成功，不做操作
        ''
    elif int(success) == 0:
        # 提现失败，返还积分
        ''


def notification(req, resp):
    """
    系统公告
    :param req:
    :param resp:
    :return:
    """

    def callback(result, rows, insertid, error):
        content = str(result[0][0], 'utf-8')
        KBEngine.globalData["AccountMgr"].mgr.systemNotification("系统公告", content)

    msg = req.params["msg"]
    _command = "SELECT body FROM msg WHERE id = %s;" % msg
    KBEngine.executeRawDatabaseCommand(_command, callback)
    resp.body = 'success'.encode()
    resp.end()


def ratioChange(req, resp):
    """
    当抽成比例变化的时候，调用
    :param req:
    :param resp:
    :return:
    """
    DBCommand.checkOutRatioFromDB(None)
    resp.body = 'success'.encode()
    resp.end()


def challenge_prize(req, resp):
    INFO_MSG('[interface KBEHttpServer] challenge_prize req.params=%s' % req.params)
    try:
        user_id = int(req.params.get('user', None))
        prize_code = int(req.params.get('prizeCode', None))
    except Exception as e:
        ERROR_MSG('KbeHttpServer challenge_prize %s' % e)
        resp.send_error(400)
        return

    account_entity = KBEngine.globalData["AccountMgr"].mgr.get_account(user_id)
    if account_entity:
        my_prize = account_entity.get_challenge_prize(prize_code)
    else:
        resp.send_error(500)
        return
    resp.body = my_prize.encode()
    resp.end()


def redeem_prize(req, resp):
    INFO_MSG('[interface KBEHttpServer] redeem_prize req.params=%s' % req.params)
    try:
        user_id = int(req.params.get('user', None))
        prize_code = int(req.params.get('prizeCode', None))
        prize_type = int(req.params.get('prizeType', None))
        prize_num = int(req.params.get('prizeNum', None))
    except Exception as e:
        ERROR_MSG('KbeHttpServer redeem_prize %s' % e)
        resp.send_error(400)
        return

    account_entity = KBEngine.globalData["AccountMgr"].mgr.get_account(user_id)
    if account_entity:
        remain_prize = account_entity.redeem_prize(prize_code, prize_type, prize_num)
        if not remain_prize[0]:
            resp.send_error(400)
            return
    else:
        resp.send_error(500)
        return

    DEBUG_MSG("redeem_prize AAA")
    account_entity.writeToDB()
    DEBUG_MSG("redeem_prize BBB")
    account_entity.retPrize(prize_type)
    DEBUG_MSG("redeem_prize ccc")

    resp.body = ('{"remain": %s}' % remain_prize[1]).encode()
    DEBUG_MSG(remain_prize)
    resp.end()


def change_game_coin_switch(req, resp):
    INFO_MSG('[interface KBEHttpServer] change_game_coin_switch req.params=%s' % req.params)
    try:
        switch = int(req.params.get('switch', None))
    except Exception as e:
        ERROR_MSG('KbeHttpServer change_game_coin_switch %s' % e)
        resp.send_error(400)
        return

    Const.ServerGameConfigJson.config_json['TeaHouse']["GameCoinSwitch"] = switch
    kbemain.save_game_config("TeaHouse")

    resp.body = 'success'.encode()
    resp.end()


def allow_change_game_coin_switch(req, resp):
    """
    是否允许开关茶楼的比赛分按钮
    """
    INFO_MSG('[interface KBEHttpServer] allow_change_game_coin_switch req.params=%s' % req.params)
    try:
        switch = int(req.params.get('switch', 0))
        tea_house_id = int(req.params.get('teahouse', 0))
    except Exception as e:
        ERROR_MSG('KbeHttpServer change_game_coin_switch %s' % e)
        resp.send_error(400)
        return

    tea_house_entity = KBEngine.globalData["TeaHouseManager"].mgr.get_tea_house_with_id(tea_house_id)
    if tea_house_entity:
        tea_house_entity.allowChangeGameCoinSwitch = 1 if switch == 1 else 0

    resp.body = 'success'.encode()
    resp.end()


def get_tea_house_player_team_game_coin(req, resp):
    tea_house_id = int(req.params.get('teaHouseId', 0))
    account_dbid = str(req.params.get('accountDbid', 0))
    str_list = account_dbid.split(',')
    int_list = []
    for i in str_list:
        int_list.append(int(i))
    dict = KBEngine.globalData["TeaHouseManager"].mgr.get_tea_house_player_team_game_coin(tea_house_id, int_list)
    resp.body = json.dumps(dict).encode()
    resp.end()


def get_tea_house_player_game_coin(req, resp):
    tea_house_id = int(req.params.get('teaHouseId', 0))
    account_dbid = str(req.params.get('accountDbid', 0))
    str_list = account_dbid.split(',')
    int_list = []
    for i in str_list:
        int_list.append(int(i))
    l = KBEngine.globalData["TeaHouseManager"].mgr.get_tea_house_player_game_coin(tea_house_id, int_list)
    resp.body = json.dumps(l).encode()
    resp.end()


def process_binding_proxy(req, resp):
    """
    处理绑定代理接口
    """
    result = int(req.params.get('result', 0))
    down = int(req.params.get('down', 0))
    up = int(req.params.get('up', 0))
    KBEngine.globalData["AccountMgr"].mgr.process_binding_proxy(up, down, result)
    resp.body = 'success'.encode()
    resp.end()


def process_create_tea_house(req, resp):
    """
    处理创建茶楼接口
    """
    result = int(req.params.get('result', 0))
    tea_house_id = int(req.params.get('teaHouseId', 0))
    KBEngine.globalData["TeaHouseManager"].mgr.process_create_tea_house(tea_house_id, result)
    resp.body = 'success'.encode()
    resp.end()


def change_add_team_switch(req, resp):
    INFO_MSG('[interface KBEHttpServer] change_add_team_switch req.params=%s' % req.params)
    try:
        switch = int(req.params.get('switch', None))
    except Exception as e:
        ERROR_MSG('KbeHttpServer change_add_team_switch %s' % e)
        resp.send_error(400)
        return

    Const.ServerGameConfigJson.config_json['TeaHouse']["AddTeamSwitch"] = switch
    kbemain.save_game_config("TeaHouse")

    resp.body = 'success'.encode()
    resp.end()


def change_partner_switch(req, resp):
    INFO_MSG('[interface KBEHttpServer] change_team_switch req.params=%s' % req.params)
    try:
        userId = int(req.params.get('userid', None))
        switch = int(req.params.get('switch', None))
    except Exception as e:
        ERROR_MSG('KbeHttpServer change_team_switch %s' % e)
        resp.send_error(400)
        return

    def onCreateAccountEntityCB(baseRef, dataBaseID, wasActive):
        if baseRef:
            baseRef.partnerSwitch = True if switch == 1 else False
            baseRef.writeToDB()
            if not wasActive:
                baseRef.destroy()
            else:
                baseRef.call_client_func('GetTeaHosuePartnerSwitch',
                                         {'partnerSwitch': True if baseRef.partnerSwitch == 1 else False})

    KBEngine.createEntityFromDBID("Account", int(userId), onCreateAccountEntityCB)

    resp.body = 'success'.encode()
    resp.end()


def get_game_config(req, resp):
    INFO_MSG('[interface KBEHttpServer] get_game_config req.params=%s' % req.params)

    dic = dict()
    dic['createTeaHousePermission'] = KBEngine.globalData["TeaHouseManager"].mgr.need_permission
    dic['gamecoinswitch'] = Const.ServerGameConfigJson.config_json['TeaHouse']["GameCoinSwitch"]
    dic['addteamswitch'] = Const.ServerGameConfigJson.config_json['TeaHouse']["AddTeamSwitch"]

    str = json.dumps(dic)
    resp.body = str.encode()
    resp.end()
