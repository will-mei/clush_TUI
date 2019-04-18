#!/usr/bin/env python
# coding=utf-8

class zstr(str):
    def __add__(self, y):
        tmp_str = str(self) + str(y)
        return zstr(tmp_str)
    def __len__(self):
        tx = str(self) + ''
        return len(tx) + list(map(lambda x : 1 if '\u4e00' <= x <= '\u9fff' else 0, tx)).count(1)
