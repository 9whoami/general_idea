# -*- coding: utf-8 -*-
import logging
import inspect
import os

from os.path import isfile
from datetime import datetime
from config import Conf

__author__ = 'whoami'
__version__ = '1.0.1'
__date__ = '27.03.16 0:46'
__description__ = """
Оборачиваем работу проекта в лог
"""

config = Conf()
config.read_section('logger')


def get_class_variable_state(fun):
    def wrapper(cls):
        head_line = '*' * 5 + ' {0} varible state '.format(cls.__class__) + '*' * 5
        foter_line = '*' * len(head_line)
        body_line = ''
        dct = dict(map(lambda x: (x, getattr(cls, x)),
                       filter(lambda x: '__' not in x and isinstance(getattr(cls, x), (tuple, list, int, str, set, dict)),
                              cls.__dir__())))
        for key in dct:
            body_line += '{0} : {1}\n'.format(key, dct[key])

        return '\n{0}\n{1}\n{2}'.format(head_line, body_line, foter_line)

    return wrapper


def call_info(fun):

    def wrapper(self, *args, **kwargs):
        result = None
        stack = inspect.stack()
        info = '\nCaller: {}\nCalling: {}\nargs: {}\nkwargs: {}'.format(
            stack[1][3], str(fun), str(args), str(kwargs))
        try:
            result = fun(self, *args, **kwargs)
        except Exception as e:
            Logger().critical(info, '\nException: {}'.format(e))
        else:
            Logger().info(info, '\nResult: {}'.format(result))
        finally:
            return result

    return wrapper


class SingletonMetaclass(type):
    """
    Метаксласс для разовой инициализации класса Logger и возврата
    объекта логгера
    """
    def __init__(cls, *args, **kw):
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(
                SingletonMetaclass, cls).__call__(*args, **kw)
        return cls.instance


class Logger(metaclass=SingletonMetaclass):
    def __init__(self):
        # '%(module)s' at line %(lineno)d:
        log_msg_format = "%(asctime)s.%(msecs)d %(levelname)s in %(message)s"

        level = logging.DEBUG if int(config.debug) else logging.INFO


        log_filename = config.log_path + '{}.log'.format(str(datetime.now()))
        formatter = logging.Formatter(log_msg_format)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)

        self.logger.addHandler(console)
        if not isfile(log_filename):
            try:
                with open(log_filename, 'w') as _:
                    pass
                file_handler = logging.FileHandler(log_filename)
                file_handler.setFormatter(formatter)
                file_handler.setLevel(level)
                self.logger.addHandler(file_handler)
            except Exception:
                pass

    @staticmethod
    def get_call_info():
        stack = inspect.stack()
        module = os.path.basename(stack[2][1])
        line = stack[2][2]
        return module, line

    def info(self, *msg):
        self.logger.info("'{}' at line {}: ".format(*self.get_call_info()) +
                         ', '.join(map(lambda x: str(x), msg)))

    def error(self, *msg):
        self.logger.error("'{}' at line {}: ".format(*self.get_call_info()) +
                          ', '.join(map(lambda x: str(x), msg)))

    def warning(self, *msg):
        self.logger.warning("'{}' at line {}: ".format(*self.get_call_info()) +
                            ', '.join(map(lambda x: str(x), msg)))

    def critical(self, *msg):
        self.logger.critical("'{}' at line {}: ".format(*self.get_call_info()) +
                             ', '.join(map(lambda x: str(x), msg)))

    def debug(self, *msg):
        self.logger.debug("'{}' at line {}: ".format(*self.get_call_info()) +
                          ', '.join(map(lambda x: str(x), msg)))
