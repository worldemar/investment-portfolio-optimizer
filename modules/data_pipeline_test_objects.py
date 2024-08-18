#!/usr/bin/env python3

import time


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


def sum5(a, b, c, d, e):  # pylint: disable=invalid-name
    start = time.time()
    while time.time() - start < (a + b + c + d + e) / 100 % 1:
        _ = a + b + c + d + e
    return a + b + c + d + e


def prod5(a, b, c, d, e):  # pylint: disable=invalid-name
    start = time.time()
    while time.time() - start < (a * b * c * d * e) / 100 % 1:
        _ = a * b * c * d * e
    return a * b * c * d * e


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


class ClosureFunction:
    def __init__(self):
        self.context = ''
    
    def __call__(self, arg):
        self.context += f'{arg}'
        return self.context

    def __copy__(self):
        assert False, "should not be called"

    def __deepcopy__(self, memo):
        assert False, "should not be called"
