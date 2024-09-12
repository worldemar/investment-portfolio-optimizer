#!/usr/bin/env python3

import asset_colors
from collections.abc import Iterable
from modules.portfolio import Portfolio
from modules.convex_hull import ConvexHullPoint

class PortfolioXYFieldsPoint(ConvexHullPoint):
    def __init__(self, portfolio: Portfolio, varname_x: str, varname_y: str):
        self.portfolio = portfolio
        self._varname_x = varname_x
        self._varname_y = varname_y

    def x(self):
        return self.portfolio.get_stat(self._varname_x)

    def y(self):
        return self.portfolio.get_stat(self._varname_y)

    def portfolio(self):
        return self.portfolio

    def __repr__(self):
        return f'[{self.x():.3f}, {self.y():.3f}] {self.portfolio}'


def portfolio_coord_points(portfolio: Portfolio, list_of_point_coord_pairs: list[tuple]):
    return {
        (field_x, field_y) : PortfolioXYFieldsPoint(portfolio, field_x, field_y) for field_x, field_y in list_of_point_coord_pairs
    }


def extract_hulls_from_points(point_hull_layers):
    return [point.portfolio for hull_layer in point_hull_layers for point in hull_layer]


def compose_plot_data(portfolios: list[Portfolio], field_x: str, field_y: str):
    return [[{
            'x': portfolio.get_stat(field_x),
            'y': portfolio.get_stat(field_y),
            'text': '\n'.join([
                portfolio.plot_tooltip_assets(),
                '—' * max(len(x) for x in portfolio.plot_tooltip_assets().split('\n')),
                portfolio.plot_tooltip_stats(),
            ]),
            'marker': portfolio.plot_marker,
            'color': portfolio.plot_color(dict(asset_colors.RGB_COLOR_MAP.items())),
            'size': 100 if portfolio.plot_always else 50 / portfolio.number_of_assets(),
            'linewidth': 0.5 if portfolio.plot_always else 1 / portfolio.number_of_assets(),
    }] for portfolio in portfolios]


def sanitize_portfolios(portfolios: Iterable, tickers_to_test: list):
    # sanitize static portfolios
    for portfolio in portfolios:
        total_weight = 0
        for ticker, weight in portfolio.weights:
            total_weight += weight
            if ticker not in tickers_to_test:
                raise ValueError(
                    f'Static portfolio {portfolio.weights} contain ticker "{ticker}",'
                    f' that is not in simulation data: {tickers_to_test}')
        if total_weight != 100:
            raise ValueError(f'Weight of portfolio {portfolio.weights} is not 100: {total_weight}')

def sanitize_portfolio(portfolio: Portfolio, tickers_to_test: list):
    total_weight = 0
    for ticker, weight in portfolio.weights:
        total_weight += weight
        if ticker not in tickers_to_test:
            raise ValueError(
                f'Static portfolio {portfolio.weights} contain ticker "{ticker}",'
                f' that is not in simulation data: {tickers_to_test}')
    if total_weight != 100:
        raise ValueError(f'Weight of portfolio {portfolio.weights} is not 100: {total_weight}')
    return portfolio

def simulate_portfolios(executor, market_data, portfolios: Iterable):
    for portfolio in portfolios:
        portfolio.simulate(market_data)
        yield portfolio

def simulate_portfolio(portfolio: Portfolio = None, market_data = None):
    portfolio.simulate(market_data)
    return portfolio

def simulate_portfolio(portfolio: Portfolio = None, market_data = None):
    portfolio.simulate(market_data)
    return portfolio

def simulate_marketdata_and_convert_to_xy_points(asset_allocation: dict, market_data: dict, xy_field_pairs: list[tuple[str, str]]):
    portfolio = Portfolio(asset_allocation)
    portfolio.simulate(market_data)
    return {
        (field_x, field_y) : PortfolioXYFieldsPoint(portfolio, field_x, field_y) for field_x, field_y in xy_field_pairs
    }

def simulate_marketdata(asset_allocation: dict, market_data: dict, xy_field_pairs: list[tuple[str, str]]):
    portfolio = Portfolio(asset_allocation).simulate(market_data)
    return portfolio