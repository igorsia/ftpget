#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

from mylib import Target, Url


class LocalTarget(Target):
    
    def __init__(self, url, **kwargs):
        Target.__init__(self, url, **kwargs)
        if not isinstance(url, Url):
            url = Url(url)
        # print("INIT File", self.Path)
        if os.path.exists(url.path):
            return
        try:
            os.makedirs(url.path)
        except os.error:
            self.log.error("Ошибка создания каталога %s" % url.path)
            # quit()
        return
    
    def list(self, url):
        if not isinstance(url, Url):
            url = Url(url)
        os.listdir(url.path)
    
    def get_file(self, target):
        print("не описан метод копирования", type(self), "в", type(target))
