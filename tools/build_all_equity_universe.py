import os
import pandas as pd

os.makedirs("market_ai/universe", exist_ok=True)

INPUT_FILE = "MW-NIFTY-500-18-Jan-2026.csv"
OUTPUT_FILE = "market_ai/universe/all_equity.csv"

# Load file
df = pd.read_csv(INPUT_FILE)

# Normalize column names
df.columns = [c.strip().upper() for c in df.columns]

# Auto-detect symbol column
POSSIBLE_SYMBOL_COLS = [
    "SYMBOL",
    "SECURITY ID",
    "SECURITYID",
    "STOCK CODE",
    "STOCKCODE",
    "NAME",
    "COMPANY"
]

symbol_col = None
for col in POSSIBLE_SYMBOL_COLS:
    if col in df.columns:
        symbol_col = col
        break

if symbol_col is None:
    raise ValueError(f"No symbol column found. Columns are: {df.columns.tolist()}")

print(f"✅ Using symbol column: {symbol_col}")

# Clean symbols
df = df[df[symbol_col].notna()]
df["symbol"] = df[symbol_col].astype(str).str.strip()

# Remove index row if present
df = df[df["symbol"].str.upper() != "NIFTY 500"]

# Build yahoo symbol
df["yahoo_symbol"] = df["symbol"] + ".NS"

# Final universe
out = df[["symbol", "yahoo_symbol"]].drop_duplicates()

# Save
out.to_csv(OUTPUT_FILE, index=False)

print("✅ ALL EQUITY UNIVERSE CREATED")
print("TOTAL STOCKS:", len(out))
