import RoomType6PassiveFindCards as R6P
import RoomType6InitiativeCardSplit as R6Split
import RoomType6AiUtil as R6Util

"""
首先根据手牌分割
分割后根据局势顶策略
根据策略选择出牌
"""


def initiative(chapter_info):
    """
    主动出牌
    :param chapter_info:
    :return:
    """
    result = check_initiative_tactics(chapter_info)
    if result is None:
        result = []
    return result


def check_initiative_tactics(chapter_info):
    """
    主动出牌策略选择
    :return: 策略的对应名称
    """
    cards = chapter_info['myCards']
    next_enemy_cards = chapter_info['nextEnemyCards']
    next_cards = chapter_info['nextCards']
    next_is_friend = chapter_info['nextIsFriend']
    dealer_cards = chapter_info['dealerCards']
    i_am_dealer = chapter_info['iAmDealer']
    previous_cards = chapter_info['preCards']
    split_cards_list, split_cards_dic = R6Split.split(cards)
    R6Util.debug("主动出牌 %s" % chapter_info)
    R6Util.debug("组牌 %s" % split_cards_dic)

    # 是否是剩一手牌
    R6Util.debug("一手牌")
    _cards = one_hand(split_cards_list, split_cards_dic)
    if _cards:
        return _cards

    R6Util.debug("敌人2张，我绝对大单")
    # 敌人只有两张牌，我有绝对大单，其他都是对子
    if len(next_enemy_cards) == 2:
        if len(split_cards_list) == 2 and 'danZhang' in split_cards_dic and 'duiZi' in split_cards_dic:
            dan_zhang = split_cards_dic['danZhang']
            if 16 in dan_zhang or 17 in dan_zhang:
                _cards = fore_enemy_single(chapter_info, split_cards_list, split_cards_dic)
                if _cards:
                    return _cards

    if i_am_dealer:
        R6Util.debug("地主牌分析")
        _play_cards = dealer_initiative(chapter_info, split_cards_dic, split_cards_list)
        if _play_cards:
            return _play_cards
    else:
        # 我是农民
        if next_is_friend:
            R6Util.debug("地主下门牌分析")
            _play_cards = dealer_next_initiative(chapter_info, split_cards_dic, split_cards_list)
            if _play_cards:
                return _play_cards
        else:
            R6Util.debug("顶门牌分析")
            _play_cards = dealer_pre_initiative(chapter_info, split_cards_dic, split_cards_list)
            if _play_cards:
                return _play_cards

    R6Util.debug("兜底")
    return normal(chapter_info, split_cards_list, split_cards_dic)


def get_split_result(chapter_info):
    cards = chapter_info['myCards']
    split_cards_list, split_cards_dic = R6Split.split(cards)
    return split_cards_list, split_cards_dic


def dealer_initiative(chapter_info, split_cards_dic, split_cards_list):
    """
    地主出牌
    """
    my_cards = chapter_info['myCards']

    # 农民一张牌时
    _cards = next_enemy_one_poke(chapter_info, split_cards_list, split_cards_dic)
    if _cards:
        return _cards

    # 手里有小的顺子、连对、飞机，先出这些
    R6Util.debug("小顺连")
    _cards = small_and_long(split_cards_dic)
    if _cards:
        return _cards

    R6Util.debug("牌比较少")
    # 派比较少的时候优先出单张以外的牌
    _cards = few_poke(my_cards, split_cards_dic)
    if _cards:
        return _cards

    return None


def dealer_pre_initiative(chapter_info, split_cards_dic, split_cards_list):
    """
    地主上门接牌
    """
    pre_play_cards = chapter_info['prePlayCards']
    pre_play_is_friend = chapter_info['prePlayIsFriend']
    my_cards = chapter_info['myCards']
    next_cards = chapter_info['nextCards']
    previous_cards = chapter_info['preCards']
    next_is_friend = chapter_info['nextIsFriend']
    i_am_dealer = chapter_info['iAmDealer']

    R6Util.debug("地主一张牌")
    # 地主一张牌时，我在他上手
    _cards = next_enemy_one_poke(chapter_info, split_cards_list, split_cards_dic)
    if _cards:
        return _cards

    R6Util.debug("小顺连")
    # 手里有小的顺子、连对、飞机，先出这些
    _cards = small_and_long(split_cards_dic)
    if _cards:
        return _cards

    R6Util.debug("牌比较少")
    # 派比较少的时候优先出单张以外的牌
    _cards = few_poke(my_cards, split_cards_dic)
    if _cards:
        return _cards


def dealer_next_initiative(chapter_info, split_cards_dic, split_cards_list):
    """
    地主下门接牌
    """
    pre_play_cards = chapter_info['prePlayCards']
    pre_play_is_friend = chapter_info['prePlayIsFriend']
    my_cards = chapter_info['myCards']
    next_cards = chapter_info['nextCards']
    previous_cards = chapter_info['preCards']
    next_is_friend = chapter_info['nextIsFriend']
    i_am_dealer = chapter_info['iAmDealer']

    # 我下手是队友，只有一张牌，且我有<10的牌
    if next_is_friend and len(next_cards) == 1:
        if 'danZhang' in split_cards_dic:
            for i in split_cards_dic['danZhang']:
                if i[0] < 10:
                    _cards = let_friend(chapter_info, split_cards_list, split_cards_dic)
                    if _cards:
                        return _cards

    R6Util.debug("小顺连")
    # 手里有小的顺子、连对、飞机，先出这些
    _cards = small_and_long(split_cards_dic)
    if _cards:
        return _cards

    R6Util.debug("牌比较少")
    # 派比较少的时候优先出单张以外的牌
    _cards = few_poke(my_cards, split_cards_dic)
    if _cards:
        return _cards

    R6Util.debug("地主一张牌")
    # 地主一张牌时，我在他下手
    return pre_enemy_one_poke(chapter_info, split_cards_list, split_cards_dic)


