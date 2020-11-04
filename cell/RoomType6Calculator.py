# -*- coding: utf-8 -*-
import copy
import random
import re

# 判断牌型
import sys
import time
from enum import unique, Enum


# 牌型
# from KBEDebug import DEBUG_MSG


@unique
class CardType(Enum):
    invalid = -1
    danzhang = 0
    duizi = 1
    sanzhang = 2
    zhadan = 4
    sandaiyi = 5
    sandaier = 10
    wangzha = 6
    shunzi = 7
    twoliandui = 8
    feiji = 9
    sidaier = 11
    feiji_single = 12
    threeliandui = 13


def play_card_correct(correct_cards, card_type=False):
    cards = copy.deepcopy(correct_cards)
    cards = convert_cards_to_value(cards)
    length = len(cards)
    if length == 1:
        return CardType.danzhang
    elif length == 2:
        if cards[0] == cards[1]:
            return CardType.duizi
        elif cards[0] + cards[1] == 33:
            return CardType.wangzha
        else:
            return CardType.invalid
    elif length == 3:
        card1, card2, card3 = cards[0], cards[1], cards[2]
        if card1 == card2 and card2 == card3:
            return CardType.sanzhang
        else:
            return CardType.invalid
    elif length == 4:
        if is_sandaiyi(cards):
            return CardType.sandaiyi
        elif is_zha_dan(cards):
            return CardType.zhadan
        else:
            return CardType.invalid
    elif length == 5:
        if is_s_z(cards):
            return CardType.shunzi
        elif is_sandaier(cards):
            return CardType.sandaier
        else:
            return CardType.invalid
    elif length > 5:
        if is_s_z(cards):
            return CardType.shunzi
        elif is_2_l_d(cards):
            return CardType.twoliandui
        elif is_3_l_d(cards):
            return CardType.threeliandui
        elif is_f_j(cards):
            return CardType.feiji
        elif is_f_single(cards):
            return CardType.feiji_single
        elif is_sidaier(cards, card_type):
            return CardType.sidaier
        else:
            return CardType.invalid
    else:
        return CardType.invalid


def convert_cards_to_value(cards):
    cards_value = []
    for card in cards:
        if isinstance(card, str):
            card = re.sub('[a-z]', '', card)
        cards_value.append(int(card))
    return cards_value


def convert_value_to_origin(origin_cards, value_cards):
    origin_cards_copy = origin_cards.copy()
    convert_origin = []
    for v in value_cards:
        for c in origin_cards_copy:
            if re.sub('[a-z]', '', c) == str(v):
                convert_origin.append(c)
                origin_cards_copy.remove(c)
                break
    return convert_origin


def is_sandaiyi(cards):
    if len(cards) != 4:
        return False
    cards.sort()
    card1, card2, card3, card4 = cards[0], cards[1], cards[2], cards[3]
    # 三带一
    if card1 == card2:
        if card2 == card3:
            if card3 != card4:
                return True
    elif card1 != card2:
        if card2 == card3:
            if card3 == card4:
                return True
    return False


def is_sandaier(cards):
    if len(cards) != 5:
        return False
    cards.sort()
    card1, card2, card3, card4, card5 = cards[0], cards[1], cards[2], cards[3], cards[4]
    # x,x,x
    # y,y
    if card1 == card2:
        if card2 == card3:
            if card4 == card5:
                if card3 != card4:
                    return True

    # x,x
    # y,y,y
    if card1 == card2:
        if card2 != card3:
            if card3 == card4:
                if card4 == card5:
                    return True
    return False


def is_zha_dan(cards):
    if len(cards) != 4:
        return False
    cards.sort()
    card1, card2, card3, card4 = cards[0], cards[1], cards[2], cards[3]
    if card1 == card2 and card2 == card3 and card3 == card4:
        return True
    return False


def is_sidaier(cards, card_type):
    if len(cards) != 6 or card_type == False:
        return False
    cards.sort()
    for cv in cards:
        if cards.count(cv) == 4:
            return True


def is_danzhang(cards):
    return len(cards) == 1


def is_duizi(cards):
    if len(cards) != 2:
        return False
    if cards[0] != cards[1]:
        return False
    return True


def is_s_zhang(cards):
    if len(cards) != 3:
        return False
    if cards[0] == cards[1] and cards[1] == cards[2]:
        return True
    else:
        return False


