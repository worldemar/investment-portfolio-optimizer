#!/usr/bin/env python3

import sys
import argparse
import multiprocessing
import functools
import time
from modules.portfolio import Portfolio
from modules.capitalgain import read_capitalgain_csv_data
from modules.plot import draw_portfolios_statistics, draw_portfolios_history
from asset_colors import RGB_COLOR_MAP


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
        help='simulation precision, values less than 5 require A LOT of ram!')
    return parser.parse_args()


def main(argv):
    cmdline_args = _parse_args(argv)
    tickers_to_test, yearly_revenue_multiplier = read_capitalgain_csv_data(cmdline_args.asset_returns_csv)
    time_start = time.time()
    portfolios = []
    for portfolio in gen_portfolios(tickers_to_test, cmdline_args.precision, []):
        portfolios.append(portfolio)
    time_prepare = time.time()
    with multiprocessing.Pool() as pool:
        pool_func = functools.partial(_simulate_portfolio, yearly_revenue_multiplier)
        portfolios_simulated = list(pool.map(pool_func, portfolios))
    time_simulate = time.time()

    print(f'DONE :: {len(portfolios_simulated)} portfolios tested')
    print(f'times: prepare = {time_prepare-time_start:.2f}s, simulate = {time_simulate-time_prepare:.2f}s')
    print(' --- Edge Cases --- ')
    portfolios_for_history = set()
    portfolios_simulated.sort(key=lambda x: x.stat_cagr)
    portfolios_for_history.add(portfolios_simulated[0])
    portfolios_for_history.add(portfolios_simulated[-1])
    print(f'MAX PROFIT: {portfolios_simulated[-1]}')
    print(f'MAX LOSS  : {portfolios_simulated[0]}')
    portfolios_simulated.sort(key=lambda x: x.stat_var)
    portfolios_for_history.add(portfolios_simulated[0])
    portfolios_for_history.add(portfolios_simulated[-1])
    print(f'  VOLATILE: {portfolios_simulated[-1]}')
    print(f'    STABLE: {portfolios_simulated[0]}')
    portfolios_simulated.sort(key=lambda x: x.stat_sharpe)
    portfolios_for_history.add(portfolios_simulated[0])
    portfolios_for_history.add(portfolios_simulated[-1])
    print(f'MAX SHARPE: {portfolios_simulated[-1]}')
    print(f'MIN SHARPE: {portfolios_simulated[0]}')

    for portfolio in portfolios_simulated:
        if portfolio.number_of_assets() == 1:
            portfolios_for_history.add(portfolio)

    draw_portfolios_history(
        portfolios_for_history,
        title='Capital gain history for edge cases portfolios',
        xlabel='Year', ylabel='Total capital gain %', color_map=RGB_COLOR_MAP)

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
        title=title, xlabel='Variance', ylabel='CAGR %', color_map=RGB_COLOR_MAP)
    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_var, f_y=lambda y: y.stat_sharpe,
        title=title, xlabel='Variance', ylabel='Sharpe', color_map=RGB_COLOR_MAP)
    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_stdev, f_y=lambda y: y.stat_cagr * 100,
        title=title, xlabel='Stdev', ylabel='CAGR %', color_map=RGB_COLOR_MAP)
    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_stdev, f_y=lambda y: y.stat_sharpe,
        title=title, xlabel='Stdev', ylabel='Sharpe', color_map=RGB_COLOR_MAP)
    draw_portfolios_statistics(
        portfolios_list=portfolios_simulated,
        f_x=lambda x: x.stat_sharpe, f_y=lambda y: y.stat_cagr * 100,
        title=title, xlabel='Sharpe', ylabel='CAGR %', color_map=RGB_COLOR_MAP)


if __name__ == '__main__':
    main(sys.argv)
