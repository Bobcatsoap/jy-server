# coding:utf-8
import datetime
import json
import pickle
import time

from KBEDebug import *
import hashlib
import Functor
# sys.path.append(r'D:\\KBE\\kbengine-2.3.5\\server_assets_BICC\\scripts\\base')
# import Const
import DateUtil
import random
import Const

# 上一次抽成时间（年月日）
lastCutTime = DateUtil.get_str_now_timestamp_ymd(time.time())


class GameConfig:
    # 斗牛抽成比例
    DNRatio = 1
    # 扎金花抽成比例
    ZJHRatio = 1
    # 斗地主抽成比例
    DDZRatio = 1
    # BICC币与钻石的兑换比例
    SubscriptionRatio = 1


def save_tea_house_game_coin_info(write_time, tea_house_id, game_coin_info):
    def call_back(result, rows, insertid, error):
        pass

    data = json.dumps(game_coin_info)
    insert_sql = "INSERT INTO tea_house_day_game_coin (tea_house_id,create_time,game_coin) " \
                 "VALUES (%s,FROM_UNIXTIME(%s,'%%Y-%%m-%%d'),'%s')" \
                 % (tea_house_id, write_time, data)
    KBEngine.executeRawDatabaseCommand(insert_sql, call_back)


def checkAccountName(_account_name, _call_back=None):
    """
    :param _account_name:
    :param _call_back:
    :return:
    """

    def _fun(_call_back, result, rows, insertid, error):
        # DEBUG_MSG("[DBCommand]--------->checkAccountNameCallback result %s rows %s insertid %s error %s" % (
        #     str(result),
        #     str(rows),
        #     str(insertid),
        #     str(error)))
        _count = int(result[0][0])
        if _call_back is not None:
            _call_back(_count)

    _coomand = "select count(*) from kbe.kbe_accountinfos where accountName='%s';" % _account_name
    KBEngine.executeRawDatabaseCommand(_coomand, Functor.Functor(_fun, _call_back))


def resetAccountCreateRooms():
    """
    玩家未到期房间清空
    :return:
    """

    def callback(result, rows, insertid, error):
        DEBUG_MSG("resetAccountCreateRooms------> result %s" % result)

    _command = "UPDATE tbl_account SET sm_createRooms = NULL"
    KBEngine.executeRawDatabaseCommand(_command, callback)


# 重置账户代开房间信息
def resetAccountCreateSubstituteRooms():
    """
    玩家未到期房间清空
    :return:
    """

    def callback(result, rows, insertid, error):
        DEBUG_MSG("resetAccountCreateSubstituteRooms------> result %s" % result)

    _command = "UPDATE tbl_account SET sm_substituteRooms = NULL"
    KBEngine.executeRawDatabaseCommand(_command, callback)


def reset_account_bless_count():
    """
    重置祈福次数
    :return:
    """

    def callback(result, rows, insertid, error):
        DEBUG_MSG("reset_account_bless_count------> result %s" % result)

    _command = "UPDATE tbl_account SET sm_blessCountToday = 0"
    KBEngine.executeRawDatabaseCommand(_command, callback)


def writeFeedbackToDB(accountDBID, content, contactway, cb):
    """
    玩家反馈
    :param content:
    :param contactway:
    :return:
    """

    def callback(result, rows, insertid, error):
        if cb:
            cb(result, rows, insertid, error)

    _command = "INSERT INTO feedback (user_id, body, tel, state, add_time) VALUES (%s, '%s', '%s', %s, '%s');" % (
        accountDBID, content, contactway, 0, int(time.time()))
    KBEngine.executeRawDatabaseCommand(_command, callback)


def setAccountPassword(accountName, newPassword, callback=None):
    """
    重设密码
    :param accountName: 账户名
    :param newPassword: 新密码
    :param callback: 回调
    :return:
    """

    def _fun(_call_back, result, rows, insertid, error):
        if callback is not None:
            callback(error)

    _md = hashlib.md5(str(newPassword).encode("utf-8")).hexdigest()
    _coomand = "UPDATE kbe.kbe_accountinfos SET 'password' = '%s' WHERE `accountName` = '%s';" % (_md, str(accountName))
    KBEngine.executeRawDatabaseCommand(_coomand, Functor.Functor(_fun, callback))


