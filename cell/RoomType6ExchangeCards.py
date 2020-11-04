import RoomType6InitiativeCardSplit as R6S
import RoomType6AiUtil as R6Util

"""
斗地主换牌函数
"""


def exchange_cards(chapter, bot_account_id, control_count):
    """
    拿出牌机器人的最小单张交换其他机器人的最大单张
    :param chapter:
    :param bot_account_id:
    :param control_count:
    :return:
    """
    control_count = 30
    true_player = R6Util.get_true_player(chapter)
    if not true_player:
        return
    another_bot_account_id = get_another_bot_account_id(chapter, bot_account_id)
    another_bot = chapter['playerInGame'][another_bot_account_id]
    play_bot = chapter['playerInGame'][bot_account_id]
    # 开启换牌
    if control_count != 0 and len(true_player['cards']) <= control_count:
        play_bot_min_dan_zhang = get_min_dan(chapter, bot_account_id)
        another_max_dan_zhang = get_max_dan(chapter, another_bot_account_id)
        if not play_bot_min_dan_zhang or not another_max_dan_zhang:
            return
        if play_bot_min_dan_zhang[0] > another_max_dan_zhang[0]:
            return
        play_bot_min_dan_zhang = R6Util.convert_value_to_origin(play_bot['cards'], play_bot_min_dan_zhang)
        another_max_dan_zhang = R6Util.convert_value_to_origin(another_bot['cards'], another_max_dan_zhang)

        R6Util.debug('换min:%s,max:%s' % (play_bot_min_dan_zhang, another_max_dan_zhang))
        R6Util.debug('换牌前,cards1:%s,cards2:%s' % (play_bot['cards'], another_bot['cards']))
        # 出牌机器人是地主，或者玩家是地主
        if play_bot['identity'] == 1 or true_player['identity'] == 1:
            play_bot['cards'].remove(play_bot_min_dan_zhang[0])
            play_bot['cards'].append(another_max_dan_zhang[0])

            another_bot['cards'].remove(another_max_dan_zhang[0])
            another_bot['cards'].append(play_bot_min_dan_zhang[0])
        R6Util.debug('换牌后,cards1:%s,cards2:%s' % (play_bot['cards'], another_bot['cards']))


def get_min_dan(chapter, account_id):
    # 找到的手牌中的最小单张
    cards = chapter['playerInGame'][account_id]['cards']
    cards_value = R6Util.convert_cards_to_value(cards)
    split_cards_list, split_cards_dic = R6S.split(cards_value)
    try:
        if split_cards_dic and 'danZhang' in split_cards_dic:
            dan_zhang_s = split_cards_dic['danZhang']
            # 不换底牌
            for dan_zhang in dan_zhang_s:
                dan_zhang_origin = R6Util.convert_value_to_origin(cards, dan_zhang)
                if dan_zhang_origin[0] in chapter['coverCards']:
                    continue
                return dan_zhang
    except Exception as e:
        R6Util.debug(e)
        return None


def get_max_dan(chapter, account_id):
    # 找到的手牌中的最大单张
    cards = chapter['playerInGame'][account_id]['cards']
    cards_value = R6Util.convert_cards_to_value(cards)
    split_cards_list, split_cards_dic = R6S.split(cards_value)
    try:
        if split_cards_dic:
            if 'joker' in split_cards_dic:
                # 换大王
                jokers = split_cards_dic['joker']
                if jokers:
                    for joker in jokers[0]:
                        joker_origin = R6Util.convert_value_to_origin(cards, [joker])
                        if joker_origin[0] in chapter['coverCards']:
                            continue
                        return [joker]

            if 'er' in split_cards_dic:
                # 换2
                er_s = split_cards_dic['er']
                if er_s:
                    for er in er_s[0]:
                        er_origin = R6Util.convert_value_to_origin(cards, [er])
                        if er_origin[0] in chapter['coverCards']:
                            continue
                        return [er]

            if 'danZhang' in split_cards_dic:
                # 换单张
                dan_zhang_s = split_cards_dic['danZhang']
                if dan_zhang_s:
                    # 不换底牌
                    for dan_zhang in reversed(dan_zhang_s):
                        dan_zhang_origin = R6Util.convert_value_to_origin(cards, dan_zhang)
                        if dan_zhang_origin[0] in chapter['coverCards']:
                            continue
                        return dan_zhang
    except Exception as e:
        R6Util.debug(e)
        return None


def get_another_bot(chapter, bot_account_id):
    for k, v in chapter['playerInGame'].items():
        if v['entity'].info['isBot'] == 1 and k != bot_account_id:
            return v


def get_another_bot_account_id(chapter, bot_account_id):
    for k, v in chapter['playerInGame'].items():
        if v['entity'].info['isBot'] == 1 and k != bot_account_id:
            return k
