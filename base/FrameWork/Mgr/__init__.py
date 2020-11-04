from .Manger import *
from .AccountMgr import AccountMgr
# from FrameWork.Mgr.RoomManager import *

from .RoomManager import *
from .TeaHouseManager import *
from .GoldSessionManager import *
from .ChallengeAreaManager import *


# def create_mgr(*args):
#     ret = {}
#     for item in args:
#         if item == "AccountMgr":
#             ret[item] = AccountMgr()
#         elif item == "RoomMgr":
#             ret[item] = RoomMgr()
#         elif item == "GuildMgr":
#             ret[item] = GuildMgr()
#     return ret


def create_mgr(*args):
    ret = []
    for item in args:
        if item == "AccountMgr":
            ret.append(AccountMgr())
        elif item == "RoomManager":
            ret.append(RoomManager())
        elif item == "TeaHouseManager":
            ret.append(TeaHouseManager())
        elif item == 'GoldSessionManager':
            ret.append(GoldSessionManager())
        elif item == 'ChallengeAreaManager':
            ret.append(ChallengeAreaManager())
    return ret
