# -*- coding: utf-8 -*-
import KBEngine
import time
from TeaHouse import TeaHousePlayerLevel


def tea_house_manager():
    return KBEngine.globalData["TeaHouseManager"].mgr


class TeaHousePerformance(KBEngine.Entity):
    proportion = 0
    performanceDetail = 0
    count = 0
    time = 0
    superior = 0
    accountDBID = 0

    def __init__(self):
        KBEngine.Entity.__init__(self)

    def create_one_item(self, account_db_id, superior, time, count, performance_count, proportion, teaHouseId):
        self.accountDBID = account_db_id
        self.superior = str(superior)
        self.time = time
        self.count = int(count)
        self.performanceDetail = str(performance_count)
        self.proportion = proportion
        tea_house_entity = tea_house_manager().get_tea_house_with_id(teaHouseId)
        tea_house_entity.update_team_rank_winner(account_db_id, performance_count)
        self.writeToDB()
