#!/usr/bin/env python3

from scipy.spatial import ConvexHull
from modules.data_pipeline import DelayedResultFunction


class ConvexHullPoint:
    def __init__(self):
        pass

    def x(self):  # pylint: disable=invalid-name
        return None

    def y(self):  # pylint: disable=invalid-name
        return None


# pylint: disable=too-few-public-methods
class LazyMultilayerConvexHull(DelayedResultFunction):
    def __init__(self, max_dirty_points: int = 100, layers: int = 1):
        self._dirty_points = 0
        self._layers = layers
        self._max_dirty_points = max_dirty_points
        self._hull_layers = [[] for _ in range(layers)]

    def __call__(self, point: ConvexHullPoint):
        if point is None:
            if self._dirty_points > 0:
                self._reconvex_hull()
            return self._hull_layers
        self._hull_layers[0].append(point)
        self._dirty_points += 1
        if self._dirty_points > self._max_dirty_points:
            self._reconvex_hull()
        return None

    def _reconvex_hull(self):
        self_hull_points = [point for layer in self._hull_layers for point in layer]
        for layer in range(self._layers):
            if len(self_hull_points) >= 3:
                points_for_hull = [[point.x(), point.y()] for point in self_hull_points]
                hull = ConvexHull(points_for_hull, incremental=False)
                hull_points = [self_hull_points[hull_vertex] for hull_vertex in hull.vertices]
                for hull_point in hull_points:
                    self_hull_points.remove(hull_point)
                self._hull_layers[layer] = hull_points
            else:
                self._hull_layers[layer] = []
        self._dirty_points = 0