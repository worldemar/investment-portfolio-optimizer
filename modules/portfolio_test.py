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

import functools
from itertools import accumulate
import pytest
from modules.portfolio import Portfolio
from modules import data_filter


def test_portfolio_serialize():
    epsilon = 1e-5
    portfolio = Portfolio(
        assets=['AAPL', 'MSFT', 'GOOG'],
        weights=[10, 40, 50],
    )
    portfolio.stat[Portfolio.STAT_GAIN] = 0.12345
    portfolio.stat[Portfolio.STAT_POP_PERCENT] = 0.54321
    portfolio.stat[Portfolio.STAT_DIP_PERCENT] = 0.67890
    portfolio.stat[Portfolio.STAT_STDDEV] = 0.23456
    portfolio.stat[Portfolio.STAT_CAGR_PERCENT] = 0.34567
    portfolio.stat[Portfolio.STAT_VARIANCE] = 0.45678
    portfolio.stat[Portfolio.STAT_SHARPE] = 0.56789
    portfolio.stat[Portfolio.STAT_ULCER_PERCENT] = 0.65432

    serialized = portfolio.serialize()
    deserialized = Portfolio.deserialize(serialized, assets=portfolio.assets)
    assert portfolio.stat[Portfolio.STAT_GAIN] - \
        deserialized.stat[Portfolio.STAT_GAIN] < epsilon
    assert portfolio.stat[Portfolio.STAT_POP_PERCENT] - \
        deserialized.stat[Portfolio.STAT_POP_PERCENT] < epsilon
    assert portfolio.stat[Portfolio.STAT_DIP_PERCENT] - \
        deserialized.stat[Portfolio.STAT_DIP_PERCENT] < epsilon
    assert portfolio.stat[Portfolio.STAT_STDDEV] - \
        deserialized.stat[Portfolio.STAT_STDDEV] < epsilon
    assert portfolio.stat[Portfolio.STAT_CAGR_PERCENT] - \
        deserialized.stat[Portfolio.STAT_CAGR_PERCENT] < epsilon
    assert portfolio.stat[Portfolio.STAT_VARIANCE] - \
        deserialized.stat[Portfolio.STAT_VARIANCE] < epsilon
    assert portfolio.stat[Portfolio.STAT_SHARPE] - \
        deserialized.stat[Portfolio.STAT_SHARPE] < epsilon
    assert portfolio.stat[Portfolio.STAT_ULCER_PERCENT] - \
        deserialized.stat[Portfolio.STAT_ULCER_PERCENT] < epsilon
    assert portfolio.weights == deserialized.weights


def test_portfolio_serialize_batch():
    epsilon = 1e-5
    portfolios = []
    for i in range(100):
        portfolio = Portfolio(
            assets=['AAPL', 'MSFT', 'GOOG'],
            weights=[100 - i, i, 0],
        )
        portfolio.stat[Portfolio.STAT_GAIN] = 0.12345 * i
        portfolio.stat[Portfolio.STAT_POP_PERCENT] = 0.54321 * i
        portfolio.stat[Portfolio.STAT_DIP_PERCENT] = 0.67890 * i
        portfolio.stat[Portfolio.STAT_STDDEV] = 0.23456 * i
        portfolio.stat[Portfolio.STAT_CAGR_PERCENT] = 0.34567 * i
        portfolio.stat[Portfolio.STAT_VARIANCE] = 0.45678 * i
        portfolio.stat[Portfolio.STAT_SHARPE] = 0.56789 * i
        portfolio.stat[Portfolio.STAT_ULCER_PERCENT] = 0.11111 * i
        portfolios.append(portfolio)

    serialized = b''.join(p.serialize() for p in portfolios)
    deserialized = list(Portfolio.deserialize_iter(serialized, assets=portfolio.assets))
    for i in range(100):
        assert portfolios[i].stat[Portfolio.STAT_GAIN] - \
            deserialized[i].stat[Portfolio.STAT_GAIN] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_POP_PERCENT] - \
            deserialized[i].stat[Portfolio.STAT_POP_PERCENT] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_DIP_PERCENT] - \
            deserialized[i].stat[Portfolio.STAT_DIP_PERCENT] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_STDDEV] - \
            deserialized[i].stat[Portfolio.STAT_STDDEV] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_CAGR_PERCENT] - \
            deserialized[i].stat[Portfolio.STAT_CAGR_PERCENT] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_VARIANCE] - \
            deserialized[i].stat[Portfolio.STAT_VARIANCE] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_SHARPE] - \
            deserialized[i].stat[Portfolio.STAT_SHARPE] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_ULCER_PERCENT] - \
            deserialized[i].stat[Portfolio.STAT_ULCER_PERCENT] < epsilon
        assert portfolios[i].weights == deserialized[i].weights