def is_f_j(cards):
    # 飞机长度必须是5的倍数，并且大于等于10
    if len(cards) < 10:
        return False
    if len(cards) % 5 != 0:
        return False
    new_cards = copy.deepcopy(cards)
    three = []
    # 找到所有的三张
    for card in new_cards:
        if new_cards.count(card) == 3 and card not in three:
            # 有 2 以上的不行
            if card >= 15:
                return False
            three.append(card)
    # 没有飞机
    if len(three) == 0:
        return False
    three.sort()
    # 判断三张是否相连
    for i in range(0, len(three) - 1):
        if three[i] + 1 != three[i + 1]:
            return False
    # 移除所有三张
    for card in three:
        # 移除
        while card in new_cards:
            new_cards.remove(card)

    # 排序
    new_cards.sort()
    # 检查剩下的是否能组成翅膀
    can_wing = True
    for index in range(0, len(new_cards), 2):
        if new_cards[index] != new_cards[index + 1]:
            can_wing = False
            break
    return can_wing


def is_f_single(cards):
    # 带单飞机
    if len(cards) < 8:
        return False
    if len(cards) % 4 != 0:
        return False
    new_cards = copy.deepcopy(cards)
    three = []
    # 找到所有的三张
    for card in new_cards:
        if new_cards.count(card) >= 3 and card not in three:
            three.append(card)
        # 没有飞机
    if len(three) == 0:
        return False
    three.sort()
    # 判断三张相连的牌
    three_connect = []
    for i in range(0, len(three) - 1):
        if three[i] + 1 == three[i + 1]:
            if three[i] not in three_connect:
                three_connect.append(three[i])
            if three[i + 1] not in three_connect:
                three_connect.append(three[i + 1])
    # 如果相连的三连对小于2不能构成飞机
    if len(three_connect) < 2:
        return False
    for i in three_connect:
        if i >= 15:
            return False
    # 记录三连对的组合长度
    three_connect_length = len(three_connect)
    # 移除所有三张
    for card in three_connect:
        # 移除
        count = 0
        for card in new_cards:
            if count == 3:
                break
            new_cards.remove(card)
            count += 1

    if len(new_cards) != three_connect_length:
        return False
    return True


def is_s_z(cards):
    if len(cards) < 5:
        return False
    # 排序
    cards.sort()
    # 不能包含大小王和 2
    if cards[len(cards) - 1] >= 15:
        return False
    for card in cards:
        if cards.count(card) != 1:
            return False
    for index in range(0, len(cards) - 1):
        if not cards[index] + 1 == cards[index + 1]:
            return False
    return True


def is_wangzha(cards):
    if len(cards) != 2:
        return False
    return cards[0] + cards[1] == 33


def is_2_l_d(cards):
    if len(cards) < 6:
        return False
    if len(cards) % 2 != 0:
        return False
    for card in cards:
        if cards.count(card) != 2:
            return False
    new_cards = copy.deepcopy(cards)
    new_cards.sort()
    # 去重
    for card in new_cards:
        while new_cards.count(card) != 1:
            new_cards.remove(card)
    # 不能包含大小王和 2
    if new_cards[len(new_cards) - 1] >= 15:
        return False

    for index in range(0, len(new_cards) - 1):
        if not new_cards[index] + 1 == new_cards[index + 1]:
            return False
    return True


def is_3_l_d(cards):
    if len(cards) < 6:
        return False
    if len(cards) % 3 != 0:
        return False
    for card in cards:
        if cards.count(card) != 3:
            return False
    new_cards = copy.deepcopy(cards)
    new_cards.sort()
    for card in new_cards:
        while new_cards.count(card) != 1:
            new_cards.remove(card)
    # 不能包含大小王和 2
    if new_cards[len(new_cards) - 1] >= 15:
        return False
    for index in range(0, len(new_cards) - 1):
        if not new_cards[index] + 1 == new_cards[index + 1]:
            return False
    return True


