#!/usr/bin/env python3

# Investment Portfolio Optimizer
# Copyright (C) 2024  Vladimir Looze

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import time
import json
import logging
import argparse
from collections import deque
from functools import partial, update_wrapper
from multiprocessing import Process
from multiprocessing import Pipe
from modules import data_output
from modules import data_source
from modules import data_filter
from modules.portfolio import Portfolio
from modules.plotter import plotter_process_func
from modules.simulator import simulator_process_func


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s :: %(levelname)s :: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def _parse_args(argv=None):
    year_selectors = {
        'first-to-last': data_filter.years_first_to_last,
        'first-to-all': data_filter.years_first_to_all,
        'window-3': partial(data_filter.years_sliding_window, window_size=3),
        'window-5': partial(data_filter.years_sliding_window, window_size=5),
        'window-10': partial(data_filter.years_sliding_window, window_size=10),
        'window-20': partial(data_filter.years_sliding_window, window_size=20),
        'all-to-last': data_filter.years_all_to_last,
        'all-to-all': data_filter.years_all_to_all,
    }
    update_wrapper(year_selectors['window-3'], data_filter.years_sliding_window)
    update_wrapper(year_selectors['window-5'], data_filter.years_sliding_window)
    update_wrapper(year_selectors['window-10'], data_filter.years_sliding_window)
    update_wrapper(year_selectors['window-20'], data_filter.years_sliding_window)
    parser = argparse.ArgumentParser(
        argv,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=', '.join([
            'Investment Portfolio Optimizer',
            'Copyright (C) 2024  Vladimir Looze'
        ]))
    parser.add_argument(
        '--precision', type=int, default=10,
        help='simulation precision: plot portfolios that have assets allocated\n'
             'to multiple of this percentage')
    parser.add_argument(
        '--hull', type=int, default=0,
        help='filter portfolios: use hull algorithm to plot only given ConvexHull layers '
             'of portfolios in coordinate space. Set to 0 to disable filter.')
    parser.add_argument(
        '--edge', type=int, default=0,
        help='filter portfolios: show edges of portfolio space '
             'by plotting portfolios having up to N assets allocated, '
             '-- Set to 0 to disable filter (will plot a lot, slow). '
             '-- Set to 1 to see pure portfolios (one asset = 100%%). '
             '-- Set to 2 to see lines connecting pure portfolios. ')
    parser.add_argument(
        '--min', action='store_true',
        help='plot theoretical portfolio that uses asset with minimum CAGR '
             'every year. Plotted as red square. ')
    parser.add_argument(
        '--max', action='store_true',
        help='plot theoretical portfolio that uses asset with maximum CAGR '
             'every year. Plotted as green square. ')
    parser.add_argument(
        '--years', choices=year_selectors.keys(),
        default=list(year_selectors.keys())[0],
        help=' '.join(['Select year ranges to average simulation data from'] +
            [f'{opt} - {func.__doc__}' for opt, func in year_selectors.items()])
    )

    parser.add_argument(
        '--config-colors', default='config_colors.json',
        help='path to json with color map for assets')
    parser.add_argument(
        '--config-portfolios', default='config_portfolios.json',
        help='path to json with static portfolios')
    parser.add_argument(
        '--config-returns', default='config_returns.csv',
        help='path to csv with yearly returns for assets')
    parser.add_argument(
        '--plot-dir', default='result',
        help='path to directory ta save plots')
    parser.add_argument(
        '--chunk', type=int, default=2**16,
        help='chunk size for data pipeline')
    args = parser.parse_args()
    args.years = year_selectors[args.years]
    return args


# pylint: disable=too-many-locals
def main(argv):
    cmdline_args = _parse_args(argv)
    coords_tuples = [
        # Y, X
        (Portfolio.STAT_CAGR_PERCENT, Portfolio.STAT_VARIANCE),
        (Portfolio.STAT_CAGR_PERCENT, Portfolio.STAT_STDDEV),
        (Portfolio.STAT_CAGR_PERCENT, Portfolio.STAT_SHARPE),
        (Portfolio.STAT_CAGR_PERCENT, Portfolio.STAT_POP_PERCENT),
        (Portfolio.STAT_CAGR_PERCENT, Portfolio.STAT_DIP_PERCENT),
        (Portfolio.STAT_GAIN, Portfolio.STAT_VARIANCE),
        (Portfolio.STAT_GAIN, Portfolio.STAT_STDDEV),
        (Portfolio.STAT_GAIN, Portfolio.STAT_SHARPE),
        (Portfolio.STAT_GAIN, Portfolio.STAT_POP_PERCENT),
        (Portfolio.STAT_GAIN, Portfolio.STAT_DIP_PERCENT),
        (Portfolio.STAT_SHARPE, Portfolio.STAT_VARIANCE),
        (Portfolio.STAT_SHARPE, Portfolio.STAT_STDDEV),
        (Portfolio.STAT_SHARPE, Portfolio.STAT_POP_PERCENT),
        (Portfolio.STAT_SHARPE, Portfolio.STAT_DIP_PERCENT),
        (Portfolio.STAT_POP_PERCENT, Portfolio.STAT_VARIANCE),
        (Portfolio.STAT_POP_PERCENT, Portfolio.STAT_STDDEV),
        (Portfolio.STAT_POP_PERCENT, Portfolio.STAT_SHARPE),
        (Portfolio.STAT_DIP_PERCENT, Portfolio.STAT_VARIANCE),
        (Portfolio.STAT_DIP_PERCENT, Portfolio.STAT_STDDEV),
        (Portfolio.STAT_DIP_PERCENT, Portfolio.STAT_SHARPE),
    ]

    time_start = time.time()

    market_assets, market_yearly_gain = \
        data_source.read_capitalgain_csv_data(cmdline_args.config_returns)
    with open(cmdline_args.config_colors, 'r', encoding='utf-8') as json_file:
        config_colors = json.load(json_file)
    with open(cmdline_args.config_portfolios, 'r', encoding='utf-8') as json_file:
        config_portfolios = [
            Portfolio.static_portfolio(portfolio) for portfolio in json.load(json_file)
        ]

    num_errors = data_output.report_errors_in_portfolios(
        portfolios=config_portfolios, tickers_to_test=market_assets, color_map=config_colors)
    if num_errors > 0:
        logging.error('Found %d invalid static portfolios', num_errors)
        return
    colored_assets = config_colors.keys()
    if not all(ticker in colored_assets for ticker in market_assets):
        logging.error('Some tickers in %s are not in config_colors: %s',
                      cmdline_args.config_returns, set(market_assets) - set(config_colors.keys()))
        return

    static_portfolios = config_portfolios
    if cmdline_args.min:
        static_portfolios.append(
            Portfolio.autoallocation_portfolio(allocation_func=min, color=[1,0,0,1], label='Minimum gain'))
    if cmdline_args.max:
        static_portfolios.append(
            Portfolio.autoallocation_portfolio(allocation_func=max, color=[0,1,0,1], label='Maximum gain'))

    static_portfolios_aligned_to_market = list(map(
        partial(Portfolio.aligned_to_market, market_assets=market_assets),
        static_portfolios))
    static_portfolios_simulated = list(map(
        partial(Portfolio.simulated,
                year_range_selector_func=cmdline_args.years,
                asset_gain_per_year=market_yearly_gain),
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
            'year_range_selector_func': cmdline_args.years,
            'asset_gain_per_year': market_yearly_gain,
            'sink': simulated_sink,
            'chunk_size': cmdline_args.chunk,
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
                'color_map': config_colors,
                'plots_directory': cmdline_args.plot_dir,
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
