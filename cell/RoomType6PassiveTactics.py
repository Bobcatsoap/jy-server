import RoomType6ValueAssess as R6Value
import RoomType6PassiveFindCards as R6P
import RoomType6CardsScore as R6CS
import RoomType6InitiativeCardSplit as R6S
import RoomType6AiUtil as R6Util
import RoomType6InitiativeCardSplit as R6Split

"""
压牌策略
"""


def passive(chapter_info):
    return check_passive_tactics(chapter_info)


def check_passive_tactics(chapter_info):
    """
    根据局势给出策略
    :return:
    """
    R6Util.debug("被动出牌牌型 %s" % chapter_info)
    pre_play_cards = chapter_info['prePlayCards']
    pre_play_is_friend = chapter_info['prePlayIsFriend']
    my_cards = chapter_info['myCards']
    next_cards = chapter_info['nextCards']
    previous_cards = chapter_info['preCards']
    next_is_friend = chapter_info['nextIsFriend']
    i_am_dealer = chapter_info['iAmDealer']
    _l, initiative_split_cards = R6S.split(my_cards)

    passive_split_dic = R6P.tip_cards_filter(pre_play_cards, my_cards)
    if len(passive_split_dic) == 0:
        return []

    R6Util.debug("主动拆牌 %s" % initiative_split_cards)
    R6Util.debug("被动拆牌 %s" % passive_split_dic)
    # 是否是一手牌
    if len(passive_split_dic) == 1:
        for k, v in passive_split_dic.items():
            if v[0] == my_cards:
                return v[0]

    if i_am_dealer:
        R6Util.debug("地主牌分析")
        _play_cards = dealer_passive(chapter_info, passive_split_dic, initiative_split_cards)
        if _play_cards:
            return _play_cards
    else:
        # 我是农民
        if next_is_friend:
            R6Util.debug("地主下门牌分析")
            _play_cards = dealer_next_passive(chapter_info, passive_split_dic, initiative_split_cards)
            if _play_cards:
                return _play_cards
        else:
            R6Util.debug("顶门牌分析")
            _play_cards = dealer_pre_passive(chapter_info, passive_split_dic, initiative_split_cards)
            if _play_cards:
                return _play_cards

    # 兜底策略
    R6Util.debug("兜底牌分析")
    return normal(chapter_info, passive_split_dic, initiative_split_cards)


#   --------------------策略--------------------    #
def dealer_passive(chapter_info, passive_split_dic, initiative_split_cards):
    """
    地主接牌
    """
    pre_play_cards = chapter_info['prePlayCards']
    next_cards = chapter_info['nextCards']
    previous_cards = chapter_info['preCards']

    """
    一个农民仅剩一张牌，必须卡住.
    1、出的是单张，用别人要不住的最大牌
    2、出的是对，用别人
    """
    # 地主接牌顶门
    if len(next_cards) == 1 or len(previous_cards) == 1:
        R6Util.debug("农民一张牌，地主顶门")
        _bigger = R6Value.find_follow_card(pre_play_cards, initiative_split_cards)
        if _bigger:
            return _bigger[-1]

        for k, v in passive_split_dic.items():
            _copy = v.copy()
            # 用最大的单张压
            if k == 'danZhang':
                _copy.sort(key=lambda x: x[0], reverse=True)
            return _copy[0]

    # 手上有独立牌，与所出牌型一样时
    R6Util.debug("独立牌分析")
    _bigger = alone_pai(chapter_info, initiative_split_cards)
    if _bigger:
        return _bigger
    return []


def dealer_pre_passive(chapter_info, passive_split_dic, initiative_split_cards):
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

    # 敌方一张牌，在我下手
    R6Util.debug("敌方一张牌")
    if len(next_cards) == 1:
        _bigger = next_enemy_one_poke(chapter_info, passive_split_dic)
        if _bigger:
            return _bigger

    # 压地主出牌
    R6Util.debug("压地主")
    if not pre_play_is_friend:
        _bigger = R6Value.find_follow_card(pre_play_cards, initiative_split_cards)
        if _bigger:
            return _bigger[0]

    # 地主牌少于4个，拆牌打
    R6Util.debug("少于4张")
    if len(next_cards) < 4:
        for k, _list in passive_split_dic.items():
            R6Value.same_type_sort(_list)
            return _list[0]
    return []


