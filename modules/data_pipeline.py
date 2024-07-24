#!/usr/bin/env python3

import concurrent.futures
from functools import partial

def generator_multiplex(gen, funcs):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for item in gen:
            item_results = []
            for f in funcs:
                item_results.append(executor.submit(f, item))
            yield list(map(lambda r: r.result(), item_results))
