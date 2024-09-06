[![Prospector](https://github.com/worldemar/investment-portfolio-optimizer/actions/workflows/linter.yml/badge.svg)](https://github.com/worldemar/investment-portfolio-optimizer/actions/workflows/linter.yml)
[![Code QL](https://github.com/worldemar/investment-portfolio-optimizer/actions/workflows/codeql.yml/badge.svg)](https://github.com/worldemar/investment-portfolio-optimizer/actions/workflows/codeql.yml)

### Investment portfolio optimizer

This simple script will simulate rebalancing portfolios with given set of assets and display statistics.

### How to use

- Install requirements via `python3 -m pip install -r requirements.txt`

- Save market data into [asset_returns.csv](asset_returns.csv) file. Each row is one rebalancing period, each column is revenue from corresponding asset. Look at example file for details.
- Open [asset_colors.py](asset_colors.py) and edit asset colors to your taste.
- Run `optimizer.py` with parameters:
  - `--precision=10` - Precision is specified in percent. Asset allocation will be stepped according to this value.
  - `--hull=3` - Use ConvexHull algorithm to select only edge-case portfolios. This considerably speeds up plotting.
     In most cases these portfolios are most interesting anyway. This settings is 0 by default.
     Note that in this case ALL portfolios will be drawn on SVG. Your browser might not be able to display it.

Results of edge case portfolios will be displayed in terminal.

Check SVG graphs in `result` folder for all portfolios performances.

### What does it actually do?

Script will generate all possible investment portfolios with every asset allocated from 0 to 100% stepping according to `--precision` parameter.

Then every portfolio is simulated through market history, rebalancing at every step. Rebalancing assumes selling all assets with new prices and buying them back according to portfolio's asset allocation. For example:

| Asset1  | Asset2  | Asset1 (20%)           | Asset2 (80%)           | Portfolio value            |
| ------- | ------- | ---------------------- | ---------------------- | -------------------------- |
| (start) | (start) | 0.2                    | 0.8                    | 1                          |
| -10%    |  25%    | 0.2 - 10% = 0.18       | 0.8 + 25% = 1          | 0.18 + 1 = 1.18            |
|         |         | 1.18 * 20% = 0.236     | 1.18 * 80% = 0.944     | 1.18 = 0.236 + 0.944       |
|  15%    |  -5%    | 0.236 + 15% = 0.2714   | 0.944 - 5% = 0.8968    | 0.2714 + 0.8968 = 1.1682   |
|         |         | 1.1682 * 20% = 0.23364 | 1.1682 * 80% = 0.93456 | 1.1682 = 0.23364 + 0.93456 |

If `--hull` is specified and is not zero, script will use ConvexHull algorithm to select only edge-case portfolios for
each plot. Edge cases are calculated separately for each plot.

### Demo SVGs
(You need to download them to enable interactivity)

<img src="./image-demos/cagr_variance.svg" width="50%"><img src="./image-demos/cagr_stdev.svg" width="50%">
<img src="./image-demos/gain_sharpe.svg" width="50%"><img src="./image-demos/sharpe_variance.svg" width="50%">

precision=10 hull=3 lists = DONE :: 15.46s


20-core i9-12900H

proc = concurrent.futures.ProcessPoolExecutor(workers=10)
thrd = concurrent.futures.ThreadPoolExecutor(workers=10)
chain = custom chaining based on concurrent.futures
chunk = add chunksize=1000 parameter

Execution time (s) for different mapping techniques (avg. 3 measurements)
Calls | proc.map(chunk)|   map| thrd.map(chunk)| thrd.map| thrd.chain(chunk)| thrd.chain| proc.map| proc.chain(chunk) | proc.chain|
----------------------------------------------------------------------------------------------------------------------|------------
  2^10|            0.05|  0.04|            0.06|     0.05|              0.05|       0.08|     0.26|               0.22|       0.40|
  2^11|            0.05|  0.09|            0.14|     0.10|              0.10|       0.18|     0.54|               0.42|       0.63|
  2^12|            0.06|  0.18|            0.23|     0.33|              0.36|       0.37|     0.95|               0.88|       1.74|
  2^13|            0.09|  0.36|            0.46|     0.56|              0.44|       0.70|     1.72|               1.67|       2.52|
  2^14|            0.15|  0.68|            1.14|     1.14|              1.47|       1.48|     3.37|               3.31|       6.73|
  2^15|            0.25|  1.34|            1.96|     2.10|              1.80|       2.83|     6.60|               6.72|      11.32|
  2^16|            0.48|  2.56|            5.54|     4.91|              4.83|       5.98|    25.08|              13.65|      24.20|
  2^17|            1.01|  5.36|           10.63|     8.84|              9.17|      11.56|    72.86|              27.44|      45.12|
  2^18|            1.83|  9.62|           18.15|    18.92|             18.85|      24.48|    54.63|              62.55|      97.85|
  2^19|            3.76| 19.97|            N/A |     N/A |              N/A |       N/A |     N/A |               N/A |       N/A |
  2^20|            7.42| 39.54|            N/A |     N/A |              N/A |       N/A |     N/A |               N/A |       N/A |