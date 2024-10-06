#!/usr/bin/env python3

import math
import importlib
import functools
from collections.abc import Iterable
import concurrent.futures
import multiprocessing
import multiprocessing.connection
from modules import data_types
import pickle

class PortfolioXYFieldsPoint(data_types.ConvexHullPoint):
    def __new__(cls, portfolio: data_types.Portfolio, varname_x: str, varname_y: str):
        try:
            return super().__new__(cls, (portfolio.get_stat(varname_x), portfolio.get_stat(varname_y)))
        except Exception as e:
            print(f'PortfolioXYFieldsPoint > {e}')
            return None

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
        source: multiprocessing.connection.Connection,
        sinks: list[multiprocessing.connection.Connection]):
    data_stream_end_pickle = pickle.dumps(data_types.DataStreamFinished())
    with concurrent.futures.ThreadPoolExecutor() as thread_pool:
        while True:
            bytes = source.recv_bytes()
            if bytes == data_stream_end_pickle:
                break # make sure all threads are finished
            for sink in sinks:
                thread_pool.submit(sink.send_bytes, bytes)
    for sink in sinks:
        sink.send_bytes(bytes)



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

class PortfolioXYPoint():
    def __init__(self, portfolio: data_types.Portfolio, coord_pair: tuple[str, str]):
        self.portfolio = portfolio
        self.x = portfolio.stats[coord_pair[0]]
        self.y = portfolio.stats[coord_pair[1]]

def multigon_filter(portfolio_batch: list, coord_pair: tuple[str, str], depth: int = 1, sparse: int = 0, gons: int = 32):
    octagons = []
    for portfolio in portfolio_batch:
        octagons.append(PortfolioXYPoint(portfolio, coord_pair))
    selected_octagons = []
    xs = list(o.x for o in octagons)
    xscale = max(xs) - min(xs)
    ys = list(o.y for o in octagons)
    yscale = max(ys) - min(ys)
    for o in octagons:
        o.x = o.x / xscale
        o.y = o.y / yscale
    for i in range(gons):
        rads = math.pi*i/gons
        _x = math.cos(rads)
        _y = math.sin(rads)
        octagons.sort(key=lambda o: o.x*_x + o.y*_y)
        selected_octagons.extend(octagons[:depth])
        selected_octagons.extend(octagons[-depth:])

    if sparse > 0:
        octagons.sort(key=lambda o: o.x)
        selected_octagons.extend(octagons[::int(len(octagons)/sparse)])
        octagons.sort(key=lambda o: o.y)
        selected_octagons.extend(octagons[::int(len(octagons)/sparse)])

    portfolios = [octagon.portfolio for octagon in selected_octagons]
    return list(set(portfolios))