def checkOutCustomerService(callback, location):
    """
    检出客服列表
    :param callback:
    :return:
    """

    def func(result, rows, insertid, error):
        if callback:
            callback(result)

    _coomand = "select * from wx_server where local='total' or local = '%s'" % location
    KBEngine.executeRawDatabaseCommand(_coomand, func)


def check_out_url_address(callback, url_type=None):
    """
    从数据库检出指定类型的url，默认全部
    :param callback:
    :param url_type:
    :return:
    """

    def func(result, rows, insertid, error):
        if callback:
            callback(result)

    if url_type:
        command = "select * from url_address where type = '%s'" % url_type
    else:
        command = "select * from url_address"
    KBEngine.executeRawDatabaseCommand(command, func)


def checkOutRatioFromDB(_call_back):
    """
    从数据库检出钻石与金币的兑换比例
    :return:
    """

    def func(call_back, result, rows, insertid, error):
        if result is not None:
            if len(result[0]) != 0:
                GameConfig.DNRatio = float(result[0][0])
                GameConfig.ZJHRatio = float(result[0][1])
                GameConfig.DDZRatio = float(result[0][2])
                GameConfig.SubscriptionRatio = int(result[0][3])
                if call_back is not None:
                    call_back()

    _spl_commond = "select niu_draw,zha_draw,dou_draw,room_draw from kbe_bicc.draw_config where id=1;"
    KBEngine.executeRawDatabaseCommand(_spl_commond, Functor.Functor(func, _call_back))


def check_out_game_coin_charge_history(account_db_id, tea_house_id, start_time=0, on_success=None):
    sql_command = "select * FROM tbl_gamecoinchargehistory WHERE sm_modifyTime>=%s and sm_teaHouseId=%s and (sm_accountDBID=%s or sm_operationAccountDBID=%s) order by sm_modifyTime desc LIMIT 300" % (
        start_time, tea_house_id, account_db_id, account_db_id)

    def callback(result, rows, insertid, error):
        if result and len(result) != 0:
            charge_info = []
            for row in result:
                item_info = {"modifyTime": int(row[3]), "accountDBID": int(row[4]), "operationDBID": int(row[5]),
                             "accountName": str(row[6], 'utf-8'), "operationName": str(row[7], 'utf-8'),
                             "modifyCount": int(row[11]), "modifiedGameCoin": int(row[12])}
                charge_info.append(item_info)
            if on_success:
                on_success(charge_info)
        else:
            if on_success:
                on_success([])

    KBEngine.executeRawDatabaseCommand(sql_command, callback)

def check_out_get_player_battle_score(account_db_id, tea_house_id, on_success=None):
    """
    E查询战绩记录
    """
    sql_command = "select * from player_battle_score WHERE teaHouseId=%s AND playerId=%s order by settleTime desc" % (tea_house_id, account_db_id)
    def callback(result, rows, insertid, error):
        if result and len(result) != 0:
            charge_info = []
            for row in result:
                room_type = str(row[3], 'utf-8')
                item_info = {"roomId": int(row[1]), "accountDBID": int(row[2]), "typeName": Const.get_name_by_type(room_type),
                             "totalGoldChange": int(row[4]),  # 比赛币
                             "BringInGold": int(row[9]),  # 带入金币
                             "SurPlusGold": int(row[10]), # 剩余金币
                             "accountName": str(row[11], "utf-8"), # 玩家名称
                             "settleTime": int(row[12])# 结算时间
                             }
                charge_info.append(item_info)
            if on_success:
                on_success(charge_info)
        else:
            if on_success:
                on_success([])

    KBEngine.executeRawDatabaseCommand(sql_command, callback)

def checkOutCornFromDBByUid(uid, _call_back):
    """
    从数据库读取并刷新内存中的玩家的BICC币数量
    :param uid:
    :return:
    """

    def func(result, rows, insertid, error):
        if result is not None and len(result) != 0:
            if len(result[0]) != 0:
                _call_back(int(float(result[0][0])))

    _spl_commond = "select bicc from kbe_bicc.wallet WHERE uid=%s;" % uid
    KBEngine.executeRawDatabaseCommand(_spl_commond, func)


