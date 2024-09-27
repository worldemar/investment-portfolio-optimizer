#!/usr/bin/env python3

import importlib
import functools
from collections.abc import Iterable
import multiprocessing
from modules import data_types


class PortfolioXYFieldsPoint(data_types.ConvexHullPoint):
    def __new__(cls, portfolio: data_types.Portfolio, varname_x: str, varname_y: str):
        return super().__new__(cls, (portfolio.get_stat(varname_x), portfolio.get_stat(varname_y)))

    def __init__(self, portfolio: data_types.Portfolio, varname_x: str, varname_y: str):
        self._portfolio = portfolio
        self._varname_x = varname_x
        self._varname_y = varname_y

    def portfolio(self):
        return self._portfolio


def portfolios_xy_points(portfolios: Iterable[data_types.Portfolio], coord_pair: tuple[str, str]):
    xy_func = functools.partial(PortfolioXYFieldsPoint, varname_x=coord_pair[1], varname_y=coord_pair[0])
    return map(xy_func, portfolios)


def queue_multiplexer(
        source_queue: multiprocessing.Queue,
        queues: list[multiprocessing.Queue]):
    while True:
        item = source_queue.get()
        if isinstance(item, data_types.DataStreamFinished):
            break
        for queue in queues:
            queue.put(item)
    for queue in queues:
        queue.put(data_types.DataStreamFinished())


def multilayer_convex_hull(point_batch: list[data_types.ConvexHullPoint], layers: int = 1):
    pyhull_convex_hull = importlib.import_module('pyhull.convex_hull').ConvexHull
    hull_layers_points = []
    self_hull_points = list(point_batch)
    for _ in range(layers):
        if len(self_hull_points) == 0:
            break
        hull = pyhull_convex_hull(self_hull_points)
        hull_vertexes = set(vertex for hull_vertex in hull.vertices for vertex in hull_vertex)
        hull_points = list(self_hull_points[vertex] for vertex in hull_vertexes)
        if len(hull_points) > 0:
            for hull_point in hull_points:
                self_hull_points.remove(hull_point)
                hull_layers_points.append(hull_point)
        else:
            hull_layers_points.extend(self_hull_points)
    return hull_layers_points
