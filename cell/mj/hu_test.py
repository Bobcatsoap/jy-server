import time

import mj.MohjangCalculator


def hu_tip(hand_cards, play_card):
    """
    胡牌提示
    :param play_card:
    :return:
    """
    tip_cards = []
    can_hu_range = can_hu_cards_range(hand_cards)
    # 1.移除要出的牌      2.加入任意牌     3.移除杠牌      4.判断能不能胡    5.判断能不能次
    if play_card in hand_cards:
        # 移除要出的牌
        hand_cards.remove(play_card)
        # 加入任意牌
        for card in can_hu_range:
            # cards_type = []
            temp = hand_cards.copy()
            temp.append(card)
            # 平胡
            _can_hu = can_hu(temp)
            if _can_hu:
                tip_cards.append(card)

    # 检查是否胡任意牌，如果胡任意牌,胡牌提示中加20张红中
    if hu_anything(tip_cards, hand_cards, can_hu_range):
        for i in range(34):
            tip_cards.append(i)

    print(tip_cards)


def hu_anything(tip_cards, hand_cards, card_range):
    """
    胡任意牌前提：
    1.相关的牌都在胡牌提示里
    2.相关的牌中有红中
    3.开启红中赖子
    :param card_range:
    :param tip_cards:
    :return:
    """
    new_card_range = card_range.copy()
    for i in new_card_range:
        if hand_cards.count(i) == 3:
            new_card_range.remove(i)

    if 31 not in new_card_range:
        return False
    for c_r in new_card_range:
        if c_r not in tip_cards:
            return False
    return True


def can_hu(cards, cards_type=None, origin_cards=None):
    """
    判胡
    :param origin_cards: 红中癞子
    :param cards_type:
    :param cards:
    :return:
    """
    magic_red_switch = True
    can_hu_range = can_hu_cards_range(cards)
    ret = mj.MohjangCalculator.is_hu_pai(cards, can_hu_range,
                                         magic_red=magic_red_switch)
    hu = ret[0]
    hu_type = ret[1]
    # 原始牌，红中癞子开启时，变为能胡牌的牌型，七星胡时无意义
    red_cards = ret[2]
    # 引用传递胡牌类型
    # if cards_type is not None:
    #     cards_type=[hu_type]
    if origin_cards is not None:
        origin_cards = red_cards
    if hu:
        # 只有平胡判断二五八将
        # if hu_type == 0:
        #     if j_258(cards, red_cards):
        #         return True
        #     else:
        #         return False
        return True
    return False


def can_hu_cards_range(hand_cards):
    """
    可能跟手牌有关系的牌列表
    :param hand_cards:
    :return:
    """
    magic_red_switch = True
    hand_cards = mj.MohjangCalculator.analyse(hand_cards)
    card_range = []
    mj.MohjangCalculator.select_perhaps_pai(hand_cards, card_range, magic_red_switch)
    for i in range(27, 33):
        if i == 31:
            continue
        if i not in card_range:
            card_range.append(i)
    return card_range


def j_258(cards, red_cards):
    """
    是否满足258将判断
    :param red_cards: 如果有红中癞子，该参数为红中癞子变为胡牌牌型后的牌列表,如果红中赖子关闭，cards=red_cards
    :param cards:
    :return:
    """
    magic_red_switch = True
    _258 = [1, 4, 7, 10, 13, 16, 19, 22, 25]
    # 红中赖子，红中也满足二五八将
    if magic_red_switch:
        for _r in red_cards:
            for i in _258:
                if _r and _r.count(i) == 2:
                    return True
    else:
        for i in _258:
            if cards and cards.count(i) == 2:
                return True
    return False


hand_cards = [19, 20, 20, 22, 23, 24, 24, 24, 25, 26, 26, 26, 31, 18]
start = time.time()
# for i in hand_cards:
print(hu_tip(hand_cards, 18))
end = time.time()
print(end - start)
