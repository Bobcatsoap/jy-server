import random
import time

from mj.AgariIndex import analyse, agariList
import PaiTypeUtil

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
# 是否是杠上炮
IS_GANG_SHANG_PAO = 'isGangShangPao'
# 自摸胡
IS_ZI_MO_HE = 'isZiMoHe'
# 荒庄
IS_HUANG_ZHUANG = 'isHuangZhuang'
# 是否杠上开花
IS_GANG_SHANG_KAI_HUA = "isGangShangKaiHua"
# 是否是点杠胡
IS_DIAN_GANG_HU = 'isDianGangHu'
# 点杠胡玩家
DIAN_GANG_PLAYER = 'dianGangPlayer'
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
HU_TYPE_DIAN_GANG = 8
# --------------------------------------------------------------------------------------------
#                            麻将player中的属性
# --------------------------------------------------------------------------------------------
# 手牌
SHOU_PAI = "cards"
# 番数
FAN_COUNT = 'fanCount'
# 翻信息
FAN_INFO = 'fanInfo'
# 嘴信息
MOUTH_INFO = 'mouthInfo'
# 嘴数
MOUTH_COUNT = 'mouthCount'
# 立张数
LI_ZHANG_COUNT = 'liZhangCount'
# 能胡的牌
HU_CARDS = 'huCards'
# 所有发过的牌
ALL_DEAL_CARDS = 'allDealCards'
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
# 玩家打出后可以听的牌，每次发牌、碰牌清空，听后清空
CAN_TING_PAIS = 'canTingPai'
# 玩家听后不能打出的牌
CAN_NOT_PLAY_AFTER_TING = 'canNotPlayAfterTing'
# 玩家是否听牌 -1.没听  1.听    2.防水听
TING_TYPE = 'tingType'
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
# 下跑分
PAO_SCORE = 'paoScore'
# 玩家能否手动出牌
CAN_MANUAL_PLAY_CARD = 'canManualPlayCard'


def can_hu_pai(shouPai, pai=-1):
    """
    :param shouPai:
    :param pai: 待验证是否可以胡的牌
    :return: true 胡牌
    """
    _tsp = shouPai.copy()
    if pai != -1:
        _tsp.append(pai)
    return is_hu(_tsp)


def is_hu(cards):
    """
    是否胡牌判断
    :param cards:
    :return:
    """
    n = analyse(cards)
    ret = agariList(n)
    return ret is not None


def is_seven_pair(shou_pais):
    """
    先整理牌个数，七星对中赖子只能做他自己，所以不用进行赖子处理
    :param shou_pais:
    :param lai_zi:赖子牌值
    :param lai_zi_count:
    :return:
    0:不是七星对
    1：是七星对
    2：豪华七星对
    """
    if len(shou_pais) != 14:
        return False

    seven_pair = True
    hao_hua_seven_count = 0
    n_pais = analyse(shou_pais)
    for pai_cnt in n_pais:
        if pai_cnt % 2 != 0:
            seven_pair = False
            break
        if pai_cnt == 4:
            hao_hua_seven_count += 1

    if seven_pair:
        if hao_hua_seven_count > 0:
            return hao_hua_seven_count + 1
        return 1
    return 0


