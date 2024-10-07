#!/usr/bin/env python3

from math import prod as math_prod
from statistics import stdev as statistics_stdev
from config.asset_colors import RGB_COLOR_MAP
import pickle
import json
import config
import config.asset_colors
import config.config


class ConvexHullPoint(tuple):
    pass


class DataStreamFinished:
    pass


# pylint: disable=too-many-instance-attributes
class Portfolio:
    def __init__(self, assets: list[str], weights: list[int], plot_always=False, plot_marker='o'):
        self.plot_marker = plot_marker
        self.plot_always = plot_always
        self.assets = assets
        self.weights = weights
        self.stat_gain = -1
        self.stat_stdev = -1
        self.stat_cagr = -1
        self.stat_var = -1
        self.stat_sharpe = -1

    def deserialize(serialized_data, assets: list[str]):
        portfolio = Portfolio(assets=assets, weights=[])
        portfolio.stat_gain, \
        portfolio.stat_stdev, \
        portfolio.stat_cagr, \
        portfolio.stat_var, \
        portfolio.stat_sharpe, \
        portfolio.weights = pickle.loads(serialized_data)
        portfolio.stats = {
            'Gain(x)': portfolio.stat_gain,
            'CAGR(%)': portfolio.stat_cagr * 100,
            'Sharpe': portfolio.stat_sharpe,
            'Variance': portfolio.stat_var,
            'Stdev': portfolio.stat_stdev,
        }
        return portfolio

    def serialize(self):
        return pickle.dumps([
            self.stat_gain,
            self.stat_stdev,
            self.stat_cagr,
            self.stat_var,
            self.stat_sharpe,
            self.weights,
        ])

    def number_of_assets(self):
        '''
        Number of asset weights that are not zero
        '''
        return len(list(filter(lambda weight: weight != 0, self.weights)))

    def asset_allocation_error(self, market_assets: list):
        if (not all(asset in market_assets for asset in self.assets)):
            return f'some tickers in portfolio are not in market data: {set(self.assets) - set(market_assets)}'
        if (sum(value for value in self.weights) != 100):
            return f'sum of weights is not 100: {sum(self.weights)}'
        if (not all(asset in RGB_COLOR_MAP.keys() for asset in self.assets)):
            return f'some tickers have no color defined, add them to asset_colors.py: {set(self.assets) - set(RGB_COLOR_MAP.keys())}'
        return ''

    def simulate(self, asset_revenue_per_year):
        annual_gains = {}
        annual_capital = {}
        capital = 1
        annual_capital[list(asset_revenue_per_year.keys())[0] - 1] = 1
        for year in asset_revenue_per_year.keys():
            gain_func = lambda index_weight: index_weight[1] * asset_revenue_per_year[year][index_weight[0]]
            proportional_gains = sum(map(gain_func, enumerate(self.weights)))
            new_capital = capital * proportional_gains / 100
            if capital != 0:
                annual_gains[year] = new_capital / capital
            capital = new_capital
            annual_capital[year] = new_capital

        self.stat_gain = math_prod(annual_gains.values())
        self.stat_stdev = statistics_stdev(annual_gains.values())
        self.stat_cagr = self.stat_gain**(1 / len(annual_gains.values())) - 1
        self.stat_var = sum(map(lambda ag: (ag - self.stat_cagr - 1) ** 2, annual_gains.values())) / (len(annual_gains) - 1)
        self.stat_sharpe = self.stat_cagr / self.stat_stdev
        self.stats = {
            'Gain(x)': self.stat_gain,
            'CAGR(%)': self.stat_cagr * 100,
            'Sharpe': self.stat_sharpe,
            'Variance': self.stat_var,
            'Stdev': self.stat_stdev,
        }
        return self

    def get_stat(self, stat_name: str):
        return {
            'Gain(x)': self.stat_gain,
            'CAGR(%)': self.stat_cagr * 100,
            'Sharpe': self.stat_sharpe,
            'Variance': self.stat_var,
            'Stdev': self.stat_stdev,
        }[stat_name]

    def __repr__(self):
        weights_without_zeros = []
        for ticker, weight in self.weights.items():
            if weight == 0:
                continue
            weights_without_zeros.append(f'{ticker}: {weight}%')
        str_weights = ' - '.join(weights_without_zeros)
        return ' '.join([
            f'GAIN={self.stat_gain:.3f}',
            f'CAGR={self.stat_cagr*100:.2f}%',
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

    def plot_tooltip_stats(self):
        return '\n'.join([
            f'GAIN  : {self.stat_gain:.3f}',
            f'CAGR  : {self.stat_cagr*100:.2f}%',
            f'VAR   : {self.stat_var:.3f}',
            f'STDEV : {self.stat_stdev:.3f}',
            f'SHARP : {self.stat_sharpe:.3f}'
        ])

    def plot_tooltip_assets(self):
        return '\n'.join(self.__weights_without_zeros())

    def plot_title(self):
        return f'«{", ".join(self.__weights_without_zeros())}»'

    def plot_color(self, color_map):
        color = [0, 0, 0, 1]
        for ticker, weight in zip(self.assets, self.weights):
            if ticker in color_map:
                color[0] = color[0] + color_map[ticker][0] * weight / 100
                color[1] = color[1] + color_map[ticker][1] * weight / 100
                color[2] = color[2] + color_map[ticker][2] * weight / 100
            else:
                raise RuntimeError(f'color map does not contain asset "{ticker}", add it to asset_colors.py')
        return (color[0] / max(color), color[1] / max(color), color[2] / max(color))


class UserPortfolio(Portfolio):
    def __init__(self, asset_allocation: dict[str, int]):
        super().__init__(assets=list(asset_allocation.keys()), weights=list(asset_allocation.values()), plot_always=True, plot_marker='X')
