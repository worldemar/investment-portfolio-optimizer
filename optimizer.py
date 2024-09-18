#!/usr/bin/env python3

import os
import sys
import argparse
import multiprocessing
import subprocess
import queue
import functools
import time
import modules.data_source as data_source
import modules.data_filter as data_filter
import modules.data_output as data_output
import importlib

import socket
import tempfile
import threading
from collections import deque
from typing import List
from itertools import chain, islice, tee
from modules.portfolio import Portfolio
from asset_colors import RGB_COLOR_MAP
from modules.convex_hull import LazyMultilayerConvexHull, ConvexHullPoint
from static_portfolios import STATIC_PORTFOLIOS

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s :: %(levelname)s :: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--asset-returns-csv', default='asset_returns.csv', help='path to csv with asset returns')
    parser.add_argument(
        '--precision', type=int, default=10,
        help='simulation precision, values less than 5 require A LOT of ram unless --hull is used')
    parser.add_argument(
        '--hull', type=int, default=0,
        help='use hull algorithm to draw only given layers'
             ' of edge portfolios, set to 0 to draw all portfolios')
    return parser.parse_args()

class DataStreamFinished:
    pass

def _report_errors_in_static_portfolios(portfolios: List[Portfolio], tickers_to_test: List[str]):
    logger = logging.getLogger(__name__)
    num_errors = 0
    for static_portfolio in STATIC_PORTFOLIOS:
        error = static_portfolio.asset_allocation_error(tickers_to_test)
        if error:
            num_errors += 1
            logger.error(f'Static portfolio {static_portfolio}\nhas invalid allocation: {error}')
    return num_errors


def allocation_to_coord_points(asset_allocation, market_data, coord_tuples: List[tuple[str,str]]):
    portfolio = Portfolio(asset_allocation)
    portfolio.simulate(market_data)
    points = data_filter.portfolio_coord_points(portfolio, coord_tuples)
    return points

def allocation_to_simulated(asset_allocation, market_data):
    portfolio = Portfolio(asset_allocation)
    portfolio.simulate(market_data)
    return portfolio

def allocation_to_simulated_q(
        market_data: dict[str, dict[str, float]] = None,
        source_queue: multiprocessing.Queue = None,
        sink_queue: multiprocessing.Queue = None):
    while True:
        asset_allocation = source_queue.get()
        if isinstance(asset_allocation, DataStreamFinished):
            sink_queue.put(DataStreamFinished())
            return
        portfolio = Portfolio(asset_allocation)
        portfolio.simulate(market_data)
        sink_queue.put(portfolio)

def simulated_q(
        assets: list = None,
        percentage_step: int = None,
        market_data: dict[str, dict[str, float]] = None,
        sink_queue: multiprocessing.Queue = None):
    logger = logging.getLogger(__name__)
    pool = multiprocessing.Pool(processes=4)
    simulated_portfolios = pool.imap(
        functools.partial(allocation_to_simulated, market_data=market_data),
        data_source.all_possible_allocations(assets, percentage_step),
        chunksize=10000
    )
    time_start = time.time()
    time_previous_report = time_start
    total_portfolios = 0
    send_buffer = []
    for portfolio in simulated_portfolios:
        send_buffer.append(portfolio)
        if len(send_buffer) >= 10000:
            sink_queue.put(send_buffer)
            send_buffer = []
        # sink_queue.send(portfolio.plot_tooltip_stats().encode('utf-8'))
        # sink_queue.send(b'123'*1000)
        total_portfolios += 1
        time_now = time.time()
        if time_now - time_previous_report > 5:
            time_previous_report = time_now
            logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time_now - time_start))}/s')
        # if time.time() - time_start > 30:
        #     break
    logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time_now - time_start))}/s')
    sink_queue.put(DataStreamFinished())