# 下面是赖子判断
# cards：手牌数组，不超过14张牌，每张牌由整数表示如下
# // 筒：1, 2, 3, 4, 5, 6, 7, 8, 9,
# // 条：11, 12, 13, 14, 15, 16, 17, 18, 19,
# // 万：21, 22, 23, 24, 25, 26, 27, 28, 29,
# // 东南西北中发白：31, 41, 51, 61, 71, 72,73
# // lai_zi：癞子数量，用整数表示
def is_pu(cards, lai_zi):
    """
    是否是扑
    """
    if len(cards) == 0:
        return True

    for first in range(cards[0] - 2, cards[0] + 1):
        if first % 10 > 7 or (lai_zi == 0 and first < cards[0]):
            continue
        shun_count = 0
        for i in range(3):
            if first + i in cards and cards.index(first + i) >= 0:
                shun_count += 1
        if shun_count == 3 or shun_count + lai_zi >= 3:
            pu_cards = cards[:]
            pu_lai_zi = lai_zi
            for i in range(3):
                delete_pos = -1
                if first + i in pu_cards:
                    delete_pos = pu_cards.index(first + i)
                if delete_pos >= 0:
                    splice(pu_cards, delete_pos, 1)
                else:
                    pu_lai_zi -= 1
            if is_pu(pu_cards, pu_lai_zi):
                return True

    ke_zi_count = 1
    ke_zi_card = cards[0]
    if len(cards) >= 2 and cards[1] == ke_zi_card:
        ke_zi_count += 1
    if len(cards) >= 3 and cards[2] == ke_zi_card:
        ke_zi_count += 1
    if ke_zi_count == 3 or ke_zi_count + lai_zi >= 3:
        pu_cards = cards[:]
        pu_lai_zi = lai_zi
        for i in range(3):
            delete_pos = -1
            if ke_zi_card in pu_cards:
                delete_pos = pu_cards.index(ke_zi_card)
            if delete_pos >= 0:
                splice(pu_cards, delete_pos, 1)
            else:
                pu_lai_zi -= 1
        if is_pu(pu_cards, pu_lai_zi):
            return True
    return False


def is_j_258(j):
    # 2
    if j == 2:
        return True
    elif j == 12:
        return True
    elif j == 22:
        return True
    # 5
    elif j == 5:
        return True
    elif j == 15:
        return True
    elif j == 25:
        return True
    # 8
    elif j == 8:
        return True
    elif j == 18:
        return True
    elif j == 28:
        return True
    else:
        return False


def can_hu_lai_zi(cards: [], lai_zi):
    """
    主函数
    return:
    第一个返回值为是否胡牌
    第二个返回值为是否满足二五八将
    """
    # 四混直接胡牌
    if lai_zi == 4:
        return True, True
    # 判断张数
    if (len(cards) + lai_zi + 1) % 3 != 0:
        return False, False
    cards.sort()
    can_hu = False
    for i in range(len(cards)):
        if i > 0 and cards[i] == cards[i - 1]:
            continue
        if (i + 1 < len(cards) and cards[i] == cards[i + 1]) or lai_zi > 0:
            # 找到对子、或是用一张癞子拼出的对子
            pu_cards = cards[:]
            pu_lai_zi = lai_zi
            _j = pu_cards[i]
            splice(pu_cards, i, 1)
            if i < len(pu_cards) and pu_cards[i] == cards[i]:
                splice(pu_cards, i, 1)
            else:
                pu_lai_zi -= 1
            # 删去对子判断剩下的牌是否成扑
            if is_pu(pu_cards, pu_lai_zi):
                # 如果能胡，并且是258将，直接返回
                can_hu = True
                if is_j_258(_j):
                    return True, True
    if lai_zi >= 2 and is_pu(cards, lai_zi - 2):
        # 两个癞子做将牌,则一定满足二五八将
        return True, True
    # 如果能胡，但不能胡二五八将，返回
    if can_hu:
        return True, False
    return False, False


def splice(_list, start, count):
    """
    js splice 函数，删除list中从start索引数起的前count个元素
    """
    for i in range(count):
        if start <= len(_list) - 1:
            del _list[start]


def hun_pai_count(cards: [], lai_zis: []):
    lai_zi_count = 0
    for val in lai_zis:
        lai_zi_count += cards.count(val)
    return lai_zi_count


def can_hu_contain_lai_zi(cards: [], lai_zis: [], pai=-1):
    """
    0-8 -> 1-9
    9-17 -> 11-19
    18-26 -> 21-29
    27-33 -> 31,41,51...91
    :param cards:
    :param lai_zis:
    :param pai:别人出的牌，是赖子牌也不能当赖子，只能做自身
    :return:
    """
    lai_zi_count = 0
    new_cards = []
    for card in cards:
        if card in lai_zis:
            lai_zi_count += 1
            continue
        val = convert_to_lai_zi_pai_val(card)
        new_cards.append(val)

    if pai != -1:
        val = convert_to_lai_zi_pai_val(pai)
        new_cards.append(val)

    return can_hu_lai_zi(new_cards, lai_zi_count)


def convert_to_lai_zi_pai_val(card):
    if 0 <= card <= 8:
        return card + 1
    elif 9 <= card <= 17:
        return card + 2
    elif 18 <= card <= 26:
        return card + 3
    elif 31 <= card <= 33:
        return card + 40


