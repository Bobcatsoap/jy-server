import RoomType6PassiveTactics as R6PT
import RoomType6PassiveFindCards as R6PF
import RoomType6InitiativeTactics as R6IT
import RoomType6InitiativeCardSplit as R6Split
import RoomType6WinPath as R6WinPath
import RoomType6AiUtil as R6Util
import RoomType6ExchangeCards as R6Exchange

"""
斗地主ai入口
"""


def bot_play_card_ai(chapter, bot_account_id, control_count):
    """
    斗地主ai主函数
    :param chapter:
    :param bot_account_id:
    :param control_count:
    :return:
    """
    bot = chapter['playerInGame'][bot_account_id]
    next_cards = R6Util.get_next_player(chapter)['cards']
    next_cards = R6Util.convert_cards_to_value(next_cards)
    pre_cards = R6Util.get_pre_player(chapter)['cards']
    pre_cards = R6Util.convert_cards_to_value(pre_cards)
    play_bot_cards = R6Util.convert_cards_to_value(bot['cards'])
    chapter_info = get_chapter_info(chapter, bot_account_id)
    split_list, split_dict = R6Split.split(play_bot_cards)

    # 主动出牌
    R6Util.debug(chapter_info)
    if chapter['prePlayer'] == bot_account_id or chapter['prePlayer'] == -1:
        # 出牌赢牌路径选择
        result = R6WinPath.chu_win_path_select(next_cards, pre_cards, split_dict)
        if not result:
            R6Util.debug("主动策略")
            result = R6IT.initiative(chapter_info)
    else:
        # 接牌路径选择
        result = R6WinPath.jie_win_path_select(chapter_info, split_dict)
        if not result:
            R6Util.debug("被动策略")
            result = R6PT.passive(chapter_info)

    if result is None:
        result = []

    return R6Util.convert_value_to_origin(bot['cards'], result)


def exchange_cards(chapter, bot_account_id, control_count):
    try:
        R6Exchange.exchange_cards(chapter, bot_account_id, control_count)
    except Exception as e:
        R6Util.debug('换牌 exception:%s' % e)


def get_chapter_info(chapter, bot_account_id):
    """
    组织牌局信息
    :param chapter:
    :param bot_account_id:
    :return:
    """
    bot = chapter['playerInGame'][bot_account_id]
    dealer = R6Util.get_dealer(chapter)
    pre_play_cards = chapter['prePlayerPlayCards']
    info = {
        'prePlayCards': R6Util.convert_cards_to_value(pre_play_cards),
        'myCards': R6Util.convert_cards_to_value(bot['cards']),
        'iAmDealer': bot['identity'] == 1,
        'dealerCards': R6Util.convert_cards_to_value(dealer['cards']),
        'nextCards': R6Util.convert_cards_to_value(R6Util.get_next_player(chapter)['cards']),
        'nextIsFriend': R6Util.next_is_friend(chapter),
        'nextEnemyCards': R6Util.convert_cards_to_value(R6Util.get_next_enemy_cards(chapter)),
        'preIsFriend': R6Util.pre_is_friend(chapter),
        'prePlayIsFriend': R6Util.pre_play_is_friend(chapter),
        'preCards': R6Util.convert_cards_to_value(R6Util.get_pre_player(chapter)['cards'])
    }

    return info


# chapter_info = {'prePlayCards': [14], 'nextEnemyCards': [14], 'nextCards': [13, 13, 7, 7, 6, 8, 5, 10, 9, 6, 5, 7, 8, 9, 12, 4], 'preIsFriend': False, 'nextIsFriend': True, 'prePlayIsFriend': True, 'myCards': [8, 5, 6, 6, 5, 8], 'dealerCards': [14], 'preCards': [14], 'iAmDealer': False}
# split_list, split_dict = R6Split.split([14])
# result = R6WinPath.jie_win_path_select(chapter_info, split_dict)
# result = R6PT.passive(chapter_info)
# result = R6IT.initiative(chapter_info)

# split_dict = R6PF.tip_cards([7, 3, 3, 3], chapter_info["myCards"])
# new_split_dict = {}
# _filter = set()
# for k, vlist in split_dict.items():
#     _filter.clear()
#     for v in vlist:
#         val = R6PF.get_card_value(v)
#         if val not in _filter:
#             if k not in new_split_dict:
#                 new_split_dict[k] = []
#             new_split_dict[k].append(v)
#             _filter.add(val)

# print(result)
