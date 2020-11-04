import time

import KBEngine

from KBEDebug import DEBUG_MSG


class GameCoinChargeHistory(KBEngine.Entity):
    teaHouseId = -1
    accountDBID = -1
    accountName = ""
    accountPhone = -1
    operationAccountDBID = -1
    operationName = ""
    operationPhone = -1
    operationProxyType = -1
    modifyTime = -1
    # 修改数量
    modifyCount = -1
    # 修改后的数量
    modifiedGameCoin = -1

    def __init__(self):
        KBEngine.Entity.__init__(self)

    def create_one_item(self, tea_house_id, account_db_id, account_name, account_phone, operation_account_db_id,
                        operation_name, operation_phone, operation_proxy_type, modify_count, modified_game_coin,
                        on_success=None, on_fail=None):

        def callback(boolean, entity):
            if boolean:
                if on_success:
                    on_success(entity)
                # 存入成功后销毁内存中的实体
                self.destroy()
            else:
                if on_fail:
                    on_fail()

        self.teaHouseId = int(tea_house_id)
        self.accountName = account_name
        self.accountPhone = account_phone
        self.accountDBID = int(account_db_id)
        self.operationAccountDBID = int(operation_account_db_id)
        self.operationName = operation_name
        self.operationPhone = operation_phone
        self.operationProxyType = int(operation_proxy_type)
        self.modifyCount = int(modify_count)
        DEBUG_MSG("modify count : %s" % modify_count)
        self.modifiedGameCoin = int(modified_game_coin)
        self.modifyTime = int(time.time())
        self.writeToDB(callback)
