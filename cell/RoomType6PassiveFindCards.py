"""
压牌时需要的找牌函数合集
"""
import copy
import time

import RoomType6CardsScore as R6CS
import RoomType6InitiativeCardSplit as R6Split
from enum import Enum, unique


@unique
class CardType(Enum):
    invalid = -1
    dan_zhang = 0
    dui_zi = 1
    san_zhang = 2
    zha_dan = 4
    san_dai_yi = 5
    san_dai_er = 10
    wang_zha = 6
    shun_zi = 7
    two_lian_dui = 8
    fei_ji = 9
    si_dai_er = 11
    fei_ji_single = 12
    three_lian_dui = 13


def tip_cards(pre_player_cards, hand_cards):
    """
    返回值为空代表没有找到牌组
    找到的所有结果以二位数组的形式返回
    示例：
    :param pre_player_cards:上家出牌
    :param hand_cards:手牌
    :return:
    """
    pre_cards_type = play_card_correct(pre_player_cards)
    pre_player_cards = pre_player_cards.copy()
    hand_cards = hand_cards.copy()
    total_return_dic = {}
    if pre_cards_type == CardType.invalid:
        return total_return_dic

    # 如果对方出的牌有王炸直接跳过
    if is_wang_zha(pre_player_cards):
        return total_return_dic

    if is_zha_dan(pre_player_cards):
        zha_dan_s = find_z_d(hand_cards)
        return_zha_dans = []
        for zha_dan in zha_dan_s:
            if compare_zha_dan(zha_dan, pre_player_cards):
                return_zha_dans.append(zha_dan)
        total_return_dic['zhaDan'] = return_zha_dans

    else:
        if is_dan_zhang(pre_player_cards):
            # 单张压制
            dan_zhang_s = find_dan_zhang(hand_cards)
            return_dan_zhang_s = []
            for dan_zhang in dan_zhang_s:
                if dan_zhang > pre_player_cards[0]:
                    return_dan_zhang_s.append([dan_zhang])

            # 没有单张，拆单
            all_cards = find_all_cards_single(hand_cards)
            for i in all_cards:
                if i > pre_player_cards[0] and [i] not in return_dan_zhang_s:
                    return_dan_zhang_s.append([i])

            total_return_dic['danZhang'] = return_dan_zhang_s

        # 如果对方出的是对子
        elif is_dui_zi(pre_player_cards):
            dui_zi_s = find_dui_zi(hand_cards)
            return_dui_zi_s = []
            for dui_zi in dui_zi_s:
                if dui_zi[0] > pre_player_cards[0]:
                    return_dui_zi_s.append(dui_zi)

            # 没有对子，拆对
            all_cards = find_all_cards_single(hand_cards)
            for i in all_cards:
                if i > pre_player_cards[0] and all_cards.count(i) >= 2:
                    return_dui_zi_s.append([i, i])

            total_return_dic['duiZi'] = return_dui_zi_s

        elif is_s_zhang(pre_player_cards):
            san_zhang_s = find_san_zhang(hand_cards)
            return_san_zhang_s = []
            for san_zhang in san_zhang_s:
                if san_zhang[0] > pre_player_cards[0]:
                    return_san_zhang_s.append(san_zhang)
            total_return_dic['sanZhang'] = return_san_zhang_s

        elif is_san_dai_yi(pre_player_cards):
            san_dai_yi_s = find_san_dai_yi(hand_cards)
            return_san_dai_yi_s = []
            for san_dai_yi in san_dai_yi_s:
                if compare_s_d_y(san_dai_yi, pre_player_cards):
                    return_san_dai_yi_s.append(san_dai_yi)
            total_return_dic['sanDaiYi'] = return_san_dai_yi_s

        elif is_san_dai_er(pre_player_cards):
            san_dai_er_s = find_san_dai_er(hand_cards)
            return_san_dai_er_s = []
            for san_dai_er in san_dai_er_s:
                if compare_san_dai_er(san_dai_er, pre_player_cards):
                    return_san_dai_er_s.append(san_dai_er)
            total_return_dic['sanDaiEr'] = return_san_dai_er_s

        elif is_s_z(pre_player_cards):
            shun_zi_s = find_s_z(hand_cards, len(pre_player_cards))
            return_shun_zi_s = []
            for shun_zi in shun_zi_s:
                if compare_s_z(shun_zi, pre_player_cards):
                    return_shun_zi_s.append(shun_zi)
            total_return_dic['shunZi'] = return_shun_zi_s

        elif is_2_l_d(pre_player_cards):
            length = int(len(pre_player_cards) / 2)
            _2_l_d_s = find_two_lian_dui(hand_cards, length)
            return_2_l_d_s = []
            for _2_l_d in _2_l_d_s:
                if compare_2_l_d(_2_l_d, pre_player_cards):
                    return_2_l_d_s.append(_2_l_d)
            total_return_dic['lianDui'] = return_2_l_d_s

        elif is_3_l_d(pre_player_cards):
            length = int(len(pre_player_cards) / 3)
            _3_l_d_s = find_3_l_d(hand_cards, length)
            return_3_l_d_s = []
            for _3_l_d in _3_l_d_s:
                if compare_3_l_d(_3_l_d, pre_player_cards):
                    return_3_l_d_s.append(_3_l_d)
            total_return_dic['feiJi'] = return_3_l_d_s

        elif is_f_j(pre_player_cards):
            length = int(len(pre_player_cards) / 5)
            f_j_s = find_f_j(hand_cards, length)
            return_f_j_s = []
            for f_j in f_j_s:
                if compare_f_j(f_j, pre_player_cards):
                    return_f_j_s.append(f_j)
            total_return_dic['feiJi'] = return_f_j_s

        elif is_f_single(pre_player_cards):
            length = int(len(pre_player_cards) / 4)
            f_j_s = find_f_j_single(hand_cards, length)
            return_f_j_s = []
            for f_j in f_j_s:
                if compare_f_j(f_j, pre_player_cards):
                    return_f_j_s.append(f_j)
            total_return_dic['feiJi'] = return_f_j_s

        zha_dan_s = find_z_d(hand_cards)
        return_dan_zhang_s = []
        for zha_dan in zha_dan_s:
            return_dan_zhang_s.append(zha_dan)
        total_return_dic['zhaDan'] = return_dan_zhang_s

    wang_zha = find_w_z(hand_cards)
    if len(wang_zha) != 0:
        total_return_dic['wangZha'] = [wang_zha]

    new_dict = {}
    # 清除空数据
    for k, v in total_return_dic.items():
        if v and v[0]:
            new_dict[k] = v
    # 按照评分排序
    sort_by_score(hand_cards, new_dict)
    return new_dict


