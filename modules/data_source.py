#!/usr/bin/env python3

import csv
from functools import partial
from itertools import islice
from itertools import batched
from concurrent.futures import ThreadPoolExecutor
from modules.Portfolio import Portfolio

def all_possible_allocations(assets_n: int, step: int):
    """
    equivalent to filter(lambda x: sum(x) == 100, itertools.product(range(0,101,step), repeat=len(assets)))
    but considerably faster
    """
    def _allocations_recursive(
            assets_n: int, step: int,
            asset_idx: int = 0, asset_idx_max: int = 0,
            allocation: list[int] = (),
            allocation_sum: int = 0):
        if asset_idx == asset_idx_max:
            allocation[asset_idx] = 100 - allocation_sum
            yield allocation.copy() # dict(zip(assets, allocation))
            allocation[asset_idx] = 0
        else:
            for next_asset_percent in range(0, 100 - allocation_sum + 1, step):
                allocation[asset_idx] = next_asset_percent
                yield from _allocations_recursive(
                    assets_n, step,
                    asset_idx + 1, asset_idx_max,
                    allocation,
                    allocation_sum + next_asset_percent)
                allocation[asset_idx] = 0
    if 100 % step != 0:
        raise ValueError(f'cannot use step={step}, must be a divisor of 100')
    yield from _allocations_recursive(
        assets_n = assets_n, step = step,
        asset_idx = 0, asset_idx_max = assets_n - 1,
        allocation = [0] * assets_n,
        allocation_sum = 0)


def allocation_slice_simulate_and_feed_to_sink(slice_idx, slice_size, assets, percentage_step, asset_revenue_per_year, sink, chunk_size):
    portfolios_sent = 0
    with ThreadPoolExecutor() as thread_executor:
        possible_allocations_gen = all_possible_allocations(len(assets), percentage_step)
        gen_slice_allocations = islice(possible_allocations_gen, slice_idx * slice_size, (slice_idx + 1) * slice_size)
        gen_portfolios = map(partial(Portfolio, assets=assets), gen_slice_allocations)
        gen_simulateds = map(partial(Portfolio.simulated, asset_revenue_per_year=asset_revenue_per_year), gen_portfolios)
        gen_serializations = map(Portfolio.serialize, gen_simulateds)
        send_task = None
        for batch in batched(gen_serializations, chunk_size):
            if send_task is not None:
                send_task.result()
            send_task = thread_executor.submit(sink.send_bytes, b''.join(batch))
            portfolios_sent += len(batch)
        if send_task is not None:
            send_task.result()
    return portfolios_sent


def read_capitalgain_csv_data(filename):
    yearly_revenue_multiplier = {}  # year, ticker = cash multiplier
    # read csv values from tickers.csv
    rows = []
    with open(filename, "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = list(csv_reader)
    assets = rows[0][1:]
    for row in rows[1:]:
        if row[0] not in yearly_revenue_multiplier:
            yearly_revenue_multiplier[int(row[0])] = [0] * len(assets)
        for i in range(1, len(row)):
            yearly_revenue_multiplier[int(row[0])][i - 1] = \
                float(row[i].replace('%', '')) / 100 + 1
    return assets, yearly_revenue_multiplier


class DataStreamFinished:
    pass