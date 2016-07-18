#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "whoami"
__version__ = "0.0.1"
__date__ = "09.07.16 17:57"
__description__ = """"""

from configparser import ConfigParser, Error


class Conf(ConfigParser):
    def __init__(self, file='settings.cfg'):
        super().__init__()
        self.cfg_file = file
        self.namespace = dict()

    def __getattr__(self, item):
        if item in self.namespace:
            return self.namespace[item]

    def write_file(self, section, option, value):
        """
        Записывает настройки в файл
        :param file:
        :param section:
        :param option:
        :param value:
        :return:
        """
        try:
            self.read(self.cfg_file)
            self.set(section, option, str(value))
            with open(self.cfg_file, "w") as f:
                self.write(f)
        except (Error, TypeError) as e:
            print(e)

    def read_section(self, section: str) -> None:
        """
        Читает настройки
        :param args: первыйм параметром идет имя файла, затем имя секции
        :param kwargs: file, section
        :return: dict в случае успеха иначе None
        """

        try:
            self.namespace.clear()

            self.read(self.cfg_file)
            if self.has_section(section):
                items = self.items(section)
                for item in items:
                    self.namespace[item[0]] = item[1]
            else:
                raise Error(
                    'Section {0!r} not found in the {1!r} file'.format(section, self.cfg_file))
        except Error as e:
            print(e)

