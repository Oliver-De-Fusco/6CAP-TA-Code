import numpy as np
from pyparsing import rest_of_line
import yfinance as yf
import seaborn as sns
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import IchimokuLibrary
from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed
import random
import os
from datetime import timedelta
import traceback
import logging
import arch.bootstrap as ab

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(args):

    returns = args["returns"]

    block_length = ab.optimal_block_length(returns ** 2)["stationary"].iloc[0]

    bs = ab.StationaryBootstrap(block_length, returns, seed=44)

    trading_lengths = {
        'short': range(5,15,2),
        'medium': range(17,33,2),
        'long': range(35,65,2)
    }

    random.seed(44)

    # dataframe for results storage
    columns = []
    for strategy in IchimokuLibrary.STRATEGIES_L:
        ex = strategy[0]
        en_list = strategy[1]
        for en in en_list:
            for measure in ["mu", "sigma","Sharpe"]:
                columns.append((ex, en, measure))

    multi_index_columns = pd.MultiIndex.from_tuples(columns)
    multi_index_index = pd.MultiIndex.from_tuples(product(trading_lengths['short'], trading_lengths['medium'],trading_lengths["long"], ["Lower", "Upper"]))

    trading_ci = pd.DataFrame(columns=multi_index_columns, index=multi_index_index)
    trading_ci.to_excel(file_name)
    trading_ci = pd.read_excel(file_name,header=[0,1,2], index_col=[0,1,2,3])

    if "btc" in file_name:
        days = 365
    else:
        days = 252

    jobs = product(
        [bs],
        [IchimokuLibrary.sharpe_ratio],
        trading_lengths['short'], 
        trading_lengths['medium'],
        trading_lengths["long"],
        ((exit, x) for exit, _entry in IchimokuLibrary.STRATEGIES_L for x in _entry),
        [days])

    # list(jobs)
    queue = []
    for job in jobs:
        # print(job[1])
        short, medium, long, strategy = job[2:6]
        position = {"short":short, "medium": medium, "long":long, "exit":strategy[0], "entry":strategy[1]}
        if pd.isna(trading_ci.loc[(position["short"], position["medium"], position["long"], "Lower"), (position["exit"], position["entry"], "mu")]):
            queue.append(job)


    with ProcessPoolExecutor(max_workers=os.process_cpu_count()-1) as executor:

        futures = []
        for job in queue:
            short, medium, long, strategy = job[2:6]
            position = {"short":short, "medium": medium, "long":long, "exit":strategy[0], "entry":strategy[1], "days":job[6]}

            if pd.isna(trading_ci.loc[(position["short"], position["medium"], position["long"], "Lower"), (position["exit"], position["entry"], "mu")]):
                futures.append(executor.submit(IchimokuLibrary.confidence_interval, *job))
                # print(f"{datetime.now().strftime('%H:%M:%S')} - Added : {job}")
            else:
                print(f"{datetime.now().strftime('%H:%M:%S')} - Skipped : {job}")

        total = len(futures)
        count = 0
        write_count = 0
        start_time = datetime.now()
        print(f"{datetime.now().strftime('%H:%M:%S')} - {count}/{total} : {round((count/total)*100,3)}%")

        for future in as_completed(futures):
            try:
                result = future.result()
                position = result[0]
                data = result[1]

                if (data[0][2] + data[1][2])/2 > 2:
                    logger.info(f"Sharpe above 2: {position}")
                    logger.info(f"\n{data}")

                trading_ci.loc[(position["short"], position["medium"], position["long"], "Lower"), (position["exit"], position["entry"], "mu")] = data[0][0]
                trading_ci.loc[(position["short"], position["medium"], position["long"], "Upper"), (position["exit"], position["entry"], "mu")] = data[1][1]

                trading_ci.loc[(position["short"], position["medium"], position["long"], "Lower"), (position["exit"], position["entry"], "sigma")] = data[0][1]
                trading_ci.loc[(position["short"], position["medium"], position["long"], "Upper"), (position["exit"], position["entry"], "sigma")] = data[1][1]

                trading_ci.loc[(position["short"], position["medium"], position["long"], "Lower"), (position["exit"], position["entry"], "Sharpe")] = data[0][2]
                trading_ci.loc[(position["short"], position["medium"], position["long"], "Upper"), (position["exit"], position["entry"], "Sharpe")] = data[1][2]

                if write_count >= 200:
                    trading_ci.to_excel(file_name)
                    logger.info(f"{datetime.now().strftime('%H:%M:%S')} - Written {write_count} to file")
                    write_count = 0

                count += 1
                write_count += 1

                elapsed = (datetime.now() - start_time)
                time_per_item = elapsed / count
                remaining_time = (time_per_item) * (total - count)
                logger.info(f"{datetime.now().strftime('%H:%M:%S')} - {count}/{total} : {round((count/total)*100,1)}% - {timedelta(seconds=remaining_time.total_seconds())}")

            except Exception as e:
                raise traceback.print_exc
                

        trading_ci.to_excel(file_name)

        print(f"Done - Started {start_time}, Finished {datetime.now()}")


if __name__ == "__main__":

    start_time = datetime.now()
    for file in ["data2","btcusd"]:
        for destination in ["no_transaction_costs/in_sample"]:
            data = pd.read_csv(f"{file}.csv", index_col=0, parse_dates=True)

            file_name = f"results/{destination}/{file}.xlsx"
            # data.drop(columns=["High", "Low", "Open", "Volume"])
            returns = np.log(data["Close"] / data["Close"].shift(1)).dropna()

            if destination == "out_of_sample":
                returns = returns["2022-01-01":]
            else:
                # Covid [:"2020-01-1"]
                # 70/30 split [:"2022-01-1"]
                returns = returns[:"2022-01-1"]

            inputs = {"file_name":file_name, "returns":returns}
            main(inputs)

    print(f"Finished all - Started {start_time}, Finished {datetime.now()}")
