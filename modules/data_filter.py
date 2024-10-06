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


class OctagonCoordinates():
    def __init__(self, portfolio: data_types.Portfolio, coord_pair: tuple[str, str]):
        self.portfolio = portfolio
        self.x = portfolio.get_stat(coord_pair[0])
        self.y = portfolio.get_stat(coord_pair[1])

def multigon_filter(portfolio_batch: list, coord_pair: tuple[str, str]):
    octagons = []
    for portfolio in portfolio_batch:
       if isinstance(portfolio, OctagonCoordinates):
         octagons.append(portfolio)
       else:
         octagons.append(OctagonCoordinates(portfolio, coord_pair))
    selected_octagons = []
    depth = 5
    sparse = 100
    gons = 64
    xs = list(o.x for o in octagons)
    xscale = max(xs) - min(xs)
    ys = list(o.y for o in octagons)
    yscale = max(ys) - min(ys)
    for i in range(gons):
        _x = math.cos(2*math.pi*i/gons)
        _y = math.sin(2*math.pi*i/gons)
        octagons.sort(key=lambda o: o.x*_x/xscale + o.y*_y/yscale)
        selected_octagons.extend(octagons[:depth])
        selected_octagons.extend(octagons[-depth:])

    octagons.sort(key=lambda o: o.x)
    selected_octagons.extend(octagons[::int(len(octagons)/sparse)])
    octagons.sort(key=lambda o: o.y)
    selected_octagons.extend(octagons[::int(len(octagons)/sparse)])

    portfolios = [octagon.portfolio for octagon in selected_octagons]
    return list(set(portfolios))