# values marked with "manually verified" are verified by LibreOffice spreadsheet
@pytest.mark.parametrize(
    'year_selector_func,expected_stats',
    [
        [
            data_filter.years_first_to_last,
            {
                Portfolio.STAT_GAIN: 2.45785490021288,  # manually verified
                Portfolio.STAT_CAGR_PERCENT: 5.78151070361981,  # manually verified
                Portfolio.STAT_VARIANCE: 0.0018272163217203368,
                Portfolio.STAT_STDDEV: 0.042745950939478895,
            }
        ],
        [
            data_filter.years_first_to_all,
            {
                Portfolio.STAT_GAIN: 1.6041653796849782,  # manually verified
                Portfolio.STAT_CAGR_PERCENT: 4.870549235845304,  # manually verified
                Portfolio.STAT_VARIANCE: 0.0015185594255915605,  # manually verified
                Portfolio.STAT_STDDEV: 0.0389686980227921,
            }
        ],
        [
            functools.partial(data_filter.years_sliding_window, window_size=1),
            {
                Portfolio.STAT_GAIN: 1.11578266666667,  # manually verified
                Portfolio.STAT_CAGR_PERCENT: 5.621660570989,  # manually verified
                Portfolio.STAT_VARIANCE: 0.0030301684159257996,
                Portfolio.STAT_STDDEV: 0.055046965546938185,
            }
        ],
        [
            functools.partial(data_filter.years_sliding_window, window_size=3),
            {
                Portfolio.STAT_GAIN: 1.2431782019556925,
                Portfolio.STAT_CAGR_PERCENT: 5.57153847572112,
                Portfolio.STAT_VARIANCE: 0.0021007027703936203,
                Portfolio.STAT_STDDEV: 0.0458334241617798,
            }
        ],
        [
            functools.partial(data_filter.years_sliding_window, window_size=5),
            {
                Portfolio.STAT_GAIN: 1.3865912682424488,
                Portfolio.STAT_CAGR_PERCENT: 5.572730719544016,
                Portfolio.STAT_VARIANCE: 0.0019195562178402974,
                Portfolio.STAT_STDDEV: 0.043812740359857626,
            }
        ],
        [
            functools.partial(data_filter.years_sliding_window, window_size=10),
            {
                Portfolio.STAT_GAIN: 1.8190128874819955,
                Portfolio.STAT_CAGR_PERCENT: 5.569547576122236,
                Portfolio.STAT_VARIANCE: 0.0018335369897705684,
                Portfolio.STAT_STDDEV: 0.04281982005766218,
            }
        ],
        [
            data_filter.years_all_to_all,
            {
                Portfolio.STAT_GAIN: 1.4675720576461573,
                Portfolio.STAT_CAGR_PERCENT: 5.582527127915593,
                Portfolio.STAT_VARIANCE: 0.0020689039538368532,
                Portfolio.STAT_STDDEV: 0.045485205878800346,
            }
        ],
        [
            data_filter.years_all_to_last,
            {
                Portfolio.STAT_GAIN: 1.8070713713975535,
                Portfolio.STAT_CAGR_PERCENT: 6.864925449389167,
                Portfolio.STAT_VARIANCE: 0.002141432843112772,
                Portfolio.STAT_STDDEV: 0.04627561823587851,
            }
        ],
    ]
)
def test_portfolio_simulate(year_selector_func, expected_stats):
    epsilon = 1e-12
    portfolio = Portfolio(
        assets=['AAPL', 'MSFT', 'GOOG', 'AMZN'],
        weights=[10, 20, 30, 40],
    )
    asset_gain_per_year = {
        2000: [1.03, 1.04, 1.05, 1.06],
        2001: [1.01, 1.01, 1.09, 1.10],
        2002: [0.99, 1.09, 0.91, 1.01],
        2003: [1.02, 1.02, 1.08, 1.12],
        2004: [0.98, 1.08, 0.92, 1.03],
        2005: [1.03, 1.03, 1.07, 1.14],
        2006: [0.97, 1.07, 0.93, 1.05],
        2007: [1.04, 1.04, 1.06, 1.16],
        2008: [0.98, 1.06, 0.94, 1.07],
        2009: [1.05, 1.05, 1.05, 1.18],
        2010: [0.99, 1.04, 0.95, 1.09],
        2011: [1.06, 1.06, 1.04, 1.20],
        2012: [1.00, 1.03, 0.96, 1.09],
        2013: [1.07, 1.07, 1.03, 1.21],
        2014: [1.01, 1.02, 0.97, 1.09],
        2015: [1.08, 1.08, 1.02, 1.22],
    }
    portfolio.simulate(year_selector_func, asset_gain_per_year)
    for stat, expected_stat in expected_stats.items():
        assert stat and abs(portfolio.stat[stat] - expected_stat) < epsilon


