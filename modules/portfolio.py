#!/usr/bin/env python3

import struct
from math import prod as math_prod
from statistics import stdev as statistics_stdev
from functools import partial


# pylint: disable=too-many-instance-attributes
class Portfolio:
    @staticmethod
    def static_portfolio(allocation: dict[str, int]):
        assets = list(allocation.keys())
        weights = list(allocation.values())
        return Portfolio(assets=assets, weights=weights, plot_always=True, plot_marker='X')

    def __init__(self, weights: list[int], assets: list[str], plot_always=False, plot_marker='o'):
        self.plot_marker = plot_marker
        self.plot_always = plot_always
        self.assets = assets
        self.weights = weights
        self.stat_gain = -1
        self.stat_stdev = -1
        self.stat_cagr = -1
        self.stat_var = -1
        self.stat_sharpe = -1
        self._number_of_assets = None
        self._named_stats = None

    @staticmethod
    def deserialize_iter(serialized_data, assets: list[str]):
        for portfolio_unpack in struct.iter_unpack(f'5f{len(assets)}i', serialized_data):
            portfolio = Portfolio(assets=assets, weights=[])
            portfolio.stat_gain, \
                portfolio.stat_stdev, \
                portfolio.stat_cagr, \
                portfolio.stat_var, \
                portfolio.stat_sharpe, \
                *portfolio.weights = portfolio_unpack
            yield portfolio

    @staticmethod
    def deserialize(serialized_data, assets: list[str]):
        portfolio = Portfolio(assets=assets, weights=[])
        portfolio.stat_gain, \
            portfolio.stat_stdev, \
            portfolio.stat_cagr, \
            portfolio.stat_var, \
            portfolio.stat_sharpe, \
            *portfolio.weights = struct.unpack(f'5f{len(assets)}i', serialized_data)
        return portfolio

    def serialize(self):
        return struct.pack(
            f'5f{len(self.assets)}i',
            self.stat_gain,
            self.stat_stdev,
            self.stat_cagr,
            self.stat_var,
            self.stat_sharpe,
            *self.weights,
        )

    def number_of_assets(self):
        '''
        Number of asset weights that are not zero
        '''
        if self._number_of_assets is None:
            self._number_of_assets = len(list(filter(lambda weight: weight != 0, self.weights)))
        return self._number_of_assets

    def asset_allocation_error(self, market_assets: list, color_map: dict[str, tuple[int, int, int]]):
        if not all(asset in market_assets for asset in self.assets):
            return f'some tickers in portfolio are not in market data: {set(self.assets) - set(market_assets)}'
        if sum(value for value in self.weights) != 100:
            return f'sum of weights is not 100: {sum(self.weights)}'
        if not all(asset in color_map.keys() for asset in self.assets):
            return 'some tickers have no color defined, ' + \
                f'add them to asset_colors.py: {set(self.assets) - set(color_map.keys())}'
        return ''

    def _simulate_y2y(self, asset_revenue_per_year, year_start, year_end):
        def gain(index_weight, asset_revenue, year):
            return asset_revenue[year][index_weight[0]] * index_weight[1]
        annual_gains = {}
        capital = 1
        for year in range(year_start, year_end + 1):
            gain_func = partial(gain, asset_revenue=asset_revenue_per_year, year=year)
            proportional_gains = sum(map(gain_func, enumerate(self.weights)))
            new_capital = capital * proportional_gains / 100
            if capital != 0:
                annual_gains[year] = new_capital / capital
            capital = new_capital

        stat_gain = math_prod(annual_gains.values())
        stat_stdev = statistics_stdev(annual_gains.values())
        stat_cagr = stat_gain**(1 / len(annual_gains.values())) - 1
        stat_var = sum(map(
            lambda ag: (ag - stat_cagr - 1) ** 2,
            annual_gains.values()))
        stat_var /= len(annual_gains) - 1
        stat_sharpe = stat_cagr / stat_stdev
        return stat_gain, stat_stdev, stat_cagr, stat_var, stat_sharpe

    def simulate(self, asset_revenue_per_year):
        years_min = min(asset_revenue_per_year.keys())
        years_max = max(asset_revenue_per_year.keys())
        def simulate_from_year_to_now(year_start):
            return self._simulate_y2y(
                asset_revenue_per_year=asset_revenue_per_year,
                year_start=year_start,
                year_end=years_max
            )
        def root_mean_square(values):
            mean = 0
            for val in values:
                mean += val * val
            mean /= len(values)
            return mean**0.5
        stats_per_year = list(map(simulate_from_year_to_now, range(years_min, years_max)))
        self.stat_gain, \
            self.stat_stdev, \
            self.stat_cagr, \
            self.stat_var, \
            self.stat_sharpe = (root_mean_square(stat_values) for stat_values in zip(*stats_per_year))

    def simulated(self, asset_revenue_per_year):
        self.simulate(asset_revenue_per_year)
        return self

    def get_stat(self, stat_name: str):
        if self._named_stats is None:
            self._named_stats = {
                'Gain(x)': self.stat_gain,
                'CAGR(%)': self.stat_cagr * 100,
                'Sharpe': self.stat_sharpe,
                'Variance': self.stat_var,
                'Stdev': self.stat_stdev,
            }
        return self._named_stats[stat_name]

    def __repr__(self):
        weights_without_zeros = []
        for ticker, weight in self.weights.items():
            if weight == 0:
                continue
            weights_without_zeros.append(f'{ticker}: {weight}%')
        str_weights = ' - '.join(weights_without_zeros)
        return ' '.join([
            f'GAIN={self.stat_gain:.3f}',
            f'CAGR={self.stat_cagr * 100:.2f}%',
            f'VAR={self.stat_var:.3f}',
            f'STDEV={self.stat_stdev:.3f}',
            f'SHARP={self.stat_sharpe:.3f}',
            '::',
            f'{str_weights}'
        ])

    def __weights_without_zeros(self):
        weights_without_zeros = []
        for ticker, weight in zip(self.assets, self.weights):
            if weight == 0:
                continue
            weights_without_zeros.append(f'{ticker}: {weight}%')
        return weights_without_zeros

    def plot_circle_tooltip_stats(self):
        return '\n'.join([
            f'GAIN  : {self.stat_gain:.3f}',
            f'CAGR  : {self.stat_cagr * 100:.2f}%',
            f'VAR   : {self.stat_var:.3f}',
            f'STDEV : {self.stat_stdev:.3f}',
            f'SHARP : {self.stat_sharpe:.3f}'  # nopep8
        ])

    def plot_circle_tooltip_assets(self):
        return '\n'.join(self.__weights_without_zeros())

    def plot_circle_color(self, color_map):
        color = [0, 0, 0, 1]
        for ticker, weight in zip(self.assets, self.weights):
            if ticker in color_map:
                color[0] = color[0] + color_map[ticker][0] * weight / 100
                color[1] = color[1] + color_map[ticker][1] * weight / 100
                color[2] = color[2] + color_map[ticker][2] * weight / 100
            else:
                raise RuntimeError(f'color map does not contain asset "{ticker}", add it to asset_colors.py')
        return (color[0] / max(color), color[1] / max(color), color[2] / max(color))

    def plot_circle_data(self, coord_pair: tuple[str, str], color_map: dict[str, tuple[int, int, int]]):
        return {
            'x': self.get_stat(coord_pair[1]),
            'y': self.get_stat(coord_pair[0]),
            'text': '\n'.join([
                self.plot_circle_tooltip_assets(),
                '—' * max(len(x) for x in self.plot_circle_tooltip_assets().split('\n')),
                self.plot_circle_tooltip_stats(),
            ]),
            'marker': self.plot_marker,
            'color': self.plot_circle_color(color_map),
            'size': 100 if self.plot_always else 50 / self.number_of_assets(),
            'linewidth': 0.5 if self.plot_always else 1 / self.number_of_assets(),
        }
