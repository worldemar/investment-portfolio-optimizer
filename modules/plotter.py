#!/usr/bin/env python3

import modules.Portfolio
import modules.data_filter as data_filter
import modules.data_source as data_types
from config.asset_colors import RGB_COLOR_MAP
from modules.data_filter import multilayer_convex_hull
from modules.data_output import draw_circles_with_tooltips
from modules.Portfolio import Portfolio
import functools

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
        batch_xy_points = map(
            functools.partial(data_filter.PortfolioXYTuplePoint, coord_pair=coord_pair), deserialized_portfolios)
        batches_hulls_points.extend(
            data_filter.multilayer_convex_hull(batch_xy_points, hull_layers))
    convex_hull_points = multilayer_convex_hull(batches_hulls_points, hull_layers)

    portfolios_for_plot = list(map(data_filter.PortfolioXYTuplePoint.portfolio, convex_hull_points))
    portfolios_for_plot.extend(persistent_portfolios)
    portfolios_for_plot.sort(key=lambda x: -x.number_of_assets())
    # plot_data = data_filter.compose_plot_data(portfolios_for_plot, field_x=coord_pair[1], field_y=coord_pair[0])
    plot_circles = map(functools.partial(Portfolio.plot_circle_data, coord_pair=coord_pair), portfolios_for_plot)
    draw_circles_with_tooltips(
        circle_lines=[[circle] for circle in plot_circles],
        xlabel=coord_pair[1],
        ylabel=coord_pair[0],
        title=f'{coord_pair[0]} vs {coord_pair[1]}',
        directory='result',
        filename=f'{coord_pair[0]} - {coord_pair[1]}',
        asset_color_map=dict(RGB_COLOR_MAP),
    )