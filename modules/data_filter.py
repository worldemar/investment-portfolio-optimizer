#!/usr/bin/env python3

from pickle import dumps
from importlib import import_module
from multiprocessing.connection import Connection
from modules.Portfolio import Portfolio
from modules.data_source import DataStreamFinished
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait as futures_wait
from functools import partial
from config.asset_colors import RGB_COLOR_MAP


class PortfolioXYTuplePoint(tuple):
    def __new__(cls, portfolio: Portfolio, coord_pair: tuple[str, str]):
        return super().__new__(cls, (portfolio.get_stat(coord_pair[0]), portfolio.get_stat(coord_pair[1])))

    def __init__(self, portfolio: Portfolio, coord_pair: tuple[str, str]):
        self._portfolio = portfolio
        self._coord_pair = coord_pair
    
    def portfolio(self):
        return self._portfolio


def multilayer_convex_hull(point_batch: list[PortfolioXYTuplePoint] = None, layers: int = 1):
    pyhull_convex_hull = import_module('pyhull.convex_hull').ConvexHull
    hull_layers_points = []
    self_hull_points = list(point_batch)
    for _ in range(layers):
        if len(self_hull_points) <= 3:
            hull_layers_points.extend(self_hull_points)
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


def queue_multiplexer(
        source: Connection,
        sinks: list[Connection]):
    data_stream_end_pickle = dumps(DataStreamFinished())
    def send_task(sink, bytes, pool):
        return pool.submit(sink.send_bytes, bytes)
    with ThreadPoolExecutor() as thread_pool:
        while True:
            bytes = source.recv_bytes()
            if bytes == data_stream_end_pickle:
                break # make sure all threads are finished before sending the end signal
            send_tasks = map(partial(send_task, pool=thread_pool, bytes=bytes), sinks)
            futures_wait(send_tasks)
    for sink in sinks:
        sink.send_bytes(bytes)