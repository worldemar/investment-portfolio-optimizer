#!/usr/bin/env python3

import time
from math import prod
from modules.data_pipeline import DelayedResultFunction


def generate_integers(a, b):  # pylint: disable=invalid-name
    for i in range(a, b):
        yield [i]


def power(x=1, y=1, t=1):  # pylint: disable=invalid-name
    start = time.time()
    while time.time() - start < t:
        _ = x**y
    return x**y


def plus(x=1, y=1, t=1):  # pylint: disable=invalid-name
    start = time.time()
    while time.time() - start < t:
        _ = x + y
    return x + y


def minus(x=1, y=1, t=1):  # pylint: disable=invalid-name
    start = time.time()
    while time.time() - start < t:
        _ = x - y
    return x - y


def mod(x=1, y=1, t=1):  # pylint: disable=invalid-name
    start = time.time()
    while time.time() - start < t:
        _ = x % y
    return x % y


def sumt(items):
    start = time.time()
    while time.time() - start < sum(items) / 100 % 1:
        _ = sum(items)
    return sum(items)


def prodt(items):
    start = time.time()
    while time.time() - start < prod(items) / 100 % 1:
        _ = prod(items)
    return prod(items)


class CallTracker:
    def __init__(self):
        self.calls = 0

    def __copy__(self):
        assert False, "should not be called"

    def __deepcopy__(self, memo):
        assert False, "should not be called"

    def call(self):
        self.calls += 1
        return self


def call_the_tracker(tracker: CallTracker, calls: int):
    for _ in range(calls):
        tracker.call()
    return tracker


# pylint: disable=too-few-public-methods
class StringAppender:
    def __init__(self):
        self.string = ''

    def __call__(self, arg):
        self.string += f'{arg}'
        return self.string


# pylint: disable=too-few-public-methods
class IntegerAverager(DelayedResultFunction):
    def __init__(self, yield_divisor: int = 0):
        self.yield_divisor = yield_divisor
        self.sum = 0
        self.count = 0

    def __call__(self, arg):
        if arg is None:
            return self.sum / self.count
        self.sum += arg
        self.count += 1
        if self.yield_divisor != 0 and self.count != 0 and self.count % self.yield_divisor == 0:
            return self.sum / self.count
        return None