# ---------------------策略对应的动作---------------------


def one_hand(split_cards_list, split_cards_dic):
    """
    一手出完
    :return:
    """
    if len(split_cards_list) == 1:
        return split_cards_list[0]
    if len(split_cards_list) == 2:
        if 'er' in split_cards_dic:
            if len(split_cards_dic['er'][0]) == 3:
                if 'danZhang' in split_cards_dic:
                    if len(split_cards_dic['danZhang']) == 1:
                        x = split_cards_list[0] + split_cards_list[1]
                        return x
                elif 'duiZi' in split_cards_dic:
                    if len(split_cards_dic['duiZi']) == 1:
                        x = split_cards_list[0] + split_cards_list[1]
                        return x


def fore_enemy_single(chapter_info, split_cards_list, split_cards_dic):
    return split_cards_dic['danZhang'][0]


def let_friend(chapter_info, split_cards_list, split_cards_dic):
    return split_cards_dic['danZhang'][0]


def small_and_long(split_cards_dic):
    card_types = ('shunZi', 'feiJi', 'lianDui')
    _cards = find_little_cards_by_type(split_cards_dic, card_types)
    if _cards:
        return _cards

    card_types = ('sanZhang', 'sanDaiEr', 'sanDaiYi')
    _cards = find_little_cards_by_type(split_cards_dic, card_types)
    if _cards:
        val = R6P.get_card_value(_cards)
        if val < 14:
            return _cards
    return None


def few_poke(my_cards, split_cards_dic):
    """"
    牌比较少时，优先出单张之外的牌
    从小的出
    """
    if len(my_cards) > 5:
        return []

    # 优先出单张以外的牌，从小的出
    small_value = 100
    small_cards = []
    for k, _list in split_cards_dic.items():
        if k == 'wangZha' or k == 'zhaDan' or k == 'danZhang' or k == 'joker' or k == 'er':
            continue
        for v in _list:
            _val = R6P.get_card_value(v)
            if _val < small_value:
                small_value = _val
                small_cards = v
    if small_cards:
        return small_cards

    # 否则，出单张
    if 'danZhang' in split_cards_dic:
        dan_zhang = split_cards_dic['danZhang']
        if dan_zhang:
            dan_zhang.sort()
            return dan_zhang[0]

    # 都没有，出任何能出的牌
    for k, v in split_cards_dic.items():
        for _ in v:
            return _


def enemy_one_poke(chapter_info, split_cards_dic):
    """
    敌人一张牌
    """
    # 优先出非单张
    for k, v in split_cards_dic.items():
        if k == "danZhang":
            continue
        for _ in v:
            return _

    # 如果除了单张没有别的，优先出大的
    for k, v in split_cards_dic.items():
        if k == "danZhang":
            v2 = sorted(v, key=lambda x: x[0], reverse=True)
            for _ in v2:
                return _


def pre_enemy_one_poke(chapter_info, split_cards_list, split_cards_dic):
    """
    如果地方手牌剩一张
    :return:
    """
    next_cards = chapter_info['nextCards']
    previous_cards = chapter_info['preCards']
    if len(previous_cards) != 1:
        return []

    # 如果有对子，而且单张很多，出非最小单张，期望和对家配合
    if 'duiZi' in split_cards_dic:
        if 'danZhang' in split_cards_dic:
            dan_zhang = split_cards_dic['danZhang']
            if len(dan_zhang) >= 3:
                mid = int(len(dan_zhang) / 2)
                return dan_zhang[mid]

    return enemy_one_poke(chapter_info, split_cards_dic)


def next_enemy_one_poke(chapter_info, split_cards_list, split_cards_dic):
    """
    下家敌方一张牌
    """
    next_cards = chapter_info['nextCards']
    if len(next_cards) != 1:
        return []

    return enemy_one_poke(chapter_info, split_cards_dic)


def normal(chapter_info, split_cards_list, split_cards_dic):
    """
    兜底策略
    :param chapter_info:
    :param split_cards_list:
    :param split_cards_dic:
    :return:
    """
    # 先出炸弹、王之外的牌
    card_types = ('zhaDan', 'wangZha', 'joker')
    _cards = find_little_cards_but_type(split_cards_dic, card_types)
    if _cards:
        return _cards
    card_types = ('joker',)
    _cards = find_little_cards_by_type(split_cards_dic, card_types)
    if _cards:
        return _cards
    card_types = ('zhaDan',)
    _cards = find_little_cards_by_type(split_cards_dic, card_types)
    if _cards:
        return _cards

    return split_cards_list[0]


# --------------------辅助函数--------------------


def find_little_cards_by_type(split_cards_dic, card_types):
    small_value = 100
    result = []
    for k, _list in split_cards_dic.items():
        if k not in card_types:
            continue
        for v in _list:
            card_value = R6P.get_card_value(v)
            if card_value < small_value:
                small_value = card_value
                result = v
    return result


def find_little_cards_but_type(split_cards_dic, card_types):
    """
    寻找除了该类型外的小牌
    :param split_cards_dic:
    :param card_types:
    :return:
    """
    small_value = 100
    result = []
    for k, _list in split_cards_dic.items():
        if k in card_types:
            continue
        for v in _list:
            card_value = R6P.get_card_value(v)
            if card_value < small_value:
                small_value = card_value
                result = v
    return result


# --------------------辅助函数--------------------
