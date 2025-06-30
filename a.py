import pandas as pd
import plotly.express as px

# === Load Trades ===
trades_df = pd.read_csv("random_trading_results.csv")

# === Histogram Plot ===
fig = px.histogram(
    trades_df,
    x="profit_usd",
    nbins=50,
    title="Histogram of Trade Profits (Non-Cumulative)",
    labels={"profit_usd": "Profit per Trade ($)"},
    color_discrete_sequence=["gold"]
)

fig.update_layout(
    template="plotly_dark",
    bargap=0.05,
    xaxis_title="Profit per Trade ($)",
    yaxis_title="Number of Trades"
)

fig.show()
