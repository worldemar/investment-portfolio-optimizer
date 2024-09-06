#!/usr/bin/env python3

import sys
import timeit
import itertools
import concurrent.futures
import functools
from collections import deque
from modules.data_pipeline import chain_generators, ParameterFormat
from modules.data_source import all_possible_allocations, all_possible_portfolios, static_portfolio_layers, read_capitalgain_csv_data
from modules.portfolio import Portfolio


def simulated_portfolio(asset_allocation, market_data):
    if asset_allocation.__class__.__name__ == 'list':
        asset_allocation = asset_allocation[0]
    portfolio = Portfolio(list(asset_allocation))
    portfolio.simulate(market_data)
    return portfolio


def exhaust_generator(gen):
    deque(gen, maxlen=0)  # twice as fast as for loop


def collect_one_perf_data_point(perf_data_size, measurements, tickers_to_test, market_data):
    process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=60)
    thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    performance_data_point = {}

    def _test_allocations():
        all_allocations = all_possible_allocations(assets=tickers_to_test, percentage_step=2)  # about 264M allocations
        return itertools.islice(all_allocations, perf_data_size)
    test_func = functools.partial(simulated_portfolio, market_data=market_data)

    for chunk_size in range(1, 20):
        performance_data_point[f'2^{chunk_size}'] = timeit.timeit(
            lambda: exhaust_generator(process_executor.map(test_func, _test_allocations(), chunksize=2**chunk_size)),
            number=measurements) / measurements
    # performance_data_point['proc.map(chunk)'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(process_executor.map(test_func, _test_allocations(), chunksize=1000)),
    # #     number=measurements) / measurements
    # performance_data_point['map'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(map(test_func, _test_allocations())),
    # #     number=measurements) / measurements
    # performance_data_point['thrd.map(chunk)'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(thread_executor.map(test_func, _test_allocations(), chunksize=1000)),
    # #     number=measurements) / measurements
    # performance_data_point['thrd.map'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(thread_executor.map(test_func, _test_allocations())),
    # #     number=measurements) / measurements
    # performance_data_point['thrd.chain(chunks)'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(chain_generators(executor=thread_executor, gens=[_test_allocations()], funcs=[test_func], chain_type=ParameterFormat.VALUE, chunk_size=1000)),
    # #     number=measurements) / measurements
    # performance_data_point['thrd.chain'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(chain_generators(executor=thread_executor, gens=[_test_allocations()], funcs=[test_func], chain_type=ParameterFormat.VALUE)),
    # #     number=measurements) / measurements
    # performance_data_point['proc.map'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(process_executor.map(test_func, _test_allocations())),
    # #     number=measurements) / measurements
    # performance_data_point['proc.chain(chunk)'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(chain_generators(executor=process_executor, gens=[_test_allocations()], funcs=[test_func], chain_type=ParameterFormat.VALUE, chunk_size=1000)),
    # #     number=measurements) / measurements
    # performance_data_point['proc.chain'] = 0
    # # timeit.timeit(
    # #     lambda: exhaust_generator(chain_generators(executor=process_executor, gens=[_test_allocations()], funcs=[test_func], chain_type=ParameterFormat.VALUE)),
    # #     number=measurements) / measurements


    thread_executor.shutdown()
    process_executor.shutdown()
    return performance_data_point

def main():
    tickers_to_test, yearly_revenue_multiplier = read_capitalgain_csv_data('asset_returns.csv')

    measurements = 3
    # title
    print(f'Execution time (s) for different mapping techniques (avg. {measurements} measurements)')

    # header
    performance_data_point_1 = collect_one_perf_data_point(
        perf_data_size=1,
        measurements=1,
        tickers_to_test=tickers_to_test,
        market_data=yearly_revenue_multiplier)
    column_width = len(max(performance_data_point_1.keys(), key=len)) + 1
    header = "|".join(
        [f"{'Data Size':>{column_width}s}"] + 
        [f"{key:>{column_width}s}" for key in performance_data_point_1.keys()]
    )
    print(header)
    print('-' * len(header))

    for perf_data_n in range(5, 20):
        perf_data_size = 2**perf_data_n
        performance_data_point = collect_one_perf_data_point(
            perf_data_size=perf_data_size,
            measurements=measurements,
            tickers_to_test=tickers_to_test,
            market_data=yearly_revenue_multiplier)
        print('|'.join(
            [f"{'2^'+str(perf_data_n):>{column_width}s}"] +
            [f"{performance_data_point[key]:>{column_width}.2f}" for key in performance_data_point.keys()]
        ))

if __name__ == '__main__':
    sys.exit(main())