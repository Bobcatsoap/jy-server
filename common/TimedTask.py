# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
import random
import json
import datetime


class TimedTask(KBEngine.Entity):
    def __int__(self):
        KBEngine.Entity.__init__(self)
        self.times = []
        self.addTimer(1, 1, 0)

    def addTask(self):
        """
        :return:
        """

    def removeTask(self):
        """

        :return:
        """

    def onTimer(self, timerId, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param timerId		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """
