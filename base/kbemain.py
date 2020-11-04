# -*- coding: utf-8 -*-
import json
import os
import KBEngine

import Const
from KBEDebug import *
import Bots
import DBCommand
import KbeHTTPServer
from FrameWork import Mgr

# TODO Baseapp进程主要负责与客户端通讯、与空间或位置无关类游戏逻辑(公会管理器、聊天系统、游戏大厅、排行榜等等)、存档与备份等等。

def onBaseAppReady(isBootstrap):
    """
    KBEngine method.
    baseapp已经准备好了
    @param isBootstrap: 是否为第一个启动的baseapp
    @type isBootstrap: BOOL
    """
    INFO_MSG('onBaseAppReady: isBootstrap=%s, appID=%s, bootstrapGroupIndex=%s, bootstrapGlobalIndex=%s' % \
             (isBootstrap, os.getenv("KBE_COMPONENTID"), os.getenv("KBE_BOOTIDX_GROUP"),
              os.getenv("KBE_BOOTIDX_GLOBAL")))

    # TODO BaseApp入口启动
    # 启动业务逻辑层
    if isBootstrap:
        KbeHTTPServer.start()
        DBCommand.resetAccountCreateRooms()
        DBCommand.resetAccountCreateSubstituteRooms()

        # TODO createEntityLocally 在本地BaseApp上创建一个新的Entity实体。 （entityType, params）
        # TODO entityType string 指定要创建的Entity实体的类型。有效的实体类型在/scripts/entities.xml列出
        # TODO params dict 一个Python字典对象，用于初始化实体属性。
        # 分别创建了 AccountMgr RoomManager...等对象
        KBEngine.createEntityLocally("MgrObj", {}).init(Mgr.create_mgr('AccountMgr')[0])
        KBEngine.createEntityLocally("MgrObj", {}).init(Mgr.create_mgr('RoomManager')[0])
        KBEngine.createEntityLocally("MgrObj", {}).init(Mgr.create_mgr('TeaHouseManager')[0])
        KBEngine.createEntityLocally('MgrObj', {}).init(Mgr.create_mgr('GoldSessionManager')[0])
        KBEngine.createEntityLocally('MgrObj', {}).init(Mgr.create_mgr('ChallengeAreaManager')[0])

        # 加载游戏配置
        load_game_config()

        KBEngine.globalData["AccountMgr"].mgr.addTimer()
        KBEngine.globalData["TeaHouseManager"].mgr.addTimer()
        KBEngine.globalData["GoldSessionManager"].mgr.start_reload_config_timer()
        KBEngine.globalData["ChallengeAreaManager"].mgr.start_reload_config_timer()
        KBEngine.globalData["AccountMgr"].mgr.addOnlineStatTimer()
        KBEngine.globalData["RoomManager"].mgr.addTimer()
        Bots.init()


def onReadyForLogin(isBootstrap):
    """
    KBEngine method.
    如果返回值大于等于1.0则初始化全部完成, 否则返回准备的进度值0.0~1.0。
    在此可以确保脚本层全部初始化完成之后才开放登录。
    @param isBootstrap: 是否为第一个启动的baseapp
    @type isBootstrap: BOOL
    """
    return 1.0


def onReadyForShutDown():
    """
    KBEngine method.
    进程询问脚本层：我要shutdown了，脚本是否准备好了？
    如果返回True，则进程会进入shutdown的流程，其它值会使得进程在过一段时间后再次询问。
    用户可以在收到消息时进行脚本层的数据清理工作，以让脚本层的工作成果不会因为shutdown而丢失。
    """
    INFO_MSG('onReadyForShutDown()')
    return True


def onBaseAppShutDown(state):
    """
    KBEngine method.
    这个baseapp被关闭前的回调函数
    @param state: 0 : 在断开所有客户端之前
                  1 : 在将所有entity写入数据库之前
                  2 : 所有entity被写入数据库之后
    @type state: int
    """
    INFO_MSG('onBaseAppShutDown: state=%i' % state)


def onInit(isReload):
    """
    KBEngine method.
    当引擎启动后初始化完所有的脚本后这个接口被调用
    @param isReload: 是否是被重写加载脚本后触发的
    @type isReload: bool
    """
    INFO_MSG('onInit::isReload:%s' % isReload)


def onFini():
    """
    KBEngine method.
    引擎正式关闭
    """
    INFO_MSG('onFini()')


def onCellAppDeath(addr):
    """
    KBEngine method.
    某个cellapp死亡
    """
    WARNING_MSG('onCellAppDeath: %s' % (str(addr)))


def onGlobalData(key, value):
    """
    KBEngine method.
    globalData有改变
    """
    DEBUG_MSG('onGlobalData: %s' % key)


def onGlobalDataDel(key):
    """
    KBEngine method.
    globalData有删除
    """
    DEBUG_MSG('onDelGlobalData: %s' % key)


def onBaseAppData(key, value):
    """
    KBEngine method.
    baseAppData有改变
    """
    DEBUG_MSG('onBaseAppData: %s' % key)


def onBaseAppDataDel(key):
    """
    KBEngine method.
    baseAppData有删除
    """
    DEBUG_MSG('onBaseAppDataDel: %s' % key)


def onLoseChargeCB(ordersID, dbid, success, datas):
    """
    KBEngine method.
    有一个不明订单被处理， 可能是超时导致记录被billing
    清除， 而又收到第三方充值的处理回调
    """
    DEBUG_MSG('onLoseChargeCB: ordersID=%s, dbid=%i, success=%i, datas=%s' % \
              (ordersID, dbid, success, datas))


def load_game_config():
    """
    读取json配置
    :return: 
    """
    path = os.path.dirname(__file__) + '/GameConfig'
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
                # TODO 加载配置到 Const下的 GameConfigJson类的 config_json属性中 游戏配置 会发送到前端
                Const.GameConfigJson.config_json[file_name] = json_data
                file_data.close()
    DEBUG_MSG("[onBaseAppReady] load_game_config over.config")

    path = os.path.dirname(__file__) + '/ServerGameConfig'
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
                # TODO 加载配置到 Const下的 ServerGameConfigJson类的 config_json属性中 服务端游戏配置
                Const.ServerGameConfigJson.config_json[file_name] = json_data
                file_data.close()
    DEBUG_MSG("[onBaseAppReady] load_server_game_config over.config")


def save_game_config(file_name):
    if file_name in Const.ServerGameConfigJson.config_json:
        path = os.path.dirname(__file__) + '/ServerGameConfig'
        with open(path + '/' + file_name + '.json', 'w', encoding='utf-8') as _file:
            json.dump(Const.ServerGameConfigJson.config_json[file_name], _file, indent=2, sort_keys=True)



