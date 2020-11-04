# 牌型
import copy
import random
import time
from enum import Enum, unique

from KBEDebug import DEBUG_MSG


@unique
class CardType(Enum):
    """
    牌值类型枚举
    """
    zha_dan = 25
    gui_zi = 24
    huang_shang = 23
    tian_wang_jiu = 22
    di_jiu_niang_niang = 21
    dui_tian = 20
    dui_di = 19
    dui_ren = 18
    dui_e = 17
    dui_chang = 16
    dui_duan = 15
    dui_za_jiu = 14
    dui_za_ba = 13
    dui_za_qi = 12
    dui_za_wu = 11
    tian_gang = 10
    di_gang = 9
    tian_x = 8
    di_x = 7
    ren_x = 6
    e_x = 5
    chang_x = 4
    duan_x = 3
    za_x = 2
    bi_shi = 1
    error = 0


# 牌值类型对应的人类可读值
card_type_string = {0: "错误", 1: "毕十", 2: "杂牌", 3: "短牌", 4: "长牌", 5: "鹅牌", 6: "人牌", 7: "地牌", 8: "天牌", 9: "地杠", 10: "天杠",
                    11: "对杂五", 12: "对杂七", 13: "对杂八",
                    14: "对杂九", 15: "对短", 16: "对长", 17: "对峨", 18: "对人", 19: "对地", 20: "对天", 21: "地九娘娘", 22: "天王九",
                    23: "皇上",
                    24: "鬼子",
                    25: "炸弹"}

# 牌值为一位数组，第一个元素是白色点数，第二个元素是红色点数
cards = [[6, 6], [6, 6],
         [0, 2], [0, 2],
         [0, 8], [0, 8],
         [3, 1], [3, 1],
         [10, 0], [10, 0],
         [6, 0], [6, 0],
         [4, 0], [4, 0],
         [11, 0], [11, 0],
         [6, 4], [6, 4],
         [6, 1], [6, 1],
         [5, 1], [5, 1],
         [2, 1], [2, 4], [9, 0], [5, 4], [7, 0], [3, 4], [0, 5], [5, 0],
         # 特别的，8,0,1 代指 2+6 的 8 点，8,0,2 代指 3+5 的 8 点
         [8, 0, 1], [8, 0, 2]]
# 炸弹的所有牌型
zha_dan_filter = [
    [[2, 1], [0, 8]],
    [[2, 1], [8, 0, 2]],
    [[2, 1], [8, 0, 1]]
]
# 鬼子的所有牌型
gui_zi_filter = [
    [[11, 0], [9, 0]],
    [[11, 0], [5, 4]]
]
# 皇上的所有牌型
huan_shang_filter = [
    [[2, 4], [2, 1]]
]
# 天王九的所有牌型
tian_wang_jiu_filter = [
    [[6, 6], [5, 4]],
    [[6, 6], [9, 0]]
]
# 地九娘娘的牌型
di_jiu_niang_ninag_filter = [
    [[0, 2], [9, 0]],
    [[0, 2], [5, 4]]
]
# 对天的牌型
dui_tian_filter = [
    [[6, 6], [6, 6]]
]
# 对地的牌型
dui_di_filter = [
    [[0, 2], [0, 2]]
]
# 对人的牌型
dui_ren_filter = [
    [[0, 8], [0, 8]]
]
# 对鹅的牌型
dui_e_filter = [
    [[3, 1], [3, 1]]
]
# 对长的牌型
dui_chang_filter = [
    [[10, 0], [10, 0]],
    [[6, 0], [6, 0]],
    [[4, 0], [4, 0]]
]
# 对短的牌型
dui_duan_filter = [
    [[11, 0], [11, 0]],
    [[6, 4], [6, 4]],
    [[6, 1], [6, 1]],
    [[5, 1], [5, 1]]
]
# 对杂的牌型
dui_za_jiu_filter = [
    [[5, 4], [9, 0]]
]
# 对杂八的牌型
dui_za_ba_filter = [
    [[8, 0, 1], [8, 0, 2]]
]
# 对杂七的牌型
dui_za_qi_filter = [
    [[7, 0], [3, 4]]
]
# 对杂五的牌型
dui_za_wu_filter = [
    [[0, 5], [5, 0]]
]
# 天杠的牌型
tian_gang_filter = [
    [[6, 6], [0, 8]],
    [[6, 6], [8, 0, 2]],
    [[6, 6], [8, 0, 1]]
]
# 地杠的牌型
di_gang_filter = [
    [[0, 2], [0, 8]],
    [[0, 2], [8, 0, 2]],
    [[0, 2], [8, 0, 1]]
]
# 天几的牌型
tian_x_filter = [
    [6, 6]
]
# 地几的牌型
di_x_filter = [
    [0, 2]
]
# 人几的牌型
ren_x_filter = [
    [0, 8]
]
# 鹅几的牌型
e_x_filter = [
    [3, 1]
]
# 长几的牌型
chang_x_filter = [
    [10, 0],
    [6, 0],
    [4, 0]
]
# 短几的牌型
duan_x_filter = [
    [11, 0],
    [6, 4],
    [6, 1],
    [5, 1]
]
# 杂几的牌型
za_x_filter = [

]
# 所有的牌型过滤器
filters = [
    zha_dan_filter,
    gui_zi_filter,
    huan_shang_filter,
    tian_wang_jiu_filter,
    di_jiu_niang_ninag_filter,
    dui_tian_filter,
    dui_di_filter,
    dui_ren_filter,
    dui_e_filter,
    dui_chang_filter,
    dui_duan_filter,
    dui_za_jiu_filter,
    dui_za_ba_filter,
    dui_za_qi_filter,
    dui_za_wu_filter,
    tian_gang_filter,
    di_gang_filter,
    tian_x_filter,
    di_x_filter,
    ren_x_filter,
    e_x_filter,
    chang_x_filter,
    duan_x_filter
]