def checkOutPlacard(_call_back):
    """
    从数据库检出公告
    :param _call_back:
    :return:
    """

    def func(result, rows, insertid, error):
        if result is not None and len(result) != 0:
            _call_back(result)

    _spl_commond = "select * from placard;"
    KBEngine.executeRawDatabaseCommand(_spl_commond, func)


def checkOutScrollAnnouncement(call_back):
    """
    检出滚动公告
    :param call_back:
    :return:
    """

    def func(result, rows, insertid, error):
        if result is not None and len(result) != 0:
            call_back(result)

    _spl_command = "select * from msg;"
    KBEngine.executeRawDatabaseCommand(_spl_command, func)


def modify_scroll_announcement(call_back, content):
    def func(result, rows, insertid, error):
        call_back(content)

    sql_command = "update msg set body='%s'" % content
    KBEngine.executeRawDatabaseCommand(sql_command, func)

def modify_total_commssion(account_db_id, superior, teaHouseId, addtime, count, performanceDetail):
    """
    修改佣金总数
    """
    def on_query_over(result, rows, insertid, error):
        if result is not None and len(result) != 0:
            DEBUG_MSG('modify_total_commssion:-------------')
            DEBUG_MSG(result)
            update_count = int(result[0][0]) + count
            update_double_count = float(result[0][1]) + performanceDetail
            # 如果有值修改佣金数量
            sql_command = "update commssion_total set addtime=%s, count=%s,  performanceDetail= %s where superior=%s" % (addtime, update_count, update_double_count)
            DEBUG_MSG('modify_total_commssion update_sql:%s' % sql_command)
            KBEngine.executeRawDatabaseCommand(sql_command, None)
        else:
            sql_command = "insert into commssion_total (accountDBID,superior,teaHouseId, addtime,count,performanceDetail) VALUES (%s,%s,%s,'%s','%s', %s)" % (
                account_db_id, superior, teaHouseId, addtime, count, performanceDetail)
            DEBUG_MSG('modify_total_commssion insert_sql:%s' % sql_command)
            KBEngine.executeRawDatabaseCommand(sql_command, None)

    sql_command = "select count, performanceDetail from commssion_total where superior=%s" % superior
    DEBUG_MSG('modify_total_commssion select_sql:%s' % sql_command)
    KBEngine.executeRawDatabaseCommand(sql_command, on_query_over)

def modify_room_card_to_db(account_db_id, modify_count, date_time, account_name, consume_type):
    """
    修改玩家钻石数量
    :param consume_type: 消耗类型
    :param account_name:
    :param account_db_id:
    :param modify_count:
    :param date_time:
    :return:
    """

    def on_query_over(result, rows, insertid, error):
        if result is not None and len(result) != 0:
            # 如果有值修改钻石数量
            sql_command = "update room_card_statistics set room_card_count=room_card_count+%s where date_time=%s and account_db_id=%s and consume_type='%s'" % (
                modify_count, date_time, account_db_id, consume_type)
            KBEngine.executeRawDatabaseCommand(sql_command, None)
        else:
            sql_command = "insert into room_card_statistics (account_db_id,room_card_count,date_time,account_name,consume_type) VALUES (%s,%s,%s,'%s','%s')" % (
                account_db_id, modify_count, date_time, account_name, consume_type)
            KBEngine.executeRawDatabaseCommand(sql_command, None)

    sql_command = "select * from room_card_statistics where date_time=%s and account_db_id=%s and consume_type='%s'" % (
        date_time, account_db_id, consume_type)
    KBEngine.executeRawDatabaseCommand(sql_command, on_query_over)


def modify_room_count_to_db(account_db_id, account_name, modify_count, date_time, level=0):
    def on_query_over(result, rows, insertid, error):
        if result is not None and len(result) != 0:
            # 如果有值修改房间数量
            sql_command = "update room_statistics set room_count=room_count+%s where date_time=%s and account_db_id=%s and room_level=%s" % (
                modify_count, date_time, account_db_id, level)
            DEBUG_MSG('modify_room_count_to_db sql:%s' % sql_command)
            KBEngine.executeRawDatabaseCommand(sql_command, None)
        else:
            sql_command = "insert into room_statistics (account_db_id,account_name,room_count,date_time, room_level) VALUES (%s,'%s',%s,%s,%s)" % (
                account_db_id, account_name, modify_count, date_time, level)
            DEBUG_MSG('modify_room_count_to_db sql:%s' % sql_command)
            KBEngine.executeRawDatabaseCommand(sql_command, None)

    sql_command = "select * from room_statistics where date_time=%s and account_db_id=%s and room_level=%s" % (
        date_time, account_db_id, level)
    KBEngine.executeRawDatabaseCommand(sql_command, on_query_over)


