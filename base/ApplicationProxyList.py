import time

import KBEngine

from HTTPServer import HttpRequest


class ApplicationProxyList(KBEngine.Entity):
    accountDBID = -1
    contactWay = ""
    applicationTime = 0

    def __init__(self):
        KBEngine.Entity.__init__(self)

    def create_one_item(self, account_db_id, contact_way,
                        on_success=None, on_fail=None):

        def callback(boolean, entity):
            if boolean:
                if on_success:
                    on_success(entity)
                #
                HttpRequest.send_message(15617751193, str(contact_way), account_db_id)
                # 存入成功后销毁内存中的实体
                self.destroy()
            else:
                if on_fail:
                    on_fail()

        self.accountDBID = account_db_id
        self.contactWay = contact_way
        self.applicationTime = int(time.time())
        self.writeToDB(callback)
