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
from static_portfolios import STATIC_PORTFOLIOS

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

def portfolio_XYpoints(portfolio: Portfolio, list_of_point_coord_pairs: list[tuple]):
    return {
        (field_x, field_y) : PortfolioXYFieldsPoint(portfolio, field_x, field_y) for field_x, field_y in list_of_point_coord_pairs
    }

# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main(argv):
    total_time = time.time()

    cmdline_args = _parse_args(argv)
    process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=10)
    thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    tickers_to_test, yearly_revenue_multiplier = read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    # portfolios = chain(static_portfolio_layers(), all_possible_portfolios(tickers_to_test, cmdline_args.precision, []))
    sanitized = map(
        functools.partial(sanitize_portfolio, tickers_to_test=tickers_to_test),
        STATIC_PORTFOLIOS
    )
    for portfolio in sanitized:
        portfolio
    # sanitized = chain_generators(
    #     thread_executor,
    #     [portfolios],
    #     [functools.partial(sanitize_portfolio, tickers_to_test=tickers_to_test)],
    #     ParameterFormat.VALUE,
    # )
    # for portfolio in sanitized:
    #     portfolio
    # sanitized_thread = thread_executor.map(
    #     functools.partial(sanitize_portfolio, tickers_to_test=tickers_to_test),
    #     portfolios
    # )
    # for portfolio in sanitized_thread:
    #     portfolio
    # sanitized_process = process_executor.map(
    #     functools.partial(sanitize_portfolio, tickers_to_test=tickers_to_test),
    #     portfolios
    # )
    # for portfolio in sanitized_process:
    #     portfolio

    # possible_portfolios = islice(all_possible_portfolios(tickers_to_test, cmdline_args.precision, []), 10000)
    # portfolios = chain(static_portfolio_layers(), possible_portfolios)
    # portfolios_simulated = chain_generators(
    #     thread_executor,
    #     [portfolios],
    #     [functools.partial(Portfolio.simulate, market_data=yearly_revenue_multiplier)],
    #     ParameterFormat.ARGS,
    # )
    possible_portfolios = all_possible_portfolios(tickers_to_test, cmdline_args.precision, [])
    portfolios = chain(STATIC_PORTFOLIOS, possible_portfolios)
    portfolios_simulated = process_executor.map(
        functools.partial(Portfolio.simulate, market_data=yearly_revenue_multiplier),
        portfolios,
        chunksize=100,
    )
    # for portfolio in portfolios_simulated:
    #     portfolio

    # portfolio_points_XY = chain_generators(
    #     thread_executor,
    #     [portfolios_simulated],
    #     [
    #         functools.partial(PortfolioXYFieldsPoint, varname_x = 'stat_var', varname_y = 'stat_cagr'),
    #         functools.partial(PortfolioXYFieldsPoint, varname_x = 'stat_stdev', varname_y = 'stat_gain'),
    #     ],
    #     ParameterFormat.ARGS,
    # )
    coords_tuples = [
        ('stat_var','stat_cagr'),
        ('stat_stdev','stat_gain'),
    ]
    portfolios_points_XY = map(
        functools.partial(portfolio_XYpoints, list_of_point_coord_pairs=coords_tuples),
        portfolios_simulated,
    )

    # portfolio_points_all_hulls = chain_generators(
    #     thread_executor,
    #     [portfolio_points_XY,],
    #     [
    #         LazyMultilayerConvexHull(max_dirty_points=1000, layers=3),
    #         LazyMultilayerConvexHull(max_dirty_points=1000, layers=3),
    #     ],
    #     ParameterFormat.VALUE,
    # )
    # ---
    # executors = {
    #     coord_tuple : concurrent.futures.ThreadPoolExecutor(max_workers=1) for coord_tuple in coords_tuples
    # }
    # lmchs = {
    #     coord_tuple : LazyMultilayerConvexHull(max_dirty_points=1000000, layers=cmdline_args.hull) for coord_tuple in coords_tuples
    # }
    # for portfolio_points_XY in portfolios_points_XY:
    #     futures = {}
    #     for coord_tuple in coords_tuples:
    #         executor = executors[coord_tuple]
    #         lmch = lmchs[coord_tuple]
    #         futures[coord_tuple] = executor.submit(lmch, portfolio_points_XY[coord_tuple])
    #     for coord_tuple, future in futures.items():
    #         lmchs[coord_tuple] = future.result()

    lmchs = {
        coord_tuple : LazyMultilayerConvexHull(max_dirty_points=1000000, layers=cmdline_args.hull) for coord_tuple in coords_tuples
    }
    for portfolio_points_XY in portfolios_points_XY:
        for coord_tuple in coords_tuples:
            lmchs[coord_tuple](portfolio_points_XY[coord_tuple])

    # ppah = list(portfolio_points_all_hulls)
    # for pp in ppah:
    #     for hullayers in pp:
    #         for hullayer_idx, hullayer in enumerate(hullayers):
    #             for portfolio_point in hullayer:
    #                 print(hullayer_idx, portfolio_point)
    # sys.exit(0)

    # for coord_tuple, lmch in lmchs.items():
    #     portfolio_points_all_hulls = lmch.points()
    #     for portfolio_point in portfolio_points_all_hulls:
    #         print(coord_tuple, portfolio_point)

    # portfolios_plot_data = chain_generators(
    #     process_executor,
    #     [portfolios_all_lmchs],
    #     [
    #         functools.partial(compose_plot_data, field_x='stat_var', field_y='stat_cagr'),
    #         functools.partial(compose_plot_data, field_x='stat_stdev', field_y='stat_gain'),
    #     ],
    #     ParameterFormat.VALUE,
    # )
    portfolios_plot_data = {
        coord_tuple : None for coord_tuple in coords_tuples
    }
    for coord_tuple, lmch in lmchs.items():
        portfolios_plot_data[coord_tuple] = compose_plot_data(
            map(lambda x: x.portfolio, lmch.points()),
            field_x=coord_tuple[0],
            field_y=coord_tuple[1],
        )
    print(portfolios_plot_data)

    # draw_futures = chain_generators(
    #     process_executor,  # matplotlib requires drawing in main thread, need process for each drawer
    #     [portfolios_plot_data],
    #     [
    #         functools.partial(draw_circles_with_tooltips, xlabel='Variance', ylabel='CAGR %', title='Variance vs CAGR %', directory='result', filename='Variance vs CAGR %', asset_color_map=dict(RGB_COLOR_MAP)),
    #         functools.partial(draw_circles_with_tooltips, xlabel='Standard deviation', ylabel='Gain', title='Standard deviation vs Gain', directory='result', filename='Standard deviation vs Gain', asset_color_map=dict(RGB_COLOR_MAP)),
    #     ],
    #     ParameterFormat.VALUE,
    # )
    # for draw_futures_result in draw_futures:
    #     draw_futures_result.result()

    # draw_futures = []
    # for coord_tuple, plot_data in portfolios_plot_data.items():
    #     draw_futures.append(
    #         process_executor.submit(
    #             draw_circles_with_tooltips,
    #             circle_lines=plot_data,
    #             xlabel=coord_tuple[0],
    #             ylabel=coord_tuple[1],
    #             title=f'{coord_tuple[0]} vs {coord_tuple[1]}',
    #             directory='result',
    #             filename=f'{coord_tuple[0]} vs {coord_tuple[1]}',
    #             asset_color_map=dict(RGB_COLOR_MAP),
    #         )
    #     )
    # for draw_future in draw_futures:
    #     draw_future.result()

    for coord_tuple, plot_data in portfolios_plot_data.items():
        draw_circles_with_tooltips(
            circle_lines=plot_data,
            xlabel=coord_tuple[0],
            ylabel=coord_tuple[1],
            title=f'{coord_tuple[0]} vs {coord_tuple[1]}',
            directory='result',
            filename=f'{coord_tuple[0]} vs {coord_tuple[1]}',
            asset_color_map=dict(RGB_COLOR_MAP),
        )

    total_time = time.time() - total_time
    print(f'DONE :: {total_time:.2f}s')


if __name__ == '__main__':
    main(sys.argv)
