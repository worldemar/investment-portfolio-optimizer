#!/usr/bin/env python3
"""
    Helper functions to draw figures using matplotlib.
"""

import os
import time
from io import StringIO
from xml.etree import ElementTree
import matplotlib.pyplot as plt
import matplotlib.lines as pltlines
from scipy.spatial import ConvexHull


def draw_portfolios_history(
        portfolios_list: list,
        title: str, xlabel: str, ylabel: str,
        color_map: dict):
    time_start = time.time()
    plot_data = []
    for portfolio in portfolios_list:
        line_data = []
        tooltip_line = '—' * max(
            [len(portfolio.plot_title())] + [len(x) for x in portfolio.plot_tooltip_assets().split('\n')])
        for year in sorted(portfolio.annual_capital.keys()):
            line_data.append({
                'x': year,
                'y': portfolio.annual_capital[year] * 100 - 100,
                'text': '\n'.join([
                    portfolio.plot_title(),
                    tooltip_line,
                    portfolio.plot_tooltip_assets(),
                    tooltip_line,
                    f'By {year}: {portfolio.annual_capital[year]*100-100:+.0f}%',
                ]),
                'marker': portfolio.plot_marker,
                'color': portfolio.plot_color(color_map),
                'size': 50 if portfolio.plot_always else 50 / portfolio.number_of_assets(),
                'linewidth': 1 if portfolio.plot_always else 1 / portfolio.number_of_assets(),
            })
        plot_data.append(line_data)
    draw_circles_with_tooltips(
        circle_lines=plot_data,
        xlabel=xlabel,
        ylabel=ylabel,
        title=title,
        directory='result',
        filename=f'{title} - {ylabel} - {xlabel}',
        asset_color_map=color_map,
        portfolio_legend=portfolios_list)
    time_end = time.time()
    print(f'--- Graph ready: {title} - {ylabel} - {xlabel} --- {time_end-time_start:.2f}s')


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def draw_portfolios_statistics(
        portfolios_list: list,
        f_x: callable, f_y: callable,
        title: str, xlabel: str, ylabel: str,
        color_map: dict, hull_layers: int):
    portfolios_to_draw = portfolios_list
    if hull_layers != 0:
        portfolios_to_draw = []
        portfolios_for_hull = portfolios_list
        for _ in range(hull_layers):
            portfolio_coords = [[f_x(portfolio), f_y(portfolio)] for portfolio in portfolios_for_hull]
            hull = ConvexHull(points=portfolio_coords, incremental=False)
            for hull_vertex in hull.vertices:
                portfolios_to_draw.append(portfolios_for_hull[hull_vertex])
            portfolios_for_hull_new = []
            for idx, portfolio in enumerate(portfolios_for_hull):
                if idx not in hull.vertices:
                    portfolios_for_hull_new.append(portfolio)
            portfolios_for_hull = portfolios_for_hull_new
        for portfolio in portfolios_list:
            if portfolio.number_of_assets() == 1 or portfolio.plot_always:
                portfolios_to_draw.append(portfolio)
    time_start = time.time()
    plot_data = []
    for portfolio in portfolios_to_draw:
        plot_data.append([{
            'x': f_x(portfolio),
            'y': f_y(portfolio),
            'text': '\n'.join([
                portfolio.plot_tooltip_assets(),
                '—' * max(len(x) for x in portfolio.plot_tooltip_assets().split('\n')),
                portfolio.plot_tooltip_stats(),
            ]),
            'marker': portfolio.plot_marker,
            'color': portfolio.plot_color(color_map),
            'size': 100 if portfolio.plot_always else 50 / portfolio.number_of_assets(),
            'linewidth': 0.5 if portfolio.plot_always else 1 / portfolio.number_of_assets(),
        }])
    draw_circles_with_tooltips(
        circle_lines=plot_data,
        xlabel=xlabel,
        ylabel=ylabel,
        title=title,
        directory='result',
        filename=f'{ylabel} - {xlabel}',
        asset_color_map=color_map)
    time_end = time.time()
    print(f'--- Graph ready: {ylabel} - {xlabel} --- {time_end-time_start:.2f}s')


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def draw_circles_with_tooltips(
        circle_lines=None,
        xlabel=None, ylabel=None, title=None,
        directory='.', filename='plot',
        asset_color_map=None, portfolio_legend=None):

    if not os.path.exists(directory):
        os.makedirs(directory)

    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
    plt.rcParams["font.family"] = "monospace"
    _, axes = plt.subplots(figsize=(9, 6))

    padding_percent = 15
    xlim_min = min(c['x'] for line in circle_lines for c in line)
    xlim_max = max(c['x'] for line in circle_lines for c in line)
    xlim_min_padded = xlim_min - padding_percent * (xlim_max - xlim_min) / 100
    xlim_max_padded = xlim_max + padding_percent * (xlim_max - xlim_min) / 100
    ylim_min = min(c['y'] for line in circle_lines for c in line)
    ylim_max = max(c['y'] for line in circle_lines for c in line)
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

    all_circles = [circle for line in circle_lines for circle in line]

    for line in circle_lines:
        if len(line) > 1:
            prev_circle = line[0]
            for circle in line[1:]:
                axes.plot(
                    [prev_circle['x'], circle['x']],
                    [prev_circle['y'], circle['y']],
                    color=(
                        (prev_circle['color'][0] + circle['color'][0]) / 2,
                        (prev_circle['color'][1] + circle['color'][1]) / 2,
                        (prev_circle['color'][2] + circle['color'][2]) / 2
                    ),
                    zorder=1
                )
                prev_circle = circle

    for index, circle in enumerate(all_circles):
        axes.scatter(
            x=circle['x'],
            y=circle['y'],
            s=circle['size'],
            marker=circle['marker'],
            facecolor=circle['color'],
            edgecolor='black',
            linewidth=circle['linewidth'],
            gid=f'patch_{index:08d}',
            zorder=2
        )

    plt.savefig(os.path.join(directory, filename + ' old.png'), format="png", dpi=300)

    for index, circle in enumerate(all_circles):
        axes.annotate(
            gid=f'tooltip_{index:08d}',
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

    tree, xmlid = ElementTree.XMLID(virtual_file.getvalue())
    tree.set('onload', 'init(evt)')

    for index, circle in enumerate(all_circles):
        element = xmlid[f'tooltip_{index:08d}']
        element.set('visibility', 'hidden')

    for index, circle in enumerate(all_circles):
        element = xmlid[f'patch_{index:08d}']
        element.set('onmouseover', f"ShowTooltip('tooltip_{index:08d}')")
        element.set('onmouseout', f"HideTooltip('tooltip_{index:08d}')")

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

    tree.insert(0, ElementTree.XML(script))
    ElementTree.ElementTree(tree).write(os.path.join(directory, filename + ' old.svg'))


if __name__ == '__main__':
    from math import sin, cos
    demo_data = []
    for j in range(0, 10):
        demo_data_line = []
        for i in range(0, 100, 2):
            demo_data_line.append({
                'x': ((i + j * 100) / 1000) ** 2 * cos((i + j * 100) / 25),
                'y': (i + j * 100)**0.5 * sin((i + j * 100) / 25),
                'text': f'{i}\n{i**0.5:.0f}\n{j}',
                'color': (1.0 * (i + j * 100) / 1000, abs(cos((i + j * 100) / 25)), 1.0 - (i + j * 100) / 1000),
                'size': (i + j * 100) / 20,
            })
        demo_data.append(demo_data_line)
    RGB_COLOR_MAP = {
        'red': (1, 0, 0),
        'blue': (0, 0, 1),
        'cyan': (0, 1, 1),
        'green': (0, 1, 0),
        'yellow': (1, 1, 0)
    }
    draw_circles_with_tooltips(
        xlabel='X LABEL', ylabel='Y LABEL',
        title='Demo',
        circle_lines=demo_data,
        asset_color_map=RGB_COLOR_MAP,
        directory='result',
        filename='plot_demo'
    )
