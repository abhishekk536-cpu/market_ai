import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_ai"))
REPORT_DIR = os.path.join(BASE_DIR, "reports")

LOG_FILE = os.path.join(REPORT_DIR, "signal_log.xlsx")
OUT_FILE = os.path.join(REPORT_DIR, "signal_score_analysis.xlsx")

df = pd.read_excel(LOG_FILE)

def bucket(score):
    if score > 75:
        return "HIGH (>75)"
    elif score >= 60:
        return "MEDIUM (60–75)"
    else:
        return "LOW (<60)"

df["score_bucket"] = df["signal_score"].apply(bucket)

summary = (
    df.groupby("score_bucket")
    .agg(
        signals=("signal_score", "count"),
        win_rate=("win", "mean"),
        avg_return=("forward_return_5d", "mean"),
        avg_score=("signal_score", "mean")
    )
    .reset_index()
)

summary["win_rate"] = (summary["win_rate"] * 100).round(1)
summary["avg_return"] = (summary["avg_return"] * 100).round(2)

summary.to_excel(OUT_FILE, index=False)

print("📊 SIGNAL SCORE ANALYSIS COMPLETE")
print(summary)
