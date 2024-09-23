#!/usr/bin/env python3

import importlib


class ConvexHullPoint:
    def __init__(self):
        pass

    def x(self):  # pylint: disable=invalid-name
        return None

    def y(self):  # pylint: disable=invalid-name
        return None


class LazyMultilayerConvexHull():
    def __init__(self, max_dirty_points: int = 100, layers: int = 1):
        self._pyhull_convex_hull = importlib.import_module('pyhull.convex_hull').ConvexHull
        self._dirty_points = 0
        self._layers = layers
        self._max_dirty_points = max_dirty_points
        self._hull_layers = [[] for _ in range(layers)]

    def points(self):
        if self._dirty_points > 0:
            self._reconvex_hull()
        return [point for layer in self._hull_layers for point in layer]

    def hull_layers(self):
        if self._dirty_points > 0:
            self._reconvex_hull()
        return self._hull_layers

    def __call__(self, point: ConvexHullPoint):
        assert point is not None
        self._hull_layers[0].append(point)
        self._dirty_points += 1
        if self._dirty_points > self._max_dirty_points:
            self._reconvex_hull()
        return self

    def _reconvex_hull(self):
        self_hull_points = [point for layer in self._hull_layers for point in layer]
        for layer in range(self._layers):
            points_for_hull = [[point.x(), point.y()] for point in self_hull_points]
            hull = self._pyhull_convex_hull(points_for_hull)
            hull_vertexes = set(vertex for hull_vertex in hull.vertices for vertex in hull_vertex)
            hull_points = list(self_hull_points[vertex] for vertex in hull_vertexes)
            if hull_points != []:
                for hull_point in hull_points:
                    self_hull_points.remove(hull_point)
                self._hull_layers[layer] = hull_points
            else:
                self._hull_layers[layer] = self_hull_points
                self_hull_points = []
            if self_hull_points == []:
                break
        self._dirty_points = 0
