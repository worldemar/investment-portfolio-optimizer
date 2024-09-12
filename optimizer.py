#!/usr/bin/env python3

import sys
import argparse
import multiprocessing
import functools
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from modules.portfolio import Portfolio
from modules.capitalgain import read_capitalgain_csv_data
from modules.plot import draw_portfolios_statistics, draw_portfolios_history
from asset_colors import RGB_COLOR_MAP
from static_portfolios import STATIC_PORTFOLIOS


def gen_portfolios(assets: list, percentage_step: int, percentages_ret: list):
    if percentages_ret and len(percentages_ret) == len(assets) - 1:
        yield Portfolio(list(zip(assets, percentages_ret + [100 - sum(percentages_ret)])))
        return
    for asset_percent in range(0, 101 - sum(percentages_ret), percentage_step):
        added_percentages = percentages_ret + [asset_percent]
        yield from gen_portfolios(assets, percentage_step, added_percentages)


def _simulate_portfolio(market_data, portfolio):
    portfolio.simulate(market_data)
    return portfolio


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


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main(argv):
    cmdline_args = _parse_args(argv)
    tickers_to_test, yearly_revenue_multiplier = read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    # sanitize static portfolios
    for portfolio in STATIC_PORTFOLIOS:
        total_weight = 0
        for ticker, weight in portfolio.weights:
            total_weight += weight
            if ticker not in tickers_to_test:
                raise ValueError(
                    f'Static portfolio {portfolio.weights} contain ticker "{ticker}",'
                    f' that is not in simulation data: {tickers_to_test}')
        if total_weight != 100:
            raise ValueError(f'Weight of portfolio {portfolio.weights} is not 100: {total_weight}')

    time_start = time.time()
    portfolios = STATIC_PORTFOLIOS + list(gen_portfolios(tickers_to_test, cmdline_args.precision, []))
    time_prepare = time.time()
    with multiprocessing.Pool() as pool:
        pool_func = functools.partial(_simulate_portfolio, yearly_revenue_multiplier)
        portfolios_simulated = list(pool.map(pool_func, portfolios))
    time_simulate = time.time()

    print(f'DONE :: {len(portfolios_simulated)} portfolios tested in {time.time()-time_start:.2f}s')
    print(f'times: prepare = {time_prepare-time_start:.2f}s, simulate = {time_simulate-time_prepare:.2f}s')

    used_colors = {ticker: color for ticker, color in RGB_COLOR_MAP.items() if ticker in tickers_to_test}
    title = ', '.join(
        [
            f'{min(yearly_revenue_multiplier.keys())}-{max(yearly_revenue_multiplier.keys())}',
            'rebalance every row',
            f'{cmdline_args.precision}% step',
        ]
    )

    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_var, f_y=lambda y: y.stat_cagr * 100,
        title=title, xlabel='Variance', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull)
    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_var, f_y=lambda y: y.stat_sharpe,
        title=title, xlabel='Variance', ylabel='Sharpe', color_map=used_colors, hull_layers=cmdline_args.hull)
    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_stdev, f_y=lambda y: y.stat_cagr * 100,
        title=title, xlabel='Stdev', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull)
    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_stdev, f_y=lambda y: y.stat_sharpe,
        title=title, xlabel='Stdev', ylabel='Sharpe', color_map=used_colors, hull_layers=cmdline_args.hull)
    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_sharpe, f_y=lambda y: y.stat_cagr * 100,
        title=title, xlabel='Sharpe', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull)

    portfolios_for_history = set()
    portfolios_simulated.sort(key=lambda x: x.stat_cagr)
    portfolios_simulated[-1].tags.append('MAX CAGR')
    portfolios_for_history.add(portfolios_simulated[-1])
    portfolios_simulated[0].tags.append('MIN CAGR')
    portfolios_for_history.add(portfolios_simulated[0])
    portfolios_simulated.sort(key=lambda x: x.stat_var)
    portfolios_simulated[-1].tags.append('MAX VAR')
    portfolios_for_history.add(portfolios_simulated[-1])
    portfolios_simulated[0].tags.append('MIN VAR')
    portfolios_for_history.add(portfolios_simulated[0])
    portfolios_simulated.sort(key=lambda x: x.stat_sharpe)
    portfolios_simulated[-1].tags.append('MAX SHARPE')
    portfolios_for_history.add(portfolios_simulated[-1])
    portfolios_simulated[0].tags.append('MIN SHARPE')
    portfolios_for_history.add(portfolios_simulated[0])
    for portfolio in portfolios_simulated:
        if portfolio.number_of_assets() == 1:
            portfolios_for_history.add(portfolio)
    draw_portfolios_history(
        portfolios_for_history,
        title='Edge cases portfolios',
        xlabel='Year', ylabel='gain %', color_map=RGB_COLOR_MAP)

    portfolios_for_history = set()
    portfolios_simulated.sort(key=lambda x: x.stat_cagr)
    for i in range(-1, -10, -1):
        portfolios_simulated[i].tags = [f'MAX CAGR #{abs(i)}']
        portfolios_for_history.add(portfolios_simulated[i])
    draw_portfolios_history(
        portfolios_for_history,
        title='Max CAGR portfolios',
        xlabel='Year', ylabel='gain %', color_map=RGB_COLOR_MAP)

    portfolios_for_history = set()
    portfolios_simulated.sort(key=lambda x: -x.stat_stdev)
    for i in range(-1, -10, -1):
        portfolios_simulated[i].tags = [f'MIN STDEV #{abs(i)}']
        portfolios_for_history.add(portfolios_simulated[i])
    draw_portfolios_history(
        portfolios_for_history,
        title='Min STDEV portfolios',
        xlabel='Year', ylabel='gain %', color_map=RGB_COLOR_MAP)

    portfolios_for_history = set()
    portfolios_simulated.sort(key=lambda x: x.stat_sharpe)
    for i in range(-1, -10, -1):
        portfolios_simulated[i].tags = [f'MAX SHARP #{abs(i)}']
        portfolios_for_history.add(portfolios_simulated[i])
    draw_portfolios_history(
        portfolios_for_history,
        title='Max Sharp portfolios',
        xlabel='Year', ylabel='gain %', color_map=RGB_COLOR_MAP)


if __name__ == '__main__':
    main(sys.argv)
