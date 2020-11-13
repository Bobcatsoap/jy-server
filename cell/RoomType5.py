# -*- coding: utf-8 -*-
import collections
import datetime

import KBEngine
from KBEDebug import *
from RoomBase import *
import mj.AgariUtils
import mj.RoomType14Calculator
import PaiTypeUtil
import time
import Account

# --------------------------------------------------------------------------------------------
#                            麻将中牌
# --------------------------------------------------------------------------------------------
# 0  1  2  3  4  5  6  7  8  --> 1-9筒
# 9  10 11 12 13 14 15 16 17 --> 1-9条
# 18 19 20 21 22 23 24 25 26 --> 1-9万
# 27 28 29 30                --> 东 南 西 北
# 31 32 33                   --> 中 發 白
TONG = 0
TONG_1 = 0
TONG_2 = 1
TONG_3 = 2
TONG_4 = 3
TONG_5 = 4
TONG_6 = 5
TONG_7 = 6
TONG_8 = 7
TONG_9 = 8
TIAO = 1
TIAO_1 = 9
TIAO_2 = 10
TIAO_3 = 11
TIAO_4 = 12
TIAO_5 = 13
TIAO_6 = 14
TIAO_7 = 15
TIAO_8 = 16
TIAO_9 = 17
WAN = 2
WAN_1 = 18
WAN_2 = 19
WAN_3 = 20
WAN_4 = 21
WAN_5 = 22
WAN_6 = 23
WAN_7 = 24
WAN_8 = 25
WAN_9 = 26
FENG_DONG = 27
FENG_NAN = 28
FENG_XI = 29
FENG_BEI = 30
SUNYUAN_ZHONG = 31
SUNYUAN_FA = 32
SUNYUAN_BAI = 33
# 0-8位：牌的编号； 9-16位：用于算额外的花分
# HUA_CHUN = 34 | 1 << 8
# HUA_XIA = 35 | 1 << 9
# HUA_QIOU = 36 | 1 << 10
# HUA_DONG = 37 | 1 << 11
# HUA_MEI = 38 | 1 << 12
# HUA_LAN = 39 | 1 << 13
# HUA_ZHU = 40 | 1 << 14
# HUA_JU = 41 | 1 << 15
HUA_CHUN = 34
HUA_XIA = 35
HUA_QIOU = 36
HUA_DONG = 37
HUA_MEI = 38
HUA_LAN = 39
HUA_ZHU = 40
HUA_JU = 41
CXQD = [HUA_CHUN, HUA_XIA, HUA_QIOU, HUA_DONG]
MLZJ = [HUA_MEI, HUA_LAN, HUA_ZHU, HUA_JU]

# --------------------------------------------------------------------------------------------
#                            麻将中玩家的操作
# --------------------------------------------------------------------------------------------
# 出牌
OPT_OUT = "outPaiOpt"
OPT_OUT_V = 1
# 小明杠
OPT_XIAOMINGGANG = "xiaoMingGangOpt"
OPT_XIAOMINGGANG_V = 1 << 1
# 暗杠
OPT_ANGANG = "anGangOpt"
OPT_ANGANG_V = 1 << 2
# 胡牌
OPT_HU_ZIMO = "ziMoHuOpt"
OPT_HU_ZIMO_V = 1 << 3

# 过
OPT_GUO = "resOutPaiGuoOpt"
OPT_GUO_V = 1 << 4
# 吃牌
OPT_CHI = "resOutPaiChiOpt"
OPT_CHI_V = 1 << 5
# 碰牌
OPT_PENG = "resOutPaiPengOpt"
OPT_PENG_V = 1 << 6
# 大明杠
OPT_DAMINGGANG = "resOutPaiDaMingGangOpt"
OPT_DAMINGGANG_V = 1 << 7
# 胡牌
OPT_HU_DIANPAO = "resOutPaiDianPaoHuOpt"
OPT_HU_DIANPAO_V = 1 << 8
# 抢杠和
OPT_HU_QIANGGANG = "resOutPaiQiangGangHuOpt"
OPT_HU_QIANGGANG_V = 1 << 9
# 明次牌胡
OPT_HU_Ming_CI = 'resOutPaiMingCiHuOpt'
OPT_HU_Ming_CI_V = 1 << 10
# 小明次胡
OPT_HU_XIAO_MING_CI = 'resOutPaiXiaoMingCiHuOpt'
OPT_HU_XIAO_Ming_CI_V = 1 << 11
# 暗次胡
OPT_HU_AN_CI = 'resOutPaiAnCiHuOpt'
OPT_HU_AN_CI_V = 1 << 12
# 皮次
OPT_HU_Pi_CI = 'resOutPaiPiCiHuOpt'
OPT_HU_Pi_CI_V = 1 << 13
# 玩家操作的牌
PLAYER_OPT_PAI = "pai"

OPT_DICT = {OPT_OUT: OPT_OUT_V, OPT_GUO: OPT_GUO_V, OPT_CHI: OPT_CHI_V, OPT_PENG: OPT_PENG_V,
            OPT_XIAOMINGGANG: OPT_XIAOMINGGANG_V, OPT_DAMINGGANG: OPT_DAMINGGANG_V, OPT_ANGANG: OPT_ANGANG_V,
            OPT_HU_ZIMO: OPT_HU_ZIMO_V, OPT_HU_DIANPAO: OPT_HU_DIANPAO_V, OPT_HU_Ming_CI: OPT_HU_Ming_CI_V,
            OPT_HU_XIAO_MING_CI: OPT_HU_XIAO_Ming_CI_V, OPT_HU_AN_CI: OPT_HU_AN_CI_V, OPT_HU_Pi_CI: OPT_HU_Pi_CI_V,
            OPT_HU_QIANGGANG: OPT_HU_QIANGGANG_V}

# FA_PAI_AFTER_OPTS = [OPT_OUT, OPT_XIAOMINGGANG, OPT_ANGANG, OPT_HU_ZIMO]
FA_PAI_AFTER_OPTS_CODE = 15
# OUT_PAI_AFTER_OPTS = [OPT_GUO, OPT_CHI, OPT_PENG, OPT_DAMINGGANG, OPT_HU_DIANPAO]
OUT_PAI_AFTER_OPTS_CODE = 496
# --------------------------------------------------------------------------------------------
#                            麻将检查结果
# --------------------------------------------------------------------------------------------
# 属于那个玩家
CHECK_PLAYER = "checkPlayer"
# 数组中嵌套数组
CHECK_CHI = "checkChi"
# 布尔类型
CHECK_PENG = "checkPeng"
# 数组类型
CHECK_XIAOMINGGANG = "checkXiaoMingGang"
# 布尔类型
CHECK_DAMINGGANG = "checkDaMingGang"

# 数组类型
CHECK_ANGANG = "checkAnGang"
# 布尔类型
CHECK_HU = "checkHu"
# 布尔类型，抢杠和
CHECK_HU_QIANG_GANG = "checkHuQiangGang"
# 布尔类型,次牌胡
CHECK_HU_MING_CI = 'checkHuMingCi'
CHECK_HU_AN_CI = 'checkHuAnCi'
CHECK_HU_PI_CI = 'checkPiCi'
# 操作优先级
PRIORITY_OPERATION = "priorityOperation"
# 玩家选择的操作
CHECK_PLAYER_OPT = "playerOpt"
# 检查的标记，1：表示出牌时吃碰杠胡检查；2：表示小明杠时抢杠和检查
CHECK_FLAG = "checkFlag"
CHECK_FLAG_OUTPAI = 1
CHECK_FLAG_XIAOMINGGANG = 2

NO_OPT = 0
CHI_ARGS = "chiArgs"
# --------------------------------------------------------------------------------------------
#                            麻将操作权重
# --------------------------------------------------------------------------------------------
HU_WEIGHT = 10000
GANG_WEIGHT = 1000
PENG_WEIGHT = 100
# --------------------------------------------------------------------------------------------
#                            同步操作
# --------------------------------------------------------------------------------------------
SYNCOPT_FAPAI = "faPai"
SYNCOPT_OUTPAI = "outPai"
SYNCOPT_CHI = "chi"
SYNCOPT_PENG = "peng"
SYNCOPT_XIAOMINGGANG = "xiaoMingGang"
SYNCOPT_DAMINGGANG = "daMingGang"
SYNCOPT_ANGANG = "anGang"
SYNCOPT_ZIMOHU = "ziMoHu"
SYNCOPT_DIANPAOHU = "dianPaoHu"
SYNC_OPT_MING_CI = 'mingCiHu'
SYNC_OPT_XIAO_MING_CI = 'xiaoMingCiHu'
SYNC_OPT_AN_CI = 'anCiHu'
SYNC_OPT_PI_CI = 'piCiHu'
SYNCOPT_QIANGGANGHU = "qiangGangHu"
SYNCOPT_HUANGZHUANG = "huangZhuang"
# --------------------------------------------------------------------------------------------
#                            麻将对局中的属性
# --------------------------------------------------------------------------------------------
# 当前操作玩家
CUR_PLAYER = "currentPlayer"
# 当前等待玩家
WAIT_PLAYER = "waitPlayer"
# 当前牌
CUR_PAI = "currentPai"
# 最多四个人打麻将
MAX_PLAYER_COUNT = 4
# 次牌
CI_CARD = -1
# 一个玩家打出一张牌，其他玩家可以操作的结果集合
CHECK_RESULTS = "checkResults"
# 胡牌玩家 {locationIndex: state, ...}
HU_PLAYER = "huPlayer"
# state: -1表示未选择，0表示不胡，1表示胡
HU_SELECT_STATE_INIT = -1
HU_SELECT_STATE_NO = 0
HU_SELECT_STATE_YES = 1
# 放炮玩家的位置
FANG_PAO_INDEX = "fangPaoIndex"
# 房间中的玩家
PLAYER_IN_GAME = "players"
# 观战玩家
PLAYER_OUT_GAME = 'playerOutGame'
# 牌库
CARDS_LIB = "cardsLib"
# 允许客户端玩家操作的集合
ALLOW_OPT_PLAYERS = "allowOptPlayers"
# 玩家按位置顺序的排列，在initRound时初始化
ROUND = "round"
# 是否能胡
CAN_HU = "isHu"
# 是否弃胡
QI_HU = "qiHu"
# 是否能碰牌
CAN_PENG = "canPeng"
# 是否赢次牌
WIN_CI = "winCi"
# 是否能听
IS_TING = "isTing"
# 是否抢杠和
IS_QIANG_GANG_HE = "isQiangGangHe"
# 是否是点炮胡
IS_DIAN_PAO__HE = "isDianPaoHe"
# 是否是明次胡
IS_MING_CI_HE = 'isMingCiHe'
# 是否是暗次胡
IS_AN_CI_HE = 'isAnCiHe'
# 是否是小明次胡
IS_XIAO_MING_CI_HE = 'isXiaoMingCiHe'
# 是否是皮次胡
IS_PI_CI_HE = 'isPiCiHe'
# 自摸胡
IS_ZI_MO_HE = 'isZiMoHe'
# 荒庄
IS_HUANG_ZHUANG = 'isHuangZhuang'
# 是否杠上开花
IS_GANG_SHANG_KAI_HUA = "isGangShangKaiHua"
# 本局中剩余牌的数量
LEFT_PAI_COUNT = "leftPaiCount"
# 房主，第一个进入房间的玩家，默认为房主
ROOM_MASTER = "roomMaster"
# 胡牌的类型 -1:表示没有结束;0:荒庄;1:自摸;2:点炮;3:抢杠
HU_TYPE = "huType"
HU_TYPE_HUANG_ZHUANG = 0
HU_TYPE_ZI_MO = 1
HU_TYPE_DIAN_PAO = 2
HU_TYPE_QIANG_GANG = 3
HU_TYPE_MING_CI = 4
HU_TYPE_AN_CI = 5
HU_TYPE_PI_CI = 6
HU_TYPE_XIAO_MING_CI = 7

# --------------------------------------------------------------------------------------------
#                            麻将player中的属性
# --------------------------------------------------------------------------------------------
# 手牌
SHOU_PAI = "cards"
# 单放: 发的一张牌
DAN_FANG = "danFang"
# 摸到的花牌
HUA_PAI = "huaPai"
# 结算时花的数量
HUA_COUNT = "huaCount"
# 吃的牌 类型{p1: (pai, otherIndex), p1: (pai, otherIndex)...}，p1表示顺子的第一张牌，pai表示吃的哪张牌
CHIS = "chis"
# 碰过的牌 类型{pai: otherIndex, pai: otherIndex ...}
PENG_S = "pengs"
# 小明杠的牌 类型{pai: otherIndex, pai: otherIndex ...}
XIAO_MING_GANG_S = "xiaoMingGangs"
# 大明杠的牌 类型{pai: otherIndex, pai: otherIndex ...}
DA_MING_GANG_S = "daMingGangs"
# 暗杠的牌 类型[pai, pai...]
AN_GANG_S = "anGangs"
# 打出的牌，不包括打出被别人用掉的牌
OUT_PAIS = "outPais"
# 所在位置
SEAT = "seat"
# 位置到玩家的映射
SEAT_TO_PLAYER = "seatToPlayer"
# 庄家位置
BANKER_LOCATION = "bankerLocation"
# 操作次数
OPT_COUNT = "optCount"
# 玩家不能胡的牌，每次发牌清空
NOT_HU_PAI = "notHuPai"
# 玩家不能碰的牌，每次发牌清空
NOT_PENG_PAI = "notPengPai"
# 允许客户端的操作
ALLOW_OPT = "allowOpt"
# 牌型
PAI_TYPES = "paiTypes"
# 同意或拒接解散房间, -1:表示未选择;0:拒绝;1:同意
IS_ARGEE = "isArgee"
#  外挂，下次发牌想要的牌；-1：为默认，正常发牌
WAI_GUA_SELECT_PAI = "waiGuaSelectPai"
# 玩家的检查结果，用于重连
CHECK_RESULT = "checkResult"
# 玩家点炮别人的次数
DIAN_PAO_COUNT = "dianPaoCount"
# --------------------------------------------------------------------------------------------
#                            全局统计数据
# --------------------------------------------------------------------------------------------
SD_BIG_WINNER_INDEX = "bigWinnerIndex"
SD_PLAYERS = "players"
SD_LOCATION_INDEX = "locationIndex"
SD_USER_ID = "userId"
SD_ENTITY_ID = "entityId"
SD_NAME = "name"
SD_ZI_MO_COUNT = "ziMoCount"
SD_DIAN_PAO_COUNT = "dianPaoCount"
SD_FANG_PAO_COUNT = "fangPaoCount"
SD_AN_GANG_COUNT = "anGangCount"
SD_MING_GANG_COUNT = "mingGangCount"
SD_MO_HUA_COUNT = "moHuaCount"
SD_MING_CI_COUNT = 'mingCiCount'
SD_AN_CI_COUNT = 'anCiCount'
SD_PI_CI_COUNT = 'piCiCount'
SD_BAO_CI_COUNT = 'baoCiCount'
SD_XIA_MI_SCORE = 'xiaMiCount'
SD_XIA_MI_LOCATION_INDEX = 'xiaMiLocationIndex'
# --------------------------------------------------------------------------------------------
#                            客户端方法
# --------------------------------------------------------------------------------------------
# func: xmgOptPrompt args: []
CLIENT_FUNC_XIAOMINGGANG = "xmgOptPrompt"
# func: agOptPrompt args: []
CLIENT_FUNC_ANGANG = "agOptPrompt"
# func: zmhOptPrompt args: boolean
CLIENT_FUNC_ZIMOHU = "zmhOptPrompt"
# func: cOptPrompt args: []
CLIENT_FUNC_CHI = "cOptPrompt"
# func: pOptPrompt args: boolean
CLIENT_FUNC_PENG = "pOptPrompt"
# func: dmgOptPrompt args: boolean
CLIENT_FUNC_DAMINGGANG = "dmgOptPrompt"
CLIENT_FUNC_MING_CI_HU = 'mchOptPrompt'
CLIENT_FUNC_XIAO_MING_CI_HU = 'xmchOptPrompt'
CLIENT_FUNC_AN_CI_HU = 'achOptPrompt'
CLIENT_FUNC_PI_CI_HU = 'pchOptPrompt'
CLIENT_FUNC_TINGPAI = 'tpOptPrompt'
# func: dphOptPrompt args: boolean
CLIENT_FUNC_DIANPAOHU = "dphOptPrompt"
# func: qghOptPrompt args: boolean
CLIENT_FUNC_QIANGGANGHU = "qghOptPrompt"
# func: gOptPrompt args: 无
CLIENT_FUNC_GUO = "gOptPrompt"
# 提醒客户端出牌 func: notifyOutPai args:[],未完成
CLIENT_FUNC_NOTIFYOUTPAI = "notifyOutPai"

# 超时操作时间
AUTO_TIME = 15
# 超时解散时间
AUTO_DISSOLVE_TIME = 90
RESTART_TIME = 15
# 总结算清理倒计时
SETTLEMENT_CLEAR_PLAYERS_TIME = 30
# 离线出牌时间 or 过牌
WAIT_TIME_LEN_ON_PLAY_OFFLINE = 1
# --------------------------------------------------------------------------------------------
#                            定时器相关
# --------------------------------------------------------------------------------------------
TIMER = "timer"
# 机器人自动出牌定时起
BOT_OUT_PAI_TIMER = "botOutPaiTimer"
# 响应出牌机器人自动吃碰杠胡定时器
INNER_BOT_OPT_TIMERS = "innerBotOptTimers"
# 离线玩家的定时器
ON_LFTE_PLAYER = 2


# # 吃和碰之后，出牌超时定时器
# CP_OUT_PAI_TIMER = "chiPengOutPaiTimer"
# # 吃和碰之后，机器人出牌定时器
# BOT_CP_OUT_PAI_TIMER = "botChiPengOutPaiTimer"