def sort_by_score(my_cards, passive_split_dic):
    """
    把压牌结果按分数排序
    :param my_cards:
    :param passive_split_dic:
    :return:
    """
    score = R6CS.get_score(R6Split.split(my_cards)[1])

    def get_score(cards, remove_cards):

        _copy = cards.copy()
        for i in remove_cards:
            _copy.remove(i)
        score2 = R6CS.get_score(R6Split.split(_copy)[1])
        return score2 - score

    for k, v in passive_split_dic.items():
        v.sort(key=lambda x: get_score(my_cards.copy(), x), reverse=True)
    return


def tip_cards_filter(pre_player_cards, hand_cards):
    split_dict = tip_cards(pre_player_cards, hand_cards)
    new_split_dict = {}
    _filter = set()
    for k, vlist in split_dict.items():
        _filter.clear()
        if k != "sanZhang" and k != "sanDaiYi" and k != "sanDaiEr":
            if k not in new_split_dict:
                new_split_dict[k] = []
            if k == 'danZhang':
                for v in vlist:
                    count = hand_cards.count(v[0])
                    new_split_dict[k].extend([v]*count)
            else:
                new_split_dict[k].extend(vlist)
            continue
        for v in vlist:
            val = get_card_value(v)
            if val not in _filter:
                if k not in new_split_dict:
                    new_split_dict[k] = []
                new_split_dict[k].append(v)
                _filter.add(val)
    return new_split_dict

def get_cards_string_type(cards):
    _type = play_card_correct(cards).value
    if _type == -1:
        return ''
    if _type == 0:
        return 'danZhang'
    if _type == 1:
        return 'duiZi'
    if _type == 2:
        return 'sanZhang'
    if _type == 4:
        return 'zhaDan'
    if _type == 5:
        return 'sanDaiYi'
    if _type == 6:
        return 'wangZha'
    if _type == 7:
        return 'shunZi'
    if _type == 8:
        return 'lianDui'
    if _type == 9:
        return 'feiJi'
    if _type == 11:
        return 'siDaiEr'
    if _type == 12:
        return 'feiJi'
    if _type == 13:
        return 'feiJi'