def compare_cards(cards1, cards2, card_type):
    """
    返回值为参数一是否大于参数二
    :param cards1: str[] 牌值
    :param cards2: str[] 牌值
    :return:
    """
    cards1_type = play_card_correct(cards1, card_type)
    cards2_type = play_card_correct(cards2, card_type)

    cards1 = convert_cards_to_value(cards1)
    cards2 = convert_cards_to_value(cards2)

    # 任何一组牌为无效组合就返回空
    if cards1_type == CardType.invalid:
        return None

    if cards2_type == CardType.invalid:
        return None

    # 如果是王炸，返回结果
    if cards1_type == CardType.wangzha:
        return True

    if cards2_type == CardType.wangzha:
        return False

    # 如果任何一方是炸弹或都是炸弹，进行比较
    if cards1_type == CardType.zhadan:
        if cards2_type == CardType.zhadan:
            return compare_zhadan(cards1, cards2)
        else:
            return True

    # if cards1_type == CardType.sidaier:

    if cards2_type == CardType.zhadan:
        if cards1_type == CardType.zhadan:
            return compare_zhadan(cards1, cards2)
        else:
            return False

    # 如果不是炸弹并且牌型不同，无法比较
    # 如果不是炸弹并且长度不同，无法比较
    if cards1_type != cards2_type:
        return None
    if len(cards1) != len(cards2):
        return None
    else:
        if cards1_type == CardType.danzhang:
            return compare_danzhang(cards1, cards2)
        if cards1_type == CardType.duizi:
            return compare_duizi(cards1, cards2)
        if cards1_type == CardType.sanzhang:
            return compare_sanzhang(cards1, cards2)
        if cards1_type == CardType.sandaiyi:
            return compare_s_d_y(cards1, cards2)
        if cards1_type == CardType.sandaier:
            return compare_sandaier(cards1, cards2)
        if cards1_type == CardType.shunzi:
            return compare_s_z(cards1, cards2)
        if cards1_type == CardType.twoliandui:
            return compare_2_l_d(cards1, cards2)
        if cards1_type == CardType.feiji:
            return compare_f_j(cards1, cards2)
        if cards1_type == CardType.threeliandui:
            return compare_3_l_d(cards1, cards2)
        if cards1_type == CardType.feiji_single:
            return compare_f_j(cards1, cards2)
        if cards1_type == CardType.sidaier:
            return compare_sidaier(cards1, cards2)


def compare_sidaier(cards1, cards2):
    # cards1.sort()
    # cards2.sort()
    card1_si, card2_si = 0, 0
    for i in cards1:
        if cards1.count(i) == 4:
            card1_si = i
            break

    for i in cards2:
        if cards2.count(i) == 4:
            card2_si = i
            break

    return card1_si > card2_si


def compare_s_d_y(cards1, cards2):
    """
    参数一是否大于参数二
    :param cards1:
    :param cards2:
    :return:
    """
    card1_three, card2_three = 0, 0
    for i in cards1:
        if cards1.count(i) == 3:
            card1_three = i
            break

    for i in cards2:
        if cards2.count(i) == 3:
            card2_three = i
            break

    return card1_three > card2_three


def compare_sandaier(cards1, cards2):
    #     """
    #     参数一是否大于参数二
    #     :param cards1:
    #     :param cards2:
    #     :return:
    #     """
    cards1_three, cards2_three = 0, 0
    cards1.sort()
    cards2.sort()
    for i in cards2:
        if cards2.count(i) == 3:
            cards2_three = i
            break
    for i in cards1:
        if cards1.count(i) == 3:
            cards1_three = i
            break
    return cards1_three > cards2_three


def compare_danzhang(cards1, cards2):
    """
    参数一是否大于参数二
    :param cards1:
    :param cards2:
    :return:
    """
    return cards1 > cards2


def compare_duizi(cards1, cards2):
    """
    参数一是否大于参数二
    :param cards1:
    :param cards2:
    :return:
    """
    return cards1[0] > cards2[0]


def compare_sanzhang(cards1, cards2):
    """
        参数一是否大于参数二
        :param cards1:
        :param cards2:
        :return:
        """
    return cards1[0] > cards2[0]


def compare_zhadan(cards1, cards2):
    """
    比较两个炸弹的大小
    :param cards1:
    :param cards2:
    :return:
    """
    return cards1[0] > cards2[0]


def compare_s_z(cards1, cards2):
    cards1.sort()
    cards2.sort()
    # 比较最大的一个元素
    return cards1[-1] > cards2[-1]


def compare_2_l_d(cards1, cards2):
    cards1.sort()
    cards2.sort()
    # 比较最大的一个元素
    return cards1[-1] > cards2[-1]


def compare_3_l_d(cards1, cards2):
    cards1.sort()
    cards2.sort()
    # 比较最大的一个元素
    return cards1[-1] > cards2[-1]


