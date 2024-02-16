#!/usr/bin/env python3

import math
import statistics

class Portfolio:
    def __score(self):
        return (self.stat_gain) * (0.5 - self.stat_stdev)

    def __init__(self, weights):
        self.weights = weights
        self.annual_gains = []
        self.stat_gain = -1
        self.stat_stdev = -1
        self.stat_cagr = -1
        self.stat_var = -1
        self.stat_sharpe = -1
        self.score = 0

    def simulate(self, market_data, debug=False):
        capital = 1
        for year in market_data.keys():
            new_capital = 0
            if debug:
                print(f"simulation of {year} -------------------------------")
            for ticker, weight in self.weights:
                new_capital += capital*weight/100*market_data[year][ticker]
                if debug:
                    print(f"{ticker}: {weight}% money ({capital*weight/100:.2f}) * market revenue ({market_data[year][ticker]}) = {capital*weight/100*market_data[year][ticker]:.2f}")
            if capital > 0:
                self.annual_gains.append(new_capital/capital)
            capital = new_capital
            if debug:
                print(f"final capital: {capital:.2f}")

        self.stat_gain = math.prod(self.annual_gains)
        self.stat_stdev = statistics.stdev(self.annual_gains)
        self.stat_cagr = self.stat_gain**(1/len(self.annual_gains)) - 1
        self.stat_var = sum([(ann_gain-self.stat_cagr-1)**2 for ann_gain in self.annual_gains]) / (len(self.annual_gains) - 1)
        self.stat_sharpe = self.stat_cagr / self.stat_stdev
        self.score = self.__score()

    def __repr__(self):
        weights_without_zeros = []
        for ticker, weight in self.weights:
            if weight == 0:
                continue
            weights_without_zeros.append(f'{ticker}: {weight}%')
        str_weights = ' - '.join(weights_without_zeros)
        return ' '.join([
                f'{self.score:.3f}',
                '|',
                f'GAIN={self.stat_gain:.3f}',
                f'CAGR={self.stat_cagr*100:.2f}%',
                f'VAR={self.stat_var:.3f}',
                f'STDEV={self.stat_stdev:.3f}',
                f'SHARP={self.stat_sharpe:.3f}',
                '::',
                f'{str_weights}'
        ])
