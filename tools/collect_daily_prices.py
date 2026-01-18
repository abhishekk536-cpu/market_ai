import os
import pandas as pd
import yfinance as yf

# ===============================
# BASE DIRECTORY (DOUBLE market_ai FIX)
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_ai"))

DATA_DIR = os.path.join(BASE_DIR, "data", "prices")
STATE_DIR = os.path.join(BASE_DIR, "state")
UNIVERSE_FILE = os.path.join(STATE_DIR, "eligible_stocks_daily.csv")

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(UNIVERSE_FILE):
    raise FileNotFoundError(f"Universe file not found: {UNIVERSE_FILE}")

stocks = pd.read_csv(UNIVERSE_FILE)

print(f"📥 COLLECTING DAILY DATA FOR: {len(stocks)} STOCKS")

saved = 0
skipped = 0

# ===============================
# MAIN LOOP
# ===============================
for _, row in stocks.iterrows():

    symbol = row["symbol"]
    yahoo_symbol = row["yahoo_symbol"]

    # --- FORCE CLEAN STRING ---
    if isinstance(symbol, tuple):
        symbol = symbol[0]
    if isinstance(yahoo_symbol, tuple):
        yahoo_symbol = yahoo_symbol[0]

    symbol = str(symbol).strip()
    yahoo_symbol = str(yahoo_symbol).strip()

    print(f"▶ Downloading: {symbol} | {yahoo_symbol}")

    try:
        df = yf.download(
            yahoo_symbol,
            period="2y",
            interval="1d",
            progress=False,
            auto_adjust=False
        )

        if df.empty or len(df) < 50:
            print(f"⚠️ {symbol}: insufficient data")
            skipped += 1
            continue

        df = df.reset_index()

        # 🔥 FIX: HANDLE MULTIINDEX COLUMNS
        df.columns = [
            "_".join(c).lower() if isinstance(c, tuple) else c.lower()
            for c in df.columns
        ]

        out_file = os.path.join(DATA_DIR, f"{symbol}.csv")
        df.to_csv(out_file, index=False)

        print(f"✅ SAVED: {symbol}")
        saved += 1

    except Exception as e:
        print(f"❌ {symbol}: {e}")
        skipped += 1

# ===============================
# SUMMARY
# ===============================
print("\n📊 DAILY PRICE COLLECTION SUMMARY")
print(f"✅ FILES SAVED : {saved}")
print(f"⚠️ SKIPPED     : {skipped}")
print(f"📁 TOTAL FILES : {len(os.listdir(DATA_DIR))}")
