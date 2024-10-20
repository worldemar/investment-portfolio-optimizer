#!/usr/bin/env python3

from modules.portfolio import Portfolio


def test_portfolio_serialize():
    epsilon = 1e-5
    portfolio = Portfolio(
        assets=['AAPL', 'MSFT', 'GOOG'],
        weights=[10, 40, 50],
    )
    portfolio.stat_gain = 0.1
    portfolio.stat_stdev = 0.2
    portfolio.stat_cagr = 0.3
    portfolio.stat_var = 0.4
    portfolio.stat_sharpe = 0.5

    serialized = portfolio.serialize()
    deserialized = Portfolio.deserialize(serialized, assets=portfolio.assets)
    assert portfolio.stat_gain - deserialized.stat_gain < epsilon
    assert portfolio.stat_stdev - deserialized.stat_stdev < epsilon
    assert portfolio.stat_cagr - deserialized.stat_cagr < epsilon
    assert portfolio.stat_var - deserialized.stat_var < epsilon
    assert portfolio.stat_sharpe - deserialized.stat_sharpe < epsilon
    assert portfolio.weights == deserialized.weights


def test_portfolio_serialize_batch():
    epsilon = 1e-5
    portfolios = []
    for i in range(100):
        portfolio = Portfolio(
            assets=['AAPL', 'MSFT', 'GOOG'],
            weights=[100 - i, i, 0],
        )
        portfolio.stat_gain = 0.1 * i
        portfolio.stat_stdev = 0.2 * i
        portfolio.stat_cagr = 0.3 * i
        portfolio.stat_var = 0.4 * i
        portfolio.stat_sharpe = 0.5 * i
        portfolios.append(portfolio)

    serialized = b''.join(p.serialize() for p in portfolios)
    deserialized_batch = list(Portfolio.deserialize_iter(serialized, assets=portfolio.assets))
    for i in range(100):
        assert portfolios[i].stat_gain - deserialized_batch[i].stat_gain < epsilon
        assert portfolios[i].stat_stdev - deserialized_batch[i].stat_stdev < epsilon
        assert portfolios[i].stat_cagr - deserialized_batch[i].stat_cagr < epsilon
        assert portfolios[i].stat_var - deserialized_batch[i].stat_var < epsilon
        assert portfolios[i].stat_sharpe - deserialized_batch[i].stat_sharpe < epsilon
        assert portfolios[i].weights == deserialized_batch[i].weights
