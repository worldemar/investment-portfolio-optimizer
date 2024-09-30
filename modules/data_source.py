#!/usr/bin/env python3

import csv
import time
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
import pickle

def allocation_simulate(asset_allocation, ticker_revenue_per_year):
    portfolio = Portfolio(asset_allocation)
    portfolio.simulate(ticker_revenue_per_year)
    return portfolio

def allocation_simulate_serialize(asset_allocation, ticker_revenue_per_year):
    portfolio = Portfolio(asset_allocation)
    portfolio.simulate(ticker_revenue_per_year)
    return portfolio.serialize()

def all_possible_allocations(assets: list, step: int):
    def _allocations_recursive(
            assets: list, step: int,
            asset_idx: int = 0, asset_idx_max: int = 0,
            allocation: dict[str, int] = {},
            allocation_sum: int = 0):
        asset_name = assets[asset_idx]
        if asset_idx == asset_idx_max:
            allocation[asset_name] = 100 - allocation_sum
            yield allocation.copy()
            allocation[asset_name] = 0
        else:
            for next_asset_percent in range(0, 100 - allocation_sum + 1, step):
                allocation[asset_name] = next_asset_percent
                yield from _allocations_recursive(
                    assets, step,
                    asset_idx + 1, asset_idx_max,
                    allocation,
                    allocation_sum + next_asset_percent)
                allocation[asset_name] = 0
    if 100 % step != 0:
        raise ValueError(f'cannot use step={step}, must be a divisor of 100')
    yield from _allocations_recursive(
        assets = assets, step = step,
        asset_idx = 0, asset_idx_max = len(assets) - 1,
        allocation = {a:0 for a in assets},
        allocation_sum = 0)

def simulated_q(
        assets: list = None,
        percentage_step: int = None,
        ticker_revenue_per_year: dict[str, dict[str, float]] = None,
        sink: multiprocessing.connection.Connection = None):
    logger = logging.getLogger(__name__)
    process_pool = multiprocessing.Pool()
    thread_pool = concurrent.futures.ThreadPoolExecutor()

    # allocation_limit = 10*1000*1000
    allocation_limit = 1000*1000
    # allocation_limit = 200*1000
    # allocation_limit = 10*1000

    time_start = time.time()

    possible_allocations_gen = itertools.islice(all_possible_allocations(assets, percentage_step), allocation_limit)
    simulate_func = partial(allocation_simulate_serialize, ticker_revenue_per_year=ticker_revenue_per_year)
    for possible_allocation_batch in itertools.batched(possible_allocations_gen, CHUNK_SIZE):
        simulated_portfolios_batch = process_pool.map(simulate_func, possible_allocation_batch)
        bytes = pickle.dumps(simulated_portfolios_batch)
        sink.send_bytes(bytes)
    thread_pool.shutdown()
    sink.send(data_types.DataStreamFinished())
    logger.info(f'Simulated {allocation_limit} portfolios, rate: {int(allocation_limit / (time.time() - time_start))}/s')


def read_capitalgain_csv_data(filename):
    yearly_revenue_multiplier = {}  # year, ticker = cash multiplier
    # read csv values from tickers.csv
    rows = []
    with open(filename, "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = list(csv_reader)
    tickers = rows[0][1:]
    for row in rows[1:]:
        if row[0] not in yearly_revenue_multiplier:
            yearly_revenue_multiplier[int(row[0])] = {}
        for i in range(1, len(row)):
            yearly_revenue_multiplier[int(row[0])][tickers[i - 1]] = \
                float(row[i].replace('%', '')) / 100 + 1
    return tickers, yearly_revenue_multiplier