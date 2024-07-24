#!/usr/bin/env python3

from functools import partial
from modules.data_pipeline import generator_multiplex
import time

def _power(x=1, y=1, t=1):
    t1 = time.time()
    while time.time() - t1 < t:
        x**y
    return x**y

def _plus(x=1, y=1, t=1):
    t1 = time.time()
    while time.time() - t1 < t:
        x + y
    return x + y

def _minus(x=1, y=1, t=1):
    t1 = time.time()
    while time.time() - t1 < t:
        x - y
    return x - y

def _mod(x=1, y=1, t=1):
    t1 = time.time()
    while time.time() - t1 < t:
        x % y
    return x % y

def test_generator_multiplex():
    result = generator_multiplex(
        range(12), [
            partial(_power, y=3, t=3),
            partial(_plus, y=7, t=2),
            partial(_minus, y=5, t=1),
            partial(_mod, y=4, t=0),
        ])
    expected = [
        [0, 7, -5, 0],
        [1, 8, -4, 1],
        [8, 9, -3, 2],
        [27, 10, -2, 3],
        [64, 11, -1, 0],
        [125, 12, 0, 1],
        [216, 13, 1, 2],
        [343, 14, 2, 3],
        [512, 15, 3, 0],
        [729, 16, 4, 1],
        [1000, 17, 5, 2],
        [1331, 18, 6, 3],
    ]
    for i in zip(result, expected):
        assert(i[0] == i[1])
