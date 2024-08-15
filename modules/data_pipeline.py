#!/usr/bin/env python3

from concurrent.futures import Executor
from typing import List, Iterable, Callable, Any


def chain_generators(
        executor: Executor, gens: List[Iterable[Any]], funcs: List[Callable[[Any], Any]]) -> Iterable[List[Any]]:
    for layer in zip(*gens):
        layer_values = [v for g in layer for v in g]
        next_layer = []
        for func in funcs:
            next_layer.append(executor.submit(func, *layer_values))
        next_layer_values = list(map(lambda r: r.result(), next_layer))
        yield next_layer_values