class RoomType5(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)
        self.wait_to_seat = []

    # --------------------------------------------------------------------------------------------
    #                            父类方法
    # --------------------------------------------------------------------------------------------
    def newChapter(self, maxPlayerCount=100):
        """
        :param maxPlayerCount:
        :return:
        """
        _chapter = RoomBase.newChapter(self, maxPlayerCount)
        # 牌局所有计时器id
        _chapter["timers"] = {  # 牌局主计时器
            "main": -1,  # 机器人下注计时器
            "botBet": -1, }
        _chapter[CUR_PLAYER] = None
        _chapter[WAIT_PLAYER] = None
        _chapter[PLAYER_OUT_GAME] = {}
        _chapter[CUR_PAI] = None
        _chapter[CHECK_RESULTS] = None
        _chapter[HU_PLAYER] = None
        _chapter[FANG_PAO_INDEX] = -1
        _chapter[SEAT] = list(range(self.info['maxPlayersCount']))
        _chapter[CI_CARD] = -1
        _chapter[SEAT_TO_PLAYER] = {}
        _chapter[BANKER_LOCATION] = 1
        _chapter[ROUND] = []
        _chapter[ALLOW_OPT_PLAYERS] = []
        _chapter[IS_QIANG_GANG_HE] = False
        _chapter[IS_DIAN_PAO__HE] = False
        _chapter[IS_AN_CI_HE] = False
        _chapter[IS_MING_CI_HE] = False
        _chapter[IS_XIAO_MING_CI_HE] = False
        _chapter[IS_PI_CI_HE] = False
        _chapter[IS_ZI_MO_HE] = False
        _chapter[IS_HUANG_ZHUANG] = False
        _chapter[IS_GANG_SHANG_KAI_HUA] = False
        # 定时器相关
        _chapter[BOT_OUT_PAI_TIMER] = -1
        _chapter['resOutPaiTimer'] = -1
        _chapter['settlementTimer'] = -1
        _chapter['autoReadyTimer'] = -1
        _chapter['startBaoCi'] = False
        _chapter['baoCiPlayer'] = None
        _chapter['deadLine'] = -1
        _chapter['dissolveDeadLine'] = -1
        _chapter['playCardTimer'] = -1
        _chapter['restartTimer'] = -1
        _chapter['xiaMiInfo'] = {}
        _chapter['settlementClearPlayers'] = -1
        _chapter[INNER_BOT_OPT_TIMERS] = {}
        _chapter[LEFT_PAI_COUNT] = -1
        _chapter['dissolveTimer'] = -1
        _chapter[ROOM_MASTER] = None
        _chapter['replay'] = []
        _chapter[HU_TYPE] = -1
        if self.cn == 0:
            _chapter['timers']["main"] = self.addTimer(1, 0.5, 0)
        return _chapter

    def onEnter(self, accountEntityId):
        """
        all--->cell
        进入房间
        """
        if not RoomBase.onEnter(self, accountEntityId):
            return
        _info = self.info
        _chapter = self.chapters[self.cn]
        _accountEntity = KBEngine.entities[accountEntityId]
        _accountEntity.info['isReady'] = False
        _accountEntity.viewing_hall = False
        _accountEntities = self.accountEntities
        DEBUG_MSG('[Room id %i]------->onEnter account = %i.' % (self.id, _accountEntity.id))
        # 此处增加从房间断开的玩家再次进入的处理逻辑
        # 相同实体不能重复登入房间
        if _accountEntity.id in _accountEntities.keys():
            return
        _accountEntities[accountEntityId] = _accountEntity
        # 一个新玩家生成的流程
        _player = self.newPlayer(_accountEntity)
        DEBUG_MSG('newPlayer %s' % _player)
        # 如果是此房间第一个玩家进入，默认为房主
        if len(_chapter[PLAYER_IN_GAME]) == 1:
            _chapter[ROOM_MASTER] = _player
        if _accountEntity.info["isBot"] == 0:
            self.reqRoomBaseInfo(accountEntityId)

        if _chapter['chapterState'] == 0 and len(_chapter[SEAT]) != 0 and not self.started:
            if len(_chapter[PLAYER_IN_GAME]) < _info["maxPlayersCount"]:
                # 通知所有客户端座位信息
                self.retChapterSysPrompt("玩家" + _accountEntity.info["name"] + "进入房间")
                self.set_seat(_player)
                self.ret_player_in_room_info()
                # 加入到统计数据
                self.addPlayerInSD(_player)
                # 广播金币
                self.retGolds()
                _accountEntity.update_player_stage(Account.PlayerStage.NO_READY)
                self.notify_viewing_hall_players_room_info()
        else:
            self.set_witness(_player)
            self.ret_player_out_game_info()
            self.reconnection(accountEntityId)
            _accountEntity.update_player_stage(Account.PlayerStage.WATCHING)

        # 每人满时，创建新的房间(onRoomEnd为true时插入在当前房间后面)
        if _chapter["playersCount"] == self.info['maxPlayersCount']:
            self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})

    def onLeave(self, accountEntityId, leave_param=None):
        """
        all--->cell
        离开房间
        """
        # 检测参数合法性
        _accountEntities = self.accountEntities
        if accountEntityId not in _accountEntities.keys():
            return
        _chapter = self.get_current_chapter()
        _player = self.get_player_by_entity_id(accountEntityId)
        _player_out_game = _chapter[PLAYER_OUT_GAME]
        # 如果游戏已开始，无法退出
        _chapter_state = self.get_current_chapter()["chapterState"]
        if _player:
            if _player[SEAT] == -1:
                if accountEntityId in _player_out_game and accountEntityId in self.wait_to_seat:
                    if _chapter_state != 0 and _chapter_state != 4:
                        self.callClientFunction(accountEntityId, 'Notice', ['已坐下，暂时无法离开房间'])
                        return
                self.remove_witness_player(_player)
            else:
                # 坐下的玩家只能在总结算或者准备阶段离开
                if _chapter_state != 0 and _chapter_state != 4:
                    if leave_param is None:
                        leave_param = {"inviteRoomInfo": None}
                    leave_param.update({"result": 0})
                    self.callClientFunction(accountEntityId, "LeaveRoomResult", leave_param)
                    return
                # 站起
                self.seat_up(_player)
                # 从所有玩家中移除
                self.remove_seat_player(_player)
                # 从统计数据中移除
                self.remove_player_from_sd(_player)
            # 广播金币
            self.retGolds()
            if leave_param is None:
                leave_param = {"inviteRoomInfo": None}
            leave_param.update({"result": 1})
            another_room = {}
            if 'JoinAnotherRoom' in leave_param:
                del leave_param['JoinAnotherRoom']
                another_room = leave_param['inviteRoomInfo']
                del leave_param['inviteRoomInfo']
            if another_room:
                self.callClientFunction(accountEntityId, "JoinAnotherRoom", another_room)

        self.callClientFunction(accountEntityId, "LeaveRoomResult", leave_param)
        # 通知所有客户端座位信息
        self.ret_player_out_game_info()
        # 通知所有客户端座位信息
        self.ret_player_in_room_info()
        # 移出房间
        _accountEntity = _accountEntities[accountEntityId]
        _accountEntities.pop(accountEntityId)
        self.base.cellToBase({"func": "LogoutRoom", "accountId": accountEntityId})
        _accountEntity.destroySelf()
        self.autoDestroy()
        if accountEntityId in self.wait_to_seat:
            self.wait_to_seat.remove(accountEntityId)
        if accountEntityId in self.agree_less_person_mode_players:
            self.agree_less_person_mode_players.remove(accountEntityId)
        # 如果是准备阶段，有玩家离开房间，重新排序座位
        if _chapter_state == 0:
            self.resort_location()
        self.notify_viewing_hall_players_room_info()
        DEBUG_MSG('[Room id %i]------->onLeave account = %i.' % (self.id, accountEntityId))

    def resort_location(self):
        """
        重新排序玩家座位
        :return:
        """
        _chapter = self.chapters[self.cn]
        new_players = _chapter[PLAYER_IN_GAME].copy()
        for p in new_players:
            self.seat_up(_chapter[PLAYER_IN_GAME][p])
        DEBUG_MSG('_chapter[SEAT]:%s' % _chapter[SEAT])
        DEBUG_MSG('_chapter[SEAT_TO_PLAYER]%s' % _chapter[SEAT_TO_PLAYER])
        DEBUG_MSG('_chapter[PLAYER_IN_GAME]%s' % _chapter[PLAYER_IN_GAME])
        new_players = _chapter[PLAYER_IN_GAME].copy()
        _chapter[PLAYER_IN_GAME].clear()
        for p in new_players:
            self.set_seat(new_players[p])
        self.statisticalData[SD_PLAYERS].clear()
        for p in _chapter[PLAYER_IN_GAME].values():
            self.addPlayerInSD(p)
        DEBUG_MSG('_chapter[SEAT]:%s' % _chapter[SEAT])
        DEBUG_MSG('_chapter[SEAT_TO_PLAYER]%s' % _chapter[SEAT_TO_PLAYER])
        DEBUG_MSG('_chapter[PLAYER_IN_GAME]%s' % _chapter[PLAYER_IN_GAME])

    def remove_want_seat_player(self, _player):
        if not _player:
            return
        _chapter = self.get_current_chapter()
        if _player['entity'].id in self.wait_to_seat:
            self.wait_to_seat.remove(_player['entity'].id)

    def remove_witness_player(self, _player):
        """
        移除观战玩家
        :param _player:
        :return:
        """
        if not _player:
            return
        _chapter = self.get_current_chapter()
        if _player['entity'].id in _chapter[PLAYER_OUT_GAME]:
            _chapter[PLAYER_OUT_GAME].pop(_player['entity'].id)

    def remove_seat_player(self, _player):
        """
        移除本局中一个坐下的玩家，并归还位置
        :param _player:
        :return:
        """

        _chapter = self.chapters[self.cn]
        _players = self.get_current_chapter()[PLAYER_IN_GAME]

        if _player:
            _locationIndex = _player["locationIndex"]
            _players.pop(_locationIndex)
            _chapter["playersCount"] -= 1
            # 通知base房间玩家人数变化
            self.base.cellToBase({"func": "playersCount", "count": _chapter["playersCount"]})
            DEBUG_MSG('[Room id%s] removePlayer locationIndex %s,players:%s' % (self.id, _locationIndex, _players))

    def set_witness(self, player):
        """
        设置观战玩家
        :param player:
        :return:
        """
        _chapter = self.chapters[-1]
        _chapter[PLAYER_OUT_GAME][player['entity'].id] = player

    def want_next_game_seat(self, account_id):
        """
        观战中下局可以开始游戏的玩家
        :param account_id:
        :return:
        """
        chapter = self.chapters[self.cn]
        # 1 在游戏中的人
        _playerInGame = chapter[PLAYER_IN_GAME]
        # 1 游戏中观战的人
        _playerOutGame = chapter[PLAYER_OUT_GAME]
        if account_id not in _playerOutGame:
            return
        if self.get_true_gold(account_id) < self.info['gameLevel']:
            self.callClientFunction(account_id, 'Notice', ['比赛币不足，无法坐下'])
            return
        if account_id in _playerOutGame:
            # 已经坐下
            if account_id in self.wait_to_seat:
                _args = {"result": 1}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                self.callOtherClientsFunction("NextGameCanSit", self.wait_to_seat)
                return

            if len(chapter[SEAT]) > len(self.wait_to_seat):
                _args = {"result": 1}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                self.wait_to_seat.append(account_id)
                self.callOtherClientsFunction("NextGameCanSit", self.wait_to_seat)
                self.get_player_entity(account_id).update_player_stage(Account.PlayerStage.PLAYING,
                                                                       self.max_chapter_count,
                                                                       self.current_chapter_count)
            else:
                _args = {"result": 0}
                self.callClientFunction(account_id, "wantNextGameSit", _args)
                return

    def set_seat(self, player, position=-1):
        """
        :param player: 要坐下的玩家
        :param position: 选择的位置，-1表示系统默认
        :return: -1 没坐下
        """
        _chapter = self.chapters[-1]
        _seats = _chapter[SEAT]
        if len(_seats) == 0:
            return -1
        p = -1
        if position == -1:
            p = _seats.pop(0)
        else:
            if position in _seats:
                p = position
                _seats.remove(position)
        if p == -1:
            return -1
        # _chapter[SEAT_TO_PLAYER][p] = player["locationIndex"]
        _chapter[SEAT_TO_PLAYER][p] = player
        player[SEAT] = p
        player['locationIndex'] = p
        _chapter[PLAYER_IN_GAME][p] = player
        # 移除观战以及等待加入
        self.remove_witness_player(player)
        self.remove_want_seat_player(player)
        return p

    def seat_up(self, player):
        """
        站起
        :param player: 玩家信息
        :return:
        """
        _chapter = self.chapters[-1]
        # 所有坐下玩家
        seat_to_player = _chapter[SEAT_TO_PLAYER]
        # 找到玩家座位
        seat = player[SEAT]
        if seat in seat_to_player.keys():
            _chapter[SEAT_TO_PLAYER].pop(seat)
            _chapter[SEAT].append(seat)
            _chapter[SEAT].sort()
            player[SEAT] = -1

    def newPlayer(self, accountEntity, total_gold_change=0, base_sync_gold_change=0):
        """
        :param total_gold_change: 每局结束后，获得上局的总金币变化
        :param accountEntity:
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter[PLAYER_IN_GAME]
        # 此用户如果已在牌局内 结束方法
        for i in _players.values():
            if i["entity"].id == accountEntity.id:
                return None
        # 创建牌局玩家 并分配一个座位
        # 玩家牌局中的初始金币数 默认为玩家账户中的总金币数
        _gold = 0
        if self.info["roomType"] == "card":
            _gold = 0
        elif self.info["roomType"] == "gameCoin":
            _gold = accountEntity.accountMutableInfo["gameCoin"]
        DEBUG_MSG('new player totalGoldChange %s' % total_gold_change)
        _player = {'locationIndex': -1, 'entity': accountEntity, 'isReady': False, 'cards': [], 'winnerBilling': 0,
                   'otherBilling': 0, 'overBilling': 0, 'continue': False, 'totalGoldChange': total_gold_change,
                   # 房间外上币统计
                   'baseSyncGoldChange': base_sync_gold_change,  # 是否已经扣过AA支付的钻石
                   'AARoomCardConsumed': False}
        # 钻石场
        if self.info["roomType"] == "card":
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 比赛分场
        elif self.info["roomType"] == "gameCoin":
            # 比赛分场修改使用比赛分为使用金币
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 普通比赛分场
        elif self.info['roomType'] == 'normalGameCoin':
            _player["gold"] = accountEntity.accountMutableInfo["gold"]

        _chapter["playersCount"] += 1
        # 通知base房间玩家人数变化
        self.base.cellToBase({"func": "playersCount", "count": _chapter["playersCount"]})
        # DEBUG_MSG('[Room id%s] newPlayer locationIndex %s' % (self.id, _locationIndex))

        _player[DAN_FANG] = -1
        _player[CHIS] = {}
        _player[PENG_S] = {}
        _player[XIAO_MING_GANG_S] = collections.OrderedDict()
        _player[DA_MING_GANG_S] = collections.OrderedDict()
        _player[AN_GANG_S] = []
        _player[OUT_PAIS] = []
        _player[SEAT] = -1
        _player[OPT_COUNT] = 0
        _player[HUA_PAI] = []
        _player[HUA_COUNT] = 0
        _player[NOT_HU_PAI] = []
        _player[NOT_PENG_PAI] = []
        _player[CAN_HU] = False
        _player[QI_HU] = False
        _player[CAN_PENG] = False
        _player[WIN_CI] = False
        _player[IS_TING] = False
        _player[TIMER] = -1
        _player[ALLOW_OPT] = 0
        _player['goldChange'] = 0
        _player[PAI_TYPES] = []
        _player['anGangGold'] = 0
        _player['mingGangGold'] = 0
        _player['ziMoGold'] = 0
        _player['xiaMiGold'] = 0
        _player['anCiGold'] = 0
        _player['mingCiGold'] = 0
        _player['piCiGold'] = 0
        _player[IS_ARGEE] = -1
        _player[WAI_GUA_SELECT_PAI] = -1
        _player[CHECK_RESULT] = None
        _player[DIAN_PAO_COUNT] = 0
        accountEntity.player = _player
        # 自动出牌
        _player["autoPlayCard"] = False
        _player["allowAutoPlayCheck"] = False
        return _player

    def newStatisticalData(self):
        """
        全局数据
        :return:
        """
        self.statisticalData = {SD_BIG_WINNER_INDEX: -1, SD_PLAYERS: {}}

    def global_data(self, players):
        """
        累计全局数据
        :param players: 本局游戏中的玩家
        :return:
        """
        _chapter = self.get_current_chapter()
        sd_players = self.statisticalData[SD_PLAYERS]
        if _chapter[IS_ZI_MO_HE]:
            if len(_chapter[HU_PLAYER]) == 1:
                if _chapter[HU_PLAYER][0]['locationIndex'] in sd_players.keys():
                    sd_players[_chapter[HU_PLAYER][0]['locationIndex']][SD_ZI_MO_COUNT] += 1
        else:
            if _chapter[FANG_PAO_INDEX] in sd_players.keys():
                sd_players[_chapter[FANG_PAO_INDEX]][SD_FANG_PAO_COUNT] += 1
            for hp in _chapter[HU_PLAYER]:
                if hp['locationIndex'] in sd_players.keys():
                    sd_players[hp['locationIndex']][SD_DIAN_PAO_COUNT] += 1

        for player in players:
            if player['locationIndex'] in sd_players:
                sd_player = sd_players[player['locationIndex']]
                sd_player[SD_AN_GANG_COUNT] += len(player[AN_GANG_S])
                sd_player[SD_MING_GANG_COUNT] += (len(player[DA_MING_GANG_S]) + len(player[XIAO_MING_GANG_S]))
                sd_player[SD_MO_HUA_COUNT] += len(player[HUA_PAI])
                DEBUG_MSG('global_data hu_player%s' % _chapter[HU_PLAYER])
                if self.is_player_in_players(player, _chapter[HU_PLAYER]):
                    sd_player[SD_AN_CI_COUNT] += 1 if _chapter[IS_AN_CI_HE] else 0
                    sd_player[SD_MING_CI_COUNT] += 1 if _chapter[IS_MING_CI_HE] else 0
                    sd_player[SD_MING_CI_COUNT] += 1 if _chapter[IS_XIAO_MING_CI_HE] else 0
                    sd_player[SD_PI_CI_COUNT] += 1 if _chapter[IS_PI_CI_HE] else 0

                # 如果包次开始了，点炮的玩家包次次数加一
                if _chapter['baoCiPlayer'] and player['locationIndex'] == _chapter['baoCiPlayer']['locationIndex']:
                    sd_player[SD_BAO_CI_COUNT] += 1 if _chapter['startBaoCi'] else 0

                sd_player[SD_XIA_MI_SCORE] += player['xiaMiGold']

        w = -1
        t = 0
        for k, v in sd_players.items():
            if v[SD_ZI_MO_COUNT] + v[SD_DIAN_PAO_COUNT] > t:
                t = v[SD_ZI_MO_COUNT] + v[SD_DIAN_PAO_COUNT]
                w = k
        self.statisticalData[SD_BIG_WINNER_INDEX] = w

    def addPlayerInSD(self, player):
        """
        :param player:
        :return:
        """
        sd = self.statisticalData
        DEBUG_MSG('[RoomType5 id %i]------->addPlayerInSD player:%s.' % (self.id, player))
        sd[SD_PLAYERS][player['locationIndex']] = {SD_LOCATION_INDEX: player['locationIndex'],
                                                   SD_USER_ID: player["entity"].info["userId"],
                                                   SD_ENTITY_ID: player["entity"].id,
                                                   # SD_NAME: player["entity"].name,
                                                   SD_ZI_MO_COUNT: 0, SD_DIAN_PAO_COUNT: 0, SD_FANG_PAO_COUNT: 0,
                                                   SD_AN_GANG_COUNT: 0, SD_AN_CI_COUNT: 0,
                                                   SD_PI_CI_COUNT: 0, SD_MING_CI_COUNT: 0, SD_MING_GANG_COUNT: 0,
                                                   SD_MO_HUA_COUNT: 0, SD_XIA_MI_SCORE: 0,
                                                   SD_BAO_CI_COUNT: 0}

    def remove_player_from_sd(self, player):
        """
        把玩家数据从全局统计删除
        :param player:
        :return:
        """
        sd = self.statisticalData
        players = sd[SD_PLAYERS]
        if player['locationIndex'] in players.keys():
            players.pop(player['locationIndex'])

    def on_player_ready(self, entityId, ready=True):
        """
        client---->cell
        :param entityId:
        :return:
        """
        _chapter = self.chapters[self.cn]
        # 只有准备阶段可以准备
        if _chapter["chapterState"] != 0 and _chapter["chapterState"] != 3:
            return
        # 如果是比赛场,准备时金币不能小于指定值
        if self.info["roomType"] == "gameCoin" and self.get_true_gold(entityId) < self.info['readyGoldLimit'] and ready:
            self.callClientFunction(entityId, 'Notice', ['您的比赛分不足,请您立即充值.'])
            info_args = {"accountId": entityId}
            self.callOtherClientsFunction("ScoreIsLess", info_args)
            if self.ready_gold_disband_timer == -1 and not self.is_forbid_disband_room():
                self.debug_msg("addTimer ready_gold_disband_timer")
                self.ready_gold_disband_timer = self.addTimer(120, 0, 0)
            return
        _players = _chapter[PLAYER_IN_GAME]
        _player = self.get_seat_player_by_entity_id(entityId)
        account_entity = KBEngine.entities[entityId]
        _playersCount = len(_chapter[PLAYER_IN_GAME])
        _chapterState = _chapter["chapterState"]
        if not _player:
            return
        _player["isReady"] = ready
        account_entity.info['isReady'] = ready
        # 同步准备消息
        self.syncReadyMsg(_player, ready)
        # 一人不能开始
        if _playersCount <= 1:
            return
        # 少人模式不判断是否大于最大人数
        if not self.is_less_mode and _playersCount < self.info["maxPlayersCount"]:
            return
        _flag = True
        for i in _players.values():
            if not i["isReady"]:
                _flag = False
                break
        if _flag:
            self.changeChapterState(1)

    def check_chapter_start(self):
        """
        检查牌局是否可以开始
        :return:
        """
        _chapter = self.get_current_chapter()
        _timers = _chapter["timers"]
        _players = _chapter[PLAYER_IN_GAME]
        _playersCount = len(_chapter[PLAYER_IN_GAME])
        # 判断牌局是否可以开始
        if _playersCount < self.info["maxPlayersCount"]:
            return
        _flag = True
        for i in _players.values():
            if not i["isReady"]:
                _flag = False
                break
        if _flag:
            self.delTimer(_timers["main"])
            _timers["main"] = -1
            self.changeChapterState(1)

    def syncReadyMsg(self, player, ready):
        """
        同步准备和取消准备消息
        :return:
        """
        self.callOtherClientsFunction("syncReadyMsg", {"locationIndex": player['locationIndex'], "ready": ready})

    # --------------------------------------------------------------------------------------------
    #                            牌局流程
    # --------------------------------------------------------------------------------------------

    def changeChapterState(self, state):
        """
        流程控制
        :param state:0准备阶段，1发牌，2打牌，3结算
        :return:
        """
        _chapter = self.chapters[self.cn]
        _timers = _chapter["timers"]
        _old = _chapter["chapterState"]
        _players = _chapter[PLAYER_IN_GAME]
        # 状态切换
        if _old == -1 and state == 0:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType5 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])

            # 让等待坐下的人坐下
            wait_to_seat_copy = self.wait_to_seat.copy()
            for k in wait_to_seat_copy:
                _player = self.get_player_by_entity_id(k)
                if not _player:
                    continue
                # 如果有空位
                if len(_chapter[SEAT]) != 0:
                    self.set_seat(_player)
                    self.ret_player_in_room_info()
                    # 加入到统计数据
                    self.addPlayerInSD(_player)
                    # 广播金币
                    self.retGolds()
                    self.sync_gold()

            # for k, v in _players.items():
            #     self.on_player_ready(v['entity'].id)

        elif (_old == 0 and state == 1) or (_old == 3 and state == 1):
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType5 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])
            if self.cn == 0:
                # 首局创建者为庄家
                for p in _players.values():
                    if p['entity'].info["dataBaseId"] == self.info['creator']:
                        _chapter[BANKER_LOCATION] = p['locationIndex']
                        break
            # 关闭自动准备计时器
            self.delTimer(_chapter['autoReadyTimer'])
            _chapter['autoReadyTimer'] = -1
            # 通知base游戏开始
            self.sendChapterStartMsgToBase()
            # 同步局数
            self.syncChapterNum(self.cn + 1)
            # 同步庄家
            self.sync_banker_index(_chapter[BANKER_LOCATION])
            # 开启下米时，同步下米信息
            if self.xia_mi_switch():
                self.sync_xia_mi_info()

            self.new_cards_lib(has_feng=self.dai_feng_switch())
            # 初始化手牌
            self.chapter_start()
        elif _old == 1 and state == 2:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType5 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])

            # 打牌阶段
            self.init_round()
        elif _old == 2 and state == 3:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType5 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])

            # 结算
            self.settlement()
            for k, v in _players.items():
                self.on_player_ready(v['entity'].id, False)
            if self.info["maxChapterCount"] == self.cn + 1:
                # 如果牌局结束 cn从0开始
                # 给base发送房间结束消息，并发送得分信息
                self.total_settlement()
                return
            else:
                self.delTimer(_chapter['playCardTimer'])
                _chapter['playCardTimer'] = -1

                self.delTimer(_chapter['resOutPaiTimer'])
                _chapter['resOutPaiTimer'] = -1

                # _chapter['restartTimer'] = self.addTimer(RESTART_TIME, 0, 0)
                self.start_next_chapter()
                self.sync_timer_count_down(RESTART_TIME)
                _chapter['deadLine'] = time.time() + RESTART_TIME
        elif state == 4:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType5 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])

        else:
            # 不存在的状态切换  抛出异常
            raise Exception('error in changeChapterState, oldState=%s, state=%s' % (_old, state))

    def sendChapterStartMsgToBase(self):
        chapter_start_msg = {"cn": self.cn}
        self.base.cellToBase({"func": "chapterStart", "args": chapter_start_msg})

    def send_chapter_end_msg_to_base(self):
        """
        发送牌局结束信息
        :return:
        """
        chapter_end_msg = {"cn": self.cn}
        self.base.cellToBase({"func": "chapterEnd", "args": chapter_end_msg})

    # 1 分享到微信
    def share_to_wx(self, account_id):
        if self.info['roomType'] == 'card':
            title = '杠次房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '杠次房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '杠次房间'
        ying_ci = '硬次' if self.info['softOrHardCi'] == 0 else '软次'
        chapter_count = '局数' + str(self.info['maxChapterCount'])
        max_chapter_count = str(self.info['maxPlayersCount']) + '人局'
        con = str('%s,%s,%s' % (ying_ci, chapter_count, max_chapter_count))
        self.callClientFunction(account_id, 'ShareToWX', {'title': title, 'content': con})

    def settlement(self):
        """
        结算
        :return:
        """
        _chapter = self.get_current_chapter()
        players = self.get_all_players_by_seat()
        hu_players = _chapter[HU_PLAYER]

        no_hu_players = []
        for p in players:
            p["isReady"] = False
            if not self.is_player_in_players(p, hu_players):
                no_hu_players.append(p)
                self.set_losing_streak_history(p, True)
            else:
                self.set_losing_streak_history(p, False)

        if _chapter[IS_HUANG_ZHUANG]:
            pass

        if not _chapter[IS_HUANG_ZHUANG]:
            for hu_player in hu_players:
                DEBUG_MSG("[RoomType5] settlement HU_TYPE=%s" % _chapter[HU_TYPE])
                # 扣次分的玩家
                ci_fen_range = []
                item_name = ''
                # 皮次，扣所有人的次分
                if _chapter[IS_PI_CI_HE]:
                    ci_fen_range = no_hu_players
                    item_name = 'piCiGold'
                    self.settlement_xia_mi()
                # 暗次，扣所有人的次分
                elif _chapter[IS_AN_CI_HE]:
                    ci_fen_range = no_hu_players
                    item_name = 'anCiGold'
                    self.settlement_xia_mi()
                # 明次，扣所有人的次分
                elif _chapter[IS_MING_CI_HE] or _chapter[IS_XIAO_MING_CI_HE]:
                    # 如果是包次阶段的大明杠次，扣三次点次人的次分
                    if _chapter['startBaoCi'] and _chapter[IS_MING_CI_HE]:
                        ci_fen_range = []
                        _bao_ci_player = self.get_bao_ci_player(hu_player)
                        if _bao_ci_player:
                            for _p in no_hu_players:
                                ci_fen_range.append(_bao_ci_player)
                            item_name = 'mingCiGold'
                            _chapter['baoCiPlayer'] = _bao_ci_player
                    else:
                        ci_fen_range = no_hu_players
                        item_name = 'mingCiGold'
                    self.settlement_xia_mi()

                # 自摸，扣所有人自摸分
                elif _chapter[IS_ZI_MO_HE]:

                    for _p in no_hu_players:
                        zi_mo_fen = self.info['ziMo']
                        # 如果庄加倍，不管庄家输赢,自摸分翻倍
                        if self.zhuang_jia_bei():
                            if hu_player['locationIndex'] == _chapter[BANKER_LOCATION] or _p['locationIndex'] == \
                                    _chapter[BANKER_LOCATION]:
                                zi_mo_fen = 2 * self.info['ziMo']

                        _p['goldChange'] -= zi_mo_fen
                        hu_player['goldChange'] += zi_mo_fen
                        _p['ziMoGold'] -= zi_mo_fen
                        hu_player['ziMoGold'] += zi_mo_fen

                # 扣次分
                for _p in ci_fen_range:
                    # 皮次也算杠分
                    if _chapter[IS_PI_CI_HE]:
                        ci_fen = self.info['ciDi'] + self.info['gangDi']
                    else:
                        ci_fen = self.info['ciDi']

                    # 如果庄加倍，不管庄家输赢,次分翻倍
                    if self.zhuang_jia_bei():
                        if hu_player['locationIndex'] == _chapter[BANKER_LOCATION] or _p['locationIndex'] == _chapter[
                            BANKER_LOCATION]:
                            if _chapter[IS_PI_CI_HE]:
                                ci_fen = 2 * self.info['ciDi'] + self.info['gangDi']
                            else:
                                ci_fen = 2 * self.info['ciDi']

                    _p['goldChange'] -= ci_fen
                    hu_player['goldChange'] += ci_fen
                    _p[item_name] -= ci_fen
                    hu_player[item_name] += ci_fen

            # 扣多少杠分
            gang_di = self.info['gangDi']
            for _gang_p in _chapter[PLAYER_IN_GAME].values():
                # 扣大明杠分
                for i in _gang_p[DA_MING_GANG_S].values():
                    _p = self.get_player_by_location(i)
                    _p['goldChange'] -= gang_di
                    _gang_p['goldChange'] += gang_di
                    _p['mingGangGold'] -= gang_di
                    _gang_p['mingGangGold'] += gang_di

                # 扣小明杠分
                for i in _gang_p[XIAO_MING_GANG_S].values():
                    _p = self.get_player_by_location(i)
                    _p['goldChange'] -= gang_di
                    _gang_p['goldChange'] += gang_di
                    _p['mingGangGold'] -= gang_di
                    _gang_p['mingGangGold'] += gang_di

                # 所有暗杠
                for k in _gang_p[AN_GANG_S]:
                    # 其他玩家
                    for _p in _chapter[PLAYER_IN_GAME].values():
                        if self.is_same_player(_p, _gang_p):
                            continue
                        _p['goldChange'] -= gang_di
                        _gang_p['goldChange'] += gang_di
                        _p['anGangGold'] -= gang_di
                        _gang_p['anGangGold'] += gang_di

        else:
            _banker_index = _chapter[BANKER_LOCATION]
            if _banker_index not in _chapter['xiaMiInfo'].keys():
                _chapter['xiaMiInfo'][_banker_index] = 1
            else:
                _chapter['xiaMiInfo'][_banker_index] += 1
            DEBUG_MSG('xiamiinfo %s' % _chapter['xiaMiInfo'])

        # 赋值总金币改变
        for _p in players:
            _p['totalGoldChange'] += _p['goldChange']
            _p["entity"].update_score_control(_p['goldChange'])
            DEBUG_MSG('RoomType5 settlement totalGoldChange%s' % _p['totalGoldChange'])

        # 封装牌局结算消息
        end_msg = []
        for p in players:
            pm = {"locationIndex": p['locationIndex'], "shouPai": p[SHOU_PAI], "anGangs": p[AN_GANG_S],
                  'ciDi': self.info['ciDi'], 'ciCard': _chapter[CI_CARD], "pengs": list(p[PENG_S].keys()),
                  "xiaoMingGangs": list(p[XIAO_MING_GANG_S].keys()), "daMingGangs": list(p[DA_MING_GANG_S].keys()),
                  'anGangGold': p['anGangGold'], 'mingGangGold': p['mingGangGold'], 'ziMoGold': p['ziMoGold'],
                  'xiaMiGold': p['xiaMiGold'], "goldChange": p['goldChange'],
                  "isHu": self.is_player_in_players(p, hu_players),
                  "huType": _chapter[HU_TYPE]}
            end_msg.append(pm)
        DEBUG_MSG('[RoomType5 id %i]------------->chapterEnd end_msg=%s' % (self.id, end_msg))
        for p in players:
            self.callClientFunction(p["entity"].id, "chapterEnd", end_msg)

        # 如果是AA支付，扣除钻石
        if self.info['payType'] == Const.PayType.AA:
            # 需要扣除钻石的玩家
            need_consume_player = []
            # 如果坐下的玩家有没有扣除过AA支付钻石的，结算时扣除
            for k, v in _chapter[PLAYER_IN_GAME].items():
                if not v['AARoomCardConsumed']:
                    need_consume_player.append(v["entity"].info["userId"])
                    v['AARoomCardConsumed'] = True
            if len(need_consume_player) != 0:
                self.base.cellToBase({'func': 'AAPayTypeModifyRoomCard', 'needConsumePlayers': need_consume_player})

        # 统计全局数据
        self.global_data(players)
        self.sync_gold()
        self.settlement_count += 1
        if self.settlement_count == 1:
            self.base.cellToBase({'func': 'addTodayRoom'})

    def settlement_xia_mi(self):
        """
        结算下米分数
        :return:
        """
        if not self.xia_mi_switch():
            return
        _chapter = self.get_current_chapter()
        _hu_player = _chapter[HU_PLAYER][0]
        for k, v in _chapter['xiaMiInfo'].items():
            xia_mi = self.info['xiaMi'] * v
            need_xia_mi = self.get_player_by_location(k)
            need_xia_mi['goldChange'] -= xia_mi
            need_xia_mi['xiaMiGold'] -= xia_mi
            _hu_player['goldChange'] += xia_mi
            _hu_player['xiaMiGold'] += xia_mi
        # 清除下米信息
        _chapter['xiaMiInfo'] = {}

    def total_settlement(self, is_disband=False):
        """
        发送房间结束
        :return:
        """
        if self.total_settlement_ed:
            return
        self.delete_all_timer()
        self.changeChapterState(4)
        self.total_settlement_ed = True
        # 清除观战玩家
        self.clear_witness_player()
        chapter = self.get_current_chapter()
        _plays = chapter[PLAYER_IN_GAME]

        sd = self.statisticalData
        room_end_msg = {"winnerIndexes": -1, "players": []}
        # 收集统计数据
        for sdp in sd[SD_PLAYERS].values():
            room_end_msg["players"].append({"locationIndex": sdp[SD_LOCATION_INDEX], "ziMoCount": sdp[SD_ZI_MO_COUNT],
                                            "anGangCount": sdp[SD_AN_GANG_COUNT], 'anCiCount': sdp[SD_AN_CI_COUNT],
                                            'mingCiCount': sdp[SD_MING_CI_COUNT], 'piCiCount': sdp[SD_PI_CI_COUNT],
                                            "mingGangCount": sdp[SD_MING_GANG_COUNT],
                                            'xiaMiScore': sdp[SD_XIA_MI_SCORE],
                                            'baoCiCount': sdp[SD_BAO_CI_COUNT], "moHuaCount": sdp[SD_MO_HUA_COUNT],
                                            "totalScore": _plays[sdp[SD_LOCATION_INDEX]]['totalGoldChange'],
                                            "dianPaoCount": sdp[SD_DIAN_PAO_COUNT]})
        room_end_msg["winnerIndexes"] = sd[SD_BIG_WINNER_INDEX]
        room_end_msg['isDisband'] = is_disband
        players = self.get_all_players_by_seat()
        DEBUG_MSG('[RoomType5 id %i]------------->totalSettlement msg=%s' % (self.id, room_end_msg))

        for p in players:
            self.callClientFunction(p["entity"].id, "totalSettlement", room_end_msg)
        self.base.cellToBase({"func": "totalSettlementEd"})
        # 忽略判断，创建一个房间
        self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info, 'ignoreJudge': True, 'onRoomEnd': True})
        self.save_record_str()
        # 扣除额外积分，抽奖
        if self.info["roomType"] == "gameCoin" and self.settlement_count > 0:
            self.mj_lottery()

        # 同步金币变化到房间外
        for p in chapter[PLAYER_IN_GAME].values():
            # 同步金币到 base
            if self.info["roomType"] == "gameCoin":
                self.set_base_player_game_coin(p)
            else:
                self.set_base_player_gold(p)

        # 同步局数
        if self.is_tea_house_room and self.settlement_count >= 1:
            self.set_base_player_chapter_count()

        # 总结算清理玩家倒计时
        chapter["settlementClearPlayers"] = self.addTimer(SETTLEMENT_CLEAR_PLAYERS_TIME, 0, 0)
        chapter["deadline"] = time.time() + SETTLEMENT_CLEAR_PLAYERS_TIME

        self.write_chapter_info_to_db()
        self.write_chapter_replay()
        self.set_losing_streak_count_in_base(chapter[PLAYER_IN_GAME])
        self.set_day_good_pai_count_in_base(chapter[PLAYER_IN_GAME])

    def clear_witness_player(self):
        """
        清理观战玩家
        :return:
        """
        _player_out_game = self.get_current_chapter()[PLAYER_OUT_GAME]
        id = []
        for _p in _player_out_game.values():
            id.append(_p['entity'].id)
        for i in id:
            self.onLeave(i)

    def is_forbid_disband_room(self):
        """
        禁止中途解散房间
        """
        return self.info["canNotDisbandOnPlay"]

    def write_chapter_info_to_db(self):
        """
        牌局信息写入库
        :return:
        """
        # 至少打一局才写库
        if self.settlement_count < 1:
            return
        _chapter = self.chapters[self.cn]
        _playerInRoom = _chapter[PLAYER_IN_GAME]
        _playerData = {}
        _playerInfo = []
        _history_record = {}
        # 回放记录
        # 如果最后一局未到结算阶段，不计入战绩
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        for c in range(0, chapter_record_max_count):
            chapter_info = self.chapters[c]
            chapter_data = []
            # 回放的牌局所有信息
            for k, v in chapter_info[PLAYER_IN_GAME].items():
                player_data = {"goldChange": v["goldChange"], "name": v["entity"].info["name"]}
                chapter_data.append(player_data)
            _history_record[c] = chapter_data
        # 战绩记录
        # 记录战绩的玩家
        record_players = []
        for k, v in _playerInRoom.items():
            _playerData = {"accountId": v['entity'].id, "accountName": v["entity"].info["name"],
                           "winnerBilling": v["winnerBilling"], "overBilling": v["overBilling"],
                           "otherBilling": v["otherBilling"], "totalGoldChange": v["totalGoldChange"],
                           "userId": v["entity"].info["userId"]}
            _playerInfo.append(_playerData)
            record_players.append(v["entity"].info["userId"])
        _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                 "maxChapterCount": self.info["maxChapterCount"], "playerInfo": _playerInfo,
                 "historyRecord": _history_record}
        self.chapterInfo = _args
        self.base.cellToBase({"func": "writeChapterInfo", "chapterInfos": self.chapterInfo})
        if self.is_tea_house_room:
            # 通知base的冠名赛记录该房间
            self.base.cellToBase(
                {"func": "writeTeaHouseRoom", "teaHouseId": self.info["teaHouseId"], "type": self.info["type"],
                 'recordPlayers': record_players})
        DEBUG_MSG('[Room id %i]------>writeChapterInfoToDB, chapterInfo %s ' % (self.id, self.chapterInfo))

    def write_chapter_replay(self):
        _replay_data = {}

        # 如果最后一局未到结算阶段，不计入回放
        chapter_record_max_count = self.cn + 1 if self.settlement_count == self.cn + 1 else self.cn
        # 操作信息
        for c in range(0, chapter_record_max_count):
            _chapter = self.chapters[c]
            _player_seat = _chapter[SEAT_TO_PLAYER]
            _replay_data[c] = {}
            _replay_data[c]['replay'] = _chapter['replay']

            # 玩家信息
            player_info = {}
            for k, v in _player_seat.items():
                _player_location = v['locationIndex']
                # 获取总金币
                total_gold_change = v['totalGoldChange']
                _player = {"entityId": v["entity"].id, "locationIndex": int(v['locationIndex']),
                           "name": v["entity"].info["name"],
                           "userId": v["entity"].info["userId"],
                           'goldChange': v['goldChange'],
                           'gold': v['gold'] + total_gold_change + v['baseSyncGoldChange'],
                           "headImageUrl": v["entity"].info["headImageUrl"]}
                player_info[int(v['locationIndex'])] = _player
            _replay_data[c]['playerInfo'] = player_info
            _replay_data[c]['xiaMiInfo'] = _chapter['xiaMiInfo']
            _replay_data[c]['ciCard'] = _chapter[CI_CARD]

        self.chapter_replay = {'chapterInfo': _replay_data}
        self.base.cellToBase({"func": "writeChapterReplay", "chapterReplay": self.chapter_replay})

    def set_base_player_game_coin(self, _player):
        """
        设置玩家比赛分数量,通知base
        :param _player:
        :return:
        """
        if self.info['roomType'] != 'gameCoin':
            return
        DEBUG_MSG('set_base_player_game_coin')
        _chapter = self.chapters[self.cn]
        _player["entity"].base.cellToBase({"func": "setAccountTotalGoldChange", "dic": {
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1, 'type': 'gameCoin',
            "totalGoldChange": _player['totalGoldChange']}})

    def set_base_player_gold(self, _player):
        """
        设置玩家金币数量,通知base
        :param _player:
        :return:
        """
        if self.info['roomType'] != 'card' and self.info['roomType'] != 'normalGameCoin':
            return
        DEBUG_MSG('set_base_player_gold')

        _chapter = self.chapters[self.cn]
        _player["entity"].base.cellToBase({"func": "setAccountTotalGoldChange", "dic": {
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1, 'type': 'gold',
            "totalGoldChange": _player['totalGoldChange']}})

    # 统计局数
    def set_base_player_chapter_count(self):
        _chapter = self.chapters[self.cn]
        for k, v in _chapter[PLAYER_IN_GAME].items():
            v["entity"].base.cellToBase({"func": "AddChapterCount", "teaHouseId": self.info["teaHouseId"]})

    def delete_all_timer(self):
        """
        删除所有计时器
        :return:
        """
        _chapter = self.get_current_chapter()
        _timers = _chapter["timers"]

        self.delTimer(_timers['main'])
        _timers['main'] = -1

        self.delTimer(_chapter['playCardTimer'])
        _chapter['playCardTimer'] = -1

        self.delTimer(_chapter['resOutPaiTimer'])
        _chapter['resOutPaiTimer'] = -1

        self.delTimer(_chapter['dissolveTimer'])
        _chapter['dissolveTimer'] = -1

        self.delTimer(_chapter['settlementTimer'])
        _chapter['settlementTimer'] = -1

        self.delTimer(_chapter['restartTimer'])
        _chapter['restartTimer'] = -1

    def new_cards_lib(self, has_feng=False):
        """
        新建牌库
        :param has_feng:是否有风牌
        :return:
        """
        _chapter = self.chapters[self.cn]
        # 生成牌并打乱
        _l = list(range(0, 27))
        if has_feng:
            _l += list(range(27, 34))
        _l *= 4
        random.shuffle(_l)
        # _l += list(range(34, 42))
        player_num = self.info["maxPlayersCount"]
        i = 13 * player_num
        _head = _l[0:i]
        _tail = _l[i:]
        _l = _head + _tail
        # 随机一张次牌
        # 如果不次风或者没有风牌
        if self.bu_ci_feng() or not self.dai_feng_switch():
            _chapter[CI_CARD] = random.randint(0, 26)
        else:
            _chapter[CI_CARD] = random.randint(0, 33)

        # DEBUG_MSG('new_cards_lib _l%s' % _l)

        # 根据时间戳翻牌
        self.random_cards_with_time(_l)
        # 根据局数决定发牌顺序
        self.random_with_chapter_count(_l)
        DEBUG_MSG('new_cards_lib after random _l%s' % _l)

        # 将一张次牌放在最后
        for i, card in enumerate(_l):
            if card == _chapter[CI_CARD]:
                _l[i], _l[-1] = _l[-1], _l[i]
                break
        _chapter[CARDS_LIB] = _l
        _chapter[LEFT_PAI_COUNT] = len(_l)

    def random_cards_with_time(self, _chapter_lib):
        """
        牌随机，根据时间值，前X张牌,放在最后
        :param _chapter_lib:
        :return:
        """
        #  取当前时间
        msval = datetime.datetime.now().microsecond
        if msval > 1000:
            msval //= 1000
        pai_val = (msval % 10) + 10

        pull_pais = _chapter_lib[:pai_val]
        del _chapter_lib[:pai_val]
        _chapter_lib.extend(pull_pais)
        # DEBUG_MSG("len %s,chapter lib%s" % (len(_chapter_lib), _chapter_lib))

    def random_with_chapter_count(self, cards_lib: []):
        chapter = self.get_current_chapter()
        player_count = len(chapter[PLAYER_IN_GAME])
        delete_cards = []
        first_index = self.cn % player_count
        for i in range(player_count):
            cards = cards_lib[:13]
            del cards_lib[:13]
            if i == first_index:
                delete_cards = cards + delete_cards
            else:
                delete_cards = delete_cards + cards

        remain_cards = cards_lib[:]
        cards_lib.clear()
        cards_lib.extend(delete_cards)
        cards_lib.extend(remain_cards)

    def reconnection(self, accountEntityId):
        """
        :return:
        """
        _chapter = self.get_current_chapter()
        # 房间信息，位置信息，玩家信息
        self.callOtherClientsFunction("chapterStateChanged", [self.get_current_chapter()["chapterState"]])
        self.reqRoomBaseInfo(accountEntityId)
        self.ret_player_in_room_info(accountEntityId)
        players = _chapter[PLAYER_IN_GAME]
        player = self.get_player_by_entity_id(accountEntityId)
        _chapter_state = _chapter["chapterState"]

        dead_line = int(_chapter["deadLine"]) - int(time.time())
        dissolve_line = int(_chapter["dissolveDeadLine"]) - int(time.time())

        users = []
        for p in players.values():
            # 封装吃碰杠消息
            chis = []
            for k, v in p[CHIS].items():
                chis.append({"pai": k, "otherIndex": v[1]})
            pengs = []
            for k, v in p[PENG_S].items():
                pengs.append({"pai": k, "otherIndex": v})
            xmgs = []
            for k, v in p[XIAO_MING_GANG_S].items():
                xmgs.append({"pai": k, "otherIndex": v})
            dmgs = []
            for k, v in p[DA_MING_GANG_S].items():
                dmgs.append({"pai": k, "otherIndex": v})

            users.append({"locationIndex": p['locationIndex'], "cards": p[SHOU_PAI], "chis": chis, "pengs": pengs,
                          "xiaoMingGangs": xmgs, "daMingGangs": dmgs, "anGangs": p[AN_GANG_S], "huaPais": p[HUA_PAI],
                          "outPais": p[OUT_PAIS], "danFang": p[DAN_FANG], "onLine": not p['entity'].client_death,
                          'isReady': p['isReady'], 'disbandSender': self.disband_sender,
                          'agreeDisbanding': True if p[IS_ARGEE] == 1 else False, 'isDisbanding': self.is_disbanding,
                          'ciCard': _chapter[CI_CARD],
                          'deadLine': dissolve_line if self.is_disbanding else dead_line,
                          'canStartGame': self.wait_to_seat
                          })

        self.syncChapterNum(self.cn + 1)
        DEBUG_MSG('[RoomType5 id %s]------------->reconnection msg:%s' % (self.id, users))
        self.callClientFunction(accountEntityId, "reconnection", users)
        # 同步庄的位置
        self.sync_banker_index(_chapter[BANKER_LOCATION])
        # 同步计时器
        self.sync_timer_count_down(dead_line)
        # 开启下米时，同步下米信息
        if self.xia_mi_switch():
            self.sync_xia_mi_info()

        # 同步当前出牌的玩家
        if _chapter[CUR_PLAYER] is not None:
            self.callClientFunction(accountEntityId, "reconnSyncCurrentPlayerIndex",
                                    _chapter[CUR_PLAYER]['locationIndex'])
            # 如果可以，同步小明杠，暗杠，自摸胡操作
            if player[DAN_FANG] != -1:
                _shouPai = player[SHOU_PAI]
                _pengs = player[PENG_S]
                # 检查当前玩家的杠胡情况
                _xmg = check_xiao_ming_gang(_shouPai, _pengs)
                _ag = check_an_gang(_shouPai)
                can_pi_ci = check_pi_ci(_shouPai, _chapter[CI_CARD])
                _isHu = mj.AgariUtils.isHuPai(_shouPai)
                if _isHu:
                    # 设置当前玩家可以胡牌
                    player[CAN_HU] = True
                else:
                    player[CAN_HU] = False

                can_an_ci = False
                can_xiao_ming_ci = False
                # 出牌提示
                if len(_xmg) != 0:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_XIAOMINGGANG, _xmg)
                    if player[WIN_CI]:
                        can_xiao_ming_ci = True
                if len(_ag) != 0:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_ANGANG, _ag)
                    if player[WIN_CI]:
                        can_an_ci = True
                if _isHu:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_ZIMOHU, _isHu)
                if can_xiao_ming_ci:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_XIAO_MING_CI_HU, _xmg)
                if can_an_ci:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_AN_CI_HU, _ag)
                if can_pi_ci:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_PI_CI_HU, _ag)
                if len(_xmg) != 0 or len(_ag) != 0 or _isHu or can_pi_ci:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_GUO, "")
        if _chapter_state == 2:
            # 如果可以，同步吃，碰，大明杠，点炮胡操作
            if player[CHECK_RESULT] is not None:
                self.send_check_result_item(player[CHECK_RESULT])
        # 同步剩余牌的数量
        self.syncLeftPaiCount(_chapter[LEFT_PAI_COUNT])
        self.sync_gold()

    def send_check_result_item(self, cr):
        """
        发送玩家可以进行的操作
        :param cr:
        :return:
        """
        # 杠次没有吃操作
        # if len(cr[CHECK_CHI]) != 0:
        #     self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_CHI, cr[CHECK_CHI])
        if cr[CHECK_PENG]:
            self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_PENG, cr[CHECK_PENG])
        if cr[CHECK_DAMINGGANG]:
            self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_DAMINGGANG, cr[CHECK_DAMINGGANG])
        if cr[CHECK_HU_MING_CI]:
            self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_MING_CI_HU, cr[CHECK_HU_MING_CI])
        if cr[CHECK_HU]:
            self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_DIANPAOHU, cr[CHECK_HU])
        if cr[CHECK_HU_QIANG_GANG]:
            self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_QIANGGANGHU, cr[CHECK_HU_QIANG_GANG])
        self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_GUO, "")

    def randomCardFromLib(self):
        """
        :return:
        """
        _chapter = self.chapters[self.cn]
        _cardlib = _chapter["cardsLib"]
        _len = len(_cardlib)
        _index = random.randint(0, _len - 1)
        _card = _cardlib.pop(_index)
        return _card

    def on_no_card(self):
        """
        荒庄，荒庄胡牌的玩家列表为空
        :return:
        """
        # pai是空，荒庄
        _chapter = self.get_current_chapter()
        _chapter[IS_HUANG_ZHUANG] = True
        _chapter[HU_TYPE] = HU_TYPE_HUANG_ZHUANG
        # 同步荒庄消息
        self.syncOpt(-1, SYNCOPT_HUANGZHUANG, -1, -1)
        self.hu([])

    def get_card(self, r=False):
        """
        从牌库里拿出一张牌
        :param r:
        :return:
        """
        _chapter = self.chapters[self.cn]
        cards_lib = _chapter[CARDS_LIB]
        if len(cards_lib) <= 1:
            self.on_no_card()
            return
        _chapter[LEFT_PAI_COUNT] -= 1
        if r:
            _v = cards_lib[-1]
            cards_lib.pop(-1)
            # return convertCard(_v)[1]
            return _v
        else:
            _v = cards_lib[0]
            cards_lib.pop(0)
            # return convertCard(_v)[1]
            return _v

    def get_card_count_un_reveal(self, card, exclude_player=-1):
        """
        获取某张牌未揭示的数量(别人手牌中的数量+牌库中的数量)
        :param exclude_player: 排除玩家（排除该玩家手牌里的数量）
        :param card:
        :return:
        """
        count_in_lib = self.get_current_chapter()[CARDS_LIB].count(card)
        count_in_player = 0
        for p in self.get_current_chapter()[PLAYER_IN_GAME].values():
            if exclude_player != -1 and p['entity'].id == exclude_player:
                continue
            count_in_player += p[SHOU_PAI].count(card)
        return count_in_lib + count_in_player

    def get_wai_gua_card(self, pai):
        """
        拿到指定牌
        :param pai:
        :return:
        """
        _chapter = self.chapters[self.cn]
        cards_lib = _chapter[CARDS_LIB]
        if len(cards_lib) <= 1:
            self.on_no_card()
            return
        _chapter[LEFT_PAI_COUNT] -= 1

        # 如果外挂拿到的是次牌并且只有一张，则拿下一张
        if pai == _chapter[CI_CARD] and cards_lib.count(pai) == 1:
            _v = cards_lib[0]
            cards_lib.pop(0)
            return _v
        # 拿到指定牌
        elif pai in cards_lib:
            cards_lib.remove(pai)
            return pai
        # 如果没有指定牌拿到下一张牌
        else:
            _v = cards_lib[0]
            cards_lib.pop(0)
            return _v

    # --------------------------------------------------------------------------------------------
    #                            与客户端交互
    # --------------------------------------------------------------------------------------------

    def playerOperation(self, accountEntityId, jsonData):
        """
        :param accountEntityId:
        :param jsonData:
        :return:
        """
        DEBUG_MSG('RoomType5 playerOperation accountEntityId:%s jsonData:%s' % (accountEntityId, jsonData))
        _player, _operation_name, _args = RoomBase.playerOperation(self, accountEntityId, jsonData)
        # 检查是否应该此玩家操作
        _check_player = self.check_current_player(_player)
        if not _check_player:
            return
        # 检查该玩家的操作
        _check_opt = self.checkOperation(_player, _operation_name)
        if not _check_opt:
            return

        # 检查出牌操作
        if OPT_OUT == _operation_name:
            out_pai = _args[0]
            if out_pai not in _player[SHOU_PAI]:
                self.callClientFunction(_player['entity'].id, 'refreshChapter', {})
                return

        # 清空允许操作
        _player[ALLOW_OPT] = 0
        # 获取操作码
        opt_code = OPT_DICT[_operation_name]
        if opt_code & FA_PAI_AFTER_OPTS_CODE == opt_code:
            # 发牌之后的操作
            self.operation_after_deal_card(_player, _operation_name, _args)
        elif opt_code & OUT_PAI_AFTER_OPTS_CODE == opt_code:
            # 出牌之后其他玩家的响应操作
            self.operation_after_play_card(_player, _operation_name, _args)
        elif _operation_name == OPT_HU_QIANGGANG:
            # 特殊，抢杠和
            self.res_out_pai_qiang_gang_hu_opt(_player)
        elif _operation_name == OPT_HU_Ming_CI:
            self.res_out_pai_ming_ci_hu_opt(_player)
        elif _operation_name == OPT_HU_XIAO_MING_CI:
            self.xiao_ming_ci_hu_opt(_player, _args[0])
        elif _operation_name == OPT_HU_AN_CI:
            self.an_ci_hu_opt(_player, _args[0])
        elif _operation_name == OPT_HU_Pi_CI:
            self.pi_ci_hu_opt(_player)
        else:
            ""

    def operation_after_deal_card(self, _player, _operation_name, _args):
        """
        发牌之后可以进行的操作
        :param _player:
        :param _operation_name:
        :param _args:
        :return:
        """
        # 出牌
        if OPT_OUT == _operation_name:
            out_pai = _args[0]
            check_cards(out_pai)
            # 玩家操作，检查过参数之后，删除系统超时操作
            self.del_play_card_timer()
            # 设置不胡牌
            self.set_not_hu_pai(_player)
            # 清除杠上花标记
            self.clearFaiPaiDate()
            # 出牌操作
            self.play_card(_player, out_pai)
        elif OPT_XIAOMINGGANG == _operation_name:
            pai = _args[0]
            check_cards(pai)
            # 玩家操作，检查过参数之后，删除系统超时操作
            self.del_play_card_timer()
            self.set_not_hu_pai(_player)
            self.clearFaiPaiDate()
            self.xiao_ming_gang_opt(_player, pai)
        elif OPT_ANGANG == _operation_name:
            pai = _args[0]
            check_cards(pai)
            # 玩家操作，检查过参数之后，删除系统超时操作
            self.del_play_card_timer()
            self.set_not_hu_pai(_player)
            self.clearFaiPaiDate()
            self.an_gang_opt(_player, pai)
        elif OPT_HU_ZIMO == _operation_name:
            # 玩家操作，删除系统超时操作
            self.del_play_card_timer()
            self.zi_mo_hu_opt(_player)

    def operation_after_play_card(self, _player, _operation_name, _args):
        """
        出牌之后进行的操作
        :param _player:
        :param _operation_name:
        :param _args:
        :return:
        """
        # 所有可以操作的玩家 操作过，删除系统超时操作
        DEBUG_MSG('out_pai_after_operation operation_name %s' % _operation_name)
        _chapter = self.get_current_chapter()
        check_results = _chapter[CHECK_RESULTS]
        total = len(check_results)
        cur_count = 0
        for cr in check_results:
            if cr[CHECK_PLAYER_OPT] != NO_OPT:
                cur_count += 1
        if total == cur_count + 1:
            self.del_res_play_card_timer()

        if OPT_GUO == _operation_name:
            self.set_not_hu_pai(_player)
            self.setNotPengPai(_player)
            self.res_out_pai_guo_opt(_player)
        elif OPT_CHI == _operation_name:
            pai = _args[0]
            self.check_chi(pai)
            self.set_not_hu_pai(_player)
            self.res_out_pai_chi_opt(_player, pai)
        elif OPT_PENG == _operation_name:
            pai = _args[0]
            check_cards(pai)
            self.set_not_hu_pai(_player)
            # self.pengOpt(_player, pai)
            self.resOutPaiPengOpt(_player, pai)
        elif OPT_DAMINGGANG == _operation_name:
            pai = _args[0]
            check_cards(pai)
            self.set_not_hu_pai(_player)
            self.res_play_card_da_ming_gang_opt(_player, pai)
        elif OPT_HU_DIANPAO == _operation_name:
            pai = _args[0]
            self.res_out_pai_dian_pao_hu_opt(_player)

    def clientReq(self, accountEntityId, jsonData):
        """
        client---->cell
        :param accountEntityId:
        :param jsonData:
        :return:
        """
        _accountEntity, _func_name, _args = RoomBase.clientReq(self, accountEntityId, jsonData)
        DEBUG_MSG('clientReq accountEntityId%s,jsonData%s' % (accountEntityId, jsonData))
        if _func_name == "LeaveRoom":
            self.onLeave(accountEntityId, _args)
        elif _func_name == "ready":
            self.on_player_ready(accountEntityId)
            if self.get_seat_player_by_entity_id(accountEntityId)["isReady"]:
                self.get_player_entity(accountEntityId).update_player_stage(Account.PlayerStage.READY)
                self.notify_viewing_hall_players_room_info()
        elif _func_name == "cancelReady":
            self.on_player_ready(accountEntityId, ready=False)
            self.get_player_entity(accountEntityId).update_player_stage(Account.PlayerStage.NO_READY)
            self.notify_viewing_hall_players_room_info()
        elif _func_name == "NextGameSit":
            self.want_next_game_seat(accountEntityId)
        elif _func_name == "reqDissolve":
            if self.is_forbid_disband_room():
                self.callClientFunction(accountEntityId, 'Notice', ['该房间禁止中途解散'])
                return
            # 请求解散
            self.req_dissolve(accountEntityId)
        elif _func_name == "dissolveSelect":
            # 同意解散或拒绝解散
            self.dissolve_select(accountEntityId, _args)
        elif _func_name == "chat":
            # 广播给其他玩家
            _player = self.get_player_by_entity_id(accountEntityId)
            _args.append(_player['locationIndex'])
            self.callOtherClientsFunction("chat", _args)
        elif _func_name == 'EmotionChat':
            self.emotion_chat(accountEntityId, _args["index"], _args["type"])
        elif _func_name == "VoiceChat":
            self.voice_chat(accountEntityId, _args["url"])
        elif _func_name == "gift":
            # 广播给其他玩家
            _player = self.get_player_by_entity_id(accountEntityId)
            _args.append(_player['locationIndex'])
            self.callOtherClientsFunction("gift", _args)
        elif _func_name == "reconnection":
            self.reconnection(accountEntityId)
        elif _func_name == "getLeftPai":
            # left_pai = self.getLeftPai()
            # self.callOtherClientsFunction("retLeftPai", self.getCurChapter()[CARDSLIB])
            self.callClientFunction(accountEntityId, "retLeftPai", self.get_current_chapter()[CARDS_LIB])
        elif _func_name == "selectPai":
            _player = self.get_seat_player_by_entity_id(accountEntityId)
            _player[WAI_GUA_SELECT_PAI] = _args[0]
        elif _func_name == 'FreeBlessCount':
            self.free_bless_count(accountEntityId)
        elif _func_name == "Bless":
            self.bless(accountEntityId, _args["type"])
        elif _func_name == 'ContinueNextChapter':
            self.continue_next_chapter(accountEntityId)
        elif _func_name == 'ShareToWX':
            self.share_to_wx(accountEntityId)
        elif _func_name == 'HuTip':
            self.hu_tip(accountEntityId, _args['playCard'])
        elif _func_name == 'CancelAutoPlay':
            self.cancel_auto_play(accountEntityId)
            self.callClientFunction(accountEntityId, 'CancelAutoPlay', {"result": True})
            self.refresh_auto_play()

    def retLocations(self):
        """
        :return:
        """
        _chapter = self.chapters[self.cn]
        _players = _chapter[PLAYER_IN_GAME]
        stp = _chapter[SEAT_TO_PLAYER]
        _entityIds = []
        _userIds = []
        _locationIndexs = []
        _seats = []
        _location_info = {}
        for i in stp:
            p = stp[i]
            _seats.append(i)
            _entityIds.append(p["entity"].id)
            _userIds.append(p["entity"].info["userId"])
            _locationIndexs.append(p['locationIndex'])
        _location_info["entityIds"] = _entityIds
        _location_info["userIds"] = _userIds
        _location_info["locationIndexs"] = _locationIndexs
        _location_info["seats"] = _seats
        # 分别通知客户端
        for _p in _players.values():
            DEBUG_MSG('retLocations players:%s' % _p)
            _e = _p["entity"]
            if _e.info["isBot"] == 0:
                _json_data = json.dumps(_location_info)
                _e.clientEntity(self.id).retLocationIndexs(_json_data)

    def ret_player_in_room_info(self, accountId=-1):
        """
        广播房间内所有玩家状态
        :return:
        """
        _chapter = self.chapters[self.cn]
        _player_in_game = {}
        _player_out_game = {}
        _player_seat = _chapter[SEAT_TO_PLAYER]
        _player_witness = _chapter[PLAYER_OUT_GAME]
        player_in_game_to_base = {}
        for k, v in _player_seat.items():
            _player_location = v['locationIndex']
            # 获取总金币
            total_gold_change = v['totalGoldChange']
            _player = {"entityId": v["entity"].id, "locationIndex": int(v['locationIndex']),
                       "name": v["entity"].info["name"],
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       'goldChange': v['goldChange'],
                       'addOn': v['entity'].info['addOn'],
                       'seat': k,
                       'agreeLessMode': v["entity"].id in self.agree_less_person_mode_players,
                       'gold': v['gold'] + total_gold_change + v['baseSyncGoldChange'],
                       "headImageUrl": v["entity"].info["headImageUrl"],
                       "ready": v["isReady"],
                       "autoPlay": v["autoPlayCard"]
                       }
            _player_in_game[v["entity"].info["userId"]] = _player
            player_in_game_to_base[int(v["locationIndex"])] = {"name": v["entity"].info["name"],
                                                               "databaseId": v["entity"].info["dataBaseId"],
                                                               "headImageUrl": v["entity"].info["headImageUrl"]}
        for k, v in _player_witness.items():
            _player_location = v['locationIndex']
            # 获取总金币
            total_gold_change = v['totalGoldChange']
            _player = {"entityId": v["entity"].id, "locationIndex": int(v['locationIndex']),
                       "name": v["entity"].info["name"],
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       'goldChange': v['goldChange'],
                       'addOn': v['entity'].info['addOn'],
                       'seat': v['locationIndex'],
                       'gold': v['gold'] + total_gold_change + v['baseSyncGoldChange'],
                       "headImageUrl": v["entity"].info["headImageUrl"],
                       "ready": v["isReady"]}
            _player_out_game[v["entity"].info["userId"]] = _player
        _args = {"playerInGame": _player_in_game, 'playerOutGame': _player_out_game}
        if accountId == -1:
            self.callOtherClientsFunction("RetPlayerInRoomInfo", _args)
        else:
            self.callClientFunction(accountId, "RetPlayerInRoomInfo", _args)

        tea_house_id = -1
        if self.is_tea_house_room:
            tea_house_id = self.info['teaHouseId']
        self.base.cellToBase({"func": "refreshPlayerInGame", "playerInGame": player_in_game_to_base,
                              "teaHouseId": tea_house_id})

    def ret_player_out_game_info(self, accountId=-1):
        """
        广播房间内所有玩家状态
        :return:
        """
        _chapter = self.chapters[self.cn]
        _player_out_room = {}
        _witness_players = _chapter[PLAYER_OUT_GAME]
        for k, v in _witness_players.items():
            _player_location = v['locationIndex']
            # 获取总金币
            total_gold_change = v['totalGoldChange']
            _player = {"entityId": v["entity"].id, "locationIndex": int(v['locationIndex']),
                       "name": v["entity"].info["name"],
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       'goldChange': v['goldChange'],
                       'addOn': v['entity'].info['addOn'],
                       'seat': v['locationIndex'],
                       'gold': v['gold'] + total_gold_change + v['baseSyncGoldChange'],
                       "headImageUrl": v["entity"].info["headImageUrl"],
                       "ready": v["isReady"]}
            _player_out_room[v["entity"].info["userId"]] = _player
        _args = {"playerOutGame": _player_out_room}
        if accountId == -1:
            self.callOtherClientsFunction("RetOutGamePlayerInfo", _args)
        else:
            self.callClientFunction(accountId, "RetOutGamePlayerInfo", _args)

    def refresh_lucky_card(self, account_db_id, modify_count):
        """
        刷新房间内福卡
        :param account_db_id:
        :param modify_count:
        :return:
        """
        _chapter = self.chapters[self.cn]
        if self.info["roomType"] == "gameCoin":
            for k, v in _chapter[PLAYER_IN_GAME].items():
                if v["entity"].info["dataBaseId"] == account_db_id:
                    v['entity'].lucky_card += modify_count
                    self.callOtherClientsFunction("refreshLuckyCard",
                                                  {"luckyCard": v["entity"].lucky_card, "accountId": k})
                    break

    def retGolds(self):
        """
        广播玩家金币数变化
        :return:
        """
        pass

    def is_first_chapter(self):
        if self.cn == 0:
            return True
        return False

    # --------------------------------------------------------------------------------------------
    #                            客户端房间内操作
    # --------------------------------------------------------------------------------------------

    def req_dissolve(self, entityId):
        """
        请求解散
        :param entityId:
        :return:
        """
        if self.is_disbanding:
            return
        if self.total_settlement_ed:
            return
        _chapter = self.get_current_chapter()
        _player = self.get_seat_player_by_entity_id(entityId)
        if not _player:
            return
        self.disband_sender = entityId
        self.is_disbanding = True
        # 发起解散的玩家，默认同意
        _player[IS_ARGEE] = 1
        # 广播解散消息
        self.callOtherClientsFunction("dissolveSelect", {"locationIndex": _player['locationIndex'],
                                                         'disbandTime': AUTO_DISSOLVE_TIME})
        # 添加定时器
        _chapter['dissolveTimer'] = self.addTimer(AUTO_DISSOLVE_TIME, 0, 0)
        _chapter['dissolveDeadLine'] = time.time() + AUTO_DISSOLVE_TIME

    def dissolve_select(self, entityId, args):
        """
        解散选择
        :param entityId:
        :param args:
        :return:
        """
        _chapter = self.get_current_chapter()
        _player = self.get_seat_player_by_entity_id(entityId)

        is_agree = args[0]
        _player[IS_ARGEE] = int(is_agree)
        if is_agree == 0:
            # 拒绝，删除解散房间定时器，重置玩家相关状态，取消解散房间
            self.delTimer(_chapter['dissolveTimer'])
            _chapter['dissolveTimer'] = -1
            self.is_disbanding = False
            self.set_agree_state()
            self.callOtherClientsFunction("cancelDissolveRoom", {"locationIndex": _player['locationIndex']})
        else:
            args = {"locationIndex": _player['locationIndex'], "result": is_agree}
            self.callOtherClientsFunction("DissolveRoomOperation", args)
            # 同意，检查是否全部同意，全部同意，解散房间
            if self.is_all_agree():
                self.callOtherClientsFunction("dissolveRoom", {})
                self.total_settlement(is_disband=True)

    def set_agree_state(self):
        """
        设置玩家解散状态
        :return:
        """
        _chapter = self.get_current_chapter()
        players = _chapter[PLAYER_IN_GAME]
        for p in players.values():
            p[IS_ARGEE] = -1

    def is_all_agree(self):
        """
        是否都同意解散
        :return:
        """
        _chapter = self.get_current_chapter()
        players = _chapter[PLAYER_IN_GAME]
        for p in players.values():
            DEBUG_MSG('is_all_agree entity_id:%s agree:%s' % (p['entity'].id, p[IS_ARGEE]))
            if p[IS_ARGEE] != 1:
                return False
        return True

    # --------------------------------------------------------------------------------------------
    #                            计时器
    # --------------------------------------------------------------------------------------------

    def onTimer(self, timerId, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param timerId		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """
        _chapter = self.get_current_chapter()
        _timers = _chapter["timers"]

        if timerId == _timers["main"]:
            # DEBUG_MSG('[Room id %s]------------->onTimer main %s' % (self.id, timerId))
            _chapter_state = _chapter["chapterState"]
            _players = _chapter[PLAYER_IN_GAME]
            _playersCount = len(_chapter[PLAYER_IN_GAME])
            if _chapter_state == 0:
                # 一人不能开始
                if _playersCount <= 1:
                    return
                # 少人模式不判断是否大于最大人数
                if not self.is_less_mode and _playersCount < self.info["maxPlayersCount"]:
                    return
                _flag = True
                for i in _players.values():
                    if not i["isReady"]:
                        _flag = False
                        break
                if _flag:
                    # 关闭计时器
                    self.delTimer(timerId)
                    _timers["main"] = -1
                    self.changeChapterState(1)
        elif timerId == _chapter['playCardTimer']:
            self.delTimer(timerId)
            _chapter['playCardTimer'] = -1
            # 发牌之后,超时默认操作
            cur_player = self.get_current_player()
            out_pai = cur_player[SHOU_PAI][-1]
            DEBUG_MSG("start_auto_play %s" % cur_player["entity"].id)
            if self.is_auto_play_checking(cur_player["entity"].id):
                self.set_auto_play_check(cur_player["entity"].id, False)
                self.start_auto_play(cur_player["entity"].id)
                self.refresh_auto_play()
            self.operation_after_deal_card(cur_player, OPT_OUT, [out_pai])
        elif timerId == _chapter['resOutPaiTimer']:
            self.delTimer(timerId)
            _chapter['resOutPaiTimer'] = -1
            # 响应出牌，其他玩家超时后默认操作
            DEBUG_MSG('[RoomType5 id %i]------------->Timer(%s) 响应出牌,(%s)超时操作[guoOpt]' % (
                self.id, timerId, self.get_current_player()['locationIndex']))
            self.not_opt_players_operate_pass()
        elif timerId == _chapter['dissolveTimer']:
            # 解散房间
            self.callOtherClientsFunction("dissolveRoom", {})
            self.total_settlement(is_disband=True)
        elif timerId == _chapter['settlementTimer']:
            _chapter['settlementTimer'] = -1
            self.delTimer(timerId)
            self.changeChapterState(3)
        elif timerId == _chapter['restartTimer']:
            self.start_next_chapter()
        elif timerId == _chapter['settlementClearPlayers']:
            _chapter["settlementClearPlayers"] = -1
            self.delTimer(_chapter["settlementClearPlayers"])
            # 清理玩家
            _players = _chapter[PLAYER_IN_GAME].copy()
            for v in _players.values():
                self.onLeave(v['entity'].id)
        elif timerId == self.ready_gold_disband_timer:
            self.delTimer(self.ready_gold_disband_timer)
            self.ready_gold_disband_timer = -1
            if not self.is_forbid_disband_room():
                self.debug_msg('onTimer ready_gold_disband_timer %s' % timerId)
                all_can_ready = self.check_ready_gold_disband()
                # 如果有人仍不满足条件，解散房间
                if not all_can_ready:
                    self.debug_msg("not all_can_ready disband")
                    self.is_manual_disband = True
                    self.delTimer(_chapter['dissolveTimer'])
                    _chapter['dissolveTimer'] = -1
                    self.is_disbanding = False
                    self.callOtherClientsFunction("dissolveRoom", {})
                    self.total_settlement(is_disband=True)
        else:
            ""

    def check_ready_gold_disband(self):
        chapter = self.get_current_chapter()
        # 所有人都
        all_can_ready = True
        if self.info["roomType"] == "gameCoin":
            for k, v in chapter[PLAYER_IN_GAME].items():
                entity_id = v['entity'].id
                if self.get_true_gold(entity_id) < self.info['readyGoldLimit']:
                    all_can_ready = False
                    break

        return all_can_ready

    def is_auto_play_card(self, account_id):
        """
        自动出牌
        """
        player = self.get_seat_player_by_entity_id(account_id)
        if player:
            return player["autoPlayCard"]
        return False

    def set_auto_play_check(self, account_id, start_check):
        player = self.get_seat_player_by_entity_id(account_id)
        if player:
            player["allowAutoPlayCheck"] = start_check

    def is_auto_play_checking(self, account_id):
        player = self.get_seat_player_by_entity_id(account_id)
        if player:
            return player["allowAutoPlayCheck"]
        return False

    def start_auto_play(self, account_entity_id):
        """
        开始自动出牌
        """
        player = self.get_seat_player_by_entity_id(account_entity_id)
        if player and not player["autoPlayCard"]:
            player["autoPlayCard"] = True
            self.callClientFunction(account_entity_id, 'AutoPlayStart', {})

    def cancel_auto_play(self, account_entity_id):
        player = self.get_seat_player_by_entity_id(account_entity_id)
        if player:
            player["autoPlayCard"] = False

    def not_opt_players_operate_pass(self):
        """
        在玩家出牌过后，会有一个给其他玩家的响应周期
        此函数为让所有未操作玩家执行跳过操作
        :return:
        """
        _chapter = self.get_current_chapter()
        check_results = _chapter[CHECK_RESULTS]
        # 检查是否全部操作了，如果全部操作了，不做任何操作，如果有玩家未操作，则执行过操作
        for cr in check_results:
            if cr[CHECK_PLAYER_OPT] == NO_OPT:
                self.operation_after_play_card(cr[CHECK_PLAYER], OPT_GUO, None)

    def continue_next_chapter(self, entity_id):
        """
        结算状态的继续按钮
        :param entity_id:
        :return:
        """
        player = self.get_seat_player_by_entity_id(entity_id)
        if player['continue']:
            return
        # 如果是比赛场,准备时金币不能小于指定值
        if self.info["roomType"] == "gameCoin" and self.get_true_gold(entity_id) < self.info['readyGoldLimit']:
            self.callClientFunction(entity_id, 'Notice', ['您的比赛分不足,请您立即充值.'])
            info_args = {"accountId": entity_id}
            self.callOtherClientsFunction("ScoreIsLess", info_args)
            return
        player['continue'] = True
        # 同步准备消息
        player['isReady'] = True
        self.syncReadyMsg(player, True)
        for _p in self.get_current_chapter()[PLAYER_IN_GAME].values():
            if not _p['continue']:
                return
        # 如果所有人都点了继续，开始下一局
        self.start_next_chapter()

    def start_next_chapter(self):
        """
        开启下一局
        :return:
        """
        _chapter = self.get_current_chapter()
        # 关闭下局开始计时器
        self.delTimer(_chapter["restartTimer"])
        _chapter["restartTimer"] = -1
        # 流程继续
        _max_players_count = self.info["maxPlayersCount"]
        # 如果荒庄，使用上局的庄家
        if len(_chapter[HU_PLAYER]) == 0:
            banker_location = _chapter[BANKER_LOCATION]
        # 如果有胡牌的人，胡牌的第一位是下局的庄家
        else:
            banker_location = _chapter[HU_PLAYER][0]['locationIndex']
        _players = _chapter[PLAYER_IN_GAME]
        new_chapter = self.newChapter(_max_players_count)
        new_chapter[PLAYER_OUT_GAME] = _chapter[PLAYER_OUT_GAME]
        new_chapter[BANKER_LOCATION] = banker_location
        # 同步下米信息
        new_chapter['xiaMiInfo'] = _chapter['xiaMiInfo']
        # 在场座位上的玩家为下一局玩家
        for i in _players.values():
            _player = self.newPlayer(i["entity"], i['totalGoldChange'], i['baseSyncGoldChange'])
            self.set_seat(_player)
        self.changeChapterState(0)

    # --------------------------------------------------------------------------------------------
    #                            房间内其他
    # --------------------------------------------------------------------------------------------

    def emotion_chat(self, account_id, index, emotion_type):
        """
        表情聊天
        :param emotion_type:
        :param account_id:
        :param index:
        :return:
        """
        _args = {"accountId": account_id, "index": index, "type": emotion_type}
        self.callOtherClientsFunction("EmotionChat", _args)

    def voice_chat(self, accountId, url):
        """
        语音聊天
        :param accountId:
        :param url:
        :return:
        """
        _args = {"accountId": accountId, "url": url}
        self.callOtherClientsFunction("VoiceChat", _args)

    def bless(self, account_entity_id, bless_type):
        """
        祈福
        :param bless_type:
        :param account_entity_id:
        :return:
        """
        account = self.get_player_by_entity_id(account_entity_id)
        account_entity = account['entity']
        # 如果超过了免费次数
        if account_entity.today_bless_count > Const.GameConfigJson.config_json['Hall']['blessRoomCardStandard']:
            remain_room_card = account_entity.room_card
            # 如果没有支付AA支付钻石，预先扣除AA支付钻石
            if self.info['payType'] == Const.PayType.AA and not account['AARoomCardConsumed']:
                remain_room_card -= self.info['roomCardConsume']
            DEBUG_MSG('remain_room_card:%s' % remain_room_card)

            if remain_room_card < Const.GameConfigJson.config_json['Hall']['blessRoomCardConsume']:
                self.callClientFunction(account_entity_id, 'Notice', ['钻石不足'])
                return
            else:
                account_entity.base.cellToBase({'func': 'bless'})
                self.callClientFunction(account_entity_id, 'blessSuccess', {'type': bless_type})
        else:
            account_entity.base.cellToBase({'func': 'bless'})
            self.callClientFunction(account_entity_id, 'blessSuccess', {'type': bless_type})

    def free_bless_count(self, account_entity_id):
        """
        免费祈福次数
        :param account_entity_id:
        :return:
        """
        account = self.get_player_by_entity_id(account_entity_id)
        account_entity = account['entity']

        free_count = Const.GameConfigJson.config_json['Hall'][
                         'blessRoomCardStandard'] - account_entity.today_bless_count
        if free_count < 0:
            free_count = 0
        self.callClientFunction(account_entity_id, 'freeBlessCount', {
            'count': free_count, 'roomCardConsume': Const.GameConfigJson.config_json['Hall']['blessRoomCardConsume']})

    # --------------------------------------------------------------------------------------------
    #                            流程方法
    # --------------------------------------------------------------------------------------------

    def chapter_start(self):
        """
        牌桌开始
        :return:
        """
        # self.newCardsLib()
        _chapter = self.get_current_chapter()
        self.started = True
        self.info['started'] = True
        # +1
        _players = _chapter[PLAYER_IN_GAME]
        player_in_game_db_id = []
        for _p in _players.values():
            player_in_game_db_id.append(_p['entity'].info['dataBaseId'])
            self.player_entity(_p).update_player_stage(Account.PlayerStage.PLAYING, self.max_chapter_count,
                                                       self.current_chapter_count)
        self.notify_viewing_hall_players_chapter_start()
        self.base.cellToBase({"func": "roomStart", "roomInfo": self.info, "playerInGameDBID": player_in_game_db_id})
        # 房间开始，并且人未满时创建新的房间(onRoomEnd为true时插入在当前房间后面)
        if len(_players) < self.info['maxPlayersCount']:
            self.base.cellToBase({"func": "autoCreateRoom", "roomInfo": self.info})
        for _player in _players.values():
            _player["entity"].base.cellToBase({"func": "setAccountMutableInfo", "dic": {"gameBureauCount": 1}})
        # 开始位置为庄家的位置,newChapter的时候给庄家位置赋值
        start_index = _chapter[BANKER_LOCATION]
        # 开始玩家
        start_player = self.get_player_by_location(start_index)
        # 排序之后的玩家集合
        players = self.get_all_players_by_seat(start_seat=start_player[SEAT])
        self.callOtherClientsFunction('CiCard', {'card': _chapter[CI_CARD]})
        # # 发牌
        # for p in players:
        #     for i in range(0, 13):
        #         # 添加手牌
        #         _c = self.get_card()
        #         p[SHOU_PAI].append(_c)
        #     self.deal_cards_to_player(p['locationIndex'], p[SHOU_PAI])

        # 有人输的太多的话，需要发好牌
        is_in_rand_range = self.is_need_rand_score_control("RoomType5")
        luck_player = None
        if is_in_rand_range:
            luck_player = self.select_max_loser(players)
            # if luck_player:
            #     self.callClientFunction(luck_player['entity'].id, 'Notice', ['发好牌'])

        if not luck_player:
            # 找连输超过5局的最大连输玩家
            luck_player, max_losing_streak_count = self.get_max_losing_streak_player(players)
            if max_losing_streak_count < 5:
                luck_player = None
            DEBUG_MSG(
                '最大连输 %s %s' % (max_losing_streak_count, luck_player['entity'].id if luck_player else luck_player))

        if not luck_player:
            # 幸运数字玩家
            is_in_rand_range = self.is_need_rand_score_control("RoomType5")
            if is_in_rand_range:
                luck_player = self.select_luck_max_loser(players)

        # 每日发好牌次数控制
        day_player = self.select_day_good_pai_player(players, 4)
        if day_player:
            luck_player = day_player
            self.player_entity(luck_player).increase_day_pai_control_count()

        # 分牌
        all_cards = []
        for p in players:
            cards = []
            for i in range(0, 13):
                # 添加手牌
                _c = self.get_card()
                cards.append(_c)
            all_cards.append(cards)

        # 给幸运玩家发好牌
        have_pai_player_id = -1
        if luck_player:
            hun_zi_list = []
            good_card_index = mj.RoomType14Calculator.get_good_pai(all_cards, hun_zi_list)
            if good_card_index >= 0:
                luck_player[SHOU_PAI] = all_cards[good_card_index]
                del all_cards[good_card_index]
                have_pai_player_id = luck_player['entity'].id
                DEBUG_MSG('good pai player id: %s cards: %s' % (have_pai_player_id, luck_player[SHOU_PAI]))

        # 给其他人发牌
        for p in players:
            if have_pai_player_id == p['entity'].id:
                self.deal_cards_to_player(p['locationIndex'], p[SHOU_PAI])
                continue
            p[SHOU_PAI] = all_cards[0]
            del all_cards[0]
            self.deal_cards_to_player(p['locationIndex'], p[SHOU_PAI])

        # 进入出牌阶段
        self.changeChapterState(2)
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

    def deal_cards_to_player(self, locationIndex, cards):
        """
        给玩家发牌
        :param locationIndex:
        :param cards:
        :return:
        """
        if self.otherClients is None:
            return
        self.retChapterSysPrompt("给玩家" + str(locationIndex) + "发牌")
        self.otherClients.dealCardsToPlayer(locationIndex, cards)

        _chapter = self.get_current_chapter()
        _replay = {'locationIndex': locationIndex, 'otherIndex': -1, "opt": 'initPai', "card": cards.copy()}
        _chapter['replay'].append(_replay)

    def init_round(self):
        """
        初始化玩家位置
        :return:
        """
        _chapter = self.get_current_chapter()
        # 开始位置
        _start_seat = _chapter[BANKER_LOCATION]
        # 获取排过序的玩家顺序
        _round = self.get_all_players_by_seat(start_seat=_start_seat)
        _chapter[ROUND] = _round
        # 通知下一个玩家操作
        self.notice_next_player(_round[-1], _round)

    def end_round(self):
        """
        结束比赛
        :return:
        """
        # 开启结算倒计时
        self.get_current_chapter()['settlementTimer'] = self.addTimer(3, 0, 0)

    def destroy_check_result(self, _cur_player):
        _chapter = self.get_current_chapter()
        _chapter[CHECK_RESULTS] = None
        players = self.get_all_players_by_seat()
        for p in players:
            p[CHECK_RESULT] = None
        self.change_cur_player(_cur_player)

    def notice_next_player(self, player, _round):
        """
        通知下个玩家操作
        :param player:
        :param _round:
        :return:
        """
        _chapter = self.get_current_chapter()
        # 找到下一个玩家
        _next = None
        # 如果当前玩家是最后一个，从第一个开始
        if player == _round[-1]:
            _next = _round[0]
        else:
            _index = _round.index(player)
            _next = _round[_index + 1]
        # 修改当前玩家
        self.change_cur_player(_next)
        # 给当前玩家发牌
        self.deal_one_card(self.get_current_player(), False)

    # --------------------------------------------------------------------------------------------
    #                            工具
    # --------------------------------------------------------------------------------------------

    def get_current_player(self):
        """
        获取当前玩家
        :return:
        """
        _chapter = self.get_current_chapter()
        return _chapter[CUR_PLAYER]

    def get_wait_player(self):
        """
        获取等待玩家
        :return:
        """
        _chapter = self.get_current_chapter()
        return _chapter[WAIT_PLAYER]

    def get_bao_ci_player(self, hu_player):
        _chapter = self.get_current_chapter()
        _index = -1
        if _chapter[IS_MING_CI_HE]:
            _index = get_last_da_ming_gang(hu_player)
        self.debug_msg('get_bao_ci_player locationIndex:%s' % _index)
        if _index != -1:
            return self.get_player_by_location(_index)
        return None

    def get_player_by_location(self, locationIndex):
        """
        通过位置获取玩家
        :param locationIndex:
        :return:
        """
        _chapter = self.get_current_chapter()
        players = _chapter[PLAYER_IN_GAME]
        return players[locationIndex]

    def get_witness_player_by_entity_id(self, entityId):
        """
        通过实体id获取观战玩家
        :param entityId:
        :return:
        """
        _chapter = self.get_current_chapter()
        for k, v in _chapter[PLAYER_OUT_GAME].items():
            if v['entity'].id == entityId:
                return v

    def get_player_by_entity_id(self, entityId):
        """
        通过实体id获取所有玩家
        :param entityId:
        :return:
        """
        _chapter = self.get_current_chapter()

        for k, v in _chapter[PLAYER_IN_GAME].items():
            if v['entity'].id == entityId:
                return v

        for k, v in _chapter[PLAYER_OUT_GAME].items():
            if v['entity'].id == entityId:
                return v

    def get_other_players_by_seat(self, seat):
        """
        获取非当前座位的玩家；比如有4个位置(0,1,2,3)，如果seat = 2,那么返回(3，0，1)上对应玩家的集合
        :param seat:
        :return:
        """
        _chapter = self.get_current_chapter()
        # seats = _chapter[SEAT]
        stp = _chapter[SEAT_TO_PLAYER]
        temp = seat
        _len = len(stp)
        if seat >= _len or seat < 0:
            raise Exception("max seat: %s, error seat: %s " % (_len - 1, seat))
        ret = []
        while True:
            temp += 1
            p = temp % _len
            if p == seat:
                break
            if p in stp.keys():
                player = stp[p]
                ret.append(player)
        return ret

    def get_all_players_by_seat(self, start_seat=0):
        """
        通过位置获取排过序的所有玩家合集
        :param start_seat:
        :return:
        """
        _chapter = self.get_current_chapter()
        stp = _chapter[SEAT_TO_PLAYER]
        start_player = stp[start_seat]
        DEBUG_MSG('get_all_players_by_seat seat_to_player%s' % _chapter[SEAT_TO_PLAYER])
        ret = self.get_other_players_by_seat(start_seat)
        ret.insert(0, start_player)
        return ret

    def clearFaiPaiDate(self):
        """
        清除杠上开花标识
        :return:
        """
        _chapter = self.get_current_chapter()
        _cur_player = self.get_current_player()
        # 清除杠上开花标记
        _chapter[IS_GANG_SHANG_KAI_HUA] = False
        # 清除单放
        _cur_player[DAN_FANG] = -1

    def set_not_hu_pai(self, player):
        """
        玩家能胡但没有胡的牌
        :param player:
        :return:
        """
        _chapter = self.get_current_chapter()
        if player[CAN_HU]:
            player[QI_HU] = True
            player[NOT_HU_PAI].append(_chapter[CUR_PAI])

    def setNotPengPai(self, player):
        """
        玩家能碰没有碰的牌
        :param player:
        :return:
        """
        _chapter = self.get_current_chapter()
        if player[CAN_PENG]:
            player[NOT_PENG_PAI].append(_chapter[CUR_PAI])

    def change_cur_player(self, player):
        """
        改变当前操作玩家
        :param player:
        :return:
        """
        _chapter = self.get_current_chapter()
        if _chapter[CUR_PLAYER]:
            DEBUG_MSG('[RoomType5 id %i]------------->ChangeCurPlayer %s to %s' % (
                self.id, _chapter[CUR_PLAYER]['locationIndex'], player['locationIndex']))
        _chapter[CUR_PLAYER] = player

    def refresh_client_state(self):
        """
        刷新玩家在线状态
        :return:
        """
        chapter = self.get_current_chapter()
        client_state = {}
        for k, v in chapter[PLAYER_IN_GAME].items():
            client_state[v['entity'].id] = not v['entity'].client_death
        self.callOtherClientsFunction('RefreshOnlineState', client_state)

    def refresh_auto_play(self):
        """
        刷新玩家自动出牌状态
        :return:
        """
        chapter = self.get_current_chapter()
        client_state = {}
        for k, v in chapter[PLAYER_IN_GAME].items():
            client_state[v['entity'].id] = v["autoPlayCard"]
        self.callOtherClientsFunction('RefreshAutoPlay', client_state)

    # --------------------------------------------------------------------------------------------
    #                            检查玩家操作
    # --------------------------------------------------------------------------------------------

    def check_current_player(self, player):
        """
        检查玩家是否可以操作
        :param player:需要检查的玩家
        :return: true:正常  false: 错误的玩家操作
        """
        _chapter = self.get_current_chapter()
        allow_out_players = self.get_allow_opt_players()
        if not self.is_player_in_players(player, allow_out_players):
            allow_location_index = []
            for item in allow_out_players:
                allow_location_index.append(item['locationIndex'])
            DEBUG_MSG('[RoomType5 id %i]------>Error: correct player: %s, current player: %s' % (
                self.id, allow_location_index, player['locationIndex']))
            return False
        return True

    def get_allow_opt_players(self):
        """
        :return: 允许操作的玩家的集合
        """
        _chapter = self.get_current_chapter()
        allow_out_players = _chapter[ALLOW_OPT_PLAYERS]
        if len(allow_out_players) != 0:
            return allow_out_players
        return [self.get_current_player()]

    def checkOperation(self, player, operation_name):
        """
        :param player:
        :param operation_name:
        :return: true: 允许操作  false: 不允许操作
        """
        _chapter = self.get_current_chapter()
        allow_opt = player[ALLOW_OPT]
        opt_v = OPT_DICT[operation_name]
        if (allow_opt & opt_v) == opt_v:
            return True
        return False

    def check_chi(self, pai):
        """
        检查是否能吃
        :param pai:
        :return:
        """
        pais = [pai, pai + 1, pai + 2]
        _chapter = self.get_current_chapter()
        cur_pai = _chapter[CUR_PAI]
        if is_shun_zi(pais):
            if cur_pai in pais:
                return
        raise Exception("error chi: %s, cur_pai: %s" % (pais, cur_pai))

    def check_opt_pai(self, pai):
        """
        检查出的牌是否合理
        :param pai:
        :return:
        """
        check_cards(pai)
        _chapter = self.get_current_chapter()
        cur_pai = _chapter[CUR_PAI]
        if pai != cur_pai:
            raise Exception("error opt pai: %s, cur_pai: %s" % (pai, cur_pai))

    # --------------------------------------------------------------------------------------------
    #                            系统操作集合
    # --------------------------------------------------------------------------------------------
    def deal_one_card(self, player, is_gang):
        """
        给某个玩家发一张牌
        :param player:
        :param is_gang:
        :return:
        """
        pai = None
        if player[WAI_GUA_SELECT_PAI] == -1:
            # 不管杠不杠都摸下一张
            pai = self.get_card()
        else:
            pai = self.get_wai_gua_card(player[WAI_GUA_SELECT_PAI])
            player[WAI_GUA_SELECT_PAI] = -1
        if pai is None:
            return
        _chapter = self.get_current_chapter()
        # 清除不能胡的牌
        player[NOT_HU_PAI].clear()
        player[QI_HU] = False
        player[WIN_CI] = False

        # 清除不能碰的牌
        player[NOT_PENG_PAI].clear()
        _shou_pai = player[SHOU_PAI]
        _pengs = player[PENG_S]
        # 设置当前操作的牌
        _chapter[CUR_PAI] = pai
        # 添加手牌
        add_hand_cards(_shou_pai, pai)
        # 设置单放
        player[DAN_FANG] = pai
        # 操作次数+1
        player[OPT_COUNT] += 1
        # 同步剩余牌的数量
        self.syncLeftPaiCount(_chapter[LEFT_PAI_COUNT])

        # 检查当前玩家的杠胡情况
        _xmg = check_xiao_ming_gang(_shou_pai, _pengs)
        _ag = check_an_gang(_shou_pai)
        can_pi_ci = check_pi_ci(_shou_pai, _chapter[CI_CARD])
        # 软次才可以自模胡
        _isHu = mj.AgariUtils.isHuPai(_shou_pai) and not self.is_ying_ci()
        DEBUG_MSG('[RoomType5 id %i]------------->FaPai ishu=%s' % (self.id, _isHu))
        # 设置当前玩家可以胡牌
        player[CAN_HU] = _isHu

        # 将玩家可以碰牌设置为False
        player[CAN_PENG] = False

        # 如果是杠后发牌，并且可以胡，那么记为杠上开花
        if is_gang and _isHu:
            _chapter[IS_GANG_SHANG_KAI_HUA] = True

        # 明次、暗次标识
        can_xiao_ming_ci = False
        can_an_ci = False
        an_ci_card = -1
        xiao_ming_ci_card = -1

        # 客户端操作验证
        player[ALLOW_OPT] = 0
        self.debug_msg('_xmg:%s' % _xmg)
        if len(_xmg) != 0:
            player[ALLOW_OPT] |= OPT_XIAOMINGGANG_V
            # 检查是否赢次牌
            if not player[WIN_CI]:
                # 剔除小明杠,再判断能不能次胡
                for _x in _xmg:
                    temp = player[SHOU_PAI].copy()
                    temp.remove(_x)
                    win_x_m_ci = check_win_ci(temp, _chapter[CI_CARD])
                    if win_x_m_ci:
                        xiao_ming_ci_card = _x
                        break
            if win_x_m_ci:
                player[WIN_CI] = win_x_m_ci
                player[ALLOW_OPT] |= OPT_HU_XIAO_Ming_CI_V
                can_xiao_ming_ci = True
        self.debug_msg('_ag:%s' % _ag)
        if len(_ag) != 0:
            player[ALLOW_OPT] |= OPT_ANGANG_V
            win_an_ci = False
            # 检查是否赢次牌
            if not player[WIN_CI]:
                # 踢出暗杠，在判断能不能次胡
                for _x in _ag:
                    temp = player[SHOU_PAI].copy()
                    temp.remove(_x)
                    temp.remove(_x)
                    temp.remove(_x)
                    temp.remove(_x)
                    win_an_ci = check_win_ci(temp, _chapter[CI_CARD])
                    if win_an_ci:
                        an_ci_card = _x
                        break
            if win_an_ci:
                player[WIN_CI] = win_an_ci
                player[ALLOW_OPT] |= OPT_HU_AN_CI_V
                can_an_ci = True

        # 如果是软次可以自摸
        if _isHu:
            player[ALLOW_OPT] |= OPT_HU_ZIMO_V
        if can_pi_ci:
            player[ALLOW_OPT] |= OPT_HU_Pi_CI_V
        player[ALLOW_OPT] |= OPT_OUT_V

        all_not = True
        # 同步发牌
        self.syncOpt(player['locationIndex'], SYNCOPT_FAPAI, pai, -1)
        # 听牌提醒：
        self.can_ting(player['entity'].id)
        # 出牌提示
        if len(_xmg) != 0:
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_XIAOMINGGANG, _xmg)
            all_not = False
        if len(_ag) != 0:
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_ANGANG, _ag)
            all_not = False

        if _isHu:
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_ZIMOHU, _isHu)
            all_not = False

        if can_xiao_ming_ci and xiao_ming_ci_card != -1:
            self.callClientFunction(player['entity'].id, CLIENT_FUNC_XIAO_MING_CI_HU, [xiao_ming_ci_card])
            all_not = False

        if can_an_ci and an_ci_card != -1:
            self.callClientFunction(player['entity'].id, CLIENT_FUNC_AN_CI_HU, [an_ci_card])
            all_not = False

        if can_pi_ci:
            self.callClientFunction(player['entity'].id, CLIENT_FUNC_PI_CI_HU, _ag)
            all_not = False  # 添加听牌提醒：
        if not all_not:
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_GUO, "")

        # 如果玩家不在线，自动出牌
        if player['entity'].client_death and self.info['timeDown'] != 0:
            # 发牌之后,超时默认操作
            cur_player = self.get_current_player()
            out_pai = cur_player[SHOU_PAI][-1]
            self.operation_after_deal_card(cur_player, OPT_OUT, [out_pai])
        # 如果玩家在线，开启计时器
        else:
            # 开启出牌定时器
            if self.info['timeDown'] > 0:
                wait_time_len = self.info['timeDown']
                if self.is_auto_play_card(player["entity"].id):
                    wait_time_len = WAIT_TIME_LEN_ON_PLAY_OFFLINE
                else:
                    self.set_auto_play_check(player["entity"].id, True)

                DEBUG_MSG("is_auto_play_card %s %s" % (player["entity"].id, wait_time_len))

                _chapter['playCardTimer'] = self.addTimer(wait_time_len, 0, 0)
                _chapter['deadLine'] = time.time() + wait_time_len
                self.sync_timer_count_down(wait_time_len)
            else:
                # 假倒计时
                self.sync_timer_count_down(20)
                _chapter['deadLine'] = time.time() + 20

    def check_other_player_can_operate(self, can_operation_s):
        """
        检查玩家可以进行的操作，并发给前台
        如果没有玩家可以操作，切换到下个玩家
        对check_results中的元素，提示对应玩家操作，如果长度为空，则给下一家发牌
        :param can_operation_s:其余玩家可以进行的操作
        :return:
        """
        _chapter = self.get_current_chapter()
        # 如果没有玩家可以操作，切换下个人
        if not can_operation_s:
            self.goNext()
        else:
            # 清空INNER_BOT_OPT_TIMERS
            # _chapter[INNER_BOT_OPT_TIMERS].clear()
            for c_op in can_operation_s:
                # 暂存起来，用于重连
                c_op[CHECK_PLAYER][CHECK_RESULT] = c_op
                _chapter[ALLOW_OPT_PLAYERS].append(c_op[CHECK_PLAYER])
                if c_op[CHECK_PLAYER]['entity'].client_death:
                    self.operation_after_play_card(c_op[CHECK_PLAYER], OPT_GUO, None)
                else:
                    self.send_check_result_item(c_op)

            # 添加超时定时器
            self.sync_timer_count_down(AUTO_TIME)
            _t_id = self.addTimer(AUTO_TIME, 0, 0)
            _chapter['resOutPaiTimer'] = _t_id

    def notifyOutPai(self, player, notOutPai=[]):
        _chapter = self.get_current_chapter()

        # 用户检查客户端操作
        # player[ALLOW_OPT] = 0
        player[ALLOW_OPT] |= OPT_OUT_V

        if player["entity"].info["isBot"] == 1:
            # 机器人定时器
            _t_id = self.addTimer(1, 0, 0)
            _chapter[BOT_OUT_PAI_TIMER] = _t_id
        else:
            # 通知客户端出牌
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_NOTIFYOUTPAI, notOutPai)
        # 开启出牌定时器
        if self.info['timeDown'] > 0:
            _chapter['playCardTimer'] = self.addTimer(self.info['timeDown'], 0, 0)
            _chapter['deadLine'] = time.time() + self.info['timeDown']
            self.sync_timer_count_down(self.info['timeDown'])
        else:
            # 假倒计时
            self.sync_timer_count_down(20)
            _chapter['deadLine'] = time.time() + 20

    def operation_over(self, timeout=False):
        """
        操作结束，进行一些收尾工作
        :param timeout:
        :return:
        """
        _chapter = self.get_current_chapter()
        check_results = _chapter[CHECK_RESULTS]
        # 检查是否全部操作了，如果全部操作了，执行下一步，如果有玩家未操作，退出
        # 如果超时了为操作，直接给出默认操作，执行下一步
        for cr in check_results:
            if cr[CHECK_PLAYER_OPT] == NO_OPT:
                if timeout:
                    cr[CHECK_PLAYER_OPT] = OPT_GUO_V
                else:
                    return
        # 清除定时器
        self.delTimer(_chapter['resOutPaiTimer'])
        _chapter['resOutPaiTimer'] = -1
        # 清空ALLOW_OPT_PLAYERS
        _chapter[ALLOW_OPT_PLAYERS].clear()

        # 根据优先级从大到小排序, 优先级：胡、杠、碰、吃
        def func(e):
            return e[CHECK_PLAYER_OPT]

        check_results = sorted(check_results, key=func, reverse=True)
        # 根据优先级，选出最终操作完成的玩家
        is_first = True
        hu_players = []
        # is_qiang_gang_hu = check_results[0][CHECK_FLAG]
        for cr in check_results:
            _cpo = cr[CHECK_PLAYER_OPT]
            # 判断操作是否是胡牌
            if _cpo == OPT_HU_DIANPAO_V:
                # 如果可以一炮多响
                is_first = False
                hu_players.append(cr[CHECK_PLAYER])
                continue
            if is_first:
                if _cpo == OPT_DAMINGGANG_V:
                    self.da_ming_gang_opt(cr[CHECK_PLAYER], _chapter[CUR_PAI])
                    return
                elif _cpo == OPT_PENG_V:
                    self.pengOpt(cr[CHECK_PLAYER], _chapter[CUR_PAI])
                    return
                elif _cpo == OPT_CHI_V:
                    self.chiOpt(cr[CHECK_PLAYER], cr[CHI_ARGS])
                    return
                elif _cpo == OPT_HU_Ming_CI_V:
                    self.ming_ci_hu_opt(cr[CHECK_PLAYER], _chapter[CUR_PAI])
                    return
                elif _cpo == OPT_GUO_V:
                    self.guoOpt(cr[CHECK_PLAYER])
            else:
                break
        if not is_first:
            self.dianPaoHuOpt(hu_players)
            return
        # 清除产生的中间数据，继续操作
        self.destroy_check_result(self.get_current_player())
        self.goNext()

    def goNext(self):
        _chapter = self.get_current_chapter()
        # 将玩家打出的牌放入自己打出牌的集合中
        self.get_current_player()[OUT_PAIS].append(_chapter[CUR_PAI])
        # 全部过，下一个玩家操作
        self.notice_next_player(self.get_current_player(), _chapter[ROUND])

    def syncOpt(self, locationIndex, opt, pai, otherIndex, is_ci=False):
        self.callOtherClientsFunction("syncOpt",
                                      {"locationIndex": locationIndex, "opt": opt, "pai": pai, "otherIndex": otherIndex,
                                       'isCi': is_ci})

        # 增加回放
        _chapter = self.get_current_chapter()
        out_pai_replay = {'locationIndex': locationIndex, 'otherIndex': otherIndex, "opt": opt, "card": [pai]}
        _chapter['replay'].append(out_pai_replay)

    def syncLeftPaiCount(self, leftPaiCount):
        self.callOtherClientsFunction("syncLeftPaiCount", {"leftPaiCount": leftPaiCount})

    def syncChapterNum(self, chapterNum):
        self.callOtherClientsFunction("syncChapterNum", {"chapterNum": chapterNum})

    def syncHuaPaiCount(self, locationIndex, huaPaiCount):
        self.callOtherClientsFunction("syncHuaPaiCount", {"locationIndex": locationIndex, "huaPaiCount": huaPaiCount})

    def sync_timer_count_down(self, t):
        """
        同步倒计时
        :param t:
        :return:
        """
        self.callOtherClientsFunction('syncTimerCountDown', {'time': t})

    def sync_gold(self):
        """
        同步金币变化、金币以及金币总变化
        scores = [{"locationIndex": locationIndex, "score": score},...]
        :return:
        """
        _chapter = self.get_current_chapter()
        _gold_info = {}
        for k, v in _chapter[PLAYER_IN_GAME].items():
            total_gold_change = v['totalGoldChange']
            base_sync_gold_change = v['baseSyncGoldChange']
            _g = {'gold': v['gold'] + total_gold_change + base_sync_gold_change,  # 'goldChange': v['goldChange'],
                  'totalGoldChange': total_gold_change}
            _gold_info[v['entity'].info['userId']] = _g
        self.callOtherClientsFunction("syncGold", _gold_info)

    def sync_xia_mi_info(self):
        """
        同步下米分
        :return:
        """
        _chapter = self.get_current_chapter()
        self.callOtherClientsFunction("syncXiaMiInfo", {'xiaMiInfo': _chapter['xiaMiInfo']})

    def get_true_gold(self, account_id):
        """
        获得玩家当前真实金币
        :param account_id:
        :return:
        """
        _chapter = self.get_current_chapter()
        for k, v in _chapter[PLAYER_IN_GAME].items():
            if v['entity'].id == account_id:
                return v['gold'] + v['baseSyncGoldChange'] + v['totalGoldChange']

        for k, v in _chapter[PLAYER_OUT_GAME].items():
            if v['entity'].id == account_id:
                return v['gold'] + v['baseSyncGoldChange'] + v['totalGoldChange']

    def sync_banker_index(self, locationIndex):
        """
        同步庄家的位置
        :param locationIndex:
        :return:
        """
        self.callOtherClientsFunction("syncBankerIndex", {"bankerIndex": locationIndex})

    # -----------------------  删除超时定时器  -----------------------

    def del_play_card_timer(self):
        _chapter = self.get_current_chapter()
        self.delTimer(_chapter['playCardTimer'])
        _chapter['playCardTimer'] = -1

    def del_res_play_card_timer(self):
        _chapter = self.get_current_chapter()
        self.delTimer(_chapter['resOutPaiTimer'])
        DEBUG_MSG('[RoomType5 id %i]------------->删除响应出牌超时定时器(%s)' % (self.id, _chapter['resOutPaiTimer']))
        _chapter['resOutPaiTimer'] = -1

    # --------------------------------------------------------------------------------------------
    #                            玩家操作集合
    # --------------------------------------------------------------------------------------------
    # ---------------------  发牌之后操作  ---------------------
    def play_card(self, player, out_pai):
        """
        出牌
        此操作同时会检测并记录其他玩家接下来可以进行的操作
        :param player:
        :param out_pai:
        :return:
        """
        _chapter = self.get_current_chapter()
        _hand_cards = player[SHOU_PAI]
        _out_cards = player[OUT_PAIS]
        # 玩家出牌后再次发送胡牌提醒
        self.hu_tip(player['entity'].id, out_pai)
        # 移除手牌,加入出牌区
        if out_pai in _hand_cards:
            remove_hand_card(_hand_cards, out_pai)
        else:
            self.debug_msg('out_pai not in _hand_cards')
            return
        _chapter[CUR_PAI] = out_pai
        # 同步出牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_OUTPAI, out_pai, -1)

        # 其他玩家；从当前玩家开始，要有顺序
        other_players = self.get_other_players_by_seat(player[SEAT])
        check_results = []
        for i, p in enumerate(other_players):

            # 检查吃碰杠胡
            p[CAN_PENG] = False
            p[CAN_HU] = False
            b_peng = check_peng(p[SHOU_PAI], out_pai)
            if not p[CAN_PENG]:
                if b_peng and out_pai not in p[NOT_PENG_PAI]:
                    p[CAN_PENG] = True

            _chi = list()
            # 杠次无法吃牌
            # if i == 0:
            #     _chi = checkChi(p[SHOU_PAI], out_pai)
            # 检查是否赢次牌

            can_da_ming_gang = check_da_ming_gang(p[SHOU_PAI], out_pai)
            # 杠次不能点炮胡
            # b_hu = mj.AgariUtils.isHuPai(p[SHOU_PAI], pai=out_pai)
            # if not p[CAN_HU]:
            #     if b_hu and not self.is_ying_ci():
            #         # 设置当前玩家可以胡牌
            #         p[CAN_HU] = True

            # 用于检查客户端操作
            p[ALLOW_OPT] = 0
            if len(_chi) != 0:
                p[ALLOW_OPT] |= OPT_CHI_V
            if p[CAN_PENG]:
                p[ALLOW_OPT] |= OPT_PENG_V
            if can_da_ming_gang:
                p[ALLOW_OPT] |= OPT_DAMINGGANG_V
                # 如果能组成大明杠，并且玩家赢次牌，那么就允许玩家明次胡
                p[WIN_CI] = False
                if not p[WIN_CI]:
                    temp = p[SHOU_PAI].copy()
                    temp.append(out_pai)
                    p[WIN_CI] = check_win_ci(temp, _chapter[CI_CARD])
                if p[WIN_CI]:
                    p[ALLOW_OPT] |= OPT_HU_Ming_CI_V
            # 杠次不能点炮
            # if p[CAN_HU]:
            #     p[ALLOW_OPT] |= OPT_HU_DIANPAO_V
            if p[ALLOW_OPT] != 0:
                p[ALLOW_OPT] |= OPT_GUO_V

            # 封装检查结果
            check_result = {CHECK_PLAYER: p, CHECK_CHI: _chi, CHECK_PENG: p[CAN_PENG],
                            CHECK_DAMINGGANG: can_da_ming_gang, CHECK_HU_MING_CI: can_da_ming_gang and p[WIN_CI],
                            # 如果软次，允许点炮胡
                            CHECK_HU: p[CAN_HU], CHECK_HU_QIANG_GANG: False, CHECK_PLAYER_OPT: NO_OPT,
                            CHECK_FLAG: CHECK_FLAG_OUTPAI}
            # 如果能碰，能大明杠、能吃、能胡将所有可以操作的玩家及允许的操作保存起来
            if p[CAN_PENG] or can_da_ming_gang or p[CAN_HU] or len(_chi) != 0:
                check_results.append(check_result)

        # 保存 outPaiCheckResults
        _chapter[CHECK_RESULTS] = check_results
        DEBUG_MSG('CHECK_RESULTS:%s' % _chapter[CHECK_RESULTS])

        # 设置等待玩家
        _chapter[WAIT_PLAYER] = player
        # 检查其他玩家可以进行的操作
        self.check_other_player_can_operate(check_results)

        # 每次出牌检查并发送包次
        self.check_bao_ci()

    def xiao_ming_gang_opt(self, player, pai):
        DEBUG_MSG('[RoomType5 id %i]------------->xiaoMingGangOpt CurPlayer=%s, Pai=%s' % (
            self.id, player['locationIndex'], pai))
        _chapter = self.get_current_player()
        _chapter[CUR_PAI] = pai
        other_index = xiao_ming_gang(player, pai)
        # 同步小明杠消息
        self.syncOpt(player['locationIndex'], SYNCOPT_XIAOMINGGANG, pai, other_index)
        # 给此玩家发牌
        self.deal_one_card(player, True)

    def an_gang_opt(self, player, pai):
        DEBUG_MSG(
            '[RoomType5 id %i]------------->anGangOpt CurPlayer=%s, Pai=%s' % (self.id, player['locationIndex'], pai))
        # 移除杠牌
        an_gang(player, pai)
        # 同步暗杠消息
        self.syncOpt(player['locationIndex'], SYNCOPT_ANGANG, pai, -1)
        # 给此玩家发牌
        self.deal_one_card(player, True)

    def zi_mo_hu_opt(self, player):
        DEBUG_MSG('[RoomType5 id %i]------------->ziMoHuOpt CurPlayer=%s' % (self.id, player['locationIndex']))
        _chapter = self.get_current_chapter()
        _chapter[IS_ZI_MO_HE] = True
        _chapter[HU_TYPE] = HU_TYPE_ZI_MO
        # 同步自摸消息
        self.syncOpt(player['locationIndex'], SYNCOPT_ZIMOHU, self.get_current_chapter()[CUR_PAI], -1)
        self.hu([player])

    # ---------------------  出牌之后操作  ---------------------

    def res_out_pai_guo_opt(self, player):
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_GUO_V
        self.operation_over()

    def guoOpt(self, player):
        """
        暂时没有操作
        :param player:
        :return:
        """
        pass

    def res_out_pai_chi_opt(self, player, pai):
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_CHI_V
                cr[CHI_ARGS] = pai
        self.operation_over()

    def chiOpt(self, player, pai):
        DEBUG_MSG(
            '[RoomType5 id %i]------------->chiOpt CurPlayer=%s, Pais=%s' % (self.id, player['locationIndex'], pai))
        _chapter = self.get_current_chapter()
        other_index = self.get_wait_player()['locationIndex']
        cur_pai = _chapter[CUR_PAI]
        # 操作次数+1
        player[OPT_COUNT] += 1
        # 清除玩家不能碰的牌
        player[NOT_PENG_PAI].clear()
        chi(player, pai, cur_pai, other_index)
        # 销毁check_results
        self.destroy_check_result(player)
        # 同步吃牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_CHI, pai, other_index)
        # 吃过之后，部分牌将不能够被打出
        shou_pai = player[SHOU_PAI]
        _noAllowDrapCard = []
        # _noAllowDrapCard.append(pai)
        # if cur_pai - pai == 0:
        #     if pai % 9 < 6:
        #         _noAllowDrapCard.append(pai + 3)
        # elif cur_pai - pai == 2:
        #     if pai % 9 != 0:
        #         _noAllowDrapCard.append(pai - 1)

        cards = [pai, pai + 1, pai + 2]
        cards.remove(cur_pai)
        for card in shou_pai:
            cards.append(card)
            if is_shun_zi(cards):
                _noAllowDrapCard.append(card)
            cards.remove(card)

        _pengs = player[PENG_S]
        _xmg = check_xiao_ming_gang(shou_pai, _pengs)
        if len(_xmg) != 0:
            player[ALLOW_OPT] |= OPT_XIAOMINGGANG_V
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_XIAOMINGGANG, _xmg)
        self.notifyOutPai(player, _noAllowDrapCard)

    def resOutPaiPengOpt(self, player, pai):
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_PENG_V
        self.operation_over()

    def pengOpt(self, player, pai):
        DEBUG_MSG(
            '[RoomType5 id %i]------------->pengOpt CurPlayer=%s, Pai=%s' % (self.id, player['locationIndex'], pai))
        self.check_opt_pai(pai)
        _chapter = self.get_current_chapter()
        other_index = self.get_wait_player()['locationIndex']

        # 清除不可以碰的牌
        player[NOT_PENG_PAI].clear()

        # 操作次数+1
        player[OPT_COUNT] += 1

        peng(player, pai, other_index)
        # 销毁check_results
        self.destroy_check_result(player)
        # 同步碰牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_PENG, pai, other_index)
        # 听牌提醒：
        self.can_ting(player['entity'].id)
        _shouPai = player[SHOU_PAI]
        _pengs = player[PENG_S]
        # 碰完不能小明杠
        # _xmg = check_xiao_ming_gang(_shouPai, _pengs)
        # if len(_xmg) != 0:
        #     player[ALLOW_OPT] |= OPT_XIAOMINGGANG_V
        #     self.callClientFunction(player["entity"].id, CLIENT_FUNC_XIAOMINGGANG, _xmg)
        self.notifyOutPai(player)

    def res_play_card_da_ming_gang_opt(self, player, pai):
        """

        :param player:
        :param pai:
        :return:
        """
        DEBUG_MSG('[RoomType5 id %i]------------->resOutPaiDaMingGangOpt CurPlayer=%s, Pai=%s' % (
            self.id, player['locationIndex'], pai))
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_DAMINGGANG_V
        self.operation_over()

    def da_ming_gang_opt(self, player, pai):
        DEBUG_MSG('[RoomType5 id %i]------------->daMingGangOpt CurPlayer=%s, Pai=%s' % (
            self.id, player['locationIndex'], pai))
        self.check_opt_pai(pai)
        _chapter = self.get_current_chapter()
        other_index = self.get_wait_player()['locationIndex']

        # 操作次数+1
        player[OPT_COUNT] += 1

        # 清除不可以碰的牌
        player[NOT_PENG_PAI].clear()

        da_ming_gang(player, pai, other_index)
        # 销毁check_results
        self.destroy_check_result(player)
        # 同步大明杠消息
        self.syncOpt(player['locationIndex'], SYNCOPT_DAMINGGANG, pai, other_index)
        # 给此玩家发牌
        self.deal_one_card(player, True)

    def res_out_pai_dian_pao_hu_opt(self, player):
        """
        点炮胡
        :param player:
        :return:
        """
        DEBUG_MSG(
            '[RoomType5 id %i]------------->resOutPaiDianPaoHuOpt CurPlayer=%s' % (self.id, player['locationIndex']))
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_HU_DIANPAO_V
        self.operation_over()

    def res_out_pai_ming_ci_hu_opt(self, player):
        """
        明次胡
        :param player:
        :return:
        """
        DEBUG_MSG('[RoomType5 id %i]------------>res_out_pai_ming_ci_hu_opt CurPlayer=%s' % (
            self.id, player['locationIndex']))
        # 玩家操作，检查过参数之后，删除系统超时操作
        self.del_play_card_timer()
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_HU_Ming_CI_V
        self.operation_over()

    def dianPaoHuOpt(self, players):
        DEBUG_MSG('[RoomType5 id %i]------------->dianPaoHuOpt CurPlayer=%s' % (self.id, players))
        # 要确保多个点炮胡操作顺序执行
        _chapter = self.get_current_chapter()
        _chapter[IS_DIAN_PAO__HE] = True
        fp_player = self.get_wait_player()

        _chapter[HU_TYPE] = HU_TYPE_DIAN_PAO
        # 同步点炮胡消息
        self.syncOpt(players[0]['locationIndex'], SYNCOPT_DIANPAOHU, _chapter[CUR_PAI], fp_player['locationIndex'])

        self.hu(players, fp_index=fp_player['locationIndex'])

    def xiao_ming_ci_hu_opt(self, player, xiao_ming_s):
        self.del_play_card_timer()
        _chapter = self.get_current_chapter()
        _chapter[IS_XIAO_MING_CI_HE] = True
        _chapter[HU_TYPE] = HU_TYPE_XIAO_MING_CI
        for xiao_ming in xiao_ming_s:
            other_index = xiao_ming_gang(player, xiao_ming)
            self.syncOpt(player['locationIndex'], SYNCOPT_XIAOMINGGANG, xiao_ming, other_index, is_ci=True)
        # 次牌加入玩家手牌
        player[SHOU_PAI].append(_chapter[CI_CARD])
        # 同步发牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_FAPAI, _chapter[CI_CARD], -1)
        # 给其他玩家发送胡牌消息
        self.syncOpt(player['locationIndex'], SYNC_OPT_XIAO_MING_CI, _chapter[CI_CARD], -1)
        # 胡牌结束，接收list，包装单个玩家
        self.hu([player])

    def ming_ci_hu_opt(self, player, card):
        """
        明次胡
        :param player:
        :return:
        """
        DEBUG_MSG('ming_ci_hu_opt player:%s' % player)
        _chapter = self.get_current_chapter()
        _chapter[IS_MING_CI_HE] = True
        _chapter[HU_TYPE] = HU_TYPE_MING_CI

        other_index = self.get_wait_player()['locationIndex']
        da_ming_gang(player, card, other_index)
        self.syncOpt(player['locationIndex'], SYNCOPT_DAMINGGANG, card, other_index, is_ci=True)

        # 次牌加入玩家手牌
        player[SHOU_PAI].append(_chapter[CI_CARD])
        # 同步发牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_FAPAI, _chapter[CI_CARD], -1)
        # 给其他玩家发送胡牌消息
        self.syncOpt(player['locationIndex'], SYNC_OPT_MING_CI, _chapter[CI_CARD], -1)
        # 胡牌结束，接收list，包装单个玩家
        self.hu([player])

    def an_ci_hu_opt(self, player, an_gang_s):
        """
        暗次胡
        :param player:
        :return:
        """
        self.del_play_card_timer()

        _chapter = self.get_current_chapter()
        _chapter[IS_AN_CI_HE] = True
        _chapter[HU_TYPE] = HU_TYPE_AN_CI
        # 移除杠牌,同步暗杠消息
        if an_gang_s:
            an_gang(player, an_gang_s[0])
            self.syncOpt(player['locationIndex'], SYNCOPT_ANGANG, an_gang_s[0], -1, is_ci=True)
        # 次牌加入玩家手牌
        player[SHOU_PAI].append(_chapter[CI_CARD])
        # 同步发牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_FAPAI, _chapter[CI_CARD], -1)
        # 给其他玩家发送胡牌消息
        self.syncOpt(player['locationIndex'], SYNC_OPT_AN_CI, _chapter[CI_CARD], -1)
        # 胡牌结束，接收list，包装单个玩家
        self.hu([player])

    def pi_ci_hu_opt(self, player):
        """
        皮次胡
        :param player:
        :return:
        """
        _chapter = self.get_current_chapter()
        _chapter[IS_PI_CI_HE] = True
        _chapter[HU_TYPE] = HU_TYPE_PI_CI
        # 次牌加入玩家手牌
        # player[SHOU_PAI].append(_chapter[CI_CARD])
        # 同步发牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_FAPAI, _chapter[CI_CARD], -1)
        # 给其他玩家发送胡牌消息
        self.syncOpt(player['locationIndex'], SYNC_OPT_PI_CI, _chapter[CI_CARD], -1)
        # 胡牌结束，接收list，包装单个玩家
        self.hu([player])

    # ---------------------  抢杠和操作  ---------------------

    def res_out_pai_qiang_gang_hu_opt(self, player):
        """
        抢杠胡
        :param player:
        :return:
        """
        DEBUG_MSG('[RoomType5 id %i]------------->resOutPaiQiangGangHuOpt CurPlayer=%s' % (self.id, player))
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_HU_QIANGGANG_V
        self.operation_over()

    def qiangGangHuOpt(self, players):
        DEBUG_MSG('[RoomType5 id %i]------------->qiangGangHuOpt CurPlayer=%s' % (self.id, players))
        _chapter = self.get_current_chapter()
        # 记录一下抢杠和
        _chapter[IS_QIANG_GANG_HE] = True
        fp_player = self.get_wait_player()

        _chapter[HU_TYPE] = HU_TYPE_QIANG_GANG
        # 同步抢杠和消息
        self.syncOpt(-1, SYNCOPT_QIANGGANGHU, _chapter[CUR_PAI], fp_player['locationIndex'])

        self.hu(players, fp_index=fp_player['locationIndex'])

    def hu(self, hu_players, fp_index=-1):
        """
        胡牌
        :param hu_players: hu_player=None时，表示荒庄
        :param fp_index: 放炮玩家的位置，-1 表示没人放炮
        :return:
        """
        _chapter = self.get_current_chapter()
        _chapter[HU_PLAYER] = hu_players
        _chapter[FANG_PAO_INDEX] = fp_index

        # if len(hu_players) != 0:
        #     if _chapter[IS_QIANG_GANG_HE]:
        #         # 同步抢杠和消息
        #         self.syncOpt(-1, SYNCOPT_QIANGGANGHU, _chapter[CUR_PAI], fp_index)
        # else:
        #     if len(hu_players) == 1:
        #         # 同步自摸消息
        #         self.syncOpt(hu_players[0]['locationIndex'], SYNCOPT_ZIMOHU, _chapter[CUR_PAI], -1)
        #     else:
        #         # 同步点炮胡消息
        #         self.syncOpt(-1, SYNCOPT_DIANPAOHU, _chapter[CUR_PAI], fp_index)
        # else:
        #     # 同步荒庄消息
        #     self.syncOpt(-1, SYNCOPT_HUANGZHUANG, -1, -1)
        DEBUG_MSG('[RoomType5 id %i]------------->HuOpt huIndex=%s, fangPaoIndex=%s' % (self.id, hu_players, fp_index))
        self.end_round()

    def can_ting(self, account_entity_id):
        """
        :param account_entity_id: 玩家id
        :return:
        """
        cards = list(range(0, 34))
        _chapter = self.get_current_chapter()
        player = self.get_current_player()
        if player['entity'].id != account_entity_id:
            return
        hand_cards = player[SHOU_PAI].copy()
        _hand_cards = player[SHOU_PAI].copy()
        DEBUG_MSG('Ting_tip hand_cards%s' % hand_cards)
        tip_cards = []
        _cards = []
        # 1.移除要出的牌      2.加入任意牌     3.移除杠牌      4.判断能不能胡    5.判断能不能次
        for _card in _hand_cards:
            play_card = _card
            if _card in _cards:
                _cards.append(_card)
                continue
            _cards.append(_card)
            if play_card in hand_cards:
                # 移除要出的牌
                hand_cards.remove(play_card)
                # 加入任意牌
                for card in cards:
                    temp = hand_cards.copy()
                    temp.append(card)

                    if not self.is_ying_ci():
                        # 平胡
                        can_hu = mj.AgariUtils.isHuPai(temp)
                        if can_hu and play_card not in tip_cards:
                            tip_cards.append(play_card)

                    # 明次
                    _ming_gang_s = check_can_ming_gang(temp)
                    for _ming_gang in _ming_gang_s:
                        t_ming = temp.copy()
                        remove_hand_card(t_ming, _ming_gang)
                        remove_hand_card(t_ming, _ming_gang)
                        remove_hand_card(t_ming, _ming_gang)

                        can_hu = mj.AgariUtils.isHuPai(t_ming)
                        if can_hu and card == _chapter[CI_CARD]:
                            if _ming_gang not in tip_cards:
                                tip_cards.append(play_card)

                    # 暗次胡
                    _an_gang_s = check_an_gang(temp)
                    # 剔除暗杠
                    for _an_gang in _an_gang_s:
                        t_an = temp.copy()
                        remove_hand_card(t_an, _an_gang)
                        remove_hand_card(t_an, _an_gang)
                        remove_hand_card(t_an, _an_gang)
                        remove_hand_card(t_an, _an_gang)
                        t_an.append(_chapter[CI_CARD])

                        can_hu = mj.AgariUtils.isHuPai(t_an)
                        if can_hu:
                            if card not in tip_cards:
                                tip_cards.append(play_card)

                    # 小明次胡
                    xiao_ming_s = check_xiao_ming_gang(temp, player[PENG_S])
                    for _xiao_ming in xiao_ming_s:
                        t_xiao = temp.copy()
                        remove_hand_card(t_xiao, _xiao_ming)
                        t_xiao.append(_chapter[CI_CARD])

                        can_hu = mj.AgariUtils.isHuPai(t_xiao)
                        if can_hu:
                            if card not in tip_cards:
                                tip_cards.append(play_card)
                hand_cards.append(play_card)

        # 皮次判断
        if hand_cards.count(_chapter[CI_CARD]) == 2:
            tip_cards = _hand_cards
            tip_cards.remove(_chapter[CI_CARD])
            tip_cards.remove(_chapter[CI_CARD])

        DEBUG_MSG('听牌结果：%s' % tip_cards)
        self.callClientFunction(player['entity'].id, CLIENT_FUNC_TINGPAI, tip_cards)

    def hu_tip(self, account_entity_id, play_card):
        """
        胡牌提示
        :param account_entity_id:
        :param play_card:
        :return:
        """
        cards = list(range(0, 34))
        _chapter = self.get_current_chapter()
        player = self.get_current_player()
        if player['entity'].id != account_entity_id:
            return
        hand_cards = player[SHOU_PAI].copy()
        DEBUG_MSG('hu_tip hand_cards %s clicked card%s' % (hand_cards, play_card))
        tip_cards = []
        # 1.移除要出的牌      2.加入任意牌     3.移除杠牌      4.判断能不能胡    5.判断能不能次
        if play_card in hand_cards:
            # 移除要出的牌
            hand_cards.remove(play_card)

            # 加入任意牌
            for card in cards:
                temp = hand_cards.copy()
                temp.append(card)

                if not self.is_ying_ci():
                    # 平胡
                    can_hu = mj.AgariUtils.isHuPai(temp)
                    if can_hu:
                        tip_cards.append(card)

                # 明次
                _ming_gang_s = check_can_ming_gang(temp)
                for _ming_gang in _ming_gang_s:
                    t_ming = temp.copy()
                    remove_hand_card(t_ming, _ming_gang)
                    remove_hand_card(t_ming, _ming_gang)
                    remove_hand_card(t_ming, _ming_gang)

                    can_hu = mj.AgariUtils.isHuPai(t_ming)
                    if can_hu and card == _chapter[CI_CARD]:
                        if _ming_gang not in tip_cards:
                            tip_cards.append(_ming_gang)

                # 暗次胡
                _an_gang_s = check_an_gang(temp)
                # 剔除暗杠
                for _an_gang in _an_gang_s:
                    t_an = temp.copy()
                    remove_hand_card(t_an, _an_gang)
                    remove_hand_card(t_an, _an_gang)
                    remove_hand_card(t_an, _an_gang)
                    remove_hand_card(t_an, _an_gang)
                    t_an.append(_chapter[CI_CARD])

                    can_hu = mj.AgariUtils.isHuPai(t_an)
                    if can_hu:
                        if card not in tip_cards:
                            tip_cards.append(card)

                # 小明次胡
                xiao_ming_s = check_xiao_ming_gang(temp, player[PENG_S])
                for _xiao_ming in xiao_ming_s:
                    t_xiao = temp.copy()
                    remove_hand_card(t_xiao, _xiao_ming)
                    t_xiao.append(_chapter[CI_CARD])

                    can_hu = mj.AgariUtils.isHuPai(t_xiao)
                    if can_hu:
                        if card not in tip_cards:
                            tip_cards.append(card)

            # 皮次判断
            if hand_cards.count(_chapter[CI_CARD]) == 2 and _chapter[CI_CARD] not in tip_cards:
                tip_cards.append(_chapter[CI_CARD])

        card_info = {}
        for card in tip_cards:
            card_info[str(card)] = self.get_card_count_un_reveal(card, exclude_player=account_entity_id)
        self.callClientFunction(account_entity_id, 'HuTip', {'huCards': card_info})

    # --------------------------------------------------------------------------------------------
    #                            依赖牌局上下文的牌型判断
    # --------------------------------------------------------------------------------------------

    # 群主解散房间通知

    def tea_house_disband_room_by_creator(self):
        """
        解散房间
        :return:
        """
        _chapter = self.chapters[self.cn]
        players = _chapter[PLAYER_IN_GAME].copy()
        self.disband_from_creator = True
        if not self.started:
            for _p in players.values():
                self.onLeave(_p['entity'].id)
            else:
                self.autoDestroy()
            return

        if self.chapters[self.cn]["chapterState"] != 4:
            self.total_settlement(is_disband=True)

    def autoDestroy(self):
        """
        自动销毁房间
        :return:
        """
        chapter = self.chapters[self.cn]
        # 如果坐下玩家不存在真实玩家则自动解散
        for k, v in chapter[PLAYER_IN_GAME].items():
            if v["entity"].info["isBot"] == 0:
                return

        # 比赛场手动解散通知 base 解散房间
        if self.is_tea_house_room:

            # 手动解散
            if self.is_manual_disband:
                self.base.cellToBase({"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                                      "teaHouseId": self.info["teaHouseId"]})
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                return

            # 群主解散,会先从冠名赛房间列表移除，所以可以直接摧毁
            if self.disband_from_creator:
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                self.destroySpace()
                return

            # 比赛场总结算，通知冠名赛移除房间并摧毁实体
            if self.total_settlement_ed:
                self.base.cellToBase({"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                                      "teaHouseId": self.info["teaHouseId"]})
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                return

            # 如果房间中没有人，房间已开始，解散
            if self.started:
                self.base.cellToBase({"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                                      "teaHouseId": self.info["teaHouseId"]})
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                return

        elif self.is_gold_session_room():
            # 如果是手动解散房间或者总结算，或者房间开始却没有人，解散房间
            if self.is_manual_disband or self.total_settlement_ed or self.started:
                self.base.cellToBase(
                    {"func": "disbandGoldSessionRoom", "roomId": self.info["roomId"], "level": self.info["level"]})

        # 普通房间正常解散
        elif self.info["roomType"] == "card":
            # 一局都没结算并且为房主支付，归还钻石
            if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                self.base.cellToBase({"func": "returnRoomCardToCreator"})
            # 代开房间先通知base从代开房间列表移除
            if "substitute" in self.info and self.info["substitute"]:
                self.base.cellToBase(
                    {"func": "disbandSubstituteRoom", "roomInfo": self.info, "creator": self.info["creator"]})
            else:
                self.destroySpace()

    def check_bao_ci(self):
        """
        检查是否需要开启包次
        :return:
        """
        _chapter = self.get_current_chapter()
        if len(_chapter[CARDS_LIB]) <= 10 and self.bao_ci_switch() and not _chapter['startBaoCi']:
            _chapter['startBaoCi'] = True
            self.callOtherClientsFunction('StartBaoCi', {})

    def bao_ci_switch(self):
        """
        包次开关
        :return:
        """
        return 2 in self.info['playingMethod']

    def xia_mi_switch(self):
        """
        下米开关
        :return:
        """
        return 4 in self.info['playingMethod']

    def dai_feng_switch(self):
        """
        带风开关
        :return:
        """
        return 3 in self.info['playingMethod']

    def zhuang_jia_bei(self):
        """
        庄加倍开关
        :return:
        """
        return 1 in self.info['playingMethod']

    def bu_ci_feng(self):
        """
        不次风开关
        :return:
        """
        return 0 in self.info['playingMethod']

    def is_ying_ci(self):
        """
        是否是硬次
        :return:
        """
        return self.info["softOrHardCi"] == 0

    def refresh_gold(self, account_db_id, count, isModify=False):
        """
        刷新房间内金币
        :param isModify: 是否是修改金币
        :param account_db_id:
        :param count:
        :return:
        """
        _chapter = self.chapters[self.cn]
        if self.info["roomType"] == "normalGameCoin" or self.info["roomType"] == "card":
            for k, v in _chapter[PLAYER_IN_GAME].items():
                if v["entity"].info["dataBaseId"] == account_db_id:
                    if isModify:
                        v["baseSyncGoldChange"] += count
                    break
        self.sync_gold()

    def refresh_game_coin(self, account_db_id, modify_count):
        """
        增加房间内比赛分
        :param account_db_id:
        :param modify_count:
        :return:
        """
        _chapter = self.chapters[self.cn]
        if self.info["roomType"] == "gameCoin":
            for k, v in _chapter[PLAYER_IN_GAME].items():
                if v["entity"].info["dataBaseId"] == account_db_id:
                    v["baseSyncGoldChange"] += modify_count
                    break
        self.sync_gold()

        # 如果都满足准备条件，关闭倒计时
        all_can_ready = self.check_ready_gold_disband()
        if all_can_ready:
            self.delTimer(self.ready_gold_disband_timer)
            self.ready_gold_disband_timer = -1

    def on_account_cell_destroy(self, account_db_id):
        """
        房间中的玩家被销毁
        :param account_db_id:
        :return:
        """
        DEBUG_MSG('RoomType5 cell on_account_cell_destroy account_db_id:%s' % account_db_id)
        _chapter = self.get_current_chapter()
        all_death = True
        for p in _chapter[PLAYER_IN_GAME].values():
            if p['entity']:
                all_death = False
                break
        # 如果房间中没有人，房间已开始，解散
        if self.started and all_death:
            self.base.cellToBase(
                {"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"], "teaHouseId": self.info["teaHouseId"]})
            # 一局都没结算并且为房主支付，归还钻石
            if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                self.base.cellToBase({"func": "returnRoomCardToCreator"})
            return
        pass

    def set_losing_streak_history(self, _player, is_loser):
        if is_loser:
            _player['entity'].info['losingstreak'] += 1
        else:
            _player['entity'].info['losingstreak'] = 0

    def get_max_losing_streak_player(self, players):
        max_losing_streak_count = 0
        max_losing_streak_player = None
        for p in players:
            if p['entity'].info['losingstreak'] > max_losing_streak_count:
                max_losing_streak_count = p['entity'].info['losingstreak']
                max_losing_streak_player = p
        return max_losing_streak_player, max_losing_streak_count

    def set_losing_streak_count_in_base(self, players_dic):
        """
        连输信息也同步到BASE
        总结算时同步一次，打牌时在cell端统计
        """
        for k, v in players_dic.items():
            v["entity"].base.cellToBase({"func": "setLosingStreakCount", "count": v['entity'].info['losingstreak']})

    def save_record_str(self):
        game_type = '杠次麻将'
        current_chapter = self.settlement_count
        max_chapter_count = self.info['maxChapterCount']
        chapter = self.get_current_chapter()
        _plays = chapter[PLAYER_IN_GAME]
        total_settlement_info = []
        for p in _plays.values():
            _dict = {'name': p['entity'].info['name'], 'totalGoldChange': p['totalGoldChange']}
            total_settlement_info.append(_dict)
        self.record_str = self.get_chapter_record_str(game_type, current_chapter,
                                                      max_chapter_count, total_settlement_info)

    @property
    def is_less_mode(self):
        if not self.info['fewPersonPattern']:
            return False
        if self.started:
            return True
        chapter = self.get_current_chapter()
        players = chapter[PLAYER_IN_GAME]
        if len(players) == len(self.agree_less_person_mode_players):
            return True
        return False


# --------------------------------------------------------------------------------------------
#                            操作集合
# --------------------------------------------------------------------------------------------


def getPriority(check_result, sequence):
    """
    根据检查得出的操作结果和位置顺序；返回一个值，值越大，优先级越高
    :param check_result:
    :param sequence:
    :return:
    """
    p = sequence
    if check_result[CHECK_HU]:
        p += HU_WEIGHT
    elif check_result[CHECK_DAMINGGANG]:
        p += GANG_WEIGHT
    elif check_result[CHECK_PENG]:
        p += PENG_WEIGHT
    return p


# --------------------------------------------------------------------------------------------
#                            吃、碰、小明杠、大明杠
# --------------------------------------------------------------------------------------------

def check_chi(hand_cards, check_pai):
    """
    :param hand_cards: 手牌
    :param check_pai: 待检查的牌
    :return: 可以吃的数组 如：[1,2],1就代表1,2,3;2就代表2,3,4
    """
    ret = []
    if check_pai > WAN_9:
        return ret
    _type = check_pai // 9
    pais = get_card_by_type(hand_cards, _type)
    has1 = (check_pai - 2) in pais
    has2 = (check_pai - 1) in pais
    has3 = (check_pai + 1) in pais
    has4 = (check_pai + 2) in pais
    if has1:
        if has2:
            ret.append(check_pai - 2)
    if has2:
        if has3:
            ret.append(check_pai - 1)
    if has3:
        if has4:
            ret.append(check_pai)

    return ret


def chi(player, chi_pai, cur_pai, other_index):
    """
    :param player:
    :param chi_pai: 第一张牌
    :param cur_pai: 吃的哪张牌
    :param other_index: 打出这张牌的玩家位置
    :return:
    """
    _chis = player[CHIS]
    _shouPai = player[SHOU_PAI]

    chi_pais = [chi_pai, chi_pai + 1, chi_pai + 2]

    for p in chi_pais:
        if cur_pai == p:
            continue
        remove_hand_card(_shouPai, p)

    _chis[chi_pais[0]] = (cur_pai, other_index)


def get_card_by_type(cards, _type):
    """
    获取牌的牌型
    :param cards:
    :param _type:
    :return:
    """
    ret = []
    _m = 0
    for p in cards:
        _m = p // 9
        if _m == _type:
            ret.append(p)
    return ret


def check_peng(hand_cards, check_card):
    """
    :param hand_cards: 手牌
    :param check_card: 是否可以碰这张牌
    :return: true 可以碰
    """
    count = get_card_count_from(hand_cards, check_card)
    if count >= 2:
        return True
    else:
        return False


def check_pi_ci(hand_cards, ci_card):
    """
    检查是否皮次
    :param hand_cards:
    :param ci_card:
    :return:
    """
    return hand_cards.count(ci_card) == 3


def check_win_ci(hand_cards, ci_card):
    """
    检查是否赢次牌
    :param ci_card: 次牌
    :param hand_cards: 手牌
    :return: true 可以碰
    """
    DEBUG_MSG('check_win_ci hand_cards:%s ci_cards:%s' % (hand_cards, ci_card))
    # 把四张拆开判断能不能赢
    _can_hu = mj.AgariUtils.isHuPai(hand_cards, pai=ci_card)
    if _can_hu:
        return True

    # 找到所有四张
    already_check = []
    four = []
    for c in hand_cards:
        if c in already_check:
            continue
        count = get_card_count_from(hand_cards, c)
        if count == 4:
            four.append(c)
        already_check.append(c)

    # 挨个移除四张，判断能不能赢
    for _an_gang in four:
        temp = hand_cards.copy()
        remove_hand_card(temp, _an_gang)
        remove_hand_card(temp, _an_gang)
        remove_hand_card(temp, _an_gang)
        remove_hand_card(temp, _an_gang)
        # 判胡，发牌不增加次牌
        _can_hu = mj.AgariUtils.isHuPai(temp, pai=ci_card)
        if _can_hu:
            return True
        DEBUG_MSG('check_win_ci temp%s, can_hu%s' % (temp, _can_hu))

    # 移除全部四张，判断能不能赢
    temp = hand_cards.copy()
    for _an_gang in four:
        remove_hand_card(temp, _an_gang)
        remove_hand_card(temp, _an_gang)
        remove_hand_card(temp, _an_gang)
        remove_hand_card(temp, _an_gang)

    # 判胡，发牌不增加次牌
    _can_hu = mj.AgariUtils.isHuPai(temp, pai=ci_card)
    DEBUG_MSG('check_win_ci temp%s, can_hu%s' % (temp, _can_hu))
    return _can_hu


def peng(player, card, otherIndex):
    """
    碰操作
    :param player: 当前操作的玩家
    :param card: 要碰的牌
    :param otherIndex: 打出这张牌的玩家的位置
    """
    _pengs = player[PENG_S]
    hand_cards = player[SHOU_PAI]

    remove_hand_card(hand_cards, card)
    remove_hand_card(hand_cards, card)

    _pengs[card] = otherIndex


def check_xiao_ming_gang(hand_cards, pengs):
    """
    检查小明杠数量
    :param hand_cards: 手牌
    :param pengs: 当前手牌中所有的碰牌集合
    :return: 数组，可以小明杠的牌(可能有多个)
    """
    ret = []
    for p in pengs:
        count = get_card_count_from(hand_cards, p)
        if count >= 1:
            ret.append(p)
    return ret


def xiao_ming_gang(player, card):
    """
    小明杠操作
    :param player: 当前操作的玩家
    :param card: 要小明杠的牌
    """
    _pengs = player[PENG_S]
    hand_cards = player[SHOU_PAI]
    _xiaoMingGangs = player[XIAO_MING_GANG_S]

    other_index = _pengs.pop(card)
    remove_hand_card(hand_cards, card)

    _xiaoMingGangs[card] = other_index
    return other_index


def get_last_xiao_ming_gang(player):
    """
    返回最后一个触发小明杠的玩家
    :param player:
    :return:
    """
    _xiaoMingGangs = player[XIAO_MING_GANG_S]
    _i = -1
    for pai, _index in _xiaoMingGangs.items():
        _i = _index
    return _i


def check_da_ming_gang(hand_cards, check_card):
    """
    判断是否能大明杠
    :param hand_cards: 手牌
    :param check_card: 是否可以大明杠这张牌
    :return: true 可以大明杠
    """
    count = get_card_count_from(hand_cards, check_card)
    if count >= 3:
        return True
    else:
        return False


def da_ming_gang(player, pai, otherIndex):
    """
    大明杠操作
    :param player: 当前操作的玩家
    :param pai: 要大明杠的牌
    :param otherIndex: 打出这张牌的玩家
    """
    hand_cards = player[SHOU_PAI]
    _daMingGangs = player[DA_MING_GANG_S]

    remove_hand_card(hand_cards, pai)
    remove_hand_card(hand_cards, pai)
    remove_hand_card(hand_cards, pai)

    _daMingGangs[pai] = otherIndex


def get_last_da_ming_gang(player):
    """
    返回最后一个触发大明杠的玩家
    :param player:
    :return:
    """
    _daMingGangs = player[DA_MING_GANG_S]
    _i = -1
    for pai, _index in _daMingGangs.items():
        _i = _index
    return _i


def check_can_ming_gang(hand_cards):
    """
    检测可以明杠的牌
    :param hand_cards:
    :return:
    """
    three = []
    for c in hand_cards:
        if hand_cards.count(c) == 3 and c not in three:
            three.append(c)
    return three


def check_an_gang(hand_cards):
    """
    :param hand_cards: 手牌
    :return: 数组，可以暗杠的牌（可能有多个）
    """
    already_check = []
    an = []
    for c in hand_cards:
        if c in already_check:
            continue
        count = get_card_count_from(hand_cards, c)
        if count == 4:
            an.append(c)
        already_check.append(c)
    return an


def an_gang(player, card):
    """
    :param player: 当前操作的玩家
    :param card: 要暗杠的牌
    """
    _hand_cards = player[SHOU_PAI]
    _anGangs = player[AN_GANG_S]
    if _hand_cards.count(card) != 4:
        return
    remove_hand_card(_hand_cards, card)
    remove_hand_card(_hand_cards, card)
    remove_hand_card(_hand_cards, card)
    remove_hand_card(_hand_cards, card)

    _anGangs.append(card)


def get_card_count_from(hand_cards, card):
    """
    获取手牌中指定牌的数量
    :param hand_cards: 手牌
    :param card: 指定的牌
    :return: 指定牌的数量
    """
    count = 0
    for c in hand_cards:
        if c == card:
            count += 1
    return count


def remove_hand_card(hand_cards, card):
    """
    移除手牌
    :param hand_cards: 手牌
    :param card: 要移除的牌
    """
    if card in hand_cards:
        hand_cards.remove(card)


def add_hand_cards(hand_cards, card):
    """
    把一张牌加入手牌
    :param hand_cards: 手牌
    :param card: 要添加的牌
    """
    DEBUG_MSG('add_hand_cards len hand_cards%s' % len(hand_cards))
    if len(hand_cards) <= 13:
        hand_cards.append(card)


def check_cards(card):
    """
    检查牌的合法性
    :param card:
    :return:
    """
    if card < TONG_1 or card > SUNYUAN_BAI:
        raise Exception("error pai: %s" % card)


def is_shun_zi(cards):
    """
    是否是顺子
    :param cards:
    :return:
    """
    if (cards is None) or (len(cards) != 3):
        return False
    _t = cards[0] // 9
    if _t < 0 or _t > 2:
        return False
    cards.sort()
    for i, p in enumerate(cards):
        _m = p // 9
        if _m == _t:
            if i == 2:
                break
            if (p + 1) == cards[i + 1]:
                continue
        return False
    return True
