#!/usr/bin/env python3

import math
import statistics
import struct
import typing
from config.asset_colors import RGB_COLOR_MAP

simulate_stat_order = ['Gain(x)', 'CAGR(%)', 'Sharpe', 'Variance', 'Stddev']
def simulate_and_pack(allocation: list[int], asset_revenue_per_year) -> list[float]:
    annual_gains = {}
    annual_capital = {}
    capital = 1
    annual_capital[list(asset_revenue_per_year.keys())[0] - 1] = 1
    for year in asset_revenue_per_year.keys():
        gain_func = lambda index_weight: index_weight[1] * asset_revenue_per_year[year][index_weight[0]]
        proportional_gains = sum(map(gain_func, enumerate(allocation)))
        new_capital = capital * proportional_gains / 100
        if capital != 0:
            annual_gains[year] = new_capital / capital
        capital = new_capital
        annual_capital[year] = new_capital

    gain = math.prod(annual_gains.values())
    cagr_percent = gain**(1 / len(annual_gains.values())) - 1
    stddev = statistics.stdev(annual_gains.values())
    variance = sum(map(lambda ag: (ag - cagr_percent - 1) ** 2, annual_gains.values())) / (len(annual_gains) - 1)
    sharpe = cagr_percent / stddev
    return serialize(allocation, [gain, cagr_percent * 100, sharpe, variance, stddev])

def serialize(allocation: list[float], simulation_result: list[float]):
    return struct.pack(
        f'{len(allocation) + len(simulation_result)}f',
        *allocation,
        *simulation_result
    )

def deserialize(allocation_and_simulation_result: bytes, assets_n:int):
    return struct.unpack(f'{assets_n + len(simulate_stat_order)}f', allocation_and_simulation_result)

    

def validate_dict_allocation(dict_allocation: dict[str, float], market_assets: list[str]):
    if (not all(asset in market_assets for asset in dict_allocation.keys())):
        return f'some tickers in portfolio are not in market data: {set(dict_allocation.keys()) - set(market_assets)}'
    if (sum(value for value in dict_allocation.values()) != 100):
        return f'sum of weights is not 100: {sum(dict_allocation.values())}'
    if (not all(asset in RGB_COLOR_MAP.keys() for asset in dict_allocation.keys())):
        return f'some tickers have no color defined, add them to asset_colors.py: {set(dict_allocation.keys()) - set(RGB_COLOR_MAP.keys())}'
    return ''

def dict_allocation_to_list_allocation(dict_allocation: dict[str, float], market_assets: list[str]):
    return [dict_allocation.get(asset,0) for asset in market_assets]

def compose_plot_data(allocation_stats: list[float], assets: str, marker: str, plot_always: bool, field_x: str, field_y: str):
    def _plot_color(assets, allocation, color_map):
        color = [0, 0, 0, 1]
        for ticker, weight in zip(assets, allocation):
            if ticker in color_map:
                color[0] = color[0] + color_map[ticker][0] * weight / 100
                color[1] = color[1] + color_map[ticker][1] * weight / 100
                color[2] = color[2] + color_map[ticker][2] * weight / 100
            else:
                raise RuntimeError(f'color map does not contain asset "{ticker}", add it to asset_colors.py')
        return (color[0] / max(color), color[1] / max(color), color[2] / max(color))
    
    def _weights_without_zeros(assets, allocation):
        weights_without_zeros = []
        for ticker, weight in zip(assets, allocation):
            if weight == 0:
                continue
            weights_without_zeros.append(f'{ticker}: {weight}%')
        return weights_without_zeros

    allocation = allocation_stats[:len(assets)]
    stats = allocation_stats[len(assets):]
    number_of_assets = len(allocation) - allocation.count(0)

    description = '\n'.join([
        '\n'.join(_weights_without_zeros(assets, allocation)),
        '—' * max(len(x) for x in '\n'.join(_weights_without_zeros(assets, allocation)).split('\n')),
        '\n'.join([
            f'GAIN  : {stats[simulate_stat_order.index('Gain(x)')]:.3f}',
            f'CAGR  : {stats[simulate_stat_order.index('CAGR(%)')]*100:.2f}%',
            f'VAR   : {stats[simulate_stat_order.index('Variance')]:.3f}',
            f'STDEV : {stats[simulate_stat_order.index('Stddev')]:.3f}',
            f'SHARP : {stats[simulate_stat_order.index('Sharpe')]:.3f}'
        ]),
    ]),

    return {
            'x': stats[simulate_stat_order.index(field_x)],
            'y': stats[simulate_stat_order.index(field_y)],
            'text': description,
            'marker': marker,
            'color': _plot_color(assets, allocation, dict(RGB_COLOR_MAP.items())),
            'size': 100 if plot_always else 50 / number_of_assets,
            'linewidth': 0.5 if plot_always else 1 / number_of_assets,
    }
