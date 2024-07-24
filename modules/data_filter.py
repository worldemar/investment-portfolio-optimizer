#!/usr/bin/env python3

from collections.abc import Iterable

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

def simulate_portfolios(executor, market_data, portfolios: Iterable):
    for portfolio in portfolios:
        yield portfolio.simulate(market_data)
