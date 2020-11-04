TONG = 0
TONG_1 = 0
TONG_2 = 1
TONG_3 = 2
TONG_4 = 3
TONG_5 = 4
TONG_6 = 5
TONG_7 = 6
TONG_8 = 7
TONG_9 = 8
TIAO = 1
TIAO_1 = 9
TIAO_2 = 10
TIAO_3 = 11
TIAO_4 = 12
TIAO_5 = 13
TIAO_6 = 14
TIAO_7 = 15
TIAO_8 = 16
TIAO_9 = 17
WAN = 2
WAN_1 = 18
WAN_2 = 19
WAN_3 = 20
WAN_4 = 21
WAN_5 = 22
WAN_6 = 23
WAN_7 = 24
WAN_8 = 25
WAN_9 = 26
ZI = 3
FENG = 3
FENG_DONG = 27
FENG_NAN = 28
FENG_XI = 29
FENG_BEI = 30
SUNYUAN = 4
SUNYUAN_ZHONG = 31
SUNYUAN_FA = 32
SUNYUAN_BAI = 33

YAO_PAI = [TONG_1, TONG_9, TIAO_1, TIAO_9, WAN_1, WAN_9]
ZI_PAI = [FENG_DONG, FENG_NAN, FENG_XI, FENG_BEI, SUNYUAN_ZHONG, SUNYUAN_FA, SUNYUAN_BAI]
YAO_13 = YAO_PAI + ZI_PAI
TUI_BU_DAO = [TONG_1, TONG_2, TONG_3, TONG_4, TONG_5, TONG_8, TONG_9, TIAO_2, TIAO_4, TIAO_5, TIAO_6, TIAO_8, TIAO_9, SUNYUAN_BAI]
LV_YI_SE = [TIAO_2, TIAO_3, TIAO_4, TIAO_6, TIAO_8, SUNYUAN_FA]


def isQingYiSe(shou_pai, chi=[], peng=[], gang=[]):
    """
    清一色：指由一种花色的序数牌组成的和牌。
    :param shou_pai:
    :param chi:只包含牌数组
    :param peng:只包含牌数组
    :param gang:只包含牌数组，包括小明杠、大明杠和暗杠
    :return:
    """
    result = getColor(shou_pai, chi=chi, peng=peng, gang=gang)
    return result[3] == 0 and (result[0] + result[1] + result[2]) == 1


def isZiYiSe(shou_pai, chi=[], peng=[], gang=[]):
    """
    字一色：手牌全部由字牌组成的和牌。
    """
    result = getColor(shou_pai, chi=chi, peng=peng, gang=gang)
    return result[3] == 1 and (result[0] + result[1] + result[2]) == 0


def isHunYiSe(shou_pai, chi=[], peng=[], gang=[]):
    """
    混一色：手牌只有字牌加上万，条，饼中的一种牌时成立。
    """
    result = getColor(shou_pai, chi=chi, peng=peng, gang=gang)
    return result[3] == 1 and (result[0] + result[1] + result[2]) == 1


def getColor(shou_pai, chi=[], peng=[], gang=[]):
    """
    :return: (hasTong, hasTiao, hasWan, hasZi)
    """
    all_shou_pai = shou_pai + chi + peng + gang
    _tong = 0
    _tiao = 0
    _wan = 0
    _zi = 0
    for i in all_shou_pai:
        t = i // 9
        if t == TONG:
            _tong = 1
        if t == TIAO:
            _tiao = 1
        if t == WAN:
            _wan = 1
        if t == ZI:
            _zi = 1
    return _tong, _tiao, _wan, _zi


def isPengPengHu(shou_pai, chi=[]):
    """
    碰碰胡：由4副刻子（或杠）、将牌组成的和牌
    """
    if chi is not None and len(chi) > 0:
        return False
    arr = toArray(shou_pai)
    is_first = True
    for i in arr:
        if i == 2:
            if is_first:
                is_first = False
                continue
            else:
                return False
        if i != 3:
            return False
    return True 


def isQiDuiHu(shou_pai):
    """
    由七个对子组成和牌
    :return: (first, second, three) first: true表示七对； second: true表示连七对; three: int 内含暗杠数量
    """
    if len(shou_pai) != 14:
        return False, False, 0
    arr = toArray(shou_pai)
    pair_count = 0;
    s = -1
    for i, _c in enumerate(arr):
        if _c == 1 or _c == 3:
            return False, False, 0
        if _c == 2 or _c == 4:
            pair_count += 1
            if pair_count == 1:
                s = i
    lian = False
    if pair_count == 7:
        a = s // 9
        b = (s + 6) // 9
        if a == b:
            for i in range(s, s + 7):
                if i == s + 6:
                    lian = True
                if arr[i] != arr[i + 1]:
                    break
    return True, lian, 7 - pair_count


def isJinJiDuLi(shou_pai):
    """
    金鸡独立：当手中牌通过碰吃杠最后只剩一张牌的牌型。可以吃碰自己本回合打出去的牌
    """
    if len(shou_pai) == 2:
        return True
    return False


def toArray(shou_pai):
    arr = [0] * 34
    for i in shou_pai:
        arr[i] += 1
    return arr


# -------------------------- 特殊胡 --------------------------
def is13yao(shou_pai):
    """
    十三幺（国士无双）：十三幺九。由1筒（饼）、9筒（饼）、1条（索）、9条（索）、1万、9万、东、南、西、北、中、发、白十三种牌统称幺九牌。
    胡牌时这十三种牌某一种有两枚，而另十二种各一枚，共计十四枚，即构成十三幺。
    :param shou_pai:
    :return:
    """
    if len(shou_pai) != 14:
        return False
    t = set(shou_pai)
    if len(t) != 13:
        return False
    for i in t:
        if i not in YAO_13:
            return False
    return True


def quanBuKao(shou_pai):
    """
    :return: (first, second) first: true为全不靠; second: true为七星全不靠
    """
    if len(shou_pai) != 14:
        return False, False
    arr = toArray(shou_pai)
    # 如果有对子或刻子或杠，否
    _t = 0
    qi_xiang = 0
    for i, c in enumerate(arr):
        if c > 1:
            return False, False
        if i % 9 == 0:
            _t = 2
        if i < 27:
            if c == 1:
                if _t < 2:
                    return False, False
                _t = 0
            else:
                _t += 1
        else:
            if c == 1:
                qi_xiang += 1
    return True, qi_xiang == 7

