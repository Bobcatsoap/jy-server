import copy
import random
import re
import datetime
import sys

from enum import Enum, unique
from time import time

from KBEDebug import DEBUG_MSG


@unique
class CardType(Enum):
    invalid = -1
    danzhang = 0
    duizi = 1
    sanzhang = 2
    zhadan = 4
    sandaiyi = 5
    wangzha = 6
    shunzi = 7
    twoliandui = 8
    threeliandui = 9
    feiji = 10


def play_card_correct(cards):
    # 将带有花色的牌转化为正常牌值
    cards = convert_cards_to_value(copy.deepcopy(cards))
    length = len(cards)
    if length == 1:
        return CardType.danzhang
    elif length == 2:
        if cards[0] == cards[1]:
            return CardType.duizi
        elif cards[0] + cards[1] == 33:
            return CardType.wangzha
        else:
            return CardType.invalid
    elif length == 3:
        card1, card2, card3 = cards[0], cards[1], cards[2]
        if card1 == card2 and card2 == card3:
            return CardType.sanzhang
        else:
            return CardType.invalid
    elif length == 4:
        if is_sandaiyi(cards):
            return CardType.sandaiyi
        elif is_zhadan(cards):
            return CardType.zhadan
        else:
            return CardType.invalid
    elif length == 5:
        if is_shunzi(cards):
            return CardType.shunzi
        else:
            return CardType.invalid
    elif length > 5:
        if is_shunzi(cards):
            return CardType.shunzi
        elif is_two_liandui(cards):
            return CardType.twoliandui
        elif is_three_liandui(cards):
            return CardType.threeliandui
        elif is_aircraft(cards):
            return CardType.feiji
        else:
            return CardType.invalid
    else:
        return CardType.invalid


def convert_cards_to_value(cards):
    cards_value = []
    for card in cards:
        card = re.sub('[a-z]', '', card)
        cards_value.append(int(card))
    return cards_value


def is_sandaiyi(cards):
    cards.sort()
    card1, card2, card3, card4 = cards[0], cards[1], cards[2], cards[3]
    # 三带一
    if card1 != card2 and card2 == card3 and card3 == card4:
        return True
    if card1 == card2 and card3 == card2 and card3 != card4:
        return True
    return False


def is_sandaiyi_4(cards):
    cards.sort()
    card1, card2, card3, card4 = cards[0], cards[1], cards[2], cards[3]
    # 三带一
    if card1 != card2 and card2 == card3 and card3 == card4:
        return True
    elif card1 == card2 and card3 == card2 and card3 != card4:
        return True
    return False


def is_sandaiyi_5(cards):
    card1, card2, card3, card4 = cards[0], cards[1], cards[2], cards[3]
    # 三带一
    if card1 == card2:
        if card2 == card3 and card3 != card4:  # 1,2,3 4
            return True
        elif card2 != card3 and card2 == card4:  # 1,2,4 3
            return True
    elif card1 != card2:
        if card1 == card3 and card3 == card4:  # 1,3,4 2
            return True
        if card2 == card3 and card3 == card4:  # 2,3,4 1
            return True
    return False


def is_sandaiyi_3(cards):
    a, b, c, d = -1, -1, 0, 0
    for card in cards:
        if a < 0:
            a = card
            c += 1
        elif a == card:
            c += 1

        elif b < 0:
            b = card
            d += 1
        elif b == card:
            d += 1
        else:
            return False

    if c == 1 or c == 3:
        return True
    else:
        return False


def is_sandaiyi_2(cards):
    three = -1
    one = -1
    for card in cards:
        if cards.count(card) == 1:
            one = card
        elif cards.count(card) == 3:
            three = card
        else:
            return False

    if three != -1 and one != -1:
        return True
    else:
        return False


def is_zhadan(cards):
    cards.sort()
    card1, card2, card3, card4 = cards[0], cards[1], cards[2], cards[3]
    if card1 == card2 and card2 == card3 and card3 == card4:
        return True
    return False


def is_aircraft(cards):
    # 飞机长度必须是5的倍数，并且大于等于10
    if len(cards) < 10:
        return False
    if len(cards) % 5 != 0:
        return False
    new_cards = copy.deepcopy(cards)
    three = []
    # 找到所有的三张
    for card in new_cards:
        if new_cards.count(card) == 3 and card not in three:
            three.append(card)
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