def play_card_correct(correct_cards, can_si_dai_er=False):
    cards = correct_cards.copy()
    length = len(cards)
    if length == 1:
        return CardType.dan_zhang
    elif length == 2:
        if cards[0] == cards[1]:
            return CardType.dui_zi
        elif cards[0] + cards[1] == 33:
            return CardType.wang_zha
        else:
            return CardType.invalid
    elif length == 3:
        card1, card2, card3 = cards[0], cards[1], cards[2]
        if card1 == card2 and card2 == card3:
            return CardType.san_zhang
        else:
            return CardType.invalid
    elif length == 4:
        if is_san_dai_yi(cards):
            return CardType.san_dai_yi
        elif is_zha_dan(cards):
            return CardType.zha_dan
        else:
            return CardType.invalid
    elif length == 5:
        if is_s_z(cards):
            return CardType.shun_zi
        elif is_san_dai_er(cards):
            return CardType.san_dai_er
        else:
            return CardType.invalid
    elif length > 5:
        if is_s_z(cards):
            return CardType.shun_zi
        elif is_2_l_d(cards):
            return CardType.two_lian_dui
        elif is_3_l_d(cards):
            return CardType.three_lian_dui
        elif is_f_j(cards):
            return CardType.fei_ji
        elif is_f_single(cards):
            return CardType.fei_ji_single
        elif is_si_dai_er(cards, can_si_dai_er):
            return CardType.si_dai_er
        else:
            return CardType.invalid
    else:
        return CardType.invalid


def get_card_value(correct_cards, card_type=None):
    if card_type is None:
        card_type = play_card_correct(correct_cards)
    if CardType.invalid == card_type:
        return None
    cards = correct_cards.copy()
    if CardType.dan_zhang == card_type or CardType.dui_zi == card_type or CardType.zha_dan == card_type:
        return cards[0]
    elif CardType.wang_zha == card_type:
        return min(cards[0], cards[1])
    elif CardType.san_zhang == card_type or CardType.san_dai_yi == card_type or CardType.san_dai_er == card_type:
        for v in cards:
            if cards.count(v) == 3:
                return v
    elif CardType.shun_zi == card_type or CardType.two_lian_dui == card_type:
        cards.sort()
        return cards[0]
    elif CardType.three_lian_dui == card_type or CardType.fei_ji == card_type or CardType.fei_ji_single == card_type:
        cards.sort()
        for v in cards:
            if cards.count(v) >= 3:
                return v
    return None


def is_san_dai_yi(cards):
    if len(cards) != 4:
        return False
    cards.sort()
    card1, card2, card3, card4 = cards[0], cards[1], cards[2], cards[3]
    # 三带一
    if card1 == card2:
        if card2 == card3:
            if card3 != card4:
                return True
    elif card1 != card2:
        if card2 == card3:
            if card3 == card4:
                return True
    return False


def is_san_dai_er(cards):
    if len(cards) != 5:
        return False
    cards.sort()
    card1, card2, card3, card4, card5 = cards[0], cards[1], cards[2], cards[3], cards[4]
    # x,x,x
    # y,y
    if card1 == card2:
        if card2 == card3:
            if card4 == card5:
                if card3 != card4:
                    return True

    # x,x
    # y,y,y
    if card1 == card2:
        if card2 != card3:
            if card3 == card4:
                if card4 == card5:
                    return True
    return False


def is_zha_dan(cards):
    if len(cards) != 4:
        return False
    cards.sort()
    card1, card2, card3, card4 = cards[0], cards[1], cards[2], cards[3]
    if card1 == card2 and card2 == card3 and card3 == card4:
        return True
    return False


def is_si_dai_er(cards, can_si_dai_er):
    if len(cards) != 6 or not can_si_dai_er:
        return False
    cards.sort()
    for cv in cards:
        if cards.count(cv) == 4:
            return True


def is_dan_zhang(cards):
    return len(cards) == 1


def is_dui_zi(cards):
    if len(cards) != 2:
        return False
    if cards[0] != cards[1]:
        return False
    return True


