# -*- coding: utf-8 -*-
import datetime
import time

import DBCommand

from FrameWork.Mgr.Manger import *
from KBEDebug import *
import KBEngine
import random
import Const
import Util


class RoomInfo:
    # 所有房间的字典,key是gold或者card,value是golds或者cards
    roominfos = {}

    def __init__(self):
        self.roominfos = {
            "gold": {},
            "card": {},
            "gameCoin": {},
            'normalGameCoin': {},
            'challenge': {}
        }


def gold_session_manager():
    """
    获取goldSessionMgr
    :return:
    """
    return KBEngine.globalData["GoldSessionManager"].mgr


def tea_house_manager():
    """
    获取teaHouseMgr
    :return:
    """
    return KBEngine.globalData["TeaHouseManager"].mgr


class RoomManager(Manger):
    # 代开房间上限
    substitute_limit = 9
    per_player_room_card_use = 2
    mainTimerId = 0

    # 所有房间的字典,key是房间类型,value是这种类型所有的房间
    rooms = {
        Const.RoomType.RoomType1: RoomInfo(),
        Const.RoomType.RoomType2: RoomInfo(),
        Const.RoomType.RoomType3: RoomInfo(),
        Const.RoomType.RoomType4: RoomInfo(),
        Const.RoomType.RoomType6: RoomInfo(),
        Const.RoomType.RoomType5: RoomInfo(),
        Const.RoomType.RoomType7: RoomInfo(),
        Const.RoomType.RoomType8: RoomInfo(),
        Const.RoomType.RoomType10: RoomInfo(),
        Const.RoomType.RoomType11: RoomInfo(),
        Const.RoomType.RoomType12: RoomInfo(),
        Const.RoomType.RoomType13: RoomInfo(),
        Const.RoomType.RoomType14: RoomInfo(),
        Const.RoomType.RoomType15: RoomInfo(),
        Const.RoomType.RoomType16: RoomInfo(),
        Const.RoomType.RoomType18: RoomInfo(),
        Const.RoomType.RoomType21: RoomInfo(),
        Const.RoomType.RoomType22: RoomInfo()

    }

    def __init__(self):
        Manger.__init__(self)
        self.snoring_all_room = False
        self.snoring_msg = ""
        self.mainTimerId = 0
        self.last_notify_tick = 0

    def addTimer(self):
        self.mainTimerId = self.add_timer(3 * 60, 17, 0)
        self.last_notify_tick = 0

    def create_room(self, _creator_db_id, _config, is_fake=False, is_auto=False, creator_id=-1,
                    creator_name='', creator_entity=None, record_sql=True):
        """
        创建房间
        :param creator_name:
        :param creator_entity: 自动创建时拿到楼主实体
        :param is_fake:
        :param _creator_db_id:
        :param _config:
        :return:
        """
        _account = KBEngine.globalData["AccountMgr"].mgr.get_account(_creator_db_id)
        if _account is None:
            _account = creator_entity
        if _account is None:
            ERROR_MSG('create room 楼主实体未找到')
            return
        _type = _config["type"]
        _roomType = _config["roomType"]
        _room = KBEngine.createEntityLocally(_type, {})
        _room.is_fake = is_fake
        _room.record_sql = record_sql
        _room.info["creator"] = _creator_db_id
        if is_auto:
            _room.info["creatorAccountId"] = creator_id
            _room.info["creatorName"] = creator_name
        else:
            _room.info["creatorAccountId"] = KBEngine.globalData["AccountMgr"].mgr.get_account(
                _creator_db_id).databaseID
            _room.info["creatorName"] = KBEngine.globalData["AccountMgr"].mgr.get_account(_creator_db_id).name
        _room.info["roomId"] = self.random_room_id(_type, _roomType)
        # 游戏类型
        _room.info["type"] = _type
        # 入场限制
        _room.info["gameLevel"] = _config["gameLevel"]
        # 支付方式：0：房主支付,1:AA支付
        _room.info['payType'] = _config['payType']
        # 房间类型
        _room.info["roomType"] = _roomType
        # gps开关
        _room.info['gps'] = _config['gps'] if 'gps' in _config else False
        _room.info["maxPlayersCount"] = _config["maxPlayersCount"]
        _room.info['roomCardConsume'] = 0
        _room.info["canVoice"] = _config["canVoice"]
        _room.roomId = _room.info["roomId"]

        # 是否是代开房间
        if "substitute" in _config.keys():
            _room.info["substitute"] = _config["substitute"]

        # 是否是金币场
        _room.info['level'] = _config['level'] if 'level' in _config.keys() else 0
        # 房费
        _room.info['roomRate'] = _config['roomRate'] if 'roomRate' in _config.keys() else 0

        # 是否允许观战
        if _room.info['type'] in Const.CanWatchGame.can_watch_game:
            if 'witness' in _config:
                _room.info["witness"] = _config["witness"]
            else:
                _room.info["witness"] = False

        if _type == Const.RoomType.RoomType1:
            _room.info["hasAnthorizeBuying"] = _config["hasAnthorizeBuying"]
            _room.info["maxRound"] = _config["maxRound"]
            # 1 特殊玩法的   顺子大于金花
            _room.info["straightBigSameColor"] = _config["straightBigSameColor"]
            # 1 特殊玩法的235 大 豹子
            _room.info["twoThreeFiveBigLeopard"] = _config["twoThreeFiveBigLeopard"]
            # 1 特殊玩法的123 大 JQk   123的首字母
            _room.info["attStraightBigJqk"] = _config["attStraightBigJqk"]
            _room.info["compareCardRound"] = _config["compareCardRound"]
            _room.info['compareCardDouble'] = _config["compareCardDouble"]
            _room.info['sequentialLookCard'] = _config['sequentialLookCard']
            _room.info["lookCardRound"] = _config["lookCardRound"]
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            _room.info["hasPushToGuild"] = _config["hasPushToGuild"]
            _room.info["betBase"] = _config["betBase"]
            # 1 防作弊
            _room.info["hasPreventCheat"] = _config["hasPreventCheat"]
            _room.info["addBetRule"] = _config["addBetRule"]
            # 1 同牌比牌方式   1是比先比为输   0 是先按照花色来比
            _room.info["sameCardCompare"] = _config["sameCardCompare"]
            # 1  首位100，准备101，房主102、2-- 满2人开始、4--满4人开始.....10--满10人开始
            _room.info["gameStartType"] = _config["gameStartType"]
            # 同花喜钱0 - -不收喜钱、5 - -同花顺5分、10 - -同花顺10分、15 - -同花顺15分、30 - -同花顺30分
            _room.info["straightXiQian"] = _config["straightXiQian"]
            #  豹子喜钱   0 - -不收喜钱、10 - -豹子10分、20 - -豹子20分、30 - -豹子30分、50 - -豹子50分
            _room.info["leopardXiQian"] = _config["leopardXiQian"]
            # 大赢家数量
            _room.info['winnerCount'] = _config['winnerCount']
            if 'timeDown' in _config:
                # 倒计时
                _room.info['timeDown'] = _config['timeDown']
            else:
                _room.info['timeDown'] = 45
        elif _type == Const.RoomType.RoomType4:
            _room.info["betBase"] = _config["betBase"]
            # 游戏模式
            _room.info["playMode"] = _config["playMode"]
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 最大抢庄
            _room.info["maxGrabBanker"] = _config["maxGrabBanker"]
            _room.info["gamePlay"] = _config["gamePlay"]
            # 禁止搓牌
            _room.info["prohibitedCuoPai"] = _config["prohibitedCuoPai"]
            # 暗抢庄家
            _room.info["darkGrabBanker"] = _config["darkGrabBanker"]
            # 特殊牌型
            _room.info["cardTypeMultiple"] = _config["cardTypeMultiple"]
            # 游戏开始类型
            _room.info["gameStartType"] = _config["gameStartType"]
            # 推注
            _room.info["tuiZhu"] = _config["tuiZhu"]
            # 买码
            _room.info["maiMa"] = _config["maiMa"]
            # 推注限制
            _room.info["tuiZhuLimit"] = _config["tuiZhuLimit"]
            # 下注加倍
            _room.info["betDouble"] = _config["betDouble"]
            # 王赖玩法
            _room.info["scorpion"] = _config["scorpion"]
            # 大赢家数量
            _room.info['winnerCount'] = _config['winnerCount']
            # 最低抢庄分数
            _room.info['grabBankerLevel'] = _config['grabBankerLevel']
            # 倍数
            _room.info['multiple'] = _config['multiple']
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
        elif _type == Const.RoomType.RoomType5:
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 硬次 & 软次  0硬   1软
            _room.info["softOrHardCi"] = _config['softOrHardCi']
            # 玩法  0 不次风 1 庄加倍 2 包次 3 带风 4 下米
            _room.info["playingMethod"] = _config['playingMethod']
            # 杠底
            _room.info["gangDi"] = _config['gangDi']
            # 自摸分
            _room.info["ziMo"] = _config['ziMo']
            # 次底
            _room.info["ciDi"] = _config["ciDi"]
            # 下米
            _room.info["xiaMi"] = _config["xiaMi"]
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            self.room5_conflict(_room.info)
        elif _type == Const.RoomType.RoomType6:
            # 1 房间底分
            _room.info["baseScore"] = _config["baseScore"]
            # 1 抢地主的方式  随机先叫  赢家先叫
            _room.info["callLandlordType"] = _config["callLandlordType"]

            #  1 倍数封顶需求代码
            # room.info["multipleCaps"] = _config["multipleCaps"]
            _room.info["bombCaps"] = _config["bombCaps"]
            #  牌局进入的局数  根据前端选择的局数来确定
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 1 双王必叫特殊规则
            _room.info["doubleKingGrab"] = _config["doubleKingGrab"]
            # 1 记牌器开关
            _room.info["clcCardSwitch"] = _config["clcCardSwitch"]
            # 1 玩游戏类型  抢地主  还是叫分斗地主
            _room.info["LandlordGameType"] = _config["LandlordGameType"]
            # 是否带有四带二牌型
            _room.info["SiDaiEr"] = _config["SiDaiEr"]
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
        elif _type == Const.RoomType.RoomType7:
            _room.info["betLimit"] = _config["betLimit"]
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            _room.info["grabBankerType"] = _config["grabBankerType"]
        elif _type == Const.RoomType.RoomType8:
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 抢庄模式
            _room.info["grabBankerType"] = _config["grabBankerType"]
            # 是否加锅
            _room.info["pot"] = _config["pot"]
            # 1 小天九、2 大天九
            _room.info["playMode"] = _config["playMode"]
            # 道数：2，3
            _room.info["stakeCount"] = _config["stakeCount"]
            # 牌型:1 炸弹，2 地九娘娘 3 鬼子 4 天王九，数组，包含就代表有
            _room.info["cardType"] = _config["cardType"]
            # 自动开牌时间
            _room.info["autoCompareTime"] = _config["autoCompareTime"]
            # 下注模式:0,选分，1，2，5，8，10 固定分
            _room.info["stakeMode"] = _config["stakeMode"]
            # 锅底分数
            _room.info["potBase"] = _config["potBase"]
            # 最小下注
            _room.info["minStake"] = _config["minStake"]
            # 加锅玩法，是否是一人一锅
            _room.info['onePersonOnePot'] = _config['onePersonOnePot']
            # 爆锅上限
            _room.info['potMaxMultiple'] = _config['potMaxMultiple']
            if _config["pot"]:
                # 增加下注上限
                _room.info['setStakeLimit'] = Const.GameConfigJson.config_json[_type][_roomType]['setStakeLimit']
            else:
                _room.info['setStakeLimit'] = -1
            self.room8_conflict(_room.info)
        elif _type == Const.RoomType.RoomType10:
            # 钓鱼开关
            _room.info['canFishing'] = _config['canFishing']
            # 最大局数
            _room.info['maxChapterCount'] = _config['maxChapterCount']
            # 锅底分数
            _room.info['potBase'] = _config['potBase']
            # 搓牌
            _room.info['rubbingCard'] = _config['rubbingCard']
            # 最小下注
            _room.info['minStake'] = _config['minStake']
            # 八叉翻倍
            _room.info['eightXDouble'] = _config['eightXDouble']
            # 爆锅上限
            _room.info['potMaxMultiple'] = _config['potMaxMultiple']
        elif _type == Const.RoomType.RoomType11:
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 抢庄模式
            _room.info["grabBankerType"] = _config["grabBankerType"]
            # 是否加锅
            _room.info["pot"] = _config["pot"]
            # 1 小天九、2 大天九
            _room.info["playMode"] = _config["playMode"]
            # 翻倍规则
            _room.info['multipleRules'] = _config['multipleRules']
            # 道数：2，3
            _room.info["stakeCount"] = _config["stakeCount"]
            # 自动开牌时间
            _room.info["autoCompareTime"] = _config["autoCompareTime"]
            # 下注模式:0,选分，1，2，5，8，10 固定分
            _room.info["stakeMode"] = _config["stakeMode"]
            # 锅底分数
            _room.info["potBase"] = _config["potBase"]
            # 最小下注
            _room.info["minStake"] = _config["minStake"]
            # 加锅玩法，是否是一人一锅
            _room.info['onePersonOnePot'] = _config['onePersonOnePot']
            # 爆锅上限
            _room.info['potMaxMultiple'] = _config['potMaxMultiple']
        elif _type == Const.RoomType.RoomType12:
            # 胡牌类型 int  0：点炮，1：自摸
            _room.info['huType'] = _config['huType']
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            # 单色    int 0：万，1：筒，2：条
            _room.info['singleColor'] = _config['singleColor']
            # 底分    int
            _room.info['baseScore'] = _config['baseScore']
            # 鱼子    int
            _room.info['fish'] = _config['fish']
            # 鱼母    int 0：单鱼，1：鱼吃鱼
            _room.info['fishMother'] = _config['fishMother']
            # 有风牌   bool
            _room.info['haveWind'] = _config['haveWind']
            # 红中赖子 bool
            _room.info['magicRed'] = _config['magicRed']
            # 258 将 bool
            _room.info['j258'] = _config['j258']
            # 过胡只能自摸    bool
            _room.info['onlySelfAfterPass'] = _config['onlySelfAfterPass']
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
            self.room12_conflict(_room.info)
        elif _type == Const.RoomType.RoomType13:
            # Special为True是15人场，Flae 是经典场   类型：bool
            _room.info["special"] = _config["special"]
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            # OutCradType:1为赢家坐庄  12 为红桃3坐庄 15 为黑桃3坐庄  20:随机庄 类型：int
            _room.info["outCradType"] = _config["outCradType"]
            # 开房局数   maxChapterCount  类型：int
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 炸弹类型    四张和AAA ：AAABoom  四张：Boom  四张带一：AAAAndOtherOne   类型:string
            _room.info["boomType"] = _config["boomType"]
            # 炸弹分数 不翻倍：1  一炸封顶 2   二炸封顶 4   三炸封顶： 8   不封顶： -1 类型：int
            _room.info["boomScore"] = _config["boomScore"]
            # 连对个数   最少两对：Double     最少三对：More    类型：string
            _room.info["doubleCount"] = _config["doubleCount"]
            # 算分模式   剩余牌*底分：1      固定算分：-1     类型：int
            _room.info["totalScore"] = _config["totalScore"]
            # 底分  类型：int
            _room.info["baseScore"] = _config["baseScore"]
            # 最大人数
            _room.info["maxPlayersCount"] = _config["maxPlayersCount"]
            # 高级选项

            # 允许三张
            _room.info["haveThree"] = _config["haveThree"]
            # 三带一
            _room.info["threeAndOne"] = _config["threeAndOne"]
            # 三带二
            _room.info["threeAndDouble"] = _config["threeAndDouble"]
            # 三带两张单
            _room.info['threeAndTwoSingle'] = _config['threeAndTwoSingle'] if 'threeAndTwoSingle' in _config else False
            # 炸弹翻倍
            _room.info['bombMultiple'] = _config['bombMultiple'] if 'bombMultiple' in _config else False
            # 报单顶大
            _room.info['singleMax'] = _config['singleMax'] if 'singleMax' in _config else False
            # 放走包赔
            _room.info['loseAll'] = _config['loseAll'] if 'loseAll' in _config else False
            # 四带二 bool
            _room.info["fourAndDouble"] = _config["fourAndDouble"]
            # 四带三 bool
            _room.info["fourAndThree"] = _config["fourAndThree"]
            # 炸弹结算状态
            _room.info["boomSettlementType"] = _config["boomSettlementType"]
            # 炸弹加分
            _room.info["boomScoreSize"] = _config["boomScoreSize"]
            # 炸弹不可拆
            _room.info["bombCannotSeparate"] = _config["bombCannotSeparate"]
            # 出牌时间
            _room.info["autoCompareTime"] = _config["autoCompareTime"]
            # 是否必要
            _room.info["haveCardMustCome"] = _config["haveCardMustCome"]
            _room.info["baseMultiple"] = _config["baseMultiple"] if 'baseMultiple' in _config else 1
        elif _type == Const.RoomType.RoomType14:
            # 胡牌类型 int  0：点炮，1：自摸
            _room.info['huType'] = _config['huType']
            # 有风牌   bool
            _room.info['haveWind'] = _config['haveWind']
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 混子类型   1：带混     0：不带混        2：双混
            _room.info["allpowerfulType"] = _config["allpowerfulType"]
            # 下跑类型
            _room.info["redoubleType"] = _config["redoubleType"]
            # 固定跑倍数
            _room.info["redoubleNum"] = _config["redoubleNum"]
            # 自主跑类型
            _room.info["redoubleWay"] = _config["redoubleWay"]
            # 杠底分
            _room.info["gangDiScore"] = _config["gangDiScore"]
            # 自摸分
            _room.info["ziMoScore"] = _config["ziMoScore"]
            # 点炮分
            _room.info["dianPaoScore"] = _config["dianPaoScore"]
            # 庄家加底
            _room.info["bankerAdd"] = _config["bankerAdd"]
            # 七对加倍
            _room.info["sevenPairSredouble"] = _config["sevenPairSredouble"]
            # 杠上花加倍
            _room.info["bloomSredouble"] = _config["bloomSredouble"]
            # 杠跑
            _room.info["gangRun"] = _config["gangRun"]
            # 抢杠胡
            _room.info["robGangHu"] = _config["robGangHu"]
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
            # self.room12_conflict(_room.info)
            # 双混只能自摸，必带风
            # 带跑时，杠跑才有意义
        elif _type == Const.RoomType.RoomType15:
            # 胡牌类型 int  0：点炮，1：自摸
            _room.info['huType'] = _config['huType']
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            # 有风牌   bool
            _room.info['haveWind'] = _config['haveWind']
            # 杠底分
            _room.info["gangDiScore"] = _config["gangDiScore"]
            # 自摸分
            _room.info["ziMoScore"] = _config["ziMoScore"]
            # 点炮分
            _room.info["dianPaoScore"] = _config["dianPaoScore"]
            # 七对加倍
            _room.info["sevenMultiple"] = _config["sevenMultiple"]
            # 豪华七星对加倍
            _room.info['luxurySevenMultiple'] = _config['luxurySevenMultiple']
            # 杠上花加倍
            _room.info["gangWinMultiple"] = _config["gangWinMultiple"]
            # 清一色倍数
            _room.info['sameColorMultiple'] = _config['sameColorMultiple']
            # 抢杠胡倍数
            _room.info["robGangHuMultiple"] = _config["robGangHuMultiple"]
            # 下飘类型
            _room.info['redoubleType'] = _config['redoubleType']
            # 固定飘倍数
            _room.info['redoubleNum'] = _config['redoubleNum']
            # 自主飘类型
            _room.info['redoubleWay'] = _config['redoubleWay']
            # 庄家加倍
            _room.info['bankerAdd'] = _config['bankerAdd']
            # 混子类型 1：红中癞子，0：没有癞子
            _room.info['wildCardType'] = _config['wildCardType']
            # 258 将 bool
            _room.info['j258'] = _config['j258']
            # 过胡只能自摸    bool
            _room.info['onlySelfAfterPass'] = _config['onlySelfAfterPass']
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 杠跑
            _room.info["gangRun"] = _config["gangRun"]
            # 荒庄不荒杠
            _room.info['notHuangGang'] = _config['notHuangGang']
            # 一炮多响
            _room.info['moreRing'] = _config['moreRing']
            # 点炮包大
            _room.info['compensateMax'] = _config['compensateMax']
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
            # self.room12_conflict(_room.info)
        elif _type == Const.RoomType.RoomType16:
            # 胡牌类型 int  0：点炮，1：自摸
            _room.info['huType'] = _config['huType']
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            # 有风牌   bool
            _room.info['haveWind'] = _config['haveWind']
            # 底分
            _room.info["baseScore"] = _config["baseScore"]
            # 庄家加倍
            _room.info['bankerAdd'] = _config['bankerAdd']
            # 混子类型 1：红中癞子，0：没有癞子
            _room.info['wildCardType'] = _config['wildCardType']
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 一炮多响
            _room.info['moreRing'] = _config['moreRing']
            # 扎马
            _room.info['maCount'] = _config['maCount']
            # 扎马分
            _room.info['zhaMaScore'] = _config['zhaMaScore']
            # 点杠胡包大
            _room.info['dianGangBaoDa'] = _config['dianGangBaoDa']
            # 抢杠胡包大
            _room.info['qiangGangBaoDa'] = _config['qiangGangBaoDa']
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
            # 荒庄不荒杠
            _room.info['notHuangGang'] = _config['notHuangGang']
            # 默认不跑，跳过跑阶段
            _room.info["redoubleType"] = 0
            # 过胡只能自摸    bool
            _room.info['onlySelfAfterPass'] = False
        elif _type == Const.RoomType.RoomType18:
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            # 双嘴    1,门清    2,断门    3,独赢    4,上听    List[int]
            _room.info['doubleMouth'] = _config['doubleMouth']
            # 特殊玩法  1,可点炮胡  2,跑子    3,立张           List[int]
            _room.info['specialRules'] = _config['specialRules']
            # 放水嘴数    int
            _room.info['fangShui'] = _config['fangShui']
            # 限番    int
            _room.info['fanLimit'] = _config['fanLimit']
            # 自摸嘴数  int
            _room.info['ziMoMouth'] = _config['ziMoMouth']
            # 点炮嘴数  int
            _room.info['dianPaoMouth'] = _config['dianPaoMouth']
            # 最大局数  int
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 点杠胡包大/点杠杠开包三家 bool
            _room.info['dianGangBaoDa'] = _config['dianGangBaoDa']
            # 点杠三家付 bool
            _room.info['dianGangAll'] = _config['dianGangAll']
            # 点炮三家付 bool
            _room.info['dianPaoAll'] = _config['dianPaoAll']
            # 抢杠胡包大 bool
            _room.info['qiangGangBaoDa'] = _config['qiangGangBaoDa']
            # 倒计时   int
            _room.info['timeDown'] = _config['timeDown']
            # 荒庄不荒杠 bool
            _room.info['notHuangGang'] = _config['notHuangGang']
            # 没有红中赖子
            _room.info["wildCardType"] = 0
            # 默认开启一炮多响
            _room.info["moreRing"] = True
            # 默认开启过胡只可自摸
            _room.info['onlySelfAfterPass'] = True
        elif _type == Const.RoomType.RoomType21:
            # 胡牌类型 int  0：点炮，1：自摸
            _room.info['huType'] = _config['huType']
            # 有风牌   bool
            _room.info['haveWind'] = _config['haveWind']
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 混子类型   商丘麻将没有混子
            _room.info["allpowerfulType"] = 0
            # 下跑类型
            _room.info["redoubleType"] = _config["redoubleType"]
            # 固定跑倍数
            _room.info["redoubleNum"] = _config["redoubleNum"]
            # 自主跑类型
            _room.info["redoubleWay"] = _config["redoubleWay"]
            # 杠底分
            _room.info["gangDiScore"] = _config["gangDiScore"]
            # 自摸分
            _room.info["ziMoScore"] = _config["ziMoScore"]
            # 点炮分
            _room.info["dianPaoScore"] = _config["dianPaoScore"]
            # 庄家加底
            _room.info["bankerAdd"] = _config["bankerAdd"]
            # 七对加倍
            _room.info["sevenPairSredouble"] = _config["sevenPairSredouble"]
            # 杠上花加倍
            _room.info["bloomSredouble"] = _config["bloomSredouble"]
            # 杠跑
            _room.info["gangRun"] = _config["gangRun"]
            # 抢杠胡
            _room.info["robGangHu"] = _config["robGangHu"]
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
            # 断门
            _room.info['duanMen'] = _config['duanMen']
            # 蹲拉
            _room.info['dunLa'] = _config['dunLa']
            # 花类型
            _room.info['flowerType'] = _config['flowerType']
        elif _type == Const.RoomType.RoomType22:
            # 胡牌类型 int  0：点炮，1：自摸
            _room.info['huType'] = _config['huType']
            # 有风牌   bool
            _room.info['haveWind'] = _config['haveWind']
            # 少人模式
            _room.info["fewPersonPattern"] = _config["fewPersonPattern"]
            # 最大局数
            _room.info["maxChapterCount"] = _config["maxChapterCount"]
            # 混子类型   1：带混     0：不带混        2：双混
            _room.info["allpowerfulType"] = _config["allpowerfulType"]
            # 下跑类型
            _room.info["redoubleType"] = _config["redoubleType"]
            # 固定跑倍数
            _room.info["redoubleNum"] = _config["redoubleNum"]
            # 自主跑类型
            _room.info["redoubleWay"] = _config["redoubleWay"]
            # 杠底分
            _room.info["gangDiScore"] = _config["gangDiScore"]
            # 自摸分
            _room.info["ziMoScore"] = _config["ziMoScore"]
            # 点炮分
            _room.info["dianPaoScore"] = _config["dianPaoScore"]
            # 庄家加底
            _room.info["bankerAdd"] = _config["bankerAdd"]
            # 七对可胡
            _room.info["sevenPairSredouble"] = _config["sevenPairSredouble"]
            # 杠上花加倍 _config["bloomSredouble"]
            _room.info["bloomSredouble"] = False
            # 杠跑
            _room.info["gangRun"] = _config["gangRun"]
            # 抢杠胡
            _room.info["robGangHu"] = _config["robGangHu"]
            # 倒计时
            _room.info['timeDown'] = _config['timeDown']
            # 倍数
            _room.info['multiple'] = _config['multiple']

        if _roomType == "card":
            # todo:其他游戏类型开房门槛
            self.rooms[_type].roominfos[_roomType][_room.info["roomId"]] = _room
            # 钻石消耗存储
        # 冠名赛比赛分场
        elif _roomType == "gameCoin":
            if 'roomName' in _config:
                _room.info['roomName'] = _config['roomName']
            if 'canNotDisbandOnPlay' in _config:
                _room.info["canNotDisbandOnPlay"] = _config["canNotDisbandOnPlay"]
            else:
                _room.info["canNotDisbandOnPlay"] = False
            if 'hideOtherGameCoin' in _config:
                _room.info['hideOtherGameCoin'] = _config['hideOtherGameCoin']
            else:
                _room.info['hideOtherGameCoin'] = False
            if 'readyGoldLimit' in _config:
                _room.info['readyGoldLimit'] = _config['readyGoldLimit']
            else:
                _room.info['readyGoldLimit'] = 0
            # 如果没开比赛分功能，中途无论多少分都能继续
            if _room.info['gameLevel'] == 0:
                _room.info['readyGoldLimit'] = -99999999
                _room.info['hideOtherGameCoin'] = False
                _room.info["canNotDisbandOnPlay"] = False
            # 比赛场只有房主支付
            _config['payType'] = Const.PayType.RoomCreator
            # 房主支付
            _room.info['payType'] = _config['payType']
            # 冠名赛 Id
            _room.info["teaHouseId"] = _config["teaHouseId"]
            # 大赢家抽水
            _room.info["winnerBilling"] = _config["winnerBilling"]
            # 其他玩家抽水
            _room.info["otherBilling"] = _config["otherBilling"]
            # 是否是匿名房间
            _room.info["anonymity"] = _config["anonymity"]
            # 超出收费标准
            _room.info["overBilling"] = _config["overBilling"]
            # 超出收费费额
            _room.info["overBillingValue"] = _config["overBillingValue"]
            # 福卡限制
            _room.info['fokaLevel'] = _config['fokaLevel']
            # 大赢家抽奖区间
            _room.info["winnerRaffleInterval"] = _config["winnerRaffleInterval"]
            _room.info["allRaffleInterval"] = _config["allRaffleInterval"]
            tea_house_entity = tea_house_manager().get_tea_house_with_id(_config['teaHouseId'])
            _room.info['gameCoinSwitch'] = tea_house_entity.gameCoinSwitch
            self.rooms[_type].roominfos[_roomType][_room.info["roomId"]] = _room
        # 冠名赛普通场
        elif _roomType == 'normalGameCoin':
            _room.info['roomName'] = _config['roomName']
            # 冠名赛只有房主支付
            _config['payType'] = Const.PayType.RoomCreator
            # 冠名赛 Id
            _room.info["teaHouseId"] = _config["teaHouseId"]
            # 是否是匿名房间
            _room.info["anonymity"] = _config["anonymity"]
            self.rooms[_type].roominfos[_roomType][_room.info["roomId"]] = _room
        # 金币场
        elif _roomType == 'gold' or _roomType == 'challenge':
            # 是否是匿名房间
            _room.info["anonymity"] = _config["anonymity"]
            self.rooms[_type].roominfos[_roomType][_room.info["roomId"]] = _room

        # 通过房间信息获取房间钻石消耗
        self.room_card_consume_init(_room)
        # 如果钻石消耗开关关闭，钻石消耗量为0
        if not self.need_consume_card(_room.info):
            _room.info['roomCardConsume'] = 0

        # 判断创建房间钻石是否
        room_card_enough = self.room_card_enough_check(_room, _account, isCreate=True)
        if not room_card_enough:
            if _account.hasClient:
                _account.call_client_func("CreateRoomFail", ["钻石不足"])
            # 销毁无用的房间
            self.rooms[_type].roominfos[_roomType].pop(_room.info["roomId"])
            _room.destroy()
            return

        # 判断是否满足gps条件
        gps_enough = self.room_gps_enough(_room, _account)
        if not gps_enough:
            if _account.hasClient:
                _account.call_client_func("CreateRoomFail", ["未开启GPS定位，无法进入"])
            # 销毁无用的房间
            self.rooms[_type].roominfos[_roomType].pop(_room.info["roomId"])
            _room.destroy()
            return

        # 元宝是否足够
        room_card_enough = self.goldIngot_enough_check(_room, _account, isCreate=True)
        if not room_card_enough:
            if _account.hasClient:
                _account.call_client_func("CreateRoomFail", ["元宝不足"])
            # 销毁无用的房间
            self.rooms[_type].roominfos[_roomType].pop(_room.info["roomId"])
            _room.destroy()
            return

        # lucky_card_enough = self.lucky_card_enough_check(_room, _account)
        # if not lucky_card_enough:
        #     if _account.hasClient:
        #         _account.call_client_func("CreateRoomFail", ["福卡不足"])
        #     # 销毁无用的房间
        #     _room.destroy()
        #     return

        # 判断比赛用的金币是否足够
        if _room.info['roomType'] in ['card', 'normalGameCoin']:
            if _account.gold < _room.info['gameLevel']:
                if _account.hasClient:
                    _account.call_client_func("CreateRoomFail", ["金币不足"])
                # 销毁无用的房间
                self.rooms[_type].roominfos[_roomType].pop(_room.info["roomId"])
                _room.destroy()
                return

        _room.create_space(self.create_room_success_callback)
        _room.initToDB()

        def func(boolean, entity):
            if boolean:
                _account.writeRooms(entity)

        _room.writeToDB(func)

        return _room

    def room_card_consume_init(self, room):
        """
        通过游戏类型和房间类型和支付方式获取当前房间的钻石消耗
        :param room: 房间的实体对象
        :return:
        """
        # 挑战赛场扣房卡
        if room.info['roomType'] == 'challenge':
            room.info['roomCardConsume'] = \
                Const.ServerGameConfigJson.config_json["ChallengeArea"][str(room.info['level'])]["roomRate"]
            return
        # 金币场房卡消耗为0
        if room.info['level'] != 0:
            room.info['roomCardConsume'] = 0
            return
        # 游戏类型
        game_type = room.info['type']
        # 房间类型
        room_type = room.info['roomType']
        # 获取该游戏的配置
        game_config_json = Const.GameConfigJson.config_json[game_type]
        DEBUG_MSG('room_card_consume_init:game_type:%s,room_type:%s,game_config:%s' %
                  (game_type, room_type, game_config_json))
        # AA支付和钻石支付判断,0:房主支付，1:AA支付
        consume_type = room.info['payType']
        # 局数和钻石赋值
        # 骨牌牌九钻石消耗规则
        if game_type == Const.RoomType.RoomType8:
            if room.info['pot'] and room.info['onePersonOnePot']:
                # 通过配置文件获取一人一锅钻石消耗量
                room_card_consume = game_config_json[room_type]['onePersonOnePotRoomCardConsume'][consume_type]
                DEBUG_MSG('consume_type%s' % consume_type)
                room.info['roomCardConsume'] = room_card_consume
                return
            elif room.info['pot'] and not room.info['onePersonOnePot']:
                # 通过配置文件获取加锅钻石消耗量
                room_card_consume = game_config_json[room_type]['potModeRoomCardConsume'][consume_type]
                room.info['roomCardConsume'] = room_card_consume
                return
            # 不加锅场
            else:
                # 通过配置文件获取不加锅房间钻石消耗量
                max_chapter = str(room.info['maxChapterCount'])
                room_card_consume = game_config_json[room_type]['chapterLimitAndRoomCard'][max_chapter][consume_type]
                room.info['roomCardConsume'] = room_card_consume
                return
        # 洛阳牌九规则
        elif game_type == Const.RoomType.RoomType11:
            if room.info['pot'] and room.info['onePersonOnePot']:
                # 通过配置文件获取一人一锅钻石消耗量
                room_card_consume = game_config_json[room_type]['onePersonOnePotRoomCardConsume'][consume_type]
                DEBUG_MSG('consume_type%s' % consume_type)
                room.info['roomCardConsume'] = room_card_consume
                return
            elif room.info['pot'] and not room.info['onePersonOnePot']:
                # 通过配置文件获取加锅钻石消耗量
                room_card_consume = game_config_json[room_type]['potModeRoomCardConsume'][consume_type]
                room.info['roomCardConsume'] = room_card_consume
                return
            # 不加锅场
            else:
                # 通过配置文件获取不加锅房间钻石消耗量
                max_chapter = str(room.info['maxChapterCount'])
                room_card_consume = game_config_json[room_type]['chapterLimitAndRoomCard'][max_chapter][consume_type]
                room.info['roomCardConsume'] = room_card_consume
                return
        # 八叉钻石消耗规则
        elif game_type == Const.RoomType.RoomType10:
            max_chapter = str(room.info['maxChapterCount'])
            # 通过配置文件获取加锅锅钻石消耗量
            room_card_consume = game_config_json[room_type]['chapterLimitAndRoomCard'][max_chapter][consume_type]
            room.info['roomCardConsume'] = room_card_consume
            return
        # 其他房间统一通过局数消耗钻石
        elif game_type == Const.RoomType.RoomType1:
            max_chapter = str(room.info['maxChapterCount'])
            # 通过配置文件获取加锅锅钻石消耗量
            room_card_consume = game_config_json[room_type]['chapterLimitAndRoomCard'][max_chapter][consume_type]
            room.info['roomCardConsume'] = room_card_consume
            return
        elif game_type == Const.RoomType.RoomType4:
            max_chapter = str(room.info['maxChapterCount'])
            # 通过配置文件获取加锅锅钻石消耗量
            room_card_consume = game_config_json[room_type]['chapterLimitAndRoomCard'][max_chapter][consume_type]
            room.info['roomCardConsume'] = room_card_consume
            return
        else:
            # 获取该游戏的配置
            # 通过配置文件获取钻石消耗量
            max_chapter = str(room.info['maxChapterCount'])
            room_card_consume = game_config_json[room_type]['chapterLimitAndRoomCard'][max_chapter][consume_type]
            room.info['roomCardConsume'] = room_card_consume
            return

    def room_gps_enough(self, room, account):
        """
        检测我玩家是否满足gps定位
        :param room:
        :param account:
        :return:
        """
        if room.info["roomType"] == "card":
            if 'gps' in room.info and room.info['gps']:
                if not account.gpsLocation:
                    return False
        return True

    def room_card_enough_check(self, room, account, isCreate=False):
        """
        通过房间信息和玩家信息判断该玩家钻石是否足以加入房间
        房主支付：
            只需在创建时判断房主钻石是否足够
        AA支付：
            钻石场:
                代开：房主不一定会进入房间，所以创建时不用判断创建者钻石
                普通：房主一定会进入房间，所以创建时判断钻石是否足够
            比赛冠名赛场：
                房主不一定会进入房间，所以创建时不用判断创建者钻石
            普通冠名赛场：
                房主不一定会进入房间，所以创建时不用判断创建者钻石
        :param isCreate:是否是创建房间
        :param room:房间实体
        :param account:用户实体
        :return:
        """
        # 如果是钻石场并且钻石场钻石消耗开启
        if room.info["roomType"] == "card" and self.need_consume_card(room.info):
            # 如果是房主支付，创建房间，只在创建时判断房主钻石是否足够
            if room.info['payType'] == Const.PayType.RoomCreator:
                DEBUG_MSG('Const.PayType.RoomCreator:%s' % Const.PayType.RoomCreator)
                if isCreate:
                    DEBUG_MSG('isCreate:%s' % isCreate)
                    if account.roomCard < room.info['roomCardConsume']:
                        DEBUG_MSG('account.roomCard:%s' % account.roomCard)
                        return False
            # 如果是AA支付
            elif room.info['payType'] == Const.PayType.AA:
                # AA支付，代开房间，加入时判断钻石是否足够
                if "substitute" in room.info.keys() and room.info["substitute"]:
                    if not isCreate:
                        if account.roomCard < room.info['roomCardConsume']:
                            return False
                # AA支付，非代开房间，加入时、创建时判断钻石是否足够
                else:
                    if account.roomCard < room.info['roomCardConsume']:
                        return False

        # 如果是比赛分场并且比赛分场钻石消耗开启
        elif room.info["roomType"] == "gameCoin" and self.need_consume_card(room.info):
            # 房主支付，创建房间时判断房主钻石是否足够
            if room.info['payType'] == Const.PayType.RoomCreator:
                if isCreate:
                    if account.roomCard < room.info['roomCardConsume']:
                        return False
            # AA支付，加入时判断钻石是否足够
            elif room.info['payType'] == Const.PayType.AA:
                if not isCreate:
                    if account.roomCard < room.info['roomCardConsume']:
                        return False

        # 如果是普通比赛分场并且比赛分场钻石消耗开启
        elif room.info["roomType"] == "normalGameCoin" and self.need_consume_card(room.info):
            # 房主支付，创建房间时判断房主钻石是否足够
            if room.info['payType'] == Const.PayType.RoomCreator:
                if isCreate:
                    if account.roomCard < room.info['roomCardConsume']:
                        return False
            # AA支付，加入时判断钻石是否足够
            elif room.info['payType'] == Const.PayType.AA:
                if not isCreate:
                    if account.roomCard < room.info['roomCardConsume']:
                        return False
        # elif room.info['roomType'] == 'challenge' and self.need_consume_card(room.info):
        #     if account.roomCard < room.info['roomCardConsume']:
        #         return False
        # 金币场不消耗钻石
        elif room.info['roomType'] == 'gold':
            pass

        return True

    def goldIngot_enough_check(self, room, account, isCreate=False):
        if room.info['roomType'] == 'challenge' and self.need_consume_card(room.info):
            if account.goldIngot < room.info['roomCardConsume']:
                return False
        return True

    def lucky_card_enough_check(self, room, account):
        """
        福卡门槛判断
        :param room:
        :param account:
        :return:
        """
        if 'teaHouseId' not in room.info:
            return True
        tea_house_id = room.info['teaHouseId']
        tea_house_entity = tea_house_manager().get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            # 如果没开启福卡开关，福卡默认足够
            if not tea_house_entity.luckyCardSwitch:
                return True
            player = tea_house_entity.get_tea_house_player(account.userId)
            return player.lucky_card >= room.info['fokaLevel']
        return True

    def game_coin_enough_check(self, room, account):
        """
        判断比赛比是否足够
        :param room:
        :param account:
        :return:
        """
        tea_house_id = room.info['teaHouseId']
        tea_house_entity = tea_house_manager().get_tea_house_with_id(tea_house_id)
        if tea_house_entity:
            # 如果没开启比赛币开关，比赛币默认足够
            if not tea_house_entity.gameCoinSwitch:
                return True
            player = tea_house_entity.get_tea_house_player(account.userId)
            if player.game_coin < room.info['readyGoldLimit']:
                return False
            return player.game_coin >= room.info['gameLevel']
        return True

    def join_card_room(self, _account, _roomId):
        """
        加入钻石场房间
        :param _account:玩家实体
        :param _roomId:房间id
        :return:
        """
        _rooms = {}
        for __type in self.rooms.values():
            for room_id, room_entity in __type.roominfos["card"].items():
                _rooms[room_id] = room_entity

        # 1  加入房间成功的回调函数  account.py的定义函数
        def join_room_success_callback():
            # _room.cell.baseToCell({"func": "onEnter", "id": _accountEntity.id})
            # 如果房间不存在，不再加入房间
            if not _room.cell:
                return
            _account.call_client_func("join_room_success", [_room.info["type"], "card", _roomId])
            _account.writeRooms(_room)

        def join_room_failed_callback():
            _account.call_client_func("join_room_failed", ['', "card", _roomId])

        _room = None
        if _roomId in _rooms.keys():
            _room = _rooms[_roomId]
        if _room is None:
            _account.call_client_func("Notice", ["房间号不存在"])
            join_room_failed_callback()
            return
        if _room.total_settlement_ed:
            _account.call_client_func("Notice", ["房间牌局已结束"])
            return

        if 'gps' in _room.info and _room.info['gps'] and not _account.gpsLocation:
            _account.call_client_func("Notice", ["未开启GPS定位，无法进入"])
            return

        # 如果房间已开始
        if _room.info["started"]:
            # 该游戏
            if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                _account.call_client_func("Notice", ["加入失败,房间牌局已开始"])
                return

            if 'witness' in _room.info and not _room.info['witness']:
                _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                return
        # 如果房间未开始
        else:
            # 如果房间人已满，加入者为观战玩家
            if len(_room.info["playerInGame"]) >= _room.info["maxPlayersCount"]:
                if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                    _account.call_client_func("Notice", ["加入失败,房间人已满"])
                    return

                if 'witness' in _room.info and not _room.info['witness']:
                    _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                    return
            # 如果房间人未满
            else:
                # 判断加入游戏者金币是否足够
                if _account.gold < _room.info["gameLevel"]:
                    if _account.hasClient:
                        _account.call_client_func("Notice", ["金币不足"])
                    return

        # 如果是AA支付先判断钻石是否足够
        if _room.info['payType'] == Const.PayType.AA:
            # 判断创建房间钻石是否
            room_card_enough = self.room_card_enough_check(_room, _account)
            # 不够，返回
            if not room_card_enough:
                if _account.hasClient:
                    _account.call_client_func("Notice", ["钻石不足"])
                return

        if "hasPreventCheat" in _room.info:
            if _room.info["hasPreventCheat"]:
                if _account not in _room.entities.values():
                    for k, v in _room.entities.items():
                        if _account.latitude and _account.longitude and v.longitude and v.latitude:
                            distance = Util.getdistance(_account.longitude, _account.latitude,
                                                        v.longitude, v.latitude)
                            if distance * 1000 < 100:
                                _account.call_client_func("Notice", ["加入失败,距离过近"])
                                join_room_failed_callback()
                                return
        _room.login_to_room(_account, join_room_success_callback)

    def join_challenge_room(self, _account, _roomId):
        """
        加入挑战赛房间
        :param _account:玩家实体
        :param _roomId:房间id
        :return:
        """
        _rooms = {}
        for type_rooms in self.rooms.values():
            for room_id, room_entity in type_rooms.roominfos["challenge"].items():
                _rooms[room_id] = room_entity

        # 1  加入房间成功的回调函数  account.py的定义函数
        def join_room_success_callback():
            # _room.cell.baseToCell({"func": "onEnter", "id": _accountEntity.id})
            # 如果房间不存在，不再加入房间
            if not _room.cell:
                return
            _account.call_client_func("join_room_success", [_room.info["type"], "card", _roomId])
            _account.writeRooms(_room)

        def join_room_failed_callback():
            _account.call_client_func("join_room_failed", ['', "card", _roomId])

        _room = None
        if _roomId in _rooms.keys():
            _room = _rooms[_roomId]
        if _room is None:
            _account.call_client_func("Notice", ["房间号不存在"])
            join_room_failed_callback()
            return
        if _room.total_settlement_ed:
            _account.call_client_func("Notice", ["房间牌局已结束"])
            return

        # 如果房间已开始
        if _room.info["started"]:
            # 该游戏
            if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                _account.call_client_func("Notice", ["加入失败,房间牌局已开始"])
                return

            if 'witness' in _room.info and not _room.info['witness']:
                _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                return
        # 如果房间未开始
        else:
            # 如果房间人已满，加入者为观战玩家
            if len(_room.info["playerInGame"]) >= _room.info["maxPlayersCount"]:
                if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                    _account.call_client_func("Notice", ["加入失败,房间人已满"])
                    return

                if 'witness' in _room.info and not _room.info['witness']:
                    _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                    return
            # 如果房间人未满
            else:
                # 判断加入游戏者金币是否足够
                if _account.gold < _room.info["gameLevel"]:
                    if _account.hasClient:
                        _account.call_client_func("Notice", ["金币不足"])
                    return

        # # 如果是AA支付先判断钻石是否足够
        # if _room.info['payType'] == Const.PayType.AA:
        #     # 判断创建房间钻石是否
        #     room_card_enough = self.room_card_enough_check(_room, _account)
        #     # 不够，返回
        #     if not room_card_enough:
        #         if _account.hasClient:
        #             _account.call_client_func("Notice", ["钻石不足"])
        #         return
        #
        # if "hasPreventCheat" in _room.info:
        #     if _room.info["hasPreventCheat"]:
        #         if _account not in _room.entities.values():
        #             for k, v in _room.entities.items():
        #                 if _account.latitude and _account.longitude and v.longitude and v.latitude:
        #                     distance = Util.getdistance(_account.longitude, _account.latitude,
        #                                                 v.longitude, v.latitude)
        #                     if distance * 1000 < 100:
        #                         _account.call_client_func("Notice", ["加入失败,距离过近"])
        #                         join_room_failed_callback()
        #                         return
        _room.login_to_room(_account, join_room_success_callback)

    # 1 加入冠名赛房间
    def join_game_coin_room(self, _account, _type, _roomId, anonymity=False, quick_join=False, teaHouseId=-1):
        """
        加入冠名赛房间
        :param teaHouseId: 冠名赛id号
        :param quick_join: 快速加入标识
        :param anonymity: 匿名房间标识
        :param _account:加入者实体
        :param _type:房间类型
        :param _roomId:房间id
        :return:
        """
        _rooms = self.rooms[_type].roominfos["gameCoin"]

        def join_room_success_callback():
            # _room.cell.baseToCell({"func": "onEnter", "id": _accountEntity.id})
            # 如果房间不存在，不再加入房间
            if not _room.cell:
                DEBUG_MSG('join_room_failed not _room.cell roomId%s' % _roomId)
                return
            _account.call_client_func("join_room_success", [_type, "gameCoin", _roomId])
            _account.writeRooms(_room)

        def join_room_failed_callback():
            _account.call_client_func("join_room_failed", [_type, "gameCoin", _roomId])

        _room = None
        # 快速加入
        if quick_join:
            tea_house_entity = tea_house_manager().get_tea_house_with_id(teaHouseId)
            can_quick_join_rooms = []
            room_max_player_count = 0
            for room in _rooms.values():
                if not tea_house_entity:
                    continue
                if "teaHouseId" not in room.info:
                    continue
                if room.info["teaHouseId"] != teaHouseId:
                    continue
                if not tea_house_manager().player_in_tea_house(_account.databaseID, room.info["teaHouseId"]):
                    continue
                if not self.game_coin_enough_check(room, _account):
                    continue
                # 快速加入，房间已开始不能加入观战
                if room.info["started"]:
                    continue
                # 房间没有空位,快速加入无法观战
                if len(room.info["playerInGame"]) >= room.info["maxPlayersCount"]:
                    continue
                if teaHouseId != room.info["teaHouseId"]:
                    continue
                if "anonymity" in room.info:
                    if room.info["anonymity"] != anonymity:
                        continue
                user_ids = list(room.entities.keys())
                if user_ids:
                    if tea_house_entity.is_exclude_same_room(_account.id, user_ids):
                        continue
                # 有合适的房间就加入可以加入的列表
                can_quick_join_rooms.append(room)
                # 找到人数最多的房间
                if len(room.info["playerInGame"]) > room_max_player_count:
                    room_max_player_count = len(room.info["playerInGame"])
            for room in can_quick_join_rooms:
                if len(room.info["playerInGame"]) == room_max_player_count:
                    _room = room
                    break
            if _room:
                DEBUG_MSG("room info:%s" % _room.info)
                _room.login_to_room(_account, join_room_success_callback)
                return
            else:
                # 没有合适的房间提示客户端
                _account.call_client_func("Notice", ["比赛分不足或没有合适的房间"])
                return
        if _roomId in _rooms.keys():
            _room = _rooms[_roomId]
        for r in _rooms.values():
            if int(r.info["roomId"]) == int(_roomId):
                _room = r
        if _room is None:
            _account.call_client_func("Notice", ["房间不存在"])
            join_room_failed_callback()
            return

        if _room.total_settlement_ed:
            _account.call_client_func("Notice", ["房间牌局已结束"])
            return

        if 'gps' in _room.info and _room.info['gps'] and not _account.gpsLocation:
            _account.call_client_func("Notice", ["未开启GPS定位，无法进入"])
            return

        # 如果房间已开始
        if _room.info["started"]:
            # 该游戏
            if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                _account.call_client_func("Notice", ["加入失败,房间牌局已开始"])
                return

            if 'witness' in _room.info and not _room.info['witness']:
                _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                return
        # 如果房间未开始
        else:
            if 'teaHouseId' in _room.info.keys() and _room.info['teaHouseId'] != -1:
                tea_house_entity = tea_house_manager().get_tea_house_with_id(teaHouseId)
                if tea_house_entity and _room.info["teaHouseId"] == teaHouseId:
                    user_ids = list(_room.entities.keys())
                    if user_ids:
                        if tea_house_entity.is_exclude_same_room(_account.id, user_ids):
                            _account.call_client_func("Notice", ["加入失败,不能同桌"])
                            return

            # 如果房间人已满，加入者为观战玩家
            if len(_room.info["playerInGame"]) >= _room.info["maxPlayersCount"]:
                if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                    _account.call_client_func("Notice", ["加入失败,房间人已满"])
                    return

                if 'witness' in _room.info and not _room.info['witness']:
                    _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                    return
            # 如果房间人未满
            else:
                game_coin_enough = self.game_coin_enough_check(_room, _account)
                if not game_coin_enough:
                    if _account.hasClient:
                        _account.call_client_func("Notice", ["比赛分不足"])
                    return

        # 如果是AA支付先判断加入游戏者钻石是否足够
        if _room.info['payType'] == Const.PayType.AA:
            # 判断创建房间钻石是否足够
            room_card_enough = self.room_card_enough_check(_room, _account)
            # 不够，返回
            if not room_card_enough:
                if _account.hasClient:
                    _account.call_client_func("Notice", ["钻石不足"])
                return

        lucky_card_enough = self.lucky_card_enough_check(_room, _account)
        if not lucky_card_enough:
            if _account.hasClient:
                _account.call_client_func("CreateRoomFail", ["福卡不足"])
            # # 销毁无用的房间
            # _room.destroy()
            return

        if "gps" in _room.info:
            if _room.info["gps"]:
                if _account not in _room.entities.values():
                    for k, v in _room.entities.items():
                        if _account.latitude and _account.longitude and v.longitude and v.latitude:
                            distance = Util.getdistance(_account.longitude, _account.latitude,
                                                        v.longitude, v.latitude)
                            if distance * 1000 < 50:
                                _account.call_client_func("Notice", ["距离过近,禁止入内"])
                                join_room_failed_callback()
                                return

        if 'teaHouseId' in _room.info.keys() and _room.info['teaHouseId'] != -1:
            tea_house_entity = tea_house_manager().get_tea_house_with_id(teaHouseId)
            # 如果进入的是母桌，创建一个和母桌相同的房间进入
            if tea_house_entity and tea_house_entity.is_base_room(_roomId):
                # 创建母桌相同房间并进入
                tea_house_entity.create_and_join_like_base_room(_account.databaseID, _roomId)
                return
        #
        DEBUG_MSG('join_game_coin_room before login_to_room')
        _room.login_to_room(_account, join_room_success_callback)

    def join_normal_game_coin_room(self, _account, _type, _roomId, anonymity=False, quick_join=False,
                                   teaHouseId=-1):
        """
        加入普通冠名赛房间
        :param teaHouseId: 冠名赛id号
        :param quick_join: 快速加入标识
        :param anonymity: 匿名房间标识
        :param _account:加入者实体
        :param _type:房间类型
        :param _roomId:房间id
        :return:
        """
        _rooms = self.rooms[_type].roominfos["normalGameCoin"]

        def join_room_success_callback():
            # _room.cell.baseToCell({"func": "onEnter", "id": _accountEntity.id})
            # 如果房间不存在，不再加入房间
            if not _room.cell:
                return
            _account.call_client_func("join_room_success", [_type, "normalGameCoin", _roomId])
            _account.writeRooms(_room)

        def join_room_failed_callback():
            _account.call_client_func("join_room_failed", [_type, "normalGameCoin", _roomId])

        _room = None
        # 快速加入
        if quick_join:
            can_quick_join_rooms = []
            room_max_player_count = 0
            for room in _rooms.values():
                if 'teaHouseId' in room.info.keys() and room.info['teaHouseId'] != -1:
                    tea_house_entity = tea_house_manager().get_tea_house_with_id(teaHouseId)
                    if not tea_house_entity:
                        continue
                    if room.info["teaHouseId"] != teaHouseId:
                        continue
                    if not tea_house_manager().player_in_tea_house(_account.databaseID,
                                                                   room.info["teaHouseId"]):
                        continue
                    user_ids = list(_room.entities.keys())
                    if user_ids:
                        if tea_house_entity.is_exclude_same_room(_account.id, user_ids):
                            continue
                elif 'level' in room.info.keys() and room.info['level'] != 0:
                    gold_session = gold_session_manager().get_gold_session_with_level(room.info['level'])
                    if not gold_session:
                        continue
                    if room.info['level'] != gold_session.sessionLevel:
                        continue
                    if not gold_session_manager().player_in_gold_session(_account.databaseID, room.info['level']):
                        continue

                # 快速加入，房间已开始不能加入观战
                if room.info["started"]:
                    continue
                # 房间没有空位,快速加入无法观战
                if len(room.info["playerInGame"]) >= room.info["maxPlayersCount"]:
                    continue
                if "anonymity" in room.info:
                    if room.info["anonymity"] != anonymity:
                        continue
                # 有合适的房间就加入可以加入的列表
                can_quick_join_rooms.append(room)
                # 找到人数最多的房间
                if len(room.info["playerInGame"]) > room_max_player_count:
                    room_max_player_count = len(room.info["playerInGame"])
            for room in can_quick_join_rooms:
                if len(room.info["playerInGame"]) == room_max_player_count:
                    _room = room
                    break
            if _room:
                DEBUG_MSG("room info:%s" % _room.info)
                _room.login_to_room(_account, join_room_success_callback)
                return
            else:
                # 没有合适的房间提示客户端
                _account.call_client_func("Notice", ["没有合适的房间"])
                return
        if _roomId in _rooms.keys():
            _room = _rooms[_roomId]
        if _room is None:
            _account.call_client_func("Notice", ["房间不存在"])
            join_room_failed_callback()
            return

        if _room.total_settlement_ed:
            _account.call_client_func("Notice", ["房间牌局已结束"])
            return

        if 'gps' in _room.info and _room.info['gps'] and not _account.gpsLocation:
            _account.call_client_func("Notice", ["未开启GPS定位，无法进入"])
            return

        # 如果房间已开始
        if _room.info["started"]:
            if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                _account.call_client_func("Notice", ["加入失败,房间牌局已开始"])
                return

            if 'witness' in _room.info and not _room.info['witness']:
                _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                return
        # 如果房间未开始
        else:

            if 'teaHouseId' in _room.info.keys() and _room.info['teaHouseId'] != -1:
                tea_house_entity = tea_house_manager().get_tea_house_with_id(teaHouseId)
                if tea_house_entity and _room.info["teaHouseId"] == teaHouseId:
                    user_ids = list(_room.entities.keys())
                    if user_ids:
                        if tea_house_entity.is_exclude_same_room(_account.id, user_ids):
                            _account.call_client_func("Notice", ["加入失败,不能同桌"])
                            return

            # 如果房间人已满，加入者为观战玩家
            if len(_room.info["playerInGame"]) >= _room.info["maxPlayersCount"]:
                if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                    _account.call_client_func("Notice", ["加入失败,房间人已满"])
                    return

                if 'witness' in _room.info and not _room.info['witness']:
                    _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                    return
            # 如果房间人未满
            else:
                # 判断加入游戏者金币是否足够
                if _account.gold < _room.info["gameLevel"]:
                    if _account.hasClient:
                        _account.call_client_func("Notice", ["金币不足"])
                    return
        # 如果是AA支付先判断钻石是否足够
        if _room.info['payType'] == Const.PayType.AA:
            # 判断创建房间钻石是否
            room_card_enough = self.room_card_enough_check(_room, _account)
            # 不够，返回
            if not room_card_enough:
                if _account.hasClient:
                    _account.call_client_func("Notice", ["钻石不足"])
                return

        if "gps" in _room.info:
            if _room.info["gps"]:
                if _account not in _room.entities.values():
                    for k, v in _room.entities.items():
                        if _account.latitude and _account.longitude and v.longitude and v.latitude:
                            distance = Util.getdistance(_account.longitude, _account.latitude,
                                                        v.longitude, v.latitude)
                            if distance * 1000 < 50:
                                _account.call_client_func("Notice", ["距离过近,禁止入内"])
                                join_room_failed_callback()
                                return

        if 'teaHouseId' in _room.info.keys() and _room.info['teaHouseId'] != -1:
            tea_house_entity = tea_house_manager().get_tea_house_with_id(teaHouseId)
            # 如果进入的是母桌，创建一个和母桌相同的房间进入
            if tea_house_entity and tea_house_entity.is_base_room(_roomId):
                # 创建母桌相同房间并进入
                tea_house_entity.create_and_join_like_base_room(_account.databaseID, _roomId)
                return
        _room.login_to_room(_account, join_room_success_callback)

    def join_gold_room(self, _account, _type, _roomId, anonymity=False, quick_join=False):
        """
        加入普通冠名赛房间
        :param quick_join: 快速加入标识
        :param anonymity: 匿名房间标识
        :param _account:加入者实体
        :param _type:房间类型
        :param _roomId:房间id
        :return:
        """
        _rooms = self.rooms[_type].roominfos["gold"]

        def join_room_success_callback():
            # _room.cell.baseToCell({"func": "onEnter", "id": _accountEntity.id})
            # 如果房间不存在，不再加入房间
            if not _room.cell:
                return
            _account.call_client_func("join_room_success", [_type, "gold", _roomId])
            _account.writeRooms(_room)

        def join_room_failed_callback():
            _account.call_client_func("join_room_failed", [_type, "gold", _roomId])

        _room = None
        # 快速加入
        if quick_join:
            can_quick_join_rooms = []
            room_max_player_count = 0
            for room in _rooms.values():
                if 'level' in room.info.keys() and room.info['level'] != 0:
                    gold_session = gold_session_manager().get_gold_session_with_level(room.info['level'])
                    if not gold_session:
                        continue
                    if room.info['level'] != gold_session.sessionLevel:
                        continue
                    if not gold_session_manager().player_in_gold_session(_account.databaseID, room.info['level']):
                        continue

                # 快速加入，房间已开始不能加入观战
                if room.info["started"]:
                    continue
                # 房间没有空位,快速加入无法观战
                if len(room.info["playerInGame"]) >= room.info["maxPlayersCount"]:
                    continue
                if "anonymity" in room.info:
                    if room.info["anonymity"] != anonymity:
                        continue
                # 有合适的房间就加入可以加入的列表
                can_quick_join_rooms.append(room)
                # 找到人数最多的房间
                if len(room.info["playerInGame"]) > room_max_player_count:
                    room_max_player_count = len(room.info["playerInGame"])
            for room in can_quick_join_rooms:
                if len(room.info["playerInGame"]) == room_max_player_count:
                    _room = room
                    break
            if _room:
                DEBUG_MSG("room info:%s" % _room.info)
                _room.login_to_room(_account, join_room_success_callback)
                return
            else:
                # 没有合适的房间提示客户端
                _account.call_client_func("Notice", ["没有合适的房间"])
                return
        if _roomId in _rooms.keys():
            _room = _rooms[_roomId]
        if _room is None:
            _account.call_client_func("Notice", ["房间不存在"])
            join_room_failed_callback()
            return

        if _room.total_settlement_ed:
            _account.call_client_func("Notice", ["房间牌局已结束"])
            return

        # 如果房间已开始
        if _room.info["started"]:
            if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                _account.call_client_func("Notice", ["加入失败,房间牌局已开始"])
                return

            if 'witness' in _room.info and not _room.info['witness']:
                _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                return
        # 如果房间未开始
        else:
            # 如果房间人已满，加入者为观战玩家
            if len(_room.info["playerInGame"]) >= _room.info["maxPlayersCount"]:
                if _room.info["type"] not in Const.CanWatchGame.can_watch_game:
                    _account.call_client_func("Notice", ["加入失败,房间人已满"])
                    return

                if 'witness' in _room.info and not _room.info['witness']:
                    _account.call_client_func("Notice", ["加入失败,房间不允许观战"])
                    return
            # 如果房间人未满
            else:
                # 判断加入游戏者金币是否足够
                if _account.gold < _room.info["gameLevel"]:
                    if _account.hasClient:
                        _account.call_client_func("Notice", ["金币不足"])
                    return

        if "hasPreventCheat" in _room.info:
            if _room.info["hasPreventCheat"]:
                if _account not in _room.entities.values():
                    for k, v in _room.entities.items():
                        if _account.latitude and _account.longitude and v.longitude and v.latitude:
                            distance = Util.getdistance(_account.longitude, _account.latitude,
                                                        v.longitude, v.latitude)
                            if distance * 1000 < 100:
                                _account.call_client_func("Notice", ["加入失败,距离过近"])
                                join_room_failed_callback()
                                return
        _room.login_to_room(_account, join_room_success_callback)

    def get_player_in_room(self, requester, _args, is_admin):
        """
        房间内玩家列表
        """
        room_type = _args["roomType"]
        game_type = _args["type"]
        room_id = _args['roomId']
        _rooms = self.rooms[game_type].roominfos[room_type]
        _room = None
        for r in _rooms.values():
            if int(r.info["roomId"]) == int(room_id):
                _room = r
        if not _room:
            return

        can_operator = False
        if "teaHouseId" in _room.info:
            if _room.info["teaHouseId"] == _args['teaHouseId']:
                can_operator = True
        if not can_operator:
            return

        room_state = 0
        if _room.info["started"]:
            room_state = 1
        if _room.total_settlement_ed:
            room_state = 2
        if not is_admin:
            room_state = 3

        all_members = []
        for k, account in _room.entities.items():
            item = {}
            item["userId"] = account.userId
            item["name"] = account.name
            item["headImage"] = account.headImageUrl
            all_members.append(item)
        requester.call_client_func('GetPlayerInRoom', {'membersInfo': all_members, "canKickOut": room_state == 0})

    def create_room_success_callback(self, _room):
        """
        创建房间成功的回调
        :param _room:
        :return:
        """
        _creator = _room.info["creator"]

        def callback(baseRef, databaseID, wasActive):
            """
            房主实体创建成功回调
            :param baseRef:
            :param databaseID:
            :param wasActive:
            :return:
            """
            _creator_entity = baseRef
            _type = _room.info["type"]
            _roomType = _room.info["roomType"]
            _roomId = _room.info["roomId"]
            _room.master = self

            # 统计今日房间数量
            today_date = datetime.date.today()
            today_end = int(time.mktime(today_date.timetuple()) + 86399)
            room_level = 0
            if _room.info["roomType"] == "challenge":
                room_level = _room.info['level']
            if _room.record_sql:
                DBCommand.modify_room_count_to_db(_creator, _creator_entity.name, 1, today_end, room_level)
            # if _type == Const.RoomType.RoomType8:
            #     _room.joinBots(3)

            # 如果是假房间，加满机器人
            if _room.is_fake and _room.info['type'] in Const.have_bot_game:
                _room.joinBots(_room.info['maxPlayersCount'])

            if _room.info["roomType"] == "card" or _room.info["roomType"] == "challenge":
                def notify_client():
                    # 如果房间不存在，不再加入房间
                    if not _room.cell:
                        return
                    _creator_entity.call_client_func("create_room_success", [_type, _roomType, _room.info["roomId"]])
                    # _room.cell.baseToCell({"func": "onEnter", "id": _account.id})
                    # if _room.info["roomType"] == "card":
                    _creator_entity.createRooms[_room.info["roomId"]] = _room.info
                    if _type == Const.RoomType.RoomType6 and _roomType == "challenge":
                        _room.joinBots(2)

                # 如果代开房间，自己不进入
                if "substitute" in _room.info.keys() and _room.info["substitute"]:
                    if len(_creator_entity.substituteRooms) >= self.substitute_limit:
                        _creator_entity.call_client_func("createSubstituteFailed", ["代开房间数量已达上限"])
                        return
                    _creator_entity.call_client_func("createSubstituteSuccess", [])
                    _creator_entity.substituteRooms.append(_room.info)
                else:
                    _room.login_to_room(_creator_entity, notify_client)

            # 钻石支付在创建房间成功的时候扣除钻石
            if _room.info['payType'] == Const.PayType.RoomCreator:
                if self.need_consume_card(_room.info):
                    if _roomType == "challenge":
                        KBEngine.globalData["AccountMgr"].mgr.modify_goldIngot(_creator, -_room.info['roomCardConsume'],
                                                                               consume_type=_room.info['type'],
                                                                               record_sql=_room.record_sql)
                    else:
                        # 创建时扣除房主钻石
                        KBEngine.globalData["AccountMgr"].mgr.modify_room_card(_creator, -_room.info['roomCardConsume'],
                                                                               consume_type=_room.info['type'],
                                                                               record_sql=_room.record_sql)

        KBEngine.createEntityFromDBID("Account", _creator, callback)

    def random_room_id(self, _type, room_type):
        """
        随机一个房间id
        :param _type: 游戏类型,对应定义的def文件类型
        :param room_type: 房间类型,金币房间或者钻石房间
        :return:
        """
        # if room_type == "gold":
        #     return 0
        _room_id = 111111
        _rooms = []
        for __type in self.rooms.values():
            for __room_type in __type.roominfos.values():
                for __room in __room_type.values():
                    _rooms.append(__room)
        _room_ids = []
        for _room in _rooms:
            _room_ids.append(_room.info["roomId"])
        while True:
            _room_id = random.randint(100000, 999999)
            if _room_id in _room_ids:
                continue
            else:
                return _room_id

    def remove_room(self, _room):
        """
        移除房间
        :param _room:
        :return:
        """
        # if _room.info["roomType"] == "gold":
        #     return
        _type = _room.info["type"]
        _roomType = _room.info["roomType"]
        self.rooms[_type].roominfos[_roomType].pop(_room.info["roomId"])

        def callback(baseRef, databaseID, wasActive):
            if baseRef:
                if _room.info["roomId"] in baseRef.createRooms:
                    baseRef.createRooms.pop(_room.info["roomId"])
                baseRef.writeToDB()
            if not wasActive:
                baseRef.destroy()

        _creator_db_id = _room.info["creator"]
        KBEngine.createEntityFromDBID("Account", int(_creator_db_id), callback)

    def remove_room_from_mgr(self, _room):
        """"此函数不起作用"""
        _type = _room.info["type"]
        _roomType = _room.info["roomType"]
        if _room.info["roomType"] == "gold" or _room.info["roomType"] == "challenge":
            DEBUG_MSG("remove_room_from_mgr %s" % self.rooms[_type].roominfos)
            if _room.info["level"] in self.rooms[_type].roominfos[_roomType].keys():
                for i in self.rooms[_type].roominfos[_roomType][_room.info["level"]].copy():
                    if i.databaseID == _room.databaseID:
                        self.rooms[_type].roominfos[_roomType][_room.info["level"]].remove(i)

    def get_room(self, _type, room_type, room_id):
        if _type in self.rooms:
            if room_type in self.rooms[_type].roominfos:
                _rooms = self.rooms[_type].roominfos
                if room_id in _rooms.keys():
                    _room = _rooms[room_id]
                    return _room
        return None

    def on_timer(self, _id, arg):
        """
        计时器
        :param _id:
        :param arg:
        :return:
        """
        if _id == self.mainTimerId:
            def get_prize_callback(prizes):
                data = []
                for v in prizes:
                    str = "恭喜 %s 中了%s%s" % (v["userName"], v["prizeNum"], "元话费" if v["prizeType"] == 0 else "元京东购物卡")
                    data.append(str)

                for k, v in self.rooms["RoomType6"].roominfos['challenge'].items():
                    arg = {'content': data, 'duration': 30}
                    DEBUG_MSG("on_timer %s" % v.__dict__)
                    if v.cell:
                        v.cell.baseToCell({'func': 'RollNoticeInRoom', "content": arg})

            if self.last_notify_tick < time.time():
                DEBUG_MSG("on_timer roomManager")
                self.last_notify_tick = time.time() + random.randint(60, 120)
                DBCommand.get_chapter_prize(get_prize_callback)

        # if _id == self.mainTimerId:
        #     _rooms = self.rooms.copy()
        #     for k, v in _rooms.items():
        #         for key, value in v.roominfos.items():
        #             for key1, value1 in value.items():
        #                 if value1.roomState == 2:
        #                     DEBUG_MSG("value1.roomState--------> %s" % key1)
        # pass

    def need_consume_card(self, room_info):
        """
        检测此房间是否需要消耗钻石
        :param room_info:
        :return:
        """
        # E 是否消耗钻石
        try:
            consume_config = Const.ServerGameConfigJson.config_json['CreateRoomConsumeSwitch']
            return bool(consume_config[room_info['roomType']][room_info['type']])
            # return False
        except TypeError as e:
            ERROR_MSG('need_consume_card %s' % e)
        except KeyError as e:
            ERROR_MSG('need_consume_card %s' % e)

    def room5_conflict(self, info):
        """
        麻将房间规则自洽
        :return:
        """
        if info['type'] != Const.RoomType.RoomType5:
            return
        # 下米没有开时，下米分为0
        if 4 not in info['playingMethod']:
            info['xiaMi'] = 0

    def room8_conflict(self, info):
        """
        牌九房间规则自洽
        :param info:
        :return:
        """
        if info['type'] != Const.RoomType.RoomType8:
            return
        if info['pot']:
            info['stakeMode'] = 0

    def room_config_conflict(self, info):
        """
        房间配置自洽
        :return:
        """
        # if info['type'] == Const.RoomType.RoomType12:
        #     # 二人单色设置
        #     if info['maxPlayersCount'] == 2:
        #         info['haveWind'] = True
        #         info['j258'] = False
        #         info['onlySelfAfterPass'] = False
        #     # 自摸，没有过胡只能自摸
        #     if info['huType'] == 1:
        #         info['onlySelfAfterPass'] = False

        pass

    def room12_conflict(self, info):
        """
        滑水开房规则自洽
        :param info:
        :return:
        """
        if info['type'] != Const.RoomType.RoomType12:
            return
        if info['maxPlayersCount'] == 2:
            info['onlySelfAfterPass'] = False
            info['haveWind'] = True
            info['j258'] = False
        else:
            info['singleColor'] = -1

    def is_snoring_all_room(self):
        return self.snoring_all_room
