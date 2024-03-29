# -*- coding: utf-8 -*-
import KBEngine
import time
from TeaHouse import TeaHousePlayerLevel


def tea_house_manager():
    return KBEngine.globalData["TeaHouseManager"].mgr


class TeaHousePerformance(KBEngine.Entity):
    # 抽水比例
    proportion = 0
    # 抽成的数量 保留两位小数
    performanceDetail = 0
    # 抽成的数量
    count = 0
    # 时间
    time = 0
    # 上级
    superior = 0
    # 用户id
    accountDBID = 0
    # 0收入，1支出，2裁判
    createType = 0
    # 原数量
    currentCount = 0
    # 提现后数量
    fundedCount = 0
    # 操作
    operateName = ''
    # 茶楼id
    teaHouseId = 0
    roomType = None

    def __init__(self):
        KBEngine.Entity.__init__(self)

    def create_one_item(self, account_db_id, superior, time, count, performance_count, proportion, teaHouseId,
                        roomType=None):
        self.accountDBID = account_db_id
        self.superior = str(superior)
        self.time = time
        self.count = int(count)
        self.performanceDetail = str(round(performance_count, 2))
        if roomType:
            self.roomType = roomType
        else:
            self.roomType = ''
        self.proportion = proportion
        self.createType = 0
        self.teaHouseId = teaHouseId
        tea_house_entity = tea_house_manager().get_tea_house_with_id(teaHouseId)
        # tea_house_entity.update_team_rank_winner(account_db_id, performance_count)
        self.writeToDB()

    def create_one_fund_item(self, account_db_id, count, current_count, operate_name, tea_house_id, callback):
        """
        提现记录
        :param account_db_id:
        :param count: 提现数量
        :param current_count: 当前携带
        :param operate_name:
        :param tea_house_id:
        :param callback:
        :return:
        """
        self.superior = str(account_db_id)
        self.time = int(time.time())
        self.performanceDetail = str(round(count, 2))
        self.currentCount = round(current_count, 2)
        self.fundedCount = round(current_count, 2) + round(count, 2)
        self.operateName = operate_name
        self.createType = 1
        self.teaHouseId = tea_house_id
        self.writeToDB(callback)

    def create_one_modify_item(self, account_db_id, count, current_count, operate_name, tea_house_id, callback):
        self.superior = str(account_db_id)
        self.time = int(time.time())
        # 裁判修改数额暂时用这个字段
        self.performanceDetail = str(round(count, 2))
        self.currentCount = round(current_count, 2)
        # 裁判后的数额暂时用这个字段
        self.fundedCount = round(current_count, 2) + round(count, 2)
        self.operateName = operate_name
        self.createType = 2
        self.teaHouseId = tea_house_id
        self.writeToDB(callback)
