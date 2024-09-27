#!/usr/bin/env python3

from math import prod as math_prod
from statistics import stdev as statistics_stdev
from config.asset_colors import RGB_COLOR_MAP


class ConvexHullPoint(tuple):
    pass


class DataStreamFinished:
    pass


# pylint: disable=too-many-instance-attributes
class Portfolio:
    def __init__(self, weights: dict[str,float], plot_always=False, plot_marker='o'):
        self.plot_marker = plot_marker
        self.plot_always = plot_always
        self.weights = dict(weights)
        self.annual_gains = {}
        self.annual_capital = {}
        self.stat_gain = -1
        self.stat_stdev = -1
        self.stat_cagr = -1
        self.stat_var = -1
        self.stat_sharpe = -1
        self.tags = []

    def number_of_assets(self):
        '''
        Number of asset weights that are not zero
        '''
        return len(list(weight for weight in self.weights.values() if weight!= 0))

    def asset_allocation_error(self, market_tickers: list):
        if (not all(ticker in market_tickers for ticker, _ in self.weights.items())):
            return f'some tickers in portfolio are not in market data: {set(self.weights.keys()) - set(market_tickers)}'
        if (sum(value for _, value in self.weights.items()) != 100):
            return f'sum of weights is not 100: {sum(self.weights.values())}'
        if (not all(ticker in RGB_COLOR_MAP.keys() for ticker, _ in self.weights.items())):
            return f'some tickers have no color defined, add them to asset_colors.py: {set(self.weights.keys()) - set(RGB_COLOR_MAP.keys())}'
        return ''

    def simulate(self, market_data):
        capital = 1
        self.annual_capital[list(market_data.keys())[0] - 1] = 1
        for year in market_data.keys():
            new_capital = 0
            for ticker, weight in self.weights.items():
                new_capital += capital * weight / 100 * market_data[year][ticker]
            if capital > 0:
                self.annual_gains[year] = new_capital / capital
            capital = new_capital
            self.annual_capital[year] = new_capital

        self.stat_gain = math_prod(self.annual_gains.values())
        self.stat_stdev = statistics_stdev(self.annual_gains.values())
        self.stat_cagr = self.stat_gain**(1 / len(self.annual_gains.values())) - 1
        self.stat_var = sum((ann_gain - self.stat_cagr - 1) ** 2 for ann_gain in self.annual_gains.values())
        self.stat_var /= (len(self.annual_gains.values()) - 1)
        self.stat_sharpe = self.stat_cagr / self.stat_stdev
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
        for ticker, weight in self.weights.items():
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
        if self.tags:
            return f'«{", ".join(self.tags)}»'
        return f'«{", ".join(self.__weights_without_zeros())}»'

    def plot_color(self, color_map):
        color = [0, 0, 0, 1]
        for ticker, weight in self.weights.items():
            if ticker in color_map:
                color[0] = color[0] + color_map[ticker][0] * weight / 100
                color[1] = color[1] + color_map[ticker][1] * weight / 100
                color[2] = color[2] + color_map[ticker][2] * weight / 100
            else:
                raise RuntimeError(f'color map does not contain asset "{ticker}", add it to asset_colors.py')
        return (color[0] / max(color), color[1] / max(color), color[2] / max(color))
