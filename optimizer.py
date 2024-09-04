#!/usr/bin/env python3

import sys
import argparse
import concurrent.futures
import functools
import time
import threading
import math
import hashlib
import random
from typing import List
from itertools import chain, islice
from modules.portfolio import Portfolio
from modules.data_source import all_possible_portfolios, static_portfolio_layers, read_capitalgain_csv_data
from modules.data_filter import sanitize_portfolio, sanitize_portfolios, simulate_portfolios, simulate_portfolio
from modules.data_pipeline import chain_generators, ParameterFormat
from modules.data_output import draw_portfolios_statistics, draw_portfolios_history, draw_circles_with_tooltips
from asset_colors import RGB_COLOR_MAP
from modules.convex_hull import LazyMultilayerConvexHull, ConvexHullPoint

import copy

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

# class ConvexHullPointWithUserData(list):
#     def __init__(self, x: float, y: float, text: str):
#         super().__init__([x, y])
#         self.text = text

# def warm_cpu_until(time_to_warm, func):
#     while time.time() < time_to_warm:
#         func()

# def pipeline_source(executor):
#     for _ in range(10000):
#         yield [random.random()]

# def pipeline_filter1(data):
#     for i in range(1000):
#         x = math.sin(data * data)
#     return math.sin(data * data)

# def pipeline_filter2(data):
#     for i in range(1000):
#         x = math.sin(data ** data)
#     return math.sin(data ** data)

# def pipeline_destination(data):
#     for i in range(1000):
#         x = hashlib.sha1(f'<<<{data}>>>'.encode('utf-8')).hexdigest()
#     return f'<<<{data}>>> {hashlib.sha1(f"<<<{data}>>>".encode("utf-8")).hexdigest()}'

# def feed_gen_to_func(executor, gen, func):
#     for item in gen:
#         yield executor.submit(func, item).result()

# def feed_gen2_to_func(executor, gen, func):
#     for item in gen:
#         yield executor.submit(func, item.result())

# class Add:
#     def __init__(self):
#         self.sum = 0
#         pass
#     def add(self):
#         self.sum += 1

# def add1(a: Add):
#     a.add()
#     return a

# def add2(a: Add):
#     a.add()
#     return a

# def _append_string(where: List[str], what: str):
#     where.append(what)
#     return where

# def check_double_function(executor):
#     the_object = []
#     futures = []
#     for func in [functools.partial(_append_string, what='foo'), functools.partial(_append_string, what='bar')]:
#         futures.append(executor.submit(func, *[the_object.copy()]))
#     results = []
#     for r in futures:
#         results.append(r.result())
#     return f'{the_object} = {results}'

# def the_decorator(func):
    # context = {}
    # def wrapper(*args, **kwargs):
    #     print(f'before {func.__name__}')
    #     result = func(*args, **kwargs)
    #     print(f'after {func.__name__}')
    #     return result
    # return wrapper

# @the_decorator
# def collect(x):
#     if 'sum' not in context:
#         context['sum'] = 0
#     context['sum'] += x
#     return context['sum']

# def gimme_closure():
#     s = 0
#     def collect(s, x):
#         s += x
#         return s
#     return functools.partial(collect, s)

# class NonCopyable:
#     def __copy__(self):
#         raise NotImplementedError()
    

class PortfolioXYFieldsPoint(ConvexHullPoint):
    def __init__(self, portfolio: Portfolio, varname_x: str, varname_y: str):
        self.portfolio = portfolio
        self._varname_x = varname_x
        self._varname_y = varname_y

    def x(self):
        return self.portfolio.__dict__[self._varname_x]

    def y(self):
        return self.portfolio.__dict__[self._varname_y]

    def portfolio(self):
        return self.portfolio

    def __repr__(self):
        return f'[{self.x():.3f}, {self.y():.3f}] {self.portfolio}'


