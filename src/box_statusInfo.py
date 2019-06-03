#!/usr/bin/env python
# coding=utf-8

import time
from src import npyscreen

class statusBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.Pager
    pass