def select_perhaps_pai(hand_cards, lst_enable, magic_red_switch=False):
    """
    通过手中牌，选择相邻牌作为可能牌，风、三元牌无相邻牌，1,9只有一个相邻牌
    :param  hand_cards:  手中牌
    :param  lst_enable:  确定可能值
    :return:
    """
    set_enable = set()
    for j in range(34):
        if hand_cards[j] > 0:
            set_enable.add(j)
            if j == 0 or j == 9 or j == 18:
                set_enable.add(j + 1)
            elif j == 8 or j == 17 or j == 26:
                set_enable.add(j - 1)
            elif j >= 27:
                pass
            else:
                set_enable.add(j + 1)
                set_enable.add(j - 1)

    for i in set_enable:
        lst_enable.append(i)

    # 如果开启红中癞子并且取值范围内没有红中，添加红中
    if magic_red_switch and 31 not in lst_enable:
        lst_enable.append(31)


# 基于赖子牌值，查找顺子、刻子、杠的个数
def pop_shun_ke_pai(cards: []):
    if len(cards) < 3:
        return False

    for i in range(len(cards)):
        first = cards[i]
        # 顺子个数
        shun_count = 0
        for j in range(3):
            if first + j in cards and cards.index(first + j) >= 0:
                shun_count += 1
            else:
                break
        if shun_count == 3:
            for k in range(3):
                if first + k in cards:
                    del_pos = cards.index(first + k)
                    del cards[del_pos]
            if i > 0:
                del cards[:i]
            return True

        # 刻子个数
        ke_zi_count = cards.count(first)
        if ke_zi_count == 3:
            del cards[:i + 3]
            return True
    return False


# 2张顺子牌的情况
def pop_part_of_shun_pai(cards:[]):
    if len(cards) < 2:
        return False

    for i in range(len(cards)):
        first = cards[i]
        # 2张顺子的情况
        if first + 1 in cards:
            if first % 10 != 1 and (first + 1) % 10 != 9:
                del cards[i]
                del_pos = cards.index(first + 1)
                del cards[del_pos]
                return True

        # 对的情况
        dui_count = cards.count(first)
        if dui_count == 2:
            del cards[:i + 2]
            return True
    return False


def get_shun_ke_count(cards: [], lai_zis: []):
    """
    获取顺子、刻子数量
    @param cards: 手牌
    @param lai_zis: 癞子数量
    @return:
    """
    # 转换牌值
    lai_zi_count = 0
    new_cards = []
    for card in cards:
        if card in lai_zis:
            lai_zi_count += 1
            continue
        val = convert_to_lai_zi_pai_val(card)
        new_cards.append(val)

    # 排序牌值,从第一张牌开始查找，
    new_cards.sort()
    new_cards2 = new_cards.copy()
    pop_count = 0
    for i in range(5):
        if pop_shun_ke_pai(new_cards):
            pop_count += 1
        else:
            break

    # 2张顺子牌的情况
    pop_part_count = 0
    for i in range(5):
        if pop_part_of_shun_pai(new_cards2):
            pop_part_count += 1
        else:
            break

    pop_count += lai_zi_count
    pop_count += (pop_part_count * 0.7)
    return pop_count


def get_good_pai(all_cards: [], lai_zis: []):
    max_count = 0
    max_index = 0
    for k, v in enumerate(all_cards):
        found_count = get_shun_ke_count(v, lai_zis)
        if found_count > max_count:
            max_count = found_count
            max_index = k

    return max_index if max_count else -1


# —————————————————————————————————— 潢川麻将番数、嘴数 ——————————————————————————————————— #
# 1：碰碰胡，2：清一色，3：一条龙，4:混一色
# 5：假混一色，6：七小对，7：豪华七小对，8：双豪华七小对，
# 9：三豪华七小对，10：大吊车，11：天胡，12：地胡
# 13：门清，14：四个头，15：上听，16：独赢
# 17：缺幺，18：般般高，19：坎，20：中发白
# 21：自摸，22：点炮，23：三碰，24：杠上开花
# 25：杠上炮，26：海底捞，27：海底炮，28：跑子
# 29：断门，30：双断门，31：立张，32：抢杠胡
# 33:十二番牌型  34：上听放水嘴数
def init_fan_and_mouth(room_info: dict, chapter: dict, hu_player: dict):
    init_fan_count(room_info, chapter, hu_player)
    init_mouth_count(room_info, chapter, hu_player)


