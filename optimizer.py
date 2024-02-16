#1/usr/bin/env python3

import sys
import argparse
import itertools
import multiprocessing
import functools
import time
import math
import statistics
from Portfolio import Portfolio
from csv_reader import read_capitalgain_csv_data

def gen_portfolios(stock_list, percentage_step, percentages_ret=[]):
    if len(percentages_ret) == len(stock_list) - 1:
        yield Portfolio(list(zip(stock_list, percentages_ret + [100-sum(percentages_ret)])))
        return
    for v in range(0,101-sum(percentages_ret), percentage_step):
        added_percentages = percentages_ret+[v]
        yield from gen_portfolios(stock_list, percentage_step, added_percentages)

def _simulate_portfolio(market_data, portfolio):
    portfolio.simulate(market_data)
    return portfolio

def _parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--precision', type=int, default=10, help='simulation precision, values less than 5 require A LOT of ram!')
    return parser.parse_args()


def main(argv):
    cmdline_args = _parse_args(argv)
    tickers_to_test, yearly_revenue_multiplier = read_capitalgain_csv_data("capital_gain_to_retire.csv")
    t1 = time.time()
    portfolios = []
    for portfolio in gen_portfolios(tickers_to_test, cmdline_args.precision):
        portfolios.append(portfolio)
    t2 = time.time()
    pool = multiprocessing.Pool(24)
    portfolios_simulated = list(pool.map(functools.partial(_simulate_portfolio, yearly_revenue_multiplier), portfolios))
    t3 = time.time()
    portfolios_simulated.sort(key=lambda x: x.score)
    for portfolio in portfolios_simulated[-100:]:
        print(f'{portfolio}')
    print(f'DONE --- {len(portfolios_simulated)} portfolios tested ------- prepare = {t2-t1:.2f}s, simulate = {t3-t2:.2f}s')
    print(f' --- Edge Cases --- ')
    print(f' MAX SCORE: {portfolios_simulated[-1]}')
    print(f' MIN SCORE: {portfolios_simulated[0]}')
    portfolios_simulated.sort(key=lambda x: x.stat_cagr)
    print(f'PROFITABLE: {portfolios_simulated[-1]}')
    print(f'     LOSSY: {portfolios_simulated[0]}')
    portfolios_simulated.sort(key=lambda x: x.stat_var)
    print(f'  VOLATILE: {portfolios_simulated[-1]}')
    print(f'    STABLE: {portfolios_simulated[0]}')
    portfolios_simulated.sort(key=lambda x: x.stat_sharpe)
    print(f'MAX SHARPE: {portfolios_simulated[-1]}')
    print(f'MIN SHARPE: {portfolios_simulated[0]}')


if __name__ == '__main__':
    main(sys.argv)
