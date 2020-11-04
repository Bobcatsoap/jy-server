# 牌型
from enum import Enum, unique

from KBEDebug import DEBUG_MSG


@unique
class CardType(Enum):
    """
    牌值类型枚举
    """
    hou_zi = 21
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
card_type_string = {0: "错误", 1: "毕十", 2: "杂牌", 3: "短牌", 4: "长牌", 5: "鹅牌", 6: "人牌",
                    7: "地牌", 8: "天牌", 9: "地杠", 10: "天杠", 11: "对杂五", 12: "对杂七", 13: "对杂八",
                    14: "对杂九", 15: "对短", 16: "对长", 17: "对峨", 18: "对人", 19: "对地", 20: "对天", 21: '猴子'}

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
# 猴王的牌型
hou_zi_filter = [
    [[2, 4], [2, 1]],
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
    hou_zi_filter,
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
def check_cards_type(check_cards):
    filter_index = check_filter(check_cards)
    cards1 = check_cards[0]
    cards2 = check_cards[1]
    # 杂牌
    if filter_index is None:
        card_type = 2
    else:
        card_type = 21 - filter_index
    cards1_number = cards1[0] + cards1[1]
    cards2_number = cards2[0] + cards2[1]
    # 点数
    number = int(str(cards1_number + cards2_number)[-1:])
    # 如果不定牌型，个位数为0，毕十
    if card_type < 9:
        if number == 0:
            card_type = 1
    return [card_type, number]


def check_filter(check_cards):
    """
    检查牌组的牌型
    :param check_cards:
    :return:
    """
    if len(check_cards) != 2:
        return CardType.error
    cards1 = check_cards[0]
    cards2 = check_cards[1]
    for _filter in filters:
        filter_index = filters.index(_filter)
        # 固定牌型
        if filter_index <= 12:
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


def compare_cards(cards1, cards2, bankerIndex):
    """
    返回值为：
    1：代表第一组牌获胜
    2：代表第二组牌获胜
    0：代表平局
    :param cards1:
    :param cards2:
    :param bankerIndex: 第几个参数是庄家的牌
    :return:
    """
    player1_cards_info_1 = check_cards_type([cards1[0], cards1[1]])
    player2_cards_info_1 = check_cards_type([cards2[0], cards2[1]])
    result1 = compare_one_couple_cards(player1_cards_info_1, player2_cards_info_1, bankerIndex)
    if len(cards1) == 2 and len(cards2) == 2:
        return result1
    if len(cards1) == 4 and len(cards2) == 4:
        player1_cards_info_2 = check_cards_type([cards1[2], cards1[3]])
        player2_cards_info_2 = check_cards_type([cards2[2], cards2[3]])
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


def get_max_combination(cards):
    """
    获取最大组合
    :param cards:
    :return:
    """
    card1 = cards[0]
    card2 = cards[1]
    card3 = cards[2]
    card4 = cards[3]

    if compare_cards([card1, card2], [card3, card4], 1) == 1:
        combination1 = [card3, card4, card1, card2]
    else:
        combination1 = [card1, card2, card3, card4]

    if compare_cards([card1, card3], [card2, card4], 1) == 1:
        combination2 = [card2, card4, card1, card3]
    else:
        combination2 = [card1, card3, card2, card4]

    if compare_cards([card1, card4], [card2, card3], 1) == 1:
        combination3 = [card2, card3, card1, card4]
    else:
        combination3 = [card1, card4, card2, card3]

    # 存储所有组合
    combinations = [combination1, combination2, combination3]

    # 按大小排序组合
    for x in range(0, len(combinations) - 1):
        for y in range(0, len(combinations) - 1 - x):
            if compare_cards(combinations[y], combinations[y + 1], 1) == 2:
                combinations[y + 1], combinations[y] = combinations[y], combinations[y + 1]

    DEBUG_MSG('get_max_combination combinations:%s' % combinations)

    # 客户端定义的的牌型组合
    combinations_str = [get_cards_string(com) for com in combinations]
    combinations_dic = {}
    # 将list转为字典，解决嵌套list无法解析的问题
    for index, com in enumerate(combinations_str):
        combinations_dic[index] = com

    return combinations_dic


def get_cards_readable(cards):
    """
    获取人类可读的牌型提示
    :param cards:
    :return:
    """
    info = check_cards_type(cards)
    type_info = info[0]
    number_info = info[1]
    str_type = card_type_string[int(type_info)]
    str_number = str(int(number_info))
    if 2 <= type_info <= 8:
        return str_type + str_number
    else:
        return str_type


def get_cards_multiple(target_cards: [], multiple: []):
    """
    获取牌型对应的翻倍规则
    :param multiple: 翻倍规则
    :param target_cards: 目标手牌
    :return:
    """
    cards_type, number = check_cards_type(target_cards)
    # 翻倍规则
    # 8,9,地杠，天杠，对杂五，对杂七，对杂八，对杂九，对短，对长，对鹅，对人，对地，对天，猴子
    # 固定牌型
    multiple_index = 0
    if 9 <= cards_type <= 21:
        multiple_index = cards_type - 7
    # 点牌
    elif 1 <= cards_type <= 8:
        if number == 8:
            multiple_index = 0
        elif number == 9:
            multiple_index = 1
        # 如果不是8，9点，返回一倍
        else:
            return 1

    return multiple[multiple_index]


print(check_cards_type([[3, 1], [0, 5]]))
print(get_cards_multiple([[4, 0], [4, 0]], [2, 2, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5]))