def is_s_zhang(cards):
    if len(cards) != 3:
        return False
    if cards[0] == cards[1] and cards[1] == cards[2]:
        return True
    else:
        return False


def is_f_j(cards):
    # 飞机长度必须是5的倍数，并且大于等于10
    if len(cards) < 10:
        return False
    if len(cards) % 5 != 0:
        return False
    new_cards = cards.copy()
    three = []
    # 找到所有的三张
    for card in new_cards:
        if new_cards.count(card) == 3 and card not in three:
            # 有 2 以上的不行
            if card >= 15:
                return False
            three.append(card)
    # 没有飞机
    if len(three) == 0:
        return False
    three.sort()
    # 判断三张是否相连
    for i in range(0, len(three) - 1):
        if three[i] + 1 != three[i + 1]:
            return False
    # 移除所有三张
    for card in three:
        # 移除
        while card in new_cards:
            new_cards.remove(card)

    # 排序
    new_cards.sort()
    # 检查剩下的是否能组成翅膀
    can_wing = True
    for index in range(0, len(new_cards), 2):
        if new_cards[index] != new_cards[index + 1]:
            can_wing = False
            break
    return can_wing


def is_f_single(cards):
    # 带单飞机
    if len(cards) < 8:
        return False
    if len(cards) % 4 != 0:
        return False
    new_cards = cards.copy()
    three = []
    # 找到所有的三张
    for card in new_cards:
        if new_cards.count(card) >= 3 and card not in three:
            three.append(card)
    if len(three) == 0:
        return False
    three.sort()
    # 判断三张相连的牌
    three_connect = []
    for i in range(0, len(three) - 1):
        if three[i] + 1 == three[i + 1]:
            if three[i] not in three_connect:
                three_connect.append(three[i])
            if three[i + 1] not in three_connect:
                three_connect.append(three[i + 1])
    # 如果相连的三连对小于2不能构成飞机
    if len(three_connect) < 2:
        return False
    for i in three_connect:
        if i >= 15:
            return False
    # 记录三连对的组合长度
    three_connect_length = len(three_connect)
    # 移除所有三张
    for card in three_connect:
        new_cards.remove(card)
        new_cards.remove(card)
        new_cards.remove(card)

    if len(new_cards) != three_connect_length:
        return False
    return True


def is_s_z(cards):
    if len(cards) < 5:
        return False
    # 排序
    cards.sort()
    # 不能包含大小王和 2
    if cards[len(cards) - 1] >= 15:
        return False
    for card in cards:
        if cards.count(card) != 1:
            return False
    for index in range(0, len(cards) - 1):
        if not cards[index] + 1 == cards[index + 1]:
            return False
    return True


def is_wang_zha(cards):
    if len(cards) != 2:
        return False
    return cards[0] + cards[1] == 33


def is_2_l_d(cards):
    if len(cards) < 6:
        return False
    if len(cards) % 2 != 0:
        return False
    for card in cards:
        if cards.count(card) != 2:
            return False
    new_cards = copy.deepcopy(cards)
    new_cards.sort()
    # 去重
    for card in new_cards:
        while new_cards.count(card) != 1:
            new_cards.remove(card)
    # 不能包含大小王和 2
    if new_cards[len(new_cards) - 1] >= 15:
        return False

    for index in range(0, len(new_cards) - 1):
        if not new_cards[index] + 1 == new_cards[index + 1]:
            return False
    return True


def is_3_l_d(cards):
    if len(cards) < 6:
        return False
    if len(cards) % 3 != 0:
        return False
    for card in cards:
        if cards.count(card) != 3:
            return False
    new_cards = copy.deepcopy(cards)
    new_cards.sort()
    for card in new_cards:
        while new_cards.count(card) != 1:
            new_cards.remove(card)
    # 不能包含大小王和 2
    if new_cards[len(new_cards) - 1] >= 15:
        return False
    for index in range(0, len(new_cards) - 1):
        if not new_cards[index] + 1 == new_cards[index + 1]:
            return False
    return True


def find_dan_zhang(target_cards):
    """
    找出所有单张
    :param target_cards:
    :return:
    """
    cards = []
    for i in target_cards:
        if target_cards.count(i) == 1:
            cards.append(i)
    return cards


