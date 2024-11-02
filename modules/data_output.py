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

import logging
from os import makedirs
from os.path import exists
from os.path import join as os_path_join
from io import StringIO
import importlib
from modules.portfolio import Portfolio


def report_errors_in_portfolios(
        portfolios: list[Portfolio],
        tickers_to_test: list[str],
        color_map: dict[str, tuple[int, int, int]]):
    num_errors = 0
    for portfolio in portfolios:
        error = portfolio.asset_allocation_error(market_assets=tickers_to_test, color_map=color_map)
        if error != '':
            num_errors += 1
            logging.error(
                'Static portfolio %s\nhas invalid allocation: %s',
                portfolio, error)
    return num_errors


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=too-many-positional-arguments
def draw_circles_with_tooltips(
        circles: list[dict[str, dict]],
        xlabel: str = None,
        ylabel: str = None,
        title: str = None,
        directory: str = '.',
        filename: str = 'plot',
        asset_color_map: dict[str, tuple[int, int, int]] = None):

    if not exists(directory):
        makedirs(directory)

    plt = importlib.import_module('matplotlib.pyplot')
    pltlines = importlib.import_module('matplotlib.lines')

    plt.rcParams["font.family"] = "monospace"
    plt.rcParams["font.size"] = 10
    _, axes = plt.subplots(figsize=(12, 9))

    padding_percent_x = 25
    padding_percent_y = 25
    xlim_min = min(circle['x'] for circle in circles)
    xlim_max = max(circle['x'] for circle in circles)
    xlim_min_padded = xlim_min - padding_percent_x * (xlim_max - xlim_min) / 100
    xlim_max_padded = xlim_max + padding_percent_x * (xlim_max - xlim_min) / 100
    ylim_min = min(circle['y'] for circle in circles)
    ylim_max = max(circle['y'] for circle in circles)
    ylim_min_padded = ylim_min - padding_percent_y * (ylim_max - ylim_min) / 100
    ylim_max_padded = ylim_max + padding_percent_y * (ylim_max - ylim_min) / 100
    axes.set_xlim(xlim_min_padded, xlim_max_padded)
    axes.set_ylim(ylim_min_padded, ylim_max_padded)
    axes.tick_params(axis='x', which='both', bottom=True)
    axes.tick_params(axis='y', which='both', left=True)
    axes.set_axisbelow(True)
    axes.minorticks_on()
    axes.tick_params(axis='both', which='major', width=1)
    axes.tick_params(axis='both', which='minor', width=0.5)
    plt.grid(axis='both', which='both', visible=True)
    plt.grid(axis='both', which='major', linewidth=1)
    plt.grid(axis='both', which='minor', linewidth=0.5, linestyle=':')
    plt.title(title, zorder=0)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    if asset_color_map:
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
            fontsize=8,
            facecolor='white',
            framealpha=0.66
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
    logging.info('ready: %s', os_path_join(directory, filename + ".png"))

    for index, circle in enumerate(circles):
        axes.annotate(
            gid=f'tooltip_{index: 08d}',
            text=circle['text'],
            xy=(circle['x'], circle['y']),
            xytext=(0, 8),
            textcoords='offset pixels',
            color='black',
            horizontalalignment='center',
            verticalalignment='bottom',
            fontsize=12,
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

    for index, circle in enumerate(circles):
        element = xmlid[f'tooltip_{index: 08d}']
        element.set('visibility', 'hidden')

    for index, circle in enumerate(circles):
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
    logging.info('ready: %s', os_path_join(directory, filename + ".svg"))
