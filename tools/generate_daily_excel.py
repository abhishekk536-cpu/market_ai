import os
import pandas as pd
from datetime import date

# -------------------------------
# CONFIG
# -------------------------------
DATA_DIR = "market_ai/data/prices"
ELIGIBLE_FILE = "market_ai/state/eligible_stocks_daily.csv"
LEARNING_FILE = "market_ai/outputs/learning_curve.xlsx"
UNIVERSE_FILE = "market_ai/universe/all_equity.csv"
OUTPUT_DIR = "market_ai/outputs"

TODAY = date.today().isoformat()
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------
# SUMMARY METRICS
# -------------------------------
universe_size = len(pd.read_csv(UNIVERSE_FILE))
eligible_df = pd.read_csv(ELIGIBLE_FILE)
eligible_count = len(eligible_df)

learning_df = pd.read_excel(LEARNING_FILE)
learning_status = learning_df.iloc[-1]["status"]

# -------------------------------
# COLLECT FEATURES SAFELY
# -------------------------------
rows = []

for _, row in eligible_df.iterrows():
    symbol = row["symbol"]
    path = f"{DATA_DIR}/{symbol}.csv"

    if not os.path.exists(path):
        continue

    df = pd.read_csv(path)

    # need indicators
    required_cols = {"ema20", "ema50", "ema200", "rsi14", "atr14"}
    if len(df) < 200 or not required_cols.issubset(df.columns):
        continue

    last = df.iloc[-1]

    trend = "UP" if last["close"] > last["ema200"] else "DOWN"

    rows.append({
        "Symbol": symbol,
        "Close": round(last["close"], 2),
        "EMA20": round(last["ema20"], 2),
        "EMA50": round(last["ema50"], 2),
        "EMA200": round(last["ema200"], 2),
        "RSI14": round(last["rsi14"], 2),
        "ATR14": round(last["atr14"], 2),
        "Trend": trend
    })

features_df = pd.DataFrame(rows)

# -------------------------------
# HANDLE EMPTY CASE (IMPORTANT)
# -------------------------------
if features_df.empty:
    print("⚠️ No stocks with full feature data today")

    summary_df = pd.DataFrame({
        "Metric": ["Date", "Universe Size", "Eligible Stocks", "Stocks With Full Data", "Learning Status"],
        "Value": [TODAY, universe_size, eligible_count, 0, learning_status]
    })

    output_file = f"{OUTPUT_DIR}/daily_report_{TODAY}.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    print("✅ DAILY EXCEL REPORT CREATED (EMPTY DATA SAFE)")
    exit()

# -------------------------------
# TOP TREND STOCKS (SAFE)
# -------------------------------
top_trend = features_df[
    (features_df["Trend"] == "UP") &
    (features_df["RSI14"] > 50)
].sort_values("RSI14", ascending=False).head(20)

# -------------------------------
# SUMMARY SHEET
# -------------------------------
summary_df = pd.DataFrame({
    "Metric": [
        "Date",
        "Universe Size",
        "Eligible Stocks",
        "Stocks With Full Data",
        "Learning Status"
    ],
    "Value": [
        TODAY,
        universe_size,
        eligible_count,
        len(features_df),
        learning_status
    ]
})

# -------------------------------
# WRITE EXCEL
# -------------------------------
output_file = f"{OUTPUT_DIR}/daily_report_{TODAY}.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    summary_df.to_excel(writer, sheet_name="Summary", index=False)
    features_df.to_excel(writer, sheet_name="Stock_Features", index=False)
    top_trend.to_excel(writer, sheet_name="Top_Trend_Stocks", index=False)

print("✅ DAILY EXCEL REPORT CREATED:", output_file)
