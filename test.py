#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from config import Conf

c = Conf()
c.read_section('base')
print(c.namespace)
