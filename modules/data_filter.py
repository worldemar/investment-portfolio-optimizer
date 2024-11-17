#!/usr/bin/env python3

# Investment Portfolio Optimizer
# Copyright (C) 2024  Vladimir Looze

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pickle import dumps
from importlib import import_module
from multiprocessing.connection import Connection
from concurrent.futures import wait as futures_wait
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from modules.portfolio import Portfolio
from modules.data_source import DataStreamFinished


class PortfolioXYTuplePoint(tuple):
    def __new__(cls, portfolio: Portfolio, coord_pair: tuple[str, str]):
        return super().__new__(cls, (portfolio.stat[coord_pair[0]], portfolio.stat[coord_pair[1]]))

    def __init__(self, portfolio: Portfolio, coord_pair: tuple[str, str]):
        self._portfolio = portfolio
        self._coord_pair = coord_pair

    def portfolio(self):
        return self._portfolio


def multilayer_convex_hull(point_batch: list[PortfolioXYTuplePoint] = None, hull_layers: int = 1, edge_layers: int = 0):
    pyhull_convex_hull = import_module('pyhull.convex_hull').ConvexHull
    hull_layers_points = []
    self_hull_points = list(point_batch)
    if hull_layers > 0:
        for _ in range(hull_layers):
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
    else:
        hull_layers_points = self_hull_points
    if edge_layers > 0:
        points_on_edge = [point for point in self_hull_points if point.portfolio().number_of_assets() <= edge_layers]
    else:
        points_on_edge = []
    return hull_layers_points + points_on_edge


def queue_multiplexer(
        source: Connection,
        sinks: list[Connection]):

    def send_task(sink, data, pool):
        return pool.submit(sink.send_bytes, data)

    data_stream_end_pickle = dumps(DataStreamFinished())
    with ThreadPoolExecutor() as thread_pool:
        while True:
            bytes_from_pipe = source.recv_bytes()
            if bytes_from_pipe == data_stream_end_pickle:
                break  # make sure all threads are finished before sending the end signal
            send_tasks = map(partial(send_task, pool=thread_pool, data=bytes_from_pipe), sinks)
            futures_wait(send_tasks)
    for sink in sinks:
        sink.send_bytes(bytes_from_pipe)


def years_first_to_last(years: list):
    '''single range, first year to last year'''
    yield years[0], years[-1]


def years_first_to_all(years: list):
    '''from first year to all later years'''
    for i in range(1, len(years)):
        yield years[0], years[i]


def years_sliding_window(years: list, window_size: int):
    '''all possible ranges of specified N years'''
    for i in range(len(years) - window_size):
        yield years[i],years[i + window_size]


def years_all_to_last(years: list):
    '''all possible ranges ending at last year'''
    for i in range(len(years) - 1):
        yield years[i], years[-1]


def years_all_to_all(years: list):
    '''all possible year ranges (min 2 years)'''
    for idx_from in range(len(years) - 1):
        for idx_to in range(idx_from + 1, len(years)):
            yield years[idx_from], years[idx_to]
