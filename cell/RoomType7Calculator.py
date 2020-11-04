# 牌型
import copy
from enum import Enum, unique

from KBEDebug import DEBUG_MSG


@unique
class CardType(Enum):
    huang_shang = 21
    wang_ye = 20
    # 对天
    tian_pai = 19
    # 对地
    di_pai = 18
    # 对人
    ren_pai = 17
    # 对鹅
    e_pai = 16
    # 对长
    chang_pai = 15
    # 对短
    duan_pai = 14
    # 对杂九
    dui_za_jiu = 13
    # 对杂八
    dui_za_ba = 12
    # 对杂七
    dui_za_qi = 11
    # 对杂五
    dui_za_wu = 10
    # 天杠
    tian_gang = 9
    # 地杠
    di_gang = 8
    tian_x = 7
    di_x = 6
    ren_x = 5
    e_x = 4
    chang_x = 3
    duan_x = 2
    za_x = 1
    bi_shi = 0
    error = -1


duan_x_filter = ['a11', 'c11', 'b10', 'd6', 'b6', 'd7', 'b7', 'd10']
chang_x_filter = ['a10', 'c10', 'a6', 'c6', 'c4', 'a4']
e_x_filter = ['b4', 'd4']
ren_x_filter = ['b8', 'd8']
di_x_filter = ['a2', 'b2', 'c2', 'd2']
tian_x_filter = ['a12', 'b12', 'c12', 'd12']
filters = [duan_x_filter, chang_x_filter, e_x_filter, ren_x_filter, di_x_filter, tian_x_filter]


def check_cards_type(cards):
    if len(cards) != 2:
        return CardType.error
    if '99' in cards and '100' in cards:
        return CardType.huang_shang
    # if '99' in cards or '100' in cards:
    #     return CardType.za_x
    if 'b12' in cards or 'd12' in cards:
        if 'a9' in cards or 'c9' in cards:
            return CardType.wang_ye
    if 'b12' in cards and 'd12' in cards:
        return CardType.tian_pai
    if 'b2' in cards and 'd2' in cards:
        return CardType.di_pai
    if 'b8' in cards and 'd8' in cards:
        return CardType.ren_pai
    if 'b4' in cards and 'd4' in cards:
        return CardType.e_pai

    if 'a10' in cards and 'c10' in cards:
        return CardType.chang_pai
    if 'a6' in cards and 'c6' in cards:
        return CardType.chang_pai
    if 'a4' in cards and 'c4' in cards:
        return CardType.chang_pai

    if 'a11' in cards and 'c11' in cards:
        return CardType.duan_pai
    if 'b10' in cards and 'd10' in cards:
        return CardType.duan_pai
    if 'b7' in cards and 'd7' in cards:
        return CardType.duan_pai
    if 'b6' in cards and 'd6' in cards:
        return CardType.duan_pai

    if 'a9' in cards and 'c9' in cards:
        return CardType.dui_za_jiu
    if 'a8' in cards and 'c8' in cards:
        return CardType.dui_za_ba
    if 'a7' in cards and 'c7' in cards:
        return CardType.dui_za_qi
    if 'a5' in cards and 'c5' in cards:
        return CardType.dui_za_wu

    if 'b12' in cards or 'd12' in cards or 'a12' in cards or 'c12' in cards:
        if 'b8' in cards or 'd8' in cards or 'a8' in cards or 'c8' in cards:
            return CardType.tian_gang

    if 'b2' in cards or 'd2' in cards or 'a2' in cards or 'c2' in cards:
        if 'b8' in cards or 'd8' in cards or 'a8' in cards or 'c8' in cards:
            return CardType.di_gang

    for f in tian_x_filter:
        if f in cards:
            return CardType.tian_x

    for f in di_x_filter:
        if f in cards:
            return CardType.di_x

    for f in ren_x_filter:
        if f in cards:
            return CardType.ren_x

    for f in e_x_filter:
        if f in cards:
            return CardType.e_x

    for f in chang_x_filter:
        if f in cards:
            return CardType.chang_x

    for f in duan_x_filter:
        if f in cards:
            return CardType.duan_x

    return CardType.za_x


def get_cards_weights(cards):
    temp = copy.deepcopy(cards)
    # 获取牌的类型
    cards_type = check_cards_type(cards).value
    # 获取牌的点数
    cards_number = get_cards_number(cards)
    if cards_type > 7 or cards_type < 1:
        return cards_type, 0
    # 毕十
    if cards_number == 0:
        return CardType.bi_shi.value, cards_number
    # 天地人鹅长短杂 X
    else:
        return cards_type, cards_number


def get_card_value(card):
    if card == '99' or card == '100':
        return int(card)
    return int(card[1:])


# 获取牌组的点数
def get_cards_number(cards):
    number1 = get_card_value(cards[0])
    number2 = get_card_value(cards[1])
    # 小王三点大王六点
    if number1 == 99:
        number1 = 3
    if number1 == 100:
        number1 = 6
    if number2 == 99:
        number2 = 3
    if number2 == 100:
        number2 = 6
    return int(str(number1 + number2)[-1:])


# bankerIndex:庄家的牌是第几个参数
def compare_cards(weights1, weights2, bankerIndex):
    # 第一组牌获胜者
    first_win = -1
    # 第二组牌获胜者
    second_win = -1
    DEBUG_MSG("cards weights1:%s,weights2:%s" % (weights1, weights2))
    # 比第一组牌
    first_win = compare_one_couple_cards(weights1[0], weights2[0], bankerIndex)
    # 比第二组牌
    second_win = compare_one_couple_cards(weights1[1], weights2[1], bankerIndex)

    return [first_win, second_win]


def compare_one_couple_cards(cards1_weights, cards2_weights, bankerIndex=-1):
    type1 = cards1_weights[0]
    type2 = cards2_weights[0]
    number1 = cards1_weights[1]
    number2 = cards2_weights[1]
    # 天地人鹅杂 先比点数
    if 1 <= type1 <= 7 and 1 <= type2 <= 7:
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
                # 如果相同庄家大
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
            if bankerIndex != -1:
                return bankerIndex
            return 0
