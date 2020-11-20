# -*- coding: utf-8 -*-
import copy
import datetime
import random
import re

# 判断牌型
from enum import unique, Enum
from time import time

from KBEDebug import DEBUG_MSG
import RoomType13

# cards_1 = [3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2,
#            8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3, 11.4, 12.1, 12.2, 12.3, 12.4, 13.1,
#            13.2, 13.3, 14.1, 15.1]
#
# cards_2 = [3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2,
#            8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3, 11.4, 12.1, 12.2, 12.3, 12.4, 13.1,
#            13.2, 13.3, 13.4, 14.1, 14.2, 14.3, 15.1]

cards_1 = [3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2,
           8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3, 11.4, 12.1, 12.2, 12.3, 12.4, 13.1,
           13.2, 13.3, 14.1, 15.3]

cards_2 = [3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2,
           8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3, 11.4, 12.1, 12.2, 12.3, 12.4, 13.1,
           13.2, 13.3, 13.4, 14.1, 14.2, 14.3, 15.3]


# ======================================================================================================================
# 牌色约定：方片：0.1  梅花：0.2  红桃：0.3  黑桃：0.4
# 牌值约定：3-15  ： 3，4...A，2
# 获取牌值int（v），牌色math.modf()保留一位小数round（）
# ======================================================================================================================

# 新牌组(待优化，可读配置文件)
def CreateCards_new(Make_Type):
    if Make_Type["special"]:
        NewCardList = copy.deepcopy(cards_1)
    else:
        NewCardList = copy.deepcopy(cards_2)
    random.shuffle(NewCardList)
    __gj_pai_rand(NewCardList)
    return NewCardList


def __gj_pai_rand(_chapter_lib):
    """
    牌随机，根据时间值，前X张牌,放在最后
    :param _chapter_lib:
    :return:
    """
    #  取当前时间
    msval = datetime.datetime.now().microsecond
    if msval > 1000:
        msval //= 1000
    pai_val = (msval % 10) + 10

    pull_pais = _chapter_lib[:pai_val]
    del _chapter_lib[:pai_val]
    _chapter_lib.extend(pull_pais)
    DEBUG_MSG("len %s,chapter lib%s" % (len(_chapter_lib), _chapter_lib))


# 牌型
@unique
class CardType(Enum):
    # 无效牌值
    Com_Invalid = -1
    # 单张
    Com_Single = 1
    # 一对
    Com_Double = 2
    # 三带一
    Com_ThreeWithSingle = 3
    # 顺子
    Com_ContinuousSingle = 4
    # 默认3带1飞机
    Com_PlaneWithSingle = 5
    # 长联对
    Com_LongDouble = 6
    # 炸弹四张
    Lin_FourBoom = 10
    # AAA炸弹
    Lin_MaxBoomForFour = 11
    # AAA炸弹带一
    Lin_MaxBoomWithSingle = 12
    # 短连对
    Lin_ShortDouble = 13
    # 三带一对
    Lin_ThreeWithDouble = 14
    # 四带一炸弹
    Lin_FourBoomWithSingle = 15
    # 3带对飞机
    Lin_PlaneWithDouble = 16
    # 四带二
    Lin_FourWithTwoSingle = 17
    # 四带三
    Lin_FourWithThreeSingle = 18
    # 三张不带（此牌型只在最后一手牌判断使用）
    Spc_OnlyThree = 20
    # 飞机不带（此牌型只在最后一手牌判断使用）
    Spc_OnlyPlan = 21
    # 四张(此牌型只在四代一为炸弹下使用)
    Spc_OnlyFour = 22
    # 3带2
    Lin_ThreeWithTwo = 23
    # 3带2飞机
    Com_PlaneWithTwo = 24


def cards_is_bomb(cards, room_info):
    """
    检测一组牌是否是炸弹
    """
    # 牌数字
    cards_number = convert_cards_to_value(cards)
    # 牌类型
    cards_type = get_cards_type(cards_number, room_info)
    if (cards_type == CardType.Lin_FourBoomWithSingle or
            cards_type == CardType.Lin_MaxBoomWithSingle or
            cards_type == CardType.Lin_FourBoom
            # cards_type == CardType.Lin_FourWithTwoSingle or
           # cards_type == CardType.Lin_FourWithThreeSingle or
           # cards_type == CardType.Lin_ThreeWithDouble or
           # cards_type == CardType.Lin_ThreeWithTwo or
          #  cards_type == CardType.Com_ThreeWithSingle or
           # cards_type == CardType.Spc_OnlyThree or
          #  cards_type == CardType.Lin_PlaneWithDouble or
          #  cards_type == CardType.Com_PlaneWithTwo or
          #  cards_type == CardType.Com_PlaneWithSingle
    ):
        return True
    else:
        return False


def check_big_bomb_and_small_bomb(pre_play_cards, this_play_cards, cards, room_info):
    """
    检测是否满足大炸弹压小炸弹
    """
    # 找到比上家大的牌
    bigger_cards = find_greater_cards(pre_play_cards, cards, room_info)
    # 如果上家出的是炸弹，并且我手里有能压住的牌
    if cards_is_bomb(pre_play_cards, room_info) and bigger_cards:
        # 如果我出的是炸弹，满足
        if cards_is_bomb(this_play_cards, room_info):
            return True
        # 如果能压住没压，不满足
        else:
            return False
    # 如果压不住，满足
    else:
        return True


def check_2_must_bomb(pre_play_cards, this_play_cards, cards, room_info):
    """
    检测是否满足2必出炸弹
    """
    # 获取上家出牌数字
    pre_play_cards_number = convert_cards_to_value(pre_play_cards)
    # 获取上家出牌类型
    pre_play_cards_type = get_cards_type(pre_play_cards_number, room_info)
    # 获取本次出牌数字
    this_play_cards_number = convert_cards_to_value(this_play_cards)
    # 获取手牌数字
    cards_number = convert_cards_to_value(cards)
    # 获取本次出牌类型
    this_play_cards_type = get_cards_type(this_play_cards_number, room_info)
    # 如果上个玩家出牌包含2，并且本玩家手牌里有炸弹
    if 15 in pre_play_cards_number and find_boom(cards_number, room_info):
        # 如果是任意一种炸弹，满足
        if (this_play_cards_type == CardType.Lin_FourBoomWithSingle or
                this_play_cards_type == CardType.Lin_MaxBoomWithSingle or
                this_play_cards_type == CardType.Lin_FourBoom

        ):
            return True
        else:
            return False
    else:
        return True


