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

import os
import time
import logging
from functools import partial
import multiprocessing.connection
from concurrent.futures import ProcessPoolExecutor
from modules import data_source


def simulator_process_func(
        assets: list = None,
        percentage_step: int = None,
        year_range_selector_func = None,
        asset_gain_per_year: dict[str, dict[str, float]] = None,
        sink: multiprocessing.connection.Connection = None,
        chunk_size: int = 1):
    possible_allocations_gen = data_source.all_possible_allocations(len(assets), percentage_step)
    possible_allocations = sum(1 for _ in possible_allocations_gen)
    logging.info('Will simulate %d portfolios', possible_allocations)
    time_start = time.time()
    with ProcessPoolExecutor() as process_pool:
        allocations_per_core = possible_allocations // os.cpu_count() + 1
        slice_sender = partial(
            data_source.allocation_slice_simulate_and_feed_to_sink,
            slice_size=allocations_per_core,
            assets=assets,
            percentage_step=percentage_step,
            year_range_selector_func=year_range_selector_func,
            asset_gain_per_year=asset_gain_per_year,
            sink=sink,
            chunk_size=chunk_size)
        portfolios_sent_per_core = process_pool.map(slice_sender, range(0, os.cpu_count()))
    time_end = time.time()
    logging.info('Simulated %d portfolios, rate: %dk/s',
                 sum(portfolios_sent_per_core), possible_allocations // (int(time_end - time_start) + 1) // 1000)
    sink.send(data_source.DataStreamFinished())
