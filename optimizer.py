#!/usr/bin/env python3

import sys
import argparse
import multiprocessing
import functools
import time
import modules.data_source as data_source
import modules.data_filter as data_filter
import modules.data_output as data_output
from collections import deque
from typing import List
from itertools import chain, islice, tee
from modules.data_types import Portfolio
from config.asset_colors import RGB_COLOR_MAP
from modules.convex_hull import LazyMultilayerConvexHull, ConvexHullPoint
from config.static_portfolios import STATIC_PORTFOLIOS
from modules.data_types import DataStreamFinished
from config.config import CHUNK_SIZE

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s :: %(levelname)s :: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--asset-returns-csv', default='config/asset_returns.csv', help='path to csv with asset returns')
    parser.add_argument(
        '--precision', type=int, default=10,
        help='simulation precision, values less than 5 require A LOT of ram unless --hull is used')
    parser.add_argument(
        '--hull', type=int, default=0,
        help='use hull algorithm to draw only given layers'
             ' of edge portfolios, set to 0 to draw all portfolios')
    return parser.parse_args()

def _report_errors_in_static_portfolios(portfolios: List[Portfolio], tickers_to_test: List[str]):
    logger = logging.getLogger(__name__)
    num_errors = 0
    for static_portfolio in STATIC_PORTFOLIOS:
        error = static_portfolio.asset_allocation_error(tickers_to_test)
        if error:
            num_errors += 1
            logger.error(f'Static portfolio {static_portfolio}\nhas invalid allocation: {error}')
    return num_errors

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
    if num_errors > 0:
        logger.error(f'Found {num_errors} invalid static portfolios')
        return
    if (not all(ticker in RGB_COLOR_MAP.keys() for ticker in tickers_to_test)):
        logger.error(f'Some tickers in {cmdline_args.asset_returns_csv} are not in RGB_COLOR_MAP: {set(tickers_to_test) - set(RGB_COLOR_MAP.keys())}')
        return

    static_portfolios_simulated = list(map(
        functools.partial(Portfolio.simulate, market_data=yearly_revenue_multiplier),
        STATIC_PORTFOLIOS))
    logger.info(f'{len(static_portfolios_simulated)} static portfolios will be plotted on all graphs')
    edge_portfolios_simulated = list(map(
        functools.partial(data_source.allocation_to_simulated, market_data=yearly_revenue_multiplier),
        data_source.all_possible_allocations(tickers_to_test, CHUNK_SIZE)))
    logger.info(f'{len(edge_portfolios_simulated)} edge portfolios will be plotted on all graphs')

    logger.info(f'+{time.time() - time_start:.2f}s :: preparing portfolio simulation data pipeline...')
    portfolios_simulated_queue = multiprocessing.Queue(maxsize=5)
    process_wait_list.append(multiprocessing.Process(
        target=data_source.simulated_q,
        kwargs={
            'assets': tickers_to_test,
            'percentage_step': cmdline_args.precision,
            'market_data': yearly_revenue_multiplier,
            'sink_queue': portfolios_simulated_queue,
        }
    ))

    coord_tuple_queues = {
        coord_pair: multiprocessing.Queue(maxsize=10) for coord_pair in coords_tuples
    }
    manager = multiprocessing.Manager()
    # plots_data = manager.dict()
    process_wait_list.append(multiprocessing.Process(
        target=data_filter.queue_multiplexer,
        kwargs={
            'source_queue': portfolios_simulated_queue,
            'queues': list(coord_tuple_queues.values()),
        }
    ))
    for coord_pair in coords_tuples:
        process_wait_list.append(multiprocessing.Process(
            target=data_output.plot_data,
            kwargs={
                'source_queue': coord_tuple_queues[coord_pair],
                # 'plots_data': plots_data,
                'persistent_portfolios': edge_portfolios_simulated + static_portfolios_simulated,
                'coord_pair': coord_pair,
                'hull_layers': cmdline_args.hull,
            }
        ))
    logger.info(f'+{time.time() - time_start:.2f}s :: data pipeline prepared')

    deque(map(multiprocessing.Process.start, process_wait_list), 0)
    logger.info(f'+{time.time() - time_start:.2f}s :: all processes started')

    deque(map(multiprocessing.Process.join, process_wait_list), 0)
    logger.info(f'+{time.time() - time_start:.2f}s :: graphs ready')


if __name__ == '__main__':
    main(sys.argv)
