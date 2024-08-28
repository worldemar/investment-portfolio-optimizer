#!/usr/bin/env python3

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


def chain_generators(
        executor: Executor, gens: List[Iterable[Any]], funcs: List[Callable[[Any], Any]]) -> Iterable[List[Any]]:
    for layer in zip(*gens):
        layer_values = [v for g in layer for v in g]
        next_layer = []
        for func in funcs:
            next_layer.append(executor.submit(func, *layer_values))
        next_layer_values = list(map(lambda r: r.result(), next_layer))
        if all(layer_value is None for layer_value in next_layer_values):
            continue
        yield next_layer_values
    if all(isinstance(funcs, DelayedResultFunction) for funcs in funcs):
        next_layer = []
        for func in funcs:
            next_layer.append(executor.submit(func, None))
        next_layer_values = list(map(lambda r: r.result(), next_layer))
        yield next_layer_values
