import os
import pandas as pd
import numpy as np

# ===============================
# PATHS
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_ai"))

PRICE_DIR = os.path.join(BASE_DIR, "data", "prices")
FEATURE_DIR = os.path.join(BASE_DIR, "data", "features")

os.makedirs(FEATURE_DIR, exist_ok=True)

files = [f for f in os.listdir(PRICE_DIR) if f.endswith(".csv")]

print(f"🧠 COMPUTING FEATURES FOR {len(files)} STOCKS")

# ===============================
# INDICATOR FUNCTIONS
# ===============================
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    return tr.rolling(period).mean()

# ===============================
# MAIN LOOP
# ===============================
processed = 0
skipped = 0

for file in files:
    symbol = file.replace(".csv", "")

    try:
        df = pd.read_csv(os.path.join(PRICE_DIR, file))

        # --- Normalize column names ---
        cols = {c: c.split("_")[0] for c in df.columns if c != "date"}
        df = df.rename(columns=cols)

        required = {"open", "high", "low", "close", "volume"}
        if not required.issubset(df.columns):
            print(f"⚠️ {symbol}: missing OHLCV columns")
            skipped += 1
            continue

        if len(df) < 200:
            print(f"⚠️ {symbol}: insufficient history")
            skipped += 1
            continue

        df["ema_20"] = ema(df["close"], 20)
        df["ema_50"] = ema(df["close"], 50)
        df["ema_200"] = ema(df["close"], 200)

        df["rsi_14"] = rsi(df["close"], 14)
        df["atr_14"] = atr(df, 14)

        # --- Trend Regime ---
        df["trend"] = np.where(
            (df["ema_20"] > df["ema_50"]) & (df["ema_50"] > df["ema_200"]),
            "UP",
            np.where(
                (df["ema_20"] < df["ema_50"]) & (df["ema_50"] < df["ema_200"]),
                "DOWN",
                "SIDEWAYS"
            )
        )

        out = os.path.join(FEATURE_DIR, f"{symbol}.csv")
        df.to_csv(out, index=False)

        processed += 1

    except Exception as e:
        print(f"❌ {symbol}: {e}")
        skipped += 1

# ===============================
# SUMMARY
# ===============================
print("\n📊 FEATURE ENGINEERING SUMMARY")
print(f"✅ PROCESSED : {processed}")
print(f"⚠️ SKIPPED   : {skipped}")
print(f"📁 TOTAL     : {len(os.listdir(FEATURE_DIR))}")
