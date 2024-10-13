#!/usr/bin/env python3

import logging
import csv
import struct
import math
import statistics
import typing
import itertools
import config.config
import config.asset_colors
import importlib
import functools
import multiprocessing
from os.path import exists, join as os_path_join

def read_capitalgain_csv_data(filename):
    yearly_revenue_multiplier = {}  # year, ticker = cash multiplier
    # read csv values from tickers.csv
    rows = []
    with open(filename, "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = list(csv_reader)
    assets = rows[0][1:]
    for row in rows[1:]:
        if row[0] not in yearly_revenue_multiplier:
            yearly_revenue_multiplier[int(row[0])] = [0] * len(assets)
        for i in range(1, len(row)):
            yearly_revenue_multiplier[int(row[0])][i - 1] = \
                float(row[i].replace('%', '')) / 100 + 1
    return assets, yearly_revenue_multiplier

def all_possible_allocations(assets_num: list, step: int):
    def _allocations_recursive(
            assets_num: list, step: int,
            asset_idx: int = 0, asset_idx_max: int = 0,
            allocation: list[int] = (),
            allocation_sum: int = 0):
        if asset_idx == asset_idx_max:
            allocation[asset_idx] = 100 - allocation_sum
            yield allocation.copy() # dict(zip(assets, allocation))
            allocation[asset_idx] = 0
        else:
            for next_asset_percent in range(0, 100 - allocation_sum + 1, step):
                allocation[asset_idx] = next_asset_percent
                yield from _allocations_recursive(
                    assets_num, step,
                    asset_idx + 1, asset_idx_max,
                    allocation,
                    allocation_sum + next_asset_percent)
                allocation[asset_idx] = 0
    if 100 % step != 0:
        raise ValueError(f'cannot use step={step}, must be a divisor of 100')
    yield from _allocations_recursive(
        assets_num = assets_num, step = step,
        asset_idx = 0, asset_idx_max = assets_num - 1,
        allocation = [0] * assets_num,
        allocation_sum = 0)


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
    return struct.pack(f'{len(allocation)+len(simulate_stat_order)}f',
                       *allocation, gain, cagr_percent, sharpe, variance, stddev)

def deserialize_iterable(iterable: typing.Iterable[bytes], record_size: int, format: str):
    for chunk in iterable:
        for bytes_idx in range(0, len(chunk), record_size):
            yield struct.unpack(format, chunk[bytes_idx: bytes_idx + record_size])

def deserialize_bytes(data: bytes, record_size: int, format: str):
    deserialized = []
    for bytes_idx in range(0, len(data), record_size):
        deserialized.append(struct.unpack(format, data[bytes_idx: bytes_idx + record_size]))
    return deserialized

class PortfolioXYPoint():
    def __init__(self, allocation_with_stats: typing.Any, coord_pair: tuple[str, str], assets_n: int):
        self.allocation_with_stats = allocation_with_stats
        self.x = allocation_with_stats[assets_n + simulate_stat_order.index(coord_pair[0])]
        self.y = allocation_with_stats[assets_n + simulate_stat_order.index(coord_pair[1])]

def portfolios_xy_points(portfolios: typing.Iterable, coord_pair: tuple[str, str], assets_n: int):
    xy_func = functools.partial(PortfolioXYPoint, coord_pair=coord_pair, assets_n = assets_n)
    return map(xy_func, portfolios)

def convex_hull(points: list[PortfolioXYPoint]):
    points_n = len(points)
    if points_n <= 3:
        return points
    leftmost_point_idx = min(range(points_n), key = lambda i: points[i].x)
    point_1_index = leftmost_point_idx
    point_2_index = 0
    hull_points = []
    while True:
        hull_points.append(points[point_1_index])
        point_2_index = (point_1_index + 1) % points_n
        for point_3_index in range(points_n):
            point_1 = points[point_1_index]
            point_2 = points[point_2_index]
            point_3 = points[point_3_index]
            cross_product = (point_2.y - point_1.y) * (point_3.x - point_2.x) - (point_2.x - point_1.x) * (point_3.y - point_2.y)
            if (cross_product < 0):
                point_2_index = point_3_index
        point_1_index = point_2_index
        if (point_1_index == leftmost_point_idx):
            break
    return hull_points

def multiprocess_convex_hull(pool, xy_point_batch: list[PortfolioXYPoint], layers=None):
    batches = itertools.batched(xy_point_batch, len(xy_point_batch)//multiprocessing.cpu_count() + 1)
    mapped = pool.imap(convex_hull, batches)
    return convex_hull([point for batch in mapped for point in batch])


def compose_plot_data(allocation_stats: list[float], assets: str, marker: str, plot_always: bool, field_x: str, field_y: str):
    def _allocation_color(assets, allocation, color_map):
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
            'color': _allocation_color(assets, allocation, dict(config.asset_colors.RGB_COLOR_MAP.items())),
            'size': 100 if plot_always else 50 / number_of_assets,
            'linewidth': 0.5 if plot_always else 1 / number_of_assets,
    }


def draw_circles_with_tooltips(
        circles=None,
        xlabel=None, ylabel=None, title=None,
        directory='.', filename='plot',
        asset_color_map=None, portfolio_legend=None):
    logger = logging.getLogger(__name__)

    if not exists(directory):
        makedirs(directory)

    plt = importlib.import_module('matplotlib.pyplot')
    pltlines = importlib.import_module('matplotlib.lines')

    plt.rcParams["font.family"] = "monospace"
    _, axes = plt.subplots(figsize=(9, 6))

    padding_percent = 15
    xlim_min = min(c['x'] for c in circles)
    xlim_max = max(c['x'] for c in circles)
    xlim_min_padded = xlim_min - padding_percent * (xlim_max - xlim_min) / 100
    xlim_max_padded = xlim_max + padding_percent * (xlim_max - xlim_min) / 100
    ylim_min = min(c['y'] for c in circles)
    ylim_max = max(c['y'] for c in circles)
    ylim_min_padded = ylim_min - padding_percent * (ylim_max - ylim_min) / 100
    ylim_max_padded = ylim_max + padding_percent * (ylim_max - ylim_min) / 100
    axes.set_xlim(xlim_min_padded, xlim_max_padded)
    axes.set_ylim(ylim_min_padded, ylim_max_padded)
    axes.tick_params(axis='x', which='minor', bottom=True)
    axes.tick_params(axis='y', which='minor', left=True)
    axes.set_axisbelow(True)
    plt.grid(visible=True, which='both', axis='both')
    plt.title(title, zorder=0)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    if asset_color_map:
        if portfolio_legend:
            portfolio_legend_sorted = sorted(list(portfolio_legend), key=lambda x: x.plot_title())
            handles = [
                pltlines.Line2D(
                    [0], [0],
                    marker='o',
                    label=portfolio.plot_title(),
                    linewidth=0,
                    markerfacecolor=portfolio.plot_color(asset_color_map),
                    markeredgecolor='black'
                ) for portfolio in portfolio_legend_sorted
            ]
            axes.legend(
                handles=handles,
                fontsize='6',
                facecolor='white',
                framealpha=1
            ).set_zorder(1)
        else:
            handles = [
                pltlines.Line2D(
                    [0], [0],
                    marker='o',
                    label=label,
                    linewidth=0,
                    markerfacecolor=color,
                    markeredgecolor='black'
                ) for label, color in asset_color_map.items()
            ]
            axes.legend(
                handles=handles,
                fontsize='6',
                facecolor='white',
                framealpha=1
            ).set_zorder(1)

    for index, circle in enumerate(circles):
        axes.scatter(
            x=circle['x'],
            y=circle['y'],
            s=circle['size'],
            marker=circle['marker'],
            facecolor=circle['color'],
            edgecolor='black',
            linewidth=circle['linewidth'],
            gid=f'patch_{index: 08d}',
            zorder=2
        )

    plt.savefig(os_path_join(directory, filename + '.png'), format="png", dpi=300)
    logger.info(f'Plot ready: {os_path_join(directory, filename + ".png")}')

    return

    for index, circle in enumerate(all_circles):
        axes.annotate(
            gid=f'tooltip_{index: 08d}',
            text=circle['text'],
            xy=(circle['x'], circle['y']),
            xytext=(0, 8),
            textcoords='offset pixels',
            color='black',
            horizontalalignment='center',
            verticalalignment='bottom',
            fontsize=8,
            bbox={
                'boxstyle': 'round,pad=0.5',
                'facecolor': (1.0, 1.0, 1.0, 0.9),
                'linewidth': 0.5,
                'zorder': 3,
            },
        )
    virtual_file = StringIO()
    plt.savefig(virtual_file, format="svg")

    # XML trickery for interactive tooltips

    element_tree = importlib.import_module('xml.etree.ElementTree')
    element_tree.register_namespace("", "http://www.w3.org/2000/svg")
    tree, xmlid = element_tree.XMLID(virtual_file.getvalue())
    tree.set('onload', 'init(evt)')

    for index, circle in enumerate(all_circles):
        element = xmlid[f'tooltip_{index: 08d}']
        element.set('visibility', 'hidden')

    for index, circle in enumerate(all_circles):
        element = xmlid[f'patch_{index: 08d}']
        element.set('onmouseover', f"ShowTooltip('tooltip_{index: 08d}')")
        element.set('onmouseout', f"HideTooltip('tooltip_{index: 08d}')")

    script = """
        <script type="text/ecmascript">
        <![CDATA[
        function init(evt) {
            if (window.svgDocument == null) { svgDocument = evt.target.ownerDocument; }
        }
        function ShowTooltip(cur) {
            svgDocument.getElementById(cur).setAttribute('visibility',"visible")
        }
        function HideTooltip(cur) {
            svgDocument.getElementById(cur).setAttribute('visibility',"hidden")
        }
        ]]>
        </script>
        """

    tree.insert(0, element_tree.XML(script))
    element_tree.ElementTree(tree).write(os_path_join(directory, filename + '.svg'))
    logger.info(f'Plot ready: {os_path_join(directory, filename + ".svg")}')