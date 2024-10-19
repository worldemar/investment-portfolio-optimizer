#!/usr/bin/env python3

import sys
import time
import argparse
import logging
from collections import deque
from functools import partial
from multiprocessing import Process
from multiprocessing import Pipe
import modules.data_output as data_output
import modules.data_source as data_source
import modules.data_filter as data_filter
from modules.Portfolio import Portfolio
from config.asset_colors import RGB_COLOR_MAP
from config.static_portfolios import STATIC_PORTFOLIOS
from config.config import CHUNK_SIZE
from modules.plotter import plotter_process_func
from modules.simulator import simulator_process_func


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s :: %(levelname)s :: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument('--asset-returns-csv', default='config/asset_returns.csv', help='path to csv with asset returns')
    parser.add_argument(
        '--precision', type=int, default=10,
        help='simulation precision')
    parser.add_argument(
        '--hull', type=int, default=1,
        help='use hull algorithm to draw only given layers'
             ' of portfolios, set to 0 to draw all portfolios'
             '(not recommended, plots will be VERY heavy)')
    return parser.parse_args()


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main(argv):
    cmdline_args = _parse_args(argv)
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
    ]

    time_start = time.time()
    market_assets, market_yearly_revenue_multiplier = data_source.read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    num_errors = data_output.report_errors_in_portfolios(portfolios=STATIC_PORTFOLIOS, tickers_to_test=market_assets, color_map=RGB_COLOR_MAP)
    if num_errors > 0:
        logging.error(f'Found {num_errors} invalid static portfolios')
        return
    if (not all(ticker in RGB_COLOR_MAP.keys() for ticker in market_assets)):
        logging.error(f'Some tickers in {cmdline_args.asset_returns_csv} are not in RGB_COLOR_MAP: {set(market_assets) - set(RGB_COLOR_MAP.keys())}')
        return

    static_portfolios_simulated = list(map(
        partial(Portfolio.simulate, asset_revenue_per_year=market_yearly_revenue_multiplier),
        STATIC_PORTFOLIOS))
    logging.info(f'{len(static_portfolios_simulated)} static portfolios will be plotted on all graphs')

    gen_edge_allocations = data_source.all_possible_allocations(len(market_assets), 100)
    gen_edge_portfolios = map(
        partial(Portfolio, assets=market_assets), gen_edge_allocations)
    list_edge_simulateds = list(map(partial(Portfolio.simulated, asset_revenue_per_year=market_yearly_revenue_multiplier), gen_edge_portfolios))
    logging.info(f'{len(list_edge_simulateds)} edge portfolios will be plotted on all graphs')

    process_wait_list = []

    logging.info(f'+{time.time() - time_start:.2f}s :: preparing portfolio simulation data pipeline...')
    simulated_source, simulated_sink = Pipe(duplex=False)
    process_wait_list.append(Process(
        target=simulator_process_func,
        kwargs={
            'assets': market_assets,
            'percentage_step': cmdline_args.precision,
            'asset_revenue_per_year': market_yearly_revenue_multiplier,
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
                'persistent_portfolios': list_edge_simulateds + static_portfolios_simulated,
                'coord_pair': coord_pair,
                'hull_layers': cmdline_args.hull,
                'color_map': RGB_COLOR_MAP,
            }
        ))

    logging.info(f'+{time.time() - time_start:.2f}s :: data pipeline prepared')

    deque(map(Process.start, process_wait_list), 0)
    logging.info(f'+{time.time() - time_start:.2f}s :: all processes started')

    deque(map(Process.join, process_wait_list), 0)
    logging.info(f'+{time.time() - time_start:.2f}s :: graphs ready')


if __name__ == '__main__':
    main(sys.argv)
