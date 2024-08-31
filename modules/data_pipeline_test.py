#!/usr/bin/env python3

import copy
import concurrent.futures
from functools import partial
from math import prod
import pytest
from modules.data_pipeline import chain_generators, DelayedResultFunction, ParameterFormat
from modules.data_pipeline_test_objects import generate_integers, power, plus, minus, mod, sumt, prodt, call_the_tracker
from modules.data_pipeline_test_objects import CallTracker, StringAppender, IntegerAverager

PROCESS_EXECUTOR = concurrent.futures.ProcessPoolExecutor(max_workers=4)
THREAD_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def test_chain_single_value_linear():
    """ chain of functions passing single value """
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 10)],
                               [partial(power, y=3, t=.3)], ParameterFormat.VALUE)
    result2 = chain_generators(PROCESS_EXECUTOR, [result1], [partial(plus, y=7, t=.1)], ParameterFormat.VALUE)
    result3 = chain_generators(PROCESS_EXECUTOR, [result2], [partial(minus, y=10, t=.2)], ParameterFormat.VALUE)
    result4 = chain_generators(PROCESS_EXECUTOR, [result3], [partial(power, y=2, t=.1)], ParameterFormat.VALUE)
    result5 = chain_generators(PROCESS_EXECUTOR, [result4], [partial(mod, y=100, t=0)], ParameterFormat.VALUE)
    expected_values = [9, 4, 25, 76, 21, 84, 69, 0, 81, 76]
    result_list = list(result5)
    assert len(result_list) == len(expected_values)
    for i in zip(result_list, expected_values):
        assert len(i[0]) == 1
        assert i[0][0] == i[1]


def test_chain_layer_expand_from_one():
    """ generator multiplexed to multiple-value layer """
    result = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 11)], [
        partial(power, y=1, t=.5),
        partial(power, y=2, t=.4),
        partial(power, y=3, t=.3),
        partial(power, y=4, t=.2),
        partial(power, y=5, t=.1),
    ], ParameterFormat.ARGS)
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


def test_executor_process_copies():
    the_tracker = CallTracker()
    result = chain_generators(PROCESS_EXECUTOR, [[[the_tracker]]], [
        partial(call_the_tracker, calls=3),
        partial(call_the_tracker, calls=5),
        partial(call_the_tracker, calls=7),
    ], ParameterFormat.ARGS)
    result_list = list(result)
    assert len(result_list) == 1
    assert result_list[0][0].calls == 3
    assert result_list[0][1].calls == 5
    assert result_list[0][2].calls == 7


def test_chain_layer_collapse_generators_to_one():
    """ multiple generators joined with single function """
    result = chain_generators(PROCESS_EXECUTOR, [
        generate_integers(0, 5),
        generate_integers(5, 10),
        generate_integers(15, 20),
        generate_integers(3, 8),
        generate_integers(7, 12),
    ], [prodt], ParameterFormat.LIST)
    expected = [0, 3072, 10710, 25920, 52668]
    result_list = list(result)
    assert len(result_list) == len(expected)
    for i in zip(result_list, expected):
        assert len(i[0]) == 1
        assert i[0][0] == i[1]


def test_chain_layer_collapse_functions_to_one():
    """ multiple-value layer aggregated with single function """
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 11)], [
        partial(power, y=1, t=.5),
        partial(power, y=2, t=.4),
        partial(power, y=3, t=.3),
        partial(power, y=4, t=.2),
        partial(power, y=5, t=.1),
    ], ParameterFormat.ARGS)
    result2 = chain_generators(PROCESS_EXECUTOR, [result1], [sumt], ParameterFormat.LIST)
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


