import re

"""
斗地主ai辅助函数
"""

from KBEDebug import *

def get_next_enemy_cards(chapter):
    """
    获取下个敌人
    :param chapter:
    :return:
    """
    _player = get_player_with_location_index(chapter, chapter['currentLocationIndex'])
    _next_player = get_next_player(chapter)
    # 如果下个人不是敌人
    if _next_player['identity'] != _player['identity']:
        return _next_player['cards']
    # 下下个人必然是敌人
    else:
        _next_next = (_next_player['locationIndex'] + 1) % 3
        return get_player_with_location_index(chapter, _next_next)['cards']


def get_dealer(chapter):
    """
    获取地主
    :param chapter:
    :return:
    """
    dealer = None
    for k, v in chapter['playerInGame'].items():
        if v['identity'] == 1:
            dealer = v
    return dealer


def get_next_player(chapter):
    """
    获取下个位置的玩家
    :param chapter:
    :return:
    """
    _next = get_next_location_index(chapter)
    return get_player_with_location_index(chapter, _next)


def get_pre_player(chapter):
    """
    获取上个位置的玩家
    :param chapter:
    :return:
    """
    _pre = get_previous_location_index(chapter)
    return get_player_with_location_index(chapter, _pre)


def get_next_location_index(chapter: {}):
    """
    获取下一个玩家位置
    :return:
    """
    current = chapter["currentLocationIndex"]
    return (current + 1) % 3


def get_previous_location_index(chapter):
    """
    获取上一个玩家位置
    :return:
    """
    current = chapter['currentLocationIndex']
    current -= 1
    if current < 0:
        current += len(chapter["playerInGame"])
    return current


def pre_is_friend(chapter):
    """
    上个位置是友方
    :param chapter:
    :return:
    """
    current = chapter['currentLocationIndex']
    _pre = get_previous_location_index(chapter)
    _pre_player = get_player_with_location_index(chapter, _pre)
    _player = get_player_with_location_index(chapter, current)
    return _player['identity'] == _pre_player['identity']


def pre_play_is_friend(chapter):
    """
    上个出牌的是否是友方
    :param chapter:
    :return:
    """
    current = chapter['currentLocationIndex']
    _player = get_player_with_location_index(chapter, current)
    if chapter['prePlayer'] == -1:
        is_friend = True
    else:
        is_friend = chapter['playerInGame'][chapter['prePlayer']]['identity'] == _player['identity']
    return is_friend


def next_is_friend(chapter):
    """
    下个位置是友方
    :param chapter:
    :return:
    """
    current = chapter['currentLocationIndex']
    _next = get_next_location_index(chapter)
    _next_player = get_player_with_location_index(chapter, _next)
    _player = get_player_with_location_index(chapter, current)
    return _player['identity'] == _next_player['identity']


# 通过 location_index 获取玩家
def get_player_with_location_index(chapter, location_index):
    for k, v in chapter["playerInGame"].items():
        if location_index == v["locationIndex"]:
            return v


def convert_value_to_origin(origin_cards, value_cards):
    """
    从纯数值转化为服务端牌值
    :param origin_cards:
    :param value_cards:
    :return:
    """
    origin_cards_copy = origin_cards.copy()
    convert_origin = []
    for v in value_cards:
        for c in origin_cards_copy:
            if re.sub('[a-z]', '', c) == str(v):
                convert_origin.append(c)
                origin_cards_copy.remove(c)
                break
    return convert_origin


def convert_cards_to_value(cards):
    cards_value = []
    for card in cards:
        if isinstance(card, str):
            card = re.sub('[a-z]', '', card)
        cards_value.append(int(card))
    return cards_value


def get_true_player(chapter):
    """
    获得一个真实玩家
    :return:
    """
    for k, v in chapter['playerInGame'].items():
        if v['entity'].info['isBot'] == 0:
            return v


def debug(s):
    DEBUG_MSG(s)
    # print(s)
