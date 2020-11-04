import RoomType6ValueAssess as R6Value
import RoomType6PassiveFindCards as R6P
import RoomType6AiUtil as R6Util
import RoomType6InitiativeCardSplit as R6Split

"""
主动出牌、被动出牌路径判断
"""


def chu_win_path_select(next_cards, previous_cards, split_cards_dic):
    """
    出牌赢牌路径选择
    :return:
    """
    small_groups = []
    # 扫描所有牌组，统计别人能接住的牌组数
    for k, v in split_cards_dic.items():
        for _ in v:
            if R6Value.have_bigger(_, next_cards, previous_cards, 0.1):
                small_groups.append(_)
    small_count = len(small_groups)

    R6Util.debug('chu_win_path_select small_count:%s' % small_count)

    # 没有能被压住的牌，随意返回一组
    if small_count == 0:
        for k, v in split_cards_dic.items():
            return v[0]

    # 只有一组能被压住的牌，把能被压住的放后面，返回第一组牌
    elif small_count == 1:
        return R6Value.find_little_cards_but_one(split_cards_dic, small_groups[0])

    # 手里的牌能否接住small1和small2
    elif small_count == 2:
        for small in small_groups:
            _bigger = R6Value.find_bigger_card_but_card(small, split_cards_dic, small_groups)
            if _bigger:
                return small

    # 判定失败
    return None


def jie_win_path_select(chapter_info, initiative_split_cards):
    """"
    接牌赢牌路径选择
    """
    pre_play_is_friend = chapter_info['prePlayIsFriend']
    my_cards = chapter_info['myCards']
    next_cards = chapter_info['nextCards']
    previous_cards = chapter_info['preCards']
    next_is_friend = chapter_info['nextIsFriend']
    i_am_dealer = chapter_info['iAmDealer']
    pre_play_cards = chapter_info['prePlayCards']

    bigger_groups = R6Value.find_all_follow_card(pre_play_cards, initiative_split_cards)
    if not bigger_groups:
        return None

    # 地主接牌路径
    def deal_win_select(_bigger_groups):
        for v in _bigger_groups:
            if R6Value.have_bigger(pre_play_cards, next_cards, previous_cards):
                # 看自己是否能收回
                other = next_cards.copy()
                other.extend(previous_cards)
                return_dic = R6P.tip_cards_filter(pre_play_cards, other)
                other_bigger_groups = R6Value.find_follow_card(pre_play_cards, return_dic)
                if other_bigger_groups:
                    other_bigger_cards = other_bigger_groups[-1]
                    if R6Value.find_follow_card(other_bigger_cards, initiative_split_cards):
                        return v
            else:
                # 看是否满足赢牌路径
                if chu_win_path_select(next_cards, previous_cards, initiative_split_cards):
                    return v
        return None

    # 农民接牌路径
    def farmer_win_select(_bigger_groups, next_cards, previous_cards):
        for v in _bigger_groups:
            if R6Value.is_next_bigger(v, next_cards, previous_cards):
                # 看自己是否能收回
                other = next_cards.copy()
                other.extend(previous_cards)
                return_dic = R6P.tip_cards_filter(pre_play_cards, other)
                other_bigger_groups = R6Value.find_follow_card(pre_play_cards, return_dic)
                if other_bigger_groups:
                    other_bigger_cards = other_bigger_groups[-1]
                    if R6Value.find_follow_card(other_bigger_cards, initiative_split_cards):
                        return v
            else:
                # 看是否满足赢牌路径
                if chu_win_path_select(next_cards, previous_cards, initiative_split_cards):
                    return v
        return None

    # 看对手是否能接住
    if i_am_dealer:
        return deal_win_select(bigger_groups)
    else:
        if next_is_friend:
            farmer_win_select(bigger_groups, previous_cards, next_cards)
        else:
            farmer_win_select(bigger_groups, next_cards, previous_cards)