# -*- coding: utf-8 -*-
import json
import os

import KBEngine

import Const
from KBEDebug import *


def onInit(isReload):
    """
    KBEngine method.
    当引擎启动后初始化完所有的脚本后这个接口被调用
    """
    DEBUG_MSG('onInit::isReload:%s' % isReload)
    # 加载游戏配置
    load_game_config()


def onGlobalData(key, value):
    """
    KBEngine method.
    globalData改变
    """
    DEBUG_MSG('onGlobalData: %s' % key)


def onGlobalDataDel(key):
    """
    KBEngine method.
    globalData删除
    """
    DEBUG_MSG('onDelGlobalData: %s' % key)


def onCellAppData(key, value):
    """
    KBEngine method.
    cellAppData改变
    """
    DEBUG_MSG('onCellAppData: %s' % key)


def onCellAppDataDel(key):
    """
    KBEngine method.
    cellAppData删除
    """
    DEBUG_MSG('onCellAppDataDel: %s' % key)


def onSpaceData(spaceID, key, value):
    """
    KBEngine method.
    spaceData改变
    """
    pass


def onAllSpaceGeometryLoaded(spaceID, isBootstrap, mapping):
    """
    KBEngine method.
    space 某部分或所有chunk等数据加载完毕
    具体哪部分需要由cell负责的范围决定
    """
    pass


def load_game_config():
    path = os.path.dirname(__file__)
    path = path[:-4]
    path += 'base/GameConfig'
    DEBUG_MSG('path:%s' % path)
    files = os.listdir(path)
    for file_full_name in files:
        # is file
        if not os.path.isdir(file_full_name):
            # is json file
            if os.path.splitext(file_full_name)[-1] == ".json":
                # get file name
                file_name = os.path.splitext(file_full_name)[0]
                file_data = open(path + '/' + file_full_name, 'r')
                json_data = json.load(file_data)
                Const.GameConfigJson.config_json[file_name] = json_data
                file_data.close()
    DEBUG_MSG("[onBaseAppReady] load_game_config over.config:%s" % Const.GameConfigJson.config_json)

    path = os.path.dirname(__file__)
    path = path[:-4]
    path += 'base/ServerGameConfig'
    DEBUG_MSG('path:%s' % path)
    files = os.listdir(path)
    for file_full_name in files:
        # is file
        if not os.path.isdir(file_full_name):
            # is json file
            if os.path.splitext(file_full_name)[-1] == ".json":
                # get file name
                file_name = os.path.splitext(file_full_name)[0]
                file_data = open(path + '/' + file_full_name, 'r', encoding='utf-8')
                json_data = json.load(file_data)
                Const.ServerGameConfigJson.config_json[file_name] = json_data
                file_data.close()
    DEBUG_MSG("[onBaseAppReady] load_server_game_config over.config")
