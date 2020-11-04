# -*- coding: utf-8 -*-
from random import shuffle

_cardValue = [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
            13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
            26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
            39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51
]
_cardColor = [
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 3, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4,
            1, 2, 3, 4
        ]
_cardWeight = [
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
            13, 13, 13, 13
        ]


class Const:
    class BaseScore:
        # 豹子
        BAOZI = 10000000
        # 顺金
        SHUNJIN = 1000000
        # 金花
        JINHUA = 100000
        # 顺子
        SHUNZI = 10000
        # 对子
        DUIZI = 1000
        # 单张
        DANZHANG = 100


def calculatorCard(_cards):
    """
    计算牌型
    :param _cards:
    :return:
    """
    _weight = 0
    for _card in _cards:
        _weight += _cardWeight[_card]
    if calculatorBaozi(_cards):
        return Const.BaseScore.BAOZI + _weight
    if calculatorShunjin(_cards):
        return Const.BaseScore.SHUNJIN + _weight
    if calculatorJinhua(_cards):
        return Const.BaseScore.JINHUA + _weight
    if calculatorShunzi(_cards):
        return Const.BaseScore.SHUNZI + _weight
    if calculatorDuizi(_cards):
        return Const.BaseScore.DUIZI + _weight
    else:
        return Const.BaseScore.DANZHANG + _weight


def calculatorBaozi(_cards):
    _weightSet = {}
    for _card in _cards:
        _weight = _cardWeight[_card]
        if _weight in _weightSet.keys():
            _weightSet[_weight] += 1
        else:
            _weightSet[_weight] = 1
    for k, v in _weightSet.items():
        if v == 3:
            return True
    return False


def calculatorShunjin(_cards):
    _cards.sort()
    if _cardColor[_cards[0]] == _cardColor[_cards[1]] == _cardColor[_cards[2]]:
        if _cardWeight[_cards[0]] + 2 == _cardWeight[_cards[1]]+1 == _cardWeight[_cards[2]]:
            return True
        return False
    return False


def calculatorJinhua(_cards):
    if _cardColor[_cards[0]] == _cardColor[_cards[1]] == _cardColor[_cards[2]]:
        return True
    return False


def calculatorShunzi(_cards):
    _cards.sort()
    if _cardWeight[_cards[0]] + 2 == _cardWeight[_cards[1]] + 1 == _cardWeight[_cards[2]]:
        return True
    return False


def calculatorDuizi(_cards):
    _cards.sort()
    if _cardWeight[_cards[0]] == _cardWeight[_cards[1]] or _cardWeight[_cards[1]] == _cardWeight[_cards[2]]:
        return True
    return False


# _cardlib = [1,2,3,4,5,6,7,8]
# shuffle(_cardlib)
# _card = _cardlib[0]
# print(_card)
# _cardlib.remove(_card)
# print(_cardlib)