def compare_f_j(cards1, cards2):
    card1_three, card2_three = [], []
    for i in cards1:
        if cards1.count(i) == 3 and i not in card1_three:
            card1_three.append(i)

    for i in cards2:
        if cards2.count(i) == 3 and i not in card2_three:
            card2_three.append(i)

    card1_three.sort()
    card2_three.sort()

    return card1_three[-1] > card2_three[-1]


def tip_cards(pre_player_cards, tip_cards_lib, true_cards_lib, single_max=False):
    """
    返回值为空代表没有找到牌组
    对子、炸弹、飞机等牌组以二位数组的形式返回
    示例：
    [[1,1,1,1],[2,2,2,2]]
    :param true_cards_lib: 真实牌库
    :param single_max: 报单顶大
    :param pre_player_cards:上家出牌
    :param tip_cards_lib:提示牌库，有可能是两位玩家的手牌和
    :return:
    """
    pre_cards_type = play_card_correct(pre_player_cards)
    pre_player_cards = convert_cards_to_value(pre_player_cards)
    tip_cards_lib = convert_cards_to_value(tip_cards_lib)
    if pre_cards_type == CardType.invalid:
        return []

    wangzha = find_w_z(tip_cards_lib)
    if len(wangzha) != 0 and 2 <= len(true_cards_lib) <= 3:
        return wangzha

    # 如果对方出的牌有王炸直接跳过
    if is_wangzha(pre_player_cards):
        return []
    if is_zha_dan(pre_player_cards):
        zhadans = find_z_d(tip_cards_lib)
        for zhadan in zhadans:
            if compare_zhadan(zhadan, pre_player_cards):
                return zhadan
        wangzha = find_w_z(tip_cards_lib)
        if len(wangzha) != 0:
            return wangzha
        return []

    # 如果对方出的是单张
    if is_danzhang(pre_player_cards):
        # 单张压制
        dan_zhang = find_danzhang(tip_cards_lib, single_max)
        for card in dan_zhang:
            if card > pre_player_cards[0]:
                return [card]

        tip_cards_lib.sort()

        # 没有单张，拆单
        all_cards = find_all_cards_single(tip_cards_lib)
        for i in all_cards:
            if i > pre_player_cards[0]:
                return [i]

    # 如果对方出的是对子
    elif is_duizi(pre_player_cards):
        duizis = find_duizi(tip_cards_lib)
        for duizi in duizis:
            if duizi[0] > pre_player_cards[0]:
                return duizi

        # 没有对子，拆对
        all_cards = find_all_cards_single(tip_cards_lib)
        for i in all_cards:
            if i > pre_player_cards[0] and all_cards.count(i) >= 2:
                return [i, i]

    elif is_s_zhang(pre_player_cards):
        sanzhangs = find_san_zhang(tip_cards_lib)
        for sanzhang in sanzhangs:
            if sanzhang[0] > pre_player_cards[0]:
                return sanzhang
    elif is_sandaiyi(pre_player_cards):
        sandaiyis = find_san_dai_yi(tip_cards_lib)
        for sandaiyi in sandaiyis:
            if compare_s_d_y(sandaiyi, pre_player_cards):
                return sandaiyi
    elif is_sandaier(pre_player_cards):
        sandaiers = find_san_dai_er(tip_cards_lib)
        for sandaier in sandaiers:
            if compare_sandaier(sandaier, pre_player_cards):
                return sandaier
    elif is_s_z(pre_player_cards):
        shunzis = find_s_z(tip_cards_lib, len(pre_player_cards))
        for shunzi in shunzis:
            if compare_s_z(shunzi, pre_player_cards):
                return shunzi
    elif is_2_l_d(pre_player_cards):
        length = int(len(pre_player_cards) / 2)
        twolianduis = find_two_lian_dui(tip_cards_lib, length)
        for twoliandui in twolianduis:
            if compare_2_l_d(twoliandui, pre_player_cards):
                return twoliandui
    elif is_3_l_d(pre_player_cards):
        length = int(len(pre_player_cards) / 3)
        threelianduis = find_3_l_d(tip_cards_lib, length)
        for threeliandui in threelianduis:
            if compare_3_l_d(threeliandui, pre_player_cards):
                return threeliandui
    elif is_f_j(pre_player_cards):
        length = int(len(pre_player_cards) / 5)
        feijis = find_f_j(tip_cards_lib, length)
        for feiji in feijis:
            if compare_f_j(feiji, pre_player_cards):
                return feiji
    elif is_f_single(pre_player_cards):
        length = int(len(pre_player_cards) / 4)
        feijis = find_f_j_single(tip_cards_lib, length)
        for feiji in feijis:
            if compare_f_j(feiji, pre_player_cards):
                return feiji

    zhadans = find_z_d(tip_cards_lib)
    for zhadan in zhadans:
        return zhadan

    return []


