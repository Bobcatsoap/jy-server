import time

import KBEngine


class RoomCardChargeHistory(KBEngine.Entity):
    accountDBID = -1
    accountName = ""
    accountPhone = -1
    accountProxyType = -1
    operationDBID = -1
    operationName = ""
    operationPhone = -1
    operationProxyType = -1
    modifyTime = -1
    # 修改数量
    modifyCount = -1
    # 修改后的数量
    modifiedRoomCard = -1

    def __init__(self):
        KBEngine.Entity.__init__(self)

    # 生成一条重置记录
    def create_one_item(self, account_entity, operator_entity, modify_count, modified_room_card,
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

        self.accountName = str(account_entity.name)
        self.accountPhone = str(account_entity.phone)
        self.accountDBID = account_entity.databaseID
        self.accountProxyType = account_entity.proxyType
        self.operationDBID = operator_entity.databaseID
        self.operationName = str(operator_entity.name)
        self.operationPhone = str(operator_entity.phone)
        self.operationProxyType = operator_entity.proxyType
        self.modifyCount = int(modify_count)
        self.modifiedRoomCard = int(modified_room_card)
        self.modifyTime = int(time.time())
        self.writeToDB(callback)

    def create_one_item_with_none_operator(self, account_entity, modify_count, modified_room_card,
                                           on_success=None, on_fail=None):
        """
        总后台充值，没有操作者
        :param account_entity:
        :param modify_count:
        :param modified_room_card:
        :param on_success:
        :param on_fail:
        :return:
        """
        def callback(boolean, entity):
            if boolean:
                if on_success:
                    on_success(entity)
                # 存入成功后销毁内存中的实体
                self.destroy()
            else:
                if on_fail:
                    on_fail()

        self.accountName = account_entity.name
        self.accountPhone = account_entity.phone
        self.accountDBID = account_entity.databaseID
        self.accountProxyType = account_entity.proxyType
        self.operationDBID = -99
        self.operationName = str("superuser")
        self.operationPhone = str("superuser")
        self.operationProxyType = -99
        self.modifyCount = modify_count
        self.modifiedRoomCard = modified_room_card
        self.modifyTime = int(time.time())
        self.writeToDB(callback)
