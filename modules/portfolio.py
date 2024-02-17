#!/usr/bin/env python3

import math
import statistics


class Portfolio:
    def __init__(self, weights):
        self.weights = weights
        self.annual_gains = []
        self.stat_gain = -1
        self.stat_stdev = -1
        self.stat_cagr = -1
        self.stat_var = -1
        self.stat_sharpe = -1

    def number_of_assets(self):
        return len([weight for weight, value in self.weights if value != 0])

    def simulate(self, market_data):
        capital = 1
        for year in market_data.keys():
            new_capital = 0
            for ticker, weight in self.weights:
                new_capital += capital * weight / 100 * market_data[year][ticker]
            if capital > 0:
                self.annual_gains.append(new_capital / capital)
            capital = new_capital

        self.stat_gain = math.prod(self.annual_gains)
        self.stat_stdev = statistics.stdev(self.annual_gains)
        self.stat_cagr = self.stat_gain**(1 / len(self.annual_gains)) - 1
        self.stat_var = sum((ann_gain - self.stat_cagr - 1) ** 2 for ann_gain in self.annual_gains)
        self.stat_var /= (len(self.annual_gains) - 1)
        self.stat_sharpe = self.stat_cagr / self.stat_stdev

    def __repr__(self):
        weights_without_zeros = []
        for ticker, weight in self.weights:
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

    def plot_tooltip(self):
        weights_without_zeros = []
        for ticker, weight in self.weights:
            if weight == 0:
                continue
            weights_without_zeros.append(f'{ticker}: {weight}%')
        str_weights = '\n'.join(weights_without_zeros)
        return '\n'.join([
            f'{str_weights}',
            '--- statistics ---',
            f'GAIN  : {self.stat_gain:.3f}',
            f'CAGR  : {self.stat_cagr*100:.2f}%',
            f'VAR   : {self.stat_var:.3f}',
            f'STDEV : {self.stat_stdev:.3f}',
            f'SHARP : {self.stat_sharpe:.3f}'
        ])

    def plot_color(self, color_map):
        color = [0, 0, 0, 1]
        for ticker, weight in self.weights:
            if ticker in color_map:
                color[0] = color[0] + color_map[ticker][0] * weight
                color[1] = color[1] + color_map[ticker][1] * weight
                color[2] = color[2] + color_map[ticker][2] * weight
        return (color[0] / max(color), color[1] / max(color), color[2] / max(color))
