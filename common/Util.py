# -*- coding: utf-8 -*-
from math import radians, cos, sin, asin, sqrt, atan2


def getdistance(lng1, lat1, lng2, lat2):
    if lng1 == 0 and lat1 == 0:
        return -1

    if lng2 == 0 and lat2 == 0:
        return -1

    R = 6373.0

    lat1 = radians(float(lat1))
    lon1 = radians(float(lng1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lng2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def get_player_level(gold):
    """
    斗牛和炸金花金币场，依据玩家的金币划分玩家的等级
    :param gold:
    :return:
    """
    if 50 <= gold <= 300:
        return 1
    elif 301 <= gold <= 1000:
        return 2
    elif 1001 <= gold <= 5000:
        return 3
    elif 5001 <= gold <= 20000:
        return 4
    elif 20001 <= gold:
        return 5
    else:
        return 0
