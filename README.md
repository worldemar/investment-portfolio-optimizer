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

main branch
precision=5 hull=3:
DONE :: 888037 portfolios tested in 15.35s
times: prepare = 3.00s, simulate = 12.36s
--- Graph ready: CAGR % - Variance --- 3.37s
--- Graph ready: Sharpe - Variance --- 1.18s
--- Graph ready: CAGR % - Stdev --- 1.65s
--- Graph ready: Sharpe - Stdev --- 1.20s
--- Graph ready: CAGR % - Sharpe --- 0.82s
DONE :: 70.09s

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