def find_all_cards_single(target_cards):
    """
    找出所有牌的单牌
    :param target_cards:
    :return:
    """
    cards = []
    for i in target_cards:
        if i not in cards:
            cards.append(i)
    cards.sort()
    return cards


def find_z_d(target_cards):
    """
    找出手牌中的所有炸弹
    :param target_cards:
    :return:
    """
    zha_dan = []
    checked = []
    copy_cards = target_cards.copy()
    copy_cards.sort()
    for i in copy_cards:
        if copy_cards.count(i) >= 4:
            if i in checked:
                continue
            temp = [i, i, i, i]
            if temp not in zha_dan:
                zha_dan.append(temp)
                checked.append(i)

    return zha_dan


def find_w_z(target_cards):
    if 16 in target_cards:
        if 17 in target_cards:
            return [16, 17]
    return []


def find_dui_zi(target_cards):
    new_cards = target_cards.copy()
    new_cards.sort()
    duizi = []
    for i in target_cards:
        if new_cards.count(i) >= 2:
            temp = []
            for j in range(0, 2):
                temp.append(i)
                new_cards.remove(i)
            if temp not in duizi:
                duizi.append(temp)

    return duizi


def find_san_zhang(target_cards):
    three = []
    for i in target_cards:
        if target_cards.count(i) >= 3:
            if i not in three:
                temp = []
                for j in range(0, 3):
                    temp.append(i)
                if temp not in three:
                    three.append(temp)
    return three


def find_san_dai_yi(target_cards):
    three = []
    target_cards.sort()
    # 找到所有三张
    for i in target_cards:
        if target_cards.count(i) >= 3:
            if i not in three:
                three.append(i)
    san_dai_yi_s = []
    for i in three:
        temp = copy.deepcopy(target_cards)
        for count in range(0, 3):
            temp.remove(i)
        for yi in temp:
            if yi != i:
                san_dai_yi = [i, i, i, yi]
                if san_dai_yi not in san_dai_yi_s:
                    san_dai_yi_s.append(san_dai_yi)
    return san_dai_yi_s


# 1 找到手牌的所有三带二
def find_san_dai_er(target_cards):
    three = []
    two = []
    target_cards.sort()
    for i in target_cards:
        if target_cards.count(i) >= 3:
            if i not in three:
                three.append(i)
    for i in target_cards:
        if target_cards.count(i) == 2:
            if i not in two:
                two.append(i)
    san_dai_er_s = []
    for i in three:
        for j in two:
            san_dai_er = [i, i, i, j, j]
            if san_dai_er not in san_dai_er_s:
                san_dai_er_s.append(san_dai_er)
    return san_dai_er_s


# length 代表组合的长度，并不是牌组长度
def find_s_z(target_cards, length):
    if length < 5:
        return []
    shunzis = []
    cards = copy.deepcopy(target_cards)
    # 去重
    for i in cards:
        while cards.count(i) > 1:
            cards.remove(i)
    cards.sort()
    for i in cards:
        shunzi = []
        num = i
        shunzi.append(num)
        can_make_up_shunzi = True
        for count in range(0, length - 1):
            num += 1
            shunzi.append(num)
            if num not in cards or num >= 15:
                can_make_up_shunzi = False
                break
        if can_make_up_shunzi:
            if shunzi not in shunzis:
                shunzis.append(shunzi)

    return shunzis


# length 代表组合的长度，并不是牌组长度

def find_two_lian_dui(target_cards, length):
    if length < 3:
        return []
    two = []
    lianduis = []
    cards = copy.deepcopy(target_cards)
    #
    for i in cards:
        if cards.count(i) >= 2:
            if i not in two:
                two.append(i)
    two.sort()
    for i in two:
        liandui = []
        num = i
        liandui.append(num)
        liandui.append(num)
        can_make_up_liandui = True
        for count in range(0, length - 1):
            num += 1
            liandui.append(num)
            liandui.append(num)
            if num not in two or num >= 15:
                can_make_up_liandui = False
                break
        if can_make_up_liandui:
            if liandui not in lianduis:
                lianduis.append(liandui)

    return lianduis


