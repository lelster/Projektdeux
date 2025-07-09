import pandas as pd
import os
from tqdm import tqdm

# === Config ===
file_path = "MQNM2025.csv.gz"
output_dir = "daily_output"
chunksize = 100_000
filter_dates = {"05/01/2025", "05/02/2025"}  # extend as needed

os.makedirs(output_dir, exist_ok=True)

usecols = [
    "Date", "Time", "GMT Offset",
    "L1-BidPrice", "L1-BidSize", "L1-BuyNo", "L1-AskPrice", "L1-AskSize", "L1-SellNo",
    "L2-BidPrice", "L2-BidSize", "L2-BuyNo", "L2-AskPrice", "L2-AskSize", "L2-SellNo",
    "L3-BidPrice", "L3-BidSize", "L3-BuyNo", "L3-AskPrice", "L3-AskSize", "L3-SellNo",
    "L4-BidPrice", "L4-BidSize", "L4-BuyNo", "L4-AskPrice", "L4-AskSize", "L4-SellNo",
    "L5-BidPrice", "L5-BidSize", "L5-BuyNo", "L5-AskPrice", "L5-AskSize", "L5-SellNo",
    "L6-BidPrice", "L6-BidSize", "L6-BuyNo", "L6-AskPrice", "L6-AskSize", "L6-SellNo",
    "L7-BidPrice", "L7-BidSize", "L7-BuyNo", "L7-AskPrice", "L7-AskSize", "L7-SellNo",
    "L8-BidPrice", "L8-BidSize", "L8-BuyNo", "L8-AskPrice", "L8-AskSize", "L8-SellNo",
    "L9-BidPrice", "L9-BidSize", "L9-BuyNo", "L9-AskPrice", "L9-AskSize", "L9-SellNo",
    "L10-BidPrice", "L10-BidSize", "L10-BuyNo", "L10-AskPrice", "L10-AskSize", "L10-SellNo"
]

# === Process ===
with tqdm(total=0, unit=' rows', dynamic_ncols=True) as pbar:
    for chunk in pd.read_csv(
        file_path,
        chunksize=chunksize,
        usecols=usecols,
        na_values=[''],
        keep_default_na=True,
        dtype=str,
        engine='c',
        on_bad_lines='skip'
    ):
        chunk = chunk[chunk["Date"].isin(filter_dates)]
        if chunk.empty:
            continue

        chunk["Hour"] = chunk["Time"].str.slice(0, 2)
        for (date, hour), hourly_data in chunk.groupby(["Date", "Hour"]):
            filename = f"{date.replace('/', '-')}.csv.gz"
            out_path = os.path.join(output_dir, filename)
            is_new = not os.path.exists(out_path)

            hourly_data.drop(columns=["Hour"]).to_csv(
                out_path,
                mode='a',
                index=False,
                header=is_new,
                compression="gzip"
            )

            print(f"✅ {date} {hour}:00 – wrote {len(hourly_data):,} rows to {filename}")
            pbar.update(len(hourly_data))
