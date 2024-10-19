#!/usr/bin/env python3

import modules.Portfolio
import modules.data_filter as data_filter
import modules.data_source as data_types
from config.asset_colors import RGB_COLOR_MAP
from modules.data_filter import compose_plot_data, multilayer_convex_hull
from modules.data_output import draw_circles_with_tooltips
from modules.Portfolio import Portfolio


import multiprocessing.connection
import pickle
from itertools import chain


def plotter_process_func(
        assets: list[str],
        source: multiprocessing.connection.Connection = None,
        coord_pair: tuple[str, str] = None,
        hull_layers: int = None,
        persistent_portfolios: list[modules.Portfolio.Portfolio] = None):
    batches_hulls_points = []
    data_stream_end_pickle = pickle.dumps(data_types.DataStreamFinished())
    while True:
        bytes = source.recv_bytes()
        if bytes == data_stream_end_pickle:
            break
        deserialized_portfolios = Portfolio.deserialize_iter(bytes, assets=assets)
        batch_xy_points = data_filter.portfolios_xy_points(deserialized_portfolios, coord_pair)
        batches_hulls_points.extend(multilayer_convex_hull(batch_xy_points, hull_layers))
    simulated_hull_points = multilayer_convex_hull(batches_hulls_points, hull_layers)
    persistent_portfolios_points = data_filter.portfolios_xy_points(persistent_portfolios, coord_pair)
    portfolios_for_plot = list(map(lambda x: x.portfolio(), chain(simulated_hull_points, persistent_portfolios_points)))
    portfolios_for_plot.sort(key=lambda x: -x.number_of_assets())
    plot_data = compose_plot_data(portfolios_for_plot, field_x=coord_pair[1], field_y=coord_pair[0])
    draw_circles_with_tooltips(
        circle_lines=plot_data,
        xlabel=coord_pair[1],
        ylabel=coord_pair[0],
        title=f'{coord_pair[0]} vs {coord_pair[1]}',
        directory='result',
        filename=f'{coord_pair[0]} - {coord_pair[1]}',
        asset_color_map=dict(RGB_COLOR_MAP),
    )