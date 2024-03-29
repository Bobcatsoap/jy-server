# -*- coding: utf-8 -*-
import datetime

import KBEngine
from KBEDebug import *

# import sys
# sys.path.append("D:/gjsoft/kbengine-bicc/assets/scripts/common")
import Const

from RoomBase import *
import mj.MohjangCalculator
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
OPT_HU_DIAN_PAO = "resOutPaiDianPaoHuOpt"
OPT_HU_DIAN_PAO_V = 1 << 8
# 抢杠和
OPT_HU_QIANG_GANG = "resOutPaiQiangGangHuOpt"
OPT_HU_QIANGGANG_V = 1 << 9
# 玩家操作的牌
PLAYER_OPT_PAI = "pai"

OPT_DICT = {OPT_OUT: OPT_OUT_V,
            OPT_GUO: OPT_GUO_V,
            OPT_CHI: OPT_CHI_V,
            OPT_PENG: OPT_PENG_V,
            OPT_XIAOMINGGANG: OPT_XIAOMINGGANG_V,
            OPT_DAMINGGANG: OPT_DAMINGGANG_V,
            OPT_ANGANG: OPT_ANGANG_V,
            OPT_HU_ZIMO: OPT_HU_ZIMO_V,
            OPT_HU_DIAN_PAO: OPT_HU_DIAN_PAO_V,
            OPT_HU_QIANG_GANG: OPT_HU_QIANGGANG_V}

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
# 是否能听
IS_TING = "isTing"
# 是否抢杠和
IS_QIANG_GANG_HE = "isQiangGangHe"
# 是否是点炮胡
IS_DIAN_PAO_HE = "isDianPaoHe"
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
# 混牌
HUN_PAIS = "hunPais"
# 荒庄余留数
HUANG_ZHUANG_LEFT_COUNT = "huangZhuangLeftCount"

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
# 下跑数
XIA_PAO_COUNT = "xiaPaoCount"
# 结算临时数据
SETTLEMENT_DATA = "settlement"

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
# func: dphOptPrompt args: boolean
CLIENT_FUNC_DIANPAOHU = "dphOptPrompt"
# func: qghOptPrompt args: boolean
CLIENT_FUNC_QIANGGANGHU = "qghOptPrompt"
# func: gOptPrompt args: 无
CLIENT_FUNC_GUO = "gOptPrompt"
# 听牌提醒
CLIENT_FUNC_TINGPAI = 'tpOptPrompt'

# 提醒客户端出牌 func: notifyOutPai args:[],未完成
CLIENT_FUNC_NOTIFYOUTPAI = "notifyOutPai"

# 超时操作时间
AUTO_TIME = 60
# 超时解散时间
AUTO_DISSOLVE_TIME = 90
RESTART_TIME = 45
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

# 特殊规则倍数
# special_multiple = {}


# # 吃和碰之后，出牌超时定时器
# CP_OUT_PAI_TIMER = "chiPengOutPaiTimer"
# # 吃和碰之后，机器人出牌定时器
# BOT_CP_OUT_PAI_TIMER = "botChiPengOutPaiTimer"

# 牌局状态
CHAPTER_STATE_INIT = -1
CHAPTER_STATE_READY = 0
CHAPTER_STATE_START = 1
CHAPTER_STATE_XIA_PAO = 2
CHAPTER_STATE_FAN_HUN = 3
CHAPTER_STATE_DEAL = 4
CHAPTER_STATE_PLAY = 5
CHAPTER_STATE_SETTLEMENT = 6
CHAPTER_STATE_TOTAL_SETTLEMENT = 7

# 胡牌类型
HU_RESULT_SEVEN_PAIR = 1
HU_RESULT_FOUR_HUN = 2
HU_RESULT_GANG_SHANG_HUA = 4
HU_RESULT_PING_HU = 3


class CurrentChapter:
    def __init__(self, chapter):
        self._chapter = chapter

    def start_chapter(self, chapter):
        self._chapter = chapter

    def end_chapter(self):
        self._chapter = None

    @property
    def hun_pais(self):
        return self._chapter[HUN_PAIS]

    @hun_pais.setter
    def hun_pais(self, hun_pais):
        self._chapter[HUN_PAIS] = hun_pais

    @property
    def players(self):
        return self._chapter[PLAYER_IN_GAME]

    @property
    def card_lib(self):
        return self._chapter[CARDS_LIB]

    @property
    def chapter_state(self):
        return self._chapter["chapterState"]

    @chapter_state.setter
    def chapter_state(self):
        return self._chapter["chapterState"]


class RoomConfig:
    def __init__(self, info):
        self._info = info

    @property
    def hun_pai_type(self):
        """
        0：不带混
        1:单混
        2：双混
        :return:
        """
        return self._info["allpowerfulType"]

    @property
    def is_double_hun_type(self):
        return self._info["allpowerfulType"] == 2

    @property
    def is_use_hun_pai(self):
        return self._info["allpowerfulType"] != 0

    @property
    def is_have_wind(self):
        return self._info["haveWind"]

    @property
    def xia_pao_type(self):
        """
        :return: 0：不带跑；1：每局下跑；2：每四局下跑；3：固定跑
        """
        if self._info["redoubleType"] == 0:
            return 0
        elif self._info["redoubleType"] == -1:
            return 1 if self._info["redoubleWay"] == 0 else 2
        elif self._info["redoubleType"] == 1:
            return 3
        else:
            pass

    @property
    def xia_pao_num(self):
        return self._info["redoubleNum"]

    @property
    def is_zi_mo_hu(self):
        return self._info["huType"] == 1

    @property
    def gang_di_score(self):
        return self._info["gangDiScore"]

    @property
    def zi_mo_score(self):
        return self._info["ziMoScore"]

    @property
    def dian_pao_score(self):
        return self._info["dianPaoScore"]

    @property
    def is_banker_add_di(self):
        return self._info["bankerAdd"]

    @property
    def is_seven_pair_add_double(self):
        return self._info["sevenPairSredouble"]

    @property
    def is_gang_kai_hua_add_double(self):
        return self._info["bloomSredouble"]

    @property
    def is_hvae_gang_pao(self):
        return self._info["gangRun"]

    @property
    def is_allow_qiang_gang_hu(self):
        return self._info["robGangHu"]


class GamePlayer:
    def __init__(self, player):
        self._player = player

    def peng(self, card, other_player):
        """
        碰操作
        :param player: 当前操作的玩家
        :param card: 要碰的牌
        :param otherIndex: 打出这张牌的玩家的位置
        """
        _pengs = self._player[PENG_S]
        hand_cards = self._player[SHOU_PAI]

        remove_hand_card(hand_cards, card)
        remove_hand_card(hand_cards, card)

        other_index = other_player['locationIndex']
        _pengs[card] = other_index
        other_player[OUT_PAIS].remove(card)

    def xiao_ming_gang(self, card):
        """
        小明杠操作
        :param player: 当前操作的玩家
        :param card: 要小明杠的牌
        """
        _pengs = self._player[PENG_S]
        hand_cards = self._player[SHOU_PAI]
        _xiaoMingGangs = self._player[XIAO_MING_GANG_S]

        other_index = _pengs.pop(card)
        remove_hand_card(hand_cards, card)

        _xiaoMingGangs[card] = other_index

        return other_index

    def da_ming_gang(self, card, other_player):
        """
        大明杠操作
        :param player: 当前操作的玩家
        :param card: 要大明杠的牌
        :param otherIndex: 打出这张牌的玩家
        """
        hand_cards = self._player[SHOU_PAI]
        _daMingGangs = self._player[DA_MING_GANG_S]

        remove_hand_card(hand_cards, card)
        remove_hand_card(hand_cards, card)
        remove_hand_card(hand_cards, card)

        other_index = other_player['locationIndex']
        _daMingGangs[card] = other_index

        other_player[OUT_PAIS].remove(card)

    def an_gang(self, card):
        """
        :param player: 当前操作的玩家
        :param card: 要暗杠的牌
        """
        _hand_cards = self._player[SHOU_PAI]
        _anGangs = self._player[AN_GANG_S]
        if _hand_cards.count(card) != 4:
            return
        remove_hand_card(_hand_cards, card)
        remove_hand_card(_hand_cards, card)
        remove_hand_card(_hand_cards, card)
        remove_hand_card(_hand_cards, card)

        _anGangs.append(card)


