import pandas as pd
import os

file_path = "C:/Users/miezi/Downloads/MQNM2025.csv.gz"
output_dir = "hourly_output"
os.makedirs(output_dir, exist_ok=True)

chunksize = 1_000_000
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

# Keep track of which hours have already been saved
written_hours = set()

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
    chunk = chunk[chunk["Date"] == "05/01/2025"]
    if chunk.empty:
        continue

    chunk["Hour"] = chunk["Time"].str.slice(0, 2)  # extract "HH" from "HH:MM:SS.fff"
    for hour, hourly_data in chunk.groupby("Hour"):
        if hour not in written_hours:
            out_path = os.path.join(output_dir, f"2025-05-01_{hour}.csv.gz")
            hourly_data.drop(columns=["Hour"]).to_csv(out_path, index=False, compression="gzip")
            print(f"✅ Created {out_path} ({len(hourly_data)} rows)")
            written_hours.add(hour)

    if chunk["Time"].max() >= "23:59:59.999":
        break
