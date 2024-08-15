#!/usr/bin/env python3

def chain_generators(executor, gens, funcs):
    for layer in zip(*gens):
        layer_values = [v for g in layer for v in g]
        next_layer = []
        for f in funcs:
            next_layer.append(executor.submit(f, *layer_values))
        next_layer_values = list(map(lambda r: r.result(), next_layer))
        yield next_layer_values
