#!/usr/bin/env python3

import csv
from modules.Portfolio import Portfolio
import concurrent.futures
from functools import partial
import itertools
from config.config import CHUNK_SIZE
import queue

def allocation_simulate(asset_allocation, assets, asset_revenue_per_year):
    portfolio = Portfolio(assets=assets, weights=asset_allocation)
    portfolio.simulate(asset_revenue_per_year)
    return portfolio

def allocation_simulate_serialize(asset_allocation, assets, asset_revenue_per_year):
    portfolio = Portfolio(assets=assets, weights=asset_allocation)
    portfolio.simulate(asset_revenue_per_year)
    return portfolio.serialize()

def allocation_simulate_serialize_slice_to_sink(slice_idx, slice_size, assets, percentage_step, asset_revenue_per_year, sink):
    portfolios_sent = 0
    with concurrent.futures.ThreadPoolExecutor() as thread_executor:
        possible_allocations_gen = all_possible_allocations(assets, percentage_step)
        slice_gen = itertools.islice(possible_allocations_gen, slice_idx * slice_size, (slice_idx + 1) * slice_size)
        simulate_func = partial(allocation_simulate_serialize, assets=assets, asset_revenue_per_year=asset_revenue_per_year)
        simulated_portfolios = map(simulate_func, slice_gen)
        send_task = None
        for batch in itertools.batched(simulated_portfolios, CHUNK_SIZE):
            if send_task is not None:
                send_task.result()
            send_task = thread_executor.submit(sink.send_bytes, b''.join(batch))
            portfolios_sent += len(batch)
        if send_task is not None:
            send_task.result()
    return portfolios_sent


def all_possible_allocations(assets: list, step: int):
    def _allocations_recursive(
            assets: list, step: int,
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
                    assets, step,
                    asset_idx + 1, asset_idx_max,
                    allocation,
                    allocation_sum + next_asset_percent)
                allocation[asset_idx] = 0
    if 100 % step != 0:
        raise ValueError(f'cannot use step={step}, must be a divisor of 100')
    yield from _allocations_recursive(
        assets = assets, step = step,
        asset_idx = 0, asset_idx_max = len(assets) - 1,
        allocation = [0] * len(assets),
        allocation_sum = 0)

def all_possible_allocations_to_queue(assets: list, step: int, sink: queue.Queue):
    for possible_allocation in all_possible_allocations(assets, step):
        sink.put(possible_allocation)
    return

def queue_batched(future, source: queue.Queue, batch_size: int):
    chunk = []
    while not source.empty() and not future.done():
        chunk.append(source.get())
        if len(chunk) >= batch_size:
            yield chunk
            chunk = []
    if len(chunk) > 0:
        yield chunk

    # # allocation_limit = 10*1000*1000
    # # allocation_limit = 1000*1000
    # # allocation_limit = 200*1000
    # # allocation_limit = 10*1000

    # time_start = time.time()

    # # possible_allocations_gen = itertools.islice(all_possible_allocations(assets, percentage_step), allocation_limit)
    # possible_allocations_gen = all_possible_allocations(assets, percentage_step)
    # simulate_func = partial(allocation_simulate_serialize, assets=assets, asset_revenue_per_year=asset_revenue_per_year)
    # total_portfolios = 0
    # send_request = None
    # for possible_allocation_batch in queue_batched(allocations_future, allocations_queue, CHUNK_SIZE):
    #     simulated_portfolios_batch = process_pool.map(simulate_func, possible_allocation_batch)
    #     total_portfolios += len(simulated_portfolios_batch)
    #     bytes = b''.join(simulated_portfolios_batch)
    #     # if send_request is not None:
    #         # send_request.result()
    #     # send_request = thread_pool.submit(sink.send_bytes, bytes)
    # # send_request.result()
    # thread_pool.shutdown()
    # sink.send(data_types.DataStreamFinished())
    # logger.info(f'Simulated {total_portfolios} portfolios, rate: {int(total_portfolios / (time.time() - time_start))}/s')


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