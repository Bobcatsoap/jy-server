# -*- coding: utf-8 -*-
from KBEDebug import *


class Manger:
    entity = None

    def __init__(self):
        INFO_MSG("[%s] init " % type(self).__name__)

    def add_timer(self, initial, repeat=0, arg=0):
        return self.entity.addTimer(initial, repeat, arg)

    def delete_timer(self, _id):
        self.entity.delTimer(_id)

    def on_timer(self, _id, arg):
        self.entity.onTimer(_id, arg)

