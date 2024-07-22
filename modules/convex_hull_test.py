#!/usr/bin/env python3

from modules.convex_hull import *
from scipy.spatial import ConvexHull
import math
import pytest

def _compare_convex_hull_points_to_zero_layer(incremental_hull, scipy_hull):
    def _str_point(p: Point):
        return f'({p.x():.3f},{p.y():.3f})'
    def _str_vertex(v: list[float]):
        return f'({v[0]:.3f},{v[1]:.3f})'
    ich_points = incremental_hull.hull_points()[0]
    ch_points = scipy_hull.points[scipy_hull.vertices]
    assert(len(ich_points) == len(ch_points))
    ich_points = ' '.join(_str_point(i) for i in sorted(ich_points, key=lambda i: _str_point(i)))
    ch_points = ' '.join(_str_vertex(i) for i in sorted(ch_points, key=lambda i: _str_vertex(i)))
    assert(ich_points == ch_points)

@pytest.mark.parametrize(
    "name, points",
    [
        ['square', [[-1, 1], [1, 1], [1, -1], [-1, -1]]],
        ['diamond', [[-1, 0], [0, 1], [1, 0], [0, -1]]],
     ],
)
def test_IncrementalConvexHull_add_one_point_to_layer(name, points):
    class PointMock(Point):
        def __init__(self, x, y):
            self._x = x
            self._y = y
        def x(self):
            return self._x
        def y(self):
            return self._y
    N = 1024
    for i in range(N):
        ich = LazyMultilayerConvexHull(points=[PointMock(x,y) for x,y in points], max_dirty_points=100, layers=1)
        ch = ConvexHull(points=points, incremental=True)
        _compare_convex_hull_points_to_zero_layer(ich, ch)

        x = 0.75 * math.cos(i * 2 * math.pi / N)
        y = 0.75 * math.sin(i * 2 * math.pi / N)
        ich.add_point(PointMock(x, y))
        ch.add_points([[x, y]])
        _compare_convex_hull_points_to_zero_layer(ich, ch)

@pytest.mark.parametrize(
    "points, layers",
    [
        [
            [[-1, 1], [1, 1], [1, -1], [-1, -1]],
            [
                [[-1, -1], [-1, 1], [1, -1], [1, 1]],
                [],
            ]
        ]
    ]
)
def test_IncrementalConvexHull_add_one_point(points, layers):
    class PointMock(Point):
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
    lmch = LazyMultilayerConvexHull(max_dirty_points=100, layers=len(layers))
    for p in points:
        lmch.add_point(PointMock(p[0], p[1]))
    for l in range(len(layers)):
        lmch_layers = sorted(lmch.hull_points()[l])
        test_layers = sorted(layers[l])
        assert(str(lmch_layers) == str(test_layers))