def find_danzhang(target_cards, single_max=False):
    """
    找出所有单张
    :param single_max: 报单顶大
    :param target_cards:
    :return:
    """
    cards = []
    for i in target_cards:
        if target_cards.count(i) == 1:
            cards.append(i)
    cards.sort(reverse=single_max)
    return cards


def find_all_cards_single(target_cards):
    """
    找出所有牌的单牌
    :param target_cards:
    :return:
    """
    cards = []
    for i in target_cards:
        if i not in cards:
            cards.append(i)
    cards.sort()
    return cards


def find_z_d(target_cards):
    """
    找出手牌中的所有炸弹
    :param target_cards:
    :return:
    """
    zha_dan = []
    checked = []
    copy_cards = target_cards.copy()
    copy_cards.sort()
    for i in copy_cards:
        if copy_cards.count(i) >= 4:
            if i in checked:
                continue
            temp = [i, i, i, i]
            if temp not in zha_dan:
                zha_dan.append(temp)
                checked.append(i)

    return zha_dan


def find_w_z(target_cards):
    if 16 in target_cards:
        if 17 in target_cards:
            return [16, 17]
    return []


def find_duizi(target_cards):
    new_cards = target_cards.copy()
    new_cards.sort()
    duizi = []
    for i in target_cards:
        if new_cards.count(i) >= 2:
            temp = []
            for j in range(0, 2):
                temp.append(i)
                new_cards.remove(i)
            if temp not in duizi:
                duizi.append(temp)

    return duizi


def find_san_zhang(target_cards):
    three = []
    for i in target_cards:
        if target_cards.count(i) >= 3:
            if i not in three:
                temp = []
                for j in range(0, 3):
                    temp.append(i)
                three.append(temp)
    return three


def find_san_dai_yi(target_cards):
    three = []
    target_cards.sort()
    # 找到所有三张
    for i in target_cards:
        if target_cards.count(i) >= 3:
            if i not in three:
                three.append(i)
    san_dai_yi_s = []
    for i in three:
        temp = copy.deepcopy(target_cards)
        for count in range(0, 3):
            temp.remove(i)
        for yi in temp:
            if yi != i:
                san_dai_yi = [i, i, i, yi]
                if san_dai_yi not in san_dai_yi_s:
                    san_dai_yi_s.append(san_dai_yi)
    return san_dai_yi_s


# 1 找到手牌的所有三带二
def find_san_dai_er(target_cards):
    three = []
    two = []
    target_cards.sort()
    for i in target_cards:
        if target_cards.count(i) >= 3:
            if i not in three:
                three.append(i)
    for i in target_cards:
        if target_cards.count(i) == 2:
            if i not in two:
                two.append(i)
    san_dai_er_s = []
    for i in three:
        for j in two:
            san_dai_er = [i, i, i, j, j]
            if san_dai_er not in san_dai_er_s:
                san_dai_er_s.append(san_dai_er)
    return san_dai_er_s


# length 代表组合的长度，并不是牌组长度
def find_s_z(target_cards, length):
    if length < 5:
        return []
    shunzis = []
    cards = copy.deepcopy(target_cards)
    # 去重
    for i in cards:
        while cards.count(i) > 1:
            cards.remove(i)
    cards.sort()
    for i in cards:
        shunzi = []
        num = i
        shunzi.append(num)
        can_make_up_shunzi = True
        for count in range(0, length - 1):
            num += 1
            shunzi.append(num)
            if num not in cards or num >= 15:
                can_make_up_shunzi = False
                break
        if can_make_up_shunzi:
            if shunzi not in shunzis:
                shunzis.append(shunzi)

    return shunzis


# length 代表组合的长度，并不是牌组长度

