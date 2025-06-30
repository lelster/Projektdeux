import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import random
import glob
import os

# === Config ===
data_folder = "C:/projects/terminaltest/hourly_output2"
take_profit_ticks = 10
trailing_ticks = 5
tick_size = 0.25
initial_balance = 100_000
contract_size = 1

# === Load only first 6 hours (00 to 05) ===
file_list = []
for i in range(3):
    hour_str = f"{i:02d}"
    pattern = os.path.join(data_folder, f"*_{hour_str}.csv.gz")
    file_list.extend(glob.glob(pattern))

file_list = sorted(file_list)
if not file_list:
    print("No matching files found.")
    exit()

print(f"✅ Loading files: {file_list}")

df_list = [pd.read_csv(file, dtype={"Time": str}) for file in file_list]
df = pd.concat(df_list, ignore_index=True)
print(f"✅ Loaded {len(df):,} rows across 6 hours.")

# === Preprocessing ===
df["MidPrice"] = (df["L1-BidPrice"].astype(float) + df["L1-AskPrice"].astype(float)) / 2
df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors='coerce')
df.dropna(subset=["MidPrice", "Timestamp"], inplace=True)
df.sort_values("Timestamp", inplace=True)

# === Strategy ===
trades = []
position = None
balance = initial_balance

for i in range(len(df)):
    row = df.iloc[i]
    bid = row["L1-BidPrice"]
    ask = row["L1-AskPrice"]
    mid = row["MidPrice"]
    time = row["Timestamp"]

    if position is not None:
        # Update max favorable price for trailing
        if position["type"] == "long":
            if mid > position["max_fav_price"]:
                position["max_fav_price"] = mid
            trail_price = position["max_fav_price"] - trailing_ticks * tick_size
            if mid >= position["entry_price"] + take_profit_ticks * tick_size or mid <= trail_price:
                exit_price = bid
                profit_ticks = (exit_price - position["entry_price"]) / tick_size
                profit_usd = profit_ticks * tick_size * contract_size
                trades.append({
                    "side": position["type"],
                    "entry_time": position["entry_time"],
                    "entry_price": position["entry_price"],
                    "exit_time": time,
                    "exit_price": exit_price,
                    "profit_ticks": profit_ticks,
                    "profit_usd": profit_usd
                })
                balance += profit_usd
                position = None

        elif position["type"] == "short":
            if mid < position["max_fav_price"]:
                position["max_fav_price"] = mid
            trail_price = position["max_fav_price"] + trailing_ticks * tick_size
            if mid <= position["entry_price"] - take_profit_ticks * tick_size or mid >= trail_price:
                exit_price = ask
                profit_ticks = (position["entry_price"] - exit_price) / tick_size
                profit_usd = profit_ticks * tick_size * contract_size
                trades.append({
                    "side": position["type"],
                    "entry_time": position["entry_time"],
                    "entry_price": position["entry_price"],
                    "exit_time": time,
                    "exit_price": exit_price,
                    "profit_ticks": profit_ticks,
                    "profit_usd": profit_usd
                })
                balance += profit_usd
                position = None

    if position is None:
        if random.random() < 0.5:
            position = {
                "type": "long",
                "entry_price": ask,
                "entry_time": time,
                "max_fav_price": mid
            }
        else:
            position = {
                "type": "short",
                "entry_price": bid,
                "entry_time": time,
                "max_fav_price": mid
            }

# === Results ===
trades_df = pd.DataFrame(trades)
if not trades_df.empty:
    trades_df["cum_pnl"] = trades_df["profit_usd"].cumsum()
    total_profit = trades_df["profit_usd"].sum()
    winrate = (trades_df["profit_usd"] > 0).mean() * 100
    avg_win = trades_df[trades_df["profit_usd"] > 0]["profit_usd"].mean()
    avg_loss = trades_df[trades_df["profit_usd"] <= 0]["profit_usd"].mean()
else:
    total_profit = 0
    winrate = 0
    avg_win = 0
    avg_loss = 0

print("\n=== Trailing TP Strategy Results ===")
print(f"Trades Executed: {len(trades_df)}")
print(f"Final Balance: ${balance:,.2f}")
print(f"Total Profit: ${total_profit:,.2f}")
print(f"Win Rate: {winrate:.1f}%")
print(f"Avg Win: ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f}")
print(f"Profit Factor: {abs(avg_win / avg_loss):.2f}" if avg_loss != 0 else "Profit Factor: ∞")

# === Visualization ===
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    subplot_titles=("MidPrice Tick Chart with Trailing TP Strategy Trades", "Cumulative Profit/Loss"))

# Price trace
fig.add_trace(go.Scatter(
    x=df["Timestamp"], y=df["MidPrice"],
    mode="lines", name="MidPrice", line=dict(color="lightgray")
), row=1, col=1)

# Trades markers
for _, trade in trades_df.iterrows():
    entry_color = "green" if trade["side"] == "long" else "red"
    exit_color = "lime" if trade["profit_usd"] >= 0 else "orange"
    symbol = "triangle-up" if trade["side"] == "long" else "triangle-down"

    fig.add_trace(go.Scatter(
        x=[trade["entry_time"]], y=[trade["entry_price"]],
        mode="markers", marker=dict(color=entry_color, symbol=symbol, size=10),
        name="Entry", showlegend=False
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=[trade["exit_time"]], y=[trade["exit_price"]],
        mode="markers", marker=dict(color=exit_color, symbol="x", size=8),
        name="Exit", showlegend=False
    ), row=1, col=1)

# PnL Curve
fig.add_trace(go.Scatter(
    x=trades_df["exit_time"], y=trades_df["cum_pnl"],
    mode="lines+markers", name="Cumulative PnL", line=dict(color="gold")
), row=2, col=1)

# Layout
fig.update_layout(
    height=800,
    template="plotly_dark",
    title="Backtest Result: Trailing TP Strategy on First 6 Hours",
    xaxis2_title="Time",
    yaxis_title="Price",
    yaxis2_title="PnL ($)"
)

fig.show()