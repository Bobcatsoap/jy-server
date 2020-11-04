import random
import time

from mj.AgariIndex import analyse,agariList
import PaiTypeUtil
from KBEDebug import *

def analyse1(hai):
    return analyse(hai)

def select_perhaps_pai(hand_cards, lst_enable):
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

    seven_pair=True
    hao_hua_seven_pair=False
    n_pais = analyse(shou_pais)
    for pai_cnt in n_pais:
        if pai_cnt % 2 != 0:
            seven_pair = False
            break
        if pai_cnt == 4:
            hao_hua_seven_pair = True

    if seven_pair:
        return 2 if hao_hua_seven_pair else 1
    else:
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


def can_hu_lai_zi(cards: [], lai_zi):
    """
    主函数
    """
    # 判断张数
    if (len(cards) + lai_zi + 1) % 3 != 0:
        return False
    cards.sort()
    for i in range(len(cards)):
        if i > 0 and cards[i] == cards[i - 1]:
            continue
        if (i + 1 < len(cards) and cards[i] == cards[i + 1]) or lai_zi > 0:
            pu_cards = cards[:]
            pu_lai_zi = lai_zi
            splice(pu_cards, i, 1)
            if i < len(pu_cards) and pu_cards[i] == cards[i]:
                splice(pu_cards, i, 1)
            else:
                pu_lai_zi -= 1
            if is_pu(pu_cards, pu_lai_zi):
                return True
    if lai_zi >= 2 and is_pu(cards, lai_zi - 2):
        return True
    return False


def splice(_list, start, count):
    """
    js splice 函数，删除list中从start索引数起的前count个元素
    """
    for i in range(count):
        if start <= len(_list) - 1:
            del _list[start]

def hun_pai_count(cards: [], lai_zis:[]):
    lai_zi_count = 0
    for val in lai_zis:
        lai_zi_count += cards.count(val)
    return lai_zi_count

def can_hu_contain_lai_zi(cards: [], lai_zis:[], pai=-1):
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
        # 风
    elif 27 <= card <= 33:
        return (card - 24) * 10 + 1


# 基于赖子牌值，查找顺子、刻子、杠的个数
def pop_shun_ke_pai(cards:[]):
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
                if first+k in cards:
                    del_pos = cards.index(first+k)
                    del cards[del_pos]
            if i > 0:
                del cards[:i]
            return True

        # 刻子个数
        ke_zi_count = cards.count(first)
        if ke_zi_count == 3:
            del cards[:i+3]
            return True
    return False

# 2张顺子牌或对的情况
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

def get_shun_ke_count(cards:[], lai_zis:[]):
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

    DEBUG_MSG("数字牌检查 %s %s %s" % (pop_count, pop_part_count, lai_zi_count))
    pop_count += lai_zi_count
    pop_count += (pop_part_count*0.7)
    return pop_count

def get_good_pai(all_cards:[], lai_zis:[]):
    max_count = 0
    max_index = 0
    for k, v in enumerate(all_cards):
        found_count = get_shun_ke_count(v, lai_zis)
        if found_count > max_count:
            max_count = found_count
            max_index = k

    return max_index if max_count else -1






# # 测试代码
# end = time.time()
# # 发发发、三四五条，一二三万,
# shou_pai = [32,32,32,11,12,13,18,19,20,1,19,20,29,29]
# print(is_hu(shou_pai))
