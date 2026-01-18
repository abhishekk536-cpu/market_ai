import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_ai"))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
FEATURE_DIR = os.path.join(BASE_DIR, "data", "features")

PICKS_FILE = os.path.join(REPORT_DIR, "weekly_picks.xlsx")
OUT_FILE = os.path.join(REPORT_DIR, "weekly_backtest.xlsx")

if not os.path.exists(PICKS_FILE):
    print("❌ weekly_picks.xlsx not found")
    exit()

picks = pd.read_excel(PICKS_FILE)

results = []

for _, row in picks.iterrows():
    symbol = row["symbol"]
    file = os.path.join(FEATURE_DIR, f"{symbol}.csv")

    if not os.path.exists(file):
        continue

    df = pd.read_csv(file)
    df = df.dropna().reset_index(drop=True)

    if len(df) < 10:
        continue

    entry = df.iloc[-6]["close"]
    exit_price = df.iloc[-1]["close"]

    ret = (exit_price - entry) / entry

    results.append({
        "symbol": symbol,
        "entry_price": entry,
        "exit_price": exit_price,
        "return_%": round(ret * 100, 2),
        "win": ret > 0
    })

if not results:
    print("⚠️ No backtest data generated")
    exit()

bt = pd.DataFrame(results)

summary = {
    "total_stocks": len(bt),
    "win_rate_%": round(bt["win"].mean() * 100, 1),
    "avg_return_%": round(bt["return_%"].mean(), 2),
    "best_%": bt["return_%"].max(),
    "worst_%": bt["return_%"].min()
}

summary_df = pd.DataFrame([summary])

with pd.ExcelWriter(OUT_FILE, engine="xlsxwriter") as writer:
    bt.to_excel(writer, sheet_name="Trades", index=False)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

print("📊 WEEKLY BACKTEST COMPLETE")
print(summary_df)
