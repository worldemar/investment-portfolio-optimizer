#!/usr/bin/env python3

import csv

def read_capitalgain_csv_data(filename):
    yearly_revenue_multiplier = {} # year, ticker = cash multiplier
    # read csv values from tickers.csv
    rows = []
    with open("tickers.csv", "r", encoding="utf-8") as f:
        csv_reader = csv.reader(f)
        rows = list(csv_reader)
    tickers = rows[0][1:]
    for row in rows[1:]:
        if row[0] not in yearly_revenue_multiplier:
            yearly_revenue_multiplier[int(row[0])] = {}
        for i in range(1, len(row)):
            yearly_revenue_multiplier[int(row[0])][tickers[i-1]] = float(row[i].replace('%',''))/100 + 1
    return tickers, yearly_revenue_multiplier