def dealer_next_passive(chapter_info, split_cards_dic, initiative_split_cards):
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

    R6Util.debug("队友一张牌分析")
    # 队友下手，且只有一张牌
    if len(next_cards) == 1:
        # 如果上个出牌的是队友，直接让队友走
        if pre_play_is_friend:
            return []
        else:
            card_value = R6P.get_card_value(pre_play_cards)
            if card_value < 10:
                return []
            else:
                _bigger = play_big(chapter_info, split_cards_dic)
                if _bigger:
                    _my_cards = my_cards.copy()
                    for x in _bigger:
                        _my_cards.remove(x)
                    _my_cards.sort()
                    if _my_cards[0] < 10:
                        return _bigger
    return []


def play_big(chapter_info, split_cards_dic):
    """
    出最大牌
    :return:
    """
    # 优先出炸弹或者王炸
    for k, v in split_cards_dic.items():
        if k == 'zhaDan' or k == 'wangZha':
            return v[-1]

    # 没有炸弹或者王炸，优先出能压住的最大牌
    for k, v in split_cards_dic.items():
        return v[-1]


def alone_pai(chapter_info, initiative_split_cards):
    """
    打出手中的独立牌
    """
    bigger_cards = []
    pre_play_cards = chapter_info['prePlayCards']
    # split_cards = R6S.split(my_cards)
    _type = R6P.get_cards_string_type(pre_play_cards)
    for k, _list in initiative_split_cards.items():
        if k == _type:
            for v in _list:
                if R6Value.same_type_greater(v, pre_play_cards):
                    bigger_cards.append(v)
    if bigger_cards:
        R6Value.same_type_sort(bigger_cards)
        return bigger_cards[0]


def next_enemy_one_poke(chapter_info, passive_split_dic):
    """
    下家是敌方, 只剩一张牌
    如果牌是敌方出的，能接一定接
    如果牌是友方出的，看是否顶的够大
    """
    pre_play_cards = chapter_info['prePlayCards']
    pre_play_is_friend = chapter_info['prePlayIsFriend']
    if not pre_play_is_friend:
        # 非友方出牌,一定得接住
        # 从牌库中找对方压不住的牌，或最大牌
        bigger = find_bigger_to_next(chapter_info, passive_split_dic, 0.1)
        if not bigger:
            for k, v in passive_split_dic.items():
                return v[0]
        return bigger
    else:
        # 友方出牌,查看敌方是否能接住，能接住的话，继续往上顶
        if is_next_bigger_to_play(chapter_info, pre_play_cards, 0.1):
            bigger = find_bigger_to_next(chapter_info, passive_split_dic, 0.1)
            if not bigger:
                for k, v in passive_split_dic.items():
                    return v[-1]
            return bigger
    return []


def normal(chapter_info, passive_split_dic, initiative_split_cards):
    """
    兜底策略,不考虑顶门
    :param chapter_info:
    :param passive_split_dic:
    :return:
    """
    # 上个出牌是否是队友
    pre_play_cards = chapter_info['prePlayCards']
    i_am_dealer = chapter_info['iAmDealer']
    pre_is_friend = chapter_info['preIsFriend']
    if len(passive_split_dic) == 0:
        return []

    if i_am_dealer:
        return dealer_normal(chapter_info, passive_split_dic, initiative_split_cards)
    else:
        # 下家是地主
        if pre_is_friend:
            return pre_dealer_normal(chapter_info, passive_split_dic, initiative_split_cards)
        # 上家是地主
        else:
            return dealer_next_normal(chapter_info, passive_split_dic, initiative_split_cards)


def dealer_normal(chapter_info, passive_split_dic, initiative_split_cards):
    """
    地主兜底
    :param chapter_info:
    :param passive_split_dic:
    :param initiative_split_cards:
    :return:
    """
    R6Util.debug("dealer_normal 兜底-主动找牌")
    pre_play_cards = chapter_info['prePlayCards']
    # 地主兜底，
    _bigger = R6Value.find_follow_card(pre_play_cards, initiative_split_cards)
    if _bigger:
        return _bigger[0]

    R6Util.debug("dealer_normal 兜底-被动拆牌")
    for k, v in passive_split_dic.items():
        R6Value.same_type_sort(v)
        return v[0]


