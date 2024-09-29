#!/usr/bin/env python3

import csv
import time
from modules.data_types import Portfolio
import logging
import concurrent.futures
from functools import partial
from multiprocessing import Queue as MultiprocessingQueue, Pool as MultiprocessingPool
import modules.data_types as data_types
import itertools
import collections
from config.config import CHUNK_SIZE

def allocation_to_simulated(asset_allocation, market_data):
    portfolio = Portfolio(asset_allocation)
    portfolio.simulate(market_data)
    return portfolio

def all_possible_allocations(assets: list, step: int):
    def _allocations_recursive(
            assets: list, step: int,
            asset_idx: int = 0, asset_idx_max: int = 0,
            portfolio: dict[str, int] = {},
            portfolio_values_sum: int = 0):
        asset_name = assets[asset_idx]
        if asset_idx == asset_idx_max:
            portfolio[asset_name] = 100 - portfolio_values_sum
            yield portfolio
            portfolio[asset_name] = 0
        else:
            for next_asset_percent in range(0, 100 - portfolio_values_sum + 1, step):
                portfolio[asset_name] = next_asset_percent
                yield from _allocations_recursive(
                    assets, step,
                    asset_idx + 1, asset_idx_max,
                    portfolio,
                    portfolio_values_sum + next_asset_percent)
                portfolio[asset_name] = 0
    if 100 % step != 0:
        raise ValueError(f'cannot use step={step}, must be a divisor of 100')
    yield from _allocations_recursive(
        assets = assets, step = step,
        asset_idx = 0, asset_idx_max = len(assets) - 1,
        portfolio = {a:0 for a in assets},
        portfolio_values_sum = 0)

def simulated_q(
        assets: list = None,
        percentage_step: int = None,
        market_data: dict[str, dict[str, float]] = None,
        sink_queue: MultiprocessingQueue = None):
    logger = logging.getLogger(__name__)
    with MultiprocessingPool() as process_pool, concurrent.futures.ThreadPoolExecutor() as thread_pool:
        # total_portfolios = 10*1000*1000
        total_portfolios = 1000*1000
        # total_portfolios = 100*1000
        # total_portfolios = 10*1000
        simulated_portfolios = itertools.islice(process_pool.imap(
            partial(allocation_to_simulated, market_data=market_data),
            all_possible_allocations(assets, percentage_step),
            chunksize=CHUNK_SIZE,
        ), total_portfolios)
        time_start = time.time()

        # ~100k/s
        collections.deque(simulated_portfolios, maxlen=0)

        # 51000/s
        # collections.deque(map(partial(thread_pool.submit, sink_queue.put), itertools.batched(simulated_portfolios, CHUNK_SIZE)), maxlen=0)

        # 54602/s
        # collections.deque(map(sink_queue.put, itertools.batched(simulated_portfolios, CHUNK_SIZE)), maxlen=0)

        # 53366/s
        # for portfolio_batch in itertools.batched(simulated_portfolios, CHUNK_SIZE):
        #     thread_pool.submit(sink_queue.put, portfolio_batch)

        # 49947/s
        # for portfolio_batch in itertools.batched(simulated_portfolios, CHUNK_SIZE):
        #     sink_queue.put(portfolio_batch)

        # 49942/s
        # send_buffer = []
        # for portfolio in simulated_portfolios:
        #     send_buffer.append(portfolio)
        #     if len(send_buffer) >= CHUNK_SIZE:
        #         thread_pool.submit(sink_queue.put, send_buffer)
        #         send_buffer = []

        # 51823/s
        # send_buffer = []
        # for portfolio in simulated_portfolios:
        #     send_buffer.append(portfolio)
        #     if len(send_buffer) >= CHUNK_SIZE:
        #         sink_queue.put(send_buffer)
        #         send_buffer = []

        # 48709/s
        # time_start = time.time()
        # time_previous_report = time_start
        # total_portfolios = 0
        # send_buffer = []
        # for portfolio in simulated_portfolios:
        #     send_buffer.append(portfolio)
        #     total_portfolios += 1
        #     if len(send_buffer) >= CHUNK_SIZE:
        #         thread_pool.submit(sink_queue.put, send_buffer)
        #         send_buffer = []
        #     time_now = time.time()
        #     if time_now - time_previous_report > 5:
        #         time_previous_report = time_now
        #         logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time_now - time_start))}/s')
    sink_queue.put(data_types.DataStreamFinished())
    logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time.time() - time_start))}/s')


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