class RoomType14(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)
        self.wait_to_seat = []

    # --------------------------------------------------------------------------------------------
    #                            父类方法
    # --------------------------------------------------------------------------------------------
    def newChapter(self, maxPlayerCount=100, dissolveDeadLine=-1, dissolveTimer=-1):
        """
        :param maxPlayerCount:
        :return:
        """
        _chapter = RoomBase.newChapter(self, maxPlayerCount)
        self.room_cfg = RoomConfig(self.info)
        # 牌局所有计时器id
        _chapter["timers"] = {
            # 牌局主计时器
            "main": -1,
            # 机器人下注计时器
            "botBet": -1,
        }
        _chapter[CUR_PLAYER] = None
        _chapter[WAIT_PLAYER] = None
        _chapter[PLAYER_IN_GAME] = {}
        _chapter[PLAYER_OUT_GAME] = {}
        _chapter[CUR_PAI] = None
        _chapter[CHECK_RESULTS] = None
        _chapter[HU_PLAYER] = None
        _chapter[FANG_PAO_INDEX] = -1
        _chapter[SEAT] = list(range(self.info['maxPlayersCount']))
        _chapter[SEAT_TO_PLAYER] = {}
        _chapter[BANKER_LOCATION] = 1
        _chapter[ROUND] = []
        _chapter[ALLOW_OPT_PLAYERS] = []
        _chapter[IS_QIANG_GANG_HE] = False
        _chapter[IS_DIAN_PAO_HE] = False
        _chapter[IS_ZI_MO_HE] = False
        _chapter[IS_HUANG_ZHUANG] = False
        _chapter[IS_GANG_SHANG_KAI_HUA] = -1
        # 定时器相关
        _chapter["mainTimer"] = -1
        _chapter[BOT_OUT_PAI_TIMER] = -1
        _chapter['resOutPaiTimer'] = -1
        # 抢杠胡计时器
        _chapter['qiangGangTimer'] = -1
        _chapter['settlementTimer'] = -1
        _chapter['autoReadyTimer'] = -1
        _chapter['deadLine'] = -1
        _chapter['dissolveDeadLine'] = dissolveDeadLine
        _chapter['playCardTimer'] = -1
        _chapter['restartTimer'] = -1
        _chapter["xiaPaoTimer"] = -1
        _chapter["fanHunTimer"] = -1
        _chapter['qiangGangCard'] = -1
        _chapter['settlementClearPlayers'] = -1
        _chapter[INNER_BOT_OPT_TIMERS] = {}
        _chapter[LEFT_PAI_COUNT] = -1
        _chapter['dissolveTimer'] = dissolveTimer
        _chapter[ROOM_MASTER] = None
        _chapter[HU_TYPE] = -1
        _chapter[HUN_PAIS] = []
        _chapter['replay'] = []
        _chapter[HUANG_ZHUANG_LEFT_COUNT] = 1 if self.room_cfg.hun_pai_type == 0 else 14
        self.current_chapter = CurrentChapter(_chapter)
        self.hu_special_multiple = {}
        if self.cn == 0:
            _chapter["mainTimer"] = self.addTimer(1, 1, 0)

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

        if _chapter['chapterState'] == CHAPTER_STATE_READY and len(_chapter[SEAT]) != 0 and not self.started \
                and len(_chapter[PLAYER_IN_GAME]) < _info["maxPlayersCount"]:
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
        # 如果是玩家就移除此玩家
        _player = self.get_player_by_entity_id(accountEntityId)
        _chapter = self.get_current_chapter()
        _player_out_game = _chapter[PLAYER_OUT_GAME]
        _chapter_state = self.get_current_chapter()["chapterState"]
        if _player:
            if _player[SEAT] == -1:
                if accountEntityId in _player_out_game and accountEntityId in self.wait_to_seat \
                        and _chapter_state != CHAPTER_STATE_READY and _chapter_state != CHAPTER_STATE_TOTAL_SETTLEMENT:
                    self.callClientFunction(accountEntityId, 'Notice', ['已坐下，暂时无法离开房间'])
                    return
                self.remove_witness_player(_player)
            else:
                # 如果游戏已开始，无法退出
                if _chapter_state != CHAPTER_STATE_READY and _chapter_state != CHAPTER_STATE_TOTAL_SETTLEMENT:
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
        # 通知所有客户端座位信息
        if _chapter_state == CHAPTER_STATE_READY:
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

    def newPlayer(self, accountEntity, total_gold_change=0, base_sync_gold_change=0, agree_disband=-1):
        """
        :param base_sync_gold_change: 房间外金币同步
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
            # 比赛分场修改使用比赛分为使用金币
            _gold = accountEntity.accountMutableInfo["gold"]
        DEBUG_MSG('new player totalGoldChange %s' % total_gold_change)
        _player = {'locationIndex': -1,
                   'entity': accountEntity,
                   'isReady': False,
                   'cards': [],
                   'winnerBilling': 0,
                   'otherBilling': 0,
                   'overBilling': 0,
                   'continue': False,
                   'special': [],
                   'qiDianPao': False,
                   'canNotXMGang': [],
                   'totalGoldChange': total_gold_change,
                   # 房间外上币统计
                   'baseSyncGoldChange': base_sync_gold_change,
                   # 是否已经扣过AA支付的钻石
                   'AARoomCardConsumed': False}
        # 钻石场
        if self.info["roomType"] == "card":
            _player["gold"] = accountEntity.accountMutableInfo["gold"]
        # 比赛分场
        elif self.info["roomType"] == "gameCoin":
            _player["gold"] = accountEntity.accountMutableInfo["gameCoin"]
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
        _player[XIAO_MING_GANG_S] = {}
        _player[DA_MING_GANG_S] = {}
        _player[AN_GANG_S] = []
        _player[OUT_PAIS] = []
        _player[SEAT] = -1
        _player[OPT_COUNT] = 0
        _player[HUA_PAI] = []
        _player[HUA_COUNT] = 0
        _player[NOT_HU_PAI] = []
        # _player[NOT_PENG_PAI] = []
        _player[CAN_HU] = False
        _player[QI_HU] = False
        _player[CAN_PENG] = False
        _player[IS_TING] = False
        _player[TIMER] = -1
        _player[ALLOW_OPT] = 0
        _player[PAI_TYPES] = []
        settle1 = {}
        settle1['goldChange'] = 0
        settle1['huGoldChange'] = 0
        settle1['gangGoldChange'] = 0
        _player[SETTLEMENT_DATA] = settle1
        _player[IS_ARGEE] = agree_disband
        _player[WAI_GUA_SELECT_PAI] = -1
        _player[CHECK_RESULT] = None
        _player[DIAN_PAO_COUNT] = 0
        _player[XIA_PAO_COUNT] = -1
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
        self.statisticalData = {
            SD_BIG_WINNER_INDEX: -1,
            SD_PLAYERS: {}
        }

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
        DEBUG_MSG('[RoomType14 id %i]------->addPlayerInSD player:%s.' % (self.id, player))
        sd[SD_PLAYERS][player['locationIndex']] = {
            SD_LOCATION_INDEX: player['locationIndex'],
            SD_USER_ID: player["entity"].info["userId"],
            SD_ENTITY_ID: player["entity"].id,
            # SD_NAME: player["entity"].name,
            SD_ZI_MO_COUNT: 0,
            SD_DIAN_PAO_COUNT: 0,
            SD_FANG_PAO_COUNT: 0,
            SD_AN_GANG_COUNT: 0,
            SD_MING_GANG_COUNT: 0,
            SD_MO_HUA_COUNT: 0,

        }

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
        if _chapter["chapterState"] != CHAPTER_STATE_READY and _chapter["chapterState"] != CHAPTER_STATE_SETTLEMENT:
            return

        # 如果是比赛场,准备时金币不能小于0
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
        # 判断牌局是否可以开始
        if self.is_less_mode:
            if _playersCount < 2:
                return
        else:
            if _playersCount < self.info["maxPlayersCount"]:
                return

        _flag = True
        for i in _players.values():
            if not i["isReady"]:
                _flag = False
                break
        if _flag:
            self.changeChapterState(CHAPTER_STATE_START)

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
            self.stop_timer("mainTimer")
            self.changeChapterState(CHAPTER_STATE_START)

    def syncReadyMsg(self, player, ready):
        """
        同步准备和取消准备消息
        :return:
        """
        self.callOtherClientsFunction("syncReadyMsg", {"locationIndex": player['locationIndex'], "ready": ready})

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
    #                            牌局流程
    # --------------------------------------------------------------------------------------------

    # @property
    # def current_chapter(self):
    #     self.chapters[self.cn]

    # @current_chapter.setter
    # def current_chapter(self):
    #     self.chapters[self.cn]

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
        if _old == CHAPTER_STATE_INIT and state == CHAPTER_STATE_READY:
            # 准备阶段，玩家可以进出房间，点击准备
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType14 id %i]------->changeChapterState to %s' % (self.id, state))
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
            # 自动准备改为手动准备
            # for k, v in _players.items():
            #    self.on_player_ready(v['entity'].id)

        elif (_old == CHAPTER_STATE_READY and state == CHAPTER_STATE_START) or (
                _old == CHAPTER_STATE_SETTLEMENT and state == CHAPTER_STATE_START):
            # 开始阶段要定庄，通知客户端和BASE游戏已开始
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType14 id %i]------->changeChapterState to %s' % (self.id, state))
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
            self.chapter_start()
            # 同步局数
            self.syncChapterNum(self.cn + 1)
            # 同步庄家
            self.sync_banker_index(_chapter[BANKER_LOCATION])
            # 新建牌库
            self.new_cards_lib()

            self.changeChapterState(CHAPTER_STATE_XIA_PAO)

        elif _old == CHAPTER_STATE_START and state == CHAPTER_STATE_XIA_PAO:
            """
          自主跑时，有每局下跑和四局下跑之分
          固定跑时，已经选定多少跑
          不带跑时，不需要下跑
          """
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType14 id %i]------->changeChapterState to %s' % (self.id, state))
            if self.room_cfg.xia_pao_type == 0:
                # 不带跑
                self.changeChapterState(CHAPTER_STATE_FAN_HUN)
                return

            self.callOtherClientsFunction("chapterStateChanged", [state])
            self.callOtherClientsFunction("StartXiaPao", [])
            if self.room_cfg.xia_pao_type == 1:
                # 每局跑
                self.start_timer("xiaPaoTimer")
            elif self.room_cfg.xia_pao_type == 2:
                # 4局跑
                if self.cn % 4 == 0:
                    self.start_timer("xiaPaoTimer")
                else:
                    _players = self.current_chapter.players
                    for player in _players.values():
                        _args = {"entityId": player['entity'].id, "pao": player[XIA_PAO_COUNT]}
                        self.callOtherClientsFunction("PaoBack", _args)
                    self.process_xia_pao_result(True)
            elif self.room_cfg.xia_pao_type == 3:
                # 固定跑
                _players = self.current_chapter.players
                for player in _players.values():
                    player[XIA_PAO_COUNT] = self.room_cfg.xia_pao_num
                    _args = {"entityId": player['entity'].id, "pao": self.room_cfg.xia_pao_num}
                    self.callOtherClientsFunction("PaoBack", _args)
                self.process_xia_pao_result(True)

        elif _old == CHAPTER_STATE_XIA_PAO and state == CHAPTER_STATE_FAN_HUN:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType14 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])

            self.stop_timer("xiaPaoTimer")

            if self.room_cfg.is_use_hun_pai:
                # 翻混，并添加翻混超时定时器,取牌值倒数第14张
                hunPais = self.calc_hun_pai()
                self.current_chapter.hun_pais = hunPais[1:]
                fanHunInfo = {}
                fanHunInfo["mingPai"] = hunPais[0]
                fanHunInfo["hunPai"] = hunPais[1:]
                self.callOtherClientsFunction("FanHun", fanHunInfo)
                self.start_timer("fanHunTimer")
            else:
                self.changeChapterState(CHAPTER_STATE_DEAL)

        elif _old == CHAPTER_STATE_FAN_HUN and state == CHAPTER_STATE_DEAL:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType14 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])

            self.stop_timer("fanHunTimer")

            # 初始化手牌
            self.init_round()
            self.init_shou_pai()
            # 进入出牌阶段
            self.changeChapterState(CHAPTER_STATE_PLAY)
        elif _old == CHAPTER_STATE_DEAL and state == CHAPTER_STATE_PLAY:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType14 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])

            # 打牌阶段
            self.notice_next_player(_chapter[ROUND][-1], _chapter[ROUND])
        elif _old == CHAPTER_STATE_PLAY and state == CHAPTER_STATE_SETTLEMENT:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType14 id %i]------->changeChapterState to %s' % (self.id, state))
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
                self.stop_timer('playCardTimer')
                self.stop_timer('resOutPaiTimer')

                # _chapter['restartTimer'] = self.addTimer(RESTART_TIME, 0, 0)
                self.start_next_chapter()
                self.sync_timer_count_down(RESTART_TIME)
                _chapter['deadLine'] = time.time() + RESTART_TIME
        elif state == CHAPTER_STATE_TOTAL_SETTLEMENT:
            _chapter["chapterState"] = state
            DEBUG_MSG('[RoomType14 id %i]------->changeChapterState to %s' % (self.id, state))
            self.callOtherClientsFunction("chapterStateChanged", [state])

        else:
            # 不存在的状态切换  抛出异常
            raise Exception('error in changeChapterState, oldState=%s, state=%s' % (_old, state))

    def calc_hun_pai(self):
        """
        单混只需要+1
        双混需要+1，-1
        例如：明牌是1筒，混牌是2筒和9筒
        :return:
        """
        cards_lib = self.current_chapter.card_lib
        card_value = cards_lib[-14]

        # 牌值范围 筒条万各9种，箭牌7种
        card_type = card_value // 9
        cards_range = []
        card_count = 9
        if card_type <= 2:
            cards_count = 9
        else:
            cards_count = 7
        cards_range = [x + card_type * 9 for x in range(cards_count)]

        # 计算前后牌值
        hun_pai = [card_value]
        pos = cards_range.index(card_value)
        if self.room_cfg.hun_pai_type == 1:
            hun_pos = (pos + 1) % cards_count
            hun_pai.append(cards_range[hun_pos])
        elif self.room_cfg.hun_pai_type == 2:
            hun_pos1 = (pos + 1) % cards_count
            hun_pos2 = (pos - 1) % cards_count
            hun_pai.append(cards_range[hun_pos1])
            hun_pai.append(cards_range[hun_pos2])

        return hun_pai

    def is_valid_xia_pao_value(self, xia_pao_count):
        return True

    def palyer_xia_pao(self, account_entity_id, xia_pao_count):  # timeout=False
        """
        用户选择下跑数，需要检查下跑数是否在允许范围内
        :param account_entity_id:
        :param xia_pao_count:
        :return:
        """
        if not self.is_valid_xia_pao_value(xia_pao_count):
            return

        player = self.get_player_by_entity_id(account_entity_id)
        player[XIA_PAO_COUNT] = xia_pao_count

        _args = {"entityId": account_entity_id, "pao": xia_pao_count}
        self.callOtherClientsFunction("PaoBack", _args)

        self.process_xia_pao_result()

    def process_xia_pao_result(self, timeout=False):
        """
        玩家下跑，检查是否都已下跑
        超时，设置默认不跑
        :param timeout:
        :return:
        """
        if self.current_chapter.chapter_state != CHAPTER_STATE_XIA_PAO:
            return
        # _chapter = self.current_chapter
        _players = self.current_chapter.players

        # 超时用户没选择，自主跑默认设为不跑；固定跑不用选择
        for player in _players.values():
            DEBUG_MSG('palyer_xia_pao count:%s %s' % (player['entity'].id, player[XIA_PAO_COUNT]))
            if player[XIA_PAO_COUNT] == -1:
                if timeout:
                    player[XIA_PAO_COUNT] = 0
                    _args = {"entityId": player['entity'].id, "pao": 0}
                    self.callOtherClientsFunction("PaoBack", _args)
                else:
                    return False

        # 开始翻混
        self.changeChapterState(CHAPTER_STATE_FAN_HUN)

    def sendChapterStartMsgToBase(self):
        chapter_start_msg = {
            "cn": self.cn
        }
        self.base.cellToBase({"func": "chapterStart", "args": chapter_start_msg})

    def send_chapter_end_msg_to_base(self):
        """
        发送牌局结束信息
        :return:
        """
        chapter_end_msg = {
            "cn": self.cn
        }
        self.base.cellToBase({"func": "chapterEnd", "args": chapter_end_msg})

    def get_fang_gang_player_by_pai(self, hu_player, pai):
        for k, v in hu_player[DA_MING_GANG_S].items():
            if pai == k:
                _p = self.get_player_by_location(v)
                return _p

        for k, v in hu_player[XIAO_MING_GANG_S].items():
            if pai == k:
                _p = self.get_player_by_location(v)
                return _p

    def settlement(self):
        """
        结算
        :return:
        """
        _chapter = self.get_current_chapter()
        players = self.get_sea_players()
        hu_players = _chapter[HU_PLAYER]

        # DEBUG_MSG("settlement %s %s" % (players, hu_players))
        no_hu_players = []
        for p in players:
            p["isReady"] = False
            if not self.is_player_in_players(p, hu_players):
                no_hu_players.append(p)
                self.set_losing_streak_history(p, True)
            else:
                self.set_losing_streak_history(p, False)

        banker_index = _chapter[BANKER_LOCATION]

        if not _chapter[IS_HUANG_ZHUANG]:

            # 扣胡分
            for hu_player in hu_players:
                DEBUG_MSG("[RoomType14] settlement HU_TYPE=%s" % _chapter[HU_TYPE])
                hu_score = 0
                # 存储扣鱼子分的玩家
                fish_range = []
                # 胡牌分数
                if _chapter[IS_ZI_MO_HE]:
                    hu_score = self.room_cfg.zi_mo_score
                    fish_range = no_hu_players.copy()
                elif _chapter[IS_QIANG_GANG_HE]:
                    hu_score = self.room_cfg.dian_pao_score
                    fish_range = [self.get_player_by_location(_chapter[FANG_PAO_INDEX])]
                elif _chapter[IS_DIAN_PAO_HE]:
                    hu_score = self.room_cfg.dian_pao_score
                    fish_range = [self.get_player_by_location(_chapter[FANG_PAO_INDEX])]

                elif _chapter[IS_HUANG_ZHUANG]:
                    hu_score = 0
                    fish_range = []

                # 根据特殊规则翻倍;如果是杠上花翻倍，暗杠对所有玩家；明杠只针对点杠者
                multiple = 0
                fang_gang_hu_player = None
                gang_shang_hua_multiple = 0
                for special in hu_player['special']:
                    if HU_RESULT_GANG_SHANG_HUA == special:
                        if 0 <= _chapter[IS_GANG_SHANG_KAI_HUA] < 100:
                            fang_gang_hu_player = self.get_fang_gang_player_by_pai(hu_player,
                                                                                   _chapter[IS_GANG_SHANG_KAI_HUA])
                        gang_shang_hua_multiple = self.get_special_multiple(special)
                    else:
                        multiple += self.get_special_multiple(special)

                DEBUG_MSG('hu_player:%s %s,special:%s gang_shang_hua_pai:%s %s' % (
                    hu_player['entity'].info['name'], multiple, hu_player['special'], _chapter[IS_GANG_SHANG_KAI_HUA],
                    fang_gang_hu_player is not None))

                xia_pao_count1 = hu_player[XIA_PAO_COUNT]
                is_banker1 = (banker_index == hu_player['locationIndex'])

                # 扣除胡分、跑分
                lose_range = fish_range
                for _lose_player in lose_range:
                    xia_pao_count2 = _lose_player[XIA_PAO_COUNT]
                    # 双方下跑数+加底数+胡分
                    banker_jia_di = 0
                    is_banker2 = (banker_index == _lose_player['locationIndex'])
                    if self.room_cfg.is_banker_add_di and (is_banker1 or is_banker2):
                        banker_jia_di = 1
                    append_count = xia_pao_count1 + xia_pao_count2
                    if append_count < 0:
                        append_count = 0
                    append_count += banker_jia_di
                    hu_pao_score = (append_count + 1) * hu_score

                    # 杠上花，明杠扣点杠者，暗杠扣所有
                    new_multiple = multiple
                    if gang_shang_hua_multiple > 0:
                        if not fang_gang_hu_player:
                            new_multiple += gang_shang_hua_multiple
                        elif fang_gang_hu_player == _lose_player:
                            new_multiple += gang_shang_hua_multiple
                    if new_multiple != 0:
                        hu_pao_score *= new_multiple

                    DEBUG_MSG('hu_pao_score:%s %s,new_multiple:%s %s, xia_pao_count: %s %s ' % (
                        hu_pao_score, hu_score, new_multiple, gang_shang_hua_multiple, xia_pao_count1, xia_pao_count2))

                    _lose_player[SETTLEMENT_DATA]['goldChange'] -= hu_pao_score
                    hu_player[SETTLEMENT_DATA]['goldChange'] += hu_pao_score
                    _lose_player[SETTLEMENT_DATA]['huGoldChange'] -= hu_pao_score
                    hu_player[SETTLEMENT_DATA]['huGoldChange'] += hu_pao_score

            # 扣多少杠分
            gang_di = self.room_cfg.gang_di_score
            for _gang_p in _chapter[PLAYER_IN_GAME].values():
                xia_pao_count1 = _gang_p[XIA_PAO_COUNT]

                # 大明杠分
                # da_ming_gang_score = gang_di
                # 大明杠扣触发杠的人
                is_banker1 = (banker_index == _gang_p['locationIndex'])
                for i in _gang_p[DA_MING_GANG_S].values():
                    _p = self.get_player_by_location(i)
                    xia_pao_count2 = _p[XIA_PAO_COUNT]
                    banker_jia_di = 0
                    is_banker2 = (banker_index == _p['locationIndex'])
                    if self.room_cfg.is_banker_add_di and (is_banker1 or is_banker2):
                        banker_jia_di = 1
                    append_count = 0
                    if self.room_cfg.is_hvae_gang_pao:
                        append_count = xia_pao_count1 + xia_pao_count2
                    if append_count < 0:
                        append_count = 0
                    append_count += banker_jia_di
                    da_ming_gang_score = (append_count + 1) * gang_di

                    _p[SETTLEMENT_DATA]['goldChange'] -= da_ming_gang_score
                    _gang_p[SETTLEMENT_DATA]['goldChange'] += da_ming_gang_score
                    _p[SETTLEMENT_DATA]['gangGoldChange'] -= da_ming_gang_score
                    _gang_p[SETTLEMENT_DATA]['gangGoldChange'] += da_ming_gang_score

                # 小明杠分
                # xiao_ming_score = gang_di
                # 小明杠扣触发碰的人
                for i in _gang_p[XIAO_MING_GANG_S].values():
                    _p = self.get_player_by_location(i)
                    xia_pao_count2 = _p[XIA_PAO_COUNT]
                    banker_jia_di = 0
                    is_banker2 = (banker_index == _p['locationIndex'])
                    if self.room_cfg.is_banker_add_di and (is_banker1 or is_banker2):
                        banker_jia_di = 1
                    append_count = 0
                    if self.room_cfg.is_hvae_gang_pao:
                        append_count = xia_pao_count1 + xia_pao_count2
                    if append_count < 0:
                        append_count = 0
                    append_count += banker_jia_di
                    xiao_ming_score = (append_count + 1) * gang_di
                    _p[SETTLEMENT_DATA]['goldChange'] -= xiao_ming_score
                    _gang_p[SETTLEMENT_DATA]['goldChange'] += xiao_ming_score
                    _p[SETTLEMENT_DATA]['gangGoldChange'] -= xiao_ming_score
                    _gang_p[SETTLEMENT_DATA]['gangGoldChange'] += xiao_ming_score

                # 暗杠
                # an_score = gang_di
                # 所有暗杠
                for _ in _gang_p[AN_GANG_S]:
                    # 其他玩家
                    for _p in _chapter[PLAYER_IN_GAME].values():
                        if self.is_same_player(_p, _gang_p):
                            continue
                        xia_pao_count2 = _p[XIA_PAO_COUNT]
                        banker_jia_di = 0
                        is_banker2 = (banker_index == _p['locationIndex'])
                        if self.room_cfg.is_banker_add_di and (is_banker1 or is_banker2):
                            banker_jia_di = 1
                        append_count = 0
                        if self.room_cfg.is_hvae_gang_pao:
                            append_count = xia_pao_count1 + xia_pao_count2
                        if append_count < 0:
                            append_count = 0
                        append_count += banker_jia_di
                        an_score = (append_count + 1) * gang_di

                        _p[SETTLEMENT_DATA]['goldChange'] -= an_score
                        _gang_p[SETTLEMENT_DATA]['goldChange'] += an_score
                        _p[SETTLEMENT_DATA]['gangGoldChange'] -= an_score
                        _gang_p[SETTLEMENT_DATA]['gangGoldChange'] += an_score

        else:
            pass

        # 赋值总金币改变
        for _p in players:
            _p['totalGoldChange'] += _p[SETTLEMENT_DATA]['goldChange']
            _p["entity"].update_score_control(_p[SETTLEMENT_DATA]['goldChange'])
            DEBUG_MSG('RoomType14 settlement totalGoldChange%s' % _p['totalGoldChange'])

        # 封装牌局结算消息
        end_msg = []
        for p in players:
            pm = {"locationIndex": p['locationIndex'],
                  "shouPai": p[SHOU_PAI],
                  "anGangs": p[AN_GANG_S],
                  "pengs": list(p[PENG_S].keys()),
                  "xiaoMingGangs": list(p[XIAO_MING_GANG_S].keys()),
                  "daMingGangs": list(p[DA_MING_GANG_S].keys()),
                  'gangGold': p[SETTLEMENT_DATA]['gangGoldChange'],
                  'huGold': p[SETTLEMENT_DATA]['huGoldChange'],
                  "goldChange": p[SETTLEMENT_DATA]['goldChange'],
                  "isHu": self.is_player_in_players(p, hu_players),
                  # 特殊规则：7：七星对  5：杠上花
                  'special': p['special'],
                  'pao': p[XIA_PAO_COUNT],
                  "huType": _chapter[HU_TYPE]}
            end_msg.append(pm)
        DEBUG_MSG('[RoomType14 id %i]------------->chapterEnd end_msg=%s' % (self.id, end_msg))
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

    def total_settlement(self, is_disband=False):
        """
        发送房间结束
        :return:
        """
        if self.total_settlement_ed:
            return
        self.delete_all_timer()
        self.changeChapterState(CHAPTER_STATE_TOTAL_SETTLEMENT)
        self.total_settlement_ed = True
        # 清除观战玩家
        self.clear_witness_player()
        chapter = self.get_current_chapter()
        _plays = chapter[PLAYER_IN_GAME]

        sd = self.statisticalData
        room_end_msg = {"winnerIndexes": -1, "players": []}
        big_winner_max = 0
        big_winner_indexes = []
        # 收集统计数据
        for sdp in sd[SD_PLAYERS].values():
            settlement_info = []
            for _ch in self.chapters:
                if sdp[SD_LOCATION_INDEX] in _ch[PLAYER_IN_GAME]:
                    _player = _ch[PLAYER_IN_GAME][sdp[SD_LOCATION_INDEX]]
                    settlement_info.append(_player[SETTLEMENT_DATA]['goldChange'])
                else:
                    # 没参与用int最大值表示
                    settlement_info.append(2147483647)
            room_end_msg["players"].append({
                "locationIndex": sdp[SD_LOCATION_INDEX],
                # "ziMoCount": sdp[SD_ZI_MO_COUNT],
                # "anGangCount": sdp[SD_AN_GANG_COUNT],
                # "mingGangCount": sdp[SD_MING_GANG_COUNT],
                'settlementInfo': settlement_info,
                "totalScore": _plays[sdp[SD_LOCATION_INDEX]]['totalGoldChange'],
                # "dianPaoCount": sdp[SD_DIAN_PAO_COUNT]
            })
            if _plays[sdp[SD_LOCATION_INDEX]]['totalGoldChange'] >= big_winner_max:
                big_winner_max = _plays[sdp[SD_LOCATION_INDEX]]['totalGoldChange']
        for _p in _plays.values():
            if _p['totalGoldChange'] == big_winner_max and _p['totalGoldChange'] > 0:
                big_winner_indexes.append(_p['locationIndex'])
        room_end_msg["winnerIndexes"] = big_winner_indexes
        room_end_msg['isDisband'] = is_disband
        DEBUG_MSG('[RoomType14 id %i]------------->totalSettlement msg=%s' % (self.id, room_end_msg))

        players = chapter[PLAYER_IN_GAME]
        for p in players.values():
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
                player_data = {"goldChange": v[SETTLEMENT_DATA]["goldChange"], "name":
                    v["entity"].info["name"]}
                chapter_data.append(player_data)
            _history_record[c] = chapter_data
        # 战绩记录
        # 记录战绩的玩家
        record_players = []
        for k, v in _playerInRoom.items():
            _playerData = {"accountId": v['entity'].id, "accountName": v["entity"].info["name"],
                           "winnerBilling": v["winnerBilling"], "overBilling": v["overBilling"],
                           "otherBilling": v["otherBilling"],
                           "totalGoldChange": v["totalGoldChange"], "userId": v["entity"].info["userId"]}
            _playerInfo.append(_playerData)
            record_players.append(v["entity"].info["userId"])

        _args = {"createRoomTime": int(time.time()), "roomId": self.info["roomId"],
                 "maxChapterCount": self.info["maxChapterCount"],
                 "playerInfo": _playerInfo, "historyRecord": _history_record}
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
            # 下跑信息
            pao_info = {}
            for k, v in _player_seat.items():
                _player_location = v['locationIndex']
                # 获取总金币
                total_gold_change = v['totalGoldChange']
                _player = {"entityId": v["entity"].id, "locationIndex": int(v['locationIndex']),
                           "name": v["entity"].info["name"],
                           "userId": v["entity"].info["userId"],
                           'goldChange': v[SETTLEMENT_DATA]['goldChange'],
                           'gold': v['gold'] + total_gold_change + v['baseSyncGoldChange'],
                           "headImageUrl": v["entity"].info["headImageUrl"]}
                pao_info[int(v['locationIndex'])] = v[XIA_PAO_COUNT]
                player_info[int(v['locationIndex'])] = _player

            _replay_data[c]['playerInfo'] = player_info
            _replay_data[c]['paoInfo'] = pao_info
            _replay_data[c]['hunPai'] = _chapter[HUN_PAIS]

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
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1,
            'type': 'gameCoin',
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
            "teaHouseId": self.info["teaHouseId"] if self.is_tea_house_room else -1,
            'type': 'gold',
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
        self.stop_timer("mainTimer")
        self.stop_timer("playCardTimer")
        self.stop_timer("resOutPaiTimer")
        self.stop_timer("dissolveTimer")
        self.stop_timer("settlementTimer")
        self.stop_timer("restartTimer")
        self.stop_timer("xiaPaoTimer")
        self.stop_timer("fanHunTimer")

    def new_cards_lib(self):
        """
        新建牌库
        :param has_feng:是否有风牌
        :return:
        """
        _chapter = self.chapters[self.cn]
        have_wind = self.room_cfg.is_have_wind
        # single_color = self.single_color

        # if single_color == 1:
        #     _l = list(range(0, 9))
        # elif single_color == 2:
        #     _l = list(range(9, 18))
        # elif single_color == 0:
        #     _l = list(range(18, 27))
        # else:
        _l = list(range(0, 27))

        if have_wind:
            _l += list(range(27, 34))

        _l *= 4
        random.shuffle(_l)
        # _l += list(range(34, 42))
        player_num = self.info["maxPlayersCount"]
        i = 13 * player_num
        _head = _l[0:i]
        _tail = _l[i:]
        _l = _head + _tail
        # DEBUG_MSG('new_cards_lib _l%s' % _l)

        # 根据时间戳翻牌
        self.random_cards_with_time(_l)
        # 根据局数决定发牌顺序
        self.random_with_chapter_count(_l)
        DEBUG_MSG('new_cards_lib after random _l%s' % _l)
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
        if not player:
            return

        dead_line = int(_chapter["deadLine"]) - int(time.time())
        dissolve_line = int(_chapter["dissolveDeadLine"]) - int(time.time())

        users = []
        for p in players.values():
            # 封装吃碰杠消息
            chis = []
            for k, v in p[CHIS].items():
                chis.append({
                    "pai": k,
                    "otherIndex": v[1]
                })
            pengs = []
            for k, v in p[PENG_S].items():
                pengs.append({
                    "pai": k,
                    "otherIndex": v
                })
            xmgs = []
            for k, v in p[XIAO_MING_GANG_S].items():
                xmgs.append({
                    "pai": k,
                    "otherIndex": v
                })
            dmgs = []
            for k, v in p[DA_MING_GANG_S].items():
                dmgs.append({
                    "pai": k,
                    "otherIndex": v
                })

            users.append({
                "locationIndex": p['locationIndex'],
                "cards": p[SHOU_PAI],
                "chis": chis,
                "pengs": pengs,
                "xiaoMingGangs": xmgs,
                "daMingGangs": dmgs,
                "anGangs": p[AN_GANG_S],
                "huaPais": p[HUA_PAI],
                "outPais": p[OUT_PAIS],
                "danFang": p[DAN_FANG],
                "onLine": not p['entity'].client_death,
                'isReady': p['isReady'],
                'disbandSender': self.disband_sender,
                'pao': p[XIA_PAO_COUNT],
                'hunPai': self.current_chapter.hun_pais,
                'agreeDisbanding': True if p[IS_ARGEE] == 1 else False,
                'isDisbanding': self.is_disbanding,
                'deadLine': dissolve_line if self.is_disbanding else dead_line,
                'canStartGame': self.wait_to_seat
            })

        self.syncChapterNum(self.cn + 1)
        # DEBUG_MSG('[RoomType14 id %s]------------->reconnection msg:%s' % (self.id, users))
        self.callClientFunction(accountEntityId, "reconnection", users)
        # 同步庄的位置
        self.sync_banker_index(_chapter[BANKER_LOCATION])
        # 同步计时器
        self.sync_timer_count_down(dead_line)

        # 同步当前出牌的玩家
        if _chapter[CUR_PLAYER] is not None:
            self.callClientFunction(accountEntityId, "reconnSyncCurrentPlayerIndex",
                                    _chapter[CUR_PLAYER]['locationIndex'])
            # 如果可以，同步小明杠，暗杠，自摸胡操作
            if player[DAN_FANG] != -1:
                _shouPai = player[SHOU_PAI]
                _pengs = player[PENG_S]
                # 检查当前玩家的杠胡情况
                _xmg = self.check_xiao_ming_gang(_shouPai, _pengs, player)
                _ag = check_an_gang(_shouPai)
                _isHu = self.can_it_hu(_shouPai)
                if _isHu:
                    # 设置当前玩家可以胡牌
                    player[CAN_HU] = True
                else:
                    player[CAN_HU] = False

                # 出牌提示
                if len(_xmg) != 0:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_XIAOMINGGANG, _xmg)
                if len(_ag) != 0:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_ANGANG, _ag)
                if _isHu:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_ZIMOHU, _isHu)
                # if len(_ting) > 0:
                #     self.callClientFunction(player["entity"].id, CLIENT_FUNC_TING, _ting)
                if len(_xmg) != 0 or len(_ag) != 0 or _isHu:
                    self.callClientFunction(player["entity"].id, CLIENT_FUNC_GUO, "")

        # 如果可以，同步吃，碰，大明杠，点炮胡操作
        if _chapter["chapterState"] == CHAPTER_STATE_PLAY:
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
        if cr[CHECK_HU]:
            self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_DIANPAOHU, cr[CHECK_HU])
        if cr[CHECK_HU_QIANG_GANG]:
            self.callClientFunction(cr[CHECK_PLAYER]["entity"].id, CLIENT_FUNC_QIANGGANGHU,
                                    cr[CHECK_HU_QIANG_GANG])
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
        self.hu_pai([])

    def get_card(self, r=False):
        """
        从牌库里拿出一张牌
        :param r:
        :return:
        """
        _chapter = self.chapters[self.cn]
        cards_lib = _chapter[CARDS_LIB]
        if len(cards_lib) <= _chapter[HUANG_ZHUANG_LEFT_COUNT]:
            self.on_no_card()
            return
        _chapter[LEFT_PAI_COUNT] -= 1
        if r:
            _v = cards_lib[-1]
            cards_lib.pop(-1)
            return _v
        else:
            _v = cards_lib[0]
            cards_lib.pop(0)
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

        # 拿到指定牌
        if pai in cards_lib:
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
        DEBUG_MSG('RoomType14 playerOperation accountEntityId:%s jsonData:%s' % (accountEntityId, jsonData))
        _player, _operation_name, _args = RoomBase.playerOperation(self, accountEntityId, jsonData)
        # 检查是否应该此玩家操作
        _check_player = self.check_current_player(_player)
        if not _check_player:
            DEBUG_MSG('is not _check_player')
            return
        # 检查该玩家的操作
        _check_opt = self.checkOperation(_player, _operation_name)
        if not _check_opt:
            DEBUG_MSG('is not _check_opt')
            return

        # 检查出牌操作
        if OPT_OUT == _operation_name:
            out_pai = _args[0]
            if out_pai not in _player[SHOU_PAI]:
                self.callClientFunction(_player['entity'].id, 'refreshChapter', {})
                return

        # 清空允许操作
        player_allow_opt = _player[ALLOW_OPT]
        _player[ALLOW_OPT] = 0
        # 获取操作码
        opt_code = OPT_DICT[_operation_name]
        if opt_code & FA_PAI_AFTER_OPTS_CODE == opt_code:
            # 发牌之后的操作
            self.operation_after_deal_card(_player, _operation_name, _args)
        elif opt_code & OUT_PAI_AFTER_OPTS_CODE == opt_code:
            # 出牌之后其他玩家的响应操作
            # 如果允许玩家点炮胡，并且玩家此时选择过牌,则视为玩家弃掉了点炮胡
            if _operation_name == OPT_GUO:
                opt_v = OPT_DICT[OPT_HU_DIAN_PAO]
                if (player_allow_opt & opt_v) == opt_v:
                    _player['qiDianPao'] = True

            self.operation_after_play_card(_player, _operation_name, _args)
        elif _operation_name == OPT_HU_QIANG_GANG:
            # 特殊，抢杠和
            self.res_out_pai_qiang_gang_hu_opt(_player)
        else:
            ""

    def operation_after_deal_card(self, _player, _operation_name, _args):
        """
        发牌之后玩家选择的操作
        :param _player:
        :param _operation_name:
        :param _args:
        :return:
        """
        # 出牌
        if OPT_OUT == _operation_name:
            out_pai = _args[0]
            check_cards(out_pai)
            # 出牌操作
            # 出牌成功
            self.play_card(_player, out_pai)
        # 小明杠
        elif OPT_XIAOMINGGANG == _operation_name:
            # 检查抢杠胡
            pai = _args[0]
            check_cards(pai)
            self.check_qiang_gang_hu(_player, pai)
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
            # self.setNotPengPai(_player)
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
            self.res_out_pai_peng_opt(_player, pai)
        elif OPT_DAMINGGANG == _operation_name:
            pai = _args[0]
            check_cards(pai)
            self.set_not_hu_pai(_player)
            self.res_play_card_da_ming_gang_opt(_player, pai)
        elif OPT_HU_DIAN_PAO == _operation_name:
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
            _player = self.get_player_by_entity_id(accountEntityId)
            _player[WAI_GUA_SELECT_PAI] = _args[0]
        elif _func_name == 'FreeBlessCount':
            self.free_bless_count(accountEntityId)
        elif _func_name == "Bless":
            self.bless(accountEntityId, _args["type"])
        elif _func_name == 'ContinueNextChapter':
            self.continue_next_chapter(accountEntityId)
        elif _func_name == 'ShareToWX':
            self.share_to_wx(accountEntityId)
        elif _func_name == 'SendPao':
            self.palyer_xia_pao(accountEntityId, _args["pao"])

        elif _func_name == 'HuTip':
            # start = time.time()
            # pass
            self.hu_tip(accountEntityId, _args['playCard'])
            # end = time.time()
            # DEBUG_MSG('HuTip time%s' % str(end - start))
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
        _locationIndexes = []
        _seats = []
        _location_info = {}
        for i in stp:
            p = stp[i]
            _seats.append(i)
            _entityIds.append(p["entity"].id)
            _userIds.append(p["entity"].info["userId"])
            _locationIndexes.append(p['locationIndex'])
        _location_info["entityIds"] = _entityIds
        _location_info["userIds"] = _userIds
        _location_info["locationIndexs"] = _locationIndexes
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
        DEBUG_MSG('[RoomType14 roomid:%s] seat_to_player%s' % (self.info['roomId'], _player_seat))
        for k, v in _player_seat.items():
            _player_location = v['locationIndex']
            # 获取总金币
            total_gold_change = v['totalGoldChange']
            _player = {"entityId": v["entity"].id, "locationIndex": int(v['locationIndex']),
                       "name": v["entity"].info["name"],
                       "userId": v["entity"].info["userId"],
                       "ip": v["entity"].info["ip"],
                       'goldChange': v[SETTLEMENT_DATA]['goldChange'],
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
                       'goldChange': v[SETTLEMENT_DATA]['goldChange'],
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
                       'goldChange': v[SETTLEMENT_DATA]['goldChange'],
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
        if not self.started:
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

        result = args[0]
        if result == 0:
            # 拒绝，删除解散房间定时器，重置玩家相关状态，取消解散房间
            self.delTimer(_chapter['dissolveTimer'])
            _chapter['dissolveTimer'] = -1
            for k, v in _chapter[PLAYER_IN_GAME].items():
                v[IS_ARGEE] = -1
            self.is_disbanding = False
            self.callOtherClientsFunction("cancelDissolveRoom", {"locationIndex": _player['locationIndex']})
        elif result == 1:
            _player[IS_ARGEE] = 1
            args = {"locationIndex": _player['locationIndex'], "result": result}
            self.callOtherClientsFunction("DissolveRoomOperation", args)
            # 同意，检查是否全部同意，全部同意，解散房间
            if self.is_all_agree():
                self.is_manual_disband = True
                self.delTimer(_chapter['dissolveTimer'])
                _chapter['dissolveTimer'] = -1
                self.is_disbanding = False
                self.callOtherClientsFunction("dissolveRoom", {})
                self.total_settlement(is_disband=True)

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
    def start_timer(self, timer_name):
        """
        mainTimer
        playCardTimer
        resOutPaiTimer
        qiangGangTimer
        dissolveTimer
        settlementTimer
        restartTimer
        settlementClearPlayers
        :param timer_name:
        :return:
        """
        timeout_second = 0
        if timer_name == "mainTimer":
            pass
        elif timer_name == "playCardTimer":
            timeout_second = AUTO_TIME
            pass
        elif timer_name == "resOutPaiTimer":
            timeout_second = AUTO_TIME
            pass
        elif timer_name == "qiangGangTimer":
            timeout_second = AUTO_TIME
            pass
        elif timer_name == "xiaPaoTimer":
            timeout_second = AUTO_TIME
            pass
        elif timer_name == "fanHunTimer":
            timeout_second = 2
            pass
        elif timer_name == "dissolveTimer":
            timeout_second = AUTO_DISSOLVE_TIME
            pass
        elif timer_name == "settlementTimer":
            timeout_second = AUTO_TIME
            pass
        elif timer_name == "restartTimer":
            timeout_second = RESTART_TIME
            pass
        elif timer_name == "settlementClearPlayers":
            timeout_second = SETTLEMENT_CLEAR_PLAYERS_TIME
            pass
        else:
            return

        _chapter = self.get_current_chapter()
        _chapter[timer_name] = self.addTimer(timeout_second, 0, 0)
        _chapter['deadLine'] = time.time() + timeout_second
        self.sync_timer_count_down(timeout_second)

    def stop_timer(self, timer_name):
        _chapter = self.get_current_chapter()
        if timer_name in _chapter:
            self.delTimer(_chapter[timer_name])
            _chapter[timer_name] = -1

    def onTimer(self, timerId, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param timerId		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """
        _chapter = self.get_current_chapter()
        _timers = _chapter["timers"]
        # if timerId != _chapter["mainTimer"]:
        #     DEBUG_MSG("onTimer timerId=%s" % timerId)

        if timerId == _chapter["mainTimer"]:
            # DEBUG_MSG('[Room id %s]------------->onTimer mainTimer %s' % (self.id, timerId))
            _chapter_state = _chapter["chapterState"]
            _players = _chapter[PLAYER_IN_GAME]
            _playersCount = len(_chapter[PLAYER_IN_GAME])
            if _chapter_state == CHAPTER_STATE_READY:
                # 默认金币场模式 暂定大于等于4人就开始
                if self.is_less_mode:
                    if _playersCount < 2:
                        return
                else:
                    if _playersCount < self.info["maxPlayersCount"]:
                        return

                _flag = True
                for i in _players.values():
                    if not i["isReady"]:
                        _flag = False
                        break
                if _flag:
                    # 关闭计时器
                    self.stop_timer("mainTimer")
                    self.changeChapterState(CHAPTER_STATE_START)
            # elif _chapter_state == 1:
            #     self.delTimer(timerId)
            #     _timers["main"] = -1
            #     self.delTimer(_timers["botBet"])
            #     _timers["botBet"] = -1
            #     # 下一阶段
            #     self.changeChapterState(2)

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
            DEBUG_MSG('[RoomType14 id %i]------------->Timer(%s) 响应出牌,(%s)超时操作[guoOpt]' % (
                self.id, timerId, self.get_current_player()['locationIndex']))
            self.not_opt_players_operate_pass()
        elif timerId == _chapter['qiangGangTimer']:
            self.delTimer(timerId)
            _chapter['qiangGangTimer'] = -1
            # 响应出牌，其他玩家超时后默认操作
            DEBUG_MSG('[RoomType14 id %i]------------->Timer(%s) 响应抢杠胡,(%s)超时操作[guoOpt]' % (
                self.id, timerId, self.get_current_player()['locationIndex']))
            self.not_opt_players_operate_pass()

        elif timerId == _chapter["xiaPaoTimer"]:
            self.process_xia_pao_result(True)
        elif timerId == _chapter["fanHunTimer"]:
            self.changeChapterState(CHAPTER_STATE_DEAL)
        elif timerId == _chapter['dissolveTimer']:
            # 解散房间
            self.callOtherClientsFunction("dissolveRoom", {})
            self.total_settlement(is_disband=True)
        elif timerId == _chapter['settlementTimer']:
            _chapter['settlementTimer'] = -1
            self.delTimer(timerId)
            self.changeChapterState(CHAPTER_STATE_SETTLEMENT)
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
        player = self.get_player_by_entity_id(entity_id)
        if player['continue']:
            return
        # 如果是比赛场,准备时金币不能小于指定值
        if self.info["roomType"] == "gameCoin" and self.get_true_gold(entity_id) < self.info['readyGoldLimit']:
            self.callClientFunction(entity_id, 'Notice', ['您的比赛分不足,请您立即充值.'])
            info_args = {"accountId": entity_id}
            self.callOtherClientsFunction("ScoreIsLess", info_args)
            return

        # 同步准备消息
        player['isReady'] = True
        self.syncReadyMsg(player, True)
        player['continue'] = True
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
        self.stop_timer("restartTimer")
        # 流程继续
        _max_players_count = self.info["maxPlayersCount"]
        # 如果荒庄，使用上局的庄家
        if len(_chapter[HU_PLAYER]) == 0:
            banker_location = _chapter[BANKER_LOCATION]
        # 如果有胡牌的人，胡牌的第一位是下局的庄家
        else:
            banker_location = _chapter[HU_PLAYER][0]['locationIndex']
        _players = _chapter[PLAYER_IN_GAME]
        new_chapter = self.newChapter(_max_players_count, dissolveDeadLine=_chapter['dissolveDeadLine'],
                                      dissolveTimer=_chapter['dissolveTimer'])
        #
        new_chapter[PLAYER_OUT_GAME] = _chapter[PLAYER_OUT_GAME]
        new_chapter[BANKER_LOCATION] = banker_location
        # 在场座位上的玩家为下一局玩家,传递解散状态
        for v in _players.values():
            _player = self.newPlayer(v["entity"], v['totalGoldChange'], v['baseSyncGoldChange'],
                                     agree_disband=v[IS_ARGEE])
            if (self.room_cfg.xia_pao_type == 2) and (self.cn % 4 != 0):
                _player[XIA_PAO_COUNT] = v[XIA_PAO_COUNT]
            self.set_seat(_player)
        self.changeChapterState(CHAPTER_STATE_READY)

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
        self.base.cellToBase({"func": "newChapter", "count": self.cn + 1})

    def init_shou_pai(self):
        _chapter = self.get_current_chapter()

        # 有人输的太多的话，需要发好牌
        is_in_rand_range = self.is_need_rand_score_control("RoomType14")
        luck_player = None
        if is_in_rand_range:
            luck_player = self.select_max_loser(_chapter[ROUND])
            # if luck_player:
            #     self.callClientFunction(luck_player['entity'].id, 'Notice', ['发好牌'])

        if not luck_player:
            # 找连输超过5局的最大连输玩家
            luck_player, max_losing_streak_count = self.get_max_losing_streak_player(_chapter[ROUND])
            if max_losing_streak_count < 5:
                luck_player = None
            DEBUG_MSG(
                '最大连输 %s %s' % (max_losing_streak_count, luck_player['entity'].id if luck_player else luck_player))

        if not luck_player:
            # 幸运数字玩家
            is_in_rand_range = self.is_need_rand_score_control("RoomType14")
            if is_in_rand_range:
                luck_player = self.select_luck_max_loser(_chapter[ROUND])

        # 每日发好牌次数控制
        day_player = self.select_day_good_pai_player(_chapter[ROUND], 4)
        if day_player:
            luck_player = day_player
            self.player_entity(luck_player).increase_day_pai_control_count()

        # 分牌
        all_cards = []
        for p in _chapter[ROUND]:
            cards = []
            for i in range(0, 13):
                # 添加手牌
                _c = self.get_card()
                cards.append(_c)
            all_cards.append(cards)

        # 给幸运玩家发好牌
        have_pai_player_id = -1
        if luck_player:
            hun_zi_list = self.current_chapter.hun_pais
            good_card_index = mj.RoomType14Calculator.get_good_pai(all_cards, hun_zi_list)
            if good_card_index >= 0:
                luck_player[SHOU_PAI] = all_cards[good_card_index]
                del all_cards[good_card_index]
                have_pai_player_id = luck_player['entity'].id
                DEBUG_MSG('good pai player id: %s cards: %s' % (have_pai_player_id, luck_player[SHOU_PAI]))

        # 给其他人发牌
        for p in _chapter[ROUND]:
            if have_pai_player_id == p['entity'].id:
                self.deal_cards_to_player(p['locationIndex'], p[SHOU_PAI])
                continue
            p[SHOU_PAI] = all_cards[0]
            del all_cards[0]
            self.deal_cards_to_player(p['locationIndex'], p[SHOU_PAI])
        # DEBUG_MSG(_chapter[ROUND])

        # 测试牌
        # pais1=[0,0,1,1,2,2,3,3,3, 4,4,5,5]
        # pais2 = [18, 18, 19, 19, 20, 20, 21, 21, 21, 22, 22, 23, 23]
        # nindex = 0
        # cards_lib = _chapter[CARDS_LIB]
        # for player in _chapter[ROUND]:
        #     nindex += 1
        #     pais = pais1
        #     if nindex == 2:
        #         pais = pais2
        #     for pai in pais:
        #         player[SHOU_PAI].append(pai)
        #         cards_lib.remove(pai)
        #     self.deal_cards_to_player(player['locationIndex'], player[SHOU_PAI])
        #
        # cards_lib.remove(0)
        # cards_lib.insert(0, 0)
        # cards_lib.remove(12)
        # cards_lib.append(12)
        # _chapter[LEFT_PAI_COUNT] -= 26

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
        _round = self.get_sea_players_by_order(start_seat=_start_seat)
        _chapter[ROUND] = _round

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
        players = self.get_sea_players()
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

    def get_sea_players_by_order(self, start_seat=0):
        """
        通过位置获取排过序的所有玩家合集
        :param start_seat:
        :return:
        """
        _chapter = self.get_current_chapter()
        stp = _chapter[SEAT_TO_PLAYER]
        start_player = stp[start_seat]
        DEBUG_MSG('get_sea_players_by_order seat_to_player%s' % _chapter[SEAT_TO_PLAYER])
        ret = self.get_other_players_by_seat(start_seat)
        ret.insert(0, start_player)
        return ret

    def get_sea_players(self):
        """
        获取有座位的所有玩家合集
        :param start_seat:
        :return:
        """
        _chapter = self.get_current_chapter()
        stp = _chapter[SEAT_TO_PLAYER]
        ret = []
        for player in stp.values():
            ret.append(player)
        return ret

    def clearFaiPaiDate(self):
        """
        清除杠上开花标识
        :return:
        """
        _chapter = self.get_current_chapter()
        _cur_player = self.get_current_player()
        # 清除杠上开花标记
        _chapter[IS_GANG_SHANG_KAI_HUA] = -1
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
            DEBUG_MSG('[RoomType14 id %i]------------->ChangeCurPlayer %s to %s' % (
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
        # DEBUG_MSG("check_current_player %s %s" % (player, allow_out_players))
        # if player not in allow_out_players:
        if not self.is_player_in_players(player, allow_out_players):
            allow_location_index = []
            for item in allow_out_players:
                allow_location_index.append(item['locationIndex'])
            DEBUG_MSG('[RoomType14 id %i]------>Error: correct player: %s, current player: %s' % (
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
    def deal_one_card(self, player, is_gang, dian_gang_pai=None):
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
        if is_gang and _chapter[HUANG_ZHUANG_LEFT_COUNT] > 1:
            _chapter[HUANG_ZHUANG_LEFT_COUNT] -= 1
        # 清除不能胡的牌
        player[NOT_HU_PAI].clear()
        # 清除弃点炮胡操作
        player['qiDianPao'] = False
        # 清除不能碰的牌
        # player[NOT_PENG_PAI].clear()
        _shou_pai = player[SHOU_PAI]
        # 设置当前操作的牌
        _chapter[CUR_PAI] = pai
        # 添加手牌
        add_hand_cards(_shou_pai, pai)
        # 打印手牌
        # 设置单放
        player[DAN_FANG] = pai
        # 操作次数+1
        player[OPT_COUNT] += 1
        # 同步剩余牌的数量
        # 同步发牌
        self.syncOpt(player['locationIndex'], SYNCOPT_FAPAI, pai, -1)
        DEBUG_MSG('deal_one_card hand_cards:%s' % _shou_pai)
        # start = time.time()
        self.ting_tip(player['entity'].id)
        # end = time.time()
        # DEBUG_MSG('ting_tip time:%s' % str(end - start))
        self.syncLeftPaiCount(_chapter[LEFT_PAI_COUNT])
        self.check_can_opt_after_deal(player, is_gang=is_gang, dian_gang_pai=dian_gang_pai)

    def check_can_opt_after_deal(self, player, is_gang=False, is_gang_after_peng=False, dian_gang_pai=None):
        """
        检查发牌后可以进行的操作
        :param is_gang_after_peng: 是否是碰后检测杠
        :param player:
        :param is_gang:是否是杠后摸牌后的检测
        :return:
        """
        _chapter = self.get_current_chapter()
        _hand_cards = player[SHOU_PAI]
        _pengs = player[PENG_S]
        # 检查当前玩家的杠胡情况
        _xmg = self.check_xiao_ming_gang(_hand_cards, _pengs, player)
        _ag = check_an_gang(_hand_cards)
        _isHu = self.can_it_hu(_hand_cards)
        DEBUG_MSG('[RoomType14 id %i]------------->FaPai ishu=%s' % (self.id, _isHu))
        # 设置当前玩家可以胡牌
        player[CAN_HU] = _isHu

        # 将玩家可以碰牌设置为False
        player[CAN_PENG] = False

        # 如果是杠后发牌，并且可以胡，那么记为杠上开花
        if is_gang and _isHu:
            _chapter[IS_GANG_SHANG_KAI_HUA] = 100 if dian_gang_pai is None else dian_gang_pai

        # 客户端操作验证
        player[ALLOW_OPT] = 0
        if len(_xmg) != 0:
            player[ALLOW_OPT] |= OPT_XIAOMINGGANG_V
        if len(_ag) != 0:
            player[ALLOW_OPT] |= OPT_ANGANG_V
        # 碰后不能胡
        if _isHu and not is_gang_after_peng:
            player[ALLOW_OPT] |= OPT_HU_ZIMO_V
        player[ALLOW_OPT] |= OPT_OUT_V

        all_not = True

        # 出牌提示
        # 碰后提示暗杠，小明杠
        if len(_xmg) != 0:
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_XIAOMINGGANG, _xmg)
            all_not = False
        if len(_ag) != 0:
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_ANGANG, _ag)
            all_not = False
        # 碰后不能提示胡
        if _isHu and not is_gang_after_peng:
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_ZIMOHU, _isHu)
            all_not = False
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

    def send_other_player_can_operate(self, can_operation_s):
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
                # if c_op[CHECK_PLAYER]['entity'].client_death:
                #     self.operation_after_play_card(c_op[CHECK_PLAYER], OPT_GUO, None)
                # else:
                self.send_check_result_item(c_op)

            # 添加超时定时器,不自动出牌时不进行超时处理
            if self.info['timeDown'] > 0:
                _chapter['resOutPaiTimer'] = self.addTimer(AUTO_TIME, 0, 0)
            _chapter['deadLine'] = time.time() + AUTO_TIME
            self.sync_timer_count_down(AUTO_TIME)

    def notify_out_pai(self, player, notOutPai=[]):
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

    def operation_over(self, timeout=False, operator=None, operation_name=None):
        """
        操作结束，进行一些收尾工作
        :param operation_name: 操作名
        :param operator:操作者
        :param timeout:
        :return:
        """
        DEBUG_MSG('operation_over')
        _chapter = self.get_current_chapter()
        check_results = _chapter[CHECK_RESULTS]
        # 检查所有可以操作的玩家是否全部操作了，如果全部操作了，执行下一步，如果有玩家未操作，退出
        # 如果超时了为操作，直接给出默认操作，执行下一步
        for cr in check_results:
            if cr[CHECK_PLAYER_OPT] == NO_OPT:
                # 检查这个没有操作过的玩家是否可以胡牌操作
                if operation_name == OPT_HU_DIAN_PAO:
                    allow_dian_pao = self.check_allow_dian_pao_hu(cr[CHECK_PLAYER])
                    if not allow_dian_pao:
                        continue
                if timeout:
                    cr[CHECK_PLAYER_OPT] = OPT_GUO_V
                else:
                    if operator:
                        self.callClientFunction(operator, 'waitOtherPlayer', {'entityId': operator})
                    return
        # 清除定时器
        self.stop_timer("resOutPaiTimer")
        # 清空ALLOW_OPT_PLAYERS
        _chapter[ALLOW_OPT_PLAYERS].clear()

        # 根据优先级从大到小排序, 优先级：胡、杠、碰、吃
        def func(e):
            return e[CHECK_PLAYER_OPT]

        check_results = sorted(check_results, key=func, reverse=True)
        # 根据优先级，选出最终操作完成的玩家
        is_first = True
        hu_players = []
        qiang_gang_he = False
        is_qiang_gang_hu = check_results[0][CHECK_FLAG]
        DEBUG_MSG('[RoomType14] operation_over is_qiang_gang_hu %s' % is_qiang_gang_hu)
        for cr in check_results:
            _cpo = cr[CHECK_PLAYER_OPT]
            # 判断操作是否是胡牌
            if _cpo == OPT_HU_DIAN_PAO_V or _cpo == OPT_HU_QIANGGANG_V:
                if _cpo == OPT_HU_QIANGGANG_V:
                    qiang_gang_he = True
                # 如果可以一炮多响
                is_first = False
                hu_players.append(cr[CHECK_PLAYER])
                continue
            if is_first:
                if _cpo == OPT_DAMINGGANG_V:
                    self.da_ming_gang_opt(cr[CHECK_PLAYER], _chapter[CUR_PAI])
                    return
                elif _cpo == OPT_PENG_V:
                    self.peng_opt(cr[CHECK_PLAYER], _chapter[CUR_PAI])
                    return
                elif _cpo == OPT_CHI_V:
                    self.chiOpt(cr[CHECK_PLAYER], cr[CHI_ARGS])
                    return
                elif _cpo == OPT_GUO_V:
                    self.guoOpt(cr[CHECK_PLAYER])
            else:
                break
        if not is_first:
            if qiang_gang_he:
                # 抢杠和
                self.qiang_gang_hu_opt(hu_players)
                return
            else:
                self.dian_pao_hu_opt(hu_players)
                return
        # 清除产生的中间数据，继续操作
        self.destroy_check_result(self.get_current_player())
        if is_qiang_gang_hu == CHECK_FLAG_XIAOMINGGANG:
            # 如果没有玩家抢杠胡，继续小明杠
            self.del_play_card_timer()
            self.set_not_hu_pai(self.get_current_player())
            self.clearFaiPaiDate()
            self.xiao_ming_gang_opt(self.get_current_player(), self.get_current_player()[SHOU_PAI][-1])
            _chapter['qiangGangCard'] = -1
        else:
            self.goNext()

    def goNext(self):
        _chapter = self.get_current_chapter()
        # 将玩家打出的牌放入自己打出牌的集合中
        # self.get_current_player()[OUT_PAIS].append(_chapter[CUR_PAI])
        # 全部过，下一个玩家操作
        self.notice_next_player(self.get_current_player(), _chapter[ROUND])

    def syncOpt(self, locationIndex, opt, pai, otherIndex):
        self.callOtherClientsFunction("syncOpt", {"locationIndex": locationIndex, "opt": opt, "pai": pai,
                                                  "otherIndex": otherIndex})
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
            _g = {'gold': v['gold'] + total_gold_change + base_sync_gold_change,
                  # 'goldChange': v['goldChange'],
                  'totalGoldChange': total_gold_change}
            _gold_info[v['entity'].info['userId']] = _g
        self.callOtherClientsFunction("syncGold", _gold_info)

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
        DEBUG_MSG('[RoomType14 id %i]------------->删除响应出牌超时定时器(%s)' % (self.id, _chapter['resOutPaiTimer']))
        self.stop_timer('resOutPaiTimer')

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
        # self.hu_tip(player['entity'].id, out_pai)

        # 移除手牌,加入出牌区
        if out_pai in _hand_cards:
            _hand_cards.remove(out_pai)
        else:
            self.debug_msg('out_pai not in _hand_cards')
            return
        _chapter[CUR_PAI] = out_pai
        self.get_current_player()[OUT_PAIS].append(_chapter[CUR_PAI])

        # 同步出牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_OUTPAI, out_pai, -1)
        # 设置不胡牌
        self.set_not_hu_pai(player)
        # 清除杠上花标记
        self.clearFaiPaiDate()
        # 玩家操作，检查过参数之后，删除系统超时操作
        self.del_play_card_timer()

        # 其他玩家；从当前玩家开始，要有顺序
        # 混牌不能吃碰杠，只能胡自身牌；双混不能碰任何牌
        is_hun_pai = out_pai in self.current_chapter.hun_pais
        is_double_hun_type = self.room_cfg.is_double_hun_type
        other_players = self.get_other_players_by_seat(player[SEAT])
        check_results = []
        for i, p in enumerate(other_players):

            # 检查吃碰杠胡
            p[CAN_PENG] = False
            p[CAN_HU] = False
            b_peng = check_peng(p[SHOU_PAI], out_pai)
            if not p[CAN_PENG] and not is_hun_pai and not is_double_hun_type:
                if b_peng:
                    p[CAN_PENG] = True

            # 郑州麻将不允许吃
            _chi = list()

            can_da_ming_gang = False
            if not is_hun_pai:
                can_da_ming_gang = check_da_ming_gang(p[SHOU_PAI], out_pai)

            b_hu = self.can_it_hu(p[SHOU_PAI], out_pai)
            if not p[CAN_HU] and b_hu:
                # 设置当前玩家可以胡牌
                p[CAN_HU] = True

            # 用于检查客户端操作
            p[ALLOW_OPT] = 0
            if len(_chi) != 0:
                p[ALLOW_OPT] |= OPT_CHI_V
            if p[CAN_PENG]:
                p[ALLOW_OPT] |= OPT_PENG_V
            if can_da_ming_gang:
                p[ALLOW_OPT] |= OPT_DAMINGGANG_V
            # 如果没有弃胡，则可以点炮胡
            if p[CAN_HU] and self.can_dian_pao(p, out_pai):
                p[ALLOW_OPT] |= OPT_HU_DIAN_PAO_V
            if p[ALLOW_OPT] != 0:
                p[ALLOW_OPT] |= OPT_GUO_V

            # 封装检查结果
            check_result = {
                CHECK_PLAYER: p,
                CHECK_CHI: _chi,
                CHECK_PENG: p[CAN_PENG],
                CHECK_DAMINGGANG: can_da_ming_gang,
                # 点炮胡
                CHECK_HU: p[CAN_HU] and self.can_dian_pao(p, out_pai),
                CHECK_HU_QIANG_GANG: False,
                CHECK_PLAYER_OPT: NO_OPT,
                CHECK_FLAG: CHECK_FLAG_OUTPAI
            }
            # 如果能碰，能大明杠、能吃、能胡将所有可以操作的玩家及允许的操作保存起来
            if p[CAN_PENG] or can_da_ming_gang or (p[CAN_HU] and self.can_dian_pao(p, out_pai)) or len(_chi) != 0:
                # 如果玩家不在线，不考虑能进行的操作
                if not p['entity'].client_death:
                    check_results.append(check_result)

        # 保存 outPaiCheckResults
        _chapter[CHECK_RESULTS] = check_results
        DEBUG_MSG('CHECK_RESULTS:%s' % _chapter[CHECK_RESULTS])

        # 设置等待玩家
        _chapter[WAIT_PLAYER] = player
        # 检查其他玩家可以进行的操作
        self.send_other_player_can_operate(check_results)

    def xiao_ming_gang_opt(self, player, pai):
        DEBUG_MSG('[RoomType14 id %i]------------->xiaoMingGangOpt CurPlayer=%s, Pai=%s' % (
            self.id, player['locationIndex'], pai))
        _chapter = self.get_current_player()
        _chapter[CUR_PAI] = pai
        other_index = GamePlayer(player).xiao_ming_gang(pai)
        # 同步小明杠消息
        self.syncOpt(player['locationIndex'], SYNCOPT_XIAOMINGGANG, pai, other_index)
        # 给此玩家发牌
        self.deal_one_card(player, True, pai)

    def an_gang_opt(self, player, pai):
        DEBUG_MSG(
            '[RoomType14 id %i]------------->anGangOpt CurPlayer=%s, Pai=%s' % (self.id, player['locationIndex'], pai))
        # 移除杠牌
        GamePlayer(player).an_gang(pai)
        # 同步暗杠消息
        self.syncOpt(player['locationIndex'], SYNCOPT_ANGANG, pai, -1)
        # 给此玩家发牌
        self.deal_one_card(player, True)

    def zi_mo_hu_opt(self, player):
        DEBUG_MSG('[RoomType14 id %i]------------->ziMoHuOpt CurPlayer=%s' % (self.id, player['locationIndex']))
        _chapter = self.get_current_chapter()
        _chapter[IS_ZI_MO_HE] = True
        _chapter[HU_TYPE] = HU_TYPE_ZI_MO
        # 同步自摸消息
        self.syncOpt(player['locationIndex'], SYNCOPT_ZIMOHU, self.get_current_chapter()[CUR_PAI], -1)
        self.hu_pai([player])

    def check_qiang_gang_hu(self, player, pai):
        """
        :param player:
        :param pai:
        :return: true：抢杠和，false：不能抢杠和
        """
        _chapter = self.get_current_chapter()
        # 检查抢杠和
        # 双混只能自摸
        if not self.room_cfg.is_double_hun_type:
            other_players = self.get_other_players_by_seat(player[SEAT])
        check_results = []
        for op_player in other_players:
            can_hu = self.can_it_hu(op_player[SHOU_PAI], pai)
            if not op_player[CAN_HU]:
                if can_hu:
                    # 设置当前玩家可以胡牌
                    op_player[CAN_HU] = True

            # 用户检查客户端操作
            op_player[ALLOW_OPT] = 0
            if op_player[CAN_HU] and self.can_dian_pao(op_player, pai):
                op_player[ALLOW_OPT] |= OPT_HU_QIANGGANG_V
                op_player[ALLOW_OPT] |= OPT_GUO_V

            # 封装检查结果
            check_result = {
                CHECK_PLAYER: op_player,
                CHECK_CHI: [],
                CHECK_PENG: False,
                CHECK_DAMINGGANG: False,
                CHECK_HU: False,
                # 抢杠和
                CHECK_HU_QIANG_GANG: can_hu and self.can_dian_pao(op_player, pai),
                CHECK_PLAYER_OPT: NO_OPT,
                CHECK_FLAG: CHECK_FLAG_XIAOMINGGANG
            }
            if can_hu and self.can_dian_pao(op_player, pai):
                if not op_player['entity'].client_death:
                    check_results.append(check_result)

        # 如果有玩家可以抢杠胡，通知玩家
        if len(check_results) != 0:
            _chapter[CHECK_RESULTS] = check_results
            # 设置等待玩家
            _chapter[WAIT_PLAYER] = player
            _chapter = self.get_current_chapter()
            for c_op in check_results:
                # 暂存起来，用于重连
                c_op[CHECK_PLAYER][CHECK_RESULT] = c_op
                _chapter[ALLOW_OPT_PLAYERS].append(c_op[CHECK_PLAYER])
                self.send_check_result_item(c_op)
                current_entity = self.get_current_player()['entity']
            self.callClientFunction(current_entity.id, 'waitOtherPlayer', {'entityId': current_entity.id})
            # 添加超时定时器,不自动出牌时不进行超时处理
            if self.info['timeDown'] > 0:
                _chapter['resOutPaiTimer'] = self.addTimer(AUTO_TIME, 0, 0)
            _chapter['deadLine'] = time.time() + AUTO_TIME
            _chapter['qiangGangCard'] = pai
            self.sync_timer_count_down(AUTO_TIME)
        # 如果没有玩家可以抢杠胡，继续小明杠
        else:
            _chapter['qiangGangCard'] = -1
            # 玩家操作，检查过参数之后，删除系统超时操作
            self.del_play_card_timer()
            self.set_not_hu_pai(player)
            self.clearFaiPaiDate()
            self.xiao_ming_gang_opt(player, pai)

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
            '[RoomType14 id %i]------------->chiOpt CurPlayer=%s, Pais=%s' % (self.id, player['locationIndex'], pai))
        _chapter = self.get_current_chapter()
        other_index = self.get_wait_player()['locationIndex']
        cur_pai = _chapter[CUR_PAI]
        # 操作次数+1
        player[OPT_COUNT] += 1
        # 清除玩家不能碰的牌
        # player[NOT_PENG_PAI].clear()
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
        _xmg = self.check_xiao_ming_gang(shou_pai, _pengs, player)
        if len(_xmg) != 0:
            player[ALLOW_OPT] |= OPT_XIAOMINGGANG_V
            self.callClientFunction(player["entity"].id, CLIENT_FUNC_XIAOMINGGANG, _xmg)
        self.notify_out_pai(player, _noAllowDrapCard)

    def res_out_pai_peng_opt(self, player, pai):
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_PENG_V
        self.operation_over(operator=player['entity'].id)

    def peng_opt(self, player, pai):
        DEBUG_MSG(
            '[RoomType14 id %i]------------->pengOpt CurPlayer=%s, Pai=%s' % (self.id, player['locationIndex'], pai))
        self.check_opt_pai(pai)
        _chapter = self.get_current_chapter()
        other_index = self.get_wait_player()['locationIndex']
        # 记录能杠但是碰的牌
        # if player[SHOU_PAI].count(pai) == 3:
        #     player['canNotXMGang'].append(pai)
        # 清除不可以碰的牌
        # player[NOT_PENG_PAI].clear()

        # 操作次数+1
        player[OPT_COUNT] += 1

        other_player = self.get_player_by_location(other_index)
        GamePlayer(player).peng(pai, other_player)
        # self.peng(player, pai, other_index)

        # 销毁check_results
        self.destroy_check_result(player)
        # 同步碰牌消息
        self.syncOpt(player['locationIndex'], SYNCOPT_PENG, pai, other_index)
        self.ting_tip(player['entity'].id)

        _hand_cards = player[SHOU_PAI]
        _pengs = player[PENG_S]
        _xmg = self.check_xiao_ming_gang(_hand_cards, _pengs, player)
        _ag = check_an_gang(_hand_cards)
        # 如果没有小明杠、暗杠，继续出牌
        if len(_xmg) == 0 and len(_ag) == 0:
            self.notify_out_pai(player)
        # 如果有小明杠，暗杠，通知操作
        else:
            self.check_can_opt_after_deal(player, is_gang_after_peng=True)

    def res_play_card_da_ming_gang_opt(self, player, pai):
        """

        :param player:
        :param pai:
        :return:
        """
        DEBUG_MSG('[RoomType14 id %i]------------->resOutPaiDaMingGangOpt CurPlayer=%s, Pai=%s' % (
            self.id, player['locationIndex'], pai))
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_DAMINGGANG_V
        self.operation_over(operator=player['entity'].id)

    def da_ming_gang_opt(self, player, pai):
        DEBUG_MSG('[RoomType14 id %i]------------->daMingGangOpt CurPlayer=%s, Pai=%s' % (
            self.id, player['locationIndex'], pai))
        self.check_opt_pai(pai)
        _chapter = self.get_current_chapter()
        other_index = self.get_wait_player()['locationIndex']

        # 操作次数+1
        player[OPT_COUNT] += 1

        # 清除不可以碰的牌
        # player[NOT_PENG_PAI].clear()

        other_player = self.get_player_by_location(other_index)
        GamePlayer(player).da_ming_gang(pai, other_player)
        # 销毁check_results
        self.destroy_check_result(player)
        # 同步大明杠消息
        self.syncOpt(player['locationIndex'], SYNCOPT_DAMINGGANG, pai, other_index)
        # 给此玩家发牌
        self.deal_one_card(player, True, pai)

    def res_out_pai_dian_pao_hu_opt(self, player):
        """
        点炮胡
        :param player:
        :return:
        """
        DEBUG_MSG(
            '[RoomType14 id %i]------------->resOutPaiDianPaoHuOpt CurPlayer=%s' % (self.id, player['locationIndex']))
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_HU_DIAN_PAO_V
        self.operation_over(operator=player['entity'].id, operation_name=OPT_HU_DIAN_PAO)

    def dian_pao_hu_opt(self, players):
        DEBUG_MSG('[RoomType14 id %i]------------->dianPaoHuOpt CurPlayer=%s' % (self.id, players))
        # 要确保多个点炮胡操作顺序执行
        _chapter = self.get_current_chapter()
        _chapter[IS_DIAN_PAO_HE] = True
        fp_player = self.get_wait_player()
        other_players = self.get_other_players_by_seat(fp_player[SEAT])
        _chapter[HU_TYPE] = HU_TYPE_DIAN_PAO
        for other in other_players:
            # if other in players:
            if self.is_player_in_players(other, players):
                other[SHOU_PAI].append(_chapter[CUR_PAI])
                DEBUG_MSG('player cards:%s,qiangGangCard%s' % (other[SHOU_PAI], _chapter[CUR_PAI]))
                players.clear()
                players.append(other)
        # 同步点炮胡消息
        self.syncOpt(players[0]['locationIndex'], SYNCOPT_DIANPAOHU, _chapter[CUR_PAI], fp_player['locationIndex'])

        self.hu_pai(players, fp_index=fp_player['locationIndex'])

    # ---------------------  抢杠和操作  ---------------------

    def res_out_pai_qiang_gang_hu_opt(self, player):
        """
        抢杠胡
        :param player:
        :return:
        """
        DEBUG_MSG('[RoomType14 id %i]------------->resOutPaiQiangGangHuOpt CurPlayer=%s' % (self.id, player))
        _chapter = self.get_current_chapter()
        _check_results = _chapter[CHECK_RESULTS]
        for cr in _check_results:
            if player['entity'].id == cr[CHECK_PLAYER]['entity'].id:
                cr[CHECK_PLAYER_OPT] = OPT_HU_QIANGGANG_V
        self.operation_over(operator=player['entity'].id)

    def qiang_gang_hu_opt(self, players):
        DEBUG_MSG('[RoomType14 id %i]------------->qiangGangHuOpt CurPlayer=%s' % (self.id, players))
        _chapter = self.get_current_chapter()
        # 记录一下抢杠和
        _chapter[IS_QIANG_GANG_HE] = True
        fp_player = self.get_wait_player()
        other_players = self.get_other_players_by_seat(fp_player[SEAT])
        _chapter[HU_TYPE] = HU_TYPE_QIANG_GANG
        qiang_gang_card = _chapter['qiangGangCard']
        # 抢杠胡，将胡的牌加入手中
        for other in other_players:
            # if other in players:
            if self.is_player_in_players(other, players):
                other[SHOU_PAI].append(qiang_gang_card)
                players.clear()
                players.append(other)
                DEBUG_MSG('player shou_pai:%s,qiangGangCard%s' % (other[SHOU_PAI], qiang_gang_card))
        # 同步抢杠和消息
        self.syncOpt(-1, SYNCOPT_QIANGGANGHU, _chapter[CUR_PAI], fp_player['locationIndex'])
        self.hu_pai(players, fp_index=fp_player['locationIndex'])

    def hu_pai(self, hu_players, fp_index=-1):
        """
        胡牌
        :param hu_players: hu_player=None时，表示荒庄
        :param fp_index: 放炮玩家的位置，-1 表示没人放炮
        :return:
        """
        _chapter = self.get_current_chapter()
        _chapter[HU_PLAYER] = hu_players
        _chapter[FANG_PAO_INDEX] = fp_index
        # 获取胡牌特殊规则
        # todo：适配一炮多响
        for player in hu_players:
            player['special'] = self.hu_type(player)
        DEBUG_MSG('[RoomType14 id %i]------------->HuOpt huIndex=%s, fangPaoIndex=%s' % (self.id, hu_players, fp_index))
        self.end_round()

    def hu_tip(self, account_entity_id, play_card):
        """
        胡牌提示
        :param account_entity_id:
        :param play_card:
        :return:
        """
        _chapter = self.get_current_chapter()
        player = self.get_current_player()
        DEBUG_MSG("hu_tip %s %s" % (player, account_entity_id))
        if player['entity'].id != account_entity_id:
            return
        hand_cards = player[SHOU_PAI].copy()
        DEBUG_MSG('hu_tip hand_cards%s' % hand_cards)
        tip_cards = []
        can_hu_range = self.can_hu_cards_range(hand_cards)
        # 1.移除要出的牌      2.加入任意牌     3.移除杠牌      4.判断能不能胡    5.判断能不能次
        if play_card in hand_cards:
            # 移除要出的牌
            hand_cards.remove(play_card)
            # 加入任意牌
            for card in can_hu_range:
                temp = hand_cards.copy()
                temp.append(card)
                # 平胡
                can_hu = self.can_it_hu(temp)
                if can_hu:
                    tip_cards.append(card)

        # 检查是否胡任意牌，如果胡任意牌,胡牌提示中加20张红中
        if self.hu_anything(hand_cards):
            DEBUG_MSG('self.hu_anything True')
            for i in range(34):
                tip_cards.append(i)

        card_info = {}
        for card in tip_cards:
            card_info[str(card)] = self.get_card_count_un_reveal(card,
                                                                 exclude_player=account_entity_id)
        self.callClientFunction(account_entity_id, 'HuTip', {'huCards': card_info})

    def hu_anything(self, hand_cards):
        """
        胡任意牌前提：
        1.开启红中赖子
        :param hand_cards: 手牌
        :param card_range:
        :param tip_cards:
        :return:
        """
        if not self.room_cfg.is_use_hun_pai:
            return False

        new_hand_cards = hand_cards.copy()
        for v in range(34):
            new_hand_cards.append(v)
            can_hu = self.can_it_hu(new_hand_cards)
            del new_hand_cards[-1]
            if not can_hu:
                return False

        return True

    def check_allow_dian_pao_hu(self, player):
        """
        检查是否允许指定玩家点炮
        :param player:
        :return:
        """
        opt_v = OPT_DICT[OPT_HU_DIAN_PAO]
        if (player[ALLOW_OPT] & opt_v) == opt_v:
            return True
        return False

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

        if self.chapters[self.cn]["chapterState"] != CHAPTER_STATE_TOTAL_SETTLEMENT:
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
                self.base.cellToBase(
                    {"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                     "teaHouseId": self.info["teaHouseId"]})
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                return

            # 如果房间中没有人，房间已开始，解散
            if self.started:
                self.base.cellToBase(
                    {"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                     "teaHouseId": self.info["teaHouseId"]})
                # 一局都没结算并且为房主支付，归还钻石
                if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                    self.base.cellToBase({"func": "returnRoomCardToCreator"})
                return

        elif self.is_gold_session_room():
            # 如果是手动解散房间或者总结算，或者房间开始却没有人，解散房间
            if self.is_manual_disband or self.total_settlement_ed or self.started:
                self.base.cellToBase({"func": "disbandGoldSessionRoom", "roomId": self.info["roomId"],
                                      "level": self.info["level"]})

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

    def on_account_cell_destroy(self, account_db_id):
        """
        房间中的玩家被销毁
        :param account_db_id:
        :return:
        """
        DEBUG_MSG('RoomType14 cell on_account_cell_destroy account_db_id:%s' % account_db_id)
        _chapter = self.get_current_chapter()
        all_death = True
        for p in _chapter[PLAYER_IN_GAME].values():
            if p['entity']:
                all_death = False
                break
        # 如果房间中没有人，房间已开始，解散
        if self.started and all_death:
            self.base.cellToBase(
                {"func": "disbandTeaHouseRoom", "roomId": self.info["roomId"],
                 "teaHouseId": self.info["teaHouseId"]})
            # 一局都没结算并且为房主支付，归还钻石
            if self.settlement_count < 1 and self.info['payType'] == Const.PayType.RoomCreator:
                self.base.cellToBase({"func": "returnRoomCardToCreator"})
            return
        pass

    # def j_258(self, cards, red_cards):
    #     """
    #     是否满足258将判断
    #     :param red_cards: 如果有红中癞子，该参数为红中癞子变为胡牌牌型后的牌列表,如果红中赖子关闭，cards=red_cards
    #     :param cards:
    #     :return:
    #     """
    #     if not self.info['j258']:
    #         return True
    #     else:
    #         _258 = [1, 4, 7, 10, 13, 16, 19, 22, 25]
    #         # 红中赖子，红中也满足二五八将
    #         DEBUG_MSG('j_258 red_cards:%s' % red_cards)
    #         if self.room_cfg.is_open_hun_pai:
    #             for _r in red_cards:
    #                 for i in _258:
    #                     if _r and _r.count(i) == 2:
    #                         return True
    #         else:
    #             for i in _258:
    #                 if cards and cards.count(i) == 2:
    #                     return True
    #         return False

    def get_special_multiple(self, special):
        """
        获取规则对应翻倍倍数
        :param special:
        :return:
        """
        if len(self.hu_special_multiple) == 0:
            # self.hu_special_multiple[HU_RESULT_PING_HU] = 1
            self.hu_special_multiple[HU_RESULT_GANG_SHANG_HUA] = 2 if self.room_cfg.is_gang_kai_hua_add_double else 0
            # self.hu_special_multiple[HU_RESULT_FOUR_HUN] = 1
            self.hu_special_multiple[HU_RESULT_SEVEN_PAIR] = 2 if self.room_cfg.is_seven_pair_add_double else 0

        # DEBUG_MSG("get_special_multiple %s %s" % (self.hu_special_multiple, self.room_cfg.is_seven_pair_add_double))
        if special in self.hu_special_multiple:
            return self.hu_special_multiple[special]
        return 0

    def can_it_hu(self, shou_pais, pai=-1, hu_result=None):
        """
        胡牌判断
        :param shou_pais:
        :param pai: 别人出的牌，不能作为赖子，只能做自身牌
        :param hu_result:7:七星对； 4：四混胡； 1：平胡
        :return:
        """
        # DEBUG_MSG("can_it_hu %s, %s" % (self.room_cfg.is_zi_mo_hu, pai))
        if self.room_cfg.is_zi_mo_hu and pai != -1:
            return False

        new_show_pais = shou_pais.copy()
        if pai != -1:
            new_show_pais.append(pai)

        # 七星判断
        ret = mj.RoomType14Calculator.is_seven_pair(new_show_pais)
        if ret:
            if hu_result is not None:
                hu_result.append(HU_RESULT_SEVEN_PAIR)
            return True

        ret = False
        temp_hu_result = HU_RESULT_PING_HU
        if self.room_cfg.hun_pai_type == 0:
            # 不带混
            ret = mj.RoomType14Calculator.can_hu_pai(new_show_pais)
        elif self.room_cfg.hun_pai_type == 1:
            # 单混
            hun_zi_list = self.current_chapter.hun_pais
            hun_pai_count = mj.RoomType14Calculator.hun_pai_count(shou_pais, hun_zi_list)
            if hun_pai_count == 4:
                ret = True
                temp_hu_result = HU_RESULT_FOUR_HUN
            else:
                ret = mj.RoomType14Calculator.can_hu_contain_lai_zi(shou_pais, hun_zi_list, pai)

        elif self.room_cfg.hun_pai_type == 2:
            # 双混, 只能自摸
            if pai == -1:
                hun_zi_list = self.current_chapter.hun_pais
                ret = mj.RoomType14Calculator.can_hu_contain_lai_zi(new_show_pais, hun_zi_list, pai)

        if ret and hu_result is not None:
            hu_result.append(temp_hu_result)
        return ret

    def hu_type(self, player):
        """
        检测胡牌类型
        :param player: 玩家信息
        :return:
        """
        # 七星胡:7
        # 四混:4
        # 普通胡:1
        _chapter = self.get_current_chapter()
        cards = player[SHOU_PAI]
        hu_result = []
        self.can_it_hu(cards, hu_result=hu_result)
        DEBUG_MSG("hu_type %s" % hu_result)
        # can_hu_range = self.can_hu_cards_range(cards)
        # ret = mj.MohjangCalculator.is_hu_pai(cards, can_hu_range, magic_red=self.room_cfg.is_open_hun_pai)
        hu_type = []
        # 七星对判断
        # or hu_result == HU_RESULT_FOUR_HUN
        if HU_RESULT_SEVEN_PAIR in hu_result:
            hu_type.append(HU_RESULT_SEVEN_PAIR)
        # # 清一色判断
        # if self.is_same_color(player):
        #     hu_type.append(3)
        # 杠上开花判断
        if _chapter[IS_GANG_SHANG_KAI_HUA] >= 0:
            hu_type.append(HU_RESULT_GANG_SHANG_HUA)
        return hu_type

    def is_same_color(self, player, cards=None):
        """
        是否是清一色
        :param cards: 特殊指定手牌，听牌提示时，不取玩家的实际手牌
        :param player:
        :return:
        """
        if cards is not None:
            hand_cards = cards.copy()
        else:
            hand_cards = player[SHOU_PAI].copy()
        # 如果是红中癞子，不判断红中
        if self.room_cfg.is_use_hun_pai:
            while 31 in hand_cards:
                hand_cards.remove(31)

        if len(hand_cards) != 0:
            color = int(hand_cards[0] / 9)
        else:
            color = -1
        # 清一色不能是风
        # if color == 3:
        #     return False
        for c in hand_cards:
            if int(c / 9) != color:
                return False

        for p in player[PENG_S].keys():
            if color == -1:
                color = int(p / 9)
            elif int(p / 9) != color:
                return False

        for x_m in player[XIAO_MING_GANG_S].keys():
            if color == -1:
                color = int(x_m / 9)
            elif int(x_m / 9) != color:
                return False

        for m in player[DA_MING_GANG_S].keys():
            if color == -1:
                color = int(m / 9)
            elif int(m / 9) != color:
                return False

        for an in player[AN_GANG_S]:
            if color == -1:
                color = int(an / 9)
            elif int(an / 9) != color:
                return False

        return True

    def can_dian_pao(self, player, out_card):
        """
        能不能点炮
        :param out_card: 打出的牌
        :param player:
        :return:
        """
        if self.room_cfg.is_zi_mo_hu or self.room_cfg.is_double_hun_type:
            return False

        if player['qiDianPao']:
            return False

        # 如果开启过胡只可自摸,玩家弃胡后只可以自摸
        # if self.info['onlySelfAfterPass']:
        # if player[QI_HU]:
        #     return False

        # else:
        #     if player['qiDianPao']:
        #         return False

        return True

    def can_hu_cards_range(self, hand_cards):
        """
        可能跟手牌有关系的牌列表
        :param hand_cards:
        :return:
        """
        hand_cards = mj.RoomType14Calculator.analyse1(hand_cards)
        card_range = []
        mj.RoomType14Calculator.select_perhaps_pai(hand_cards, card_range)

        # 增加混牌
        if self.room_cfg.is_use_hun_pai:
            for k in self.current_chapter.hun_pais:
                if k not in card_range:
                    card_range.append(k)

        # 加一张手牌里不存在的风牌，增加胡任意牌成功率
        for i in range(27, 34):
            if i in self.current_chapter.hun_pais:
                continue
            if i not in card_range:
                card_range.append(i)
                return card_range

        return card_range

    # 1 分享到微信
    def share_to_wx(self, account_id):
        if self.info['roomType'] == 'card':
            title = '郑州麻将房间号：' + str(self.info["roomId"])
        elif self.info['teaHouseId'] != -1:
            title = '郑州麻将房间' + ',冠名赛id:' + str(self.info['teaHouseId'])
        else:
            title = '郑州麻将房间'
        # single_color = '二人单色' if self.info['maxPlayersCount'] == 2 else '四人滑水'
        red_magic = '混子' if self.room_cfg.is_use_hun_pai else ''
        # single_color = "????"
        base_score = '底分：' + str(
            self.room_cfg.zi_mo_score if self.room_cfg.is_zi_mo_hu else self.room_cfg.dian_pao_score)
        fish = '杠分:' + str(self.room_cfg.gang_di_score)
        chapter_count = '局数' + str(self.info['maxChapterCount'])
        con = str('%s,%s,%s,%s' % (chapter_count, red_magic, base_score, fish))
        self.callClientFunction(account_id, 'ShareToWX', {'title': title, 'content': con})

    def ting_tip(self, account_entity_id):
        """
        听牌提示
        :param account_entity_id:实体id
        :return:tips_cards:听牌
        """
        _chapter = self.get_current_chapter()
        player = self.get_current_player()
        if player['entity'].id != account_entity_id:
            return

        _hand_cards = player[SHOU_PAI].copy()
        ting_tip_cards = []
        checked_cards = []
        # 听牌对应的最大胡牌类型
        hu_max = {}
        # 胡牌最多的听牌
        hu_most = {}
        # 1.移除要出的牌      2.加入任意牌     3.移除杠牌      4.判断能不能胡    5.判断能不能次
        #
        start = time.time()
        for play_card in _hand_cards:
            if play_card in checked_cards:
                continue
            checked_cards.append(play_card)
            # 听牌后能胡的牌
            can_hu_card_after_ting = []
            # DEBUG_MSG('can_ting checked_cards:%s,check_card:%s' % (checked_cards, play_card))
            hand_cards = player[SHOU_PAI].copy()
            cards_hu_range = self.can_hu_cards_range(hand_cards)

            # play_card 打出后能听的牌
            if play_card in hand_cards:
                # 移除要出的牌
                hand_cards.remove(play_card)
                # 加入任意牌
                start2 = time.time()
                for card in cards_hu_range:
                    temp = hand_cards.copy()
                    temp.append(card)
                    # 记录胡牌类型
                    hu_result_type = []
                    multiple = 1
                    start3 = time.time()
                    can_hu = self.can_it_hu(temp, hu_result=hu_result_type)
                    end3 = time.time()

                    if can_hu:
                        # 记录可以胡的牌
                        can_hu_card_after_ting.append(card)
                        if play_card not in ting_tip_cards:
                            # 记录打出后可以听牌的牌
                            ting_tip_cards.append(play_card)

                        # 如果胡牌类型是0:平胡，7:七星胡，4：4混
                        if len(hu_result_type) != 0:
                            # 计算胡牌类型
                            _m = self.get_special_multiple(hu_result_type[0])
                            if _m != 0:
                                multiple *= _m

                        if play_card not in hu_max or multiple > hu_max[play_card]:
                            hu_max[play_card] = multiple

            # 检查是否胡任意牌，如果胡任意牌,胡牌提示中加20张红中
            if self.hu_anything(hand_cards):
                DEBUG_MSG('self.hu_anything True')
                for i in range(34):
                    can_hu_card_after_ting.append(i)

            hu_most[play_card] = len(can_hu_card_after_ting)
        end = time.time()
        hu_most_count = 0
        hu_most_list = []
        # 找出最多
        for k, v in hu_most.items():
            if v > hu_most_count:
                hu_most_count = v

        # 找出数量最多的牌
        for k, v in hu_most.items():
            if v == hu_most_count:
                hu_most_list.append(k)

        # 当所有多牌提示的胡牌数量都相同时，不发送多牌提示
        if len(hu_most_list) == len(hu_most):
            hu_most_list = []

        hu_max_multiple = 1
        hu_max_list = []
        # 找出最大牌型的倍数
        for k, v in hu_max.items():
            if v > hu_max_multiple:
                hu_max_multiple = v

        # 没有特殊牌型时，不发送大牌提示
        if hu_max_multiple == 1:
            hu_max_list = []
        else:
            for k, v in hu_max.items():
                if v == hu_max_multiple:
                    hu_max_list.append(k)

        DEBUG_MSG('听牌结果：%s' % ting_tip_cards)
        self.callClientFunction(player['entity'].id, CLIENT_FUNC_TINGPAI, {'tingCards': ting_tip_cards,
                                                                           'huMost': hu_most_list,
                                                                           'huMax': hu_max_list})

    def check_xiao_ming_gang(self, hand_cards, pengs, player):
        """
        检查小明杠数量
        :param hand_cards: 手牌
        :param pengs: 当前手牌中所有的碰牌集合
        :return: 数组，可以小明杠的牌(可能有多个)
        """
        ret = []
        for p in pengs:
            # if p in player['canNotXMGang']:
            #     continue
            count = get_card_count_from(hand_cards, p)
            if count >= 1:
                ret.append(p)
        return ret

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
        game_type = '郑州麻将'
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


def check_an_gang(hand_cards):
    """
    :param hand_cards: 手牌
    :return: 数组，可以暗杠的牌（可能有多个）
    """
    already_check = []
    an_gang = []
    for c in hand_cards:
        if c in already_check:
            continue
        count = get_card_count_from(hand_cards, c)
        if count == 4:
            an_gang.append(c)
        already_check.append(c)
    return an_gang


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


def re_convert_hua_pai(pai):
    """
    转换花牌
    :param pai:
    :return:
    """
    if pai == 34:
        return pai | 1 << 8
    elif pai == 35:
        return pai | 1 << 9
    elif pai == 36:
        return pai | 1 << 10
    elif pai == 37:
        return pai | 1 << 11
    elif pai == 38:
        return pai | 1 << 12
    elif pai == 39:
        return pai | 1 << 13
    elif pai == 40:
        return pai | 1 << 14
    elif pai == 41:
        return pai | 1 << 15


def to_array(shou_pai):
    """
    转化为数组
    :param shou_pai:
    :return:
    """
    arr = [0] * 34
    for i in shou_pai:
        arr[i] += 1
    return arr