def is_shunzi(cards):
    if len(cards) < 5:
        return False
    for card in cards:
        if cards.count(card) != 1:
            return False
    # 排序
    cards.sort()
    # 不能包含大小王
    if cards[len(cards) - 1] > 15:
        return False
    for index in range(0, len(cards) - 1):
        if not cards[index] + 1 == cards[index + 1]:
            return False
    return True


def is_two_liandui(cards):
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
    # 不能包含大小王
    if new_cards[len(new_cards) - 1] > 15:
        return False

    for index in range(0, len(new_cards) - 1):
        if not new_cards[index] + 1 == new_cards[index + 1]:
            return False
    return True


def is_three_liandui(cards):
    if len(cards) < 9:
        return False
    if len(cards) % 3 != 0:
        return False
    for card in cards:
        if cards.count(card) != 3:
            return False
    new_cards = copy.deepcopy(cards)
    new_cards.sort()
    # 去重
    for card in new_cards:
        while new_cards.count(card) != 1:
            new_cards.remove(card)
    # 不能包含大小王
    if new_cards[len(new_cards) - 1] > 15:
        return False
    for index in range(0, len(new_cards) - 1):
        if not new_cards[index] + 1 == new_cards[index + 1]:
            return False
    return True


def generate_cards():
    # 黑红梅方
    card_type = ["a", "b", "c", "d"]
    # 14,A
    # 15,2
    # 16，小王
    # 17，大王
    card_num = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    card_pairs = []
    player1_cards = []
    player2_cards = []
    player3_cards = []
    cover_cards = []
    for card_color in card_type:
        for num in card_num:
            card_pairs.append(card_color + str(num))

    card_pairs.append(str(16))
    card_pairs.append(str(17))

    # 底牌数量
    cover_card_num = 3
    for index in range(0, len(card_pairs) - cover_card_num):
        card_pair = card_pairs[index]
        if index % 3 == 0:
            player1_cards.append(card_pair)
        if index % 3 == 1:
            player2_cards.append(card_pair)
        if index % 3 == 2:
            player3_cards.append(card_pair)
    # 底牌
    cover_cards = card_pairs[-cover_card_num:]
    all_cards = [player1_cards, player2_cards, player3_cards]
    return all_cards, cover_cards


def find_sandaiyi(target_cards):
    three = []
    # 找到所有三张
    for i in target_cards:
        if target_cards.count(i) >= 3:
            if i not in three:
                three.append(i)
    print(three)
    sandaiyis = []
    for i in three:
        temp = copy.deepcopy(target_cards)
        for count in range(0, 3):
            temp.remove(i)
        for yi in temp:
            if yi != i:
                sandaiyi = [i, i, i, yi]
                if not sandaiyis.__contains__(sandaiyi):
                    sandaiyis.append(sandaiyi)

    return sandaiyis


def find_shunzi(target_cards, length):
    shunzis = []
    cards = copy.deepcopy(target_cards)
    # 去重
    for i in cards:
        while cards.count(i) > 1:
            cards.remove(i)
    cards.sort()
    print(cards)
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


def find_twoliandui(target_cards, length):
    two = []
    lianduis = []
    cards = copy.deepcopy(target_cards)
    #
    for i in cards:
        if cards.count(i) == 2:
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


def find_threeliandui(target_cards, length):
    three = []
    lianduis = []
    cards = copy.deepcopy(target_cards)
    for i in cards:
        if cards.count(i) == 3:
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


def find_duizi(target_cards):
    cards = copy.deepcopy(target_cards)
    duizi = []
    for i in cards:
        if cards.count(i) >= 2:
            temp = []
            for j in range(0, 2):
                temp.append(i)
            if temp not in duizi:
                duizi.append(temp)

    return duizi


def find_feiji(target_cards, length):
    if length < 2:
        DEBUG_MSG("find feiji length two short: %s" % length)
        return []
    # 找出所有三连对
    three_liandui = find_threeliandui(target_cards, length)
    feijis = []
    for three in three_liandui:
        cards = copy.deepcopy(target_cards)
        # 移除三连对的牌
        for i in three:
            cards.remove(i)
        # 找出剩余牌中所有的对子
        duizis = []
        duizi_arrangement(copy.deepcopy(cards), length, [])
        # 如果对子的数跟三连对不匹配，则没有飞机


def duizi_arrangement(cards, count, duizi, duizis):
    count -= 1
    if count == -1:
        print(duizi)
        duizis.append(duizi)
        return duizi
    for i in cards:
        new_cards = copy.deepcopy(cards)
        new_duizi = copy.deepcopy(duizi)
        new_duizi.extend(i)
        new_cards.remove(i)
        duizi_arrangement(copy.deepcopy(new_cards), count, copy.deepcopy(new_duizi), duizis)

    return duizis


def generate_cards():
    # 黑红梅方
    card_type = ["a", "b", "c", "d"]
    # 14,A
    # 15,2
    # 16，小王
    # 17，大王
    card_num = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    card_pairs = []
    player1_cards = []
    player2_cards = []
    player3_cards = []
    cover_cards = []
    for card_color in card_type:
        for num in card_num:
            card_pairs.append(card_color + str(num))

    card_pairs.append(str(16))
    card_pairs.append(str(17))

    random.shuffle(card_pairs)
    random.shuffle(card_pairs)

    # 底牌数量
    cover_card_num = 3
    for index in range(0, len(card_pairs) - cover_card_num):
        card_pair = card_pairs[index]
        if index % 3 == 0:
            player1_cards.append(card_pair)
        if index % 3 == 1:
            player2_cards.append(card_pair)
        if index % 3 == 2:
            player3_cards.append(card_pair)
    # 底牌
    cover_cards = card_pairs[-cover_card_num:]
    all_cards = [player1_cards, player2_cards, player3_cards]
    return all_cards, cover_cards


def parse_card_value_to_client(cards):
    card_nums = []
    for card in cards:
        card_type = -1
        # 黑红梅方
        # a b c d

        if card.startswith('a'):
            card_type = 1
        elif card.startswith('b'):
            card_type = 2
        elif card.startswith('c'):
            card_type = 3
        elif card.startswith('d'):
            card_type = 0

        if card_type != -1:
            card_value = int(re.sub('[a-z]', '', card))
            card_num = (card_value - 3) * 4 + card_type
            card_nums.append(card_num)
        else:
            if int(card) == 16:
                card_nums.append(52)
            if int(card) == 17:
                card_nums.append(53)
    return card_nums


# 转为服务端牌值
def parse_card_to_server(cards):
    if len(cards) == 0:
        return []
    card_nums = []
    for card in cards:
        card_type = card % 4
        card_value = int(card / 4) + 3
        card_color = ''
        if card_type == 0:
            card_color = 'd'
        elif card_type == 1:
            card_color = 'a'
        elif card_type == 2:
            card_color = 'b'
        elif card_type == 3:
            card_color = 'c'

        if card == 52:
            card_nums.append(str(16))
        elif card == 53:
            card_nums.append(str(17))
        else:
            card_nums.append(str(card_color) + str(card_value))

    return card_nums

#
# t1, t2, t3, t4, t5 = 0, 0, 0, 0, 0
# for x in range(0, 1000000):
#     num = []
#     for i in range(1, 5):
#         num.append(random.randint(3, 15))
#
#     new_num = copy.deepcopy(num)
#     start = time()
#     is_sandaiyi(new_num)
#     stop = time()
#     t1 += stop - start
#
#     new_num = copy.deepcopy(num)
#     start = time()
#     is_sandaiyi_2(new_num)
#     stop = time()
#     t2 += stop - start
#
#     new_num = copy.deepcopy(num)
#     start = time()
#     is_sandaiyi_3(new_num)
#     stop = time()
#     t3 += stop - start
#
#     new_num = copy.deepcopy(num)
#     start = time()
#     is_sandaiyi_4(new_num)
#     stop = time()
#     t4 += stop - start
#
#     new_num = copy.deepcopy(num)
#     start = time()
#     is_sandaiyi_5(new_num)
#     stop = time()
#     t5 += stop - start

