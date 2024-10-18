#!/usr/bin/env python3

import multiprocessing.process
import os
import sys
import argparse
import config.config
import modules.pipeline as pipeline
import functools
import struct
import config
import multiprocessing
# import functools
import time
# import random
# from modules.data_output import report_errors_in_static_portfolios
# import modules.data_source as data_source
# import modules.data_filter as data_filter
# import modules.data_output as data_output
# import modules.data_generators as data_generators
# import modules.data_processors as data_processors
# from collections import deque
import itertools
# from modules.data_types import Portfolio
# from config.asset_colors import RGB_COLOR_MAP
# from config.static_portfolios import STATIC_PORTFOLIOS
from config.config import CHUNK_SIZE
from config.asset_colors import RGB_COLOR_MAP
# import pickle
import concurrent.futures as concurrent
# import json

import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s :: %(levelname)s :: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--asset-returns-csv', default='config/asset_returns.csv', help='path to csv with asset returns')
    parser.add_argument(
        '--precision', type=int, default=10,
        help='simulation precision, values less than 5 require A LOT of ram unless --hull is used')
    parser.add_argument(
        '--hull', type=int, default=0,
        help='use hull algorithm to draw only given layers'
             ' of edge portfolios, set to 0 to draw all portfolios')
    return parser.parse_args()

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main(argv):
    # pool = multiprocessing.Pool(processes=8)
    # points_n = 65535
    # repeats_n = 100
    # points = [(random.random(), random.random()) for _ in range(points_n)]
    # t1 = time.time()
    # for i in range(repeats_n):
    #     data_filter.multilayer_convex_hull(points, 1)
    # t2 = time.time()
    # print(f'multilayer_convex_hull: {t2 - t1:.2f}s rate {int(points_n*repeats_n/(t2-t1)/1000)}k/s')
    # points_xy = list(map(lambda point: Point(point[0],point[1]), points))
    # t1 = time.time()
    # for i in range(repeats_n):
    #     data_filter.convex_hull_filter1(points_xy)
    # t2 = time.time()
    # print(f'convex_hull_filter1: {t2 - t1:.2f}s rate {int(points_n*repeats_n/(t2-t1)/1000)}k/s')
    # t1 = time.time()
    # for i in range(repeats_n):
    #     data_filter.convex_hull_filter2(pool, points_xy)
    # t2 = time.time()
    # print(f'convex_hull_filter2: {t2 - t1:.2f}s rate {int(points_n*repeats_n/(t2-t1)/1000)}k/s')
    # return
    

    # top_n_funcs = [data_filter.top_n_filter_1, data_filter.top_n_filter_2, data_filter.top_n_filter_3, data_filter.top_n_filter_4, data_filter.top_n_filter_5]
    # for order in range(1, 10):
    #     length = 10**order
    #     list_of_random_ints = list(random.random() for _ in range(length))
    #     func_times = {}
    #     for func in top_n_funcs:
    #         func_times[func.__name__] = 0

    #         # check correctness
    #         correct_answer = list_of_random_ints.copy()
    #         correct_answer.sort(reverse=True)
    #         correct_answer = correct_answer[:10]
    #         correct_answer.sort()
    #         the_answer = sorted(func(list_of_random_ints.copy(), 10, lambda x: x))
    #         if the_answer != correct_answer:
    #             print(f'{func.__name__} returns {the_answer}')
    #             print(f'correct answer is {correct_answer}')
    #             return

    #         for _ in range(100):
    #             list_copy = list_of_random_ints.copy()
    #             t1 = time.time()
    #             func(list_copy, 10, lambda x: x)
    #             t2 = time.time()
    #             func_times[func.__name__] += t2 - t1
    #     print(order,'\t'.join(f'{func_name}={func_time:.3f}' for func_name, func_time in func_times.items()))

    # return

    # logger = logging.getLogger(__name__)
    # tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data('config/asset_returns.csv')
    # p = STATIC_PORTFOLIOS[-1]
    # p.simulate(yearly_revenue_multiplier)
    # number_of_sinks = 1
    # sinks = [
    #     dict(zip(('source', 'sink'), multiprocessing.Pipe(duplex=False))) for _ in range(number_of_sinks)
    # ]
    # feed_source, feed_sink = multiprocessing.Pipe(duplex=False)
    # process_wait_list = []
    # for sink in sinks:
    #     process_wait_list.append(multiprocessing.Process(
    #         target=data_source.source_exhauster,
    #         kwargs={
    #             'source': sink['source'],
    #         }
    #     ))
    # process_wait_list.append(multiprocessing.Process(
    #     target=data_filter.queue_multiplexer,
    #     kwargs={
    #         'source': feed_source,
    #         'sinks': list(pipe['sink'] for pipe in sinks),
    #     }
    # ))
    # data = pickle.dumps(p) * 100000
    # data = data[:128*1024] # appsrently 128k is the best size to send in one go
    # count = 30000*2*2
    # t1 = time.time()
    # deque(map(multiprocessing.Process.start, process_wait_list), 0)
    # data_source.sink_feeder(feed_sink, data, count)
    # deque(map(multiprocessing.Process.join, process_wait_list), 0)
    # t2 = time.time()
    # total = len(data) * count
    # logger.info(f'performance ({len(data)}) : {int(total/(t2 - t1)/1000000):d}M/s')
    # return

    # logger = logging.getLogger(__name__)
    # tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data('config/asset_returns.csv')
    # p = STATIC_PORTFOLIOS[-1]
    # p.simulate(yearly_revenue_multiplier)
    # t1 = time.time()
    # count = 0
    # while time.time() - t1 < 10:
    #     Portfolio.deserialize(p.serialize())
    #     count += 1
    # t2 = time.time()
    # logger.info(f'performance: {int(count/(t2 - t1)/1000):.2f}k/s')
    # return

    # logger = logging.getLogger(__name__)
    # tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data('config/asset_returns.csv')
    # t1 = time.time()
    # N = 20000000
    # deque(itertools.islice(data_source.all_possible_allocations(list(tickers_to_test), 1), N), maxlen=0)
    # t2 = time.time()
    # logger.info(f'Time to generate all possible allocations: {t2 - t1:.2f}s ({int(N/(t2-t1)/1000):d}k/s)')
    # sys.exit(0)

    # logger = logging.getLogger(__name__)
    # tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data('config/asset_returns.csv')
    # t1 = time.time()
    # N = 1000000
    # deque(map(
    #     functools.partial(data_source.allocation_to_simulated, ticker_revenue_per_year=yearly_revenue_multiplier),
    #     itertools.islice(data_source.all_possible_allocations(list(tickers_to_test), 1), N)), maxlen=0)
    # t2 = time.time()
    # logger.info(f'Time to generate all possible allocations: {t2 - t1:.2f}s ({int(N/(t2-t1)/1000):d}k/s)')
    # sys.exit(0)

    # logger = logging.getLogger(__name__)
    # pool = multiprocessing.Pool()
    # tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data('config/asset_returns.csv')
    # N = 1000000
    # simulated_portfolios = pool.map(
    #     functools.partial(data_source.allocation_simulate, assets=tickers_to_test, asset_revenue_per_year=yearly_revenue_multiplier),
    #     itertools.islice(data_source.all_possible_allocations(list(tickers_to_test), 1), N)
    # )
    # simulated_points = map(functools.partial(data_filter.PortfolioXYPoint, coord_pair=('CAGR(%)', 'Stdev')), simulated_portfolios)
    # logger.info(f'Total portfolios: {len(simulated_portfolios)}')
    # t1 = time.time()
    # filtered_portfolios = []
    # for batch in itertools.batched(simulated_points, CHUNK_SIZE):
    #     filtered_portfolios.extend(data_filter.multigon_filter(batch))
    # portfolios = data_filter.multigon_filter(filtered_portfolios)
    # logger.info(f'Total portfolios: {len(portfolios)}')
    # t2 = time.time()
    # logger.info(f'Time to generate all possible allocations: {t2 - t1:.2f}s ({int(N/(t2-t1)/1000):d}k/s)')
    # sys.exit(0)

    # return

    logger = logging.getLogger(__name__)
    cmdline_args = _parse_args(argv)

    time_start = time.time()
    time_last = time_start

    # process_pool = concurrent.ProcessPoolExecutor(os.cpu_count())
    process_pool = multiprocessing.Pool(processes=os.cpu_count())
    thread_pool = concurrent.ThreadPoolExecutor()

    asset_names, asset_revenue_per_year = pipeline.read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    time_now = time.time()
    logger.info(f'+{time_now - time_last:.2f}s : pools ready')
    time_last = time.time()

    all_allocs = pipeline.all_possible_allocations(assets_num=len(asset_names), step=cmdline_args.precision)
    total_allocations = sum(1 for _ in all_allocs)

    time_now = time.time()
    logger.info(f'+{time_now - time_last:.2f}s : {total_allocations} allocations counted, rate: {int(total_allocations/(time_now-time_last)/1000):d}k/s')
    # time_last = time_now

    # (167+163+158)/3 = 162k/s # CHUNK/cores
    # (149+156+154)/3 = 153k/s  # CHUNK * cores
    # portfolios_saved, packed_batch_size = pipeline.simulate_and_save_to_file(
    #     thread_pool=thread_pool,
    #     process_pool=process_pool,
    #     asset_names=asset_names,
    #     asset_revenue_per_year=asset_revenue_per_year,
    #     precision=cmdline_args.precision)

    # (179+177+173)/3 = 176k/s
    portfolios_saved, packed_batch_size = pipeline.simulate_and_save_to_file_slices(
        process_pool=process_pool,
        allocations_n=total_allocations,
        assets_n=len(asset_names),
        asset_revenue_per_year=asset_revenue_per_year,
        precision=cmdline_args.precision)

    # time.sleep(1)
    # portfolios_saved = 10000000
    # packed_batch_size = 60

    time_now = time.time()
    logger.info(f'+{time_now - time_last:.2f}s : {portfolios_saved} portfolios simulated, rate: {int(portfolios_saved/(time_now-time_last)/1000):d}k/s')
    # time_last = time_now

    # pack_size = 60
    # func_deserialize = functools.partial(pipeline.deserialize_bytes, record_size=pack_size, format=f'{len(asset_names)+5}f')
    # func_allocation_to_xy_point = functools.partial(pipeline.convex_hull_tuple_points, x_name='CAGR(%)', y_name='Stddev', assets_n=len(asset_names))

    coords_tuples = [
        # Y, X
        ('CAGR(%)', 'Variance'),
        ('CAGR(%)', 'Stddev'),
        ('CAGR(%)', 'Sharpe'),
        # ('Gain(x)', 'Variance'),
        # ('Gain(x)', 'Stdev'),
        # ('Gain(x)', 'Sharpe'),
        ('Sharpe', 'Stddev'),
        ('Sharpe', 'Variance'),
        # ('Sharpe', 'Gain(x)'),
        # ('Sharpe', 'CAGR(%)'),
    ]
    # coords_tuples = [
    #     # Y, X
    #     ('CAGR(%)', 'Stddev'),
    # ]
    plot_data_future = []
    for stat_y, stat_x in coords_tuples:
        plot_data_future.append(thread_pool.submit(pipeline.calculate_plot_data_from_file_cache,
            asset_names=asset_names,
            pack_size=packed_batch_size,
            thread_pool=thread_pool,
            process_pool=process_pool,
            hull=cmdline_args.hull,
            stat_x=stat_x,
            stat_y=stat_y,
        ))
    plots = []
    for idx, plot_data in enumerate(plot_data_future):
        plot_datas = plot_data.result()
        stat_x = coords_tuples[idx][1]
        stat_y = coords_tuples[idx][0]
        plots.append(multiprocessing.Process(None,
            pipeline.draw_circles_with_tooltips,
            args=(
                plot_datas,
                stat_x, stat_y, f'{stat_y} vs {stat_x}',
                'result', f'{stat_y} - {stat_x}',
                dict(RGB_COLOR_MAP.items()), False
            )
        ))
    logger.info(f'Plotting {len(plots)} plots')
    for plot in plots:
        plot.start()
    logger.info(f'Waiting for {len(plots)} plots to finish')
    for plot in plots:
        plot.join()

    time_now = time.time()
    logger.info(f'+{time_now - time_last:.2f}s : {portfolios_saved} portfolios processed, rate: {int(portfolios_saved/(time_now-time_last)/1000):d}k/s')
    time_last = time_now

    # func_dict_allocation_to_list = functools.partial(pipeline.dict_allocation_to_list_allocation, market_assets=tickers_to_test)

    # errors = data_processors.validate_dict_allocations(dict_allocations=STATIC_PORTFOLIOS, market_assets=tickers_to_test)
    # if len(errors) > 0:
    #     logger.error(f'Found {len(errors)} invalid static portfolios: {"\n".join(errors)}')
    #     return

    # static_portfolios_as_lists = map(func_dict_allocation_to_list, STATIC_PORTFOLIOS)
    # static_portfolios_stats_packed = map(func_simulate_list_and_pack, static_portfolios_as_lists)

    # for s in static_portfolios_stats_packed:
    #     print(len(s),s)
        # print(list(zip(data_processors.simulate_stat_order,s)))

    # deserialized_static_portfolios = map(functools.partial(data_processors.deserialize, assets_n=len(tickers_to_test)), static_portfolios_stats_packed)

    # for s in deserialized_static_portfolios:
    #     print(s)
        # print(list(zip(data_processors.simulate_stat_order,s)))

    # plot_data = map(functools.partial(
    #         data_processors.compose_plot_data,
    #         assets=tickers_to_test,
    #         marker='X', plot_always=True,
    #         field_x='CAGR(%)', field_y='Stddev'),
    #     deserialized_static_portfolios)

    # for pd in plot_data:
    #     print(json.dumps(pd, indent=4))
    
    # data_output.draw_circles_with_tooltips(
    #     circles=list(plot_data),
    #     xlabel='CAGR(%)',
    #     ylabel='Stddev',
    #     title=f'{'CAGR(%)'} vs {'Stddev'}',
    #     directory='result',
    #     filename=f'CAGR - STDEV - DIRECT',
    #     asset_color_map=dict(RGB_COLOR_MAP),
    # )


    # data pipeline below

    # process_wait_list = []
    # logger = logging.getLogger(__name__)
    # cmdline_args = _parse_args(argv)
    # coords_tuples = [
    #     # Y, X
    #     ('CAGR(%)', 'Variance'),
    #     ('CAGR(%)', 'Stdev'),
    #     ('CAGR(%)', 'Sharpe'),
    #     # ('Gain(x)', 'Variance'),
    #     # ('Gain(x)', 'Stdev'),
    #     # ('Gain(x)', 'Sharpe'),
    #     ('Sharpe', 'Stdev'),
    #     ('Sharpe', 'Variance'),
    #     # ('Sharpe', 'Gain(x)'),
    #     # ('Sharpe', 'CAGR(%)'),
    # ]

    # time_start = time.time()
    # tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    # num_errors = report_errors_in_static_portfolios(portfolios=STATIC_PORTFOLIOS, tickers_to_test=tickers_to_test)
    # if num_errors > 0:
    #     logger.error(f'Found {num_errors} invalid static portfolios')
    #     return
    # if (not all(ticker in RGB_COLOR_MAP.keys() for ticker in tickers_to_test)):
    #     logger.error(f'Some tickers in {cmdline_args.asset_returns_csv} are not in RGB_COLOR_MAP: {set(tickers_to_test) - set(RGB_COLOR_MAP.keys())}')
    #     return

    # static_portfolios_simulated = list(map(
    #     functools.partial(Portfolio.simulate, asset_revenue_per_year=yearly_revenue_multiplier),
    #     STATIC_PORTFOLIOS))
    # logger.info(f'{len(static_portfolios_simulated)} static portfolios will be plotted on all graphs')
    # edge_portfolios_simulated = list(map(
    #     functools.partial(data_source.allocation_simulate, assets=tickers_to_test, asset_revenue_per_year=yearly_revenue_multiplier),
    #     data_source.all_possible_allocations(tickers_to_test, 100)))
    # logger.info(f'{len(edge_portfolios_simulated)} edge portfolios will be plotted on all graphs')

    # logger.info(f'+{time.time() - time_start:.2f}s :: preparing portfolio simulation data pipeline...')
    # portfolios_simulated_source, portfolios_simulated_sink = multiprocessing.Pipe(duplex=False)
    # process_wait_list.append(multiprocessing.Process(
    #     target=data_source.simulated_q,
    #     kwargs={
    #         'assets': tickers_to_test,
    #         'percentage_step': cmdline_args.precision,
    #         'asset_revenue_per_year': yearly_revenue_multiplier,
    #         'sink': portfolios_simulated_sink,
    #     }
    # ))


    # coord_tuple_queues = {
    #     coord_pair: dict(zip(('source', 'sink'), multiprocessing.Pipe(duplex=False))) for coord_pair in coords_tuples[:1]
    # }
    # process_wait_list.append(multiprocessing.Process(
    #     target=data_filter.queue_multiplexer,
    #     kwargs={
    #         'source': portfolios_simulated_source,
    #         'sinks': list(pipe['sink'] for pipe in coord_tuple_queues.values()),
    #     }
    # ))
    # for coord_pair in coords_tuples[:1]:
    #     process_wait_list.append(multiprocessing.Process(
    #         target=data_output.save_data,
    #         kwargs={
    #             'assets': tickers_to_test,
    #             'source': coord_tuple_queues[coord_pair]['source'],
    #             'persistent_portfolios': edge_portfolios_simulated + static_portfolios_simulated,
    #             'coord_pair': coord_pair,
    #             'hull_layers': cmdline_args.hull,
    #         }
    #     ))

    # logger.info(f'+{time.time() - time_start:.2f}s :: data pipeline prepared')

    # deque(map(multiprocessing.Process.start, process_wait_list), 0)
    # logger.info(f'+{time.time() - time_start:.2f}s :: all processes started')

    # deque(map(multiprocessing.Process.join, process_wait_list), 0)
    # logger.info(f'+{time.time() - time_start:.2f}s :: graphs ready')


if __name__ == '__main__':
    main(sys.argv)