def compose_plot_data(portfolios: list[Portfolio], field_x: str, field_y: str):
    return [[{
            'x': portfolio.__dict__[field_x],
            'y': portfolio.__dict__[field_y],
            'text': '\n'.join([
                portfolio.plot_tooltip_assets(),
                '—' * max(len(x) for x in portfolio.plot_tooltip_assets().split('\n')),
                portfolio.plot_tooltip_stats(),
            ]),
            'marker': portfolio.plot_marker,
            'color': portfolio.plot_color(dict(RGB_COLOR_MAP.items())),
            'size': 100 if portfolio.plot_always else 50 / portfolio.number_of_assets(),
            'linewidth': 0.5 if portfolio.plot_always else 1 / portfolio.number_of_assets(),
    }] for portfolio in portfolios]

def extract_hulls_from_points(point_hull_layers):
    return [point.portfolio for hull_layer in point_hull_layers for point in hull_layer]

# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main(argv):
    # tpe1 = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    # tpe2 = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    # print(id(tpe1),id(tpe2))
    # print(tpe1, tpe2)

    # class Kek(NonCopyable):
    #     pass

    # kek = Kek()
    # kek1 = copy.copy(kek)

    # c = gimme_closure()
    # print(c(1))
    # print(c(2))
    # print(c(3))

    # print(collect(1))
    # print(collect(2))
    # print(collect(3))

    # sys.exit(0)

    # thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    # process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)
    # print(check_double_function(thread_executor))
    # print(check_double_function(process_executor))
    # sys.exit(0)


    # _min = 2003
    # _max = 2024
    # years_counted = {}
    # for start in range(_min, _max + 1):
    #     for end in range(_min, _max + 1):
    #         if end < start:
    #             continue
    #         if not(start == _min or end == _max):
    #             continue
    #         for y in range(start, end + 1):
    #             if y not in years_counted:
    #                 years_counted[y] = 1
    #             else:
    #                 years_counted[y] += 1
    # for y, count in years_counted.items():
    #     print(f'{y}: {count}')

    # # execute warmer in separate thread for 5 seconds
    # threads = []
    # for thread_num in range(3):
    #     thread = threading.Thread(target=warm_cpu_until, args=(time.time() + 5, lambda: random.random()))
    #     threads.append(thread)
    # for thread in threads:
    #     thread.start()
    # for thread in threads:
    #     thread.join()

    # executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)

    # forward1 = generator_multiplex(executor, pipeline_source(executor), [pipeline_filter1])
    # # for x in forward1:
    # #     print(x)
    # forward2 = generator_multiplex(executor, forward1, [pipeline_filter2])
    # # for x in forward2:
    # #     print(x)
    # forward3 = generator_multiplex(executor, forward2, [pipeline_destination])
    # for x in forward3:
    #     print(x)

    # forward1 = feed_gen_to_func(executor, pipeline_source(executor), pipeline_filter1)
    # # for x in forward1:
    # #     print(x)
    # forward2 = feed_gen_to_func(executor, forward1, pipeline_filter2)
    # # for x in forward2:
    # #     print(x)
    # forward3 = feed_gen_to_func(executor, forward2, pipeline_destination)
    # for x in forward3:
    #     print(x)

    # future1 = executor.submit(ggenerator)
    # print(future1.result())
    # future2 = executor.submit(fsquare, ggenerator)
    # print(future2.result())
    # future3 = executor.submit(fprint, future2.result())
    # print(future3.result())

    total_time = time.time()

    cmdline_args = _parse_args(argv)
    process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)
    thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    tickers_to_test, yearly_revenue_multiplier = read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    # portfolios = chain(static_portfolio_layers(), all_possible_portfolios(tickers_to_test, cmdline_args.precision, []))
    portfolios = static_portfolio_layers()
    sanitized = chain_generators(
        thread_executor,
        [portfolios],
        [functools.partial(sanitize_portfolio, tickers_to_test=tickers_to_test)],
        ParameterFormat.VALUE,
    )
    for portfolio in sanitized:
        portfolio

    possible_portfolios = islice(all_possible_portfolios(tickers_to_test, cmdline_args.precision, []), 1000000)
    portfolios = chain(static_portfolio_layers(), possible_portfolios)
    portfolios_simulated = chain_generators(
        thread_executor,
        [portfolios],
        [functools.partial(Portfolio.simulate, market_data=yearly_revenue_multiplier)],
        ParameterFormat.ARGS,
    )

    portfolio_points_XY = chain_generators(
        thread_executor,
        [portfolios_simulated],
        [
            functools.partial(PortfolioXYFieldsPoint, varname_x = 'stat_var', varname_y = 'stat_cagr'),
            functools.partial(PortfolioXYFieldsPoint, varname_x = 'stat_stdev', varname_y = 'stat_gain'),
        ],
        ParameterFormat.ARGS,
    )

    portfolio_points_all_hulls = chain_generators(
        thread_executor,
        [portfolio_points_XY,],
        [
            LazyMultilayerConvexHull(max_dirty_points=1000, layers=3),
            LazyMultilayerConvexHull(max_dirty_points=1000, layers=3),
        ],
        ParameterFormat.VALUE,
    )

    # ppah = list(portfolio_points_all_hulls)
    # for pp in ppah:
    #     for hullayers in pp:
    #         for hullayer_idx, hullayer in enumerate(hullayers):
    #             for portfolio_point in hullayer:
    #                 print(hullayer_idx, portfolio_point)
    # sys.exit(0)


    # extract_hulls_from_points = lambda hulls: [point.portfolio for hull_layer in hulls for point in hull_layer]
    portfolios_all_lmchs = chain_generators(
        process_executor,
        [portfolio_points_all_hulls],
        [
            extract_hulls_from_points,
            extract_hulls_from_points,
        ],
        ParameterFormat.VALUE,
    )

    # pal = list(portfolios_all_lmchs)[0]  # take one (last) layer
    # for portfolios_one_lmch in pal:
    #     for portfolio_idx, portfolio in enumerate(portfolios_one_lmch):
    #         print(portfolio_idx, portfolio)
    # sys.exit(0)

    portfolios_plot_data = chain_generators(
        process_executor,
        [portfolios_all_lmchs],
        [
            functools.partial(compose_plot_data, field_x='stat_var', field_y='stat_cagr'),
            functools.partial(compose_plot_data, field_x='stat_stdev', field_y='stat_gain'),
        ],
        ParameterFormat.VALUE,
    )

    # pal = list(portfolios_plot_data)[0]  # take one (last) layer
    # for portfolios_one_lmch in pal:
    #     for portfolio_idx, portfolio in enumerate(portfolios_one_lmch):
    #         print(portfolio_idx, portfolio)
    # sys.exit(0)

    draw_futures = chain_generators(
        process_executor,  # matplotlib requires drawing in main thread, need process for each drawer
        [portfolios_plot_data],
        [
            functools.partial(draw_circles_with_tooltips, xlabel='Variance', ylabel='CAGR %', title='Variance vs CAGR %', directory='result', filename='Variance vs CAGR %', asset_color_map=dict(RGB_COLOR_MAP)),
            functools.partial(draw_circles_with_tooltips, xlabel='Standard deviation', ylabel='Gain', title='Standard deviation vs Gain', directory='result', filename='Standard deviation vs Gain', asset_color_map=dict(RGB_COLOR_MAP)),
        ],
        ParameterFormat.VALUE,
    )
    for draw_futures_result in draw_futures:
        draw_futures_result.result()

    # used_colors = { ticker: color for ticker, color in RGB_COLOR_MAP.items() if ticker in tickers_to_test }
    # title = ', '.join(
    #     [
    #         f'{min(yearly_revenue_multiplier.keys())}-{max(yearly_revenue_multiplier.keys())}',
    #         'rebalance every row',
    #         f'{cmdline_args.precision}% step',
    #     ]
    # )

    # fp = functools.partial(
    #     draw_portfolios_statistics,
    #     f_x=lambda x: x.stat_var, f_y=lambda y: y.stat_cagr * 100,
    #     title=title, xlabel='Variance', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull
    # )
    # fp(portfolios_simulated)

    # fp = functools.partial(
    #     draw_portfolios_statistics,
    #     f_x=_x, f_y=_y,
    #     title=title, xlabel='Variance', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull
    # )
    # print(f'portfolios_simulated: {portfolios_simulated.__class__.__name__}')
    # # result = chain_generators(executor, [portfolios_simulated], [fp])
    # # result = executor.submit(fp, portfolios_simulated) # BAD
    # # result = executor.submit(fp, list(portfolios_simulated)[:10]) # GOOD ?!
    # result = chain_generators(process_executor, [portfolios_simulated], [fp])
    # for r in result:
    #     print(r)

    # results = generator_multiplex(executor, portfolios_simulated,[
    #         functools.partial(
    #             draw_portfolios_statistics,
    #             f_x=_x, f_y=_y,
    #             title=title, xlabel='Variance', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull
    #         )
    # ])

    # for r in results:
    #      print(r)
    # print(hull.vertices)

    # f = executor.submit(
    #     draw_portfolios_statistics,
    #     portfolios_iterable=portfolios_simulated_gen,
    #     f_x=lambda x: x.stat_var, f_y=lambda y: y.stat_cagr * 100,
    #     title=title, xlabel='Variance', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull
    # )
    # results = f.result()

    # draw_portfolios_statistics(
    #     portfolios=portfolios_simulated,
    #     f_x=lambda x: x.stat_var, f_y=lambda y: y.stat_cagr * 100,
    #     title=title, xlabel='Variance', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull
    # )

    process_executor.shutdown(wait=True)

    # for i in read_capitalgain_csv_data_gen(cmdline_args.asset_returns_csv):
    #     print(i)
    # sys.exit(0)

    # time_start = time.time()
    # portfolios = STATIC_PORTFOLIOS + list(gen_portfolios(tickers_to_test, cmdline_args.precision, []))
    # time_prepare = time.time()
    # with multiprocessing.Pool(processes=4) as pool:
    #     pool_func = functools.partial(_simulate_portfolio, yearly_revenue_multiplier)
    #     portfolios_simulated = list(pool.map(pool_func, portfolios))
    # time_simulate = time.time()

    # print(f'DONE :: {len(portfolios_simulated)} portfolios tested')
    # print(f'times: prepare = {time_prepare-time_start:.2f}s, simulate = {time_simulate-time_prepare:.2f}s')

    # used_colors = {ticker: color for ticker, color in RGB_COLOR_MAP.items() if ticker in tickers_to_test}
    # title = ', '.join(
    #     [
    #         f'{min(yearly_revenue_multiplier.keys())}-{max(yearly_revenue_multiplier.keys())}',
    #         'rebalance every row',
    #         f'{cmdline_args.precision}% step',
    #     ]
    # )

    # draw_portfolios_statistics(
    #     portfolios_list=portfolios_simulated,
    #     f_x=lambda x: x.stat_var, f_y=lambda y: y.stat_cagr * 100,
    #     title=title, xlabel='Variance', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull)
    # draw_portfolios_statistics(
    #     portfolios_list=portfolios_simulated,
    #     f_x=lambda x: x.stat_var, f_y=lambda y: y.stat_sharpe,
    #     title=title, xlabel='Variance', ylabel='Sharpe', color_map=used_colors, hull_layers=cmdline_args.hull)
    # draw_portfolios_statistics(
    #     portfolios_list=portfolios_simulated,
    #     f_x=lambda x: x.stat_stdev, f_y=lambda y: y.stat_cagr * 100,
    #     title=title, xlabel='Stdev', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull)
    # draw_portfolios_statistics(
    #     portfolios_list=portfolios_simulated,
    #     f_x=lambda x: x.stat_stdev, f_y=lambda y: y.stat_sharpe,
    #     title=title, xlabel='Stdev', ylabel='Sharpe', color_map=used_colors, hull_layers=cmdline_args.hull)
    # draw_portfolios_statistics(
    #     portfolios_list=portfolios_simulated,
    #     f_x=lambda x: x.stat_sharpe, f_y=lambda y: y.stat_cagr * 100,
    #     title=title, xlabel='Sharpe', ylabel='CAGR %', color_map=used_colors, hull_layers=cmdline_args.hull)

    # portfolios_for_history = set()
    # portfolios_simulated.sort(key=lambda x: x.stat_cagr)
    # portfolios_simulated[-1].tags.append('MAX CAGR')
    # portfolios_for_history.add(portfolios_simulated[-1])
    # portfolios_simulated[0].tags.append('MIN CAGR')
    # portfolios_for_history.add(portfolios_simulated[0])
    # portfolios_simulated.sort(key=lambda x: x.stat_var)
    # portfolios_simulated[-1].tags.append('MAX VAR')
    # portfolios_for_history.add(portfolios_simulated[-1])
    # portfolios_simulated[0].tags.append('MIN VAR')
    # portfolios_for_history.add(portfolios_simulated[0])
    # portfolios_simulated.sort(key=lambda x: x.stat_sharpe)
    # portfolios_simulated[-1].tags.append('MAX SHARPE')
    # portfolios_for_history.add(portfolios_simulated[-1])
    # portfolios_simulated[0].tags.append('MIN SHARPE')
    # portfolios_for_history.add(portfolios_simulated[0])
    # for portfolio in portfolios_simulated:
    #     if portfolio.number_of_assets() == 1:
    #         portfolios_for_history.add(portfolio)
    # draw_portfolios_history(
    #     portfolios_for_history,
    #     title='Edge cases portfolios',
    #     xlabel='Year', ylabel='gain %', color_map=RGB_COLOR_MAP)

    # portfolios_for_history = set()
    # portfolios_simulated.sort(key=lambda x: x.stat_cagr)
    # for i in range(-1, -10, -1):
    #     portfolios_simulated[i].tags = [f'MAX CAGR #{abs(i)}']
    #     portfolios_for_history.add(portfolios_simulated[i])
    # draw_portfolios_history(
    #     portfolios_for_history,
    #     title='Max CAGR portfolios',
    #     xlabel='Year', ylabel='gain %', color_map=RGB_COLOR_MAP)

    # portfolios_for_history = set()
    # portfolios_simulated.sort(key=lambda x: -x.stat_stdev)
    # for i in range(-1, -10, -1):
    #     portfolios_simulated[i].tags = [f'MIN STDEV #{abs(i)}']
    #     portfolios_for_history.add(portfolios_simulated[i])
    # draw_portfolios_history(
    #     portfolios_for_history,
    #     title='Min STDEV portfolios',
    #     xlabel='Year', ylabel='gain %', color_map=RGB_COLOR_MAP)

    # portfolios_for_history = set()
    # portfolios_simulated.sort(key=lambda x: x.stat_sharpe)
    # for i in range(-1, -10, -1):
    #     portfolios_simulated[i].tags = [f'MAX SHARP #{abs(i)}']
    #     portfolios_for_history.add(portfolios_simulated[i])
    # draw_portfolios_history(
    #     portfolios_for_history,
    #     title='Max Sharp portfolios',
    #     xlabel='Year', ylabel='gain %', color_map=RGB_COLOR_MAP)

    total_time = time.time() - total_time
    print(f'DONE :: {total_time:.2f}s')


if __name__ == '__main__':
    main(sys.argv)
