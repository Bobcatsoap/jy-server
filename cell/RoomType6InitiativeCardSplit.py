import collections
import copy
import math
import time
from random import shuffle

"""
主动出牌牌型分割，为主动出牌提供参考

输入：
    [3, 3, 3, 4, 5, 5, 6, 7, 8, 9, 10, 11, 11, 13, 15, 15]

输出：

    total_list:
        [[15, 15], [4, 5, 6, 7, 8, 9, 10], [3, 3, 3, 5], [11, 11], [13]]
    total_dic:
        {'er': [15, 15], 'shunZi': [4, 5, 6, 7, 8, 9, 10], 'sanDaiYi': [[3, 3, 3, 5]], 'duiZi': [[11, 11]], 'danZhang': [13]}
    
    total_list为分组后的手牌，每个数组为一手
    total_dic为分组并归类后的手牌


"""


def split(cards, make_single_less=False):
    """
    将手牌分割成list，dict
    :param make_single_less: 让单张尽量少的策略开启
    :param cards:
    :return:
    """
    cards = cards.copy()
    # 原始手牌
    origin_cards = cards.copy()
    # 返回值
    total_dic = {}
    total_list = []

    w_z = find_w_z(cards)
    remove_list(cards, w_z)

    z_d = find_z_d(cards)
    remove_list(cards, z_d)

    _2 = find_number(cards, 15)
    remove_list(cards, _2)

    _joker = find_joker(cards)
    remove_list(cards, _joker)

    # 找最大的飞机
    _3_l_d = find_3_l_d(cards)
    remove_list(cards, _3_l_d)

    # 找顺子
    _s_z = find_s_z(cards)
    remove_list(cards, _s_z)

    # 找出一个最长的连对
    _l_d = find_l_d(cards)
    remove_list(cards, _l_d)

    # 找出所有的三张
    _san_zhang = find_san_zhang(cards)
    remove_list(cards, _san_zhang)

    # 找出所有对子
    _dui_zi = find_dui_zi(cards)
    remove_list(cards, _dui_zi)

    # 如果开启让单张尽量少，不延长顺子
    if not make_single_less:
        # 通过对子延长顺子
        expand_s_z(_s_z, _dui_zi)

    # 合并顺子
    merge_s_z(_s_z)

    # 找出所有单张
    _dan_zhang = find_dan_zhang(cards)
    remove_list(cards, _dan_zhang)

    # 组合单张和飞机
    connect_f_j_dan_zhang(_3_l_d, _dan_zhang)
    # 组合单张和三带一
    _san_dai_yi = connect_s_d_dan_zhang(_san_zhang, _dan_zhang)

    # 组合对子和飞机
    connect_f_j_dui_zi(_3_l_d, _dui_zi)
    # 组合对子和三带
    _san_dai_er = connect_s_d_dui_zi(_san_zhang, _dui_zi)

    if _2 and _2[0]:
        total_dic['er'] = _2
        total_list.extend(_2)
    if _joker and _joker[0]:
        total_dic['joker'] = _joker
        total_list.extend(_joker)
    # 一维数组，最长的三联对
    if _3_l_d and _3_l_d[0]:
        total_dic['feiJi'] = _3_l_d
        total_list.extend(_3_l_d)
    if _s_z and _s_z[0]:
        total_dic['shunZi'] = _s_z
        total_list.extend(_s_z)
    if _l_d and _l_d[0]:
        total_dic['lianDui'] = _l_d
        total_list.extend(_l_d)
    if _san_zhang and _san_zhang[0]:
        total_dic['sanZhang'] = _san_zhang
        total_list.extend(_san_zhang)
    if _san_dai_er and _san_dai_er[0]:
        total_dic['sanDaiEr'] = _san_dai_er
        total_list.extend(_san_dai_er)
    if _san_dai_yi and _san_dai_yi[0]:
        total_dic['sanDaiYi'] = _san_dai_yi
        total_list.extend(_san_dai_yi)
    if _dui_zi and _dui_zi[0]:
        total_dic['duiZi'] = _dui_zi
        total_list.extend(_dui_zi)
    if _dan_zhang and _dan_zhang[0]:
        total_dic['danZhang'] = _dan_zhang
        total_list.extend(_dan_zhang)
    if z_d and z_d[0]:
        total_dic['zhaDan'] = z_d
        total_list.extend(z_d)
    if w_z and w_z[0]:
        total_dic['wangZha'] = w_z
        total_list.extend(w_z)

    return total_list, total_dic


