import os
import pandas as pd
from datetime import datetime

# ===============================
# PATHS
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_ai"))

FEATURE_DIR = os.path.join(BASE_DIR, "data", "features")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

SIGNAL_LOG = os.path.join(REPORT_DIR, "signal_log.xlsx")
OUT_FILE = os.path.join(REPORT_DIR, "weekly_picks.xlsx")

# ===============================
# LOAD DATA
# ===============================
signals = pd.read_excel(SIGNAL_LOG)

latest_date = signals["date"].max()

recent = signals[signals["date"] == latest_date].copy()

print(f"📅 Generating weekly picks for: {latest_date}")

# ===============================
# HISTORICAL PERFORMANCE PER STOCK
# ===============================
history = (
    signals.groupby("symbol")
    .agg(
        win_rate=("win", "mean"),
        avg_return=("forward_return_5d", "mean"),
        signals=("signal_score", "count")
    )
    .reset_index()
)

# Merge with recent signals
df = recent.merge(history, on="symbol", how="left")

# ===============================
# TECHNICAL CONFIRMATION
# ===============================
qualified = []

for _, row in df.iterrows():
    symbol = row["symbol"]
    feature_file = os.path.join(FEATURE_DIR, f"{symbol}.csv")

    if not os.path.exists(feature_file):
        continue

    fdf = pd.read_csv(feature_file)

    if len(fdf) < 220:
        continue

    last = fdf.iloc[-1]
    prev1 = fdf.iloc[-2]
    prev2 = fdf.iloc[-3]

    atr_pct = last["atr_14"] / last["close"]

    trend_ok = (
        last["trend"] == "UP"
        and prev1["trend"] == "UP"
        and prev2["trend"] == "UP"
    )

    if not (
        row["signal_score"] >= 70
        and row["win_rate"] >= 0.55
        and 0.01 <= atr_pct <= 0.06
        and trend_ok
    ):
        continue

    qualified.append({
        "symbol": symbol,
        "signal_score": row["signal_score"],
        "win_rate_%": round(row["win_rate"] * 100, 1),
        "avg_return_%": round(row["avg_return"] * 100, 2),
        "atr_%": round(atr_pct * 100, 2),
        "signals_seen": int(row["signals"]),
        "trend": last["trend"]
    })

# ===============================
# FINAL RANKING
# ===============================
weekly = pd.DataFrame(qualified)

if weekly.empty:
    print("⚠️ No weekly candidates found")
    exit()

weekly = weekly.sort_values(
    ["signal_score", "win_rate_%"],
    ascending=False
)

# Take Top 15 (configurable)
weekly = weekly.head(15)

# ===============================
# SAVE
# ===============================
weekly["week"] = datetime.now().strftime("%Y-%U")

weekly.to_excel(OUT_FILE, index=False)

print("✅ WEEKLY PICKS GENERATED")
print(weekly[["symbol", "signal_score", "win_rate_%", "atr_%"]])
