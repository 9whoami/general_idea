#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from config import Conf

__author__ = "wiom"
__version__ = "0.0.0"
__date__ = "31.07.16 16:31"
__description__ = """Скрипт для развертывания проекта. Инициализирует необходимые папки, файлы и настройки"""


class Init:
    dirs = ['logs', 'screen']
    files = ['proxy', 'search_requests']
    conf_file = 'settings.cfg'
    conf_source = 'config.py'
    sub_pattern_from = "def __init__(self, file='')"
    sub_pattern_to = "def __init__(self, file='{}')".format(conf_source)

    def __init__(self):
        self.default_conf = {
            'base': {'init': '1'},
            'log': {'dir': '', 'p': '2'}
        }

    def cat_dir(self):
        for dir in self.dirs:
            os.mkdir(dir)

    def cat_files(self):
        for file in self.files:
            open(file, 'w')

    def load_def_settings(self):

        with open(self.conf_source, 'r') as f:
            source = f.read()
        source = re.sub(self.sub_pattern_from, self.sub_pattern_to, source, count=1)
        with open(self.conf_source, 'w') as f:
            f.write(source)

        conf = Conf(file=self.conf_file)
        for section in self.default_conf:
            conf.write_file(section=section, **self.default_conf[section])

base_class = Init()
base_class.load_def_settings()
