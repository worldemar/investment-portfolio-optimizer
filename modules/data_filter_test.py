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

import random
import functools
import itertools
import pytest
from modules import data_filter


class PointMock(tuple):
    def __new__(cls, x, y, payload):
        return super().__new__(cls, (x, y))

    # pylint: disable=unused-argument
    def __init__(self, x, y, payload):
        self.payload = payload


def mod_list(_list: list) -> list:
    return _list[:]


def mod_shuffle(_list: list) -> list:
    new_list = _list[:]
    random.shuffle(new_list)
    return new_list


def mod_reverse(_list: list) -> list:
    new_list = _list[:]
    new_list.reverse()
    return new_list


def mod_sort(_list: list) -> list:
    new_list = _list[:]
    new_list.sort()
    return new_list


def mod_sort_reverse(_list: list) -> list:
    new_list = _list[:]
    new_list.sort(reverse=True)
    return new_list


@pytest.mark.parametrize('modifier', [
    mod_list,
    mod_shuffle,
    mod_reverse,
    mod_sort,
    mod_sort_reverse
])
@pytest.mark.parametrize(
    "points, hull_layers",
    [
        [
            [[-1, 1], [1, 1], [1, -1], [-1, -1]],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
            ]
        ],
        [
            [[-1, 1], [1, 1], [1, -1], [-1, -1]],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [],
            ]
        ],
        [
            [[-1, 1], [1, 1], [1, -1], [-1, -1]],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [], [],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5]
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[0.5, 0.5]],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5]
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[0.5, 0.5], [0.5, -0.5]],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5]
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5]],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5]
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5]],
                [],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5], [-0.5, 0.5]
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[-0.5, -0.5], [-0.5, 0.5], [0.5, -0.5], [0.5, 0.5]],
                [],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5], [-0.5, 0.5],
                [0.3, 0.3]
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[-0.5, -0.5], [-0.5, 0.5], [0.5, -0.5], [0.5, 0.5]],
                [[0.3, 0.3]],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5], [-0.5, 0.5],
                [0.3, 0.3], [-0.3, -0.3],
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[-0.5, -0.5], [-0.5, 0.5], [0.5, -0.5], [0.5, 0.5]],
                [[0.3, 0.3], [-0.3, -0.3]],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5], [-0.5, 0.5],
                [0.3, 0.3], [-0.3, -0.3], [0.3, -0.3],
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[-0.5, -0.5], [-0.5, 0.5], [0.5, -0.5], [0.5, 0.5]],
                [[-0.3, -0.3], [0.3, -0.3], [0.3, 0.3]],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5], [-0.5, 0.5],
                [0.3, 0.3], [-0.3, -0.3], [0.3, -0.3], [-0.3, 0.3],
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [[-0.5, -0.5], [-0.5, 0.5], [0.5, -0.5], [0.5, 0.5]],
                [[-0.3, -0.3], [-0.3, 0.3], [0.3, -0.3], [0.3, 0.3]],
            ]
        ],
    ]
)
def test_multilayer_hull(points, hull_layers, modifier):
    points_shuffled = modifier(points)
    expected_points = [point for layer in hull_layers for point in layer]
    hull_points = data_filter.multilayer_convex_hull(points_shuffled, hull_layers=len(hull_layers))
    expected_points.sort()
    hull_points.sort()
    assert hull_points == expected_points


@pytest.mark.parametrize(
    "years, algorithm, expected_ranges",
    [
        [
            list(range(2000, 2021)),
            data_filter.years_first_to_last,
            [
                (2000, 2020),
            ]
        ],
        [
            list(range(2000, 2008)),
            functools.partial(data_filter.years_sliding_window, window_size=3),
            [
                (2000, 2003),
                (2001, 2004),
                (2002, 2005),
                (2003, 2006),
                (2004, 2007),
            ]
        ],
        [
            list(range(2000, 2011)),
            functools.partial(data_filter.years_sliding_window, window_size=10),
            [
                (2000, 2010),
            ]
        ],
        [
            list(range(2000, 2006)),
            functools.partial(data_filter.years_sliding_window, window_size=1),
            [
                (2000, 2001),
                (2001, 2002),
                (2002, 2003),
                (2003, 2004),
                (2004, 2005),
            ]
        ],
        [
            list(range(2000, 2007)),
            data_filter.years_all_to_last,
            [
                (2000, 2006),
                (2001, 2006),
                (2002, 2006),
                (2003, 2006),
                (2004, 2006),
                (2005, 2006),
            ]
        ],
        [
            list(range(2000, 2007)),
            data_filter.years_first_to_all,
            [
                (2000, 2001),
                (2000, 2002),
                (2000, 2003),
                (2000, 2004),
                (2000, 2005),
                (2000, 2006),
            ]
        ],
        [
            list(range(2000, 2007)),
            data_filter.years_all_to_all,
            list(filter(lambda r: r[1] > r[0], itertools.product(range(2000, 2007), repeat=2))),
        ]
    ]
)
def test_years_ranges(years, algorithm, expected_ranges):
    ranges = list(algorithm(years))
    assert ranges == expected_ranges
    # simulating one year range is generally useless, since stats like
    # variance, stddev and sharpe could not be determined from single data point
    for begin, end in ranges:
        assert begin != end
