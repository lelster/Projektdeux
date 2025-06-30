import pandas as pd
import numpy as np

# === Config ===
file_path = "C:/projects/terminaltest/hourly_output2/05-01-2025_00.csv.gz"
take_profit_ticks = 20
stop_loss_ticks = 10
tick_size = 0.25
entry_threshold_ticks = 12
initial_balance = 100_000
per_contract_value = tick_size * 1  # adjust if needed

# === Load Data ===
df = pd.read_csv(file_path, dtype={"Time": str})
df["MidPrice"] = (df["L1-BidPrice"].astype(float) + df["L1-AskPrice"].astype(float)) / 2
df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors='coerce')
df.dropna(subset=["MidPrice", "Timestamp"], inplace=True)
df.sort_values("Timestamp", inplace=True)

# === VWAP ===
df["Price"] = df["MidPrice"]
df["Volume"] = df["L1-BidSize"].astype(float) + df["L1-AskSize"].astype(float)
df["PV"] = df["Price"] * df["Volume"]
df["VWAP"] = df["PV"].cumsum() / df["Volume"].cumsum()

# === Strategy ===
trades = []
position = None

for i in range(len(df)):
    row = df.iloc[i]
    price = row["MidPrice"]
    vwap = row["VWAP"]
    time = row["Timestamp"]

    if position is None:
        if price < vwap - entry_threshold_ticks * tick_size:
            position = {"type": "long", "entry_price": price, "entry_time": time}
        elif price > vwap + entry_threshold_ticks * tick_size:
            position = {"type": "short", "entry_price": price, "entry_time": time}
    else:
        exit_trade = False
        if position["type"] == "long":
            if price >= position["entry_price"] + take_profit_ticks * tick_size:
                result = "TP"
                profit_ticks = take_profit_ticks
                exit_trade = True
            elif price <= position["entry_price"] - stop_loss_ticks * tick_size:
                result = "SL"
                profit_ticks = -stop_loss_ticks
                exit_trade = True
        elif position["type"] == "short":
            if price <= position["entry_price"] - take_profit_ticks * tick_size:
                result = "TP"
                profit_ticks = take_profit_ticks
                exit_trade = True
            elif price >= position["entry_price"] + stop_loss_ticks * tick_size:
                result = "SL"
                profit_ticks = -stop_loss_ticks
                exit_trade = True

        if exit_trade:
            trades.append({
                "side": position["type"],
                "entry_time": position["entry_time"],
                "entry_price": position["entry_price"],
                "exit_time": time,
                "exit_price": price,
                "result": result,
                "profit_ticks": profit_ticks,
                "profit_usd": profit_ticks * per_contract_value
            })
            position = None

# === Results ===
trades_df = pd.DataFrame(trades)
total_profit = trades_df["profit_usd"].sum() if not trades_df.empty else 0
winrate = (trades_df["profit_usd"] > 0).mean() * 100 if not trades_df.empty else 0

print("✅ Trades executed:", len(trades_df))
print(f"💰 Total Profit: ${total_profit:.2f}")
print(f"📈 Winrate: {winrate:.2f}%")
