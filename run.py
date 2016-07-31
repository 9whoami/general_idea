#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from main import runer
from logger import Logger
from threadpool import ThreadPool
from virtual_display import VirtualDisplay

__author__ = "wiom"
__version__ = "0.0.0"
__date__ = "31.07.16 3:21"
__description__ = """"""

th_pool = ThreadPool(max_threads=1)
logger = Logger()

if __name__ == '__main__':
    virt_disp = VirtualDisplay()
    virt_disp.start()
    while True:
        try:
            runer()
        except KeyboardInterrupt:
            logger.info('Job canceled by the user')
            raise SystemExit
        except Exception:
            continue
    virt_disp.stop()
