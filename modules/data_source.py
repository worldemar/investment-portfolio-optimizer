#!/usr/bin/env python3

import csv
from modules.portfolio import Portfolio
from static_portfolios import STATIC_PORTFOLIOS

def all_possible_allocations(assets: list, percentage_step: int, percentages_ret: list = []):
    if percentages_ret and len(percentages_ret) == len(assets) - 1:
        yield zip(assets, percentages_ret + [100 - sum(percentages_ret)])
        return
    for asset_percent in range(0, 101 - sum(percentages_ret), percentage_step):
        added_percentages = percentages_ret + [asset_percent]
        yield from all_possible_allocations(assets, percentage_step, added_percentages)

def all_possible_portfolios(assets: list, percentage_step: int, percentages_ret: list = []):
    if percentages_ret and len(percentages_ret) == len(assets) - 1:
        yield Portfolio(dict(zip(assets, percentages_ret + [100 - sum(percentages_ret)])))
        return
    for asset_percent in range(0, 101 - sum(percentages_ret), percentage_step):
        added_percentages = percentages_ret + [asset_percent]
        yield from all_possible_portfolios(assets, percentage_step, added_percentages)

def static_portfolio_layers():
    for portfolio in STATIC_PORTFOLIOS:
        yield [portfolio]

def read_capitalgain_csv_data(filename):
    yearly_revenue_multiplier = {}  # year, ticker = cash multiplier
    # read csv values from tickers.csv
    rows = []
    with open(filename, "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = list(csv_reader)
    tickers = rows[0][1:]
    for row in rows[1:]:
        if row[0] not in yearly_revenue_multiplier:
            yearly_revenue_multiplier[int(row[0])] = {}
        for i in range(1, len(row)):
            yearly_revenue_multiplier[int(row[0])][tickers[i - 1]] = \
                float(row[i].replace('%', '')) / 100 + 1
    return tickers, yearly_revenue_multiplier