def find_two_lian_dui(target_cards, length):
    if length < 3:
        return []
    two = []
    lianduis = []
    cards = copy.deepcopy(target_cards)
    #
    for i in cards:
        if cards.count(i) >= 2:
            if i not in two:
                two.append(i)
    two.sort()
    for i in two:
        liandui = []
        num = i
        liandui.append(num)
        liandui.append(num)
        can_make_up_liandui = True
        for count in range(0, length - 1):
            num += 1
            liandui.append(num)
            liandui.append(num)
            if num not in two or num >= 15:
                can_make_up_liandui = False
                break
        if can_make_up_liandui:
            if liandui not in lianduis:
                lianduis.append(liandui)

    return lianduis


# 查找手牌中的三连对
# length 代表组合的长度，并不是牌组长度
def find_3_l_d(target_cards, length):
    if length < 2:
        return []
    three = []
    lianduis = []
    cards = copy.deepcopy(target_cards)
    for i in cards:
        if cards.count(i) >= 3:
            if i not in three:
                three.append(i)
    three.sort()
    for i in three:
        liandui = []
        num = i
        liandui.append(num)
        liandui.append(num)
        liandui.append(num)
        can_make_up_liandui = True
        for count in range(0, length - 1):
            num += 1
            liandui.append(num)
            liandui.append(num)
            liandui.append(num)
            if num not in three or num >= 15:
                can_make_up_liandui = False
                break
        if can_make_up_liandui:
            if liandui not in lianduis:
                lianduis.append(liandui)

    return lianduis


def find_f_j_single(target_cards, length):
    if length < 2:
        return []
    # 找出所有三连对
    three_liandui_s = find_3_l_d(target_cards, length)
    feijis = []
    for three_liandui in three_liandui_s:
        cards = copy.deepcopy(target_cards)
        for i in three_liandui:
            cards.remove(i)
        # 如果移除所有三连对之后的单张不够组合飞机
        if len(cards) < length:
            return []
        danzhang_s = []
        # 找出所有单张组合
        danzhang_arrangement(cards, length, [], danzhang_s)
        for danzhang in danzhang_s:
            feiji = []
            feiji.extend(three_liandui)
            feiji.extend(danzhang)
            feiji.sort()
            if feiji not in feijis:
                feijis.append(feiji)

    return feijis


def danzhang_arrangement(cards, count, danzhang, danzhang_s):
    count -= 1
    if count == -1:
        danzhang_s.append(danzhang)
        return danzhang
    for i in cards:
        new_cards = copy.deepcopy(cards)
        new_danzhang = copy.deepcopy(danzhang)
        new_danzhang.append(i)
        new_cards.remove(i)
        danzhang_arrangement(copy.deepcopy(new_cards), count, copy.deepcopy(new_danzhang), danzhang_s)

    return danzhang_s


# 查找手牌中的飞机
# length 代表组合的长度，并不是牌组长度
def find_f_j(target_cards, length):
    if length < 2:
        return []
    # 找出所有三连对
    three_liandui_s = find_3_l_d(target_cards, length)
    feijis = []
    for three_liandui in three_liandui_s:
        cards = copy.deepcopy(target_cards)
        for i in three_liandui:
            cards.remove(i)
        cards = find_duizi(cards)
        duizis = []
        # 找出所有对子组合
        duizi_arrangement(cards, length, [], duizis)
        for duizi in duizis:
            feiji = []
            feiji.extend(three_liandui)
            feiji.extend(duizi)
            feiji.sort()
            if feiji not in feijis:
                feijis.append(feiji)

    return feijis


# 找对子递归
def duizi_arrangement(cards, count, duizi, duizis):
    count -= 1
    if count == -1:
        duizis.append(duizi)
        return duizi
    for i in cards:
        new_cards = copy.deepcopy(cards)
        new_duizi = copy.deepcopy(duizi)
        new_duizi.extend(i)
        new_cards.remove(i)
        duizi_arrangement(copy.deepcopy(new_cards), count, copy.deepcopy(new_duizi), duizis)

    return duizis


def get_number_count_in_cards(number, cards):
    value_cards = convert_cards_to_value(cards)
    return value_cards.count(number)


def sort_single_on_first(cards):
    card_value = convert_cards_to_value(cards)
    card_value = sorted(card_value, key=lambda x: card_value.count(x))
    return convert_value_to_origin(cards, card_value)


def sort_not_cover_on_end(cards, cover_cards):
    cards = sorted(cards, key=lambda x: x in cover_cards)
    return cards