def pre_dealer_normal(chapter_info, passive_split_dic, initiative_split_cards):
    """
    地主上家兜底
    :param chapter_info:
    :param passive_split_dic:
    :param initiative_split_cards:
    :return:
    """
    R6Util.debug("pre_dealer_normal 兜底牌分析")
    pre_play_is_friend = chapter_info['prePlayIsFriend']
    pre_play_cards = chapter_info['prePlayCards']
    next_cards = chapter_info['nextCards']
    my_cards = chapter_info['myCards']
    dealer_cards = chapter_info['dealerCards']
    previous_cards = chapter_info['preCards']
    if not pre_play_is_friend:

        # 我的牌绝对好，肯定接
        jie_cards = R6Value.is_absolute_big_cards(passive_split_dic, initiative_split_cards)
        if jie_cards:
            R6Util.debug("我的牌绝对好，肯定接")
            return jie_cards

        # 接完手牌有没有变差
        cha_score, jie_cards = jie_and_score(my_cards, passive_split_dic)
        if cha_score > -5:
            R6Util.debug("接完手牌没有变差")
            return jie_cards

        # 我的接牌比他大得不多
        jie_cards = jie_not_so_bigger(pre_play_cards, passive_split_dic)
        if jie_cards:
            R6Util.debug("我的接牌比他大得不多")
            return jie_cards

        # 能用飞机、连对、顺子压，就压
        R6Util.debug("飞机连对压")
        for k, v in passive_split_dic.items():
            if k == 'shunZi' or k == 'lianDui' or k == 'feiJi' or k == 'duiZi':
                R6Value.same_type_sort(v)
                return v[0]
            if k == 'danZhang' or k == 'sanZhang' or k == 'sanDaiYi' or k == 'siDaiEr':
                R6Value.same_type_sort(v)
                return v[0]

        # 如果只能用炸弹压，对面出的牌又没有王，不压  'wangZha'
        if len(passive_split_dic) == 1 and 'zhaDan' in passive_split_dic:
            if len(pre_play_cards) > 8 and (15 not in pre_play_cards and 16 not in pre_play_cards):
                R6Util.debug("如果只能用炸弹压，对面出的牌又没有王，不压")
                return []

        # 地主牌很少，或者出了大牌
        jie_cards = dealer_cards_less_or_pre_play_cards_big(chapter_info, passive_split_dic)
        if jie_cards:
            R6Util.debug("地主牌很少，或者出了大牌")
            return jie_cards

    else:

        # 不压队友大牌
        if R6Value.is_bigger_card(pre_play_cards):
            return []

        # 不用大牌压队友
        small = small_follow_friend(pre_play_cards, initiative_split_cards)
        if small:
            return small

        # 手上有独立牌，与所出牌型一样时
        R6Util.debug("独立牌分析")
        _bigger = alone_pai(chapter_info, initiative_split_cards)
        if _bigger:
            return _bigger

        if not R6Value.is_next_bigger(pre_play_cards, next_cards, previous_cards):
            return []

        return []


def dealer_next_normal(chapter_info, passive_split_dic, initiative_split_cards):
    """
    地主下家兜底
    :param chapter_info:
    :param passive_split_dic:
    :param initiative_split_cards:
    :return:
    """
    R6Util.debug("dealer_next_normal 兜底牌分析")
    my_cards = chapter_info['myCards']
    pre_play_is_friend = chapter_info['prePlayIsFriend']
    pre_play_cards = chapter_info['prePlayCards']
    if not pre_play_is_friend:
        # 手上有独立牌，与所出牌型一样时
        R6Util.debug("独立牌分析")
        _bigger = alone_pai(chapter_info, initiative_split_cards)
        if _bigger:
            return _bigger

        # 我的牌绝对好，肯定接
        jie_cards = R6Value.is_absolute_big_cards(passive_split_dic, initiative_split_cards)
        if jie_cards:
            R6Util.debug("我的牌绝对好，肯定接")
            return jie_cards

        # 我的接牌比他大得不多
        jie_cards = jie_not_so_bigger(pre_play_cards, passive_split_dic)
        if jie_cards:
            R6Util.debug("我的接牌比他大得不多")
            return jie_cards

        # 接完手牌有没有变差
        jie_score, jie_cards = jie_and_score(my_cards, passive_split_dic)
        if jie_score > -5:
            R6Util.debug("接完手牌没有变差")
            return jie_cards

        # 能用飞机、连对、顺子压，就压
        R6Util.debug("飞机连对压")
        for k, v in passive_split_dic.items():
            if k == 'shunZi' or k == 'lianDui' or k == 'feiJi' or k == 'duiZi':
                R6Value.same_type_sort(v)
                return v[0]
            if k == 'danZhang' or k == 'sanZhang' or k == 'sanDaiYi' or k == 'siDaiEr':
                R6Value.same_type_sort(v)
                return v[0]

        # 如果只能用炸弹压，对面出的牌又没有王，不压  'wangZha'
        if len(passive_split_dic) == 1 and 'zhaDan' in passive_split_dic:
            if len(pre_play_cards) > 8 and (15 not in pre_play_cards and 16 not in pre_play_cards):
                R6Util.debug("如果只能用炸弹压，对面出的牌又没有王，不压")
                return []

        # 地主牌很少，或者出了大牌
        jie_cards = dealer_cards_less_or_pre_play_cards_big(chapter_info, passive_split_dic)
        if jie_cards:
            R6Util.debug("地主牌很少，或者出了大牌")
            return jie_cards

    else:
        # 不接队友大牌
        if R6Value.is_bigger_card(pre_play_cards):
            return []
        # 不用大牌接队友
        small = small_follow_friend(pre_play_cards, initiative_split_cards)
        if small:
            return small
        return []


