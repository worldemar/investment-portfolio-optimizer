#!/usr/bin/env python3

import importlib
import functools
from collections.abc import Iterable
import concurrent.futures
import multiprocessing
import multiprocessing.connection
from modules import data_types
import pickle

import modules.Portfolio
import modules.data_source

class PortfolioXYFieldsPoint(tuple):
    def __new__(cls, portfolio: modules.Portfolio.Portfolio, varname_x: str = None, varname_y: str = None):
        try:
            if varname_x is None or varname_y is None:
                return super().__new__(cls, (0,0))
            return super().__new__(cls, (portfolio.get_stat(varname_x), portfolio.get_stat(varname_y)))
        except Exception as e:
            print(f'PortfolioXYFieldsPoint > {e}')
            return None

    def __init__(self, portfolio: modules.Portfolio.Portfolio, varname_x: str = None, varname_y: str = None):
        self._portfolio = portfolio
        self._varname_x = varname_x
        self._varname_y = varname_y

    def portfolio(self):
        return self._portfolio

def portfolios_xy_points(portfolios: Iterable[modules.Portfolio.Portfolio], coord_pair: tuple[str, str]):
    xy_func = functools.partial(PortfolioXYFieldsPoint, varname_x=coord_pair[1], varname_y=coord_pair[0])
    return map(xy_func, portfolios)

def queue_multiplexer(
        source: multiprocessing.connection.Connection,
        sinks: list[multiprocessing.connection.Connection]):
    data_stream_end_pickle = pickle.dumps(modules.data_source.DataStreamFinished())
    def send_task(sink, bytes, pool):
        return pool.submit(sink.send_bytes, bytes)
    with concurrent.futures.ThreadPoolExecutor() as thread_pool:
        while True:
            bytes = source.recv_bytes()
            if bytes == data_stream_end_pickle:
                break # make sure all threads are finished before sending the end signal
            send_tasks = map(functools.partial(send_task, pool=thread_pool, bytes=bytes), sinks)
            concurrent.futures.wait(send_tasks)
    for sink in sinks:
        sink.send_bytes(bytes)


def multilayer_convex_hull(point_batch: list, layers: int = 1):
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
