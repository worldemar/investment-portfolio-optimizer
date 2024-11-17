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

import pickle
import multiprocessing.connection
import functools
from modules import data_filter
from modules import data_source
from modules.data_filter import multilayer_convex_hull
from modules.data_output import draw_circles_with_tooltips
from modules.portfolio import Portfolio


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
def plotter_process_func(
        assets: list[str],
        source: multiprocessing.connection.Connection = None,
        coord_pair: tuple[str, str] = None,
        hull_layers: int = None,
        edge_layers: int = None,
        persistent_portfolios: list[Portfolio] = None,
        color_map: dict[str, tuple[int, int, int]] = None,
        plots_directory: str = None):
    batches_hulls_points = []
    data_stream_end_pickle = pickle.dumps(data_source.DataStreamFinished())
    while True:
        bytes_from_pipe = source.recv_bytes()
        if bytes_from_pipe == data_stream_end_pickle:
            break
        deserialized_portfolios = Portfolio.deserialize_iter(bytes_from_pipe, assets=assets)
        batch_xy_points = map(
            functools.partial(data_filter.PortfolioXYTuplePoint, coord_pair=coord_pair), deserialized_portfolios)
        batches_hulls_points.extend(
            data_filter.multilayer_convex_hull(batch_xy_points, hull_layers, edge_layers))
    convex_hull_points = multilayer_convex_hull(batches_hulls_points, hull_layers, edge_layers)

    portfolios_for_plot = list(map(data_filter.PortfolioXYTuplePoint.portfolio, convex_hull_points))
    portfolios_for_plot.extend(persistent_portfolios)
    portfolios_for_plot.sort(key=lambda x: -x.number_of_assets())
    # plot_data = data_filter.compose_plot_data(portfolios_for_plot, field_x=coord_pair[1], field_y=coord_pair[0])
    plot_circles = list(map(
        functools.partial(
            Portfolio.plot_circle_data,
            coord_pair=coord_pair, color_map=color_map),
        portfolios_for_plot))
    draw_circles_with_tooltips(
        circles=plot_circles,
        xlabel=coord_pair[1],
        ylabel=coord_pair[0],
        title=f'{coord_pair[0]} vs {coord_pair[1]}',
        directory=plots_directory,
        filename=f'{coord_pair[0]} - {coord_pair[1]}',
        asset_color_map=color_map,
    )