def connect_f_j_dan_zhang(_3_l_d, _d_z):
    if not _3_l_d or not _d_z:
        return
    _d_z.sort()

    for _3 in _3_l_d:
        if len(_d_z) < len(_3) / 3:
            return
        for i in range(int(len(_3) / 3)):
            number = _d_z.pop(0)
            _3.extend(number)


def connect_f_j_dui_zi(_3_l_d, _dui_zi):
    if not _3_l_d or not _dui_zi:
        return
    _dui_zi.sort()

    if len(_dui_zi) < len(_3_l_d) / 3:
        return
    for i in range(int(len(_3_l_d) / 3)):
        number = _dui_zi.pop(0)
        _3_l_d.extend(number)


def connect_s_d_dui_zi(_san_zhang, _dui_zi):
    """
    连接三张和对子
    :param _san_zhang:
    :param _dui_zi:
    :return:
    """
    if not _san_zhang or not _dui_zi:
        return
    _san_dai_er = []
    length = min(len(_dui_zi), len(_san_zhang))
    for i in range(length):
        _ = _dui_zi.pop(0)
        _3 = _san_zhang.pop(0)
        _3.extend(_)
        _san_dai_er.append(_3)
    return _san_dai_er


def connect_s_d_dan_zhang(_san_zhang, _d_z):
    """
    连接三张和单张
    :param _san_zhang:
    :param _d_z:
    :return:
    """
    if not _san_zhang or not _d_z:
        return
    _san_dai_yi = []
    length = min(len(_d_z), len(_san_zhang))
    for i in range(length):
        _ = _d_z.pop(0)
        _3 = _san_zhang.pop(0)
        _3.extend(_)
        _san_dai_yi.append(_3)
    return _san_dai_yi


def find_w_z(target_cards):
    """
    找出手牌中的王炸
    :param target_cards:
    :return:
    """
    if 16 in target_cards and 17 in target_cards:
        return [[16, 17]]
    return []


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


def find_number(cards, number):
    """
    找某个数字
    :param cards:
    :param number:
    :return:
    """
    numbers = []
    for c in cards:
        if c == number:
            numbers.append(c)
    return [numbers]


def find_joker(cards):
    numbers = []
    for c in cards:
        if c == 16 or c == 17:
            numbers.append(c)
    return [numbers]


def find_3_l_d(cards):
    """
    找三连对（飞机不带翅膀）
    :param cards:
    :return:
    """
    _3 = []
    _3_l_d_s = []
    cards = cards.copy()
    for i in cards:
        if cards.count(i) >= 3:
            if i not in _3:
                _3.append(i)
    _3.sort()

    for i in _3:
        num = i
        _3_l_d = []
        while num in _3 and num < 15:
            _3_l_d.append(num)
            num += 1

        if len(_3_l_d) >= 2:
            _3_l_d_s.append(_3_l_d)

    t = []
    if _3_l_d_s:
        _3_l_d_s.sort(key=lambda x: len(x), reverse=True)
        t = _3_l_d_s[0] * 3
        t.sort()
    return [t]


def find_san_zhang(cards):
    san_zhang_s = []
    checked = []
    for c in cards:
        if cards.count(c) == 3 and c not in checked:
            san_zhang_s.append([c, c, c])
            checked.append(c)

    return san_zhang_s


