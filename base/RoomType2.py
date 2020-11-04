# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
from RoomBase import *


class RoomType2(RoomBase):
    """
    """

    def __init__(self):
        RoomBase.__init__(self)
        self.info["maxNum"] = 30
        self.info["maxPlayersCount"] = 100
