#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil

__author__ = "wiom"
__version__ = "0.1.0"
__date__ = "31.07.16 16:31"
__description__ = """Скрипт для развертывания проекта. Инициализирует необходимые папки, файлы и настройки"""


class Init:

    dirs = [
        'logs',
        'screen'
    ]

    files = [
        'proxy',
        'search_requests'
    ]

    conf_file = 'settings.cfg'

    lib = 'lib/%s'
    conf_source = 'config.py'
    sub_pattern_from = r"def \_\_init\_\_\(self\, file\=\'.*\'\)"
    sub_pattern_to = "def __init__(self, file='{}')".format(conf_file)

    def cat_dir(self):
        for dir in self.dirs:
            try:
                os.mkdir(dir)
            except FileExistsError:
                pass
        return self

    def cat_files(self):
        for file in self.files:
            open(file, 'w')
        return self

    def change_config_source(self):
        with open(self.conf_source, 'r') as f:
            source = f.read()
        source = re.sub(self.sub_pattern_from, self.sub_pattern_to, source)
        with open(self.conf_source, 'w') as f:
            f.write(source)
        return self

    def load_def_settings(self):
        try:
            shutil.copyfile(self.lib % self.conf_file, self.conf_file)
        except IOError:
            pass
        return self


Init().change_config_source().load_def_settings().cat_dir().cat_files()
