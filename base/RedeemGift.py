import time
import KBEngine


class RedeemGift(KBEngine.Entity):
    accountDBID = 0
    time = 0
    giftID = 0

    def __init__(self):
        KBEngine.Entity.__init__(self)

    def create_one_item(self, accountDBID, giftID):
        self.accountDBID = accountDBID
        self.giftID = giftID
        self.time = int(time.time())
        self.writeToDB()
