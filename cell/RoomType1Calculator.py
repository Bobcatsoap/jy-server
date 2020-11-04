# -*- coding: utf-8 -*-


def convert_to_weight(cards):
    # 转变权值 A 0~3---->52~55
    for i in range(0, len(cards)):
        # if cards[i] >= 0 and cards[i] <= 3:
        if 0 <= cards[i] <= 3:
            cards[i] += 52


def convert_to_num(cards):
    # 转变权值 A 52~55---->0~3
    for i in range(0, len(cards)):
        if 52 <= cards[i] <= 55:
            cards[i] -= 52


def type_of_cards(cards, room_info):
    """
    牌型判断
    :param room_info:
    :param cards:
    :return:
    """
    if len(cards) != 3:
        return
    # 转变权值
    convert_to_weight(cards)
    # 排序
    cards.sort()
    _card_1 = int(cards[0] / 4)
    _card_2 = int(cards[1] / 4)
    _card_3 = int(cards[2] / 4)
    _color_1 = cards[0] % 4
    _color_2 = cards[1] % 4
    _color_3 = cards[2] % 4
    if _card_1 == _card_2 and _card_1 == _card_3:
        # 豹子
        _ret = 100
    elif _color_1 == _color_2 and _color_1 == _color_3:
        if _card_1 + 1 == _card_2 and _card_2 + 1 == _card_3:
            # 顺金
            _ret = 99
        # 1、2、3 顺金
        elif _card_1 == 1 and _card_2 == 2 and _card_3 == 13:
            _ret = 99
        else:
            # 1 如果勾选顺子大于金花
            if room_info["straightBigSameColor"]:
                # 金花
                _ret = 97
            # 1 如果没有勾选顺子大于金花  金花要大于顺子
            else:
                _ret = 98

    # 1 只是顺子牌型
    elif _card_1 + 1 == _card_2 and _card_2 + 1 == _card_3:
        # 顺子   且如果勾选顺子大于金花
        if room_info["straightBigSameColor"]:
            # 1 判断是QKA置权值更高
            if _card_1 == 11 and _card_2 == 12 and _card_3 == 13:
                _ret = 98.7
            # 顺子
            else:
                _ret = 98
        else:
            # 1 如果没有勾选顺子大于金花  金花要大于顺子  顺子就等于97
            # 1 判断是QKA置权值更高
            if _card_1 == 11 and _card_2 == 12 and _card_3 == 13:
                _ret = 97.7
            else:
                _ret = 97
    # 如果是牌是A23且勾选了顺子大于金花    A23>JQK   顺子此时为 98   那么牌型权值为98.5  A23  大于顺子  97
    elif _card_1 == 1 and _card_2 == 2 and _card_3 == 13:
        # 1 如果勾选顺子大于金花
        if room_info["straightBigSameColor"]:
            # 1 如果勾选123大于JQK
            if room_info["attStraightBigJqk"]:
                _ret = 98.5
            else:
                _ret = 97.5
        # 1 没有勾选顺子大于金花  顺子此时97
        else:
            # 1 如果勾选123大于JQK
            if room_info["attStraightBigJqk"]:
                _ret = 97.5
            else:
                _ret = 96.5
    elif _card_1 == _card_2 or _card_2 == _card_3:
        # 对子
        _ret = 96
    else:
        # 单张
        _ret = 95
    # 还原
    convert_to_num(cards)
    # 排序
    cards.sort()
    return _ret