def check_single_1_must_2(pre_play_cards, this_play_cards, cards, room_info):
    """
    检测是否满足单A必出2
    """
    # 获取上家出牌数字
    pre_play_cards_number = convert_cards_to_value(pre_play_cards)
    # 获取上家出牌类型
    pre_play_cards_type = get_cards_type(pre_play_cards_number, room_info)
    # 获取本次出牌数字
    this_play_cards_number = convert_cards_to_value(this_play_cards)
    # 获取手牌数字
    cards_number = convert_cards_to_value(cards)
    # 获取本次出牌类型
    this_play_cards_type = get_cards_type(this_play_cards_number, room_info)
    # 如果上个玩家出牌是单A，并且手里有2，判断本次是否是2
    if pre_play_cards_type == CardType.Com_Single and pre_play_cards_number[0] == 14 and 15 in cards_number:
        if this_play_cards_type == CardType.Com_Single and this_play_cards_number[0] == 15:
            return True
        else:
            return False
    # 如果上个玩家出牌不是单A,一定满足
    else:
        return True


def check_single_k_must_1(pre_play_cards, this_play_cards, cards, room_info):
    """
    检测是否满足单k必出1
    """
    # 获取上家出牌数字
    pre_play_cards_number = convert_cards_to_value(pre_play_cards)
    # 获取上家出牌类型
    pre_play_cards_type = get_cards_type(pre_play_cards_number, room_info)
    # 获取本次出牌数字
    this_play_cards_number = convert_cards_to_value(this_play_cards)
    # 获取手牌数字
    cards_number = convert_cards_to_value(cards)
    # 获取本次出牌类型
    this_play_cards_type = get_cards_type(this_play_cards_number, room_info)
    # 如果上个玩家出牌是单K，并且手里有A，判断本次是否是A
    if pre_play_cards_type == CardType.Com_Single and pre_play_cards_number[0] == 13 and 14 in cards_number:
        if this_play_cards_type == CardType.Com_Single and this_play_cards_number[0] == 14:
            return True
        timeCard = 0
        for _p in cards_number:
            if _p == 14:
                timeCard += 1
        if timeCard == 3:
            return True
        else:
            return False
    # 如果上个玩家出牌不是单k,一定满足
    else:
        return True


def check_double_k_must_1(pre_play_cards, this_play_cards, cards, room_info):
    """
    检测是否满足对k必出对1
    """
    # 获取上家出牌数字
    pre_play_cards_number = convert_cards_to_value(pre_play_cards)
    # 获取上家出牌类型
    pre_play_cards_type = get_cards_type(pre_play_cards_number, room_info)
    # 获取本次出牌数字
    this_play_cards_number = convert_cards_to_value(this_play_cards)
    # 获取手牌数字
    cards_number = convert_cards_to_value(cards)
    # 获取本次出牌类型
    this_play_cards_type = get_cards_type(this_play_cards_number, room_info)
    # 如果上个玩家出牌是对K，并且手里有两个A，判断本次是否是两个A
    if pre_play_cards_type == CardType.Com_Double and pre_play_cards_number[0] == 13 and cards_number.count(14) == 2:
        if this_play_cards_type == CardType.Com_Double and this_play_cards_number[0] == 14:
            return True
        timeCard = 0
        for _p in cards_number:
            if _p == 14:
                timeCard += 1
        if timeCard == 3:
            return True
        else:
            return False
    # 如果上个玩家出牌不是对k,一定满足
    else:
        return True


def check_straight_not_a(pre_play_cards, this_play_cards, cards, room_info):
    """
    检测是否满足A不能连
    """
    # 获取本次出牌数字
    this_play_cards_number = convert_cards_to_value(this_play_cards)
    # 获取本次出牌类型
    this_play_cards_type = get_cards_type(this_play_cards_number, room_info)
    if this_play_cards_type == CardType.Com_LongDouble and 14 in this_play_cards_number:
        return False
    elif this_play_cards_type == CardType.Com_ContinuousSingle and 14 in this_play_cards_number:
        return False
    elif this_play_cards_type == CardType.Lin_ShortDouble and 14 in this_play_cards_number:
        return False
    elif this_play_cards_type == CardType.Spc_OnlyPlan and 14 in this_play_cards_number:
        return False
    return True