def init_fan_count(room_info: dict, chapter: dict, hu_player: dict):
    """
    获取番数和特殊规则
    @param chapter:
    @param hu_player:
    @return:
    """
    fan_count = 0
    fan_info = hu_player[FAN_INFO]
    # 碰碰胡
    if is_peng_peng_hu(chapter, hu_player):
        fan_info[1] = 2
    # 清一色
    if is_qing_yi_se(hu_player):
        fan_info[2] = 5
    # 一条龙
    if is_yi_tiao_long(hu_player):
        fan_info[3] = 2
    # 混一色
    if is_hun_yi_se(hu_player):
        fan_info[4] = 3
    # 假混一色
    if is_fake_hun_yi_se(hu_player):
        fan_info[5] = 2
    # 七对胡
    if is_seven_hu(hu_player):
        fan_info[6] = 4
    # 豪华七对胡
    if is_one_luxury_seven_hu(hu_player):
        fan_info[7] = 6
    # 双豪华七对胡
    if is_two_luxury_seven_hu(hu_player):
        fan_info[8] = 8
    # 三豪华七对胡
    if is_three_luxury_seven_hu(hu_player):
        fan_info[9] = 16
    # 大吊车
    if is_da_diao_che(hu_player):
        fan_info[10] = 4
    # 天胡
    if is_tian_hu(chapter, hu_player):
        fan_info[11] = 2
    # 地胡
    if is_di_hu(chapter, hu_player):
        fan_info[12] = 2
    for v in fan_info.values():
        fan_count += v
    if 'fanLimit' in room_info and room_info['fanLimit'] > 0:
        if fan_count > room_info['fanLimit']:
            fan_count = room_info['fanLimit']
    if fan_count != 0:
        hu_player[FAN_COUNT] = fan_count


def init_mouth_count(room_info: dict, chapter: dict, hu_player: dict):
    """
    获取嘴数和特殊规则
    @param chapter:
    @param hu_player:
    @return:
    :param room_info: 房间信息
    """
    mouth_info = hu_player[MOUTH_INFO]
    mouth_count = 0
    # 双嘴    1,门清    2,断门    3,独赢    4,上听
    double_mouth = room_info['doubleMouth']
    zi_mo_mouth = room_info['ziMoMouth']
    dian_pao_mouth = room_info['dianPaoMouth']
    # 门清
    if is_men_qing(hu_player):
        mouth_info[13] = 2 if 1 in double_mouth else 1
    # 断门
    if is_duan_men(get_all_hand_cards(hu_player)):
        duan_men_count = get_duan_men_count(get_all_hand_cards(hu_player))
        # 单断门
        if duan_men_count == 1:
            mouth_info[29] = 2 if 2 in double_mouth else 1
        # 双断门
        elif duan_men_count == 2:
            mouth_info[30] = 4 if 2 in double_mouth else 2
    # 四个头
    if is_si_ge_tou(hu_player):
        mouth_info[14] = 1
    # 上听
    if is_shang_ting(hu_player):
        mouth_info[15] = 2 if 4 in double_mouth else 1
    # 独赢
    if is_du_ying(hu_player):
        mouth_info[16] = 2 if 3 in double_mouth else 1
    # 缺幺
    if is_que_yao(hu_player):
        mouth_info[17] = 1
    # 般般高
    if is_ban_ban_gao(hu_player):
        mouth_info[18] = 1
    # 坎数
    kan_count = get_kan_count(hu_player)
    if kan_count > 0:
        mouth_info[19] = kan_count
    # 中发牌数
    z_f_b_count = get_zhong_fa_bai_count(hu_player)
    if z_f_b_count > 0:
        if z_f_b_count == 1:
            mouth_info[20] = z_f_b_count
        elif z_f_b_count == 2:
            mouth_info[20] = 3
        elif z_f_b_count == 3:
            mouth_info[20] = 5
        elif z_f_b_count == 4:
            mouth_info[20] = 8

    # 自摸
    if is_zi_mo(chapter):
        mouth_info[21] = zi_mo_mouth
    # 点炮
    if is_dian_pao(chapter):
        mouth_info[22] = dian_pao_mouth
    # 三碰
    if is_san_peng(hu_player):
        mouth_info[23] = 1
    # 杠上开花
    if is_gang_shang_hua(chapter, hu_player):
        mouth_info[24] = 1
    # 杠上炮
    if is_gang_shang_pao(chapter, hu_player):
        mouth_info[25] = 1
    # 海底捞
    if is_hai_di_lao(chapter):
        mouth_info[26] = 1
    # 海底炮
    if is_hai_di_pao(chapter):
        mouth_info[27] = 1
    # 跑数
    pao_count = get_pao_zi_count(hu_player)
    if pao_count > 0:
        mouth_info[28] = pao_count
    # 立张
    li_zhang_count = get_li_zhang_count(hu_player)
    if li_zhang_count > 0:
        mouth_info[31] = li_zhang_count
    # 抢杠胡
    if is_qiang_gang_hu(chapter, hu_player):
        mouth_info[32] = 1
    # 十二番
    twelve_count = get_twelve_count(hu_player)
    if twelve_count > 0:
        mouth_info[33] = twelve_count
    # 上听防水嘴数
    fang_shui_mouth = get_fang_shui_mouth(room_info, chapter, hu_player)
    if fang_shui_mouth > 0:
        mouth_info[34] = fang_shui_mouth
    for v in mouth_info.values():
        mouth_count += v
    hu_player[MOUTH_COUNT] = mouth_count


