#!/usr/bin/env python3

import os
import sys
import argparse
import json
import logging
from datetime import datetime
import requests

MOEX_API_URL_TEMPLATE = "".join([
    "https://iss.moex.com/iss",
    "/engines/{engine}",
    "/markets/{market}",
    "/boards/{board}",
    "/securities/{security}",
    "/candles.json?from={from_date}&till={till_date}",
    "&interval={interval}&start=0"])
MOEX_API_INTERVALS = {"minute": "1", "10min": "10", "hour": "60", "day": "24", "week": "7", "month": "31"}


def load_ticker_settings():
    with open("config_tickers.json", "r", encoding="utf-8") as f:
        config_tickers = json.load(f)
    tickers_settings = []
    for ticker_settings in config_tickers:
        tickers_settings.append(dict(zip(["engine", "market", "board", "security"], ticker_settings)))
    return tickers_settings


def candles_load(filename: str, avg_from_volume: bool):
    with open(filename, "r", encoding="utf-8") as f:
        file_data = json.load(f)
    candles = []
    for row in file_data["candles"]["data"]:
        candles.append(dict(zip(file_data["candles"]["columns"], row)))
        candles[-1]["begin_datetime"] = datetime.strptime(candles[-1]["begin"], "%Y-%m-%d %H:%M:%S")
        candles[-1]["end_datetime"] = datetime.strptime(candles[-1]["end"], "%Y-%m-%d %H:%M:%S")
        if avg_from_volume:
            candles[-1]["avg_price"] = \
                (candles[-1]["value"] / candles[-1]["volume"]) if candles[-1]["volume"] else 0
        else:
            candles[-1]["avg_price"] = \
                (candles[-1]["open"] + candles[-1]["close"] + candles[-1]["high"] + candles[-1]["low"]) / 4
    return candles


def sync_ticker_data(ticker_settings: dict[str, str]):
    request_settings = ticker_settings.copy()
    request_settings["from_date"] = "1990-01-01"
    request_settings["till_date"] = "2050-12-31"
    request_settings["interval"] = MOEX_API_INTERVALS["month"]
    formatted_url = MOEX_API_URL_TEMPLATE.format(**request_settings)
    logging.info("- retrieving URL: %s", formatted_url)
    response = requests.get(url=formatted_url, timeout=15)
    return response.text


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--sync",
        action="store_true",
        help="Sync data for all tickers, only new ones are loaded by default")
    return parser.parse_args(argv[1:])


def sync_all_tickers(args, tickers_settings):
    for ticker_setting in tickers_settings:
        logging.info("Processing ticker: %s", ticker_setting["security"])
        # pylint: disable=consider-using-f-string
        filename = "data/{engine}_{market}_{board}_{security}.json".format(**ticker_setting)
        if not args.sync and os.path.exists(filename):
            candles = candles_load(filename, ticker_setting["market"] != "index")
            last_candle_date = sorted(candles, key=lambda x: x["end_datetime"])[-1]["end_datetime"].date()
            if last_candle_date >= datetime.now().date():
                logging.info("- Data for %s is up to date: %s", ticker_setting["security"], last_candle_date)
                continue
            logging.info("- Data for %s is outdated: %s", ticker_setting["security"], last_candle_date)
        logging.info("- Syncing data from MOEX for %s", ticker_setting["security"])
        ticker_data_str = sync_ticker_data(ticker_setting)
        with open(filename, "w", encoding="utf-8", newline="") as f:
            f.write(ticker_data_str)
        logging.info("- Saved to File: %s", filename)


def compute_monthly_returns(tickers_settings: list[dict[str, str]]):
    monthly_returns = {}
    for ticker_setting in tickers_settings:
        # pylint: disable=consider-using-f-string
        filename = "data/{engine}_{market}_{board}_{security}.json".format(**ticker_setting)
        candles = candles_load(filename, ticker_setting["market"] != "index")
        candles.sort(key=lambda x: x["end_datetime"])
        last_candle_avgprice = 0
        for candle in candles:
            month_str = candle["end_datetime"].strftime("%Y-%m")
            if last_candle_avgprice != 0:
                returns_percent = (candle["avg_price"] - last_candle_avgprice) / last_candle_avgprice * 100
            else:
                returns_percent = None
            last_candle_avgprice = candle["avg_price"]
            if returns_percent is not None:
                if month_str not in monthly_returns:
                    monthly_returns[month_str] = {}
                monthly_returns[month_str][ticker_setting["security"]] = f"{returns_percent:.4f}%"
    return monthly_returns


def write_csv(filename: str, ticker_list: list[str], monthly_returns: dict[str, dict[str, str]]):
    with open(filename, "w", encoding="utf-8", newline="") as f:
        f.write("month," + ",".join(ticker_list) + "\n")
        history_limited_by = None
        for month in sorted(monthly_returns.keys()):
            row = [month]
            for ticker in ticker_list:
                if ticker in monthly_returns[month]:
                    row.append(monthly_returns[month][ticker])
                else:
                    row.append(None)
                    history_limited_by = ticker
            if None not in row:
                f.write(",".join(row) + "\n")
    if history_limited_by is not None:
        logging.info("Returns history limited by ticker: %s", history_limited_by)


def main(argv):
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s :: %(levelname)s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    tickers_settings = load_ticker_settings()
    ticker_list = [ticker_setting["security"] for ticker_setting in tickers_settings]
    sync_all_tickers(args, tickers_settings)
    monthly_returns = compute_monthly_returns(tickers_settings)
    write_csv("monthly_returns.csv", ticker_list, monthly_returns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
