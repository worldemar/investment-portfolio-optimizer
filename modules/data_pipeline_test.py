#!/usr/bin/env python3

import concurrent.futures
from functools import partial
from modules.data_pipeline import chain_generators
from modules.data_pipeline_test_objects import generate_integers, power, plus, minus, mod, sum5, prod5, call_the_tracker
from modules.data_pipeline_test_objects import CallTracker, ClosureFunction

PROCESS_EXECUTOR = concurrent.futures.ProcessPoolExecutor(max_workers=4)
THREAD_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def test_linear_chain():
    """ chain of functions passing single value """
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 10)], [partial(power, y=3, t=.3)])
    result2 = chain_generators(PROCESS_EXECUTOR, [result1], [partial(plus, y=7, t=.1)])
    result3 = chain_generators(PROCESS_EXECUTOR, [result2], [partial(minus, y=10, t=.2)])
    result4 = chain_generators(PROCESS_EXECUTOR, [result3], [partial(power, y=2, t=.1)])
    result5 = chain_generators(PROCESS_EXECUTOR, [result4], [partial(mod, y=100, t=0)])
    expected_values = [9, 4, 25, 76, 21, 84, 69, 0, 81, 76]
    result_list = list(result5)
    assert len(result_list) == len(expected_values)
    for i in zip(result_list, expected_values):
        assert len(i[0]) == 1
        assert i[0][0] == i[1]


def test_fork():
    """ generator multiplexed to multiple-value layer """
    result = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 11)], [
        partial(power, y=1, t=.5),
        partial(power, y=2, t=.4),
        partial(power, y=3, t=.3),
        partial(power, y=4, t=.2),
        partial(power, y=5, t=.1),
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
    assert len(result_list) == len(expected_layers)
    for i in zip(result_list, expected_layers):
        assert i[0] == i[1]


def test_fork_copies():
    the_tracker = CallTracker()
    result = chain_generators(PROCESS_EXECUTOR, [[[the_tracker]]], [
        partial(call_the_tracker, calls=3),
        partial(call_the_tracker, calls=5),
        partial(call_the_tracker, calls=7),
    ])
    result_list = list(result)
    assert len(result_list) == 1
    assert result_list[0][0].calls == 3
    assert result_list[0][1].calls == 5
    assert result_list[0][2].calls == 7


def test_join():
    """ multiple generators joined with single function """
    result = chain_generators(PROCESS_EXECUTOR, [
        generate_integers(0, 5),
        generate_integers(5, 10),
        generate_integers(15, 20),
        generate_integers(3, 8),
        generate_integers(7, 12),
    ], [prod5])
    expected = [0, 3072, 10710, 25920, 52668]
    result_list = list(result)
    assert len(result_list) == len(expected)
    for i in zip(result_list, expected):
        assert len(i[0]) == 1
        assert i[0][0] == i[1]


def test_aggregate():
    """ multiple-value layer aggregated with single function """
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 11)], [
        partial(power, y=1, t=.5),
        partial(power, y=2, t=.4),
        partial(power, y=3, t=.3),
        partial(power, y=4, t=.2),
        partial(power, y=5, t=.1),
    ])
    result2 = chain_generators(PROCESS_EXECUTOR, [result1], [sum5])
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
    assert len(result_list) == len(expected_values)
    for i in zip(result_list, expected_values):
        assert len(i[0]) == 1
        assert i[0][0] == i[1]


def test_statistics():
    """ multiple-value layer aggregated to multiple functions """
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 11)], [
        partial(power, y=1, t=.5),
        partial(power, y=2, t=.4),
        partial(power, y=3, t=.3),
        partial(power, y=4, t=.2),
        partial(power, y=5, t=.1),
    ])
    result2 = chain_generators(PROCESS_EXECUTOR, [result1], [sum5, prod5])
    expected_layers = [
        [sum([0, 0, 0, 0, 0]), prod5(0, 0, 0, 0, 0)],
        [sum([1, 1, 1, 1, 1]), prod5(1, 1, 1, 1, 1)],
        [sum([2, 4, 8, 16, 32]), prod5(2, 4, 8, 16, 32)],
        [sum([3, 9, 27, 81, 243]), prod5(3, 9, 27, 81, 243)],
        [sum([4, 16, 64, 256, 1024]), prod5(4, 16, 64, 256, 1024)],
        [sum([5, 25, 125, 625, 3125]), prod5(5, 25, 125, 625, 3125)],
        [sum([6, 36, 216, 1296, 7776]), prod5(6, 36, 216, 1296, 7776)],
        [sum([7, 49, 343, 2401, 16807]), prod5(7, 49, 343, 2401, 16807)],
        [sum([8, 64, 512, 4096, 32768]), prod5(8, 64, 512, 4096, 32768)],
        [sum([9, 81, 729, 6561, 59049]), prod5(9, 81, 729, 6561, 59049)],
        [sum([10, 100, 1000, 10000, 100000]), prod5(10, 100, 1000, 10000, 100000)],
    ]
    result_list = list(result2)
    assert len(result_list) == len(expected_layers)
    for i in zip(result_list, expected_layers):
        assert len(i[0]) == 2
        assert i[0][0] == i[1][0]
        assert i[0][1] == i[1][1]


def test_closure_class():
    closure = ClosureFunction()
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 5)], [str])
    result2 = chain_generators(THREAD_EXECUTOR, [result1], [closure])
    list_result = list(result2)
    expected_layers = [['0'], ['01'], ['012'], ['0123'], ['01234']]
    assert list_result == expected_layers
