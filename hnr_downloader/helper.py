"""
Help functions used in app.

    now(): datetime.datetime.now()
    now_str(): formated now
    is_url(str:url): check if url qualified

    strsize(int:size): formated file size, eg. 60MB for 6*1024*1024.
    strspeed(int:speed): formated download speed, eg 10KB/s for 10*1024.
    strduration(float:duration): formated duration, eg 1分10秒 for 70.0.
    format_datetime(datetime:d): formated datetime.
    find_suitable_filename(str:filename): find a unused filename under the same folder.
"""

import os
import re
import datetime
from urllib.parse import urlparse


def now():
    return datetime.datetime.now()


def now_str():
    return now().strftime('%Y-%m-%d %H:%M:%S')


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


one_K = 1024
one_M = one_K * one_K
one_G = one_M * one_K
one_T = one_G * one_G


def strsize(size, bytes=False):
    size = size or 0
    if isinstance(size, str):
        try:
            size = int(size)
        except BaseException:
            size = 0

    if size < one_K:
        r = f'{size}'
    elif size < one_M:
        r = f'{size/one_K:0.2f}KB'
    elif size < one_G:
        r = f'{size/one_M:0.2f}MB'
    elif size < one_T:
        r = f'{size/one_G:0.2f}GB'
    else:
        r = f'{size/one_T:0.2f}TB'
    if bytes:
        r = f'{r}( {size:,})'
    return r


def strspeed(speed):
    if speed is None:
        return _('未知')
    elif speed < one_K:
        return f'{speed}B/s'
    elif speed < one_M:
        return f'{speed/one_K:0.2f}KB/s'
    else:
        return f'{speed/one_M:0.2f}MB/s'


one_Minute = 60
one_Hour = one_Minute * 60
one_Day = one_Hour * 24


def strduration(duration):
    if duration is None:
        return _('未知')
    if duration < 1:
        return _('小于1秒')
    duration = int(duration)
    if duration < one_Minute:
        return _('{}秒').format(duration)
    elif duration < one_Hour:
        m = int(duration / one_Minute)
        sec = duration % one_Minute
        return _('{minute}分{second}秒').format(minute=m, second=sec)
    elif duration < one_Day:
        h = int(duration / one_Hour)
        m = int(duration % one_Hour / one_Minute)
        sec = duration % one_Hour % one_Minute
        return _('{hour}小时{minute}分{second}秒').format(
            hour=h, minute=m, second=sec)
    else:
        d = int(duration / one_Day)
        rh = int(duration % one_Day)
        h = int(rh / one_Hour)
        m = int(rh % one_Hour / one_Minute)
        sec = rh % one_Hour % one_Minute
        return _('{day}天{hour}小时{minute}分{second}秒').format(
            day=d, hour=h, minute=m, second=sec)


def format_datetime(d):
    return d.strftime('%H:%M:%S') if d else ''


def find_suitable_filename(filename):
    if not os.path.exists(filename):
        return filename

    dir = os.path.dirname(filename)
    fn = os.path.basename(filename)
    fn, ext = os.path.splitext(fn)
    i = 1
    while True:
        filename = os.path.join(dir, f'{fn}({i:02d}){ext}')
        if not os.path.exists(filename):
            return filename
        i += 1


def sanitize(filename):
    return re.sub(r'[/\\:*"<>|?]', '', filename) if filename else None