# 查找手牌中的三连对
# length 代表组合的长度，并不是牌组长度
def find_3_l_d(target_cards, length):
    if length < 2:
        return []
    three = []
    lianduis = []
    cards = copy.deepcopy(target_cards)
    for i in cards:
        if cards.count(i) >= 3:
            if i not in three:
                three.append(i)
    three.sort()
    for i in three:
        liandui = []
        num = i
        liandui.append(num)
        liandui.append(num)
        liandui.append(num)
        can_make_up_liandui = True
        for count in range(0, length - 1):
            num += 1
            liandui.append(num)
            liandui.append(num)
            liandui.append(num)
            if num not in three or num >= 15:
                can_make_up_liandui = False
                break
        if can_make_up_liandui:
            if liandui not in lianduis:
                lianduis.append(liandui)

    return lianduis


def find_f_j_single(target_cards, length):
    if length < 2:
        return []
    # 找出所有三连对
    three_liandui_s = find_3_l_d(target_cards, length)
    feijis = []
    for three_liandui in three_liandui_s:
        cards = copy.deepcopy(target_cards)
        for i in three_liandui:
            cards.remove(i)
        # 如果移除所有三连对之后的单张不够组合飞机
        if len(cards) < length:
            return []
        danzhang_s = []
        # 找出所有单张组合
        dan_zhang_arrangement(cards, length, [], danzhang_s)
        for danzhang in danzhang_s:
            feiji = []
            feiji.extend(three_liandui)
            feiji.extend(danzhang)
            feiji.sort()
            if feiji not in feijis:
                feijis.append(feiji)

    return feijis


def dan_zhang_arrangement(cards, count, danzhang, danzhang_s):
    count -= 1
    if count == -1:
        danzhang_s.append(danzhang)
        return danzhang
    for i in cards:
        new_cards = copy.deepcopy(cards)
        new_danzhang = copy.deepcopy(danzhang)
        new_danzhang.append(i)
        new_cards.remove(i)
        dan_zhang_arrangement(copy.deepcopy(new_cards), count, copy.deepcopy(new_danzhang), danzhang_s)

    return danzhang_s


# 查找手牌中的飞机
# length 代表组合的长度，并不是牌组长度
def find_f_j(target_cards, length):
    if length < 2:
        return []
    # 找出所有三连对
    three_liandui_s = find_3_l_d(target_cards, length)
    feijis = []
    for three_liandui in three_liandui_s:
        cards = copy.deepcopy(target_cards)
        for i in three_liandui:
            cards.remove(i)
        cards = find_dui_zi(cards)
        duizis = []
        # 找出所有对子组合
        dui_zi_arrangement(cards, length, [], duizis)
        for duizi in duizis:
            feiji = []
            feiji.extend(three_liandui)
            feiji.extend(duizi)
            feiji.sort()
            if feiji not in feijis:
                feijis.append(feiji)

    return feijis


# 找对子递归
def dui_zi_arrangement(cards, count, duizi, duizis):
    count -= 1
    if count == -1:
        duizis.append(duizi)
        return duizi
    for i in cards:
        new_cards = copy.deepcopy(cards)
        new_duizi = copy.deepcopy(duizi)
        new_duizi.extend(i)
        new_cards.remove(i)
        dui_zi_arrangement(copy.deepcopy(new_cards), count, copy.deepcopy(new_duizi), duizis)

    return duizis


