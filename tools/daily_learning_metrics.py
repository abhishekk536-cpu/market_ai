import os
import pandas as pd
import numpy as np
from datetime import datetime

# ===============================
# PATHS
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_ai"))

FEATURE_DIR = os.path.join(BASE_DIR, "data", "features")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(REPORT_DIR, exist_ok=True)

SUMMARY_FILE = os.path.join(REPORT_DIR, "daily_learning.xlsx")
SIGNAL_LOG_FILE = os.path.join(REPORT_DIR, "signal_log.xlsx")

files = [f for f in os.listdir(FEATURE_DIR) if f.endswith(".csv")]

print(f"📊 RUNNING DAILY LEARNING ON {len(files)} STOCKS")

today = datetime.now().date()

signal_records = []

# ===============================
# MAIN LOOP
# ===============================
for file in files:
    symbol = file.replace(".csv", "")

    try:
        df = pd.read_csv(os.path.join(FEATURE_DIR, file))

        if len(df) < 220:
            continue

        df = df.dropna().reset_index(drop=True)

        last = df.iloc[-1]
        future = df.iloc[-6]

        # ===============================
        # SIGNAL FILTER
        # ===============================
        ema_stack_ok = last["ema_20"] > last["ema_50"] > last["ema_200"]
        rsi_ok = 45 <= last["rsi_14"] <= 65

        atr_pct = last["atr_14"] / last["close"]
        atr_ok = 0.01 <= atr_pct <= 0.06

        trend_1 = df.iloc[-1]["trend"] == "UP"
        trend_2 = df.iloc[-2]["trend"] == "UP"
        trend_3 = df.iloc[-3]["trend"] == "UP"

        if not (ema_stack_ok and rsi_ok and atr_ok and trend_1 and trend_2):
            continue

        # ===============================
        # SIGNAL SCORE
        # ===============================
        ema_score = np.clip(
            ((last["ema_20"] - last["ema_200"]) / last["ema_200"]) * 300,
            0, 30
        )

        rsi_score = np.clip(
            25 - abs(last["rsi_14"] - 55) * 1.25,
            0, 25
        )

        atr_score = np.clip(
            25 - abs(atr_pct - 0.03) * 500,
            0, 25
        )

        trend_score = 20 if trend_1 and trend_2 and trend_3 else 12

        signal_score = round(
            ema_score + rsi_score + atr_score + trend_score, 1
        )

        forward_return = (future["close"] - last["close"]) / last["close"]

        signal_records.append({
            "date": today,
            "symbol": symbol,
            "signal_score": signal_score,
            "forward_return_5d": forward_return,
            "win": forward_return > 0,
            "rsi": last["rsi_14"],
            "atr": last["atr_14"],
            "trend": last["trend"]
        })

    except Exception:
        continue

# ===============================
# SAVE SIGNAL LOG
# ===============================
if not signal_records:
    print("⚠️ No valid signals today")
    exit()

signal_df = pd.DataFrame(signal_records)

if os.path.exists(SIGNAL_LOG_FILE):
    old = pd.read_excel(SIGNAL_LOG_FILE)
    signal_df = pd.concat([old, signal_df], ignore_index=True)

signal_df.to_excel(SIGNAL_LOG_FILE, index=False)

# ===============================
# DAILY SUMMARY
# ===============================
summary = {
    "date": today,
    "stocks_evaluated": len(signal_df[signal_df["date"] == today]),
    "avg_signal_score": round(signal_df["signal_score"].mean(), 1),
    "win_rate": round(signal_df["win"].mean(), 3),
    "avg_forward_return": round(signal_df["forward_return_5d"].mean(), 4),
    "avg_atr": round(signal_df["atr"].mean(), 2),
    "status": "OK"
}

summary_df = pd.DataFrame([summary])

if os.path.exists(SUMMARY_FILE):
    old = pd.read_excel(SUMMARY_FILE)
    final = pd.concat([old, summary_df], ignore_index=True)
else:
    final = summary_df

final.to_excel(SUMMARY_FILE, index=False)

print("✅ DAILY LEARNING METRICS UPDATED")
print(summary_df)
