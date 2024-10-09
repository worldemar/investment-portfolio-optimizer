#!/usr/bin/env python3

import sys
import argparse
import multiprocessing
import functools
import time
import random
from modules.data_output import report_errors_in_static_portfolios
import modules.data_source as data_source
import modules.data_filter as data_filter
import modules.data_output as data_output
from collections import deque
import itertools
from modules.data_types import Portfolio
from config.asset_colors import RGB_COLOR_MAP
from config.static_portfolios import STATIC_PORTFOLIOS
from config.config import CHUNK_SIZE
import pickle

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

    process_wait_list = []
    logger = logging.getLogger(__name__)
    cmdline_args = _parse_args(argv)
    coords_tuples = [
        # Y, X
        ('CAGR(%)', 'Variance'),
        ('CAGR(%)', 'Stdev'),
        ('CAGR(%)', 'Sharpe'),
        # ('Gain(x)', 'Variance'),
        # ('Gain(x)', 'Stdev'),
        # ('Gain(x)', 'Sharpe'),
        ('Sharpe', 'Stdev'),
        ('Sharpe', 'Variance'),
        # ('Sharpe', 'Gain(x)'),
        # ('Sharpe', 'CAGR(%)'),
    ]

    time_start = time.time()
    tickers_to_test, yearly_revenue_multiplier = data_source.read_capitalgain_csv_data(cmdline_args.asset_returns_csv)

    num_errors = report_errors_in_static_portfolios(portfolios=STATIC_PORTFOLIOS, tickers_to_test=tickers_to_test)
    if num_errors > 0:
        logger.error(f'Found {num_errors} invalid static portfolios')
        return
    if (not all(ticker in RGB_COLOR_MAP.keys() for ticker in tickers_to_test)):
        logger.error(f'Some tickers in {cmdline_args.asset_returns_csv} are not in RGB_COLOR_MAP: {set(tickers_to_test) - set(RGB_COLOR_MAP.keys())}')
        return

    static_portfolios_simulated = list(map(
        functools.partial(Portfolio.simulate, asset_revenue_per_year=yearly_revenue_multiplier),
        STATIC_PORTFOLIOS))
    logger.info(f'{len(static_portfolios_simulated)} static portfolios will be plotted on all graphs')
    edge_portfolios_simulated = list(map(
        functools.partial(data_source.allocation_simulate, assets=tickers_to_test, asset_revenue_per_year=yearly_revenue_multiplier),
        data_source.all_possible_allocations(tickers_to_test, 100)))
    logger.info(f'{len(edge_portfolios_simulated)} edge portfolios will be plotted on all graphs')

    logger.info(f'+{time.time() - time_start:.2f}s :: preparing portfolio simulation data pipeline...')
    portfolios_simulated_source, portfolios_simulated_sink = multiprocessing.Pipe(duplex=False)
    process_wait_list.append(multiprocessing.Process(
        target=data_source.simulated_q,
        kwargs={
            'assets': tickers_to_test,
            'percentage_step': cmdline_args.precision,
            'asset_revenue_per_year': yearly_revenue_multiplier,
            'sink': portfolios_simulated_sink,
        }
    ))


    coord_tuple_queues = {
        coord_pair: dict(zip(('source', 'sink'), multiprocessing.Pipe(duplex=False))) for coord_pair in coords_tuples[:1]
    }
    process_wait_list.append(multiprocessing.Process(
        target=data_filter.queue_multiplexer,
        kwargs={
            'source': portfolios_simulated_source,
            'sinks': list(pipe['sink'] for pipe in coord_tuple_queues.values()),
        }
    ))
    for coord_pair in coords_tuples[:1]:
        process_wait_list.append(multiprocessing.Process(
            target=data_output.save_data,
            kwargs={
                'assets': tickers_to_test,
                'source': coord_tuple_queues[coord_pair]['source'],
                'persistent_portfolios': edge_portfolios_simulated + static_portfolios_simulated,
                'coord_pair': coord_pair,
                'hull_layers': cmdline_args.hull,
            }
        ))

    logger.info(f'+{time.time() - time_start:.2f}s :: data pipeline prepared')

    deque(map(multiprocessing.Process.start, process_wait_list), 0)
    logger.info(f'+{time.time() - time_start:.2f}s :: all processes started')

    # data_output.plot_data(
    #     assets=tickers_to_test,
    #     source=portfolios_simulated_source,
    #     persistent_portfolios=edge_portfolios_simulated + static_portfolios_simulated,
    #     coord_pair=('CAGR(%)', 'Variance'),
    #     hull_layers=cmdline_args.hull,
    # )

    deque(map(multiprocessing.Process.join, process_wait_list), 0)
    logger.info(f'+{time.time() - time_start:.2f}s :: graphs ready')


if __name__ == '__main__':
    main(sys.argv)
