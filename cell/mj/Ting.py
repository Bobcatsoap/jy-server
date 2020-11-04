from mj import AgariUtils


def getOutTing(shou_pai, all_pai, wild_card=[]):
    """
    算出打出什么牌之后，可以听牌
    :param shou_pai: 此时的手牌数量应该是3n + 2
    :param all_pai: 用到的牌
    :param wild_card: 万能牌
    :return: [] 打出之后，可以听的数组
    """
    ret = []
    if len(shou_pai) % 3 != 2:
        return ret

    sp_copy = shou_pai.copy()
    for i in range(0, len(sp_copy)):
        _t = sp_copy.pop(0)
        r = getHuPai(sp_copy, all_pai=all_pai, wild_card=wild_card)
        if len(r) > 0:
            ret.append(_t)
        sp_copy.append(_t)

    return ret


def getOutTing2(shou_pai, all_pai, wild_card=[]):
    """
    算出打出什么牌之后，可以听牌，直接返回的是给客户端的消息的格式
    :param shou_pai: 此时的手牌数量应该是3n + 2
    :param all_pai: 用到的牌
    :param wild_card: 万能牌
    :return: {outpai:[canHuPai, canHuPai], outpai:[canHuPai]} 打出之后，可以听的数组
    """
    ret = {}
    # 牌的数量不对，直接返回
    if len(shou_pai) % 3 != 2:
        return ret

    sp_copy = shou_pai.copy()
    # 避免重复计算
    aleary_compute = []
    for i in range(0, len(sp_copy)):
        _t = sp_copy.pop(0)
        if _t not in aleary_compute:
            r = getHuPai(sp_copy, all_pai=all_pai, wild_card=wild_card)
            if len(r) > 0:
                ret[_t] = r
            aleary_compute.append(_t)
        sp_copy.append(_t)

    return ret


def getHuPai(shou_pai, all_pai, wild_card=[]):
    """
    获取可以胡的牌
    :param shou_pai: 此时手牌的数量应该是 3n + 1
    :param all_pai: 用到的牌
    :param wild_card: 万能牌
    :return: [] 可以胡到牌
    """
    ret = []
    if len(shou_pai) % 3 != 1:
        return ret

    for p in all_pai:
        if AgariUtils.isHuPai(shou_pai, pai=p, wild_card=wild_card, all_pai=all_pai):
            ret.append(p)

    return ret


