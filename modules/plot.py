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


# pylint: disable=too-many-arguments
def draw_portfolios_statistics(
        portfolios_list: list,
        f_x: callable, f_y: callable,
        xlabel: str, ylabel: str,
        color_map: dict):
    time_start = time.time()
    plot_data = []
    for portfolio in portfolios_list:
        plot_data.append({
            'x': f_x(portfolio),
            'y': f_y(portfolio),
            'text': portfolio.plot_tooltip(),
            'color': portfolio.plot_color(color_map),
            'size': 50 / portfolio.number_of_assets(),
        })
    draw_circles_with_tooltips(
        circles=plot_data,
        xlabel=xlabel,
        ylabel=ylabel,
        title=f'{ylabel} / {xlabel}',
        directory='result',
        filename=f'{ylabel} - {xlabel}',
        color_legend=color_map)
    time_end = time.time()
    print(f'--- Graph ready: {ylabel} - {xlabel} --- {time_end-time_start:.2f}s')


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def draw_circles_with_tooltips(
        circles=None,
        xlabel=None, ylabel=None, title=None,
        directory='.', filename='plot.svg',
        color_legend=None):

    if not os.path.exists(directory):
        os.makedirs(directory)

    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
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
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    handles = [
        pltlines.Line2D(
            [0], [0],
            marker='o',
            label=label,
            linewidth=0,
            markerfacecolor=color,
            markeredgecolor='black'
        ) for label, color in color_legend.items()
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
            facecolor=circle['color'],
            edgecolor='black',
            linewidth=circle['size'] / 50,
            gid=f'patch_{index:08d}'
        )
    plt.savefig(os.path.join(directory, filename + '.png'), format="png", dpi=300)

    for index, circle in enumerate(circles):
        axes.annotate(
            gid=f'tooltip_{index:08d}',
            text=circle['text'],
            xy=(circle['x'], circle['y']),
            xytext=(16, 0),
            textcoords='offset pixels',
            color='black',
            horizontalalignment='left',
            verticalalignment='center',
            fontsize=8,
            bbox={
                'boxstyle': 'round,pad=0.5',
                'facecolor': (1.0, 1.0, 1.0, 0.9),
                'linewidth': 0.5,
                'zorder': 2,
            },
        )
    virtual_file = StringIO()
    plt.savefig(virtual_file, format="svg")

    # XML trickery for interactive tooltips

    tree, xmlid = ElementTree.XMLID(virtual_file.getvalue())
    tree.set('onload', 'init(evt)')

    for index, circle in enumerate(circles):
        element = xmlid[f'tooltip_{index:08d}']
        element.set('visibility', 'hidden')

    for index, circle in enumerate(circles):
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
    ElementTree.ElementTree(tree).write(os.path.join(directory, filename + '.svg'))


if __name__ == '__main__':
    from math import sin, cos
    demo_data = []
    for i in range(0, 1000, 2):
        demo_data.append({
            'x': (i / 1000) ** 2 * cos(i / 25),
            'y': i**0.5 * sin(i / 25),
            'text': f'{i}\n{i**0.5:.0f}',
            'color': (1.0 * i / 1000, abs(cos(i / 25)), 1.0 - i / 1000),
            'size': i / 20,
        })
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
        circles=demo_data,
        color_legend=RGB_COLOR_MAP,
        directory='result',
        filename='plot_demo.svg'
    )
