#!/usr/bin/python3
from typing import Union
from ftplib import FTP
import ftplib
import socket
import re

from mylib import Target, Url, full_stack


class FtpTarget(Target):

    def __new__(cls, url, *args, **kwargs):
        instance = super().__new__(cls, url, *args, **kwargs)
        instance.log.debug(f"INIT {url}")
        if not isinstance(url, Url):
            url = Url(url)
        instance.start_url = url
        instance.start_path = url.path

        instance.server_type = instance.chk_server(url)
        cls.log.debug(f"{instance.server_type=}")

        return instance

    def __init__(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        super().__init__(url)
        self.log.debug("create FtpTarget " + url.path + url.mask)
        self.ftp = self._ftp_connect(url)
        self.ftp.cwd(self.start_path)
        if self.server_type == 'linux':
            self._list = self._linux_list
        elif self.server_type == 'win32':
            self._list = self._win32_list
        elif self.server_type == 'mlst':
            self._list = self._mlst_list

    @classmethod
    def chk_server(cls, url: Union[Url, str]):
        """
        Проверяет тип FTP сервера
        type: [default, mlst, linux, win32]
        """
        if not isinstance(url, Url):
            url = Url(url)
        
        path = '/'.join(url.path.split('/')[:-2]) + '/'
        ftp = cls._ftp_connect(url)
        ftp.cwd(path)

        syst = ''

        try:
            list([item for _, item in ftp.mlsd(url.path)])
            server_type = "mlst"
            return server_type
        except Exception as e:
            cls.log.debug(f"MLSD exception as {e}")
            server_type = "default"

        try:
            syst = ftp.sendcmd("SYST")
        except Exception as e:
            cls.log.debug(f"SYST exception as {e}")

        if 'UNIX' in syst:
            server_type = "linux"
        elif 'Windows' in syst:
            server_type = "win32"

        lines = []
        if server_type == 'linux':
            ftp.retrlines('LIST', lines.append)
            # drwxrwxr-x    2 500      500          4096 Jul 23 09:29 Architector
            if not lines:
                server_type = 'default'
            if re.match(r'[d-]([r-][w-][x-]){3}(\s+\d+){4}\s.+', lines[0]):
                ...
            else:
                server_type = 'default'
        elif server_type == 'win32':
            ftp.retrlines('LIST', lines.append)
            # self.log.info(lines)
            # 09-07-23  10:41PM       <DIR>          RND_LTE
            if len(lines[0].split()) != 4:
                server_type = 'default'

        cls.log.debug(f"{server_type=}")
        return server_type

    @classmethod
    def _ftp_connect(cls, url):
        try:
            # self.ftp = FTP(self.url.host, self.url.user, self.url.passw, timeout=self.args.timeout)
            ftp = FTP(url.host, url.user, url.passw, timeout=cls.args.timeout)
            if cls.args.debugging:
                ftp.set_debuglevel(2)
        except ftplib.error_temp:
            return False
        except socket.timeout:
            return False

        modes = ""
        try:
            modes = ftp.sendcmd("FEAT")
            # self.log.debug("FEAT=%s" % modes)

        except Exception as e:
            cls.log.error("исключение %s при выполнении команды FEAT" % (str(e)))

        if modes.find("UTF8"):
            cls.log.debug("Encoding=UTF-8")
            ftp.encoding = 'utf-8'
        return ftp

    def reconnect(self):
        self.log.info('Reconnecting')
        self.ftp.close()
        for i in range(self.args.retries):
            try:
                self.ftp = self._ftp_connect(self.start_url)
                if self.is_connected():
                    break
            except (ftplib.all_errors, socket.error):
                continue
        else:
            return False
        return True

    def is_connected(self):
        try:
            return self.ftp.voidcmd("NOOP")
        except Exception as e:
            self.log.error("Exception while touch FTP server with error %s" % e)
            return False

    def get_file_size(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        if self.is_mask(url.url):
            return -7
        if not isinstance(url, Url):
            url = Url(url)
        try:
            self.ftp.cwd(url.path)
            return self.ftp.size(url.file)
        except ftplib.all_errors as e:  # ftplib.error_perm:
            self.log.error(f"{url=}")
            self.log.error(full_stack())
            return -1

    def is_dir(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)

        if self.is_mask(url.mask):
            return True
        
        if self.args.broken_size:
            try:
                self.ftp.cwd(url.path)
            except ftplib.all_errors:
                return False
            else:
                return True
        else:
            self.ftp.cwd(url.path)
            size = self.get_file_size(url.path)

            return True if size == -1 else False

    def _list(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        from mylib.Common import full_stack
        out_list = []
        try:
            self.log.debug("ftp.cwd(%s)" % url.path)
            self.ftp.cwd(url.path)
            self.current_path = url.path
            self.current_list = self.ftp.nlst()  # Читаем все, выберем сами
            self.log.debug(str(self.current_list))
            for item in self.current_list:
                self.log.debug(item)
                item = url.full_path + item
                if self.is_dir(item):
                    item += '/'
                if self.is_correspond(item):
                    out_list.append(item)

        except Exception as e:
            self.log.error("Error - %s" % str(e))
            self.log.error(full_stack())
            return -1

        return out_list

    def _mlst_list(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        answ = [(f"{url.full_path}{file_name}"
                 f"{'' if meta.get('type') == 'file' else '/'}") for file_name, meta in self.ftp.mlsd(url.path)]
        return list(filter(self.is_correspond, answ))

    def _linux_list(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        self.ftp.cwd(url.path)
        lines = []
        self.ftp.retrlines('LIST', lines.append)
        answ = [f"{url.full_path}{x.split()[8]}{'/' if x[0] == 'd' else ''}" for x in lines]
        return list(filter(self.is_correspond, answ))

    def _win32_list(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        self.ftp.cwd(url.path)
        lines = []
        self.ftp.retrlines('LIST', lines.append)
        answ = [f"{url.full_path}{x.split()[3]}{'/' if '<DIR>' in x else ''}" for x in lines]
        return list(filter(self.is_correspond, answ))

    def _get_file(self, remote_file, temp_file):
        # self.log.info(f"Скачиваем файл {File}")
        self.log.debug(f"{remote_file=}")
        try:
            with open(temp_file, 'wb') as local_file:
                self.log.debug("файл %s открыт" % temp_file)
                self.log.debug(remote_file)
                rez = self.ftp.retrbinary(f'RETR {remote_file.path}{remote_file.file}', local_file.write)
                self.log.debug("файл скачан %s" % rez)
                local_file.close()
        except Exception as e:
            self.log.error(f"Ошибка получения файла {e}")
            if not self.is_connected():
                self.reconnect()
            if 'local_file' in locals():
                local_file.close()
            return False
        '''
        except Exception as e:
            self.log.error(f"Неустановленная ошибка при приеме файла {e}")
            self.log.error(full_stack())
            return False
        '''
        return True

    def put_file(self, url: Union[Url, str]):
        ...

    def remove(self, url: Union[Url, str]):
        if not isinstance(url, Url):
            url = Url(url)
        self.ftp.cwd(url.path)
        self.ftp.delete(url.file)
        self.log.debug(f"REMOVE FILE {url.path}{url.file}")
