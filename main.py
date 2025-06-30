import pandas as pd
import os

# === CONFIG ===
file_path = "MQNM2025.csv.gz"
output_dir = "extracted_days"
chunksize = 3_000_000

dates_to_extract = {"05/01/2025", "05/02/2025"}

# Clean column list
levels = [f"L{i}" for i in range(1, 11)]
fields = ["BidPrice", "BidSize", "BuyNo", "AskPrice", "AskSize", "SellNo"]
usecols = ["Date", "Time", "GMT Offset"] + [f"{level}-{field}" for level in levels for field in fields]

os.makedirs(output_dir, exist_ok=True)

# Initialize writers
writers = {}

# === PROCESS ===
for chunk in pd.read_csv(
    file_path,
    chunksize=chunksize,
    usecols=usecols,
    dtype=str,
    engine='c',
    on_bad_lines='skip'
):
    # Filter only the dates we need
    chunk = chunk[chunk["Date"].isin(dates_to_extract)]
    if chunk.empty:
        continue

    # Write to separate files
    for date in dates_to_extract:
        date_data = chunk[chunk["Date"] == date]
        if date_data.empty:
            continue

        out_path = os.path.join(output_dir, f"{date.replace('/', '-')}.csv")
        mode = 'a' if os.path.exists(out_path) else 'w'
        header = not os.path.exists(out_path)

        date_data.to_csv(out_path, mode=mode, index=False, header=header)
        print(f"✅ Appended {len(date_data):,} rows to {out_path}")

print("✅ Extraction complete. You can now backtest immediately.")
