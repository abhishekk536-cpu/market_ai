import os
import pandas as pd
import yfinance as yf
from datetime import date

# -------------------------------
# CONFIG
# -------------------------------
UNIVERSE_FILE = "market_ai/universe/all_equity.csv"
OUTPUT_FILE = "market_ai/state/eligible_stocks_daily.csv"

MIN_MARKET_CAP_CR = 1000          # ₹1000 Cr
RUPEES_IN_CR = 1e7

TODAY = date.today().isoformat()

# -------------------------------
# SETUP
# -------------------------------
os.makedirs("market_ai/state", exist_ok=True)

df = pd.read_csv(UNIVERSE_FILE)

print("TOTAL STOCKS IN UNIVERSE:", len(df))

eligible = []

# -------------------------------
# MARKET CAP FILTER
# -------------------------------
for _, row in df.iterrows():
    symbol = row["symbol"]
    yahoo_symbol = row["yahoo_symbol"]

    try:
        ticker = yf.Ticker(yahoo_symbol)
        info = ticker.fast_info

        market_cap = info.get("marketCap", None)

        if market_cap is None:
            continue

        market_cap_cr = market_cap / RUPEES_IN_CR

        if market_cap_cr >= MIN_MARKET_CAP_CR:
            eligible.append({
                "symbol": symbol,
                "yahoo_symbol": yahoo_symbol,
                "market_cap_cr": round(market_cap_cr, 2),
                "date": TODAY
            })

    except Exception:
        continue

# -------------------------------
# SAVE OUTPUT
# -------------------------------
out_df = pd.DataFrame(eligible)
out_df = out_df.sort_values("market_cap_cr", ascending=False)

out_df.to_csv(OUTPUT_FILE, index=False)

print("ELIGIBLE STOCKS (>=1000 Cr):", len(out_df))
print("Saved to:", OUTPUT_FILE)
