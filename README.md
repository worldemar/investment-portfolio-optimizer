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

main-performance
precision=5 hull=3:
processes=16
DONE :: 888037 portfolios tested in 11.50s, rate: 77k/s
--- Graph ready: CAGR % - Variance --- 1.85s
--- Graph ready: Sharpe - Variance --- 1.06s
--- Graph ready: CAGR % - Stdev --- 1.55s
--- Graph ready: Sharpe - Stdev --- 1.21s
--- Graph ready: CAGR % - Sharpe --- 0.85s
DONE :: in 60.26s, rate = 14k/s

map-pipeline branch
precision=5 hull=3:
2024-09-12 17:28:06 :: INFO :: 7 static portfolios will be plotted on all graphs
2024-09-12 17:28:09 :: INFO :: +3.07s :: simulated portfolios map ready
2024-09-12 17:29:25 :: INFO :: +79.49s :: hulls ready
2024-09-12 17:29:26 :: INFO :: +79.61s :: plot data ready
2024-09-12 17:29:26 :: INFO :: Plot ready: result\CAGR(%) - Sharpe new.png
2024-09-12 17:29:26 :: INFO :: Plot ready: result\Gain(x) - Sharpe new.png
2024-09-12 17:29:26 :: INFO :: Plot ready: result\Sharpe - Stdev new.png
2024-09-12 17:29:26 :: INFO :: Plot ready: result\Sharpe - Variance new.png
2024-09-12 17:29:26 :: INFO :: Plot ready: result\CAGR(%) - Stdev new.png
2024-09-12 17:29:26 :: INFO :: Plot ready: result\Gain(x) - Stdev new.png
2024-09-12 17:29:26 :: INFO :: Plot ready: result\Gain(x) - Variance new.png
2024-09-12 17:29:26 :: INFO :: Plot ready: result\CAGR(%) - Variance new.png
2024-09-12 17:29:27 :: INFO :: Plot ready: result\Gain(x) - Sharpe new.svg
2024-09-12 17:29:27 :: INFO :: Plot ready: result\CAGR(%) - Sharpe new.svg
2024-09-12 17:29:27 :: INFO :: Plot ready: result\Sharpe - Gain(x) new.png
2024-09-12 17:29:27 :: INFO :: Plot ready: result\Sharpe - CAGR(%) new.png
2024-09-12 17:29:27 :: INFO :: Plot ready: result\Sharpe - Stdev new.svg
2024-09-12 17:29:27 :: INFO :: Plot ready: result\Sharpe - Variance new.svg
2024-09-12 17:29:28 :: INFO :: Plot ready: result\Sharpe - Gain(x) new.svg
2024-09-12 17:29:28 :: INFO :: Plot ready: result\Gain(x) - Stdev new.svg
2024-09-12 17:29:28 :: INFO :: Plot ready: result\Sharpe - CAGR(%) new.svg
2024-09-12 17:29:28 :: INFO :: Plot ready: result\CAGR(%) - Stdev new.svg
2024-09-12 17:29:28 :: INFO :: Plot ready: result\Gain(x) - Variance new.svg
2024-09-12 17:29:28 :: INFO :: Plot ready: result\CAGR(%) - Variance new.svg
2024-09-12 17:29:28 :: INFO :: +82.27s :: graphs ready

2024-09-30 10:56:49 :: INFO :: 7 static portfolios will be plotted on all graphs
2024-09-30 10:56:49 :: INFO :: 10 edge portfolios will be plotted on all graphs
2024-09-30 10:56:49 :: INFO :: +0.00s :: preparing portfolio simulation data pipeline...
2024-09-30 10:56:49 :: INFO :: +0.00s :: data pipeline prepared
2024-09-30 10:56:49 :: INFO :: +0.31s :: all processes started
2024-09-30 10:59:43 :: INFO :: Plot ready: result\CAGR(%) - Sharpe new.png
2024-09-30 10:59:44 :: INFO :: Plot ready: result\Sharpe - Stdev new.png
2024-09-30 10:59:44 :: INFO :: Plot ready: result\Sharpe - Variance new.png
2024-09-30 10:59:44 :: INFO :: Plot ready: result\CAGR(%) - Variance new.png
2024-09-30 10:59:44 :: INFO :: Plot ready: result\CAGR(%) - Stdev new.png
2024-09-30 10:59:45 :: INFO :: Plot ready: result\CAGR(%) - Sharpe new.svg
2024-09-30 10:59:45 :: INFO :: Plot ready: result\Sharpe - Stdev new.svg
2024-09-30 10:59:45 :: INFO :: Plot ready: result\Sharpe - Variance new.svg
2024-09-30 10:59:48 :: INFO :: Plot ready: result\CAGR(%) - Stdev new.svg
2024-09-30 10:59:48 :: INFO :: Plot ready: result\CAGR(%) - Variance new.svg
2024-09-30 10:59:48 :: INFO :: +179.32s :: graphs ready

