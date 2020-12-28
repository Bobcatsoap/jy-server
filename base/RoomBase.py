# -*- coding: utf-8 -*-
import datetime
import time

import Const
from KBEDebug import *
import Bots
import DBCommand


def tea_house_manager():
    return KBEngine.globalData["TeaHouseManager"].mgr


class RoomBase(KBEngine.Entity):
    """
    """
    chapterInfos = {}
    chapterReplay = {}
    roomInfos = {}
    roomState = 0
    roomId = 0
    total_settlement_ed = False   # TODO total_settlement_ed 总结算标志位  False未结算 True已结算
    room_mgr = None
    tea_house_mgr = None
    account_mgr = None
    gold_session_mgr = None
    # 是否是假房间
    is_fake = False
    # 是否计入数据库统计
    record_sql = True

    def __init__(self):
        KBEngine.Entity.__init__(self)
        # 保存一下当前场景中的所有实体
        # 包含的实体字典，key=id，value=EntityCall
        self.entities = {}
        self.room_mgr = self.room_mgr
        # 房间信息
        self.info = {
            # 实例类型
            "type": None,
            # 房间类型 金币场 或是 普通场 newRoom中获取
            "roomType": None,
            # 房间号GameHall newRoom中获取
            "roomId": 0,
            # 最大局数
            "maxNum": 10,
            # 最大玩家数
            "maxPlayersCount": 3,
            # 创建者databaseId -1表示为系统创建
            "creator": -1,
            # 创建者的accountId -1表示为系统创建
            "creatorAccountId": -1,
            # 房间是否开始标识
            "started": False,
            # 房间是否有特殊牌型
            # "SpacrCardType":False
            # 房间名字
            "roomName": None
        }
        # 当前玩家数
        self.currentPlayersCount = 0
        # 当前坐下玩家
        self.currentSeatPlayersCount = 0
        # 管理这个房间的大厅
        self.master = None
        self.create_cell_cb = None
        self.createUserEntity = None
        self.roomConfig = {}
        self.tea_house_mgr = KBEngine.globalData["TeaHouseManager"].mgr
        self.room_mgr = KBEngine.globalData["RoomManager"].mgr
        self.account_mgr = KBEngine.globalData["AccountMgr"].mgr
        self.gold_session_mgr = KBEngine.globalData['GoldSessionManager'].mgr
        # 仅在房间结束后,用来查看战绩，并根据最后查看时间，清除房间实体
        self.last_query_tick = 0

    def initFromDB(self):
        self.info = self.roomInfos

    def initToDB(self):
        self.roomInfos = self.info

    def create_space(self, cb):
        # 向cellappmgr请求创建一个cell，并关联本实体对象
        # 参数cellappIndex为None，表示由引擎负载均衡进行动态选择
        self.create_cell_cb = cb
        self.createCellEntityInNewSpace(None)

    def on_account_cell_destroy(self, account_db_id):
        """
        每当有玩家的cell端被销毁时，通知房间内
        :param account_db_id:
        :return:
        """
        DEBUG_MSG('RoomBase on_account_cell_destroy account_db_id%s' % account_db_id)
        self.cell.baseToCell({'func': 'OnAccountCellDestroy', 'accountDBID': account_db_id})

    # --------------------------------------------------------------------------------------------
    #                            DEF中定义的方法
    # --------------------------------------------------------------------------------------------

    def login_to_room(self, account, cb=None):
        """
        某个Entity请求登录到该房间
        :param account: 要进入本房间的实体account
        """
        if account is None or account.cell is not None:
            DEBUG_MSG("[RoomBase]login to room ------>Fail Because Account is None Or Account.cell is Not None")
            return
        account.createCell(self, cb)
        self.entities[account.id] = account

    def logoutRoom(self, entityId):
        """
        某个玩家请求登出该场景
        :param entityId: 登出者的id
        """
        if entityId in self.entities:
            del self.entities[entityId]

        # 通知scene的cell部分，有人离开了
        # if self.cell is not None:
        #     self.cell.onLeave(entityId)

    def onRoomInit(self):
        """
        cell--->base
        :return:
        """
        if self.create_cell_cb is not None:
            self.create_cell_cb(self)

    def cellToBase(self, pyDic):
        """
        cell向base请求通信
        :param pyDic:
        :return:
        """
        _func_name = pyDic["func"]
        log_filter = set()
        log_filter.add("writeChapterReplay")
        DEBUG_MSG('[RoomBase] ------>cellToBase pyDic=%s' % _func_name if _func_name in log_filter else pyDic)

        # 房间初始化
        if _func_name == "onRoomInit":
            self.onRoomInit()
        # 退出房间
        elif _func_name == "LogoutRoom":
            self.logoutRoom(pyDic['accountId'])
        # 房间开始
        elif _func_name == "roomStart":
            self.info["started"] = True
            room_info = pyDic["roomInfo"]
            # 通知冠名赛，加入当天列表
            if "teaHouseId" in room_info and room_info["teaHouseId"] != -1:
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(
                    pyDic["roomInfo"]["teaHouseId"])
                if tea_house_entity:
                    # 更新客户端某个房间状态
                    tea_house_entity.update_single_room_state_to_client(self)
            elif 'level' in room_info and room_info['level'] != 0:
                self.gold_session_mgr.update_single_room_state_to_client(self.info['level'], self)
        # 记录房间统计
        elif _func_name == 'addTodayRoom':
            if 'teaHouseId' in self.info and self.info['teaHouseId'] != -1:
                try:
                    tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(self.info['teaHouseId'])
                    tea_house_entity.add_today_rooms(self.databaseID, self.info['createRoomTime'], self.info['type'])
                except AttributeError as e:
                    ERROR_MSG('RoomBase::addTodayRoom %s' % e)
                except KeyError as e:
                    ERROR_MSG('RoomBase::addTodayRoom %s' % e)
        # 玩家数量刷新
        elif _func_name == "playersCount":
            self.currentPlayersCount = pyDic["count"]
        # 自动创建房间
        elif _func_name == "autoCreateRoom":
            room_info = pyDic["roomInfo"]
            if "teaHouseId" in room_info and room_info["teaHouseId"] != -1:
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(
                    pyDic["roomInfo"]["teaHouseId"])
                ignore_judge = pyDic['ignoreJudge'] if 'ignoreJudge' in pyDic else False
                # 是否是房间结束时发送的自动创建房间,True时，创建的房间跟在原来房间后面
                room_end = pyDic['onRoomEnd'] if 'onRoomEnd' in pyDic else False
                tea_house_entity.auto_create_room_with_judgement(pyDic["roomInfo"], ignore_judge=ignore_judge,
                                                                 room_end=room_end)
            elif 'level' in room_info and room_info['level'] != 0:
                self.gold_session_mgr.auto_create_room_with_judgement(room_info)
        # 刷新玩家数量
        elif _func_name == "refreshPlayerInGame":
            self.info["playerInGame"] = pyDic["playerInGame"]
            if pyDic["teaHouseId"] != -1:
                # 通知客户端最新房间信息
                self.tea_house_mgr.update_single_room_info_to_client(pyDic["teaHouseId"], self.info)
                # 如果是未开始的房间，通知茶楼修正房间数
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(pyDic['teaHouseId'])
                if tea_house_entity and len(pyDic["playerInGame"]) == 0:
                    tea_house_entity.on_room_player_all_leave(self.info)
            elif 'level' in self.info and self.info['level'] != 0:
                self.gold_session_mgr.update_single_room_info_to_client(self.info['level'], self.info)
            elif "substitute" in self.info and self.info["substitute"]:
                self.refresh_substitute()
        # 刷新局数
        elif _func_name == 'newChapter':
            self.info['currentChapterCount'] = pyDic['count']
            if "teaHouseId" in self.info and self.info["teaHouseId"] != -1:
                # 通知客户端最新房间信息
                self.tea_house_mgr.update_chapter_count_info(self.info['teaHouseId'], self.info['roomId'],
                                                             pyDic['count'])
            elif "substitute" in self.info and self.info["substitute"]:
                self.refresh_substitute()
        # 解散冠名赛房间
        elif _func_name == "disbandTeaHouseRoom":
            def on_success():
                # 通知cell删除自己
                self.cell.baseToCell({"func": "destroySpace"})

            if pyDic["teaHouseId"] != -1:
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(pyDic["teaHouseId"])
                tea_house_entity.remove_room(pyDic["roomId"], pyDic["teaHouseId"], on_success)
        # 解散金币场房间
        elif _func_name == 'disbandGoldSessionRoom':
            def on_success():
                # 通知cell删除自己
                self.cell.baseToCell({"func": "destroySpace"})

            if pyDic["level"] != 0:
                gold_session = self.gold_session_mgr.get_gold_session_with_level(pyDic["level"])
                gold_session.remove_room(pyDic["roomId"], on_success)
        # 返还房主钻石
        elif _func_name == "returnRoomCardToCreator":
            if self.info['payType'] == Const.PayType.RoomCreator:
                # 如果是钻石场并且钻石场钻石消耗开启，返还钻石
                if self.info["roomType"] == "card":
                    self.reduce_room_count()
                    if self.room_mgr.need_consume_card(self.info):
                        self.modify_player_room_card(self.info['creator'], self.info['roomCardConsume'])
                # 如果冠名赛场钻石消耗开启，返还钻石
                elif self.info["roomType"] == "gameCoin":
                    self.reduce_room_count()
                    if self.room_mgr.need_consume_card(self.info):
                        self.modify_player_room_card(self.info['creator'], self.info['roomCardConsume'])
                # 如果普通冠名赛场钻石消耗开启，返还钻石
                elif self.info['roomType'] == 'normalGameCoin':
                    self.reduce_room_count()
                    if self.room_mgr.need_consume_card(self.info):
                        self.modify_player_room_card(self.info['creator'], self.info['roomCardConsume'])
                elif self.info['roomType'] == 'challenge':
                    if self.room_mgr.need_consume_card(self.info):
                        self.modify_player_goldIngot(self.info['creator'], self.info['roomCardConsume'])
        # AA支付消耗玩家钻石
        elif _func_name == "AAPayTypeModifyRoomCard":
            if self.info['payType'] == Const.PayType.AA:
                need_consume = pyDic['needConsumePlayers']
                for account_db_id in need_consume:
                    if self.info["roomType"] == "card":
                        if self.room_mgr.need_consume_card(self.info):
                            self.modify_player_room_card(account_db_id, -self.info['roomCardConsume'])
                    elif self.info["roomType"] == "gameCoin":
                        if self.room_mgr.need_consume_card(self.info):
                            self.modify_player_room_card(account_db_id, -self.info['roomCardConsume'])
                    elif self.info['roomType'] == 'normalGameCoin':
                        if self.room_mgr.need_consume_card(self.info):
                            self.modify_player_room_card(account_db_id, -self.info['roomCardConsume'])
        elif _func_name == "BigWinnerRoomCard":

            account_db_id = pyDic['account_db_id']
            DEBUG_MSG('account_db_id%s 修改者大赢家的uresID' % account_db_id)
            self.modify_player_room_card(account_db_id, 1)

        elif _func_name == "extractRoomCostToCreator":
            #获取房间费用
            billingCount = pyDic['billingCount']
            # 如果是钻石场并且钻石场钻石消耗开启，返还钻石，应该获取茶楼创建者ID
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(self.info['teaHouseId'])
            DEBUG_MSG('冠名赛ID%s creatorid' % self.info['teaHouseId'])
            creatorid = tea_house_entity.creatorDBID
            DEBUG_MSG('茶楼创建者ID%s creatorid' % creatorid)
            tea_house_entity.modify_game_coin_to_public(creatorid, billingCount)


            self.account_mgr.give_gold_modify(creatorid, billingCount, 1)
            player = self.account_mgr.get_account(creatorid)
            # tea_house_entity.set_game_coin(creatorid, player.gold+billingCount)
        # 解散代开房间
        elif _func_name == "disbandSubstituteRoom":
            creator_db_id = pyDic["creator"]
            def callback(baseRef, databaseID, wasActive):
                for room in baseRef.substituteRooms:
                    if room["roomId"] == pyDic["roomInfo"]["roomId"]:
                        baseRef.substituteRooms.remove(room)
                        self.cell.baseToCell({"func": "destroySpace"})
                        break
                # 不在线，存库
                if not wasActive:
                    baseRef.writeToDB()

            KBEngine.createEntityFromDBID("Account", creator_db_id, callback)
        # 写入冠名赛房间记录
        elif _func_name == "writeTeaHouseRoom":
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(pyDic["teaHouseId"])
            tea_house_entity.write_history_room(pyDic["type"], self.databaseID, pyDic['recordPlayers'])
        # 写入牌局信息
        elif _func_name == "writeChapterInfo":
            self.save_challenge_score(pyDic["chapterInfos"])
            if 'challengeControl' in pyDic["chapterInfos"]:
                del pyDic["chapterInfos"]['challengeControl']
            self.chapterInfos = pyDic["chapterInfos"]
            self.save_player_score(self.chapterInfos)
            # self.writeToDB()
        # 写入回放
        elif _func_name == "writeChapterReplay":
            self.chapterReplay = pyDic["chapterReplay"]
            # self.writeToDB()
        # 改变房间状态
        elif _func_name == "changeRoomState":
            self.roomState = pyDic["roomState"]
        # 今日比赛分收成
        elif _func_name == "todayGameBilling":
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(pyDic["teaHouseId"])
            DEBUG_MSG('todayGameBilling------------------')
            DEBUG_MSG(pyDic)
            if tea_house_entity:
                # pyDic["todayGameCoinAdd"] 抽成的数量
                if float(pyDic["todayGameCoinAdd"]) > 0.0:
                    tea_house_entity.add_today_game_coin_billing(pyDic["userId"], pyDic["todayGameCoinAdd"], pyDic['roomType'])
        elif _func_name == "todayBillStatic":
            tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(pyDic["teaHouseId"])
            if tea_house_entity:
                DBCommand.add_game_coin_billing(pyDic)
        # 总结算
        elif _func_name == "totalSettlementEd":
            self.total_settlement_ed = True
        elif _func_name == 'joinBots':
            self.join_bots_from_cell()
        elif _func_name == 'Lottery':
            self.lottery(pyDic['args'])

    def lottery(self, dic):
        """
        抽奖
        :param dic:
        :return:
        """
        for v in dic:
            account_db_id = v['accountDBID']
            consume_lucky_card = v['consumeLuckyCard']
            count = v['count']
            award_type = v['type']
            # DEBUG_MSG('account_db_id%s consume_lucky_card%s award_type%s count%s' % (account_db_id,
                                                                                    #  consume_lucky_card, award_type,
                                                                                    #  count))
            if award_type == 1:
                # 钻石
                self.account_mgr.modify_room_card(account_db_id, count, consume_type='award')
            elif award_type == 0:
                # 金币
                self.account_mgr.modify_gold(account_db_id, count)
            try:
                # DEBUG_MSG('RoomBase consume:%s,teaHouseId:%s' % (count, self.info['teaHouseId']))
                # 消耗福卡
                tea_house_entity = self.tea_house_mgr.get_tea_house_with_id(self.info['teaHouseId'])
                tea_house_entity.consume_lucky_card(account_db_id, consume_lucky_card)
            except AttributeError as e:
                DEBUG_MSG(e)

    def join_bots_from_cell(self):
        """
        玩家进入房间后自动加入机器人
        :return:
        """
        # 金币场才有机器人
        if self.info['level'] == 0:
            return
        if len(self.info['playerInGame']) >= self.info['maxPlayersCount']:
            return
        if self.info['started']:
            return
        self.joinBots(1)

    def joinBots(self, count):
        """
        加入机器人
        :return:
        """
        for i in range(0, count):
            _bot = Bots.getBotBotAccountEntity()
            if not _bot:
                return
            # if self.info["type"] == "RoomType7":
            #     if _bot.gold < Const.Room7Stake.stake[self.info["betLimit"]][0]:
            #         return
            # if self.info["type"] == "RoomType6":
            #     if _bot.gold < Const.Room6GoldLimit.gold[int(self.info["level"]) - 1]:
            #         return
            _bot.createCell(self)

    def save_player_score(self, chapterInfos):
        """
        保存玩家得分，进行分数控制
        冠名赛ID，游戏类型，结算时间，结算数据，玩家ID，房间ID
        """
        if 'teaHouseId' not in self.roomInfos:
            return
        tea_house_id = self.roomInfos["teaHouseId"]
        room_type = self.roomInfos["type"]
        settle_time = chapterInfos["createRoomTime"]
        players_score = {}
        values = ""
        DEBUG_MSG("save_player_score %s %s %s" % (tea_house_id, room_type, chapterInfos["playerInfo"]))
        max_win = 0
        for v in chapterInfos["playerInfo"]:
            tmp = v['totalGoldChange'] - v['otherBilling'] - v['winnerBilling']
            if tmp > max_win:
                max_win = tmp

        for v in chapterInfos["playerInfo"]:
            bill_score = v['otherBilling'] + v['winnerBilling']
            win_score = v['totalGoldChange'] - bill_score
            accountName = v['accountName']
            gold = 0
            totalGold = 0
            if v.get("gold"):
                gold = v["gold"]
            if v.get("totalGold"):
                totalGold = v["totalGold"]
            value_item = "(%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s,'%s',%s)," % (
                tea_house_id, v['userId'], room_type, v['totalGoldChange'], self.roomId,
                1 if win_score == max_win else 0, win_score, bill_score, gold, totalGold, accountName, settle_time)
            values += value_item
            players_score[v['userId']] = v['totalGoldChange']

        sql = "INSERT IGNORE into player_battle_score(teaHouseId,playerId,roomType,totalGoldChange,roomId,winner,winScore,bill, gold, totalGold, accountName, settleTime) values"
        sql += values[:-1]
        # DEBUG_MSG("保存大战绩save_player_score --->sql %s" % sql)
        DBCommand.exec_normal_sql(sql)

        tea_house = tea_house_manager().get_tea_house_with_id(tea_house_id)
        if tea_house:
            tea_house.update_tea_house_score_control(players_score)

    def save_challenge_score(self, chapterInfos):
        """
        保存玩家得分，进行分数控制
        冠名赛ID，游戏类型，结算时间，结算数据，玩家ID，房间ID
        """
        # DEBUG_MSG(self.roomInfos)
        if 'roomType' not in self.roomInfos or self.roomInfos['roomType'] != 'challenge':
            return
        try:
            challenge_level = self.roomInfos["level"]
            room_type = self.roomInfos["type"]
            settle_time = chapterInfos["createRoomTime"]

            challenge_control = chapterInfos["challengeControl"]
            win_percent = challenge_control["winPercent"]
            win_control = challenge_control["winControl"]
            luck_user = challenge_control["luckUser"]
            DEBUG_MSG("save_challenge_score %s %s %s %s" % (
            challenge_level, room_type, luck_user, chapterInfos["playerInfo"]))

            for v in chapterInfos["playerInfo"]:
                # 找到真正的玩家，判断是否赢
                account = self.account_mgr.get_account(v['userId'])
                if account and account.isBot == 0:
                    value_item = "(%s,%s,'%s',%s,%s,from_unixtime(%s),%s,%s,%s)" % (
                    challenge_level, v['userId'], room_type, v['totalGoldChange'], self.roomId,
                    settle_time, luck_user, win_control, win_percent)
                    sql = 'INSERT INTO `player_challenge_battle`(`level`, `playerId`, `roomType`, `goldChange`, `roomId`, `settleTime`, `luckUser`, `winControl`,' \
                          '`winPercent`) VALUES '
                    sql += value_item
                    DBCommand.exec_normal_sql(sql)
                    break
        except Exception as e:
            DEBUG_MSG("save_challenge_score %s" % e)

    #   ===============================================
    #                       系统回调
    #   ===============================================

    def onGetCell(self):
        """
        entity的cell部分被创建成功
        """
        self.cell.baseToCell({"func": "initRoom", "dic": self.info})
        self.cell.baseToCell({'func': 'initServerConfig', 'dic': Const.ServerGameConfigJson.config_json['Lottery']})
        # 如果是茶楼房间，在cell创建好后发送茶楼配置信息
        if 'teaHouseId' in self.info and self.info['teaHouseId'] != -1:
            tea_house_entity = tea_house_manager().get_tea_house_with_id(self.info['teaHouseId'])
            if tea_house_entity:
                tea_house_entity.refresh_tea_house_info_to_room_cell(self.info['roomId'])

    def onLoseCell(self):
        """
        entity的cell部分实体丢失
        """
        self.room_mgr.remove_room_from_mgr(self)
        self.destroy()
        DEBUG_MSG("Scene[%i]::onLoseCell:" % self.id)

    def onDestroy(self):
        """
        :return:
        """
        self.room_mgr = None
        self.tea_house_mgr = None
        self.account_mgr = None
        self.gold_session_mgr = None
        self.entities.clear()
        self.create_cell_cb = None
        try:
            if self.master:
                self.master.remove_room(self)
            self.master = None
        except AttributeError as e:
            ERROR_MSG('RoomBase onDestroy %s' % e)

    def modify_player_room_card(self, player_db_id, modify_count):
        """
        修改房卡
        :param player_db_id:
        :param modify_count:
        :return:
        """
        DEBUG_MSG('创建房间消耗房卡,房间信息%s' % self.info)
        self.account_mgr.modify_room_card(player_db_id, modify_count, consume_type=self.info['type'])

    def modify_player_goldIngot(self, player_db_id, modify_count):
        """
        修改元宝
        :param player_db_id:
        :param modify_count:
        :return:
        """
        DEBUG_MSG('创建房间消耗元宝,房间信息%s' % self.info)
        self.account_mgr.modify_goldIngot(player_db_id, modify_count, consume_type=self.info['type'])

    def refresh_substitute(self):
        """
        如果该房间是代开房间，刷新创建者UI
        :return:
        """
        creator = self.account_mgr.get_account(self.info["creator"])
        # 如果在线，通知代开房间信息
        if creator:
            creator.send_substitute_room_list()

    def is_tea_house_room(self):
        """
        判断此房间是否是茶楼房间
        :return:
        """
        if 'teaHouseId' in self.info and self.info['teaHouseId'] != -1:
            if self.info['roomType'] == 'normalGameCoin' or self.info['roomType'] == 'gameCoin':
                return True
        return False

    def is_gold_session_room(self):
        """
        判断此房间是否是金币场房间
        :return:
        """
        return 'level' in self.info and self.info['level'] != 0

    def reduce_room_count(self):
        creator = self.info['creator']

        def callback(baseRef, databaseID, wasActive):
            today_date = datetime.date.today()
            today_end = int(time.mktime(today_date.timetuple()) + 86399)
            DBCommand.modify_room_count_to_db(creator, baseRef.name, -1, today_end)

        KBEngine.createEntityFromDBID("Account", creator, callback)
