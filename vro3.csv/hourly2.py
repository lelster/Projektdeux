import pandas as pd
import os
from tqdm import tqdm

# === Config ===
file_path = "C:/projects/Projektdeux/MQNM2025(1).csv.gz"
output_dir = "hourly_output2_quotes"
chunksize = 1_000_000
filter_dates = {"05/01/2025"}  # extend this set as needed

os.makedirs(output_dir, exist_ok=True)

usecols = [
    "Date", "Time", "Price", "Volume"
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
            filename = f"{date.replace('/', '-')}_{hour}.csv.gz"
            out_path = os.path.join(output_dir, filename)
            is_new = not os.path.exists(out_path)

            hourly_data.drop(columns=["Hour"]).to_csv(
                out_path,
                mode='a',
                index=False,
                header=is_new,
                compression="gzip"
            )

            pbar.update(len(hourly_data))
