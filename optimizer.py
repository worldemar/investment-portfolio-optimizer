#!/usr/bin/env python3

import sys
import time
import argparse
import logging
from collections import deque
from functools import partial
from multiprocessing import Process
from multiprocessing import Pipe
from modules import data_output
from modules import data_source
from modules import data_filter
from modules.portfolio import Portfolio
from modules.plotter import plotter_process_func
from modules.simulator import simulator_process_func
from config.asset_colors import RGB_COLOR_MAP
from config.static_portfolios import STATIC_PORTFOLIOS
from config.config import CHUNK_SIZE


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s :: %(levelname)s :: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument(
        '--asset-returns-csv', default='config/asset_returns.csv',
        help='path to csv with asset returns')
    parser.add_argument(
        '--precision', type=int, default=10,
        help='simulation precision: plot portfolios that have assets allocated\n'
             'to multiple of this percentage')
    parser.add_argument(
        '--hull', type=int, default=0,
        help='filter portfolios: use hull algorithm to plot only given ConvexHull layers '
             'of portfolios in coordinate space. Set to 0 (default) to disable filter.')
    parser.add_argument(
        '--edge', type=int, default=0,
        help='filter portfolios: show edges of portfolio space '
             'by adding all portfolios that have up to N assets to plots. '
             'Set to 0 to disable filter (default). '
             'Set to 1 to see pure portfolios (100%% of one asset). '
             'Set to 2 to see edge lines connecting pure portfolios. ')
    return parser.parse_args()


# pylint: disable=too-many-locals
def main(argv):
    cmdline_args = _parse_args(argv)
    coords_tuples = [
        # Y, X
        (Portfolio.STAT_CAGR_PERCENT, Portfolio.STAT_VARIANCE),
        (Portfolio.STAT_CAGR_PERCENT, Portfolio.STAT_STDDEV),
        (Portfolio.STAT_CAGR_PERCENT, Portfolio.STAT_SHARPE),
        (Portfolio.STAT_GAIN, Portfolio.STAT_VARIANCE),
        (Portfolio.STAT_GAIN, Portfolio.STAT_STDDEV),
        (Portfolio.STAT_GAIN, Portfolio.STAT_SHARPE),
        (Portfolio.STAT_SHARPE, Portfolio.STAT_STDDEV),
        (Portfolio.STAT_SHARPE, Portfolio.STAT_VARIANCE),
    ]

    time_start = time.time()

    market_assets, market_yearly_gain = \
        data_source.read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    num_errors = data_output.report_errors_in_portfolios(
        portfolios=STATIC_PORTFOLIOS, tickers_to_test=market_assets, color_map=RGB_COLOR_MAP)
    if num_errors > 0:
        logging.error('Found %d invalid static portfolios', num_errors)
        return
    colored_assets = RGB_COLOR_MAP.keys()
    if not all(ticker in colored_assets for ticker in market_assets):
        logging.error('Some tickers in %s are not in RGB_COLOR_MAP: %s',
                      cmdline_args.asset_returns_csv, set(market_assets) - set(RGB_COLOR_MAP.keys()))
        return

    static_portfolios_aligned_to_market = list(map(
        partial(Portfolio.aligned_to_market, market_assets=market_assets),
        STATIC_PORTFOLIOS))
    static_portfolios_simulated = list(map(
        partial(Portfolio.simulated, asset_gain_per_year=market_yearly_gain),
        static_portfolios_aligned_to_market))
    logging.info('%d static portfolios will be plotted on all graphs', len(static_portfolios_simulated))

    process_wait_list = []

    logging.info('+%.2fs :: preparing portfolio simulation data pipeline...', time.time() - time_start)
    simulated_source, simulated_sink = Pipe(duplex=False)
    process_wait_list.append(Process(
        target=simulator_process_func,
        kwargs={
            'assets': market_assets,
            'percentage_step': cmdline_args.precision,
            'asset_gain_per_year': market_yearly_gain,
            'sink': simulated_sink,
            'chunk_size': CHUNK_SIZE,
        }
    ))
    coodr_pair_pipes = {
        coord_pair: dict(zip(('source', 'sink'), Pipe(duplex=False))) for coord_pair in coords_tuples
    }
    process_wait_list.append(Process(
        target=data_filter.queue_multiplexer,
        kwargs={
            'source': simulated_source,
            'sinks': list(pipe['sink'] for pipe in coodr_pair_pipes.values()),
        }
    ))
    for coord_pair in coords_tuples:
        process_wait_list.append(Process(
            target=plotter_process_func,
            kwargs={
                'assets': market_assets,
                'source': coodr_pair_pipes[coord_pair]['source'],
                'persistent_portfolios': static_portfolios_simulated,
                'coord_pair': coord_pair,
                'hull_layers': cmdline_args.hull,
                'edge_layers': cmdline_args.edge,
                'color_map': RGB_COLOR_MAP,
            }
        ))

    logging.info('+%.2fs :: data pipeline prepared', time.time() - time_start)

    deque(map(Process.start, process_wait_list), 0)
    logging.info('+%.2fs :: all processes started', time.time() - time_start)

    deque(map(Process.join, process_wait_list), 0)
    logging.info('+%.2fs :: graphs ready', time.time() - time_start)


if __name__ == '__main__':
    if sys.version_info <= (3, 12):
        logging.error('Python 3.12 or higher required')
        sys.exit(1)
    main(sys.argv)