2024-10-06 11:28:49 :: INFO :: 7 static portfolios will be plotted on all graphs
2024-10-06 11:28:49 :: INFO :: 10 edge portfolios will be plotted on all graphs
2024-10-06 11:28:49 :: INFO :: +0.00s :: preparing portfolio simulation data pipeline...
2024-10-06 11:28:49 :: INFO :: +0.00s :: data pipeline prepared
2024-10-06 11:28:49 :: INFO :: +0.05s :: all processes started
2024-10-06 11:30:03 :: INFO :: Simulated 10015005 portfolios, rate: 137205/s
2024-10-06 11:30:14 :: INFO :: Plot ready: result\CAGR(%) - Sharpe - ConvexHull1.png
2024-10-06 11:30:14 :: INFO :: Plot ready: result\Sharpe - Stdev - ConvexHull1.png
2024-10-06 11:30:14 :: INFO :: Plot ready: result\Sharpe - Variance - ConvexHull1.png
2024-10-06 11:30:14 :: INFO :: Plot ready: result\CAGR(%) - Stdev - ConvexHull1.png
2024-10-06 11:30:14 :: INFO :: Plot ready: result\CAGR(%) - Variance - ConvexHull1.png
2024-10-06 11:30:14 :: INFO :: Plot ready: result\CAGR(%) - Sharpe - ConvexHull1 new.svg
2024-10-06 11:30:14 :: INFO :: Plot ready: result\Sharpe - Stdev - ConvexHull1 new.svg
2024-10-06 11:30:14 :: INFO :: Plot ready: result\Sharpe - Variance - ConvexHull1 new.svg
2024-10-06 11:30:14 :: INFO :: Plot ready: result\CAGR(%) - Stdev - ConvexHull1 new.svg
2024-10-06 11:30:15 :: INFO :: Plot ready: result\CAGR(%) - Variance - ConvexHull1 new.svg
2024-10-06 11:30:15 :: INFO :: +85.55s :: graphs ready

2024-10-06 11:31:06 :: INFO :: 7 static portfolios will be plotted on all graphs
2024-10-06 11:31:06 :: INFO :: 10 edge portfolios will be plotted on all graphs
2024-10-06 11:31:06 :: INFO :: +0.00s :: preparing portfolio simulation data pipeline...
2024-10-06 11:31:06 :: INFO :: +0.00s :: data pipeline prepared
2024-10-06 11:31:06 :: INFO :: +0.04s :: all processes started
2024-10-06 11:32:19 :: INFO :: Simulated 10015005 portfolios, rate: 137309/s
2024-10-06 11:34:10 :: INFO :: Plot ready: result\CAGR(%) - Sharpe - ConvexHull5.png
2024-10-06 11:34:10 :: INFO :: Plot ready: result\Sharpe - Stdev - ConvexHull5.png
2024-10-06 11:34:10 :: INFO :: Plot ready: result\Sharpe - Variance - ConvexHull5.png
2024-10-06 11:34:10 :: INFO :: Plot ready: result\CAGR(%) - Stdev - ConvexHull5.png
2024-10-06 11:34:11 :: INFO :: Plot ready: result\CAGR(%) - Sharpe - ConvexHull5 new.svg
2024-10-06 11:34:11 :: INFO :: Plot ready: result\CAGR(%) - Variance - ConvexHull5.png
2024-10-06 11:34:12 :: INFO :: Plot ready: result\Sharpe - Stdev - ConvexHull5 new.svg
2024-10-06 11:34:12 :: INFO :: Plot ready: result\Sharpe - Variance - ConvexHull5 new.svg
2024-10-06 11:34:13 :: INFO :: Plot ready: result\CAGR(%) - Stdev - ConvexHull5 new.svg
2024-10-06 11:34:15 :: INFO :: Plot ready: result\CAGR(%) - Variance - ConvexHull5 new.svg
2024-10-06 11:34:15 :: INFO :: +188.67s :: graphs ready

2024-10-07 01:37:35 :: INFO :: 7 static portfolios will be plotted on all graphs
2024-10-07 01:37:35 :: INFO :: 10 edge portfolios will be plotted on all graphs
2024-10-07 01:37:35 :: INFO :: +0.00s :: preparing portfolio simulation data pipeline...
2024-10-07 01:37:35 :: INFO :: +0.00s :: data pipeline prepared
2024-10-07 01:37:35 :: INFO :: +0.32s :: all processes started
2024-10-07 01:38:49 :: INFO :: Simulated 10015005 portfolios, rate: 135846/s
2024-10-07 01:41:59 :: INFO :: Plotting 45 portfolios
2024-10-07 01:41:59 :: INFO :: Plotting 43 portfolios
2024-10-07 01:41:59 :: INFO :: Plotting 39 portfolios
2024-10-07 01:42:00 :: INFO :: Plot ready: result\CAGR(%) - Variance - Multigon.png
2024-10-07 01:42:00 :: INFO :: Plotting 33 portfolios
2024-10-07 01:42:00 :: INFO :: Plotting 41 portfolios
2024-10-07 01:42:01 :: INFO :: Plot ready: result\CAGR(%) - Sharpe - Multigon.png
2024-10-07 01:42:01 :: INFO :: Plot ready: result\Sharpe - Stdev - Multigon.png
2024-10-07 01:42:01 :: INFO :: Plot ready: result\Sharpe - Variance - Multigon.png
2024-10-07 01:42:01 :: INFO :: Plot ready: result\CAGR(%) - Stdev - Multigon.png
2024-10-07 01:42:01 :: INFO :: +266.18s :: graphs read