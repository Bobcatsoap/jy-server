import random
import time

from mj.AgariIndex import *
import PaiTypeUtil
from KBEDebug import *


def isHuPai(shouPai, pai=-1, wild_card=None, all_pai=None, chi=None):
    """
    有pai参数，shouPai长度改为3n + 1；无pai参数，shouPai长度改为3n + 2
    :param shouPai:
    :param pai: 待验证是否可以胡的牌
    :param wild_card: 万能牌
    :param all_pai: 用到的牌，每张牌1张的集合
    :param chi: 玩家吃过的牌
    :return: true 胡牌
    """
    _tsp = shouPai.copy()
    if pai != -1:
        _tsp.append(pai)
    return is_hu(_tsp)


def _checkContains(shouPai, wild_card):
    """
    :param shouPai:
    :param wild_card:
    :return: true 手牌中有万能牌
    """
    for w in wild_card:
        if w in shouPai:
            return True
    return False


def is_hu(cards):
    """
    是否胡牌判断
    :param cards:
    :return:
    """
    n = analyse(cards)
    ret = agariList(n)
    return ret is not None


def _isWildCardHuPai(shou_pai, wild_card, all_pai):
    t_shou_pai = [0] * len(shou_pai)
    pos = [0] * 14

    has1 = checkRemove(wild_card, shou_pai)
    has2 = checkRemove(wild_card, shou_pai)
    has3 = checkRemove(wild_card, shou_pai)
    has4 = checkRemove(wild_card, shou_pai)

    for v1 in all_pai:
        if has2:
            for v2 in all_pai:
                if has3:
                    for v3 in all_pai:
                        if has4:
                            for v4 in all_pai:
                                b3 = _checkHuiRrHuPai(pos, shou_pai, t_shou_pai, [v1, v2, v3, v4])
                                if b3:
                                    return [v1, v2, v3, v4]
                        else:
                            b3 = _checkHuiRrHuPai(pos, shou_pai, t_shou_pai, [v1, v2, v3])
                            if b3:
                                return [v1, v2, v3]
                else:
                    b2 = _checkHuiRrHuPai(pos, shou_pai, t_shou_pai, [v1, v2])
                    if b2:
                        return [v1, v2]
        else:
            b1 = _checkHuiRrHuPai(pos, shou_pai, t_shou_pai, [v1])
            if b1:
                return [v1]


def checkRemove(wild_card, shou_pai):
    if wild_card or shou_pai is None:
        return False
    for w in wild_card:
        if w in shou_pai:
            shou_pai.remove(w)
            return True
    return False


def _checkHuiRrHuPai(pos, shou_pai, t_shou_pai, pais):
    _l = 0
    for _l, v in enumerate(shou_pai):
        t_shou_pai[_l] = v
    _l += 1
    for i in pais:
        t_shou_pai[_l] = i
        _l += 1
    n = analyse(t_shou_pai)
    listFill(pos, 0)
    ret = agariPos(n, pos)
    return ret is not None


def listFill(_list, v):
    for i in range(0, len(_list)):
        _list[i] = v


# 测试代码
end = time.time()
# 发发发、三四五条，一二三万,
shou_pai = [32,32,32,11,12,13,18,19,20,1,19,20,29,29]
print(is_hu(shou_pai))
