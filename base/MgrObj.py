# -*- coding: utf-8 -*-
from KBEDebug import *
from FrameWork import Mgr


class MgrObj(KBEngine.Entity):

    mgr = None

    def __init__(self):
        KBEngine.Entity.__init__(self)

    def init(self, mgr):
        self.mgr = mgr
        _mgr_name = type(mgr).__name__
        KBEngine.globalData[_mgr_name] = self
        mgr.entity = self
        INFO_MSG("[%s id %s] MgrObj entity init " % (_mgr_name, self.id))

    def onTimer(self, id, userArg):
        self.mgr.on_timer(id, userArg)


