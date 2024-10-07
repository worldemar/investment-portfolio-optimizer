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
from typing import Callable
import itertools

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

def multigon_filter(xy_point_batch: list, depth: int = 1, sparse: int = 0, gons: int = 64):
    xs = list(point.x for point in xy_point_batch)
    xscale = max(xs) - min(xs)
    ys = list(point.y for point in xy_point_batch)
    yscale = max(ys) - min(ys)
    selected_points = []
    for o in xy_point_batch:
        o.x = o.x / xscale
        o.y = o.y / yscale
    for i in range(0,gons,2):  # half of the gons since we use top and bottom of sorted list
        rads = math.pi*i/gons
        _x = math.cos(rads)
        _y = math.sin(rads)
        xy_point_batch.sort(key = lambda point: point.x * _x + point.y * _y)
        selected_points.extend(xy_point_batch[:depth])
        selected_points.extend(xy_point_batch[-depth:])

    if sparse > 0:
        xy_point_batch.sort(key=lambda o: o.x)
        selected_points.extend(xy_point_batch[::int(len(xy_point_batch)/sparse)])
        xy_point_batch.sort(key=lambda o: o.y)
        selected_points.extend(xy_point_batch[::int(len(xy_point_batch)/sparse)])

    return list(set(selected_points))


def top_n_filter_1(items: list, n: int, predicate: Callable):
    return sorted(items, key=predicate, reverse=True)[:n]

def top_n_filter_2(items: list, n: int, predicate: Callable):
    top = []
    for _ in range(n):
        top.append(max(items, key=predicate))
        items.remove(top[-1])
    return top

def top_n_filter_3(items: list, n: int, predicate: Callable):
    top = []
    topmin = min(items, key=predicate)
    top.append(topmin)
    for item in items:
        if item >= topmin:
            top.append(item)
        if len(top) > n:
            top.remove(topmin)
            topmin = min(top, key=predicate)
    return top

def top_n_filter_4(items: list, n: int, predicate: Callable):
    '''
    faster equivalent of
    sorted(items, key=predicate, reverse=True)[:n]
    '''
    top = []
    top = items[:n]
    topmin = min(top, key=predicate)
    for item in items[n:]:
        if predicate(item) >= topmin:
            top.append(item)
        if len(top) > n:
            top.remove(topmin)
            topmin = min(top, key=predicate)
    return top

def top_n_filter_5(items: list, n: int, predicate: Callable):
    top = []
    top = items[:n]
    topmin = min(top, key=predicate)
    for item_idx in range(n, len(items)):
        if predicate(items[item_idx]) >= topmin:
            top.append(items[item_idx])
        if len(top) > n:
            top.remove(topmin)
            topmin = min(top, key=predicate)
    return top

def convex_hull_filter_(xy_point_batch: list):
    '''
    this function calculates convex hull of the points and returns the points that are part of the hull.
    this function does not use any external libraries to save memory.
    '''
    def angle(point1, point2):
        return math.atan2(point1.y - point2.y, point1.x - point2.x)
    hull_points = []
    leftmost_point = min(xy_point_batch, key=lambda o: o.x)
    hull_points.append(leftmost_point)
    second_point = max(xy_point_batch, key=lambda point: angle(leftmost_point, point))
    hull_points.append(second_point)
    while True:
        current_direction = angle(hull_points[-2], hull_points[-1])
        next_point_closest_to_direction = min(xy_point_batch, key=lambda point: angle(hull_points[-1], point) - current_direction)
        if next_point_closest_to_direction in hull_points:
            break
        hull_points.append(next_point_closest_to_direction)
    return hull_points

def convex_hull_filter1(xy_point_batch: list):
    def points_orientation(point1, point2, point3):
        val = (point2.y - point1.y) * (point3.x - point2.x) - (point2.x - point1.x) * (point3.y - point2.y)
        if val == 0:
            # collinear
            return 0
        elif val > 0:
            # counterclockwise
            return 1
        else:
            # clockwise
            return 2
    def convexHull(points, n):
        if n < 3:
            return
        l = min(range(n), key = lambda i: points[i].x)
        p = l
        q = 0
        hull = []
        while True:
            hull.append(points[p])
            q = (p + 1) % n
            for r in range(n):
                if (points_orientation(points[p], points[q], points[r]) == 2):
                    q = r
            p = q
            if (p == l):
                break
        return hull
    return convexHull(xy_point_batch, len(xy_point_batch))

def convex_hull(points: list[PortfolioXYPoint]):
    points_n = len(points)
    if points_n <= 3:
        return points
    leftmost_point_idx = min(range(points_n), key = lambda i: points[i].x)
    point_1_index = leftmost_point_idx
    point_2_index = 0
    hull_points = []
    while True:
        hull_points.append(points[point_1_index])
        point_2_index = (point_1_index + 1) % points_n
        for point_3_index in range(points_n):
            point_1 = points[point_1_index]
            point_2 = points[point_2_index]
            point_3 = points[point_3_index]
            cross_product = (point_2.y - point_1.y) * (point_3.x - point_2.x) - (point_2.x - point_1.x) * (point_3.y - point_2.y)
            if (cross_product < 0):
                point_2_index = point_3_index
        point_1_index = point_2_index
        if (point_1_index == leftmost_point_idx):
            break
    return hull_points

def multiprocess_convex_hull(pool, xy_point_batch: list[PortfolioXYPoint]):
    batches = itertools.batched(xy_point_batch, len(xy_point_batch)//multiprocessing.cpu_count() + 1)
    mapped = pool.imap(convex_hull, batches)
    return convex_hull([point for batch in mapped for point in batch])