def checkOutNameByUID(uid, _call_back):
    """
    查找玩家的昵称
    :param uid:
    :param _call_back:
    :return:
    """

    def func(result, rows, insertid, error):
        if result is not None and len(result) != 0:
            if len(result[0]) != 0:
                _call_back(str(result[0][0], encoding="utf-8"))

    _spl_commond = "select user_name from kbe_bicc.user WHERE user_id=%s;" % uid
    KBEngine.executeRawDatabaseCommand(_spl_commond, func)


def sync_gold_to_bicc(goldChange, uid):
    """
    当kbe中玩家的bicc币变化的时候，同步到bicc数据库
    :param goldChange: 金币变化值
    :param uid: 玩家userid
    :return:
    """
    _coomand = "UPDATE kbe_bicc.wallet SET bicc = bicc + '%s' WHERE uid = '%s';" % (goldChange, uid)
    KBEngine.executeRawDatabaseCommand(_coomand)


def checkOutExChangeRate(_call_back):
    """
    查询当前BICC币的币值(兑换比例)
    :return:
    """

    def func(call_back, result, rows, insertid, error):
        if result is not None and len(result) != 0:
            if len(result[0]) != 0:
                call_back(float(result[0][0]))

    _spl_commond = "select price from kbe_bicc.bicc_price WHERE id=1000;"
    KBEngine.executeRawDatabaseCommand(_spl_commond, Functor.Functor(func, _call_back))


def upDateCut(value, gameType):
    """
    刷新当日平台抽成
    :param value:
    :return:
    """
    _ratio = 0
    if gameType == "RoomType1":
        _ratio = GameConfig.ZJHRatio
    elif gameType == "RoomType4":
        _ratio = GameConfig.DNRatio
    _commond1 = "INSERT INTO fund VALUES(0,%s,%s);" % (
        DateUtil.get_str_now_timestamp_ymd(time.time()), round(value * _ratio, 2))

    def func(result, rows, insertid, error):
        if len(result) == 0:
            KBEngine.executeRawDatabaseCommand(_commond1)
        else:
            _date = int(result[0][0])
            _commond2 = "UPDATE kbe_bicc.platFormCut SET total_cut += %s WHERE 'date' = %s;" % (
                round(value * _ratio, 2), _date)
            KBEngine.executeRawDatabaseCommand(_commond2)

    _commond = "select 'date' from tbl_Account order by id DESC limit 1;"
    KBEngine.executeRawDatabaseCommand(_commond, func)


def check_out_account_by_db_id(db_id, _call_back=None):
    def _fun(_call_back, result, rows, insertid, error):
        if _call_back is not None:
            _call_back(result)

    _command = "select * from tbl_Account where sm_userId in (%s);" % db_id
    KBEngine.executeRawDatabaseCommand(_command, Functor.Functor(_fun, _call_back))


def update_invite_code_relations(user_id, unionid):
    """
    更新邀请码关系表
    :return:
    """

    def _fun(result, rows, insertid, error):
        if len(result) == 0:
            # 插入一条数据
            _command2 = "INSERT INTO invite_code_relations ( user_id, unionid ) VALUES( %s, '%s' );" % (
                user_id, unionid)
            KBEngine.executeRawDatabaseCommand(_command2, None)
        else:
            # 修改当前数据
            _command1 = "UPDATE invite_code_relations SET user_id='%s' WHERE unionid = %s;" % (user_id, unionid)
            KBEngine.executeRawDatabaseCommand(_command1, None)

    _command = "SELECT * FROM `invite_code_relations` WHERE `unionid`='%s'" % unionid
    DEBUG_MSG(_command)
    KBEngine.executeRawDatabaseCommand(_command, _fun)


