#!/usr/bin/python3
from abc import abstractmethod
from typing import Union
import re
import os
from shutil import move

from mylib import Url, parse_mask, time_it


class Target:
    log = None
    args = None
    destination = None
    start_path = '/'

    def __new__(cls, url, *args, **kwargs):
        instance = super().__new__(cls)
        if not isinstance(url, Url):
            url = Url(url)

        instance.full_mask = parse_mask(url.mask)
        instance.start_url = url
        instance.start_path = url.path
        return instance

    def __init__(self, url, **param):
        ...

    def list(self, url: Union[Url, str]):  # Метод возвращает список если цель - каталог, иначе размер файла
        """
        Метод возвращает список файлов
        Каталог обязательно заканчивается '/'
        """
        if not isinstance(url, Url):
            url = Url(url)

        self.log.debug(f"LIST {url}")

        rez = self._list(url)
        self.log.info(f"Считали список файлов каталога {url.path} - {len(rez)} файлов.")
        return rez

    @abstractmethod
    def _list(self, url: Union[Url, str]):
        ...

    @abstractmethod
    def get_file_size(self, url: Union[Url, str]):
        ...

    def get_file(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        msg = ""
        relative_path = url.path[len(self.start_path):]
        remote_file = url.path + url.file
        local_path = self.destination.start_path

        if self.args.no_create_dir:
            current_path = local_path
        else:
            current_path = local_path + relative_path

        host_file = str(os.path.join(current_path, url.file))
        temp_file = str(os.path.join(self.args.tempdir, url.file))
        # sw_get - скачиваем файл
        # sw_del - удаляем скачаный файл
        # sw_db  - записываем в базу данных
        sw_get = self.args.mode in ['COPY', 'XCPY', 'MOVE', 'XMOV']  # Скачиваем файл
        sw_del = self.args.mode in ['DELE', 'MOVE', 'XMOV']  # Удалять скачаный файл
        sw_force = self.args.mode in ['XCPY', 'XMOV']  # игнорировать наличие уже скачаного файла локально
        sw_db = self.args.mode == 'MKDB' or self.args.database == 'DB'  # Работа с БД
        successful = True

        # Начало
        file_size = self.get_file_size(url)
        if file_size == 0:
            self.log.info(f'{url.file} size is 0, skipping')
            sw_get = False
            sw_del = True
            # return

        if not os.path.exists(current_path) and sw_get:
            os.makedirs(current_path)
        # ==============================================================
        if sw_db:
            # db_size = self.args.DB.get_file_sz(remote_file.replace(' ', '%20'))
            db_size = self.args.DB.get_file_sz(url.file.replace(' ', '%20'))
        else:
            db_size = file_size

        if sw_get:
            if sw_db and db_size == file_size and not sw_force:  # Если файл уже имеется в базе
                msg = f"Файл {url.file} размером {file_size} уже имеется в базе"
            elif (os.path.exists(host_file) and  # Если файл уже существует
                  os.path.getsize(host_file) and
                  not sw_force):  # И не указана насильно перезаписывать
                msg = f"Файл {url.file} размером {file_size} уже имеется локально"
            else:
                successful = self._get_file(url, temp_file)
                if successful:
                    move(temp_file, host_file)
                else:
                    os.remove(temp_file)
                if successful and not sw_del:
                    msg = (f"Копируем файл {url.file} -> {current_path} "
                           f"размером {file_size} в режиме {self.args.mode}")
                elif successful and sw_del:
                    msg = (f"Переносим файл {url.file} -> {current_path} "
                           f"размером {file_size} в режиме {self.args.mode}")
                    msg += f" удаляем исходный файл."
                    self.remove(remote_file)

        if successful and sw_del and not sw_get:
            msg += f"Удаляем файл {url}"
            self.remove(remote_file)

        if sw_db and successful:
            if not sw_get:
                msg = f"Записываем в базу файл {url.file}"
            # self.args.DB.store_file(remote_file.replace(' ', '%20'), file_size)
            self.args.DB.store_file(url.file.replace(' ', '%20'), file_size)

        self.log.info(msg)

    @abstractmethod
    def remove(self, url: Union[Url, str]):
        ...

    @abstractmethod
    def _get_file(self, source_file, temp_file):
        ...

    def is_correspond(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        full_url = url.path + url.file
        url_len = len(full_url.split('/'))
        if url.file:
            url_len += 1
        mask_len = len((self.start_url.path + self.start_url.mask).split('/')) + 1
        parsed_mask = parse_mask(self.start_url.path + self.start_url.mask)
        parsed_mask = '/'.join(parsed_mask.split('/')[:url_len - 1])
        if full_url.endswith('/') and url_len < mask_len:
            parsed_mask += '/'
        answ = re.fullmatch(parsed_mask, full_url)
        self.log.debug(f"{parsed_mask=} {full_url=} answ={bool(answ)}")
        return bool(answ)

    @abstractmethod
    def reconnect(self):
        self.log.error("Reconnect")

    def is_dir(self, file_name):
        ...

    @staticmethod
    def is_mask(mask):
        if "*" in mask or "(" in mask or "[" in mask or "%" in mask:
            return True
        return False