def compare_cards(cards1, cards2, can_si_dai_er):
    """
    返回值为参数一是否大于参数二
    :param can_si_dai_er:
    :param cards1: str[] 牌值
    :param cards2: str[] 牌值
    :return:
    """
    cards1_type = play_card_correct(cards1, can_si_dai_er)
    cards2_type = play_card_correct(cards2, can_si_dai_er)

    cards1 = cards1.copy()
    cards2 = cards2.copy()

    # 任何一组牌为无效组合就返回空
    if cards1_type == CardType.invalid:
        return None

    if cards2_type == CardType.invalid:
        return None

    # 如果是王炸，返回结果
    if cards1_type == CardType.wang_zha:
        return True

    if cards2_type == CardType.wang_zha:
        return False

    # 如果任何一方是炸弹或都是炸弹，进行比较
    if cards1_type == CardType.zha_dan:
        if cards2_type == CardType.zha_dan:
            return compare_zha_dan(cards1, cards2)
        else:
            return True

    # if cards1_type == CardType.sidaier:

    if cards2_type == CardType.zha_dan:
        if cards1_type == CardType.zha_dan:
            return compare_zha_dan(cards1, cards2)
        else:
            return False

    # 如果不是炸弹并且牌型不同，无法比较
    # 如果不是炸弹并且长度不同，无法比较
    if cards1_type != cards2_type:
        return None
    if len(cards1) != len(cards2):
        return None
    else:
        if cards1_type == CardType.dan_zhang:
            return compare_dan_zhang(cards1, cards2)
        if cards1_type == CardType.dui_zi:
            return compare_dui_zi(cards1, cards2)
        if cards1_type == CardType.san_zhang:
            return compare_san_zhang(cards1, cards2)
        if cards1_type == CardType.san_dai_yi:
            return compare_s_d_y(cards1, cards2)
        if cards1_type == CardType.san_dai_er:
            return compare_san_dai_er(cards1, cards2)
        if cards1_type == CardType.shun_zi:
            return compare_s_z(cards1, cards2)
        if cards1_type == CardType.two_lian_dui:
            return compare_2_l_d(cards1, cards2)
        if cards1_type == CardType.fei_ji:
            return compare_f_j(cards1, cards2)
        if cards1_type == CardType.three_lian_dui:
            return compare_3_l_d(cards1, cards2)
        if cards1_type == CardType.fei_ji_single:
            return compare_f_j(cards1, cards2)
        if cards1_type == CardType.si_dai_er:
            return compare_si_dai_er(cards1, cards2)


def compare_si_dai_er(cards1, cards2):
    # cards1.sort()
    # cards2.sort()
    card1_si, card2_si = 0, 0
    for i in cards1:
        if cards1.count(i) == 4:
            card1_si = i
            break

    for i in cards2:
        if cards2.count(i) == 4:
            card2_si = i
            break

    return card1_si > card2_si


def compare_s_d_y(cards1, cards2):
    """
    参数一是否大于参数二
    :param cards1:
    :param cards2:
    :return:
    """
    card1_three, card2_three = 0, 0
    for i in cards1:
        if cards1.count(i) == 3:
            card1_three = i
            break

    for i in cards2:
        if cards2.count(i) == 3:
            card2_three = i
            break

    return card1_three > card2_three


def compare_san_dai_er(cards1, cards2):
    #     """
    #     参数一是否大于参数二
    #     :param cards1:
    #     :param cards2:
    #     :return:
    #     """
    cards1_three, cards2_three = 0, 0
    cards1.sort()
    cards2.sort()
    for i in cards2:
        if cards2.count(i) == 3:
            cards2_three = i
            break
    for i in cards1:
        if cards1.count(i) == 3:
            cards1_three = i
            break
    return cards1_three > cards2_three


def compare_dan_zhang(cards1, cards2):
    """
    参数一是否大于参数二
    :param cards1:
    :param cards2:
    :return:
    """
    return cards1 > cards2


def compare_dui_zi(cards1, cards2):
    """
    参数一是否大于参数二
    :param cards1:
    :param cards2:
    :return:
    """
    return cards1[0] > cards2[0]


def compare_san_zhang(cards1, cards2):
    """
        参数一是否大于参数二
        :param cards1:
        :param cards2:
        :return:
        """
    return cards1[0] > cards2[0]


def compare_zha_dan(cards1, cards2):
    """
    比较两个炸弹的大小
    :param cards1:
    :param cards2:
    :return:
    """
    return cards1[0] > cards2[0]


def compare_s_z(cards1, cards2):
    cards1.sort()
    cards2.sort()
    # 比较最大的一个元素
    return cards1[-1] > cards2[-1]


def compare_2_l_d(cards1, cards2):
    cards1.sort()
    cards2.sort()
    # 比较最大的一个元素
    return cards1[-1] > cards2[-1]


def compare_3_l_d(cards1, cards2):
    cards1.sort()
    cards2.sort()
    # 比较最大的一个元素
    return cards1[-1] > cards2[-1]


def compare_f_j(cards1, cards2):
    card1_three, card2_three = [], []
    for i in cards1:
        if cards1.count(i) >= 3 and i not in card1_three:
            card1_three.append(i)

    for i in cards2:
        if cards2.count(i) >= 3 and i not in card2_three:
            card2_three.append(i)

    card1_three.sort()
    card2_three.sort()

    return card1_three[-1] > card2_three[-1]