# —————————————————————————————————— 潢川麻将牌型判断 ——————————————————————————————————— #
def is_qing_yi_se(player):
    """
    是否是清一色
    :param cards: 特殊指定手牌，听牌提示时，不取玩家的实际手牌
    :param player:玩家
    :return:
    """
    hand_cards = get_all_hand_cards(player)
    color = get_card_color(hand_cards[0])
    # 清一色不能是风
    for c in hand_cards:
        if get_card_color(c) != color:
            return False
    return True


def is_yi_tiao_long(player):
    """
    是否是一条龙
    @param player:
    @return:
    """
    hand_cards = get_all_hand_cards(player)
    cards_info = {}
    for c in hand_cards:
        number = get_card_number(c)
        color = get_card_color(c)
        # 不记录风牌
        if color == -1:
            continue
        # 记录各种颜色对应的牌值
        if color not in cards_info:
            cards_info[color] = [number]
        else:
            if number not in cards_info[color]:
                cards_info[color].append(number)

    # 如果有任何一种颜色的牌有9张，则为一条龙
    for k, v in cards_info.items():
        if len(v) == 9:
            return True
    return False


def is_hun_yi_se(player):
    """
    是否是混一色
    @param player:
    @return:
    """
    hand_cards = get_all_hand_cards(player)
    # 手牌必须有中发白
    if 31 not in hand_cards or 32 not in hand_cards or 33 not in hand_cards:
        return False
    # 中发白数量必须一样
    zhong_count = hand_cards.count(31)
    fa_count = hand_cards.count(32)
    bai_count = hand_cards.count(33)
    if zhong_count != fa_count or zhong_count != bai_count or fa_count != bai_count:
        return False
    # 去除中发白
    while 31 in hand_cards:
        hand_cards.remove(31)
    while 32 in hand_cards:
        hand_cards.remove(32)
    while 33 in hand_cards:
        hand_cards.remove(33)
    if not hand_cards:
        return False
    color = get_card_color(hand_cards[0])
    for c in hand_cards:
        if get_card_color(c) != color:
            return False
    return True


def is_fake_hun_yi_se(player):
    """
    是否是假混一色
    @param player:
    @return:
    """
    hand_cards = get_all_hand_cards(player)
    # 手牌必须有中发白中的一张
    if 31 not in hand_cards and 32 not in hand_cards and 33 not in hand_cards:
        return False
    # 去除中发白
    while 31 in hand_cards:
        hand_cards.remove(31)
    while 32 in hand_cards:
        hand_cards.remove(32)
    while 33 in hand_cards:
        hand_cards.remove(33)
    if not hand_cards:
        return False
    # 判断剩余的牌是否是清一色
    color = get_card_color(hand_cards[0])
    for c in hand_cards:
        if get_card_color(c) != color:
            return False
    return True


