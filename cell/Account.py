# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
import json
from enum import IntEnum


# 玩游戏的阶段
class PlayerStage(IntEnum):
    FREE = 0
    NO_READY = 1
    WATCHING = 2
    READY = 3
    PLAYING = 4


class ChallengeControl(IntEnum):
    WIN = 0
    FAIL = 1


class Account(KBEngine.Entity):
    """
    Account实体的cell部分
    """
    room_card = 0
    goldIngot = 0
    today_bless_count = 0
    lucky_card = 0

    def __init__(self):
        KBEngine.Entity.__init__(self)
        self.info = {}
        self.client_death = False   # TODO 是否在线  False在线   True不在线
        self.accountMutableInfo = {
            # 金币数
            "gold": 0,
            # 比赛分数
            "gameCoin": 0
        }
        # 是否进行分数控制
        self.recent_score = 0
        self.lose_score = 0
        self.win_score = 0
        self.need_score_control = False
        self.luck_lose_score = 0
        self.luck_win_score = 0
        self.luck_score_control = False

        # 玩游戏的阶段
        self.playing_stage = PlayerStage.NO_READY
        self.viewing_hall = False

        # 输赢控制
        self.challenge_control = ChallengeControl.WIN
        self.challenge_result_control = []
        self.control_pai_count = 12
        self.control_percent = 0

        self.teahouse_chapter_count = -1
        # 空间管理者信息 owner必须实现玩家非正常离开的处理方法
        self.spaceOwner = KBEngine.entities[int(KBEngine.getSpaceData(self.spaceID, "owner"))]

    # --------------------------------------------------------------------------------------------
    #
    # --------------------------------------------------------------------------------------------

    def initAccountInfo(self, info):
        """
        :param info:
        :return:
        """
        self.info = info
        # 请求冠名赛局数
        if "teaHouseId" in self.spaceOwner.info:
            tea_house_id = self.spaceOwner.info["teaHouseId"]
            if tea_house_id > 0:
                self.base.cellToBase({"func": "reqTeaHouseChapterCount", "teaHouseId": tea_house_id, "accountId": self.id})

        # 如果是挑战赛，请求输赢控制
        if self.spaceOwner.info["type"] == "RoomType6":
            if not self.info["isBot"] and self.spaceOwner.is_challenge_room():
                self.base.cellToBase({"func": "reqChallengeWinControl", "challengeLevel": self.spaceOwner.get_level(), "accountId": self.id})

        self.base.cellToBase({"func": "onCellInit"})

    def retAccountMutableInfo(self, pyDic):
        """
        base---->cell
        :param pyDic:
        :return:
        """
        for key in pyDic.keys():
            if key == "gold":
                _v = pyDic[key]
                _v = int(_v)
                self.accountMutableInfo["gold"] = _v
            # elif key == "goldBean":
            #     _v = int(pyDic[key])
            #     self.accountMutableInfo["goldBean"] = _v
            elif key == "gameCoin":
                DEBUG_MSG('cell Account.py line54 _v value:%s_v type:%s' % (pyDic[key], type(pyDic[key])))
                _v = int(pyDic[key])
                self.accountMutableInfo["gameCoin"] = _v
            elif key == "controlScore":
                self.lose_score = int(pyDic[key][0])
                self.win_score = int(pyDic[key][1])
                self.recent_score = int(pyDic[key][2])
                self.need_score_control = int(pyDic[key][3])
                self.luck_lose_score = int(pyDic[key][4])
                self.luck_win_score = int(pyDic[key][5])
                self.luck_score_control = int(pyDic[key][6])
                DEBUG_MSG('controlScore %s' % pyDic[key])

    def get_need_control_score(self):
        """是否需要分数控制
        如果需要，返回控制分
        """
        if self.win_score == 0 and self.lose_score == 0:
            return 0
        if self.need_score_control:
            return self.win_score - self.recent_score
        return 0

    def get_need_control_luck_score(self):
        """
        是否为幸运数字玩家，是否需要幸运控制
        如果需要，返回控制分
        """
        if self.luck_win_score == 0 and self.luck_lose_score == 0:
            return False
        if self.luck_score_control:
            return self.luck_win_score - self.recent_score
        return 0

    def update_score_control(self, score):
        """根据用户得分，更新是否需要分数控制"""
        DEBUG_MSG('update_score_control id: %s score: %s' % (self.id, score))
        self.recent_score += score

        if self.need_score_control:
            if self.recent_score > self.win_score:
                self.need_score_control = False
        else:
            if self.recent_score < self.lose_score:
                self.need_score_control = True

        # 幸运数字玩家分数控制
        if self.luck_score_control:
            if self.recent_score > self.luck_win_score:
                self.luck_score_control = False
        # else:
        #    没有进行幸运分数控制的玩家，可能不是幸运用户，也可能分数之前比较高；因为不能区分，且只是一大局游戏，这里不再进行恢复控制处理

    def update_player_stage(self, play_stage, room_chapter_count=0, cur_chapter_count=0):
        """
        更新玩家的游戏阶段
        观战、未准备、已准备、游戏中
        """

        if play_stage < self.playing_stage:
            return
        self.playing_stage = play_stage

        # 通知给BASE
        self.base.cellToBase({"func": "updatePlayingStage", "stage": self.playing_stage.value,
                              "maxChapterCount": room_chapter_count, "curChapterCount": cur_chapter_count})

    def is_ready(self):
        return False if self.playing_stage < PlayerStage.READY else True

    def get_need_day_pai_control_count(self):
        """
        每日发N次好牌控制，
        返回今日还需要发几次好牌
        """
        return self.info['goodPaiCount']

    def increase_day_pai_control_count(self, add_count=1):
        ncount = int(self.info['goodPaiCount'])
        self.info['goodPaiCount'] = ncount + add_count

    def get_challenge_control(self, chapter_no):
        """
        需要控制，则返回剩余多少张时，开始压牌；不需要控制则返回0
        """
        if (chapter_no + 1) > len(self.challenge_result_control):
            return 12

        if self.challenge_result_control[chapter_no] == ChallengeControl.FAIL:
            DEBUG_MSG("get_challenge_control %s" % self.control_pai_count)
            return self.control_pai_count
        return 0

    def feedback_challenge_control(self, chapter_no, result):
        """
        每局结束重新计算输赢控制
        result：赢：1； 输：0
        """
        DEBUG_MSG("recalc_challenge_control %s %s %s" % (self.challenge_result_control, chapter_no, result))
        if (chapter_no + 1) > len(self.challenge_result_control):
            return

        if (self.challenge_result_control[chapter_no] == ChallengeControl.FAIL and result == 0)\
                or (self.challenge_result_control[chapter_no] == ChallengeControl.WIN and result == 1):
            return

        # 应该胜，但输了-1;   应该输，但赢了+1
        if self.challenge_result_control[chapter_no] == ChallengeControl.FAIL:
            self.control_pai_count += 1
        else:
            self.control_pai_count -= 1
        if self.control_pai_count < 1:
            self.control_pai_count = 1
        elif self.control_pai_count > 17:
            self.control_pai_count = 17
        DEBUG_MSG("recalc_challenge_control2 %s" % self.control_pai_count)

    def get_control_percent(self):
        return self.control_percent

    def get_win_control(self):
        """
        需要胜，返回 1， 败：返回0
        """
        return 0 if self.challenge_control == ChallengeControl.WIN else 1

    def destroySelf(self):
        """
        :return:
        """
        self.spaceOwner = None
        setattr(self, 'player', None)
        self.destroy()

    def destroyCell(self):
        """
        base---->cell
        :return:
        """
        self.spaceOwner.onPlayerClientDeath(self)
        self.destroySelf()

    # --------------------------------------------------------------------------------------------
    #                              CELL中定义的方法
    # --------------------------------------------------------------------------------------------

    def baseToCell(self, pyDic):
        """

        :param pyDic:
        :return:
        """
        _func_name = pyDic["func"]
        if _func_name == "initAccountInfo":
            _dic = pyDic["dic"]
            self.initAccountInfo(_dic)
        elif _func_name == "retAccountMutableInfo":
            _dic = pyDic["dic"]
            self.retAccountMutableInfo(_dic)
        elif _func_name == "clientStateChange":
            _state = pyDic["state"]
            if _state == "death":
                self.client_death = True
            elif _state == "enable":
                self.client_death = False
        elif _func_name == 'retRoomCard':
            self.room_card = pyDic['roomCard']
        elif _func_name == 'retGoldIngot':
            self.goldIngot = pyDic['goldIngot']
        elif _func_name == 'retTodayBlessCount':
            self.today_bless_count = pyDic['todayBlessCount']
        elif _func_name == 'refreshLuckyCard':
            self.lucky_card = pyDic['luckyCardCount']
        elif _func_name == 'retTeaHouseChapterCount':
            self.teahouse_chapter_count = int(pyDic['dic'])
            DEBUG_MSG("获取到牌局数 %s" % self.teahouse_chapter_count)
        elif _func_name == 'retChallengeWinControl':
            DEBUG_MSG("retChallengeWinControl %s" % pyDic)
            _dic = pyDic['dic']
            if int(_dic['control']) == 1:
                self.challenge_control = ChallengeControl.FAIL
            else:
                self.challenge_control = ChallengeControl.WIN
            self.control_pai_count = int(_dic['controlCount'])
            self.control_percent = int(_dic['controlPercent'])
            DEBUG_MSG("retChallengeWinControl1 %s %s %s %s" % (self.challenge_result_control, self.challenge_control, self.control_pai_count, self.control_percent))
            data = []
            if self.challenge_control == ChallengeControl.FAIL:
                data = [ChallengeControl.FAIL, ChallengeControl.WIN, ChallengeControl.FAIL]
            else:
                data = [ChallengeControl.WIN, ChallengeControl.FAIL, ChallengeControl.WIN]
            if not data:
                random.shuffle(data)
            self.challenge_result_control = data
            DEBUG_MSG("retChallengeWinControl3 %s" % self.challenge_result_control)
        elif _func_name == 'KickOutPlayerInRoom':
            DEBUG_MSG("KickOutPlayerInRoom %s" % pyDic)
            self.spaceOwner.onLeave(self.id)

    def clientToCell(self, exposed, jsonData):
        """
        :param exposed:
        :param jsonData:
        :return:
        """
        # DEBUG_MSG('[Account id %s]---------->clientToCell exposed id %s' % (self.id, exposed))
        sender_entity = KBEngine.entities[exposed]
        if sender_entity is None:
            ERROR_MSG("[Account id %i]:: can not find sender with exposedvalue=[%i]!" % (self.id, exposed))
            return
        _py_dic = json.loads(jsonData)
        _func_name = _py_dic["func"]
        _args = _py_dic["args"]
        if _func_name == "reqAccountInfo":
            # 调用发送方的客户端方法
            _d = self.info.copy()
            _d["flag"] = _args[0]
            sender_entity.cellToClient("retAccountInfo", _d)
        elif _func_name == "reqPlayGold":
            sender_entity.cellToClient("retPlayGold", {"args": [self.id, self.accountMutableInfo["goldBean"]]})
        elif _func_name == "GetPlayerReadyInfoOnTeaHouse":
            """客户端返回茶楼，这里设置房间变动时，进行通知"""
            self.viewing_hall = True
            self.spaceOwner.notify_viewing_hall_players_room_info()
            if self.spaceOwner.started:
                self.spaceOwner.notify_viewing_hall_players_chapter_start()
        elif _func_name == "LeaveRoomInTeaHouse":
            """用户在大厅执行离开房间操作"""
            self.spaceOwner.onLeave(self.id)
        if _func_name == "GetPlayersDistance":
            self.spaceOwner.get_distance_everyone(self.id)

    # --------------------------------------------------------------------------------------------
    #                            Client定义的方法
    # --------------------------------------------------------------------------------------------

    def cellToClient(self, func, info):
        """

        :param func:
        :param info:
        :return:
        """
        _json_data = json.dumps(info, ensure_ascii=False)
        if self.info["isBot"] == 0:
            self.client.cellToClient(func, _json_data)
        else:
            ""

    # --------------------------------------------------------------------------------------------
    #                              System Callbacks
    # --------------------------------------------------------------------------------------------
    def onTimer(self, id, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param id		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """
        DEBUG_MSG(id, userArg)

    def onDestroy(self):
        """
        KBEngine method.
        entity销毁
        """
        DEBUG_MSG("Account::onDestroy: %i." % self.id)