# 牌值为二维数组
def check_cards_type(cards, card_type_filter):
    filter_index = check_filter(cards, card_type_filter)
    cards1 = cards[0]
    cards2 = cards[1]
    card_type = -1
    # 杂牌
    if filter_index is None:
        card_type = 2
    else:
        card_type = 25 - filter_index
    cards1_number = cards1[0] + cards1[1]
    cards2_number = cards2[0] + cards2[1]
    # 点数
    number = int(str(cards1_number + cards2_number)[-1:])
    if card_type < 9:
        if number == 0:
            # 如果不定牌型，个位数为0，毕十
            card_type = 1
    return [card_type, number]


def check_filter(cards, card_type_filter):
    """
    检查牌组的牌型
    :param cards:
    :param card_type_filter: 牌型限制，包含几就代表允许什么牌型
    :return:
    """
    if len(cards) != 2:
        return CardType.error
    cards1 = cards[0]
    cards2 = cards[1]
    for _filter in filters:
        filter_index = filters.index(_filter)
        # 固定牌型
        if filter_index <= 16:
            # 炸弹
            if filter_index == 0:
                if 1 not in card_type_filter:
                    continue
            # 地九娘娘
            if filter_index == 4:
                if 2 not in card_type_filter:
                    continue
            # 鬼子
            if filter_index == 1:
                if 3 not in card_type_filter:
                    continue
            # 天王九
            if filter_index == 3:
                if 4 not in card_type_filter:
                    continue
            for sub_filter in _filter:
                temp = sub_filter.copy()
                if cards1 in temp:
                    temp.remove(cards1)
                    if cards2 in temp:
                        return filter_index
        # 不定牌型
        else:
            for s_f in _filter:
                temp = s_f.copy()
                if cards1 == temp or cards2 == temp:
                    return filter_index


def compare_cards(cards1, cards2, bankerIndex, card_type):
    """
    返回值为：
    1：代表第一组牌获胜
    2：代表第二组牌获胜
    0：代表平局
    :param cards1:
    :param cards2:
    :param bankerIndex: 第几个参数是庄家的牌
    :param card_type: 包含的四种特殊牌型
    :return:
    """
    player1_cards_info_1 = check_cards_type([cards1[0], cards1[1]], card_type)
    player2_cards_info_1 = check_cards_type([cards2[0], cards2[1]], card_type)
    result1 = compare_one_couple_cards(player1_cards_info_1, player2_cards_info_1, bankerIndex)
    if len(cards1) == 2 and len(cards2) == 2:
        return result1
    if len(cards1) == 4 and len(cards2) == 4:
        player1_cards_info_2 = check_cards_type([cards1[2], cards1[3]], card_type)
        player2_cards_info_2 = check_cards_type([cards2[2], cards2[3]], card_type)
        result2 = compare_one_couple_cards(player1_cards_info_2, player2_cards_info_2, bankerIndex)
        # 如果两次比牌结果一样返回结果，否则平局
        if result1 == result2:
            return result1
        else:
            return 0


