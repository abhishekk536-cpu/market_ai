# ===============================
# MARKET AI — LIVE DASHBOARD
# ===============================

import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# ===============================
# AUTO REFRESH (5 minutes)
# ===============================
st_autorefresh(interval=300_000, key="auto_refresh")

# ===============================
# PATHS
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "market_ai"))

DATA_DIR = os.path.join(BASE_DIR, "data")
PRICE_DIR = os.path.join(DATA_DIR, "prices")
FEATURE_DIR = os.path.join(DATA_DIR, "features")

REPORT_DIR = os.path.join(BASE_DIR, "reports")
UNIVERSE_FILE = os.path.join(BASE_DIR, "universe", "all_equity.csv")

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Market AI Dashboard",
    layout="wide"
)

st.title("📊 Market AI — System Dashboard")

# ===============================
# SYSTEM STATUS LOGIC
# ===============================
def system_status(universe, prices, features):
    if prices >= universe and features >= universe * 0.95:
        return "GREEN", "🟢 SYSTEM HEALTHY"
    elif prices >= universe * 0.8:
        return "AMBER", "🟠 DATA STILL BUILDING"
    else:
        return "RED", "🔴 DATA INCOMPLETE — CHECK PIPELINE"

# ===============================
# LOAD COUNTS
# ===============================
universe_count = len(pd.read_csv(UNIVERSE_FILE)) if os.path.exists(UNIVERSE_FILE) else 0
price_count = len(os.listdir(PRICE_DIR)) if os.path.exists(PRICE_DIR) else 0
feature_count = len(os.listdir(FEATURE_DIR)) if os.path.exists(FEATURE_DIR) else 0

status, msg = system_status(universe_count, price_count, feature_count)

# ===============================
# STATUS BANNER
# ===============================
if status == "GREEN":
    st.success(msg)
elif status == "AMBER":
    st.warning(msg)
else:
    st.error(msg)

# ===============================
# SYSTEM HEALTH METRICS
# ===============================
st.subheader("🧱 System Health Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Universe Stocks", universe_count)
c2.metric("Price Files", price_count)
c3.metric("Feature Files", feature_count)
c4.metric("System Status", status)

st.divider()

# ===============================
# DAILY LEARNING CURVE
# ===============================
st.subheader("📈 Learning Curve")

learning_file = os.path.join(REPORT_DIR, "daily_learning.xlsx")

if os.path.exists(learning_file):
    df = pd.read_excel(learning_file)

    fig, ax = plt.subplots()
    ax.plot(df["date"], df["win_rate"], marker="o")
    ax.set_title("Daily Win Rate")
    ax.set_ylabel("Win Rate")
    ax.set_xlabel("Date")
    ax.grid(True)

    st.pyplot(fig)
    st.dataframe(df.tail(7), use_container_width=True)
else:
    st.warning("Daily learning data not available yet")

st.divider()

# ===============================
# SIGNAL SCORE DISTRIBUTION
# ===============================
st.subheader("🧠 Signal Intelligence")

signal_log = os.path.join(REPORT_DIR, "signal_log.xlsx")

if os.path.exists(signal_log):
    s = pd.read_excel(signal_log)

    fig, ax = plt.subplots()
    s["signal_score"].hist(bins=25, ax=ax)
    ax.set_title("Signal Score Distribution")
    ax.set_xlabel("Signal Score")
    ax.set_ylabel("Frequency")

    st.pyplot(fig)
else:
    st.warning("Signal log not available yet")

st.divider()

# ===============================
# LEARNED WEIGHTS
# ===============================
st.subheader("⚙️ Learned Model Weights")

weights_file = os.path.join(REPORT_DIR, "learned_weights.xlsx")

if os.path.exists(weights_file):
    w = pd.read_excel(weights_file)
    st.dataframe(w.tail(1), use_container_width=True)
else:
    st.info("Model weights will appear after sufficient learning data")

st.divider()

# ===============================
# WEEKLY PICKS
# ===============================
st.subheader("⭐ Weekly Picks")

weekly_file = os.path.join(REPORT_DIR, "weekly_picks.xlsx")

if os.path.exists(weekly_file):
    wp = pd.read_excel(weekly_file)
    st.dataframe(wp, use_container_width=True)
