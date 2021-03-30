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


def bytes_to_str(input_bytes: bytes):
    """
    字节解码为字符串
    """
    return bytes.decode(input_bytes)


def bytes_to_int(input_bytes: bytes):
    """
    字节解码为整形
    """
    return int(bytes.decode(input_bytes))
