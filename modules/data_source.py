#!/usr/bin/env python3

import csv
import time
from modules.data_types import Portfolio
import logging
from functools import partial
from multiprocessing import Queue as MultiprocessingQueue, Pool as MultiprocessingPool
import modules.data_types as data_types
from config.config import CHUNK_SIZE

def allocation_to_simulated(asset_allocation, market_data):
    portfolio = Portfolio(asset_allocation)
    portfolio.simulate(market_data)
    return portfolio


def all_possible_allocations(assets: list, percentage_step: int, percentages_ret: list = []):
    if percentages_ret and len(percentages_ret) == len(assets) - 1:
        yield zip(assets, percentages_ret + [100 - sum(percentages_ret)])
        return
    for asset_percent in range(0, 101 - sum(percentages_ret), percentage_step):
        added_percentages = percentages_ret + [asset_percent]
        yield from all_possible_allocations(assets, percentage_step, added_percentages)


def simulated_q(
        assets: list = None,
        percentage_step: int = None,
        market_data: dict[str, dict[str, float]] = None,
        sink_queue: MultiprocessingQueue = None):
    logger = logging.getLogger(__name__)
    pool = MultiprocessingPool(processes=4)
    simulated_portfolios = pool.imap(
        partial(allocation_to_simulated, market_data=market_data),
        all_possible_allocations(assets, percentage_step),
        chunksize=CHUNK_SIZE,
    )
    time_start = time.time()
    time_previous_report = time_start
    total_portfolios = 0
    send_buffer = []
    for portfolio in simulated_portfolios:
        send_buffer.append(portfolio)
        total_portfolios += 1
        if len(send_buffer) >= CHUNK_SIZE:
            sink_queue.put(send_buffer)
            send_buffer = []
        time_now = time.time()
        if time_now - time_previous_report > 5:
            time_previous_report = time_now
            logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time_now - time_start))}/s')
    logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time_now - time_start))}/s')
    sink_queue.put(data_types.DataStreamFinished())

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