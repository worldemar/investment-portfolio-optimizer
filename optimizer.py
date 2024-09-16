#!/usr/bin/env python3

import sys
import argparse
import multiprocessing
import queue
import functools
import time
import modules.data_source as data_source
import modules.data_filter as data_filter
import modules.data_output as data_output

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

def allocation_to_simulated(asset_allocation, market_data, coord_tuples: List[tuple[str,str]]):
    portfolio = Portfolio(asset_allocation)
    portfolio.simulate(market_data)
    return portfolio


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main(argv):
    logger = logging.getLogger(__name__)

    cmdline_args = _parse_args(argv)

    time_start = time.time()

    process_pool = multiprocessing.Pool(processes=8)

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

    tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    num_errors = _report_errors_in_static_portfolios(portfolios=STATIC_PORTFOLIOS, tickers_to_test=tickers_to_test)
    if num_errors:
        logger.error(f'Found {num_errors} invalid static portfolios')
        return

    static_portfolios_simulated = list(map(
        functools.partial(Portfolio.simulate, market_data=yearly_revenue_multiplier),
        STATIC_PORTFOLIOS,
    ))
    logger.info(f'{len(static_portfolios_simulated)} static portfolios will be plotted on all graphs')

    possible_asset_allocations = islice(data_source.all_possible_allocations(tickers_to_test, cmdline_args.precision), 100000)

    logger.info(f'+{time.time() - time_start:.2f}s :: simulating portfolios map...')
    portfolios_simulated = process_pool.imap(
        functools.partial(allocation_to_simulated, market_data=yearly_revenue_multiplier, coord_tuples=coords_tuples),
        possible_asset_allocations,
        chunksize=64,
    )
    logger.info(f'+{time.time() - time_start:.2f}s :: simulated portfolios map ready')

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