def compare_one_couple_cards(cards1_info, cards2_info, bankerIndex=-1):
    """
    返回值为：
    1：代表第一组牌获胜
    2：代表第二组牌获胜
    0：代表平局
    :param cards1_info:
    :param cards2_info:
    :param bankerIndex: 第几个参数是庄家的牌
    :return:
    """
    type1 = cards1_info[0]
    type2 = cards2_info[0]
    number1 = cards1_info[1]
    number2 = cards2_info[1]
    # 天地人鹅杂 先比点数
    if 2 <= type1 <= 8 and 2 <= type2 <= 8:
        if number1 > number2:
            return 1
        elif number1 < number2:
            return 2
        elif number1 == number2:
            # 点数相同比类型
            if type1 > type2:
                return 1
            elif type1 < type2:
                return 2
            elif type1 == type2:
                # 如果牌值完全相同,庄家大
                if bankerIndex != -1:
                    return bankerIndex
                return 0
    # 其他牌型比较类型
    else:
        # 先比牌型
        if type1 > type2:
            return 1
        elif type1 < type2:
            return 2
        elif type1 == type2:
            # 如果牌值完全相同，庄家大
            if bankerIndex != -1:
                return bankerIndex
            return 0


def get_cards_string(cards):
    """
    获取客户端牌值，例如,[5,4] 转化后为 "5+4",解决客户端无法解析二位数组的问题
    :param cards:
    :return:
    """
    cards_string = []
    for c in cards:
        s = str(c[0]) + "+" + str(c[1])
        if len(c) == 3:
            s += "+" + str(c[2])
        cards_string.append(s)
    return cards_string


def get_cards_readable(cards):
    """
    获取人类可读的牌型提示
    :param cards:
    :return:
    """
    info = check_cards_type(cards, [1, 2, 3, 4])
    type_info = info[0]
    number_info = info[1]
    str_type = card_type_string[int(type_info)]
    str_number = str(int(number_info))
    if 2 <= type_info <= 8:
        return str_type + str_number
    else:
        return str_type


def get_max_combination(cards, card_type, is_server_use=False):
    """
    获取最大组合
    :param cards:
    :return:
    """
    card1 = cards[0]
    card2 = cards[1]
    card3 = cards[2]
    card4 = cards[3]

    if compare_cards([card1, card2], [card3, card4], 1, card_type) == 1:
        combination1 = [card3, card4, card1, card2]
    else:
        combination1 = [card1, card2, card3, card4]

    if compare_cards([card1, card3], [card2, card4], 1, card_type) == 1:
        combination2 = [card2, card4, card1, card3]
    else:
        combination2 = [card1, card3, card2, card4]

    if compare_cards([card1, card4], [card2, card3], 1, card_type) == 1:
        combination3 = [card2, card3, card1, card4]
    else:
        combination3 = [card1, card4, card2, card3]

    # 存储所有组合
    combinations = [combination1, combination2, combination3]

    # 按大小排序组合
    for x in range(0, len(combinations) - 1):
        for y in range(0, len(combinations) - 1 - x):
            if compare_cards(combinations[y], combinations[y + 1], 1, card_type) == 2:
                combinations[y + 1], combinations[y] = combinations[y], combinations[y + 1]

    DEBUG_MSG('get_max_combination combinations:%s' % combinations)

    if is_server_use:
        return combinations[0]

    # 客户端定义的的牌型组合
    combinations_str = [get_cards_string(com) for com in combinations]
    combinations_dic = {}
    # 将list转为字典，解决嵌套list无法解析的问题
    for index, com in enumerate(combinations_str):
        combinations_dic[index] = com

    return combinations_dic
