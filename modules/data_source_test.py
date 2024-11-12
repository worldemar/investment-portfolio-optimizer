#!/usr/bin/env python3

# Investment Portfolio Optimizer
# Copyright (C) 2024  Vladimir Looze

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import itertools
import pytest
from modules import data_source


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
    def _expected_allocations(assets_n: int, step: int):
        yield from filter(
            lambda x: sum(x) == 100,
            itertools.product(range(0, 101, step), repeat=assets_n))

    expected_allocations_gen = _expected_allocations(assets_n, step)
    expected_allocations = list(tuple(a) for a in expected_allocations_gen)
    expected_allocations.sort()
    test_allocations_gen = data_source.all_possible_allocations(assets_n, step)
    test_allocations = list(tuple(a) for a in test_allocations_gen)
    test_allocations.sort()
    # must be strictly equivalent to filtered product
    assert test_allocations == expected_allocations
