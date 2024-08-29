#!/usr/bin/env python3

import concurrent.futures
import pytest
from modules.convex_hull import LazyMultilayerConvexHull, ConvexHullPoint
from modules.data_pipeline import chain_generators


class PointMock(ConvexHullPoint):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y

    def __lt__(self, other):
        return [self._x, self._y] < [other._x, other._y]

    def __repr__(self):
        return f'[{self._x}, {self._y}]'


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
                [],
            ]
        ],
        [
            [
                [-1, 1], [1, 1], [1, -1], [-1, -1],
                [0.5, 0.5], [0.5, -0.5]
            ],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [],
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
                [],
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
                [],
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
class TestLazyMultilayerConvexHull:

    def test_convex_hull(self, points, hull_layers):
        lmch = LazyMultilayerConvexHull(max_dirty_points=3, layers=len(hull_layers))
        for point in points:
            lmch(PointMock(point[0], point[1]))
        for hull_layer_idx, expected_hull_layer in enumerate(hull_layers):
            lmch_layers = sorted(lmch(None)[hull_layer_idx])
            test_layers = sorted(expected_hull_layer)
            assert str(lmch_layers) == str(test_layers)

    def test_convex_hull_pipeline(self, points, hull_layers):
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        lmch = LazyMultilayerConvexHull(max_dirty_points=3, layers=len(hull_layers))
        result1 = chain_generators(executor, [points], [PointMock])
        result2 = chain_generators(executor, [result1], [lmch])
        result_list = list(result2)
        lmch_layer = result_list[0]
        lmch_result = lmch_layer[0]
        for hull_layer_idx, expected_hull_layer in enumerate(hull_layers):
            lmch_layers = sorted(lmch_result[hull_layer_idx])
            test_layers = sorted(expected_hull_layer)
            assert str(lmch_layers) == str(test_layers)
