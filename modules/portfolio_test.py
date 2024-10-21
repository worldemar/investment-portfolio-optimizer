#!/usr/bin/env python3

from modules.portfolio import Portfolio


def test_portfolio_serialize():
    epsilon = 1e-5
    portfolio = Portfolio(
        assets=['AAPL', 'MSFT', 'GOOG'],
        weights=[10, 40, 50],
    )
    portfolio.stat[Portfolio.STAT_GAIN] = 0.1
    portfolio.stat[Portfolio.STAT_STDDEV] = 0.2
    portfolio.stat[Portfolio.STAT_CAGR_PERCENT] = 0.3
    portfolio.stat[Portfolio.STAT_VARIANCE] = 0.4
    portfolio.stat[Portfolio.STAT_SHARPE] = 0.5

    serialized = portfolio.serialize()
    deserialized = Portfolio.deserialize(serialized, assets=portfolio.assets)
    assert portfolio.stat[Portfolio.STAT_GAIN] - \
        deserialized.stat[Portfolio.STAT_GAIN] < epsilon
    assert portfolio.stat[Portfolio.STAT_STDDEV] - \
        deserialized.stat[Portfolio.STAT_STDDEV] < epsilon
    assert portfolio.stat[Portfolio.STAT_CAGR_PERCENT] - \
        deserialized.stat[Portfolio.STAT_CAGR_PERCENT] < epsilon
    assert portfolio.stat[Portfolio.STAT_VARIANCE] - \
        deserialized.stat[Portfolio.STAT_VARIANCE] < epsilon
    assert portfolio.stat[Portfolio.STAT_SHARPE] - \
        deserialized.stat[Portfolio.STAT_SHARPE] < epsilon
    assert portfolio.weights == deserialized.weights


def test_portfolio_serialize_batch():
    epsilon = 1e-5
    portfolios = []
    for i in range(100):
        portfolio = Portfolio(
            assets=['AAPL', 'MSFT', 'GOOG'],
            weights=[100 - i, i, 0],
        )
        portfolio.stat[Portfolio.STAT_GAIN] = 0.1 * i
        portfolio.stat[Portfolio.STAT_STDDEV] = 0.2 * i
        portfolio.stat[Portfolio.STAT_CAGR_PERCENT] = 0.3 * i
        portfolio.stat[Portfolio.STAT_VARIANCE] = 0.4 * i
        portfolio.stat[Portfolio.STAT_SHARPE] = 0.5 * i
        portfolios.append(portfolio)

    serialized = b''.join(p.serialize() for p in portfolios)
    deserialized = list(Portfolio.deserialize_iter(serialized, assets=portfolio.assets))
    for i in range(100):
        assert portfolios[i].stat[Portfolio.STAT_GAIN] - \
            deserialized[i].stat[Portfolio.STAT_GAIN] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_STDDEV] - \
            deserialized[i].stat[Portfolio.STAT_STDDEV] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_CAGR_PERCENT] - \
            deserialized[i].stat[Portfolio.STAT_CAGR_PERCENT] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_VARIANCE] - \
            deserialized[i].stat[Portfolio.STAT_VARIANCE] < epsilon
        assert portfolios[i].stat[Portfolio.STAT_SHARPE] - \
            deserialized[i].stat[Portfolio.STAT_SHARPE] < epsilon
        assert portfolios[i].weights == deserialized[i].weights
