#!/usr/bin/env python3

import concurrent.futures
from functools import partial
from modules.data_pipeline import chain_generators
import time

EXECUTOR = concurrent.futures.ProcessPoolExecutor(max_workers=4)

def _generate_integers(a, b):
    for i in range(a, b):
        yield [i]

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

def _sum5(a, b, c, d, e):
    t1 = time.time()
    while time.time() - t1 < (a + b + c + d + e)/100 % 1:
        a + b + c + d + e
    return a + b + c + d + e

def _prod5(a, b, c, d, e):
    t1 = time.time()
    while time.time() - t1 < (a * b * c * d * e)/100 % 1:
        a * b * c * d * e
    return a * b * c * d * e

def test_linear_chain():
    """ chain of functions passing single value """
    result = chain_generators(EXECUTOR, [_generate_integers(0, 10) ], [partial(_power, y=3, t=.3)])
    result2 = chain_generators(EXECUTOR, [result], [partial(_plus, y=7, t=.1)])
    result3 = chain_generators(EXECUTOR, [result2], [partial(_minus, y=10, t=.2)])
    result4 = chain_generators(EXECUTOR, [result3], [partial(_power, y=2, t=.1)])
    result5 = chain_generators(EXECUTOR, [result4], [partial(_mod, y=100, t=0)])
    result_list = list(result5)
    expected_values = [9, 4, 25, 76, 21, 84, 69, 0, 81, 76]
    assert(len(result_list) == len(expected_values))
    for i in zip(result_list, expected_values):
        assert(len(i[0]) == 1)
        assert(i[0][0] == i[1])

def test_fork():
    """ generator multiplexed to multiple-value layer """
    result = chain_generators(EXECUTOR, [_generate_integers(0, 11)],
        [
            partial(_power, y=1, t=.5),
            partial(_power, y=2, t=.4),
            partial(_power, y=3, t=.3),
            partial(_power, y=4, t=.2),
            partial(_power, y=5, t=.1),
        ])
    expected_layers = [
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [2, 4, 8, 16, 32],
        [3, 9, 27, 81, 243],
        [4, 16, 64, 256, 1024],
        [5, 25, 125, 625, 3125],
        [6, 36, 216, 1296, 7776],
        [7, 49, 343, 2401, 16807],
        [8, 64, 512, 4096, 32768],
        [9, 81, 729, 6561, 59049],
        [10, 100, 1000, 10000, 100000],
    ]
    result_list = list(result)
    assert(len(result_list) == len(expected_layers))
    for i in zip(result_list, expected_layers):
        assert(i[0] == i[1])

def test_join():
    """ multiple generators joined with single function """
    result = chain_generators(EXECUTOR, [
            _generate_integers(0,5),
            _generate_integers(5,10),
            _generate_integers(15,20),
            _generate_integers(3,8),
            _generate_integers(7,12),
        ], [_prod5])
    expected = [0, 3072, 10710, 25920, 52668]
    result_list = list(result)
    assert(len(result_list) == len(expected))
    for i in zip(result_list, expected):
        assert(len(i[0]) == 1)
        assert(i[0][0] == i[1])

def test_aggregate():
    """ multiple-value layer aggregated with single function """
    result = chain_generators(EXECUTOR, [_generate_integers(0, 11)],
        [
            partial(_power, y=1, t=.5),
            partial(_power, y=2, t=.4),
            partial(_power, y=3, t=.3),
            partial(_power, y=4, t=.2),
            partial(_power, y=5, t=.1),
        ])
    result = list(result)
    result2 = chain_generators(EXECUTOR, [result], [_sum5])
    expected_values = [
        sum([0, 0, 0, 0, 0]),
        sum([1, 1, 1, 1, 1]),
        sum([2, 4, 8, 16, 32]),
        sum([3, 9, 27, 81, 243]),
        sum([4, 16, 64, 256, 1024]),
        sum([5, 25, 125, 625, 3125]),
        sum([6, 36, 216, 1296, 7776]),
        sum([7, 49, 343, 2401, 16807]),
        sum([8, 64, 512, 4096, 32768]),
        sum([9, 81, 729, 6561, 59049]),
        sum([10, 100, 1000, 10000, 100000]),
    ]
    result_list = list(result2)
    assert(len(result_list) == len(expected_values))
    for i in zip(result_list, expected_values):
        assert(len(i[0]) == 1)
        assert(i[0][0] == i[1])

def test_statistics():
    """ multiple-value layer aggregated to multiple functions """
    result = chain_generators(EXECUTOR, [_generate_integers(0, 11)],
        [
            partial(_power, y=1, t=.5),
            partial(_power, y=2, t=.4),
            partial(_power, y=3, t=.3),
            partial(_power, y=4, t=.2),
            partial(_power, y=5, t=.1),
        ])
    result = list(result)
    result2 = chain_generators(EXECUTOR, [result], [_sum5, _prod5])
    expected_layers = [
        [sum([0, 0, 0, 0, 0]),_prod5(0, 0, 0, 0, 0)],
        [sum([1, 1, 1, 1, 1]),_prod5(1, 1, 1, 1, 1)],
        [sum([2, 4, 8, 16, 32]),_prod5(2, 4, 8, 16, 32)],
        [sum([3, 9, 27, 81, 243]),_prod5(3, 9, 27, 81, 243)],
        [sum([4, 16, 64, 256, 1024]),_prod5(4, 16, 64, 256, 1024)],
        [sum([5, 25, 125, 625, 3125]),_prod5(5, 25, 125, 625, 3125)],
        [sum([6, 36, 216, 1296, 7776]),_prod5(6, 36, 216, 1296, 7776)],
        [sum([7, 49, 343, 2401, 16807]),_prod5(7, 49, 343, 2401, 16807)],
        [sum([8, 64, 512, 4096, 32768]),_prod5(8, 64, 512, 4096, 32768)],
        [sum([9, 81, 729, 6561, 59049]),_prod5(9, 81, 729, 6561, 59049)],
        [sum([10, 100, 1000, 10000, 100000]),_prod5(10, 100, 1000, 10000, 100000)],
    ]
    result_list = list(result2)
    assert(len(result_list) == len(expected_layers))
    for i in zip(result_list, expected_layers):
        assert(len(i[0]) == 2)
        assert(i[0][0] == i[1][0])
        assert(i[0][1] == i[1][1])
