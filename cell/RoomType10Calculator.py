# 生成牌
import random


def generate_cards():
    """
    生成52张牌
    :return:
    """
    # 黑红梅方
    card_type = ["a", "b", "c", "d"]
    # 13 个数字
    card_num = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    card_pairs = []
    for card_color in card_type:
        for num in card_num:
            card_pairs.append(card_color + str(num))

    random.shuffle(card_pairs)
    random.shuffle(card_pairs)

    return card_pairs


def compare_cards(cards1, cards2, banker_arg_index=-1):
    """
    比牌，返回值为胜者的Index
    例如：cards1 获胜返回 1，cards2 获胜返回 2，平局返回 0,比牌失败 -1
    :param banker_arg_index: 第几个参数是庄家的牌
    :param cards1:
    :param cards2:
    :return:
    """
    # 牌值长度必须为2
    if len(cards1) != 2 or len(cards2) != 2:
        return -1
    # 获取牌的点数
    cards1_weights = get_cards_weights(cards1)
    cards2_weights = get_cards_weights(cards2)
    # 返回
    if cards1_weights < cards2_weights:
        return 2
    elif cards2_weights < cards1_weights:
        return 1
    else:
        # 平局算庄家大
        if banker_arg_index != -1:
            return banker_arg_index
        return 0


def get_cards_weights(cards):
    # 获取牌的大小
    cards_int_1 = int(cards[0][1:])
    cards_int_2 = int(cards[1][1:])
    # 相加取个位数
    cards_weights = str(get_card_value(cards_int_1) + get_card_value(cards_int_2))[-1:]
    return int(cards_weights)


def get_card_value(card_int):
    # 获取牌的点数
    if card_int == 10:
        card_int = 0
    elif card_int > 10:
        card_int = 1
    return card_int


def get_total_result(result):
    """
    通过比牌结果获取该区域输赢
    :param result: 结果
    :return:
    """
    if result == 2:
        return 'winArea'
    elif result == 1:
        return "loseArea"
    else:
        return "drawArea"
