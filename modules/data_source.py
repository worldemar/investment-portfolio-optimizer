#!/usr/bin/env python3

import csv
import time
import config.asset_colors
from modules.data_types import Portfolio
import logging
import concurrent.futures
from functools import partial
import multiprocessing
import multiprocessing.connection
import modules.data_types as data_types
import itertools
import collections
from config.config import CHUNK_SIZE
import config
import pickle
import struct

def allocation_simulate(asset_allocation, assets, asset_revenue_per_year):
    portfolio = Portfolio(assets=assets, weights=asset_allocation)
    portfolio.simulate(asset_revenue_per_year)
    return portfolio

def allocation_simulate_serialize(asset_allocation, assets, asset_revenue_per_year):
    portfolio = Portfolio(assets=assets, weights=asset_allocation)
    portfolio.simulate(asset_revenue_per_year)
    return portfolio.serialize()

def all_possible_allocations(assets: list, step: int):
    def _allocations_recursive(
            assets: list, step: int,
            asset_idx: int = 0, asset_idx_max: int = 0,
            allocation: list[int] = (),
            allocation_sum: int = 0):
        if asset_idx == asset_idx_max:
            allocation[asset_idx] = 100 - allocation_sum
            yield allocation.copy() # dict(zip(assets, allocation))
            allocation[asset_idx] = 0
        else:
            for next_asset_percent in range(0, 100 - allocation_sum + 1, step):
                allocation[asset_idx] = next_asset_percent
                yield from _allocations_recursive(
                    assets, step,
                    asset_idx + 1, asset_idx_max,
                    allocation,
                    allocation_sum + next_asset_percent)
                allocation[asset_idx] = 0
    if 100 % step != 0:
        raise ValueError(f'cannot use step={step}, must be a divisor of 100')
    yield from _allocations_recursive(
        assets = assets, step = step,
        asset_idx = 0, asset_idx_max = len(assets) - 1,
        allocation = [0] * len(assets),
        allocation_sum = 0)

def sink_feeder(sink: multiprocessing.connection.Connection, data: bytes, count: int):
    data_stream_end_pickle = pickle.dumps(data_types.DataStreamFinished())
    for _ in range(count):
        sink.send_bytes(data)
    sink.send_bytes(data_stream_end_pickle)

def source_exhauster(source: multiprocessing.connection.Connection):
    data_stream_end_pickle = pickle.dumps(data_types.DataStreamFinished())
    while True:
        data = source.recv_bytes()
        if data == data_stream_end_pickle:
            break

def simulated_q(
        assets: list = None,
        percentage_step: int = None,
        asset_revenue_per_year: dict[str, dict[str, float]] = None,
        sink: multiprocessing.connection.Connection = None):
    logger = logging.getLogger(__name__)
    process_pool = multiprocessing.Pool()
    thread_pool = concurrent.futures.ThreadPoolExecutor()

    # allocation_limit = 10*1000*1000
    # allocation_limit = 1000*1000
    # allocation_limit = 100*1000
    # allocation_limit = 10*1000

    time_start = time.time()

    # possible_allocations_gen = itertools.islice(all_possible_allocations(assets, percentage_step), allocation_limit)
    possible_allocations_gen = all_possible_allocations(assets, percentage_step)
    total_portfolios = 0
    simulate_func = partial(allocation_simulate, assets=assets, asset_revenue_per_year=asset_revenue_per_year)
    simulate_serialize_func = partial(allocation_simulate_serialize, assets=assets, asset_revenue_per_year=asset_revenue_per_year)
    write_offset = 0
    write_future = None
    with concurrent.futures.ThreadPoolExecutor() as executor:
        with open('portfolios.dat', 'wb') as f:
            for possible_allocation_batch in itertools.batched(possible_allocations_gen, CHUNK_SIZE):
                
                # just simulation: 155k/s
                # simulated_portfolios_batch = process_pool.map(simulate_func, possible_allocation_batch)
                
                # simulate and serialize 180k/s (faster because of less data transfer from processes?)
                # simulated_portfolios_batch = process_pool.map(simulate_serialize_func, possible_allocation_batch)

                # simulate and struct-serialize 180k/s
                # simulated_portfolios_batch = process_pool.map(simulate_serialize_func, possible_allocation_batch)

                # simulate and struct-serialize and write 170k/s
                simulated_portfolios_batch = process_pool.map(simulate_serialize_func, possible_allocation_batch)
                # simbatch = struct.pack('s'*len(simulated_portfolios_batch), *simulated_portfolios_batch)
                # simbatch = b''.join(simulated_portfolios_batch)
                # if write_future is not None:
                #     write_future.result()
                # write_future = executor.submit(f.write, simbatch)
                # write_offset += len(simbatch)

                # simulate and struct-serialize and seek-write 160k/s
                    # def save_bytes(file=None, offset=0, data=None):
                    #     file.seek(offset)
                    #     file.write(data)
                    #     # file.flush() # does not make a difference
                # simulated_portfolios_batch = process_pool.map(simulate_serialize_func, possible_allocation_batch)
                # simbatch = struct.pack('s'*len(simulated_portfolios_batch), *simulated_portfolios_batch)
                # executor.submit(save_bytes, f, write_offset, simbatch)
                # write_offset += len(simbatch)

                # simulate and serialize with pickle: 129k/s
                # simulated_portfolios_batch = process_pool.map(simulate_func, possible_allocation_batch)
                # bytes = pickle.dumps(simulated_portfolios_batch)

                # bytes = pickle.dumps(simulated_portfolios_batch)
                # f.write(bytes)
                # sink.send_bytes(bytes)
                total_portfolios += len(possible_allocation_batch)
    thread_pool.shutdown()
    sink.send(data_types.DataStreamFinished())
    logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time.time() - time_start)//1000)}k/s')
    logger.info(f'Written {write_offset} bytes, rate: {int(write_offset / (time.time() - time_start)//1000)}k/s')


def read_capitalgain_csv_data(filename):
    yearly_revenue_multiplier = {}  # year, ticker = cash multiplier
    # read csv values from tickers.csv
    rows = []
    with open(filename, "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = list(csv_reader)
    assets = rows[0][1:]
    for row in rows[1:]:
        if row[0] not in yearly_revenue_multiplier:
            yearly_revenue_multiplier[int(row[0])] = [0] * len(assets)
        for i in range(1, len(row)):
            yearly_revenue_multiplier[int(row[0])][i - 1] = \
                float(row[i].replace('%', '')) / 100 + 1
    return assets, yearly_revenue_multiplier