#!/usr/bin/env python3

import config.asset_colors as asset_colors
from collections.abc import Iterable
import modules.data_types as data_types
from modules.convex_hull import ConvexHullPoint
import multiprocessing
import modules.data_source as data_source

class PortfolioXYFieldsPoint(ConvexHullPoint):
    def __init__(self, portfolio: data_types.Portfolio, varname_x: str, varname_y: str):
        self.portfolio = portfolio
        self._varname_x = varname_x
        self._varname_y = varname_y

    def x(self):
        return self.portfolio.get_stat(self._varname_x)

    def y(self):
        return self.portfolio.get_stat(self._varname_y)

    def portfolio(self):
        return self.portfolio

    def __repr__(self):
        return f'[{self.x():.3f}, {self.y():.3f}] {self.portfolio}'

def queue_multiplexer(
        source_queue: multiprocessing.Queue,
        queues: list[multiprocessing.Queue]):
    while True:
        item = source_queue.get()
        if isinstance(item, data_types.DataStreamFinished):
            break
        for queue in queues:
            queue.put(item)
    for queue in queues:
        queue.put(data_types.DataStreamFinished())

def compose_plot_data(portfolios: Iterable[data_types.Portfolio], field_x: str, field_y: str):
    return [[{
            'x': portfolio.get_stat(field_x),
            'y': portfolio.get_stat(field_y),
            'text': '\n'.join([
                portfolio.plot_tooltip_assets(),
                '—' * max(len(x) for x in portfolio.plot_tooltip_assets().split('\n')),
                portfolio.plot_tooltip_stats(),
            ]),
            'marker': portfolio.plot_marker,
            'color': portfolio.plot_color(dict(asset_colors.RGB_COLOR_MAP.items())),
            'size': 100 if portfolio.plot_always else 50 / portfolio.number_of_assets(),
            'linewidth': 0.5 if portfolio.plot_always else 1 / portfolio.number_of_assets(),
    }] for portfolio in portfolios]