def find_dui_zi(cards):
    dui_zi = []
    checked = []
    for c in cards:
        if cards.count(c) == 2 and c not in checked:
            dui_zi.append([c, c])
            checked.append(c)

    return dui_zi


def expand_s_z(s_z, dui_zi):
    if not s_z or not dui_zi:
        return
    if not s_z[0] or not dui_zi[0]:
        return
    expand = []
    for s in s_z:
        for d in dui_zi:
            i = d[0]
            if i < 10 and (i == s[0] - 1 or i == s[-1] + 1):
                expand.append(i)

        for e in expand:
            if [e, e] in dui_zi and e not in s:
                dui_zi.remove([e, e])
                s.append(e)

        s.sort()

    dui_zi.sort()


def merge_s_z(s_z):
    merge = []
    for s in s_z:
        for s2 in s_z:
            if not s or not s2:
                continue
            if s[-1] + 1 == s2[0] or s2[-1] + 1 == s[0]:
                if [s, s2] not in merge:
                    merge.append([s, s2])
    for i in merge:
        s1 = i[0]
        s2 = i[1]
        s = s1 + s2
        if s1 in s_z and s2 in s_z:
            s_z.remove(s1)
            s_z.remove(s2)
            s_z.append(s)


def find_dan_zhang(cards):
    dan_zhang = []
    for c in cards:
        if cards.count(c) == 1 and c not in dan_zhang:
            dan_zhang.append([c])

    return dan_zhang


def find_s_z(cards):
    """
    找顺子
    :param cards:
    :return:
    """
    _1 = []
    _s_z_s = []
    cards = cards.copy()
    for i in cards:
        if i not in _1:
            _1.append(i)
    _1.sort()

    for i in _1:
        num = i
        _s_z = []
        while num in _1 and num < 15:
            _s_z.append(num)
            num += 1

        if len(_s_z) >= 5:
            _s_z_s.append(_s_z)

    # 顺子从大到小排列
    _s_z_s.sort(key=lambda x: len(x), reverse=True)
    # 只保留最长的顺子
    _s_z_s = _s_z_s[:1]
    max_s_z = []
    for _s_z in _s_z_s:
        cards_copy = cards.copy()
        remove_all(cards_copy, _s_z)
        # 分裂处理顺子
        s = split_s_z(cards_copy, _s_z)
        if s:
            length = len(s)
            max_length = len(max_s_z)
            # 如果是两个小顺子
            if length == 2:
                length = len(s[0]) + len(s[1])
            if max_length == 2:
                max_length = len(max_s_z[0]) + len(max_s_z[1])

            if length > max_length:
                max_s_z = s
    if len(max_s_z) == 2:
        return max_s_z
    else:
        return [max_s_z]


def find_l_d(cards):
    """
    找最长连对
    :param cards:
    :return:
    """
    _2 = []
    _2_l_d_s = []
    _cards = cards.copy()
    for i in _cards:
        if _cards.count(i) >= 2:
            if i not in _2:
                _2.append(i)
    _2.sort()

    for i in _2:
        num = i
        _2_l_d = []
        while num in _2 and num < 15:
            _2_l_d.append(num)
            num += 1

        if len(_2_l_d) >= 3:
            _2_l_d_s.append(_2_l_d)

    t = []
    if _2_l_d_s:
        _2_l_d_s.sort(key=lambda x: len(x), reverse=True)
        t = _2_l_d_s[0] * 2
        t.sort()
    return [t]


def split_s_z(cards, _s_z):
    # 分裂出连对
    _2_l_d_s_z = s_z_split_2_l_d(cards, _s_z)
    # 如果可以分裂出两个
    _two_s_z = s_z_split_2_s_z(cards, _2_l_d_s_z)
    if len(_two_s_z) == 2:
        return _two_s_z
    else:
        # 分裂出三张
        _3_z_s_z = s_z_split_3_z(cards, _2_l_d_s_z)
        # 分裂出对子
        _2_z_s_z = s_z_split_2_z(cards, _3_z_s_z)
        if len(_2_z_s_z) < 5:
            _2_z_s_z = []
        return _2_z_s_z


