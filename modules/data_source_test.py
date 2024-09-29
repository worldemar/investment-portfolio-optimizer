#!/usr/bin/env python3

import pytest
import itertools
import modules.data_source as data_source

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
    assets = list('abcdefghijkl'[i] for i in range(assets_n))

    expected_allocations_gen = _expected_allocations(assets, step)
    expected_allocations = list(tuple(i for i in a.items()) for a in expected_allocations_gen)
    expected_allocations.sort()

    test_allocations_gen = data_source.all_possible_allocations(assets, step)
    test_allocations = list(tuple(i for i in a.items()) for a in test_allocations_gen)
    test_allocations.sort()

    assert test_allocations == expected_allocations


def _expected_allocations(assets: list, step: int):
    asset_values = filter(lambda x: sum(x) == 100, itertools.product(range(0,101,step), repeat=len(assets)))
    for asset_values in asset_values:
        yield dict(zip(assets, asset_values))
