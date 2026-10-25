import os
from pathlib import Path

import mysql.connector
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / "config" / ".env")

st.set_page_config(page_title="NSE Stock Dashboard", page_icon="📈", layout="wide")

NUMERIC_COLS = [
    "open_price", "high_price", "low_price", "close_price",
    "volume", "daily_change_pct", "ma_7",
]
GREEN, RED = "#16a34a", "#dc2626"


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """Read the whole stock_prices table from MySQL (cached for 5 minutes)."""
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT date, ticker, open_price, high_price, low_price, "
            "close_price, volume, daily_change_pct, ma_7 "
            "FROM stock_prices ORDER BY date"
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(pd.to_numeric, errors="coerce")
    return df


def short(ticker: str) -> str:
    return ticker.replace(".NS", "")


# ---------- load data ----------
try:
    df = load_data()
except Exception as e:
    st.error(f"Could not read data from MySQL: {e}")
    st.info("Check that MySQL is running and that config/.env has the right DB_* values.")
    st.stop()

if df.empty:
    st.warning("The stock_prices table is empty. Run the pipeline first.")
    st.stop()

# ---------- sidebar ----------
st.sidebar.title("Filters")
tickers = sorted(df["ticker"].unique())
ticker = st.sidebar.selectbox("Stock", tickers, format_func=short)

min_d, max_d = df["date"].min().date(), df["date"].max().date()
date_range = st.sidebar.date_input(
    "Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d
)
if not (isinstance(date_range, tuple) and len(date_range) == 2):
    st.info("Pick an end date in the sidebar.")
    st.stop()
start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])

chart_type = st.sidebar.radio("Price chart", ["Line", "Candlestick"])

if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

in_range = df[(df["date"] >= start) & (df["date"] <= end)]
data = in_range[in_range["ticker"] == ticker].sort_values("date")

st.title("📈 NSE Stock Market Dashboard")
st.caption(f"Data from MySQL · latest date in database: {max_d:%d %b %Y}")

if data.empty:
    st.warning("No data for this stock in the selected date range.")
    st.stop()

# ---------- KPI cards ----------
latest = data.iloc[-1]
change = latest["daily_change_pct"]
if pd.isna(change) and len(data) > 1:
    prev_close = data.iloc[-2]["close_price"]
    change = (latest["close_price"] - prev_close) / prev_close * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    f"{short(ticker)} latest close",
    f"₹{latest['close_price']:,.2f}",
    None if pd.isna(change) else f"{change:+.2f}%",
)
c2.metric("Period high", f"₹{data['high_price'].max():,.2f}")
c3.metric("Period low", f"₹{data['low_price'].min():,.2f}")
c4.metric("Avg daily volume", f"{data['volume'].mean():,.0f}")

# ---------- price + moving average ----------
st.subheader(f"{short(ticker)} price and 7-day moving average")
fig = go.Figure()
if chart_type == "Candlestick":
    fig.add_trace(go.Candlestick(
        x=data["date"], open=data["open_price"], high=data["high_price"],
        low=data["low_price"], close=data["close_price"], name="Price",
        increasing_line_color=GREEN, decreasing_line_color=RED,
    ))
else:
    fig.add_trace(go.Scatter(
        x=data["date"], y=data["close_price"], name="Close", mode="lines",
    ))
fig.add_trace(go.Scatter(
    x=data["date"], y=data["ma_7"], name="7-day MA",
    mode="lines", line=dict(dash="dash"),
))
fig.update_layout(
    height=450, margin=dict(l=10, r=10, t=10, b=10),
    xaxis_rangeslider_visible=False, yaxis_title="Price (₹)",
    legend=dict(orientation="h", y=1.08),
)
st.plotly_chart(fig)

# ---------- daily change and volume ----------
left, right = st.columns(2)

with left:
    st.subheader("Daily change %")
    change_series = data["daily_change_pct"].fillna(0)
    fig_change = go.Figure(go.Bar(
        x=data["date"], y=change_series,
        marker_color=[GREEN if v >= 0 else RED for v in change_series],
    ))
    fig_change.update_layout(
        height=320, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="%",
    )
    st.plotly_chart(fig_change)

with right:
    st.subheader("Volume")
    fig_vol = go.Figure(go.Bar(x=data["date"], y=data["volume"]))
    fig_vol.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_vol)

# ---------- comparison of all stocks ----------
st.subheader("All stocks compared (starting value = 100)")
pivot = in_range.pivot_table(index="date", columns="ticker", values="close_price")
fig_cmp = go.Figure()
for t in pivot.columns:
    series = pivot[t].dropna()
    if series.empty:
        continue
    fig_cmp.add_trace(go.Scatter(
        x=series.index, y=series / series.iloc[0] * 100,
        name=short(t), mode="lines",
    ))
fig_cmp.update_layout(
    height=400, margin=dict(l=10, r=10, t=10, b=10),
    yaxis_title="Indexed price", legend=dict(orientation="h", y=1.08),
)
st.plotly_chart(fig_cmp)

# ---------- raw data ----------
with st.expander("Show raw data"):
    show = data.copy()
    show["date"] = show["date"].dt.date
    st.dataframe(show.sort_values("date", ascending=False))
    st.download_button(
        "Download CSV",
        show.to_csv(index=False).encode("utf-8"),
        file_name=f"{short(ticker)}_prices.csv",
        mime="text/csv",
    )