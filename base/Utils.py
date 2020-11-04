import math
import time


def getStrNowTime():
    timeStamp = time.time()
    localTime = time.localtime(timeStamp)
    strTime = time.strftime("%Y-%m-%d %H:%M:%S", localTime)
    return strTime


def getTodayDate():
    timeStamp = time.time()
    localTime = time.localtime(timeStamp)
    strTime = time.strftime("%Y-%m-%d", localTime)
    return strTime