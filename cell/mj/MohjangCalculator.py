import time

from KBEDebug import DEBUG_MSG
from mj import MohjangTable

MAN = 0
MAN1 = 0
MAN2 = 1
MAN3 = 2
MAN4 = 3
MAN5 = 4
MAN6 = 5
MAN7 = 6
MAN8 = 7
MAN9 = 8
PIN = 9
PIN1 = 9
PIN2 = 10
PIN3 = 11
PIN4 = 12
PIN5 = 13
PIN6 = 14
PIN7 = 15
PIN8 = 16
PIN9 = 17
SOU = 18
SOU1 = 18
SOU2 = 19
SOU3 = 20
SOU4 = 21
SOU5 = 22
SOU6 = 23
SOU7 = 24
SOU8 = 25
SOU9 = 26
TON = 27
NAN = 28
SHA = 29
PEI = 30
HAK = 31
HAT = 32
CHU = 33

tbl = {}
tbl_seven_pair = {}

MohjangTable.init(tbl, tbl_seven_pair)


def is_hu_pai(h_cards, card_range, pai=-1, magic_red=False):
    """
    有pai参数,hand_cards长度改为3n + 1；无pai参数,hand_cards长度改为3n + 2
    :param magic_red: 红中赖子
    :param card_range: 牌范围
    :param h_cards:手牌
    :param pai: 待验证是否可以胡的牌
    :return: true 胡牌
    """
    _tsp = h_cards.copy()
    if pai != -1:
        _tsp.append(pai)

    return is_hu(_tsp, card_range, magic_red=magic_red)


def is_hu(cards, card_range, magic_red=False):
    """
    是否胡牌判断
    :param magic_red:
    :param card_range:
    :param cards:
    :return:
    """
    n = analyse(cards)
    # 判胡结果（元组）
    # 筛选可能牌范围
    ret = agar_list(n, card_range, magic_red=magic_red)
    return ret


def analyse(hai):
    n = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for i in hai:
        n[i] += 1
    return n


def calc_key(n, pos):
    # n = []
    # pos = []

    p = -1
    x = 0
    pos_p = 0
    b = False

    for i in range(0, 3):
        for j in range(0, 9):
            if n[i * 9 + j] == 0:
                if b:
                    b = False
                    x |= 0x1 << p
                    p += 1
            else:
                p += 1
                b = True

                pos[pos_p] = i * 9 + j
                pos_p += 1
                t = n[i * 9 + j]
                if t == 2:
                    x |= 0x3 << p
                    p += 2
                elif t == 3:
                    x |= 0xF << p
                    p += 4
                elif t == 4:
                    x |= 0x3F << p
                    p += 6
        if b:
            b = False
            x |= 0x1 << p
            p += 1
    for i in range(TON, CHU + 1):
        if n[i] > 0:
            p += 1
            pos[pos_p] = i
            pos_p += 1

            t = n[i]
            if t == 2:
                x |= 0x3 << p
                p += 2
            elif t == 3:
                x |= 0xF << p
                p += 4
            elif t == 4:
                x |= 0x3F << p
                p += 6

            x |= 0x1 << p
            p += 1
    return x


def agari(key):
    if key in tbl.keys():
        return tbl[key]


def seven_pair(key):
    """
    判断是否是七星对
    :param key:
    :return:
    """
    if key in tbl_seven_pair.keys():
        return tbl_seven_pair[key]


def agar_list(n, c_range, magic_red=False):
    """
    胡牌类型：0：平胡,1：七星对,2：豪华七星对
    :param c_range:
    :param magic_red: 红中赖子开关
    :param n:
    :return:
    # 1.是否胡
    # 2.胡牌类型：0，1，2 平胡，七星胡，豪华七星胡
    # 3.牌的原始值，七星胡时无效
    """
    pos = []
    for i in range(0, 14):
        pos.append(0)
    key = calc_key(n, pos)
    if magic_red:
        red_count = n[HAK]
    # 不开红中癞子时
    else:
        red_count = 0
    hu_type = -1
    if red_count <= 0:
        normal_hu = agari(key)
        seven_hu = seven_pair(key)
        card_value = [(normal_hu, n)]
    elif red_count == 4:
        seven_hu = seven_pair_with_red(n)
        normal_hu = True
        card_value = [(normal_hu, n)]
    else:
        result = []
        magic_red_check(red_count, [], n, c_range[0], c_range, result)
        seven_hu = seven_pair_with_red(n)
        if result:
            normal_hu = True
            card_value = result
        else:
            normal_hu = False
            card_value = []
    if normal_hu:
        hu_type = 0
    if seven_hu == [0x1]:
        hu_type = 1
    if seven_hu == [0x0]:
        hu_type = 2

    return normal_hu or seven_hu is not None, hu_type, convert_to_origin(card_value)


