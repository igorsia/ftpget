#!/usr/bin/python3
import re
from typing import Union

import httplib2
import requests
from bs4 import BeautifulSoup

from mylib import Url,  parse_mask, Target


class HttpTarget(Target):

    def remove(self, url: Union[Url, str]):
        pass

    def _get_file(self, source_file, temp_file):
        pass

    def reconnect(self):
        pass

    def __init__(self, url):
        Target.__init__(self, url)

    def get_file_size(self, url: Union[Url, str]):
        import requests
        response = requests.head(url, allow_redirects=True)
        size = response.headers.get('content-length', 0)
        return int(size)

    def is_dir(self, url: Union[Url, str]):
        if url[-1] == '/':
            return True
        return False

    def _list(self, url: Union[Url, str]):
        page = requests.get(Url(url).full_path)
        # print(page.status_code)

        soup = BeautifulSoup(page.text, features="lxml")
        files = soup.findAll('a', href=True, tite=False)
        files = [file_.text for file_ in files]

        return files

    def put_file(self, url):
        raise NotImplementedError

    def get_file(self, source, target):
        self.log.debug(f"get_file({source}, {target})")
        try:
            with open(target, 'wb') as fl:
                h = httplib2.Http()
                response, content = h.request(source)
                fl.write(content)

        except Exception as e:
            self.log.error(f"Ошибка получения файла {e}")
            return False

        if response.reason == "OK":
            return True
        return False