else:
    st.info("Weekly picks not generated yet")

st.caption("Market AI Dashboard — auto-refreshes every 5 minutes")
# ===============================
# STOCK DRILLDOWN
# ===============================
st.divider()
st.subheader("🔍 Stock Drilldown (Click-to-Analyze)")

feature_files = []
if os.path.exists(FEATURE_DIR):
    feature_files = sorted([f.replace(".csv", "") for f in os.listdir(FEATURE_DIR) if f.endswith(".csv")])

if not feature_files:
    st.warning("No feature files available for drilldown")
else:
    symbol = st.selectbox("Select Stock", feature_files)

    file_path = os.path.join(FEATURE_DIR, f"{symbol}.csv")

    try:
        df = pd.read_csv(file_path)

        if len(df) < 50:
            st.warning("Not enough data for this stock")
        else:
            df["date"] = pd.to_datetime(df["date"])

            # -------------------------------
            # PRICE + EMA CHART
            # -------------------------------
            st.markdown("### 📈 Price & EMA")

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df["date"], df["close"], label="Close", linewidth=2)
            ax.plot(df["date"], df["ema_20"], label="EMA 20")
            ax.plot(df["date"], df["ema_50"], label="EMA 50")
            ax.plot(df["date"], df["ema_200"], label="EMA 200")
            ax.legend()
            ax.grid(True)

            st.pyplot(fig)

            # -------------------------------
            # RSI
            # -------------------------------
            st.markdown("### 📉 RSI (14)")

            fig, ax = plt.subplots(figsize=(10, 2.5))
            ax.plot(df["date"], df["rsi_14"], color="purple")
            ax.axhline(70, linestyle="--", color="red")
            ax.axhline(30, linestyle="--", color="green")
            ax.set_ylim(0, 100)
            ax.grid(True)

            st.pyplot(fig)

            # -------------------------------
            # ATR & TREND INFO
            # -------------------------------
            last = df.iloc[-1]
            atr_pct = (last["atr_14"] / last["close"]) * 100

            c1, c2, c3 = st.columns(3)
            c1.metric("ATR (₹)", round(last["atr_14"], 2))
            c2.metric("ATR %", round(atr_pct, 2))
            c3.metric("Trend", last["trend"])

    except Exception as e:
        st.error(f"Error loading stock data: {e}")
# ===============================
# PER-STOCK DRILLDOWN
# ===============================
st.divider()
st.subheader("🔍 Stock Drill-Down Analysis")

if os.path.exists(FEATURE_DIR):
    stock_files = sorted(
        [f.replace(".csv", "") for f in os.listdir(FEATURE_DIR) if f.endswith(".csv")]
    )

    selected_stock = st.selectbox(
        "Select a stock",
        stock_files,
        index=0
    )

    stock_file = os.path.join(FEATURE_DIR, f"{selected_stock}.csv")

    if os.path.exists(stock_file):
        df = pd.read_csv(stock_file)

        if len(df) < 50:
            st.warning("Not enough data for this stock yet")
        else:
            df = df.tail(150)

            # ===============================
            # PRICE + EMA CHART
            # ===============================
            fig, ax = plt.subplots(figsize=(10, 4))

            ax.plot(df["date"], df["close"], label="Close", linewidth=2)
            ax.plot(df["date"], df["ema_20"], label="EMA 20")
            ax.plot(df["date"], df["ema_50"], label="EMA 50")
            ax.plot(df["date"], df["ema_200"], label="EMA 200")

            ax.set_title(f"{selected_stock} — Price & EMA")
            ax.legend()
            ax.grid(True)

            st.pyplot(fig)

            # ===============================
            # RSI
            # ===============================
            fig, ax = plt.subplots(figsize=(10, 2.5))
            ax.plot(df["date"], df["rsi_14"], color="orange")
            ax.axhline(70, color="red", linestyle="--")
            ax.axhline(30, color="green", linestyle="--")
            ax.set_title("RSI (14)")
            ax.grid(True)

            st.pyplot(fig)

            # ===============================
            # ATR
            # ===============================
            fig, ax = plt.subplots(figsize=(10, 2.5))
            ax.plot(df["date"], df["atr_14"], color="purple")
            ax.set_title("ATR (14)")
            ax.grid(True)

            st.pyplot(fig)