def convert_to_origin(return_cards):
    """
    将牌转为原始牌值
    :param cards:
    :return:
    """
    origin_cards = []
    for _tuple in return_cards:
        cards = _tuple[1]
        _c = []
        for index, value in enumerate(cards):
            if value > 0:
                for count in range(value):
                    _c.append(index)
        origin_cards.append(_c)
    return origin_cards


def seven_pair_with_red(cards):
    sum = 0
    for i in cards:
        if i > 0:
            sum += i
    if sum != 14:
        return
    n_pai2 = cards.copy()
    red_count = n_pai2[HAK]
    n_pai2[HAK] = 0
    single_count = 0
    gang_count = 0
    #  取单的数目（1个或3个）、杠的数目（3个或4个）
    for i in n_pai2:
        single_count += i % 2
        if i > 2:
            gang_count += 1

    #  红中的个数大于单的数目
    red_count -= single_count
    if red_count == 0:
        if gang_count > 0:
            return [0x0]  # 豪华七星对
        return [0x1]  # 七星对
    elif red_count == 2:
        return [0x0]  # 豪华七星对


def select_perhaps_pai(hand_cards, lst_enable, magic_red_switch=False):
    """
    通过手中牌，选择相邻牌作为可能牌，风、三元牌无相邻牌，1,9只有一个相邻牌
    :param  hand_cards:  手中牌
    :param  lst_enable:  确定可能值
    :return:
    """
    set_enable = set()
    for j in range(34):
        if hand_cards[j] > 0:
            set_enable.add(j)
            if j == 0 or j == 9 or j == 18:
                set_enable.add(j + 1)
            elif j == 8 or j == 17 or j == 26:
                set_enable.add(j - 1)
            elif j >= 27:
                pass
            else:
                set_enable.add(j + 1)
                set_enable.add(j - 1)

    for i in set_enable:
        lst_enable.append(i)

    # 如果开启红中癞子并且取值范围内没有红中，添加红中
    if magic_red_switch and 31 not in lst_enable:
        lst_enable.append(31)


def magic_red_check(red_count, other_red_value, hand_cards, start_count, card_range, return_cards):
    """
    :param card_range:
    :param red_count: 有几个红中需要
    :param other_red_value: 其他红中对应数字列表
    :param hand_cards: 手中牌
    :param start_count: 为防止重复组合,需要从数字多少开始0~33
    :return: 匹配结果
    """
    if red_count == 1:
        n_pai2 = hand_cards.copy()
        n_pai2[HAK] = 0
        for item in other_red_value:
            n_pai2[item] += 1
        pos = []
        for j in range(0, 14):
            pos.append(0)
        _index = card_range.index(start_count)
        for i in card_range[_index:]:  # 组合红中代表值,进行计算判断
            n_pai3 = n_pai2.copy()
            n_pai3[i] += 1
            pos1 = pos.copy()
            key = calc_key(n_pai3, pos1)
            result_normal = agari(key)
            if result_normal is not None:
                return_cards.append((result_normal, n_pai3))
    else:
        _index = card_range.index(start_count)
        for i in card_range[_index:]:
            lst_append = other_red_value.copy()
            lst_append.append(i)
            magic_red_check(red_count - 1, lst_append, hand_cards, i, card_range, return_cards)
            # if return_cards:
            #     return return_cards


def agariPos(n, pos):
    key = calc_key(n, pos)
    return agari(key)