# ---------------------------------------------------------------------------
# Ulcer index tests
# ---------------------------------------------------------------------------

def _ulcer_reference(annual_gains):
    """independent re-implementation for cross-checking: pure functional style"""
    values = list(accumulate(annual_gains, lambda v, gain: v * gain, initial=1.0))[1:]
    # running peak includes the initial capital 1.0: falling below start counts as drawdown
    peaks = list(accumulate([1.0] + values, max))[1:]
    drawdowns = [v / p - 1 for v, p in zip(values, peaks)]
    return (sum(d * d for d in drawdowns) / len(drawdowns)) ** 0.5


def test_ulcer_percent_manually_verified():
    # gains: 1.10, 0.90, 1.20, 0.95
    # portfolio values: 1.10, 0.99, 1.188, 1.1286; peaks: 1.10, 1.10, 1.188, 1.188
    # drawdowns:        0,     -10%,  0,       -5%
    # UI = sqrt((0 + 0.01 + 0 + 0.0025) / 4) = sqrt(0.003125)  (manually verified)
    epsilon = 1e-12
    portfolio = Portfolio(assets=['ASSET'], weights=[100])
    portfolio.simulate(
        year_range_selector_func=data_filter.years_first_to_last,
        asset_gain_per_year={2000: [1.10], 2001: [0.90], 2002: [1.20], 2003: [0.95]})
    assert abs(portfolio.stat[Portfolio.STAT_ULCER_PERCENT] - 5.590169943749474) < epsilon


def test_ulcer_percent_zero_when_never_below_peak():
    portfolio = Portfolio(assets=['ASSET'], weights=[100])
    portfolio.simulate(
        year_range_selector_func=data_filter.years_first_to_last,
        asset_gain_per_year={2000: [1.10], 2001: [1.20], 2002: [1.05], 2003: [1.00]})
    assert portfolio.stat[Portfolio.STAT_ULCER_PERCENT] == 0.0


def test_ulcer_percent_average_of_all_ranges():
    # multiple year ranges: ulcer must be averaged across ranges, same way as Dip
    epsilon = 1e-12
    asset_gain_per_year = {
        2000: [1.10], 2001: [0.90], 2002: [1.20], 2003: [0.95], 2004: [1.07],
    }
    years_sorted = sorted(asset_gain_per_year)
    portfolio = Portfolio(assets=['ASSET'], weights=[100])
    portfolio.simulate(
        year_range_selector_func=data_filter.years_all_to_last,
        asset_gain_per_year=asset_gain_per_year)
    year_ranges = list(data_filter.years_all_to_last(years_sorted))
    expected = sum(_ulcer_reference(
        [asset_gain_per_year[year][0]
         for year in years_sorted[years_sorted.index(start):years_sorted.index(end) + 1]])
        for start, end in year_ranges) / len(year_ranges) * 100
    assert abs(portfolio.stat[Portfolio.STAT_ULCER_PERCENT] - expected) < epsilon


def test_ulcer_percent_for_allocation_func():
    epsilon = 1e-12
    asset_gain_per_year = {
        2000: [1.10, 0.80], 2001: [0.90, 1.30], 2002: [1.20, 0.95], 2003: [0.95, 1.10],
    }
    portfolio = Portfolio(assets=['A', 'B'], weights=[], allocation_func=max)
    portfolio.simulate(
        year_range_selector_func=data_filter.years_first_to_last,
        asset_gain_per_year=asset_gain_per_year)
    best_gain_per_year = [max(asset_gain_per_year[year]) for year in sorted(asset_gain_per_year)]
    assert abs(portfolio.stat[Portfolio.STAT_ULCER_PERCENT] - _ulcer_reference(best_gain_per_year) * 100) < epsilon
