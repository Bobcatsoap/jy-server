# -*- coding: utf-8 -*-
import copy
import time
from enum import Enum

_cardValue = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
    13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
    26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
    39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
    52, 53
]
c_color = [
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    1, 2, 3, 4,
    5, 5
]
c_num = [
    1, 1, 1, 1,
    2, 2, 2, 2,
    3, 3, 3, 3,
    4, 4, 4, 4,
    5, 5, 5, 5,
    6, 6, 6, 6,
    7, 7, 7, 7,
    8, 8, 8, 8,
    9, 9, 9, 9,
    10, 10, 10, 10,
    11, 11, 11, 11,
    12, 12, 12, 12,
    13, 13, 13, 13,
    14, 14
]


class CardType(Enum):
    wu_xiao = 18
    tong_hua_shun = 17
    zha_dan = 16
    hu_lu = 15
    tong_hua = 14
    shun_zi = 13
    wu_hua = 12
    si_hua = 11


class CardFilter(Enum):
    wu_xiao = 7
    tong_hua_shun = 6
    zha_dan = 5
    hu_lu = 4
    tong_hua = 3
    shun_zi = 2
    wu_hua = 1
    si_hua = 0


def has_wild_card(wild_card, cards):
    """
    检测是否有万能牌
    :param wild_card:
    :param cards:
    :return:
    """
    if wild_card is None or cards is None:
        return False
    for w in wild_card:
        if w in cards:
            cards.remove(w)
            return True
    return False


def judge(_hand_cards, filter, wild_cards):
    """
    判断牌型
    :param _hand_cards: 手牌
    :param filter: 包含的特殊牌型
    :param wild_cards: 万能牌的集合
    :return:
    """
    _cards = copy.deepcopy(_hand_cards)
    has1 = has_wild_card(wild_cards, _cards)
    has2 = has_wild_card(wild_cards, _cards)
    has3 = has_wild_card(wild_cards, _cards)
    has4 = has_wild_card(wild_cards, _cards)
    if has4:
        return 17
    if has1:
        _cards.append(-1)
    if has2:
        _cards.append(-1)
    if has3:
        _cards.append(-1)
    _max_card_type = 0
    if has1:
        for c1 in range(0, 52):
            _cards[-1] = c1
            if has2:
                for c2 in range(0, 52):
                    _cards[-2] = c2
                    if has3:
                        for c3 in range(0, 52):
                            _cards[-3] = c3
                            _card_type = calculatorCard(_cards, filter)
                            if _card_type > _max_card_type:
                                _max_card_type = _card_type
                    else:
                        _card_type = calculatorCard(_cards, filter)
                        if _card_type > _max_card_type:
                            _max_card_type = _card_type
            else:
                _card_type = calculatorCard(_cards, filter)
                if _card_type > _max_card_type:
                    _max_card_type = _card_type
    else:
        _card_type = calculatorCard(_cards, filter)
        if _card_type > _max_card_type:
            _max_card_type = _card_type

    return _max_card_type


def get_wild_card_count_in_cards(wild_cards: [], cards: []):
    """
    检测手牌中万能牌的数量
    :param wild_cards:
    :param cards:
    :return:
    """
    wild_length = 0
    for wild in wild_cards:
        if wild in cards:
            wild_length += 1
            cards.remove(wild)
    return wild_length


def calculatorCard(_cards, cards_filter):
    _cards = _cards.copy()
    _cards.sort()
    if wu_xiao(_cards) and CardFilter.wu_xiao.value in cards_filter:
        return CardType.wu_xiao.value
    if tong_hua_shun(_cards) and CardFilter.tong_hua_shun.value in cards_filter:
        return CardType.tong_hua_shun.value
    if zha_dan(_cards) and CardFilter.zha_dan.value in cards_filter:
        return CardType.zha_dan.value
    if hu_lu(_cards) and CardFilter.hu_lu.value in cards_filter:
        return CardType.hu_lu.value
    if tong_hua(_cards) and CardFilter.tong_hua.value in cards_filter:
        return CardType.tong_hua.value
    if wu_hua(_cards) and CardFilter.wu_hua.value in cards_filter:
        return CardType.wu_hua.value
    if si_hua(_cards) and CardFilter.si_hua.value in cards_filter:
        return CardType.si_hua.value
    if shun_zi(_cards) and CardFilter.shun_zi.value in cards_filter:
        return CardType.shun_zi.value
    return niu_count(_cards)


