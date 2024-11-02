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

import struct
from math import prod as math_prod
from math import sumprod as math_sumprod


# pylint: disable=too-many-instance-attributes
class Portfolio:
    STAT_GAIN = 'Gain(x)'
    STAT_CAGR_PERCENT = 'CAGR(%)'
    STAT_VARIANCE = 'Variance'
    STAT_STDDEV = 'Stddev'
    STAT_SHARPE = 'Sharpe'

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
        self.stat = {}
        self._number_of_assets = None

    def aligned_to_market(self, market_assets: list):
        assets = self.assets
        weights = self.weights
        self.assets = market_assets
        self.weights = [0] * len(market_assets)
        for asset_idx, asset_name in enumerate(assets):
            self.weights[market_assets.index(asset_name)] = weights[asset_idx]
        return self

    @staticmethod
    def deserialize_iter(serialized_data, assets: list[str]):
        for portfolio_unpack in struct.iter_unpack(f'5f{len(assets)}i', serialized_data):
            portfolio = Portfolio(assets=assets, weights=[])
            portfolio.stat[Portfolio.STAT_GAIN], \
                portfolio.stat[Portfolio.STAT_CAGR_PERCENT], \
                portfolio.stat[Portfolio.STAT_VARIANCE], \
                portfolio.stat[Portfolio.STAT_STDDEV], \
                portfolio.stat[Portfolio.STAT_SHARPE], \
                *portfolio.weights = portfolio_unpack
            yield portfolio

    @staticmethod
    def deserialize(serialized_data, assets: list[str]):
        portfolio = Portfolio(assets=assets, weights=[])
        portfolio.stat[Portfolio.STAT_GAIN], \
            portfolio.stat[Portfolio.STAT_CAGR_PERCENT], \
            portfolio.stat[Portfolio.STAT_VARIANCE], \
            portfolio.stat[Portfolio.STAT_STDDEV], \
            portfolio.stat[Portfolio.STAT_SHARPE], \
            *portfolio.weights = struct.unpack(f'5f{len(assets)}i', serialized_data)
        return portfolio

    def serialize(self):
        return struct.pack(
            f'5f{len(self.assets)}i',
            self.stat[Portfolio.STAT_GAIN],
            self.stat[Portfolio.STAT_CAGR_PERCENT],
            self.stat[Portfolio.STAT_VARIANCE],
            self.stat[Portfolio.STAT_STDDEV],
            self.stat[Portfolio.STAT_SHARPE],
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

    # pylint: disable=too-many-locals
    @staticmethod
    def _simulate_y2y(allocation, asset_gain_per_year, year_start, year_end):
        annual_gains = [
            math_sumprod(asset_gain_per_year[year], allocation) / 100 for year in range(year_start, year_end + 1)
        ]
        stat_gain = math_prod(annual_gains)
        stat_cagr = stat_gain ** (1 / len(annual_gains)) - 1
        stat_var = sum(map(lambda ag: (ag - stat_cagr - 1) ** 2, annual_gains)) / (len(annual_gains) - 1)
        stat_stdev = stat_var ** 0.5
        return stat_gain, stat_stdev, stat_cagr, stat_var

    def simulate(self, asset_gain_per_year):
        years_min = min(asset_gain_per_year.keys())
        years_max = max(asset_gain_per_year.keys())

        def simulate_from_year_to_now(year_start):
            return Portfolio._simulate_y2y(
                self.weights,
                asset_gain_per_year=asset_gain_per_year,
                year_start=year_start,
                year_end=years_max
            )

        stats_per_year = list(map(simulate_from_year_to_now, range(years_min, years_max)))
        self.stat[Portfolio.STAT_GAIN], \
            self.stat[Portfolio.STAT_STDDEV], \
            stat_cagr, \
            self.stat[Portfolio.STAT_VARIANCE], \
            = (sum(stat_values) / len(stats_per_year) for stat_values in zip(*stats_per_year))
        self.stat[Portfolio.STAT_SHARPE] = stat_cagr / self.stat[Portfolio.STAT_STDDEV]
        self.stat[Portfolio.STAT_CAGR_PERCENT] = stat_cagr * 100

    def simulated(self, asset_gain_per_year):
        self.simulate(asset_gain_per_year)
        return self

    def __repr__(self):
        weights_without_zeros = []
        for ticker, weight in self.weights.items():
            if weight == 0:
                continue
            weights_without_zeros.append(f'{ticker}: {weight}%')
        str_weights = ' - '.join(weights_without_zeros)
        return f'{self.stat} :: {str_weights}'

    def __weights_without_zeros(self):
        weights_without_zeros = []
        for ticker, weight in zip(self.assets, self.weights):
            if weight == 0:
                continue
            weights_without_zeros.append(f'{ticker}: {weight}%')
        return weights_without_zeros

    def plot_circle_tooltip_stats(self):
        return '\n'.join([f'{key:8s}: {value:.3f}' for key, value in self.stat.items()])

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
            'x': self.stat[coord_pair[1]],
            'y': self.stat[coord_pair[0]],
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
