#!/usr/bin/env python3

import random
from modules.convex_hull import LazyMultilayerConvexHull, ConvexHullPoint

class PointMock(ConvexHullPoint):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y

    def __lt__(self, other):
        return [self._x, self._y] < [other._x, other._y]

    def __repr__(self):
        return f'[{self._x}, {self._y}]'


lmch = LazyMultilayerConvexHull(max_dirty_points=1000, layers=3)
for i in range(10000):
    lmch(PointMock(random.random(), random.random()))
hull = lmch(None)
