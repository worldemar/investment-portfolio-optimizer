#!/usr/bin/env python3

from collections.abc import Iterable
from modules.portfolio import Portfolio

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