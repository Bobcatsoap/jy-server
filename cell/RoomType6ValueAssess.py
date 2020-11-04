"""
斗地主牌型大小评估
"""

import RoomType6PassiveFindCards as R6P
import RoomType6InitiativeCardSplit as R6Split


def have_bigger(play_cards, next_cards, previous_cards=None, probability=0.1):
    """
    评估此牌能否被压住
    todo:改为能被敌方压住
    :return:
    """
    probability1 = calc_next_bigger_probability(play_cards, next_cards, previous_cards)
    if probability1 > probability:
        return True
    if previous_cards:
        probability1 = calc_next_bigger_probability(play_cards, previous_cards, next_cards)
        if probability1 > probability:
            return True
    return False


def is_next_bigger(play_cards, next_cards, previous_cards, probability=0.1):
    """
    评估下个人是否能压住此牌
    :return:
    """
    probability1 = calc_next_bigger_probability(play_cards, next_cards, previous_cards)
    if probability1 > probability:
        return True
    return False


def calc_probability(n1, k1, s1):
    """
    计算n个数中取K个数，有固定S个牌的几率
    """
    if s1 > k1 or k1 > n1:
        return 0
    _total_count = calc_total_num(n1, k1)
    _s_count = calc_total_num(n1 - s1, k1 - s1)
    return _s_count / _total_count


def calc_next_bigger_probability(play_cards, next_cards, privous_cards=None):
    """
    计算n个数中取K个数，有固定S个牌的几率
    """
    other_cards = next_cards.copy()
    if privous_cards:
        other_cards.extend(privous_cards)

    # 找到有几副牌可以押注，几率相加
    probability = 0
    split_dic = R6P.tip_cards_filter(play_cards, other_cards)
    for k, _list in split_dic.items():
        for v in _list:
            probability += calc_probability(len(other_cards), len(next_cards), len(v))
    return probability


def calc_total_num(_n, _k):
    """
    计算从n中取K个数的组合
    """
    _total_count = num_factorial(_n) / (num_factorial(_k) * num_factorial(_n - _k))
    return _total_count


def is_bigger_card(pre_play_cards):
    """
    比较大的牌
    """
    card_type = R6P.play_card_correct(pre_play_cards)
    card_value = R6P.get_card_value(pre_play_cards, card_type)
    if R6P.CardType.zha_dan == card_type or R6P.CardType.wang_zha == card_type:
        return True
    if R6P.CardType.dan_zhang == card_type or R6P.CardType.dui_zi == card_type:
        return card_value > 10
    elif R6P.CardType.san_zhang == card_type or R6P.CardType.san_dai_yi == card_type or R6P.CardType.san_dai_er == card_type:
        return card_value > 7
    elif R6P.CardType.shun_zi == card_type or R6P.CardType.two_lian_dui == card_type:
        return len(pre_play_cards) >= 6
    elif R6P.CardType.three_lian_dui == card_type or R6P.CardType.fei_ji == card_type or R6P.CardType.fei_ji_single == card_type:
        return True


def is_absolute_big_cards(passive_split_dic, initiative_split_cards):
    """
    绝对大牌（除了炸弹没有别的牌）
    :return:
    """
    for k, v in initiative_split_cards.items():
        if k != 'zhaDan' and k != 'wangZha':
            return None

    for k, v in passive_split_dic.items():
        return v[0]


def num_factorial(num):
    """
    计算一个数的阶乘
    """
    if num <= 0:
        return 1
    factorial = 1
    for i in range(1, num + 1):
        factorial = factorial * i
    return factorial


def same_type_sort(_list):
    _list.sort(key=lambda x: R6P.get_card_value(x))


def same_type_greater(v1, v2):
    """
    同类型牌比较，v1》v2
    """
    if len(v1) != len(v2):
        return False

    type1 = R6P.play_card_correct(v1)
    type2 = R6P.play_card_correct(v2)
    if type1 != type2:
        return False
    value1 = R6P.get_card_value(v1, type1)
    value2 = R6P.get_card_value(v2, type2)
    if value1 and value2:
        return value1 > value2
    return False


def same_type_equal(v1, v2):
    """
    同类型牌比较，v1==v2
    """
    if len(v1) != len(v2):
        return False

    type1 = R6P.play_card_correct(v1)
    type2 = R6P.play_card_correct(v2)
    if type1 != type2:
        return False
    return R6P.get_card_value(v1, type1) == R6P.get_card_value(v2, type2)


def find_follow_card(pre_play_cards, initiative_split_cards):
    """
    查找能接住的牌
    """
    bigger_cards = []
    _type = R6P.get_cards_string_type(pre_play_cards)
    for k, v in initiative_split_cards.items():
        if k == _type:
            for _ in v:
                if same_type_greater(_, pre_play_cards):
                    bigger_cards.append(_)
        if k == 'er':
            if _type == 'danZhang' or _type == 'duiZi' or _type == 'sanZhang':
                if len(v[0]) == len(pre_play_cards):
                    if v[0][0] > pre_play_cards[0]:
                        bigger_cards.append(v[0])

        if k == 'joker':
            if _type == 'danZhang' and v[0][0] > pre_play_cards[0]:
                bigger_cards.append(v[0])

    same_type_sort(bigger_cards)
    return bigger_cards


def find_all_follow_card(pre_play_cards, initiative_split_cards):
    """
    查找所有能接住的牌
    """
    bigger_cards = find_follow_card(pre_play_cards, initiative_split_cards)

    _type = R6P.get_cards_string_type(pre_play_cards)
    if _type != "zhaDan" and _type != "wangZha":
        for k, _list in initiative_split_cards.items():
            if k == "zhaDan" or k == "wangZha":
                bigger_cards.extend(_list)

    # same_type_sort(bigger_cards)
    return bigger_cards


def find_bigger_card_but_card(pre_play_cards, split_dict, small_groups):
    """
    查找是否有牌能接住指定牌
    """

    def is_in_groups(cards, _small_groups):
        for _v in _small_groups:
            if same_type_equal(_v, cards):
                return True
        return False

    bigger_cards = []
    _type = R6P.get_cards_string_type(pre_play_cards)
    for k, _list in split_dict.items():
        if k == 'wangZha':
            return _list[0]
        elif k == 'zhaDan' and _type != 'zhaDan':
            return _list[0]
        if k == _type:
            for v in _list:
                if is_in_groups(v, small_groups):
                    continue
                if same_type_greater(v, pre_play_cards):
                    bigger_cards.append(v)
    same_type_sort(bigger_cards)
    return bigger_cards


def find_little_cards_but_one(split_cards_dic, small_card):
    """
    把最小牌放最后，返回最大牌
    :param split_cards_dic:
    :param small_card:
    :return:
    """
    small_value = 100
    result = []
    for k, _list in split_cards_dic.items():
        for v in _list:
            if small_card == v:
                continue
            card_value = R6P.get_card_value(v)
            if card_value < small_value:
                small_value = card_value
                result = v
    return result