# --------------------策略--------------------#


# --------------------辅助函数-----------------#

def get_split_cards_dic(chapter_info):
    pre_play_cards = chapter_info['prePlayCards']
    my_cards = chapter_info['myCards']
    split_cards_dic = R6P.tip_cards(pre_play_cards, my_cards)
    return split_cards_dic


def small_follow_friend(pre_play_cards, initiative_split_cards):
    """
    不用大牌跟队友
    :param initiative_split_cards:
    :return:
    """
    R6Util.debug('small_follow_friend')
    _bigger = R6Value.find_follow_card(pre_play_cards, initiative_split_cards)
    for _b in _bigger:
        _value = R6P.get_card_value(_b)
        if _value > 14:
            return []
        return _b


def find_bigger_to_next(chapter_info, split_cards_dic, chance=0.1):
    """
    查找下位玩家压不住的牌
    """
    next_cards = chapter_info['nextCards']
    previous_cards = chapter_info['preCards']
    for k, v in split_cards_dic.items():
        v.sort()
        for _ in v:
            if R6Value.calc_next_bigger_probability(_, next_cards, previous_cards) < chance:
                return _
    return []


def is_next_bigger_to_play(chapter_info, play_cards, chance=0.1):
    """
    下家的牌是否更大
    """
    next_cards = chapter_info['nextCards']
    previous_cards = chapter_info['preCards']
    if R6Value.calc_next_bigger_probability(play_cards, next_cards, previous_cards) < chance:
        return False
    return True


def jie_and_score(my_cards, passive_split_dic):
    """
    接牌后有没有变差
    :param my_cards:
    :param passive_split_dic:
    :return:
    """
    score = R6CS.get_score(R6Split.split(my_cards)[1])
    max_score = -100
    max_cards = []
    for k, v in passive_split_dic.items():
        for _ in v:
            _copy = my_cards.copy()
            for i in _:
                _copy.remove(i)
            score2 = R6CS.get_score(R6Split.split(_copy)[1])
            _s = score2 - score
            if _s > max_score:
                max_score = _s
                max_cards = _

    return max_score, max_cards


def jie_not_so_bigger(pre_play_cards, passive_split_dic):
    """
    我的接牌比他大得不多
    :param pre_play_cards:
    :param passive_split_dic:
    :return:
    """

    for k, v in passive_split_dic.items():
        if 15 in v[0] or 16 in v[0] or 17 in v[0]:
            continue
        return v[0]

    return None


def dealer_cards_less_or_pre_play_cards_big(chapter_info, passive_split_dic):
    """
    地主牌很少，或者出了大牌
    :param chapter_info:
    :param passive_split_dic:
    :return:主动拆牌
    """
    dealer_cards = chapter_info['dealerCards']
    pre_play_cards = chapter_info['prePlayCards']
    if len(dealer_cards) <= 5 or 15 in pre_play_cards or 16 in pre_play_cards or 17 in pre_play_cards:
        for k, v in passive_split_dic.items():
            return v[0]
    return None

# --------------------辅助函数--------------------#