def is_seven_hu(player):
    """
    是否是七对胡
    @param player:
    @return:
    """
    hand_cards = player[SHOU_PAI].copy()
    seven_hu = is_seven_pair(hand_cards)
    return seven_hu == 1


def is_one_luxury_seven_hu(player):
    """
    是否是豪华七对胡
    @param player:
    @return:
    """
    hand_cards = player[SHOU_PAI].copy()
    seven_hu = is_seven_pair(hand_cards)
    return seven_hu == 2


def is_two_luxury_seven_hu(player):
    """
    是否是双豪华七对胡
    @param player:
    @return:
    """
    hand_cards = player[SHOU_PAI].copy()
    seven_hu = is_seven_pair(hand_cards)
    return seven_hu == 3


def is_three_luxury_seven_hu(player):
    """
    是否是三豪华七对胡
    @param player:
    @return:
    """
    hand_cards = player[SHOU_PAI].copy()
    seven_hu = is_seven_pair(hand_cards)
    return seven_hu == 4


def is_peng_peng_hu(chapter, player):
    """
    判断指定牌组是不是碰碰胡,前提是牌组已经胡牌
    @return:
    :param player:
    :param chapter:
    """
    hand_cards = get_all_hand_cards(player)
    # 如果除了将牌有任何牌有两张则不为碰碰胡
    # 例如七星对、豪华七星对、双豪华七星对都不算碰碰胡
    numbers = []
    for i in hand_cards:
        if hand_cards.count(i) < 3 and i not in numbers:
            numbers.append(i)
    if len(numbers) > 1:
        return False

    # 将牌只能有两张
    two_numbers = []
    for card in hand_cards:
        if hand_cards.count(card) == 2 and card not in two_numbers:
            two_numbers.append(card)

    if len(two_numbers) != 1:
        return False

    # 必须单吊将牌
    if two_numbers[0] != chapter[CUR_PAI]:
        return False
    return True


def is_da_diao_che(player):
    """
    是否是大吊车
    @param player:
    @return:
    """
    # 如果手里只剩下了两张将牌，则为大吊车
    hand_cards = player[SHOU_PAI].copy()
    if len(hand_cards) == 2:
        return True
    return False


def is_tian_hu(chapter, player):
    """
    判断是否是天湖
    :param player:
    :param chapter:
    """
    return player['canTianHu'] and is_zi_mo(chapter)


def is_di_hu(chapter, player):
    """
    判断是否是地湖
    :param player:
    :param chapter:
    """
    return player['canDiHu'] and is_dian_pao(chapter)


def is_men_qing(player) -> bool:
    """
    是否是门清
    @param player:
    @return:
    """
    # 如果没有任何碰牌算门清
    peng_count = len(player[PENG_S])
    if peng_count == 0:
        return True
    return False


def get_duan_men_count(hand_cards: []) -> int:
    """
    获取手牌的断门数
    @return:
    :param hand_cards:
    """
    cards = hand_cards.copy()
    men_count = same_type_count(cards)
    return 3 - men_count


def is_duan_men(hand_cards: []) -> int:
    """
    是否断门
    @return:
    :param hand_cards:
    """
    cards = hand_cards.copy()
    men_count = same_type_count(cards)
    return not men_count == 3


def is_si_ge_tou(player: dict) -> bool:
    """
    是否是四个头
    @param player:
    @return:
    """
    hand_cards = player[SHOU_PAI].copy()
    # 如果有任何暗杠则为四个头
    if len(player[AN_GANG_S]) != 0:
        return True
    # 如果手里牌任意牌的数量是4，则为四个头
    for c in hand_cards:
        if hand_cards.count(c) == 4:
            return True

    return False


def is_shang_ting(player: dict) -> bool:
    return player[TING_TYPE] != -1


def is_du_ying(player: dict) -> bool:
    """
    是否是独赢
    @param player:
    @return:
    """
    # 当能胡的牌数量为1时，独赢
    hu_cards = player[HU_CARDS]
    if len(hu_cards) == 1:
        return True
    return False


def is_que_yao(player: dict) -> bool:
    """
    是否是缺幺
    @param player:
    @return:
    """
    hand_cards = get_all_hand_cards(player)
    for c in hand_cards:
        number = get_card_number(c)
        if number == 1 or number == 9:
            return False
    return True


