import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# === Config ===
file_path = "C:/projects/terminaltest/hourly_output2/05-01-2025_15.csv.gz"
file_path_quotes = "C:/projects/terminaltest/hourly_output2_quotes/05-01-2025_15.csv.gz"
take_profit_ticks = 20
stop_loss_ticks = 10
tick_size = 0.25
entry_threshold_ticks = 50
initial_balance = 100_000
contract_size = 1

# === Load Quotes and Calculate VWAP ===
quotes = pd.read_csv(file_path_quotes, dtype={"Time": str})
quotes["Timestamp"] = pd.to_datetime(quotes["Date"] + " " + quotes["Time"], errors='coerce')
quotes.dropna(subset=["Price", "Volume", "Timestamp"], inplace=True)
quotes.sort_values("Timestamp", inplace=True)

quotes["PV"] = quotes["Price"].astype(float) * quotes["Volume"].astype(float)
quotes["CumPV"] = quotes["PV"].cumsum()
quotes["CumVolume"] = quotes["Volume"].astype(float).cumsum()
quotes["VWAP"] = quotes["CumPV"] / quotes["CumVolume"]

quotes_vwap = quotes[["Timestamp", "VWAP"]]

# === Load Main Data ===
df = pd.read_csv(file_path, dtype={"Time": str})
df["MidPrice"] = (df["L1-BidPrice"].astype(float) + df["L1-AskPrice"].astype(float)) / 2
df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors='coerce')
df.dropna(subset=["MidPrice", "Timestamp"], inplace=True)
df.sort_values("Timestamp", inplace=True)

# === Merge VWAP into Main Data ===
df = pd.merge_asof(df, quotes_vwap, on="Timestamp", direction="backward")

# === Strategy ===
trades = []
position = None
balance = initial_balance

for i in range(len(df)):
    row = df.iloc[i]
    bid = row["L1-BidPrice"]
    ask = row["L1-AskPrice"]
    mid = row["MidPrice"]
    vwap = row["VWAP"]
    time = row["Timestamp"]

    if pd.isna(vwap):
        continue

    if position is not None:
        exit_price = None
        result = None

        if position["type"] == "long":
            if bid >= position["entry_price"] + take_profit_ticks * tick_size:
                exit_price = bid
                result = "TP"
            elif ask <= position["entry_price"] - stop_loss_ticks * tick_size:
                exit_price = bid
                result = "SL"
        elif position["type"] == "short":
            if ask <= position["entry_price"] - take_profit_ticks * tick_size:
                exit_price = ask
                result = "TP"
            elif bid >= position["entry_price"] + stop_loss_ticks * tick_size:
                exit_price = ask
                result = "SL"

        if exit_price is not None:
            profit_ticks = ((exit_price - position["entry_price"]) / tick_size
                            if position["type"] == "long" else
                            (position["entry_price"] - exit_price) / tick_size)
            profit_usd = profit_ticks * tick_size * contract_size

            trades.append({
                "side": position["type"],
                "entry_time": position["entry_time"],
                "entry_price": position["entry_price"],
                "exit_time": time,
                "exit_price": exit_price,
                "result": result,
                "profit_ticks": profit_ticks,
                "profit_usd": profit_usd
            })
            balance += profit_usd
            position = None

    if position is None:
        if mid < vwap - entry_threshold_ticks * tick_size:
            position = {
                "type": "long",
                "entry_price": ask,
                "entry_time": time
            }
        elif mid > vwap + entry_threshold_ticks * tick_size:
            position = {
                "type": "short",
                "entry_price": bid,
                "entry_time": time
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

print("\n=== VWAP Strategy Results ===")
print(f"Trades Executed: {len(trades_df)}")
print(f"Final Balance: ${balance:,.2f}")
print(f"Total Profit: ${total_profit:,.2f}")
print(f"Win Rate: {winrate:.1f}%")
print(f"Avg Win: ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f}")
print(f"Profit Factor: {abs(avg_win / avg_loss):.2f}" if avg_loss != 0 else "Profit Factor: ∞")

# === Save Results ===
trades_df.to_csv("trading_results_vwap.csv", index=False)

# === Visualization ===
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=("MidPrice Tick Chart with VWAP Strategy Trades", "Cumulative Profit/Loss"))

# Price with VWAP
fig.add_trace(go.Scatter(
    x=df["Timestamp"], y=df["MidPrice"],
    mode="lines", name="MidPrice", line=dict(color="lightgray")
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=df["Timestamp"], y=df["VWAP"],
    mode="lines", name="VWAP", line=dict(color="dodgerblue")
), row=1, col=1)

# Trades
for _, trade in trades_df.iterrows():
    entry_color = "green" if trade["side"] == "long" else "red"
    exit_color = "lime" if trade["result"] == "TP" else "orange"
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
    title="Backtest Result: VWAP Strategy with PnL Curve",
    xaxis2_title="Time",
    yaxis_title="Price",
    yaxis2_title="PnL ($)",
)

fig.show()
