#!/usr/bin/env python
# coding: utf-8

import os
import time
from collections import defaultdict
import dbm

def now():
    return int(time.time())

class ThrottleDB:
    _db = dict()

    def __init__(self, filename):
        self.filename = os.path.realpath(filename)

    @property
    def db(self):
        if self.filename not in self._db:
            self._db[self.filename] = dbm.open(self.filename, 'c')
        return self._db[self.filename]

    def __del__(self):
        self.db.close()

class OverThrottle(Exception):
    def __init__(self, blah='too fast'):
        super().__init__(blah)

class Ticks(defaultdict):
    def __repr__(self):
        i = ', '.join(f'{x}' for x in self.items())
        return f'Ticks({i})'

class TimeCounts(defaultdict):
    def __repr__(self):
        n = now()
        i = ', '.join(f'{c}@{n-t}' for t,c in self.items())
        return f'TimeCounts({i})'

class Throttle:
    db = None
    _count = 0
    _ticks = Ticks(lambda: TimeCounts(lambda: 0))

    def __init__(self, name, items_per_interval, interval_in_seconds, filename=None):
        self.name = name
        self.interval = int(interval_in_seconds)
        self.limit = int(items_per_interval)
        if filename:
            self.db = ThrottleDB(filename)
            if self.name in self.db:
                self.ticks[self.name] = self.db[self.name]
        self.cleanup_ticks()

    @property
    def ticks(self):
        return self._ticks[self.name]

    def cleanup_ticks(self):
        n = now()
        t = self.ticks
        todo = list()
        for k in t:
            if n-k >= self.interval:
                todo.append(k)
        for k in todo:
            del t[k]
        if todo and self.db:
            self.db[self.name] = t
        self._count = sum(v for v in t.values())
        return self._count

    @property
    def count(self):
        self.cleanup_ticks()
        return self._count

    def tick(self):
        n = int(now())
        c = self.cleanup_ticks()
        if c >= self.limit:
            raise OverThrottle()
        self.ticks[n] += 1
        if self.db:
            self.db[self.name] = t

    def __repr__(self):
        c = self.count
        return str(self.ticks).replace('TimeCounts','Throttle') + f' => {c} / {self.limit}'
