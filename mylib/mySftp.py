from typing import Union
import pysftp
import stat
import logging
from threading import Lock
from datetime import datetime as dt

from mylib import Target, Url


class SftpTarget(Target):
    def __new__(cls, url, *args, **kwargs):
        instance = super().__new__(cls, url, *args, **kwargs)
        instance.path_dict = {}  # Словарь структур {Путь: (_get_list(Путь), datetime)}
        instance.mutex = Lock()
        instance.interval = 5  # Интервал N минут через которые обновляется листинг каталога
        return instance

    def __init__(self, url):  # Список аргументов: args:config.args DB:myDB.DB Log:myLog.Log
        Target.__init__(self, url)
        if not isinstance(url, Url):
            url = Url(url)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        self.sftp = pysftp.Connection(host=url.host, username=url.user, password=url.passw)
        # self.sftp._cnopts.compression = self.args.compression

    def get_file_size(self, url):
        if not isinstance(url, Url):
            url = Url(url)
        if url.path not in self.path_dict:
            self._list(url.path)
        if url.file in self.path_dict[url.path]:
            return self.path_dict[url.path][url.file].st_size
        return False

    def is_dir(self, url: Union[Url, str]):
        if isinstance(url, str) and url.endswith('/'):
            return True
        if not isinstance(url, Url):
            url = Url(url)
        if not url.file:
            self.log.debug(f"is_dir {url} return False")
            return False
        self.sftp.cwd(url.path)
        return self.path_dict[url.path][0][url.file].st_mode & stat.S_IFDIR

    def _list(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        self.log.debug(f"_get_list {url.url}")

        self.mutex.acquire()
        self.sftp.cwd(url.path)
        current_time = dt.now()
        if url.path in self.path_dict:
            previous_time = self.path_dict[url.path][1]  # Получаем время предыдущего запроса
            time_diff = (current_time - previous_time).total_seconds() / 60
        else:
            time_diff = 100

        if time_diff > self.interval:
            file_list = self.sftp.listdir_attr()
            file_dict = {item.filename: item for item in file_list}  # Получаем словарь файлов с аттрибутами
            self.path_dict[url.path] = (file_dict, dt.now())
        self.mutex.release()

        file_dict = self.path_dict[url.path][0]
        out_list = [item for item in file_dict.keys()]  # Создаем список файлов
        if not out_list:
            return out_list
        out_list = map(lambda name: url.full_path + name, out_list)
        out_list = list(filter(self.is_correspond, out_list))  # Фильтруем по маске

        return [x + '/' if self.is_dir(x) else x for x in out_list]

    def _get_file(self, remote_file: Union[Url, str], temp_file: str):
        if not isinstance(remote_file, Url):
            remote_file = Url(remote_file)
        self.sftp.cwd(remote_file.path)
        self.log.debug(f"SFTP GET {remote_file} {temp_file}")
        self.sftp.get(remote_file.path + remote_file.file, temp_file)
        return True

    def put_file(self, url):
        ...

    def remove(self, url):
        if not isinstance(url, Url):
            url = Url(url)
        self.sftp.cwd(url.path)
        self.sftp.remove(url.file)
