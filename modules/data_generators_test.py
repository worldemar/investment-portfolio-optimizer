#!/usr/bin/env python3

import pytest
import itertools
import modules.data_generators as data_generators

@pytest.mark.parametrize('assets_n, step',
    itertools.chain(
        itertools.product([1, 2, 3], [1, 2, 4, 5, 10, 20, 25, 50, 100]),
        itertools.product([4],          [2, 4, 5, 10, 20, 25, 50, 100]),
        itertools.product([5],             [4, 5, 10, 20, 25, 50, 100]),
        itertools.product([6, 7],                [10, 20, 25, 50, 100]),
        itertools.product([8, 9],                    [20, 25, 50, 100]),
        itertools.product([10],                          [25, 50, 100]),
    )
)
def test_all_possible_allocations(assets_n: int, step: int):
    expected_allocations_gen = _expected_allocations(assets_n, step)
    expected_allocations = list(tuple(a) for a in expected_allocations_gen)
    expected_allocations.sort()

    test_allocations_gen = data_generators.all_possible_allocations(assets_n, step)
    test_allocations = list(tuple(a) for a in test_allocations_gen)
    test_allocations.sort()

    assert test_allocations == expected_allocations


def _expected_allocations(assets_n: int, step: int):
    asset_values = filter(lambda x: sum(x) == 100, itertools.product(range(0,101,step), repeat=assets_n))
    for values in asset_values:
        yield values