def is_ban_ban_gao(player: dict) -> bool:
    """
    是否是般般高
    @param player:
    @return:
    """
    hand_cards = player[SHOU_PAI].copy()
    shun_zi_info = get_shun_zi(hand_cards)
    # 中发白不算般般高
    if 31 in shun_zi_info:
        shun_zi_info.pop(31)
    for k, v in shun_zi_info.items():
        if v >= 2:
            return True
    return False


def get_kan_count(player: dict) -> int:
    """
    获取坎的数量
    @param player:
    @return:
    """
    hand_cards = player[SHOU_PAI].copy()
    can_count = 0
    # 找出所有三张
    three_numbers = []
    for i in hand_cards:
        if hand_cards.count(i) == 3 and i not in three_numbers:
            three_numbers.append(i)
    for i in three_numbers:
        new_hand_cards = hand_cards.copy()
        new_hand_cards.remove(i)
        new_hand_cards.remove(i)
        new_hand_cards.remove(i)
        normal_hu, j_258 = can_hu_contain_lai_zi(new_hand_cards, [])
        if normal_hu:
            can_count += 1

    return can_count


def get_zhong_fa_bai_count(player: dict) -> int:
    """
    获取手牌中有多少套中发白
    @param player:
    @return:
    """
    hand_cards = player[SHOU_PAI].copy()
    zhong_count = hand_cards.count(31)
    fa_count = hand_cards.count(32)
    bai_count = hand_cards.count(33)
    return min(zhong_count, fa_count, bai_count)


def is_zi_mo(chapter: dict) -> bool:
    """
    是否是自摸
    @param chapter:
    @param player:
    @return:
    """
    return chapter[IS_ZI_MO_HE] or chapter[IS_DIAN_GANG_HU]


def is_dian_pao(chapter: dict) -> bool:
    """
    是否是点炮
    @param chapter:
    @param player:
    @return:
    """
    return chapter[IS_DIAN_PAO_HE] or chapter[IS_QIANG_GANG_HE]


def is_qiang_gang_hu(chapter: dict, player: dict) -> bool:
    return chapter[IS_QIANG_GANG_HE]


def is_gang_shang_hua(chapter: dict, player: dict) -> bool:
    return chapter[IS_GANG_SHANG_KAI_HUA]


def is_gang_shang_pao(chapter: dict, player: dict) -> bool:
    """
    是否是杠上炮
    @param chapter:
    @param player:
    @return:
    """
    return chapter[IS_GANG_SHANG_PAO]


def is_san_peng(player: dict) -> bool:
    """
    是否是三碰
    @param player:
    @return:
    """
    # 如果碰的数量和小明杠的数量加起来大于3，则为三碰
    peng_count = len(player[PENG_S])
    xiao_ming_count = len(player[XIAO_MING_GANG_S])
    if xiao_ming_count + peng_count >= 3:
        return True
    return False


def is_hai_di_lao(chapter: dict) -> bool:
    """
    是否是海底捞
    @param chapter:
    @return:
    """
    player_count = len(chapter[PLAYER_IN_GAME])
    if chapter[IS_ZI_MO_HE] and len(chapter[CARDS_LIB]) <= player_count:
        return True
    return False


def is_hai_di_pao(chapter: dict) -> bool:
    """
    是否是海底炮
    @param chapter:
    @return:
    """
    player_count = len(chapter[PLAYER_IN_GAME])
    if chapter[IS_DIAN_PAO_HE] or chapter[IS_QIANG_GANG_HE]:
        if len(chapter[CARDS_LIB]) <= player_count:
            return True
    return False


def get_pao_zi_count(player: dict) -> int:
    """
    获取跑数
    @param player:
    @return:
    """
    return player[XIA_PAO_COUNT]


def get_li_zhang_count(player: dict) -> int:
    """
    获取立张数
    @param player:
    @return:
    """
    return player[LI_ZHANG_COUNT]


def get_twelve_count(player: dict) -> int:
    """
    获取十二番嘴数
    @param player:
    @return:
    """
    return len(player[FAN_INFO])


