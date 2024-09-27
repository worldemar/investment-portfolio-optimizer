#!/usr/bin/env python3

import random
import time
import os
import psutil
import importlib
from modules.convex_hull import LazyMultilayerConvexHull, ConvexHullPoint, batched_multilayer_convex_hull, multilayer_convex_hull

class PointMock(ConvexHullPoint):
    def __new__(cls, x, y, payload):
        return super().__new__(cls, (x, y))

    def __init__(self, x, y, payload):
        self.payload = payload

def main():
    pyhull_convex_hull = importlib.import_module('pyhull.convex_hull').ConvexHull

    timestamp_points_start = time.time()
    N = 1000*1000
    random_points = [PointMock(random.random(), random.random(), n) for n in range(N)]
    timestamp_points_end = time.time()
    print(f'generating {N} points :: {timestamp_points_end - timestamp_points_start:.2f}s ')
    base_used_ram = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    print(f'used ram: {base_used_ram:.2f} MB')

    timestamp_qhull_start = time.time()
    qhull = pyhull_convex_hull(random_points)
    qhull_vertexes = set(vertex for hull_vertex in qhull.vertices for vertex in hull_vertex)
    qhull_points = list(random_points[vertex] for vertex in qhull_vertexes)
    timestamp_qhull_end = time.time()
    print(f'qhull 3x :: {(timestamp_qhull_end - timestamp_qhull_start)*3:.2f}s ')
    qhull_points.sort()

    LAYERS = 3
    BATCH=1000000

    random_points = (PointMock(random.random(), random.random(), n) for n in range(N))
    base_used_ram = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    timestamp_mhull_start = time.time()
    mhull_points, max_used_ram = multilayer_convex_hull(random_points, layers=LAYERS)
    timestamp_mhull_end = time.time()
    print(f'mhull :: {timestamp_mhull_end - timestamp_mhull_start:.2f}s {max_used_ram-base_used_ram:.2f} MB')
    mhull_points.sort()

    random_points = (PointMock(random.random(), random.random(), n) for n in range(N))
    base_used_ram = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    timestamp_bhull_start = time.time()
    bhull_points, max_used_ram = batched_multilayer_convex_hull(random_points, batch_size=BATCH, layers=LAYERS)
    timestamp_bhull_end = time.time()
    print(f'bhull :: {timestamp_bhull_end - timestamp_bhull_start:.2f}s {max_used_ram-base_used_ram:.2f} MB')
    bhull_points.sort()

    # assert bhull_points == mhull_points

    random_points = (PointMock(random.random(), random.random(), n) for n in range(N))
    base_used_ram = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    lmch = LazyMultilayerConvexHull(max_dirty_points=BATCH, layers=LAYERS)
    timestamp_points_lmch_start = time.time()
    for i in random_points:
        lmch(i)
    lmch_hull_points = lmch.points()
    timestamp_points_lmch_end = time.time()
    print(f'lmch :: {timestamp_points_lmch_end - timestamp_points_lmch_start:.2f}s {lmch.max_used_ram-base_used_ram:.2f} MB')
    lmch_hull_points.sort()

    # assert lmch_hull_points == bhull_points

def main2():
    pyhull_convex_hull = importlib.import_module('pyhull.convex_hull').ConvexHull
    REPEATS=10
    for N in range(10,20):
        random_points = [PointMock(random.random(), random.random(), n) for n in range(2**N)]
        unsorted_start = time.time()
        for r in range(REPEATS):
            unsorted_hull = pyhull_convex_hull(random_points)
        unsorted_end = time.time()
        unsorted_batch_start = time.time()
        for r in range(REPEATS):
            sorted_hull = batched_multilayer_convex_hull(random_points, batch_size=100000)
        unsorted_batch_end = time.time()
        random_points.sort()
        sorted_start = time.time()
        for r in range(REPEATS):
            sorted_hull = pyhull_convex_hull(random_points)
        sorted_end = time.time()
        print(f'N={N} :: unsorted :: {(unsorted_end - unsorted_start)/REPEATS:.2f}s sorted :: {(sorted_end - sorted_start)/REPEATS:.2f}s :: batch :: {(unsorted_batch_end - unsorted_batch_start)/REPEATS:.2f}s')

if __name__ == '__main__':
    main2()
