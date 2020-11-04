import random
import time

from mj.AgariIndex import analyse, agariList
import PaiTypeUtil
from KBEDebug import *


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


def is_seven_pair_contain_lai_zi(shou_pais, lai_zis):
    """
    先整理牌个数，赖子个数只要大于等于单的个数即可
    :param  shou_pais:
    :param  lai_zis:赖子牌值,可以多个或没有
    :return:
    0:不是七星对
    1：是七星对
    2：豪华七星对
    """
    if len(shou_pais) != 14:
        return False

    lai_zi_count = 0
    for lai_zi in lai_zis:
        lai_zi_count += shou_pais.count(lai_zi)

    new_cards = []
    if lai_zi_count:
        new_cards = [v for v in shou_pais if v not in lai_zis]
    else:
        new_cards = shou_pais

    single_count = 0
    hao_hua_seven_pair = False
    n_pais = analyse(new_cards)
    for pai_cnt in n_pais:
        if pai_cnt % 2 == 0:
            if pai_cnt == 4:
                hao_hua_seven_pair = True
            continue
        if pai_cnt == 3:
            hao_hua_seven_pair = True
        single_count += 1

    if lai_zi_count >= single_count:
        return 2 if hao_hua_seven_pair else 1
    return 0


# 下面是赖子判断
# cards：手牌数组，不超过14张牌，每张牌由整数表示如下
# // 条：1, 2, 3, 4, 5, 6, 7, 8, 9,
# // 万：11, 12, 13, 14, 15, 16, 17, 18, 19,
# // 筒：21, 22, 23, 24, 25, 26, 27, 28, 29,
# // 东南西北中发白：31, 41, 51, 61, 71, 81, 91,
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
    elif 27 <= card <= 33:
        return (card - 24) * 10 + 1


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

print(can_hu_contain_lai_zi([31, 25, 23, 20, 21, 24, 21, 22],[31],-1))

# 测试代码
# end = time.time()
# # 发发发、三四五条，一二三万,
# start = time.time()
# shou_pai = [1, 2, 3, 11, 12, 13, 21, 22, 23, 4, 4, 4, 24, 24]
# print(can_hu_contain_lai_zi(shou_pai, []))
# end = time.time()
# print(end - start)
