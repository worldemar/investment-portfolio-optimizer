#!/usr/bin/env python3

import os
import math
import matplotlib.pyplot as plt
import matplotlib.lines as pltlines
import xml.etree.ElementTree as ET
from io import StringIO

def draw_circles_with_tooltips(circles = [], xlabel = None, ylabel = None, title = None, directory = '.', filename = 'plot.svg', color_legend = {}):

    if not os.path.exists(directory):
        os.makedirs(directory)

    ET.register_namespace("","http://www.w3.org/2000/svg")
    plt.rcParams["font.family"] = "monospace"
    fig, ax = plt.subplots(figsize=(9, 6))

    padding_percent = 15
    xlim_min = min([c['x'] for c in circles])
    xlim_max = max([c['x'] for c in circles])
    xlim_min_padded = xlim_min - padding_percent * (xlim_max - xlim_min) / 100
    xlim_max_padded = xlim_max + padding_percent * (xlim_max - xlim_min) / 100
    ylim_min = min([c['y'] for c in circles])
    ylim_max = max([c['y'] for c in circles])
    ylim_min_padded = ylim_min - padding_percent * (ylim_max - ylim_min) / 100
    ylim_max_padded = ylim_max + padding_percent * (ylim_max - ylim_min) / 100
    ax.set_xlim(xlim_min_padded,xlim_max_padded)
    ax.set_ylim(ylim_min_padded,ylim_max_padded)
    ax.tick_params(axis='x', which='minor', bottom=True)
    ax.tick_params(axis='y', which='minor', left=True)
    ax.set_axisbelow(True)
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
    ax.legend(
        handles=handles,
        fontsize='6',
        facecolor='white',
        framealpha=1
        ).set_zorder(1)

    for index, circle in enumerate(circles):
        s = ax.scatter(
            x=circle['x'],
            y=circle['y'],
            s = circle['size'],
            facecolor=circle['color'],
            edgecolor='black',
            linewidth=circle['size']/50,
            gid=f'patch_{index:08d}'
        )
    plt.savefig(os.path.join(directory, filename + '.png'), format="png", dpi=300)

    for index, circle in enumerate(circles):
        a = ax.annotate(
            gid=f'tooltip_{index:08d}',
            text=circle['text'],
            xy=(circle['x'], circle['y']),
            xytext=(16, 0),
            textcoords='offset pixels',
            color='black',
            horizontalalignment='left',
            verticalalignment='center',
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.5', facecolor=(1.0,1.0,1.0,0.9), linewidth=0.5, zorder=2),
         )
    f = StringIO()
    plt.savefig(f, format="svg")

    # XML trickery for interactive tooltips

    tree, xmlid = ET.XMLID(f.getvalue())
    tree.set('onload', 'init(evt)')

    for index, circle in enumerate(circles):
        el = xmlid[f'tooltip_{index:08d}']
        el.set('visibility', 'hidden')

    for index, circle in enumerate(circles):
        el = xmlid[f'patch_{index:08d}']
        el.set('onmouseover', f"ShowTooltip('tooltip_{index:08d}')")
        el.set('onmouseout', f"HideTooltip('tooltip_{index:08d}')")

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

    tree.insert(0, ET.XML(script))
    ET.ElementTree(tree).write(os.path.join(directory, filename + '.svg'))

if __name__ == '__main__':
    demo_data = []
    for i in range(0, 1000, 2):
        demo_data.append({
            'x': (i/1000)**2 * math.cos(i / 25),
            'y': i**0.5 * math.sin(i / 25),
            'text': f'{i}\n{i**0.5:.0f}',
            'color': (1.0 * i / 1000, abs(math.cos(i / 25)), 1.0 - i / 1000),
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
