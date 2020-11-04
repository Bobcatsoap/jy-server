"""
评分，大小估计

"""


def get_score(split_cards_dic):
    """
    根据牌型分类评分
    :param split_cards_dic:
    :return:
    """
    total_score = 0
    if 'danZhang' in split_cards_dic:
        for _ in split_cards_dic['danZhang']:
            dan_zhang_score = _[0] - 10
            total_score += dan_zhang_score

    if 'joker' in split_cards_dic:
        for _ in split_cards_dic['joker']:
            joker_score = _[0] - 10
            total_score += joker_score

    if 'er' in split_cards_dic:
        for _ in split_cards_dic['er']:
            er_score = _[0] - 10
            total_score += er_score

    if 'duiZi' in split_cards_dic:
        for _ in split_cards_dic['duiZi']:
            dui_zi_score = _[0] - 10
            if dui_zi_score > 0:
                dui_zi_score *= 1.5
            total_score += dui_zi_score

    if 'sanZhang' in split_cards_dic:
        for _ in split_cards_dic['sanZhang']:
            san_zhang_score = _[0] - 10
            if san_zhang_score > 0:
                san_zhang_score *= 2
            total_score += san_zhang_score

    if 'sanDaiYi' in split_cards_dic:
        for _ in split_cards_dic['sanDaiYi']:
            _san = -1
            for __ in _:
                if _.count(__) == 3:
                    _san = __
                    break
            if _san != -1:
                _san_score = _san - 10
                if _san_score > 0:
                    _san_score *= 1.5
                total_score += _san_score

    if 'sanDaiEr' in split_cards_dic:
        for _ in split_cards_dic['sanDaiEr']:
            _san = -1
            for __ in _:
                if _.count(__) == 3:
                    _san = __
                    break
            if _san != -1:
                _san_score = _san - 10
                if _san_score > 0:
                    _san_score *= 1.5
                total_score += _san_score

    if 'shunZi' in split_cards_dic:
        for _ in split_cards_dic['shunZi']:
            max_card = _[-1]
            shun_zi_score = (max_card - 10) / 2
            total_score += shun_zi_score

    if 'lianDui' in split_cards_dic:
        for _ in split_cards_dic['lianDui']:
            max_card = _[-1]
            lian_dui_score = (max_card - 10) / 2
            total_score += lian_dui_score

    if 'lianDui' in split_cards_dic:
        for _ in split_cards_dic['lianDui']:
            max_card = _[-1]
            lian_dui_score = (max_card - 10) / 2
            total_score += lian_dui_score

    if 'zhaDan' in split_cards_dic:
        for _ in split_cards_dic['zhaDan']:
            total_score += 9

    if 'wangZha' in split_cards_dic:
        for _ in split_cards_dic['wangZha']:
            total_score += 12

    if 'feiJi' in split_cards_dic:
        for _ in split_cards_dic['feiJi']:
            _copy = _.copy()
            f_j = []
            fei_ji_score = 0
            # 飞机分数
            for __ in _:
                if _.count(__) >= 3 and __ not in f_j:
                    f_j.append(__)

            f_j.sort()
            fei_ji_score += (f_j[-1] - 10) / 2

            # 翅膀分数
            for f in f_j:
                _copy.remove(f)
                _copy.remove(f)
                _copy.remove(f)

            checked = []
            for c in _copy:
                if c in checked:
                    continue
                if _copy.count(c) == 2:
                    c_score = c - 10
                    if c_score > 0:
                        c_score *= 1.5
                        fei_ji_score += c_score
                elif _copy.count(c) == 1:
                    c_score = c - 10
                    if c_score > 0:
                        fei_ji_score += c_score

                checked.append(c)

            total_score += fei_ji_score

    p = [6, 6, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
    # 手数
    count = 0
    for k, v in split_cards_dic.items():
        count += len(v)
    total_score -= p[count - 1] * count

    return total_score