# 获取card2中与card1牌型一样的牌或者大的牌型(找到任意合适的牌就返回，待优化)
def find_greater_cards(card1, _card2, room_info):
    """
    找更大牌，
    炸弹不可拆
    """
    pre_cards = convert_cards_to_value(card1)
    hand_cards = convert_cards_to_value(_card2)
    # 获取上家的牌型
    card1_type = get_cards_type(pre_cards, room_info)
    DEBUG_MSG("find_greater_cards card1_type was:%s" % card1_type)

    # 最大炸弹
    if card1_type == CardType.Lin_MaxBoomWithSingle or card1_type == CardType.Lin_MaxBoomForFour:
        return []
    get_type_over_list = find_max_boom_and_negative(hand_cards, room_info)
    if len(get_type_over_list):
        return get_type_over_list

    # 牌型是炸弹
    if card1_type == CardType.Lin_FourBoomWithSingle or card1_type == CardType.Lin_FourBoom:
        value_s = get_cards_value(pre_cards, 4)
        get_type_over_list = find_bigger_boom(value_s, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list
        else:
            return []

    # 牌型不是炸弹
    if card1_type != CardType.Lin_FourBoomWithSingle and card1_type != CardType.Lin_FourBoom:
        get_type_over_list = find_boom_and_negative(hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list

    card2 = _card2
    if room_info["bombCannotSeparate"]:
        # 将玩家的手牌移除四张
        card2 = remove_boom_by_info(_card2, room_info)

    return find_greater_cards_can_split_boom(card1, card2, room_info)


def find_greater_cards_can_split_boom(card1, card2, room_info):
    """"
    找更大的牌，
    可以拆炸弹
    """
    # 返回查找结果
    pre_cards = convert_cards_to_value(card1)
    hand_cards = convert_cards_to_value(card2)
    # 获取上家的牌型
    card1_type = get_cards_type(pre_cards, room_info)
    DEBUG_MSG("playCard_type was:%s" % card1_type)
    # 如果牌型信息是无效的 返回空
    if card1_type == CardType.Com_Invalid:
        return []
    # 如果牌型是最大炸弹
    if card1_type == CardType.Lin_MaxBoomWithSingle:
        return []
    # 如果牌型是最大炸弹
    if card1_type == CardType.Lin_MaxBoomForFour:
        return []
    # 牌型为单张的时候
    if card1_type == CardType.Com_Single:
        bigger_list = find_single(pre_cards[0], hand_cards, room_info)
        if bigger_list:
            return bigger_list
    # 牌型为对子
    if card1_type == CardType.Com_Double:
        get_type_over_list = find_double(pre_cards[0], hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list
    # 牌型为三张
    if card1_type == CardType.Spc_OnlyThree:
        value_s = value_s = get_cards_value(pre_cards, 3)
        get_type_over_list = find_three(value_s, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list
    # 牌型为三带一
    if card1_type == CardType.Com_ThreeWithSingle:
        value_s = get_cards_value(pre_cards, 3)
        get_type_over_list = find_three_with_single(value_s, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list
    # 牌型为三带一对
    if card1_type == CardType.Lin_ThreeWithDouble:
        three = get_cards_value(pre_cards, 3)
        get_type_over_list = find_three_with_double(three, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list
        else:
            # 如果开启了3.2单和3带一对，可以互压
            if room_info["threeAndDouble"] and room_info["threeAndTwoSingle"]:
                get_type_over_list = find_three_with_two_single(three, hand_cards, room_info)
                if len(get_type_over_list):
                    return get_type_over_list
    # 3带2单
    if card1_type == CardType.Lin_ThreeWithTwo:
        three = get_cards_value(pre_cards, 3)
        get_type_over_list = find_three_with_two_single(three, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list
        else:
            # 如果开启了3.2单和3带一对，可以互压
            if room_info["threeAndDouble"] and room_info["threeAndTwoSingle"]:
                get_type_over_list = find_three_with_double(three, hand_cards, room_info)
                if len(get_type_over_list):
                    return get_type_over_list
    # 牌型为顺子
    if card1_type == CardType.Com_ContinuousSingle:
        get_type_over_list = find_continuous_single(pre_cards, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list
    # 联对
    if card1_type == CardType.Com_LongDouble or card1_type == CardType.Lin_ShortDouble:
        get_type_over_list = find_continuous_double(pre_cards, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list

    # 3张飞机
    if card1_type == CardType.Spc_OnlyPlan:
        get_type_over_list = find_planeWithNone(pre_cards, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list

    # 3带1单飞机
    if card1_type == CardType.Com_PlaneWithSingle:
        get_type_over_list = find_planeWithSingle(pre_cards, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list

    # 3带一对飞机
    if card1_type == CardType.Lin_PlaneWithDouble:
        get_type_over_list = find_planWithDouble(pre_cards, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list
        else:
            # 如果开启了3.2单和3带一对，可以互压
            if room_info["threeAndDouble"] and room_info["threeAndTwoSingle"]:
                get_type_over_list = find_planeWithTwo(pre_cards, hand_cards, room_info)
                if len(get_type_over_list):
                    return get_type_over_list

    # 3带2单飞机
    if card1_type == CardType.Com_PlaneWithTwo:
        get_type_over_list = find_planeWithTwo(pre_cards, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list

    # 最大炸弹
    if card1_type == CardType.Lin_MaxBoomWithSingle or card1_type == CardType.Lin_MaxBoomForFour:
        return []
    get_type_over_list = find_max_boom_and_negative(hand_cards, room_info)
    if len(get_type_over_list):
        return get_type_over_list

    # 牌型是炸弹
    if card1_type == CardType.Lin_FourBoomWithSingle or card1_type == CardType.Lin_FourBoom:
        value_s = get_cards_value(pre_cards, 4)
        get_type_over_list = find_bigger_boom(value_s, hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list

    # 牌型不是炸弹
    if card1_type != CardType.Lin_FourBoomWithSingle and card1_type != CardType.Lin_FourBoom:
        get_type_over_list = find_boom_and_negative(hand_cards, room_info)
        if len(get_type_over_list):
            return get_type_over_list

    DEBUG_MSG("find None")
    return []


# 查找牌组的炸弹，匹配玩家手牌
# def find_boom_in_player(card, cards, room_info):
#     # 获取玩家手牌类型
#     card1 = convert_cards_to_value(card)
#     card2 = convert_cards_to_value(cards)
#     card_type = get_cards_type(card1, room_info)
#     # 如果上一家打出的牌为最大炸弹，直接返回空
#     if card_type == CardType.Lin_MaxBoomWithSingle or card_type == CardType.Lin_MaxBoomForFour:
#         return []
#
#     # 如果上家打出的是炸弹
#     if card_type == CardType.Lin_FourBoomWithSingle or card_type == CardType.Lin_FourBoom:
#         value_s = -1
#         for k in card1:
#             if card1.count(k) == 4:
#                 value_s = k
#         # 此处
#         get_type_over_list = find_bigger_boom(value_s, card2, room_info)
#         if len(get_type_over_list):
#             return get_type_over_list
#
#     # 牌型不是炸弹
#     if card_type != CardType.Lin_FourBoomWithSingle and card_type != CardType.Lin_FourBoom:
#         get_type_over_list = find_boom_and_negative(card2, room_info)
#         if len(get_type_over_list):
#             return get_type_over_list
#
#     # 直接寻找最大炸弹
#     get_type_over_list = find_max_boom_and_negative(card2, room_info)
#     if len(get_type_over_list):
#         return get_type_over_list
#     DEBUG_MSG("None")
#     return []


# 最后一手特殊牌判断,包括3张和多个3张
def is_last_shou_cards(card1, card2):
    card1 = convert_cards_to_value(card1)
    for cv in card1:
        if card1.count(cv) == 4:
            return False
    if len(card1) == len(card2):
        ite_cards = distinct_number_list(card1)
        ite_cards.sort()
        if len(ite_cards) * 3 == len(card2) and (ite_cards[0] + len(ite_cards) - 1) == ite_cards[-1]:
            return True
    return False


def remove_boom_by_info(cards, room_info):
    """
    移除手中所有炸弹
    4带1,3带1也只移除4张和3张
    """
    cards = convert_cards_to_value(cards)
    itm_list = []
    for value in cards:
        if cards.count(value) != 4:
            if room_info["boomType"] != 2:
                if value == 14 and cards.count(value) == 3:
                    continue
            itm_list.append(value)
    return itm_list


# 获取玩家手中所有炸弹（炸弹不可拆，辅助函数）
def get_boom_cards_value(card, room_info):
    card = convert_cards_to_value(card)
    itm_list = []
    for value in card:
        if value == 14 and card.count(value) == 3 and value not in itm_list:
            if room_info["boomType"] == 1 or room_info["boomType"] == 3:
                itm_list.append(value)
        if card.count(value) == 4 and value not in itm_list:
            itm_list.append(value)
    return itm_list


# 判断两个牌组是否存在相同的牌(炸弹不可拆，辅助函数,可用子集判断函数)
def is_both_have_same_card(card1, card2):
    card1 = convert_cards_to_value(card1)
    card2 = convert_cards_to_value(card2)
    for value in card1:
        if value in card2:
            return True
    return False


def find_max_boom_and_negative(card2, room_info):
    """
    查牌组中3A，如果需要带单，用-1表示
    """
    if room_info["boomType"] == 3:
        if card2.count(14) == 3:
            return [[14, 14, 14, -1]]
    if room_info["boomType"] == 1:
        if card2.count(14) == 3:
            return [[14, 14, 14]]
    return []


def find_boom_and_negative(card2, room_info):
    """
    查牌组中4张炸弹，如果需要带单，用-1表示
    """
    card_filter = set()
    itm_list = []
    if room_info["boomType"] == 3:
        for k in card2:
            if card2.count(k) == 4 and k not in card_filter:
                itm_list.append([k, k, k, k, -1])
                card_filter.add(k)
                break
        return itm_list

    for k in card2:
        if card2.count(k) == 4 and k not in card_filter:
            itm_list.append([k, k, k, k])
            card_filter.add(k)
            break
    return itm_list


def find_bigger_boom(V, card2, room_info):
    """
    查找更大炸弹
    """
    card_filter = set()
    itm_cards = []
    for k in card2:
        if room_info["boomType"] == 3:
            if k > V and card2.count(k) == 4 and k not in card_filter:
                itm_cards.append([k, k, k, k, -1])
                card_filter.add(k)
        elif card2.count(k) == 4:
            if k > V and k not in card_filter:
                itm_cards.append([k, k, k, k])
                card_filter.add(k)
    return itm_cards


def find_boom(card2, room_info):
    """
    找手中的炸弹
    """
    card_filter = set()
    itm_cards = []
    for k in card2:
        if room_info["boomType"] == 3:
            if card2.count(k) == 4 and k not in card_filter:
                itm_cards.append([k, k, k, k, -1])
                card_filter.add(k)
        elif card2.count(k) == 4:
            if k not in card_filter:
                itm_cards.append([k, k, k, k])
                card_filter.add(k)
    return itm_cards


def find_single(pre_card_val, card2, room_info):
    """
    找到手牌中大于指定牌的所有单
    单放前面
    """
    card_filter = set()
    itm_cards = []
    for k in card2:
        if k > pre_card_val and k not in card_filter and card2.count(k) == 1:
            itm_cards.append([k])
            card_filter.add(k)

    for k in card2:
        if k > pre_card_val and k not in card_filter:
            itm_cards.append([k])
            card_filter.add(k)
    return itm_cards


def find_double(pre_card_val, card2, room_info):
    """
    找到手牌大于指定牌的所有对
    对方前面
    """
    if len(card2) < 2:
        return []
    card_filter = set()
    itm_cards = []
    for k in card2:
        if k > pre_card_val and card2.count(k) == 2 and k not in card_filter:
            itm_cards.append([k, k])
            card_filter.add(k)

    for k in card2:
        if k > pre_card_val and card2.count(k) > 2 and k not in card_filter:
            itm_cards.append([k, k])
            card_filter.add(k)
    return itm_cards


def find_three(pre_card_val, card2, room_info):
    """
    找到手牌大于指定牌的所有3张
    """
    if len(card2) < 3:
        return []
    card_filter = set()
    itm_cards = []
    for k in card2:
        if pre_card_val < k and card2.count(k) >= 3 and k not in card_filter:
            itm_cards.append([k, k, k])
            card_filter.add(k)
            break
    return itm_cards


def find_three_with_single(pre_card_val, card2, room_info):
    """
    找到手牌大于指定牌的所有3张
    """
    if len(card2) < 4:
        return []
    card_filter = set()
    itm_cards = []
    for k in card2:
        if pre_card_val < k and card2.count(k) >= 3 and k not in card_filter:
            if len(card2) > 3:
                itm_cards.append([k, k, k, -1])
                card_filter.add(k)
    return itm_cards


def find_three_with_double(pre_card_val, card2, room_info):
    """
    从target_cards找出大于值v的三带对
    """
    # 找3张
    # 3,3,3 5,5,5  => 3,3,3,5,5 和 5,5,5,3,3
    card_filter = set()
    all_itm_cards = []
    for k in card2:
        if k > pre_card_val and card2.count(k) >= 3 and k not in card_filter:
            itm_cards = [k] * 3
            # 找对
            for j in card2:
                if j != k and card2.count(j) >= 2:
                    itm_cards.append(1)
                    all_itm_cards.append(itm_cards)
                    card_filter.add(k)
                    break
    return all_itm_cards


def find_three_with_two_single(pre_card_val, card2, room_info):
    """
    找所有3带2单
    """
    if len(card2) < 5:
        return []
    # 找3张
    card_filter = set()
    all_itm_cards = []
    for k in card2:
        if k > pre_card_val and card2.count(k) >= 3 and k not in card_filter:
            itm_cards = [k] * 3
            # 找2单
            two = []
            for v in card2:
                if v != k and v not in two:
                    two.append(v)
                    if len(two) == 2:
                        itm_cards += [-1] * 2
                        all_itm_cards.append(itm_cards)
                        card_filter.add(k)
                        break
    return all_itm_cards


def find_continuous_single(pre_cards, card2, room_info):
    """
    找大于指定牌的顺子
    """
    cards = distinct_number_list(card2)
    if len(cards) < len(pre_cards):
        return []

    ite_cards = []
    cards.sort()
    pre_cards.sort()
    index = 0
    length = len(pre_cards)
    while index + length <= len(cards):
        itm_cards_00 = cards[index:(index + length)]
        if itm_cards_00[-1] > pre_cards[-1] and itm_cards_00[-1] != 15:
            card_type = get_cards_type(itm_cards_00, room_info)
            if card_type == CardType.Com_ContinuousSingle:
                ite_cards.append(itm_cards_00)
        index += 1
    return ite_cards


# 寻找所有的适配
def _find_double_all(card):
    """
    找到所有含有对的牌
    """
    item_list = []
    for v in card:
        if card.count(v) >= 2 and v not in item_list:
            item_list.append(v)
    item_list.sort()
    return item_list


def find_continuous_double(card1, card2, room_info):
    """
    找大于指定牌的连对
    """
    cards_01 = distinct_number_list(card1)
    cards_02 = _find_double_all(card2)
    if len(cards_02) < len(cards_01):
        return []
    itm_cards = []
    index = 0
    length = len(cards_01)
    while index + length <= len(cards_02):
        itm_cards_00 = cards_02[index:index + length]
        if itm_cards_00[-1] != 15 and itm_cards_00[-1] > cards_01[-1]:
            if itm_cards_00[0] + len(itm_cards_00) - 1 == itm_cards_00[-1]:
                itm_cards.append(itm_cards_00 + itm_cards_00)
        index += 1
    return itm_cards


def _find_bigger_continues_single(pre_cards, card2):
    """
    查找更大的连，
    """
    itm_cards = []
    len_pre_cards = len(pre_cards)
    index = 0
    while index + len_pre_cards <= len(card2):
        itm_cards_00 = card2[index:(index + len_pre_cards)]
        if itm_cards_00[-1] != 15 and itm_cards_00[-1] > pre_cards[-1]:
            if itm_cards_00[0] + len(itm_cards_00) - 1 == itm_cards_00[-1]:
                itm_cards.append(itm_cards_00)
        index += 1
    return itm_cards


def find_planeWithNone(card1, card2, room_info):
    """
    找大于指定牌的3张飞机
    """
    if len(card2) < len(card1):
        return []
    card_1_plane = []
    card_2_plane = []
    for value_s in card1:
        if card1.count(value_s) >= 3 and value_s not in card_1_plane:
            card_1_plane.append(value_s)
    card_1_plane.sort()
    for value_s in card2:
        if card2.count(value_s) >= 3 and value_s not in card_2_plane:
            card_2_plane.append(value_s)
    card_2_plane.sort()

    itm_cards = []
    itm_cards = _find_bigger_continues_single(card_1_plane, card_2_plane)
    for v in itm_cards:
        v *= 3
    return itm_cards


def find_planeWithSingle(card1, card2, room_info):
    """
    找大于指定牌的3张带1单飞机
    """
    if len(card2) < len(card1):
        return []
    card_1_plane = []
    card_2_plane = []
    for value_s in card1:
        if card1.count(value_s) >= 3 and value_s not in card_1_plane:
            card_1_plane.append(value_s)
    card_1_plane.sort()
    for value_s in card2:
        if card2.count(value_s) >= 3 and value_s not in card_2_plane:
            card_2_plane.append(value_s)
    card_2_plane.sort()

    bigger = []
    itm_cards = _find_bigger_continues_single(card_1_plane, card_2_plane)
    for v in itm_cards:
        if len(v) * 4 <= len(card2):
            single_count = len(v)
            v *= 3
            v.extend([-1] * single_count)
            bigger.append(v)
    return bigger


def find_planWithDouble(card1, card2, room_info):
    """
    找大于指定牌的3张带对飞机
    """
    if len(card2) < len(card1):
        return []
    if len(card1) % 5 != 0:
        return []
    card_1_plane = []
    card_2_plane = []
    # 找出所有三张
    for value_s in card1:
        if card1.count(value_s) >= 3 and value_s not in card_1_plane:
            card_1_plane.append(value_s)
    card_1_plane.sort()
    for value_s in card2:
        if card2.count(value_s) >= 3 and value_s not in card_2_plane:
            card_2_plane.append(value_s)
    card_2_plane.sort()

    def find_pair_count(_cards, threes):
        # 找不含3张的对的个数
        card_filter = set()
        pair_count = 0
        for pair in _cards:
            if _cards.count(pair) >= 2 and pair not in threes and pair not in card_filter:
                pair_count += (_cards.count(pair) // 2)
                card_filter.add(pair)
        return pair_count

    bigger = []
    itm_cards = _find_bigger_continues_single(card_1_plane, card_2_plane)
    for v in itm_cards:
        # 对的个数必须够
        if find_pair_count(card2, v) >= len(v):
            _pair_count = len(v)
            v *= 3
            v.extend([1] * _pair_count)
            bigger.append(v)
    return bigger


def find_planeWithTwo(card1, card2, room_info):
    """
    找大于指定牌的3张带2单飞机
    """
    if len(card2) < len(card1):
        return []
    card_1_plane = []
    card_2_plane = []
    for value_s in card1:
        if card1.count(value_s) >= 3 and value_s not in card_1_plane:
            card_1_plane.append(value_s)
    card_1_plane.sort()

    new_card_1_plane = []
    # 移除不连续的地方
    for i in card_1_plane:
        if i + 1 not in card_1_plane and i - 1 not in card_1_plane:
            continue
        new_card_1_plane.append(i)
    card_1_plane = new_card_1_plane

    for value_s in card2:
        if card2.count(value_s) >= 3 and value_s not in card_2_plane:
            card_2_plane.append(value_s)
    card_2_plane.sort()

    bigger = []
    itm_cards = _find_bigger_continues_single(card_1_plane, card_2_plane)
    for v in itm_cards:
        # 单的个数必须够
        if len(v) * 5 <= len(card2):
            single_count = 2 * len(v)
            v *= 3
            v.extend([-1] * single_count)
            bigger.append(v)
    return bigger


def _compare_cards(cards1, cards2, card_type):
    """
    同牌型比较
    必须是同牌型，同长度
    """
    if len(cards1) != len(cards2):
        return False
    if CardType.Com_ContinuousSingle == card_type:
        # 顺子
        if get_cards_value(cards1, 1) > get_cards_value(cards2, 1):
            return True
    elif card_type == CardType.Com_LongDouble or card_type == CardType.Lin_ShortDouble:
        # 大小联对
        if get_cards_value(cards1, 2) > get_cards_value(cards2, 2):
            return True
        return False
    elif card_type == CardType.Lin_FourWithThreeSingle or card_type == CardType.Lin_FourWithTwoSingle:
        # 四带二和四带三
        if get_cards_value(cards1, 4) > get_cards_value(cards2, 4):
            return True
        return False
    elif card_type == CardType.Com_Double:
        # 对子
        if get_cards_value(cards1, 2) > get_cards_value(cards2, 2):
            return True
        return False
    elif card_type == CardType.Com_Single:
        # 单张
        if cards1[0] > cards2[0]:
            return True
        return False
    elif card_type == CardType.Spc_OnlyThree \
            or card_type == CardType.Com_ThreeWithSingle \
            or card_type == CardType.Lin_ThreeWithDouble \
            or card_type == CardType.Lin_ThreeWithTwo:
        # 3带
        if get_cards_value(cards1, 3) > get_cards_value(cards2, 3):
            return True
        return False
    elif card_type == CardType.Spc_OnlyPlan:
        # 3张飞机，3带对飞机
        if get_cards_value(cards1, 3) > get_cards_value(cards2, 3):
            return True
        return False
    elif card_type == CardType.Com_PlaneWithSingle \
            or card_type == CardType.Lin_PlaneWithDouble \
            or card_type == CardType.Com_PlaneWithTwo:
        # 带的牌里面也可能有3张，需要先找出飞机，再比较大小
        three_dai_count = 5
        if card_type == CardType.Com_PlaneWithSingle:
            three_dai_count = 4

        three_cards1 = []
        three_cards2 = []
        is_plane(cards1, three_dai_count, three_cards1)
        is_plane(cards2, three_dai_count, three_cards2)
        if three_cards1 and three_cards2 and three_cards1[-1] > three_cards2[-1]:
            return True
        return False
    return False


# 比较两牌型大小 1>2 True or 1<2 False（待优化）
def compare_cards(_cards1, _cards2, room_info):
    # 拿到牌型
    # 规则 Lin_MaxBoomForFour 和 Lin_MaxBoomWithSingle 为最大
    # 不同牌型无法比较
    cards1_type = get_cards_type(_cards1, room_info)
    cards2_type = get_cards_type(_cards2, room_info)
    cards1 = convert_cards_to_value(_cards1)
    cards2 = convert_cards_to_value(_cards2)
    DEBUG_MSG("compare_cards cards1:%s %s cards2:%s %s " % (cards1, cards1_type, cards2, cards2_type))

    # 任何一组牌为无效组合就返回空
    if cards1_type == CardType.Com_Invalid or cards2_type == CardType.Com_Invalid:
        return None

    # 最大炸弹首先过滤
    if cards1_type == CardType.Lin_MaxBoomForFour or cards1_type == CardType.Lin_MaxBoomWithSingle:
        return True
    if cards2_type == CardType.Lin_MaxBoomForFour or cards2_type == CardType.Lin_MaxBoomWithSingle:
        return False

    # 任意一方为特殊炸弹 或者是普通炸弹
    if (CardType.Lin_FourBoomWithSingle == cards1_type or CardType.Lin_FourBoom == cards1_type) \
            or (CardType.Lin_FourBoomWithSingle == cards2_type or CardType.Lin_FourBoom == cards2_type):
        if cards1_type == cards2_type:
            # 双方都为炸弹
            if get_cards_value(cards1, 4) > get_cards_value(cards2, 4):
                return True
        else:
            # 一方为炸弹
            if cards1_type == CardType.Lin_FourBoomWithSingle or cards1_type == CardType.Lin_FourBoom:
                return True
        return False

    # 长度比较
    if len(cards1) != len(cards2):
        return False

    if cards1_type == cards2_type:
        return _compare_cards(cards1, cards2, cards1_type)
    else:
        if room_info["threeAndDouble"] and room_info["threeAndTwoSingle"]:
            # 3带2、3带对都开时，可以胡压
            if (cards1_type == CardType.Lin_ThreeWithTwo or cards1_type == CardType.Lin_ThreeWithDouble) \
                    and (cards2_type == CardType.Lin_ThreeWithTwo or cards2_type == CardType.Lin_ThreeWithDouble):
                if get_cards_value(cards1, 3) > get_cards_value(cards2, 3):
                    return True
            elif (cards1_type == CardType.Com_PlaneWithTwo or cards1_type == CardType.Lin_PlaneWithDouble) \
                    and (cards2_type == CardType.Com_PlaneWithTwo or cards2_type == CardType.Lin_PlaneWithDouble):
                if get_cards_value(cards1, 3) > get_cards_value(cards2, 3):
                    return True
    return False


# 转化牌值
def convert_cards_to_value(cards):
    it_men_card = []
    for i in cards:
        it_men_card.append(int(i))
    it_men_card.sort()
    return it_men_card


# 获取玩家出牌的类型
def get_cards_type(correct_cards, card_type):
    """
    牌型判断
    3带1,3带2单等牌型根据设置判断
    result: int
    """
    # 转换牌值
    cards = convert_cards_to_value(correct_cards)
    cards = convert_cards_to_value(correct_cards)
    # DEBUG_MSG("get_cards_type card:%s" % cards)
    length = len(cards)
    if not length:
        return CardType.Com_Invalid  # 无效牌
    if length == 1:
        return CardType.Com_Single  # 单张
    elif length == 2:  # 一对
        if cards.count(cards[-1]) > 1:
            return CardType.Com_Double  # 一对
        return CardType.Com_Invalid  # 无效牌
    elif length == 3:
        if cards.count(cards[0]) == 3:
            if card_type["boomType"] == 1:
                if cards.count(14) == 3:
                    return CardType.Lin_MaxBoomForFour  # AAA炸弹
            if card_type["haveThree"]:  # haveThree
                return CardType.Spc_OnlyThree  # 三张不带
        return CardType.Com_Invalid  # 无效牌
    elif length == 4:
        # AAA为炸弹时，不能作为3带1出（炸弹不可拆？）
        if cards.count(14) == 3:
            if card_type["boomType"] == 3:
                # aaa.1为炸弹
                return CardType.Lin_MaxBoomWithSingle  # AAA炸弹带一
            # elif card_type["boomType"] == 1:
            #     # aaa为炸弹
            #     return CardType.Com_Invalid
        # 炸弹
        if cards.count(cards[0]) == 4:
            if card_type["boomType"] == 1 or card_type["boomType"] == 2:
                return CardType.Lin_FourBoom  # 炸弹四张
            else:
                return CardType.Spc_OnlyFour  # 四张(此牌型只在四代一为炸弹下使用)
        # 三带一
        if cards.count(cards[0]) == 3 or cards.count(cards[1]) == 3:
            if card_type["threeAndOne"]:
                return CardType.Com_ThreeWithSingle  # 三带一
            else:
                return CardType.Com_Invalid  # 无效牌
        # 二联对
        if card_type["doubleCount"] == 2:
            cards.sort()
            if cards.count(cards[0]) == cards.count(cards[-1]) and cards[0] + 1 == cards[-1]:
                return CardType.Lin_ShortDouble  # 短连对
        return CardType.Com_Invalid  # 无效牌

    elif length == 5:
        cards.sort()
        # 顺子
        if is_continuous_single(cards):
            return CardType.Com_ContinuousSingle  # 顺子
        # 四带一
        if cards.count(cards[0]) == 4 or cards.count(cards[-1]) == 4:
            if card_type["boomType"] == 3:
                return CardType.Lin_FourBoomWithSingle  # 四带一炸弹
        # 三带二
        if cards.count(cards[0]) == 3 or cards.count(cards[1]) == 3 or cards.count(cards[2]) == 3:
            # if card_type["boomType"] == 3 or card_type["boomType"] == 1:
            #     if cards.count(14) == 3:
            #         return CardType.Com_Invalid
            # 最后一张牌有两张，三带一对
            if card_type['threeAndDouble'] and (cards.count(cards[0]) == 2 or cards.count(cards[-1]) == 2):
                return CardType.Lin_ThreeWithDouble  # 三带一对
            # 最后两张牌只有一张,三带两单
            if card_type['threeAndTwoSingle'] and (cards.count(cards[0]) == 1 or cards.count(cards[-1]) == 1):
                return CardType.Lin_ThreeWithTwo  # 3带2
        return CardType.Com_Invalid
    elif length > 5:
        # 顺子
        if is_continuous_single(cards):
            return CardType.Com_ContinuousSingle  # 顺子
        # 连对
        elif is_continuous_double(cards):
            return CardType.Com_LongDouble  # 长联对
        # 飞机(默认)
        elif is_plane_with_nothing(cards) and card_type["haveThree"]:
            return CardType.Spc_OnlyPlan  # 飞机不带（此牌型只在最后一手牌判断使用）
        elif is_plane_with_single(cards) and card_type["threeAndOne"]:
            return CardType.Com_PlaneWithSingle  # 默认3带1飞机
        # 飞机（规则）
        elif is_plane_with_double(cards) and card_type["threeAndDouble"]:
            return CardType.Lin_PlaneWithDouble  # 3带对飞机
        elif is_plane_with_two(cards) and card_type["threeAndTwoSingle"]:
            return CardType.Com_PlaneWithTwo  # 3带2飞机
        # # 3带2张任意牌飞机
        # elif is_plane_with_two_any(cards) and (card_type["threeAndDouble"] and card_type["threeAndTwoSingle"]):
        #     return CardType.Com_PlaneWithTwo
        # 四带二
        elif is_four_with_two(cards) and card_type["fourAndDouble"]:
            return CardType.Lin_FourWithTwoSingle  # 四带二
        # 四带三
        elif is_four_with_three(cards) and card_type["fourAndThree"]:
            return CardType.Lin_FourWithThreeSingle  # 四带三
        else:
            return CardType.Com_Invalid  # 无效牌


# 以下为牌型判断函数
# 是否为顺子
def is_continuous_single(cards):
    len_s = len(cards)
    it_men_card = distinct_number_list(cards)
    if len(it_men_card) == len_s:
        if it_men_card[0] + len_s - 1 == it_men_card[-1] and it_men_card[-1] != 15 and it_men_card[0] != 15:
            return True
    return False


# 是否为连对
def is_continuous_double(cards):
    it_men_card = distinct_number_list(cards)
    if not is_continuous_single(it_men_card):
        return False

    for v in it_men_card:
        if cards.count(v) != 2:
            return False
    return True


# 飞机判断，3,3带1,3带2判断
def is_plane(cards, three_and_dai_count, three_cards=None):
    if 3 > three_and_dai_count > 5:
        return False
    # 查看牌数量是否合适
    count = len(cards) % three_and_dai_count
    if count > 0:
        return False
    plane_count = len(cards) // three_and_dai_count
    if plane_count < 2:
        return False

    # 找顺子个数
    card_list = []
    for k in cards:
        if cards.count(k) >= 3 and k not in card_list:
            card_list.append(k)
    if len(card_list) < plane_count:
        return False

    def get_continues_count(distinct_cards, v):
        # 取V开始的顺子长度
        _count = 0
        card_len = len(distinct_cards)
        for i in range(card_len):
            if v in distinct_cards:
                v += 1
                _count += 1
                continue
            break
        return _count

    def get_max_continues_count(distinct_cards):
        # 查从几开始顺子最长
        _max_count = 0
        max_v = 0
        for v in distinct_cards:
            tmp_count = get_continues_count(distinct_cards, v)
            if tmp_count >= _max_count:
                _max_count = tmp_count
                max_v = v
        return _max_count, max_v

    # 取最大连续个数
    max_count, start_val = get_max_continues_count(card_list)
    if max_count < plane_count:
        return False

    # 组织返回3张的值
    if three_cards is not None:
        if max_count > plane_count:
            start_val += (max_count - plane_count)
        for i in range(plane_count):
            three_cards.append(start_val + i)
    return True


def is_plane_with_nothing(cards):
    """
    飞机不带翅膀
    :param cards:
    :return:
    """
    if is_plane(cards, 3):
        return True
    return False


def is_plane_with_single(cards):
    """
    飞机带单
    2单可以是一对
    :param cards:
    :return:
    """
    if is_plane(cards, 4):
        return True
    return False


def is_plane_with_two(cards):
    """
    3带2飞机
    2单可以是一对
    :param cards:
    :return:
    """
    three_cards = []
    if is_plane(cards, 5, three_cards):
        return True
    return False


# 是否为3带对飞机
def is_plane_with_double(cards):
    three_cards = []
    if is_plane(cards, 5, three_cards):
        double_count = len(three_cards)
        # 找有几个对
        tmp_count = 0
        for v in cards:
            if v not in three_cards and cards.count(v) == 2:
                tmp_count += 1
        tmp_count /= 2
        if double_count == tmp_count:
            return True
    return False


def is_plane_with_two_single(cards):
    # 3带2张单
    # 单不能是对
    three_cards = []
    if is_plane(cards, 5, three_cards):
        single_count = len(three_cards) * 2
        # 找有几个单
        tmp_count = 0
        for v in cards:
            if v not in three_cards and cards.count(v) == 1:
                tmp_count += 1
        if single_count == tmp_count:
            return True
    return False


# 是否为四带二
def is_four_with_two(cards):
    for k in cards:
        if cards.count(k) == 4 and len(cards) == 6:
            return True
    return False


# 是否为四带三
def is_four_with_three(cards):
    for k in cards:
        if cards.count(k) == 4 and len(cards) == 7:
            return True
    return False


def get_cards_value(cards, count):
    """
    取牌中个数为count的最大值
    """
    value = 0
    for v in cards:
        if cards.count(v) == count:
            if value < v:
                value = v
    return value


# # 牌型辅助函数
# def get_value_c1_and_c2_max(card1, card2, number):
#     if len(card1) != len(card2):
#         return False
#     value_01 = -1
#     value_02 = -1
#     for K in card1:
#         if card1.count(K) == number:
#             value_01 = K
#     for V in card2:
#         if card2.count(V) == number:
#             value_02 = V
#     if -1 != value_01 and -1 != value_02:
#         if value_01 > value_02:
#             return True
#         return False
#     return None


# 将牌组序列化(可用set()代替此函数,序列结果为集合)结果为list
def distinct_number_list(card):
    item_list = []
    for v in card:
        if card.count(v) == 1:
            item_list.append(v)
        else:
            if v not in item_list:
                item_list.append(v)
    item_list.sort()
    return item_list


# 将固定牌移除，确保1是2的子集,否则返回结果为None
# 判断时不可转值化，否则会出现异常
def remove_c_list_from_p_list(c_card, p_card):
    # 判定是不是子集
    if set(p_card) < set(c_card):
        return None
    # 如果是子集
    itm_list = []
    for v in p_card:
        if v not in c_card:
            itm_list.append(v)
    return itm_list


# 统计手牌普通炸弹数量
def get_boom_number(card1, room_info):
    itm_list = get_boom_cards_value(card1, room_info)
    if len(itm_list):
        if 14 not in itm_list:
            return 1, len(itm_list)
        return 10, len(itm_list)
    else:
        return -1, 0


def find_no_single_cards(card, room_info):
    """
    查找非单张牌型的牌
    """
    get_card_in_players = []
    send_card_in_player = []
    # 将牌转化成判断值
    card_value = convert_cards_to_value(card)
    # 寻找最大炸弹
    get_card_in_players = find_max_boom_and_negative(card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    get_card_in_players = find_boom_and_negative(card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    get_card_in_players = find_bigger_boom(0, card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    get_card_in_players = find_three_with_single(0, card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    get_card_in_players = find_double(0, card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    get_card_in_players = find_three_with_double(0, card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    return send_card_in_player


# 转化成牌面
def change_to_card(itm_list, card_list, room_info):
    item_card_list = change_to_card_for_one(itm_list[-1], card_list, room_info)
    return item_card_list


def change_to_card_for_one(one_list, card_list, room_info):
    """
    整型换算成具体牌
    3带-1，换算成一个单张牌
    """

    def move_one_card(src_list, dest_list, int_val):
        """
        根据3，把3.1从一个列表移动到另一个列表
        """
        for val in src_list:
            if int_val == int(val):
                src_list.remove(val)
                dest_list.append(val)
                return True
        return False

    # 找整数对应的牌 3 -》 3.1
    item_card_list = []
    common_list = copy.deepcopy(card_list)
    for v in one_list:
        if v >= 3:
            move_one_card(common_list, item_card_list, v)

    # 找3带1中带的牌， -1：单； 1：对； 不能拆炸弹
    if room_info["bombCannotSeparate"]:
        # 将玩家的手牌移除四张
        tmp_list = []
        card_filter = set(remove_boom_by_info(common_list, room_info))
        for v in common_list:
            if int(v) in card_filter:
                tmp_list.append(v)
        common_list = tmp_list

    # 对
    added_count = 0
    pair_count = one_list.count(1)
    if pair_count > 0:
        common2_list = convert_cards_to_value(common_list)
        finded_cards = find_double(0, common2_list, room_info)
        cards_filter = set(one_list)
        for i in range(pair_count):
            for arr_v in finded_cards:
                if arr_v[0] not in cards_filter:
                    move_one_card(common_list, item_card_list, arr_v[0])
                    move_one_card(common_list, item_card_list, arr_v[0])
                    added_count += 1
                    break
    if added_count != pair_count:
        return []

    # 单
    added_count = 0
    single_count = one_list.count(-1)
    if single_count > 0:
        common2_list = convert_cards_to_value(common_list)
        finded_cards = find_single(0, common2_list, room_info)
        cards_filter = set(one_list)
        for i in range(single_count):
            for arr_v in finded_cards:
                if arr_v[0] not in cards_filter:
                    move_one_card(common_list, item_card_list, arr_v[0])
                    cards_filter.add(arr_v[0])
                    added_count += 1
                    break
    if added_count != single_count:
        return []
    return item_card_list


def find_one_boom(card, room_info):
    """
    查找任何炸弹
    """
    get_card_in_players = []
    send_card_in_player = []
    # 将牌转化成判断值
    card_value = convert_cards_to_value(card)
    # 寻找最大炸弹
    get_card_in_players = find_max_boom_and_negative(card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    get_card_in_players = find_boom_and_negative(card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    get_card_in_players = find_bigger_boom(0, card_value, room_info)
    if len(get_card_in_players):
        send_card_in_player = change_to_card(get_card_in_players, card, room_info)
        return send_card_in_player
    return send_card_in_player
