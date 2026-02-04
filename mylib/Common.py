import os
import re
from urllib.parse import urlparse
from shutil import disk_usage
from datetime import datetime as dt


def full_stack():
    import traceback
    import sys
    exc = sys.exc_info()[0]
    if exc is not None:
        f = sys.exc_info()[-1].tb_frame.f_back
        stack = traceback.extract_stack(f)
    else:
        stack = traceback.extract_stack()[:-1]
    trc = 'Traceback (most recent call last):\n'
    stacktr = trc + ''.join(traceback.format_list(stack))
    if exc is not None:
        stacktr += '  ' + traceback.format_exc().lstrip(trc)
    return stacktr



def time_it(fun):
    def do(*args, **kwargs):
        start = dt.now()
        rez = fun(*args, **kwargs)
        duration = (dt.now() - start).total_seconds()
        hours = duration // 3600
        duration = duration - hours * 3600
        minutes = duration // 60
        seconds = duration - minutes * 60
        minutes_str = f" {minutes:0.0f} мин." if minutes else ''
        hours_str = f"{hours:0.0f} часов" if hours else ''
        seconds_str = f" {seconds:0.2f} сек." if seconds else ''
        print(f"Функция {fun.__name__}{args[1:]}{kwargs} выполнялась {
              hours_str}{minutes_str}{seconds_str}")
        print("Результат")
        print(f"{rez}")
        return rez
    return do