def compare_card(cards1, cards2, room_info, is_manual_compare=False):
    """
    比较两组牌的大小
    :param room_info:
    :param cards1:
    :param cards2:
    :return: 1 0 -1
    """
    if len(cards1) != 3 or len(cards2) != 3:
        if len(cards1) != 3:
            return -1
        elif len(cards2) != 3:
            return 1
        else:
            return 0
    _type_1 = type_of_cards(cards1, room_info)
    _type_2 = type_of_cards(cards2, room_info)
    # 转变权值
    convert_to_weight(cards1)
    convert_to_weight(cards2)
    # 对手里的牌排序
    cards1.sort()
    cards2.sort()
    # 比较大小
    _cards1_list = []
    _cards2_list = []
    # 将转换后的牌放进列表里
    _cards_1_1 = int(cards1[0] / 4)
    _cards1_list.append(_cards_1_1)

    _cards_1_2 = int(cards1[1] / 4)
    _cards1_list.append(_cards_1_2)

    _cards_1_3 = int(cards1[2] / 4)
    _cards1_list.append(_cards_1_3)

    _cards_2_1 = int(cards2[0] / 4)
    _cards2_list.append(_cards_2_1)

    _cards_2_2 = int(cards2[1] / 4)
    _cards2_list.append(_cards_2_2)

    _cards_2_3 = int(cards2[2] / 4)
    _cards2_list.append(_cards_2_3)
    _ret = 0
    # 111   等于1 的是发起比牌的人赢  等于-1是被比牌的人赢
    if _type_1 > _type_2:
        # 1 如果发起比牌的人是豹子  被比牌的人是单张
        if _type_1 == 100 and _type_2 == 95:
            # 1如果勾选了235大豹子
            if room_info["twoThreeFiveBigLeopard"]:
                # 如果被比牌的人是235
                if _cards_2_1 == 1 and _cards_2_2 == 2 and _cards_2_3 == 4:
                    _ret = -1
                else:
                    _ret = 1
                #   还原
                convert_to_num(cards1)
                convert_to_num(cards2)
                # 排序
                cards1.sort()
                cards2.sort()
                return _ret
            # 1 没有勾选 235 > 豹子
            else:
                _ret = 1
            #   还原
            convert_to_num(cards1)
            convert_to_num(cards2)
            # 排序
            cards1.sort()
            cards2.sort()
            return _ret
        else:
            _ret = 1
        #   还原
        convert_to_num(cards1)
        convert_to_num(cards2)
        # 排序
        cards1.sort()
        cards2.sort()
        return _ret
    elif _type_1 < _type_2:
        # 1 如果发起比牌的人是单张且第二个人是豹子
        if _type_1 == 95 and _type_2 == 100:
            # 1如果勾选了235大豹子
            if room_info["twoThreeFiveBigLeopard"]:
                if _cards_1_1 == 1 and _cards_1_2 == 2 and _cards_1_3 == 4:
                    _ret = 1
                else:
                    _ret = -1
                #   还原
                convert_to_num(cards1)
                convert_to_num(cards2)
                # 排序
                cards1.sort()
                cards2.sort()
                return _ret
            else:
                _ret = -1
            #   还原
            convert_to_num(cards1)
            convert_to_num(cards2)
            # 排序
            cards1.sort()
            cards2.sort()
            return _ret
        else:
            _ret = -1
        #   还原
        convert_to_num(cards1)
        convert_to_num(cards2)
        # 排序
        cards1.sort()
        cards2.sort()
        return _ret
    # 1 牌型相等的情况
    else:
        # 如果两个人都是对子
        if _type_1 == _type_2 == 96:
            # 找到两个人的对子  两个人的对子肯定都是列表中的第二张牌
            _cards_1_dui = _cards1_list[1]
            _cards_2_dui = _cards2_list[1]
            # 1找出第一个人的单张
            for i in range(len(_cards1_list)):
                if _cards1_list[i] != _cards_1_dui:
                    _cards_1_dan = _cards1_list[i]
            # 1 找出第二个人的单张
            for i in range(len(_cards2_list)):
                if _cards2_list[i] != _cards_2_dui:
                    _cards_2_dan = _cards2_list[i]
            if _cards_1_dui > _cards_2_dui:
                _ret = 1
            # 1 第二个人的对子大
            elif _cards_1_dui < _cards_2_dui:
                _ret = -1
            # 1 两个人的对子相等 判断两个人的单张
            else:
                if _cards_1_dan > _cards_2_dan:
                    _ret = 1
                elif _cards_1_dan < _cards_2_dan:
                    _ret = -1
                # 两个人的牌都一样判断比最大的那张牌的花色
                else:
                    # 如果是手动比牌，并且开启了先比者输，则cards1输
                    if is_manual_compare and 'sameCardCompare' in room_info and room_info['sameCardCompare'] == 1:
                        return -1
                    if cards1[2] % 4 < cards2[2] % 4:
                        _ret = 1
                    else:
                        _ret = -1
            #   还原
            convert_to_num(cards1)
            convert_to_num(cards2)
            # 排序
            cards1.sort()
            cards2.sort()
            return _ret

        if _cards_1_1 == 1 and _cards_1_2 == 2 and _cards_1_3 == 13:
            _cards_1_3 = 0

        if _cards_2_1 == 1 and _cards_2_2 == 2 and _cards_2_3 == 13:
            _cards_2_3 = 0

        # 1 比第三张牌的大小
        if _cards_1_3 > _cards_2_3:
            _ret = 1
        elif _cards_1_3 < _cards_2_3:
            _ret = -1
        # 1 第三张牌相等
        else:
            # 比第二张牌
            if _cards_1_2 > _cards_2_2:
                _ret = 1
            elif _cards_1_2 < _cards_2_2:
                _ret = -1
            # 第二张牌还相等
            else:
                if _cards_1_1 > _cards_2_1:
                    _ret = 1
                elif _cards_1_1 < _cards_2_1:
                    _ret = -1
                #第三张牌还相等 比最大这张牌的花色
                else:
                    # 如果是手动比牌，并且开启了先比者输，则cards1输
                    if is_manual_compare and 'sameCardCompare' in room_info and room_info['sameCardCompare'] == 1:
                        return -1
                    if cards1[2] % 4 < cards2[2] % 4:
                        _ret = 1
                    else:
                        _ret = -1
    # 还原
    convert_to_num(cards1)
    convert_to_num(cards2)
    # 排序
    cards1.sort()
    cards2.sort()
    return _ret


def get_good_pai(all_cards, room_info):
    if len(all_cards) == 0:
        return -1

    max_index = 0
    max_cards = all_cards[max_index]
    for k in range(1, len(all_cards)):
        if compare_card(all_cards[k], max_cards, room_info) == 1:
            max_cards = all_cards[k]
            max_index = k
    return max_index

# 对子
# print(typeofCard([9,10,37]))
# print(typeofCard([6,33,34]))
# print(compareCard([9,10,37],[6,33,34]))
# 顺子
# print(typeofCard([47,49,0]))
# print(typeofCard([46,50,1]))
# print(compareCard([47,49,0],[46,50,1]))

# 带1的和单张
# print(typeofCard([6,33,34]))
# print(typeofCard([36,37,38]))
# print(compareCard([6,33,38],[36,46,2]))

# print(typeofCard([37,38,25]))
# print(typeofCard([6,33,34]))
# print(compareCard([37,38,25],[6,33,34]))
