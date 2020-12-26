import datetime
import random
from random import shuffle


def compare_cards_widget(cards1, cards2):
    """
    比牌
    """
    widget_1 = get_cards_widget(cards1)
    widget_2 = get_cards_widget(cards2)
    if widget_1 > widget_2:
        return 1
    elif widget_1 < widget_2:
        return 2
    else:
        return 0


def get_cards_widget(cards: []):
    """
    获取牌的大小权值
    """
    if cards_busted(cards):
        return -1
    if cards_is_five_dragon(cards):
        return 10000
    if cards_is_five_min(cards):
        return 1000
    if cards_is_ten_half(cards):
        return 100
    return get_cards_score(cards)


def get_cards_score(cards: []):
    """
    获取手牌点数
    """
    _sum = 0.0
    for i in cards:
        number = get_card_number(i)
        if number > 10:
            score = 0.5
        else:
            score = number
        _sum += score
    return _sum


def cards_busted(cards: []):
    """
    是否爆牌(大于十点半)
    """
    return get_cards_score(cards) > 10.5


def cards_is_ten_half(cards: []):
    """
    是否是十点半(点数等于十点半)
    """
    return get_cards_score(cards) == 10.5


def cards_is_five_dragon(cards: []):
    """
    天王(五张牌并且点数等于十点半)
    """
    return get_cards_score(cards) <= 10.5 and len(cards) == 5


def cards_is_five_min(cards: []):
    """
    五小(五张牌并且点数小于十点半)
    """
    return get_cards_score(cards) < 10.5 and len(cards) == 5


def get_card_number(card: int):
    """
    获取牌的数字
    """
    return int(card / 4)


def generate_cards_lib():
    """
    生成玩家手牌
    """
    _cards_lib = list(range(0, 52))
    return _cards_lib


def random_shuffle_cards_lib(cards_lib):
    """
    洗牌
    """
    shuffle(cards_lib)
    shuffle(cards_lib)
    for i in range(8):
        shuffle_cards_by_time(cards_lib)


def shuffle_cards_by_time(_chapter_lib):
    """
    根据时间戳洗洗牌，前X张牌,放在最后
    :param _chapter_lib:
    :return:
    """
    # 取当前时间
    ms_val = datetime.datetime.now().microsecond
    if ms_val > 1000:
        ms_val //= 1000
    pai_val = (ms_val % 10) + 10
    pull_pais = _chapter_lib[:pai_val]
    del _chapter_lib[:pai_val]
    _chapter_lib.extend(pull_pais)