def s_z_split_2_s_z(cards, s_z):
    """
    分裂为两个顺子
    找出重复的点
    [3,4,5,6,7,8,9]
        [5,6,7]
    :param cards:
    :param s_z:
    :return:
    """
    if not s_z:
        return s_z
    cards.sort()
    # 找出开始重复的点
    repeats = []
    for s in s_z:
        repeat = []
        num = s
        while num in cards and num < 15:
            repeat.append(num)
            num += 1
        if len(repeat) >= 2:
            repeats.append(repeat)
    if not repeats:
        return s_z

    repeats.sort(key=lambda x: len(x), reverse=True)
    max_repeat = repeats[0]

    s1 = []
    for s in s_z:
        s1.append(s)
        if s == max_repeat[-1]:
            break

    s2 = []
    for s in reversed(s_z):
        s2.append(s)
        if s == max_repeat[0]:
            break

    s1.sort()
    s2.sort()

    shun_zi_s = []
    if len(s1) >= 5:
        shun_zi_s.append(s1)

    if len(s2) >= 5:
        shun_zi_s.append(s2)
    return shun_zi_s


def s_z_split_2_l_d(cards, s_z):
    """
    从顺子中分出二连对
    :param cards:
    :param s_z:
    :return:
    """
    if not s_z:
        return []
    _2_l_d_s = []
    for s in s_z:
        num = s
        _2_l_d = []
        # 如果能和手牌里的牌组成连对
        while num in cards and num < 15:
            _2_l_d.append(num)
            num += 1
        if len(_2_l_d) >= 3:
            _2_l_d_s.append(_2_l_d)
    # 二连对从小到大排列
    _2_l_d_s.sort(key=lambda x: len(x), reverse=True)
    # 找到一个去掉后仍可以组成顺子的二连对
    for _2 in _2_l_d_s:
        if len(s_z) - len(_2) >= 5:
            if _2[0] == s_z[0] or _2[-1] == s_z[-1]:
                s_z_copy = s_z.copy()
                for _ in _2:
                    s_z_copy.remove(_)
                return s_z_copy
        else:
            # 如果组不成顺子，但二连对很长
            if len(_2) > len(s_z) / 2:
                return []
    return s_z


def s_z_split_3_z(cards, s_z):
    """
    从顺子中分出三张
    :param cards:
    :param s_z:
    :return:
    """
    if not s_z:
        return []
    _3_z = []
    if cards.count(s_z[0]) >= 2:
        _3_z.append(s_z[0])
    if cards.count(s_z[-1]) >= 2:
        _3_z.append(s_z[-1])
    # 二连对从小到大排列
    _3_z.sort(reverse=True)
    # 找到一个去掉后仍可以组成顺子的二连对
    s_z_copy = s_z.copy()
    for _3 in _3_z:
        s_z_copy.remove(_3)
        if len(s_z_copy) <= 5:
            return s_z_copy
    return s_z_copy


def s_z_split_2_z(cards, s_z):
    """
    从顺子中分出两张
    :param cards:
    :param s_z:
    :return:
    """
    if not s_z:
        return []
    if len(s_z) < 7:
        return s_z
    _liang_zhang = []
    # 如果手里有顺子的头尾，把头尾放回去
    if cards.count(s_z[0]) >= 1 and cards.count(s_z[-1]) >= 1:
        _liang_zhang.append(s_z[0])
        _liang_zhang.append(s_z[-1])
    else:
        return s_z
    _liang_zhang.sort(reverse=True)
    s_z_copy = s_z.copy()
    for _ in _liang_zhang:
        s_z_copy.remove(_)
    return s_z_copy


def remove_list(origin: [], remove: []):
    for i in remove:
        for ii in i:
            if ii in origin:
                origin.remove(ii)


def remove_all(origin: [], remove: []):
    for i in remove:
        if i in origin:
            origin.remove(i)