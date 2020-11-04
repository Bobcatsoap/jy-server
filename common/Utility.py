# -*- coding: utf-8 -*-
import sys

#   ===========================================
#                   等级计算规则
#   ===========================================

expBase = 100
expGrowMultiple = 1.2
lvExpConfig = []
for i in range(0, 40):
    if i == 0:
        expBase = 100
    else:
        expBase = int(lvExpConfig[i - 1] * expGrowMultiple)
    lvExpConfig.append(expBase)
vipLvExpConfig = [100, 3000, 5000, 7000, 10000, 200000, 300000, 50000]


def retLv(_total_exp):
    """

    :param _total_exp:
    :return:
    """
    return retLvInfo(_total_exp, lvExpConfig)


def retVipLv(_total_exp):
    """

    :param _total_exp:
    :return:
    """
    return retLvInfo(_total_exp, vipLvExpConfig)


def retLvInfo(_total_exp, _lv_exp_config):
    """
    
    :param _total_exp:
    :param _lv_exp_config:
    :return:
    """
    _lv = 0
    _lv_max = len(_lv_exp_config) - 1
    while True:
        _total_exp -= _lv_exp_config[_lv]
        if _total_exp < 0:
            _c_lv = _lv
            _c_lv_max = _lv_exp_config[_c_lv]
            _c_exp = _total_exp + _lv_exp_config[_c_lv]
            return _c_lv, _c_exp, _c_lv_max
        else:
            _lv += 1
            if _lv > _lv_max:
                _c_lv = _lv - 1
                return _c_lv, _lv_exp_config[_c_lv], _lv_exp_config[_c_lv]


# print(retLv(54845))
# print(retVipLv(54845))

accountCount = 0


def getTouristAccount():
    """

    :return:
    """
