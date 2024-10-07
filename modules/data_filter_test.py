#!/usr/bin/env python3

import random
from typing import List
import pytest
import modules.data_types as data_types
import modules.data_filter as data_filter
import multiprocessing


class PointMock(data_types.ConvexHullPoint):
    def __new__(cls, x, y, payload):
        return super().__new__(cls, (x, y))

    def __init__(self, x, y, payload):
        self.payload = payload

class PortfolioXYPointMock:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __lt__(self, other):
        if self.x < other.x:
            return True
        elif self.x > other.x:
            return False
        else:
            return self.y < other.y
        

def mod_list(_list: List) -> List:
    return _list[:]


def mod_shuffle(_list: List) -> List:
    new_list = _list[:]
    random.shuffle(new_list)
    return new_list


def mod_reverse(_list: List) -> List:
    new_list = _list[:]
    new_list.reverse()
    return new_list


def mod_sort(_list: List) -> List:
    new_list = _list[:]
    new_list.sort()
    return new_list


def mod_sort_reverse(_list: List) -> List:
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
class TestConvexHullFilters:
    def test_multilayer_hull(self, points, hull_layers, modifier):
        points_shuffled = modifier(points)
        expected_points = [point for layer in hull_layers for point in layer]
        hull_points = data_filter.multilayer_convex_hull(points_shuffled, layers=len(hull_layers))
        expected_points.sort()
        hull_points.sort()
        assert hull_points == expected_points

    def test_convex_hull_filter(self, points, hull_layers, modifier):
        points_shuffled = modifier(points)
        expected_points = [point for point in hull_layers[0]]
        points_shuffled_xy = list(map(lambda point: PortfolioXYPointMock(point[0],point[1]), points_shuffled))
        hull_xy_points = data_filter.convex_hull_filter1(points_shuffled_xy)
        hull_points = list([point.x, point.y] for point in hull_xy_points)
        expected_points.sort()
        hull_points.sort()
        assert hull_points == expected_points

    def test_convex_hull(self, points, hull_layers, modifier):
        points_shuffled = modifier(points)
        expected_points = [point for point in hull_layers[0]]
        points_shuffled_xy = list(map(lambda point: PortfolioXYPointMock(point[0],point[1]), points_shuffled))
        hull_xy_points = data_filter.convex_hull(points_shuffled_xy)
        hull_points = list([point.x, point.y] for point in hull_xy_points)
        expected_points.sort()
        hull_points.sort()
        assert hull_points == expected_points

    def test_multiprocess_convex_hull(self, points, hull_layers, modifier):
        points_shuffled = modifier(points)
        expected_points = [point for point in hull_layers[0]]
        points_shuffled_xy = list(map(lambda point: PortfolioXYPointMock(point[0],point[1]), points_shuffled))
        with multiprocessing.Pool() as pool:
            hull_xy_points = data_filter.multiprocess_convex_hull(pool, points_shuffled_xy)
        hull_points = list([point.x, point.y] for point in hull_xy_points)
        expected_points.sort()
        hull_points.sort()
        assert hull_points == expected_points