def exec_normal_sql(sql):
    """执行SQL查询"""

    def _fun(result, rows, insertid, error):
        if not result:
            DEBUG_MSG("exec_normal_sql %s %s" % (error, sql))

    KBEngine.executeRawDatabaseCommand(sql, _fun)


def load_tea_house_avg_score(tea_house_id, callback_func):
    """加载茶楼玩家平均输赢分"""

    # 查询最近50个房间的房间ID
    def _fun(callback_func, tea_house_id2, result, rows, insertid, error):
        if result:
            # DEBUG_MSG("load_tea_house_avg_score %s" % result)
            roomids = []
            for v in result:
                roomids.append(int(v[0]))

            # 查询50个房间中，玩家的平均输赢分
            def _fun2(callback_func, tea_house_id3, result, rows, insertid, error):
                if result:
                    win_avg_score = 0
                    lose_avg_score = 0
                    for v2 in result:
                        temp = float(v2[0])
                        if temp > 0:
                            win_avg_score = temp
                        else:
                            lose_avg_score = temp
                    # DEBUG_MSG("load_tea_house_avg_score fun3 %s %s %s" % (tea_house_id3, win_avg_score, lose_avg_score))
                    callback_func(tea_house_id3, win_avg_score, lose_avg_score)
                # else:
                #     DEBUG_MSG("load_tea_house_avg_score fun2 %s %s %s %s" % (result, rows, insertid, error))

            _command = "select sum(score)/count(*) from(SELECT sum(totalGoldChange) as score from player_battle_score where teaHouseId=%s and roomId in(%s) " \
                       "GROUP BY playerId) as b GROUP BY interval(score, 0)" % (
                           tea_house_id2, ','.join(str(v) for v in roomids))
            KBEngine.executeRawDatabaseCommand(_command, Functor.Functor(_fun2, callback_func, tea_house_id2))
        # else:
        #     DEBUG_MSG("load_tea_house_avg_score fun %s %s %s %s" % (result, rows, insertid, error))

    _command = "SELECT DISTINCT roomId from player_battle_score where teaHouseId=%s order by settleTime DESC limit 50" % tea_house_id
    # DEBUG_MSG("load_tea_house_avg_score %s" % _command)
    KBEngine.executeRawDatabaseCommand(_command, Functor.Functor(_fun, callback_func, tea_house_id))


def load_tea_house_player_score(account_id, call_back):
    """加载茶楼玩家最近得分
    , tea_house_id, callback
    """

    def _fun(call_back, _account_id, result, rows, insertid, error):
        if result:
            # DEBUG_MSG("load_tea_house_player_score %s %s %s %s %s" % (_account_id, result, rows, insertid, error))
            for v in result:
                _tea_house_id = int(v[0])
                score = float(v[1])
                call_back(_account_id, _tea_house_id, score)
        # else:
        #     DEBUG_MSG("load_tea_house_player_score %s %s %s %s %s" % (_account_id, result, rows, insertid, error))

    _command = "select teaHouseId, sum(totalGoldChange) FROM (SELECT * FROM player_battle_score c WHERE playerId=%s and (" \
               "SELECT count(*) FROM player_battle_score WHERE teaHouseId=c.teaHouseId and playerId=c.playerId AND settleTime>c.settleTime )<=30 " \
               "ORDER BY settleTime DESC) as d GROUP BY teaHouseId, playerId" % account_id
    # DEBUG_MSG("load_tea_house_player_score %s" % _command)
    KBEngine.executeRawDatabaseCommand(_command, Functor.Functor(_fun, call_back, account_id))


def load_account_control(account_id, entity_id, call_back):
    # 如果数据库中没记录，需要增加一条
    # 如果有记录，则加载出来
    def check_exist(call_back, _account_id, _entity_id, result, rows, insertid, error):
        good_pai_count = 0
        last_tick = 0
        # DEBUG_MSG("load_account_control %s %s %s" % (call_back, _account_id, result))
        if result:
            # 存在记录，取出参数
            for v in result:
                good_pai_count = int(v[0])
                last_tick = int(v[1])
                break
        else:
            # 不存在，插入新记录
            sql2 = "INSERT IGNORE INTO player_control_param(userId) VALUES(%s);" % _account_id
            KBEngine.executeRawDatabaseCommand(sql2)
        call_back(_entity_id, good_pai_count, last_tick)

    sql = 'select good_pai_count,last_good_pai_tick from player_control_param where userId=%s' % account_id
    KBEngine.executeRawDatabaseCommand(sql, Functor.Functor(check_exist, call_back, account_id, entity_id))


