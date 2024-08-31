#!/usr/bin/env python3

import enum
from concurrent.futures import Executor
from typing import List, Iterable, Callable, Any


class DelayedResultFunction:
    '''
    This function will be called multiple times until there is no more data from source generator.
    Then a None will be passed to it to indicate that it should return its result.
    '''

    def __copy__(self):
        pass  # pylint: disable=unnecessary-pass
        raise NotImplementedError()

    def __deepcopy__(self, _):
        pass  # pylint: disable=unnecessary-pass
        raise NotImplementedError()


class ParameterFormat(enum.Enum):
    'Describe how data from generators should be chained to functions'

    VALUE = enum.auto()
    'Each function is called with next value from corresponding generator as an argument.'

    ARGS = enum.auto()
    'Each function is called with all generators next values used as a tuple of arguments.'

    LIST = enum.auto()
    'Functions are called with all generators next values used as a single list argument.'


def chain_generators(
        executor: Executor,
        gens: List[Iterable[Any]],
        funcs: List[Callable[[Any], Any]],
        chain_type: ParameterFormat,
        ) -> Iterable[List[Any]]:

    # validate parameters
    if chain_type == ParameterFormat.VALUE:
        if len(funcs) != len(gens):
            raise ValueError(f'Number of generators and functions must be equal when using {chain_type} chaining')
    funcs_delayed = list(map(lambda fn: isinstance(fn, DelayedResultFunction), funcs))
    if any(funcs_delayed) != all(funcs_delayed):
        raise ValueError('All functions must be DelayedResultFunction or all of them must be not')

    # iterate over generators
    for layer in zip(*gens):
        layer_values = [v for g in layer for v in g]
        next_layer = []
        for idx, func in enumerate(funcs):
            match chain_type:
                case ParameterFormat.VALUE:
                    next_layer.append(executor.submit(func, layer_values[idx]))
                case ParameterFormat.ARGS:
                    next_layer.append(executor.submit(func, *layer_values))
                case ParameterFormat.LIST:
                    next_layer.append(executor.submit(func, layer_values))
                case _:
                    raise NotImplementedError("Unsupported chain type")
        next_layer_values = list(map(lambda r: r.result(), next_layer))
        if all(layer_value is None for layer_value in next_layer_values):
            continue
        yield next_layer_values

    # yield value layer for delayed functions
    if all(funcs_delayed):
        next_layer = []
        for func in funcs:
            next_layer.append(executor.submit(func, None))
        next_layer_values = list(map(lambda r: r.result(), next_layer))
        yield next_layer_values
