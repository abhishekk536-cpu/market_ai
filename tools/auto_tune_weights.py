import os
import pandas as pd
import numpy as np
from datetime import datetime

# ===============================
# PATHS
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_ai"))
REPORT_DIR = os.path.join(BASE_DIR, "reports")

SIGNAL_LOG = os.path.join(REPORT_DIR, "signal_log.xlsx")
WEIGHT_FILE = os.path.join(REPORT_DIR, "learned_weights.xlsx")

# ===============================
# LOAD DATA
# ===============================
df = pd.read_excel(SIGNAL_LOG)

# Use last 90 days for learning
df["date"] = pd.to_datetime(df["date"])
cutoff = df["date"].max() - pd.Timedelta(days=90)
df = df[df["date"] >= cutoff]

if len(df) < 200:
    print("⚠️ Not enough data to tune weights")
    exit()

# ===============================
# FEATURE NORMALIZATION
# ===============================
features = {
    "ema": df["signal_score"],   # proxy – EMA already embedded
    "rsi": df["rsi"],
    "atr": df["atr"],
    "trend": df["trend"].apply(lambda x: 1 if x == "UP" else 0)
}

returns = df["forward_return_5d"]

scores = {}

for name, series in features.items():
    try:
        corr = np.corrcoef(series, returns)[0, 1]
        scores[name] = max(corr, 0)
    except Exception:
        scores[name] = 0

# ===============================
# NORMALIZE WEIGHTS
# ===============================
total = sum(scores.values())

if total == 0:
    print("⚠️ Learning failed: zero signal contribution")
    exit()

weights = {k: round(v / total, 3) for k, v in scores.items()}

# Apply safety caps
weights["ema"] = min(max(weights["ema"], 0.25), 0.45)
weights["rsi"] = min(max(weights["rsi"], 0.15), 0.30)
weights["atr"] = min(max(weights["atr"], 0.10), 0.25)
weights["trend"] = min(max(weights["trend"], 0.10), 0.25)

# Renormalize after caps
norm = sum(weights.values())
weights = {k: round(v / norm, 3) for k, v in weights.items()}

# ===============================
# SAVE
# ===============================
row = {
    "date": datetime.now().date(),
    **weights
}

out = pd.DataFrame([row])

if os.path.exists(WEIGHT_FILE):
    old = pd.read_excel(WEIGHT_FILE)
    out = pd.concat([old, out], ignore_index=True)

out.to_excel(WEIGHT_FILE, index=False)

print("🧠 MODEL WEIGHTS UPDATED")
print(out.tail(1))