def update_good_pai_count(user_id, good_pai_count, last_tick):
    sql = 'update player_control_param set good_pai_count=%s, last_good_pai_tick=%s where userId=%s' % (
        good_pai_count, last_tick, user_id)
    KBEngine.executeRawDatabaseCommand(sql)


def update_online_player_count(player_count):
    def check_exist(_date, _player_count, result, rows, insertid, error):
        DEBUG_MSG("update_online_player_count %s %s %s" % (_date, _player_count, result))
        if result:
            # 存在记录，取出参数
            for v in result:
                dbid = int(v[0])
                sql2 = 'update player_online_statistics set min%s=%s where id=%s' % (
                    _date['minute'], _player_count, dbid)
                KBEngine.executeRawDatabaseCommand(sql2)
                break
        else:
            # 不存在，插入新记录
            sql2 = "INSERT INTO player_online_statistics(`date`,`hour`,min%s) VALUES(%s,%s,%s);" % (_date['minute'],
                                                                                                    _date['date'],
                                                                                                    _date['hour'],
                                                                                                    _player_count)
            KBEngine.executeRawDatabaseCommand(sql2)

    now = datetime.datetime.now()
    param_data = {}
    date = now.year * 10000 + now.month * 100 + now.day
    param_data['date'] = date
    param_data['hour'] = now.hour
    cur_minute = (now.minute // 10) * 10
    param_data['minute'] = cur_minute

    sql = 'select id from player_online_statistics where `date`=%s and `hour`=%s' % (
        param_data['date'], param_data['hour'])
    KBEngine.executeRawDatabaseCommand(sql, Functor.Functor(check_exist, param_data, player_count))


def clear_history_battle_score():
    """清除15天以上战绩"""
    days_ago = time.time() - 15 * 24 * 60 * 60
    sql = 'delete from player_battle_score where settleTime<from_unixtime(%s)' % days_ago
    KBEngine.executeRawDatabaseCommand(sql)


def add_challenge_prize(prize_info):
    sql = "INSERT INTO `player_challenge_prize`(`player_id`,`player_name`,`prize_name`,`prize_type`,`prize_price`,`win_time`) " \
          "VALUES(%s,'%s','%s',%s,%s,now());" % (
              prize_info["player_id"], prize_info["player_name"], prize_info["prize"], prize_info["prizeType"],
              prize_info["prizePrice"])
    KBEngine.executeRawDatabaseCommand(sql)


def get_my_prize(user_id, my_prize_callback):
    def _db_callback_fun(result, rows, insertid, error):
        my_prize = []
        if result:
            for v in result:
                data_item = dict()
                data_item["prizeId"] = int(v[0])
                data_item["prize"] = str(v[1], encoding="utf-8")
                data_item["prizeType"] = int(v[2])
                data_item["time"] = str(v[3], encoding="utf-8")
                my_prize.append(data_item)
        my_prize_callback(my_prize)

    sql = "select id,prize_name,prize_type,win_time from player_challenge_prize where player_id=%s and receive_state=1 order by id desc" % user_id
    KBEngine.executeRawDatabaseCommand(sql, _db_callback_fun)


def change_prize_state_for_share(user_id, prize_callback):
    def _db_callback_fun(result, rows, insertid, error):
        if result:
            dbid = int(result[0][0])
            price = float(result[0][1])
            type = int(result[0][2])
            sql = "update player_challenge_prize set receive_state=1 where id=%s" % dbid
            KBEngine.executeRawDatabaseCommand(sql)
            if prize_callback:
                prize_callback(type, price)

    sql = "select id,prize_price,prize_type from player_challenge_prize where player_id=%s and receive_state=0 and win_time>DATE_SUB(now(), INTERVAL 1 DAY) " \
          "order by id desc limit 1" % user_id
    KBEngine.executeRawDatabaseCommand(sql, _db_callback_fun)


def get_all_prize(prize_callback):
    def _db_callback_fun(result, rows, insertid, error):
        all_prize = []
        if result:
            for v in result:
                data_item = dict()
                data_item["userId"] = int(v[0])
                data_item["userName"] = str(v[1], encoding="utf-8")
                data_item["prizeNum0"] = int(float(v[2]))
                data_item["prizeNum1"] = int(float(v[3]))
                # data_item["prizeType0"] = int(v[2])
                # data_item["prizeType1"] = int(v[4])
                all_prize.append(data_item)
        prize_callback(all_prize)

    def _db_callback_count(result, rows, insertid, error):
        if result:
            count = int(result[0][0])
            offset_pos = random.randint(1, count - 10)
            sql2 = "select player_id,player_name,prize_num1,prize_num2 from player_challenge_prize_fake limit %s, 10" % offset_pos
            KBEngine.executeRawDatabaseCommand(sql2, _db_callback_fun)

    sql = "select count(*) from player_challenge_prize_fake"
    KBEngine.executeRawDatabaseCommand(sql, _db_callback_count)


def get_chapter_prize(prize_callback):
    def _db_callback_fun(result, rows, insertid, error):
        all_prize = []
        if result:
            for v in result:
                data_item = dict()
                data_item["userId"] = int(v[0])
                data_item["userName"] = str(v[1], encoding="utf-8")
                data_item["prizeNum"] = int(float(v[2]))
                data_item["prizeType"] = int(float(v[3]))
                all_prize.append(data_item)
        prize_callback(all_prize)

    def _db_callback_count(result, rows, insertid, error):
        if result:
            count = int(result[0][0])
            offset_pos = random.randint(1, count - 15)
            sql2 = "select player_id,player_name,prize_num,prize_type from player_challenge_prize_chapter limit %s, 15" % offset_pos
            KBEngine.executeRawDatabaseCommand(sql2, _db_callback_fun)

    sql = "select count(*) from player_challenge_prize_chapter"
    KBEngine.executeRawDatabaseCommand(sql, _db_callback_count)


def add_game_coin_billing(pyDic):
    def _db_callback_count(v, result, rows, insertid, error):
        if result:
            DEBUG_MSG("add_game_coin_billing %s " % v)
            dbid = int(result[0][0])
            sql = 'UPDATE player_game_coin_bill SET game_coin=game_coin+%s, winner=winner+%s,score=score+%s where id =%s' % (
                v['todayGameCoinAdd'], v['winner'], v['score'], dbid)
            KBEngine.executeRawDatabaseCommand(sql)
        else:
            DEBUG_MSG("add_game_coin_billing2 %s" % v)
            sql = 'INSERT INTO player_game_coin_bill(`tea_house_id`,`user_id`,`game_coin`,`winner`,`score`,`create_date`) VALUES (%s,%s,%s,%s,%s,now())' % (
                pyDic["teaHouseId"], v['userId'], v['todayGameCoinAdd'], v['winner'], v['score'])
            KBEngine.executeRawDatabaseCommand(sql)

    tea_hosue_id = pyDic["teaHouseId"]
    for v in pyDic['bill']:
        userId = v['userId']
        sql = 'select id from player_game_coin_bill where tea_house_id=%s and user_id=%s and create_date=date(now())' % (
            tea_hosue_id, userId)
        KBEngine.executeRawDatabaseCommand(sql, Functor.Functor(_db_callback_count, v))


def change_player_level(tea_house_id, player_db_id, player_level):
    def _db_callback_count(result, rows, insertid, error):
        if result:
            DEBUG_MSG("change_player_level %s " % player_db_id)
            dbid = int(result[0][0])
            sql = 'UPDATE `tea_house_captain` set `level`=%s, `change_time`=now() WHERE `id`=%s;' % (player_level, dbid)
            KBEngine.executeRawDatabaseCommand(sql)
        else:
            DEBUG_MSG("change_player_level2 %s" % player_db_id)
            sql = 'INSERT INTO `tea_house_captain`(`tea_house_id`, `player_id`, `level`, `change_time`) VALUES (%s, %s, %s, now());' % (
                tea_house_id, player_db_id, player_level)
            KBEngine.executeRawDatabaseCommand(sql)

    sql = 'select id from tea_house_captain where tea_house_id=%s and player_id=%s' % (tea_house_id, player_db_id)
    KBEngine.executeRawDatabaseCommand(sql, _db_callback_count)
