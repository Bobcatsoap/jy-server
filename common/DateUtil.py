import time
import datetime


def get_str_now_time_ymdhms():
    timeStamp = time.time()
    localTime = time.localtime(timeStamp)
    strTime = time.strftime("%Y-%m-%d %H:%M:%S", localTime)
    return strTime


def get_str_now_time_ymd():
    timeStamp = time.time()
    localTime = time.localtime(timeStamp)
    strTime = time.strftime("%Y-%m-%d", localTime)
    return strTime


def get_str_yesterday_time_ymd():
    now_time = datetime.datetime.now()
    yes_time = now_time + datetime.timedelta(days=-1)
    yes_time_nyr = yes_time.strftime('%Y-%m-%d')
    return yes_time_nyr


def get_str_now_timestamp_ymdhms():
    time = get_str_now_time_ymdhms()
    ctime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S').timestamp()
    return int(ctime)


def get_str_now_timestamp_ymd(_time=None):
    if _time is None:
        _time_ = time.strftime("%Y-%m-%d", time.localtime(_time))
    else:
        _time_ = get_str_now_time_ymd()
    ctime = datetime.datetime.strptime(_time_, '%Y-%m-%d').timestamp()
    return int(ctime)


def get_str_yesterday_timestamp_ymd(_time=None):
    if _time is None:
        _time_ = time.strftime("%Y-%m-%d", time.localtime(_time))
    else:
        _time_ = get_str_yesterday_time_ymd()
    ctime = datetime.datetime.strptime(_time_, '%Y-%m-%d').timestamp()
    return int(ctime)

