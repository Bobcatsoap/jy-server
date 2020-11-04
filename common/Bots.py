# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
import random
import json


botsId = []
botsAccountEntityPoolMaxCount = 200
botsAccountEntitys = []


def init():
    """

    :return:
    """
    getBotsId()


def getBotsId():
    """

    :return:
    """
    _coomand = 'select id from tbl_account where sm_isBot=1;'
    KBEngine.executeRawDatabaseCommand(_coomand, onGetBotsId)


def onGetBotsId(result, rows, insertid, error):
    """

    :param result:
    :param rows:
    :param insertid:
    :param error:
    :return:
    """
    global botsId
    for i in result:
        botsId.append(int(i[0]))
    fullAccountEntityPool()


def fullAccountEntityPool():
    """

    :return:
    """
    global botsAccountEntitys
    global botsAccountEntityPoolMaxCount
    _l = len(botsAccountEntitys)
    for i in range(0, botsAccountEntityPoolMaxCount - _l):
        createBotAccountEntity()


def createBotAccountEntity():
    """
    获得一个机器人账号
    :return:
    """
    global botsId
    _l = len(botsId)
    if _l > 1:
        _i = random.randint(1, _l - 1)
        KBEngine.createEntityFromDBID("Account", botsId[_i], onGetAccountEntity)
        botsId.pop(_i)


def onGetAccountEntity(baseRef, databaseID, wasActive):
    """
    :param baseRef:
    :param databaseID:
    :param wasActive:
    :return:
    """
    global botsAccountEntitys
    if baseRef:
        if baseRef.gold <= 100:
            baseRef.gold = 100
        botsAccountEntitys.append(baseRef)


def getBotBotAccountEntity():
    """
    创建机器人实体
    :return:
    """
    global botsAccountEntitys
    _l = len(botsAccountEntitys)
    if _l > 0:
        DEBUG_MSG('botsAccountEntitys  _l :%s'%_l)
        _i = random.randint(0, _l - 1)
        _ret = botsAccountEntitys.pop(_i)
        fullAccountEntityPool()
        return _ret


def returnBotId(_id):
    botsId.append(_id)
