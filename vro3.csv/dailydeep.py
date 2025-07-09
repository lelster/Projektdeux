import pandas as pd
import os
from tqdm import tqdm

# === Config ===
input_path = "MQNM2025.csv.gz"
output_dir = "parquet_output"
target_dates = {"05/01/2025", "05/02/2025"}
chunksize = 50_000  # Ultra-safe for 6GB RAM

# Only essential columns (adjust as needed)
usecols = ["Date", "Time"] + [
    f"L{i}-{field}" for i in range(1, 6)  # L1-L5 only
    for field in ["BidPrice", "BidSize", "AskPrice", "AskSize"]
]

# === Directory Preparation ===
def prepare_directories():
    """Create all possible date/hour directories in advance"""
    os.makedirs(output_dir, exist_ok=True)
    for date in target_dates:
        date_str = date.replace("/", "-")
        for hour in [f"{h:02d}" for h in range(24)]:
            os.makedirs(f"{output_dir}/date={date_str}/hour={hour}", exist_ok=True)

prepare_directories()

# === Processing ===
processed_dates = set()

with tqdm(desc="Processing", unit="rows") as pbar:
    for chunk in pd.read_csv(
        input_path,
        chunksize=chunksize,
        usecols=usecols,
        dtype={
            "Date": "category",
            "Time": "category",
            "L1-BidPrice": "float32",
            "L1-AskPrice": "float32",
            # Add other numeric columns
        },
        engine="c",
        on_bad_lines="skip"
    ):
        # Filter and process
        chunk = chunk[chunk["Date"].isin(target_dates)]
        if chunk.empty:
            continue
        
        # Extract hour
        hours = chunk["Time"].str[:2]
        
        # Process each date/hour combination
        for date in chunk["Date"].unique():
            date_str = date.replace("/", "-")
            date_mask = chunk["Date"] == date
            
            for hour in hours[date_mask].unique():
                hour_data = chunk[date_mask & (hours == hour)]
                hour_data.drop(columns=["Date", "Time"]).to_parquet(
                    f"{output_dir}/date={date_str}/hour={hour}/data.parquet",
                    engine="pyarrow",
                    compression="zstd",
                    index=False
                )
            
            processed_dates.add(date)
            if len(processed_dates) == len(target_dates):
                break
        
        pbar.update(len(chunk))
        if len(processed_dates) == len(target_dates):
            break

print(f"✅ Successfully processed dates: {processed_dates}")