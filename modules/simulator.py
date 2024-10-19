#!/usr/bin/env python3

import modules.data_source as data_types
from modules.data_source import all_possible_allocations, allocation_slice_simulate_and_feed_to_sink


import concurrent.futures
import logging
import multiprocessing.connection
import os
import time
from functools import partial


def simulator_process_func(
        assets: list = None,
        percentage_step: int = None,
        asset_revenue_per_year: dict[str, dict[str, float]] = None,
        sink: multiprocessing.connection.Connection = None,
        chunk_size: int = 1):
    logger = logging.getLogger(__name__)
    process_pool = concurrent.futures.ProcessPoolExecutor()
    thread_pool = concurrent.futures.ThreadPoolExecutor()

    possible_allocations_gen = all_possible_allocations(len(assets), percentage_step)
    total_possible_allocations = sum(1 for _ in possible_allocations_gen)

    time_start = time.time()
    allocations_per_core = total_possible_allocations // os.cpu_count() + 1
    slice_sender = partial(
        allocation_slice_simulate_and_feed_to_sink,
        slice_size=allocations_per_core,
        assets=assets,
        percentage_step=percentage_step,
        asset_revenue_per_year=asset_revenue_per_year,
        sink=sink,
        chunk_size=chunk_size)
    portfolios_sent_per_core = process_pool.map(slice_sender, range(0, os.cpu_count()))
    process_pool.shutdown()
    time_end = time.time()
    logger.info(f'Simulated {sum(portfolios_sent_per_core)} portfolios, rate: {int(total_possible_allocations / (time_end - time_start))}/s')
    sink.send(data_types.DataStreamFinished())