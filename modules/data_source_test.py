#!/usr/bin/env python3

import itertools
import pytest
from modules import data_source

_divizors_of_100 = [1, 2, 4, 5, 10, 20, 25, 50, 100]


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
    test_allocations_gen = data_source.all_possible_allocations(assets_n, step)
    test_allocations = list(tuple(a) for a in test_allocations_gen)
    test_allocations.sort()
    # must be strictly equivalent to filtered product
    assert test_allocations == expected_allocations


def _expected_allocations(assets_n: int, step: int):
    gen_asset_values = filter(lambda x: sum(x) == 100, itertools.product(range(0, 101, step), repeat=assets_n))
    for asset_values in gen_asset_values:
        yield asset_values
