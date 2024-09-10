#!/usr/bin/env python3

import sys
import argparse
import concurrent.futures
import functools
import time
import modules.data_source as data_source
import modules.data_filter as data_filter
import modules.data_output as data_output

from collections import deque
from typing import List
from itertools import chain, islice
from modules.portfolio import Portfolio
from asset_colors import RGB_COLOR_MAP
from modules.convex_hull import LazyMultilayerConvexHull, ConvexHullPoint
from static_portfolios import STATIC_PORTFOLIOS

import logging

logging.basicConfig(
    level=logging.DEBUG,
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


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main(argv):
    logger = logging.getLogger(__name__)

    cmdline_args = _parse_args(argv)
    process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=8)

    total_time = time.time()

    coords_tuples = [
        ('stat_var','stat_cagr'),
        ('stat_stdev','stat_gain'),
    ]

    tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data(cmdline_args.asset_returns_csv)
    # deque is the fastest way to exhaust generator
    num_errors = _report_errors_in_static_portfolios(portfolios=STATIC_PORTFOLIOS, tickers_to_test=tickers_to_test)
    if num_errors:
        logger.error(f'Found {num_errors} invalid static portfolios')
        return

    static_portfolios_simulated = map(
        functools.partial(Portfolio.simulate, market_data=yearly_revenue_multiplier),
        STATIC_PORTFOLIOS,
    )

    possible_asset_allocations = data_source.all_possible_allocations(tickers_to_test, cmdline_args.precision)
    possible_portfolios = map(Portfolio, possible_asset_allocations)
    portfolios = chain(STATIC_PORTFOLIOS, possible_portfolios)
    portfolios_simulated = process_executor.map(
        functools.partial(Portfolio.simulate, market_data=yearly_revenue_multiplier),
        portfolios,
        chunksize=1000,
    )

    portfolios_points_XY = map(
        functools.partial(data_filter.portfolio_XYpoints, list_of_point_coord_pairs=coords_tuples),
        portfolios_simulated,
    )

    lmchs = {
        coord_tuple : LazyMultilayerConvexHull(max_dirty_points=1000, layers=cmdline_args.hull) for coord_tuple in coords_tuples
    }
    for portfolio_points_XY in portfolios_points_XY:
        for coord_tuple in coords_tuples:
            lmchs[coord_tuple](portfolio_points_XY[coord_tuple])

    portfolios_plot_data = {
        coord_tuple : None for coord_tuple in coords_tuples
    }
    for coord_tuple, lmch in lmchs.items():
        portfolios_plot_data[coord_tuple] = data_filter.compose_plot_data(
            chain(static_portfolios_simulated, map(lambda x: x.portfolio, lmch.points())),
            field_x=coord_tuple[0],
            field_y=coord_tuple[1],
        )

    for coord_tuple, plot_data in portfolios_plot_data.items():
        data_output.draw_circles_with_tooltips(
            circle_lines=plot_data,
            xlabel=coord_tuple[0],
            ylabel=coord_tuple[1],
            title=f'{coord_tuple[0]} vs {coord_tuple[1]}',
            directory='result',
            filename=f'{coord_tuple[0]} vs {coord_tuple[1]}',
            asset_color_map=dict(RGB_COLOR_MAP),
        )

    total_time = time.time() - total_time
    logger.info(f'DONE :: {total_time:.2f}s')


if __name__ == '__main__':
    main(sys.argv)