def shun_zi(cards):
    """
    计算顺子牛
    :param cards:
    :return:
    """
    num1, num2, num3, num4, num5 = c_num[cards[0]], c_num[cards[1]], c_num[cards[2]], c_num[cards[3]], c_num[cards[4]]

    if num2 - num1 == 1:
        if num3 - num2 == 1:
            if num4 - num3 == 1:
                if num5 - num4 == 1:
                    return True
    return False


def tong_hua_shun(cards):
    """
    计算同花顺
    :param cards:
    :return:
    """
    if tong_hua(cards):
        if shun_zi(cards):
            return True
    return False


def hu_lu(_cards):
    """
    计算葫芦牛
    :param _cards:
    :return:
    """
    card1, card2, card3, card4, card5 = c_num[_cards[0]], c_num[_cards[1]], c_num[_cards[2]], c_num[_cards[3]], c_num[
        _cards[4]]
    if card1 == card2:
        if card2 == card3:
            if card4 == card5:
                if card3 != card4:
                    return True

    if card1 == card2:
        if card2 != card3:
            if card3 == card4:
                if card4 == card5:
                    return True
    return False


def tong_hua(cards):
    """
    计算同花牛
    :param cards:
    :return:
    """
    color1, color2 = c_color[cards[0]], c_color[cards[1]]
    color3, color4, color5 = c_color[cards[2]], c_color[cards[3]], c_color[cards[4]]
    if color1 == color2:
        if color3 == color2:
            if color4 == color3:
                if color5 == color4:
                    return True
    return False


def zha_dan(cards):
    """
    计算炸弹牛
    :param cards:
    :return:
    """
    num1, num2, num3, num4, num5 = c_num[cards[0]], c_num[cards[1]], c_num[cards[2]], c_num[cards[3]], c_num[cards[4]]
    if num1 == num2:
        if num2 == num3:
            if num3 == num4:
                return True

    if num2 == num3:
        if num3 == num4:
            if num4 == num5:
                return True
    return False


def wu_hua(cards):
    """
    计算五花牛
    :return:
    """
    num1, num2, num3, num4, num5 = c_num[cards[0]], c_num[cards[1]], c_num[cards[2]], c_num[cards[3]], c_num[cards[4]]
    if num1 > 10:
        if num2 > 10:
            if num3 > 10:
                if num4 > 10:
                    if num5 > 10:
                        return True
    return False


def si_hua(cards):
    """
    计算四花牛
    :param cards:
    :return:
    """
    num1, num2, num3, num4, num5 = c_num[cards[0]], c_num[cards[1]], c_num[cards[2]], c_num[cards[3]], c_num[cards[4]]
    nums = [num1, num2, num3, num4, num5]
    nums_count = 0
    for n in nums:
        if n > 10:
            nums_count += 1
    return nums_count >= 4


def wu_xiao(cards):
    """
    计算五小牛
    :param cards:
    :return:
    """
    num1, num2, num3, num4, num5 = c_num[cards[0]], c_num[cards[1]], c_num[cards[2]], c_num[cards[3]], c_num[cards[4]]
    if num1 < 5:
        if num2 < 5:
            if num3 < 5:
                if num4 < 5:
                    if num5 < 5:
                        if num1 + num2 + num3 + num4 + num5 <= 10:
                            return True
    return False


def niu_count(_cards):
    """
    计算牛
    :param _cards:
    :return:
    """
    _weightSet = []
    _niuCard = {}
    for _card in _cards:
        _weight = c_num[_card]
        if _weight > 10:
            _weight = 10
        _weightSet.append(_weight)
    _hasNiu = False
    for _m in range(0, len(_weightSet)):
        if _hasNiu:
            break
        for _n in range(_m + 1, len(_weightSet)):
            if _hasNiu:
                break
            for _k in range(_n + 1, len(_weightSet)):
                if _hasNiu:
                    break
                if (_weightSet[_m] + _weightSet[_n] + _weightSet[_k]) % 10 == 0:
                    _niuCard[_m] = _cards[_m]
                    _niuCard[_n] = _cards[_n]
                    _niuCard[_k] = _cards[_k]
                    _hasNiu = True
    if not _hasNiu:
        return 0
    _leftCard = 0
    for _card in _cards:
        if _card not in _niuCard.values():
            _weight = c_num[_card]
            if _weight > 10:
                _weight = 10
            _leftCard += _weight
    _leftCard = _leftCard % 10
    if _leftCard == 0:
        return 10
    return _leftCard


def convert_card(args):
    color = args[0:2]
    num = int(args[-1])
    value = num * 4
    if color == "黑桃":
        value -= 4
    elif color == "红桃":
        value -= 3
    elif color == "梅花":
        value -= 2
    elif color == "方片":
        value -= 1
    return value
