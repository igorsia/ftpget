import os
import re
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse
from shutil import disk_usage


class Url:
    def __init__(self, url: str):
        """
        :param url:
        """

        """
        ftp://andy:andy00@192.168.10.39/home/andy/igor/*
        url_type://user:password@host:port/path/to/files/mask
        url_type
        user
        password
        host
        port
        path
        mask
        """

        if isinstance(url, Url):
            self._type_url = url.type_url
            self._user = url.user
            self._passw = url.passw
            self._host = url.host
            self._port = url.port
            self._path = url.path
            self._mask = url.mask
            return
        if url.endswith('/') or url.endswith(os.sep):
            url += '*'
        parsed_url = urlparse(url)
        if '://' not in url:  # Это у нас обычный файловый путь вместо урла
            type_url = "file"
        else:
            type_url = parsed_url.scheme

        if type_url == "file":
            host = ''
            user = ''
            passw = ''
            port = ''
            i = 0
            path = parsed_url.netloc + parsed_url.path
            for i, item in enumerate(path.split('/')):
                if is_mask(item):
                    break
            splitted_path = path.split(os.sep)
            path = os.sep.join(splitted_path[:i]) + os.sep
            mask = os.sep.join(splitted_path[i:])
        else:
            host = parsed_url.hostname
            user = parsed_url.username
            passw = parsed_url.password
            port = parsed_url.port
            # /dir/to/files*/with/mask*
            # path = /dir/to/
            # mask = files*/with/mask*
            i = 0
            for i, item in enumerate(parsed_url.path.split('/')):
                if is_mask(item):
                    break
            splitted_path = parsed_url.path.split('/')
            path = '/'.join(splitted_path[:i]) + '/'
            mask = '/'.join(splitted_path[i:])

            if user is None:  # если логина и пароля нет то анонимный вход
                user = "anonymous"
                passw = "mail@local.net"
            if passw is None:
                passw = ''

        if mask == "":
            mask = "*"

        self._type_url = type_url
        self._user = user
        self._passw = passw
        self._host = host
        self._port = port
        self._path = path
        self._mask = mask

    def __getitem__(self, key):
        return (self.type_url, self._user, self._passw, self._host, self._path, self._mask)[key]

    @property
    def type_url(self):
        return self._type_url

    @property
    def user(self):
        return self._user

    @property
    def passw(self):
        return self._passw

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def path(self):
        return self._path

    @property
    def mask(self):
        return self._mask

    @property
    def file(self):
        return '' if is_mask(self._mask) else self._mask

    @property
    def url(self):
        return f"{self._type_url}://{self.host}{self.path}{self.mask}"

    @property
    def full_url(self):
        if self._type_url == 'file':
            return self.url
        return f"{self._type_url}://{self.user}:{self.passw}@{self.host}{self.path}{self.mask}"

    @property
    def full_path(self):
        return f"{self._type_url}://{self.host}{self.path}"

    @property
    def str(self):
        return self.full_url

    def __len__(self):
        return 6

    def __call__(self, url):
        return self._type_url, self.user, self.passw, self.host, self.path, self.mask

    def __str__(self):
        return self.full_url

    def __repr__(self):
        return (f"Object Url: {self._type_url=}://{self.user=}:{self.passw=}@"
                f"{self.host=}:{self._port=}{self.path=}{self.mask=}")


def parse_mask(line):
    # В маске может быть что то одно из %D %M %Y %F
    # Если в маске присутствует %D значит маска соответствует текущему и предыдущему дню
    # Если в маске присутствует %M значит маска соответствует текущему и предыдущему месяцу
    # Если в маске присутствует %Y или %F значит маска соответствует текущему и предыдущему году
    now = dt.now()
    # print(line)
    f = now.strftime('%Y')
    y = now.strftime('%y')
    m = now.strftime('%m')
    d = now.strftime('%d')

    if '%F' in line:
        if '%M' in line or '%D' in line or '%F' in line:
            print("Неправильная комбинация в маске")
            quit(1)
        one_year_ago = now - relativedelta(years=1)
        F = one_year_ago.strftime('%Y')
        tmp_line = re.sub('%F', f"{F}", line)
        line = re.sub('%f', f"{f}", line)
        line = f"({tmp_line}|{line})"
    elif '%Y' in line:
        if '%M' in line or '%D' in line:
            print("Неправильная комбинация в маске")
            quit(1)
        one_year_ago = now - relativedelta(years=1)
        F = one_year_ago.strftime('%Y')
        Y = one_year_ago.strftime('%y')
        tmp_line = re.sub('%Y', f"{Y}", line)
        line = re.sub('%y', f"{y}", line)
        line = f"({tmp_line}|{line})"
    elif '%M' in line:
        if '%D' in line:
            print("Неправильная комбинация в маске")
            quit(1)
        one_month_ago = now - relativedelta(months=1)
        Y = one_month_ago.strftime('%y')
        F = one_month_ago.strftime('%Y')
        M = one_month_ago.strftime('%m')
        tmp_line = re.sub('%y', f"{Y}", line)
        tmp_line = re.sub('%f', f"{F}", tmp_line)
        tmp_line = re.sub('%M', f"{M}", tmp_line)
        line = re.sub('%M', f"{m}", line)
        line = re.sub('%y', f"{y}", line)
        line = re.sub('%f', f"{f}", line)
        line = f"({tmp_line}|{line})"
    elif '%D' in line:
        one_day_ago = now - relativedelta(days=1)
        two_day_ago = now - relativedelta(days=2)
        Y = one_day_ago.strftime('%y')
        F = one_day_ago.strftime('%Y')
        M = one_day_ago.strftime('%m')
        D = one_day_ago.strftime('%d')
        tmp_line = re.sub('%D', f"({D})", line)
        tmp_line = re.sub('%y', f"({Y})", tmp_line)
        tmp_line = re.sub('%f', f"({F})", tmp_line)
        tmp_line = re.sub('%m', f"({M})", tmp_line)

        Y = two_day_ago.strftime('%y')
        F = two_day_ago.strftime('%Y')
        M = two_day_ago.strftime('%m')
        D = two_day_ago.strftime('%d')
        tmp2_line = re.sub('%D', f"({D})", line)
        tmp2_line = re.sub('%y', f"({Y})", tmp2_line)
        tmp2_line = re.sub('%f', f"({F})", tmp2_line)
        tmp2_line = re.sub('%m', f"({M})", tmp2_line)

        line = re.sub('%D', f"({d})", line)
        line = re.sub('%y', f"({y})", line)
        line = re.sub('%f', f"({f})", line)
        line = re.sub('%m', f"({m})", line)
        line = f"({tmp2_line}|{tmp_line}|{line})"
    else:
        line = re.sub('%m', m, line)
        line = re.sub('%y', y, line)
        line = re.sub('%f', f, line)
        line = re.sub('%d', d, line)
    # print(line)
    line = line.replace('.', '\\.')
    line = line.replace('?', '.')
    line = line.replace('*', '.*')
    return line


def get_free_space(folder):
    """ Возвращает свободное место на диске в процентах
    """
    stat = disk_usage(folder)
    return stat[2] / stat[0] * 100


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


def is_mask(mask):
    if "*" in mask or "(" in mask or "[" in mask or "%" in mask:
        return True
    return False


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