def plot_hull(
        coord_pair: tuple[str,str] = None,
        hull_layers: int = None,
        source_queue: multiprocessing.Queue = None):
    lmch = LazyMultilayerConvexHull(max_dirty_points=10000, layers=hull_layers)
    while True:
        simulated_portfolios = source_queue.get()
        if isinstance(simulated_portfolios, DataStreamFinished):
            break
        for simulated_portfolio in simulated_portfolios:
            point = data_filter.PortfolioXYFieldsPoint(simulated_portfolio, coord_pair[1], coord_pair[0])
            lmch(point)
    plot_data = data_filter.compose_plot_data(
            map(lambda x: x.portfolio, lmch.points()),
            field_x=coord_pair[1],
            field_y=coord_pair[0],
        )
    data_output.draw_circles_with_tooltips(
        circle_lines=plot_data,
        xlabel=coord_pair[1],
        ylabel=coord_pair[0],
        title=f'{coord_pair[0]} vs {coord_pair[1]}',
        directory='result',
        filename=f'{coord_pair[0]} - {coord_pair[1]}',
        asset_color_map=dict(RGB_COLOR_MAP),
    )


def all_possible_allocations_q(assets: list, percentage_step: int, percentages_ret: list = [], the_queue: multiprocessing.Queue = None):
    if percentages_ret and len(percentages_ret) == len(assets) - 1:
        the_queue.put(zip(assets, percentages_ret + [100 - sum(percentages_ret)]))
        return
    for asset_percent in range(0, 101 - sum(percentages_ret), percentage_step):
        added_percentages = percentages_ret + [asset_percent]
        all_possible_allocations_q(assets, percentage_step, added_percentages, the_queue)
    if len(percentages_ret) == 0:  # we are at top level
        the_queue.put(DataStreamFinished())


def queue_multiplexer(
        source_queue: multiprocessing.Queue,
        queues: list[multiprocessing.Queue]):
    while True:
        item = source_queue.get()
        if isinstance(item, DataStreamFinished):
            break
        for queue in queues:
            queue.put(item)
    for queue in queues:
        queue.put(DataStreamFinished())

def drain_queue(the_queue: multiprocessing.Queue):
    while True:
        if the_queue.qsize() <= 100:
            continue
        drained = False
        while not drained:
            try:
                the_queue.empty()
            except queue.Empty:
                drained = True
                break
        # item = the_queue.recv(1024)
        # if isinstance(item, DataStreamFinished):
        #     break

# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main(argv):
    process_wait_list = []
    logger = logging.getLogger(__name__)
    cmdline_args = _parse_args(argv)
    # process_pool = multiprocessing.Pool(processes=8)
    coords_tuples = [
        # Y, X
        ('CAGR(%)', 'Variance'),
        ('CAGR(%)', 'Stdev'),
        ('CAGR(%)', 'Sharpe'),
        ('Gain(x)', 'Variance'),
        ('Gain(x)', 'Stdev'),
        ('Gain(x)', 'Sharpe'),
        ('Sharpe', 'Stdev'),
        ('Sharpe', 'Variance'),
        ('Sharpe', 'Gain(x)'),
        ('Sharpe', 'CAGR(%)'),
    ]

    time_start = time.time()
    tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    num_errors = _report_errors_in_static_portfolios(portfolios=STATIC_PORTFOLIOS, tickers_to_test=tickers_to_test)
    if num_errors:
        logger.error(f'Found {num_errors} invalid static portfolios')
        return

    static_portfolios_simulated = deque(map(
        functools.partial(Portfolio.simulate, market_data=yearly_revenue_multiplier),
        STATIC_PORTFOLIOS,
    ),0)
    logger.info(f'{len(static_portfolios_simulated)} static portfolios will be plotted on all graphs')

    logger.info(f'+{time.time() - time_start:.2f}s :: simulating portfolios map...')
    portfolios_simulated_queue = multiprocessing.Queue(maxsize=5)
    # sock_sink, sock_source = socket.socketpair()
    process_wait_list.append(multiprocessing.Process(
        target=simulated_q,
        kwargs={
            'assets': tickers_to_test,
            'percentage_step': cmdline_args.precision,
            'market_data': yearly_revenue_multiplier,
            'sink_queue': portfolios_simulated_queue,
        }
    ))

    logger.info(f'+{time.time() - time_start:.2f}s :: simulated portfolios map ready')

    coord_tuple_queues = {
        coord_pair: multiprocessing.Queue(maxsize=10) for coord_pair in coords_tuples
    }
    process_wait_list.append(multiprocessing.Process(
        target=queue_multiplexer,
        kwargs={
            'source_queue': portfolios_simulated_queue,
            'queues': list(coord_tuple_queues.values()),
        }
    ))
    for coord_pair in coords_tuples:
        process_wait_list.append(multiprocessing.Process(
            target=plot_hull,
            kwargs={
                'source_queue': coord_tuple_queues[coord_pair],
                'coord_pair': coord_pair,
                'hull_layers': cmdline_args.hull,
            }
        ))

    deque(map(multiprocessing.Process.start, process_wait_list), 0)
    logger.info(f'+{time.time() - time_start:.2f}s :: all processes started')

    # portfolios_simulated_queue = multiprocessing.Queue(maxsize=1000)
    # portfolios_simulated_queue = queue.Queue(maxsize=1000)

    # threading.Thread(target=drain_queue, args=(portfolios_simulated_queue,)).start()

    # pool = multiprocessing.Pool(processes=8)
    # simulated_portfolios = pool.imap(
    #     functools.partial(allocation_to_simulated, market_data=yearly_revenue_multiplier),
    #     data_source.all_possible_allocations(tickers_to_test, cmdline_args.precision),
    #     chunksize=1000
    # )
    # time_start = time.time()
    # total_portfolios = 0
    # for portfolio in simulated_portfolios:
    #     portfolios_simulated_queue.put(portfolio)
    #     total_portfolios += 1
    #     if total_portfolios % 10000 == 0:
    #         logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time.time() - time_start))}/s')
    #     if time.time() - time_start > 10:
    #         break
    # logger.info(f'Simulated {total_portfolios} portfolios')
    # portfolios_simulated_queue.put(DataStreamFinished())

    deque(map(multiprocessing.Process.join, process_wait_list), 0)
    logger.info(f'+{time.time() - time_start:.2f}s :: all processes joined')
    sys.exit(0)

    # coord_tees = tee(portfolios_simulated, len(coords_tuples))
    # lmchs_list = [LazyMultilayerConvexHull(max_dirty_points=1000, layers=cmdline_args.hull) for coord_tuple in coords_tuples]
    # map_pairs = zip(lmchs_list, coord_tees)
    # lmch_processes = []
    # for lmch, portfolio_points_YX in map_pairs:
    #     lmch_processes.append(multiprocessing.Process(target=functools.partial(lmch.add_points, lmch, portfolio_points_YX)))
    # for lmch_process in lmch_processes:
    #     lmch_process.start()
    # for lmch_process in lmch_processes:
    #     lmch_process.join()

    lmchs = {
        coord_tuple : LazyMultilayerConvexHull(max_dirty_points=10000, layers=cmdline_args.hull) for coord_tuple in coords_tuples
    }
    for portfolio in portfolios_simulated:
        for coord_tuple in coords_tuples:
            field_x, field_y = coord_tuple
            lmchs[coord_tuple](data_filter.PortfolioXYFieldsPoint(portfolio, field_x, field_y))
    logger.info(f'+{time.time() - time_start:.2f}s :: hulls ready')

    portfolios_plot_data = {
        coord_tuple : None for coord_tuple in coords_tuples
    }
    for coord_tuple, lmch in lmchs.items():
        portfolios_plot_data[coord_tuple] = data_filter.compose_plot_data(
            chain(static_portfolios_simulated, map(lambda x: x.portfolio, lmch.points())),
            field_x=coord_tuple[1],
            field_y=coord_tuple[0],
        )
    logger.info(f'+{time.time() - time_start:.2f}s :: plot data ready')

    process_pool.map(
        data_output.draw_coord_tuple_plot_data,
        portfolios_plot_data.items(),
    )
    logger.info(f'+{time.time() - time_start:.2f}s :: graphs ready')


if __name__ == '__main__':
    main(sys.argv)