def test_chain_layer_collapse_functions_to_two():
    """ multiple-value layer aggregated to multiple functions """
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 11)], [
        partial(power, y=1, t=.5),
        partial(power, y=2, t=.4),
        partial(power, y=3, t=.3),
        partial(power, y=4, t=.2),
        partial(power, y=5, t=.1),
    ], ParameterFormat.ARGS)
    result2 = chain_generators(PROCESS_EXECUTOR, [result1], [sumt, prodt], ParameterFormat.LIST)
    expected_layers = [
        [sum([0, 0, 0, 0, 0]), prod([0, 0, 0, 0, 0])],
        [sum([1, 1, 1, 1, 1]), prod([1, 1, 1, 1, 1])],
        [sum([2, 4, 8, 16, 32]), prod([2, 4, 8, 16, 32])],
        [sum([3, 9, 27, 81, 243]), prod([3, 9, 27, 81, 243])],
        [sum([4, 16, 64, 256, 1024]), prod([4, 16, 64, 256, 1024])],
        [sum([5, 25, 125, 625, 3125]), prod([5, 25, 125, 625, 3125])],
        [sum([6, 36, 216, 1296, 7776]), prod([6, 36, 216, 1296, 7776])],
        [sum([7, 49, 343, 2401, 16807]), prod([7, 49, 343, 2401, 16807])],
        [sum([8, 64, 512, 4096, 32768]), prod([8, 64, 512, 4096, 32768])],
        [sum([9, 81, 729, 6561, 59049]), prod([9, 81, 729, 6561, 59049])],
        [sum([10, 100, 1000, 10000, 100000]), prod([10, 100, 1000, 10000, 100000])],
    ]
    result_list = list(result2)
    assert len(result_list) == len(expected_layers)
    for i in zip(result_list, expected_layers):
        assert len(i[0]) == 2
        assert i[0][0] == i[1][0]
        assert i[0][1] == i[1][1]


def test_chain_layer_collapse_functions_to_two_by_value():
    """ multiple-value layer aggregated to multiple functions """
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 6)], [
        partial(power, y=2, t=.1),
        partial(power, y=3, t=.1),
    ], ParameterFormat.ARGS)
    result2 = chain_generators(PROCESS_EXECUTOR, [result1], [
        partial(plus, y=1, t=.1),
        partial(plus, y=-1, t=.1),
    ], ParameterFormat.VALUE)
    expected_layers = [[1, -1], [2, 0], [5, 7], [10, 26], [17, 63], [26, 124]]
    result_list = list(result2)
    assert len(result_list) == len(expected_layers)
    for i in zip(result_list, expected_layers):
        assert len(i[0]) == 2
        assert i[0][0] == i[1][0]
        assert i[0][1] == i[1][1]


def test_chain_stateful_function():
    result1 = chain_generators(PROCESS_EXECUTOR, [generate_integers(0, 5)], [str], ParameterFormat.VALUE)
    result2 = chain_generators(THREAD_EXECUTOR, [result1], [StringAppender()], ParameterFormat.VALUE)
    list_result = list(result2)
    expected_layers = [['0'], ['01'], ['012'], ['0123'], ['01234']]
    assert list_result == expected_layers


def test_chain_layer_skip_all():
    result1 = chain_generators(THREAD_EXECUTOR,
                               [generate_integers(0, 38)],
                               [IntegerAverager()],
                               ParameterFormat.VALUE)
    list_result = list(result1)
    expected_layers = [[18.5]]
    assert list_result == expected_layers


def test_chain_layer_ensure_funcnum_for_value_parameter_format():
    with pytest.raises(ValueError):
        result = chain_generators(THREAD_EXECUTOR,
                         [generate_integers(0, 38)],
                         [IntegerAverager(), StringAppender()],
                         ParameterFormat.VALUE)
        _ = list(result)


def test_chain_layer_ensure_functypes():
    with pytest.raises(ValueError):
        result = chain_generators(THREAD_EXECUTOR,
                         [generate_integers(0, 38)],
                         [IntegerAverager(), sumt],
                         ParameterFormat.LIST)
        _ = list(result)


def test_chain_layers_skip_some():
    def avg(values):
        values_list = list(values)
        return sum(values_list) / len(values_list)
    result1 = chain_generators(THREAD_EXECUTOR,
                               [generate_integers(0, 17)],
                               [IntegerAverager(5), IntegerAverager(3)],
                               ParameterFormat.ARGS)
    list_result = list(result1)
    expected_layers = [
        [None,           avg(range(3))],
        [avg(range(5)),  None],
        [None,           avg(range(6))],
        [None,           avg(range(9))],
        [avg(range(10)), None],
        [None,           avg(range(12))],
        [avg(range(15)), avg(range(15))],
        [avg(range(17)), avg(range(17))],  # this is the last layer formed by calling IntegerAverager-s with None
    ]
    assert list_result == expected_layers


def test_chainable_function_init():
    chainable = DelayedResultFunction()
    assert isinstance(chainable, DelayedResultFunction)


def test_chainable_function_copy():
    chainable = DelayedResultFunction()
    with pytest.raises(NotImplementedError):
        copy.copy(chainable)


def test_chainable_function_deepcopy():
    chainable = DelayedResultFunction()
    with pytest.raises(NotImplementedError):
        copy.deepcopy(chainable)
