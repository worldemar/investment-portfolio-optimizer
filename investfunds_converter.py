#!/usr/bin/env python3

silver_data = {}
with open("MONEY - silver.csv", "r") as silver_f:
    for line in silver_f:
        line = line.strip()
        if line:
            silver_data[line.split(',')[0]] = float(line.split(',')[1].replace(" ", ""))

gold_data = {}
with open("MONEY - gold.csv", "r") as gold_f:
    for line in gold_f:
        line = line.strip()
        if line:
            gold_data[line.split(',')[0]] = float(line.split(',')[1].replace(" ", ""))

imoex_data = {}
with open("MONEY - imoex.csv", "r") as imoex_f:
    for line in imoex_f:
        line = line.strip()
        if line:
            imoex_data[line.split(',')[0]] = float(line.split(',')[1].replace(" ", ""))

gold_dates = sorted(gold_data.keys())
imoex_dates = sorted(imoex_data.keys())
silver_dates = sorted(silver_data.keys())
all_dates = sorted(set(gold_dates).intersection(imoex_dates).intersection(silver_dates))[::180]

with open('asset_returns.csv', 'w') as f:
    f.write('Date,IMOEX,GOLD,SILVER\n')
    prev_imoex = 0
    prev_gold = 0
    prev_silver = 0
    for date in all_dates:
        if not prev_imoex or not prev_gold:
            prev_imoex = imoex_data[date]
            prev_gold = gold_data[date]
            prev_silver = silver_data[date]
            continue
        imoex_gain_percent = (imoex_data[date] - prev_imoex) / prev_imoex * 100
        gold_gain_percent = (gold_data[date] - prev_gold) / prev_gold * 100
        silver_gain_percent = (silver_data[date] - prev_silver) / prev_silver * 100
        f.write(f'{date.replace("-","")},{imoex_gain_percent:.4f},{gold_gain_percent:.4f},{silver_gain_percent:.4f}\n')
        prev_imoex = imoex_data[date]
        prev_gold = gold_data[date]
        prev_silver = silver_data[date]