def get_fang_shui_mouth(room_info: dict, chapter: dict, hu_player: dict) -> int:
    """
    获取放水嘴数
    :param hu_player:
    :param room_info:
    :param chapter:
    :return:
    """
    if is_zi_mo(chapter) and hu_player[TING_TYPE] == 2:
        if 'fangShui' in room_info:
            return room_info['fangShui']
    return 0


# —————————————————————————————————— 辅助方法 ——————————————————————————————————— #
def is_same_type(cards: []) -> bool:
    """
    list中的牌是否都是同一门
    @param cards:
    @return:
    """
    if not cards:
        return False
    _type = int(cards[0] / 9)
    for c in cards:
        if int(c / 9) != _type:
            return False
    return True


def get_card_number(card):
    """
    获取牌面上的数字
    :param card:
    :return:
    """
    # 数字
    if 0 <= card <= 26:
        return card % 9 + 1
    # 如果是风牌，返回0
    else:
        return 0


def get_card_color(card):
    """
    获取牌面上的颜色
    :param card:
    :return:
    """
    # 数字
    if 0 <= card <= 26:
        return int(card / 9)
    # 如果是风牌，返回-1
    else:
        return -1


def same_type_count(cards: []) -> int:
    """
    list中的牌有多少门
    @param cards:
    @return:
    """
    # 0 筒，1 条，2 万
    if not cards:
        return 0
    _type_list = []
    for c in cards:
        _type = int(c / 9)
        if _type <= 2 and _type not in _type_list:
            _type_list.append(_type)

    return len(_type_list)


def get_shun_zi(cards) -> dict:
    """
    获取指定list里的所有顺子及其数量
    @param cards:
    @return:
    """
    if not cards:
        return {}
    _cards = cards.copy()
    shun_zi_s = []
    # 去重
    for i in cards:
        while _cards.count(i) > 1:
            _cards.remove(i)
    # 找顺子
    for i in _cards:
        if i + 1 in _cards and i + 2 in _cards:
            shun_zi = [i, i + 1, i + 2]
            if shun_zi not in shun_zi_s:
                shun_zi_s.append(shun_zi)

    shun_zi_info = {}
    for shun_zi in shun_zi_s:
        count_1 = cards.count(shun_zi[0])
        count_2 = cards.count(shun_zi[1])
        count_3 = cards.count(shun_zi[2])
        count = min(count_1, count_2, count_3)
        shun_zi_info[shun_zi[0]] = count

    # 返回值为字典，key为顺子首位的数字，value为这个顺子的数量
    return shun_zi_info


def is_shun_zi(cards) -> bool:
    """
    判断指定的三张牌是否是顺子
    @param cards:
    @return:
    """
    if len(cards) != 3:
        return False
    cards.sort()
    # 支持从大到小排列或者从小到大排列
    if cards[0] + 1 == cards[1] and cards[1] + 1 == cards[2]:
        return True
    if cards[0] - 1 == cards[1] and cards[1] - 1 == cards[2]:
        return True
    return False


def get_all_hand_cards(player: dict) -> []:
    """
    获取玩家的所有手牌，包括碰牌、杠牌和其他手牌
    @param player:
    @return:
    """
    hand_cards = []
    for peng in player[PENG_S].keys():
        hand_cards.extend([peng] * 3)

    for xiao_ming in player[XIAO_MING_GANG_S].keys():
        hand_cards.extend([xiao_ming] * 4)

    for da_ming in player[DA_MING_GANG_S].keys():
        hand_cards.extend([da_ming] * 4)

    for an_gang in player[AN_GANG_S]:
        hand_cards.extend([an_gang] * 4)

    hand_cards.extend(player[SHOU_PAI])
    hand_cards.sort()
    return hand_cards


player = {'pengs': {14: -1}, 'xiaoMingGangs': {}, 'daMingGangs': {}, 'anGangs': {},
          'cards': [18, 18, 18, 31, 31, 31, 31, 32, 32, 32, 32, 33, 33, 33]}
# 测试代码
# end = time.time()
# # 发发发、三四五条，一二三万,
# start = time.time()
# shou_pai = [1, 2, 3, 11, 12, 13, 21, 22, 23, 4, 4, 4, 24, 24]
# print(can_hu_contain_lai_zi(shou_pai, []))
# end = time.time()
# print(end - start)
