import os
import json
import pandas as pd
import yfinance as yf
from datetime import date, datetime

# ======================================================
# CONFIG
# ======================================================
UNIVERSE_FILE = "universe/nifty500.csv"
DATA_DIR = "data/prices"
STATE_DIR = "state"
LEARN_DIR = "state/learned_atr"

ATR_LOOKBACK_DAYS = 365
LEARN_LOOKBACK_YEARS = "3y"
ATR_WINDOW = 14
MIN_ROWS = 20
DEFAULT_ATR_MULTIPLIER = 1.5

TODAY = date.today().isoformat()

# ======================================================
# SYMBOL OVERRIDES (Corporate Actions / Renames)
# ======================================================
SYMBOL_OVERRIDES = {
    "ADANITRANS": "ADANIENSOL.NS"
}

# ======================================================
# SETUP
# ======================================================
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(LEARN_DIR, exist_ok=True)

print("STEP 11: FULLY AUTOMATED MULTI-STOCK SYSTEM STARTED")

# ======================================================
# DAILY LOCK
# ======================================================
LOCK_FILE = f"{STATE_DIR}/last_run.json"

if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "r") as f:
        if json.load(f).get("date") == TODAY:
            print("Already ran today. Exiting.")
            exit()

# ======================================================
# LOAD UNIVERSE
# ======================================================
if not os.path.exists(UNIVERSE_FILE):
    raise FileNotFoundError(f"Universe file not found: {UNIVERSE_FILE}")

universe = pd.read_csv(UNIVERSE_FILE)

if "symbol" not in universe.columns or "yahoo_symbol" not in universe.columns:
    raise ValueError("Universe file must contain columns: symbol, yahoo_symbol")

print(f"TOTAL STOCKS IN UNIVERSE: {len(universe)}")

# ======================================================
# MAIN LOOP
# ======================================================
for idx, row in universe.iterrows():
    symbol = str(row["symbol"]).strip()
    yahoo_symbol = SYMBOL_OVERRIDES.get(symbol, row["yahoo_symbol"])

    print(f"\n[{idx+1}/{len(universe)}] Processing {symbol}")

    try:
        # ==================================================
        # WEEKLY LEARNING CHECK
        # ==================================================
        learn_flag = True
        learn_date_file = f"{STATE_DIR}/last_learn_{symbol}.json"

        if os.path.exists(learn_date_file):
            with open(learn_date_file, "r") as f:
                last_learn = datetime.strptime(
                    json.load(f)["date"], "%Y-%m-%d"
                ).date()
            if (date.today() - last_learn).days < 7:
                learn_flag = False

        # ==================================================
        # WEEKLY LEARNING
        # ==================================================
        if learn_flag:
            print("  🔁 Weekly learning")

            df = yf.download(
                yahoo_symbol,
                period=LEARN_LOOKBACK_YEARS,
                interval="1d",
                progress=False
            )

            if df is None or df.empty or len(df) < MIN_ROWS:
                print("  ⚠️ Insufficient data for learning, skipping learning")
                atr_multiplier = DEFAULT_ATR_MULTIPLIER
            else:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df["HL"] = df["High"] - df["Low"]
                df["HPC"] = (df["High"] - df["Close"].shift(1)).abs()
                df["LPC"] = (df["Low"] - df["Close"].shift(1)).abs()
                df["TR"] = df[["HL", "HPC", "LPC"]].max(axis=1)
                df["ATR"] = df["TR"].rolling(ATR_WINDOW).mean()
                df = df.dropna()

                best_r = -999
                best_m = DEFAULT_ATR_MULTIPLIER

                for m in [1.0, 1.2, 1.5, 1.8, 2.0]:
                    r_vals = []

                    for i in range(1, len(df)):
                        entry = df.iloc[i - 1]["Close"]
                        atr = df.iloc[i]["ATR"]
                        risk = atr * m

                        if risk <= 0:
                            continue

                        pnl = df.iloc[i]["Close"] - entry
                        r_vals.append(pnl / risk)

                    if r_vals:
                        avg_r = sum(r_vals) / len(r_vals)
                        if avg_r > best_r:
                            best_r = avg_r
                            best_m = m

                atr_multiplier = round(best_m, 2)

                with open(f"{LEARN_DIR}/{symbol}.json", "w") as f:
                    json.dump(
                        {
                            "best_atr_multiplier": atr_multiplier,
                            "average_r": round(best_r, 4)
                        },
                        f,
                        indent=4
                    )

                with open(learn_date_file, "w") as f:
                    json.dump({"date": TODAY}, f)

                print(f"  ✅ Learned ATR multiplier: {atr_multiplier}")

        # ==================================================
        # LOAD LEARNED MULTIPLIER
        # ==================================================
        learn_file = f"{LEARN_DIR}/{symbol}.json"
        if os.path.exists(learn_file):
            with open(learn_file, "r") as f:
                atr_multiplier = float(json.load(f)["best_atr_multiplier"])
        else:
            atr_multiplier = DEFAULT_ATR_MULTIPLIER

        # ==================================================
        # DAILY TRAILING
        # ==================================================
        df = yf.download(
            yahoo_symbol,
            period=f"{ATR_LOOKBACK_DAYS}d",
            interval="1d",
            progress=False
        )

        if df is None or df.empty or len(df) < MIN_ROWS:
            print("  ⚠️ No sufficient daily data, skipping")
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["HL"] = df["High"] - df["Low"]
        df["HPC"] = (df["High"] - df["Close"].shift(1)).abs()
        df["LPC"] = (df["Low"] - df["Close"].shift(1)).abs()
        df["TR"] = df[["HL", "HPC", "LPC"]].max(axis=1)
        df["ATR"] = df["TR"].rolling(ATR_WINDOW).mean()
        df = df.dropna()

        close_price = round(float(df.iloc[-1]["Close"]), 2)
        atr = round(float(df.iloc[-1]["ATR"]), 2)

        new_sl = round(close_price - (atr * atr_multiplier), 2)

        # ==================================================
        # READ PREVIOUS STOPLOSS (SAFE)
        # ==================================================
        file_path = f"{DATA_DIR}/{symbol}.csv"

        if os.path.exists(file_path):
            try:
                old = pd.read_csv(file_path)
                if "stoploss" in old.columns and len(old) > 0:
                    prev_sl = float(old.iloc[-1]["stoploss"])
                    new_sl = max(prev_sl, new_sl)
            except Exception:
                print("  ⚠️ Corrupt CSV detected, resetting")

        # ==================================================
        # SAVE DATA
        # ==================================================
        out = pd.DataFrame([{
            "date": TODAY,
            "close_price": close_price,
            "atr": atr,
            "atr_multiplier": atr_multiplier,
            "stoploss": new_sl
        }])

        if os.path.exists(file_path):
            out.to_csv(file_path, mode="a", header=False, index=False)
        else:
            out.to_csv(file_path, index=False)

        print(f"  ✅ Close: {close_price} | SL: {new_sl}")

    except Exception as e:
        print(f"  ❌ Error processing {symbol}: {e}")

# ======================================================
# SAVE DAILY LOCK
# ======================================================
with open(LOCK_FILE, "w") as f:
    json.dump({"date": TODAY}, f)

print("\nSTEP 11 COMPLETED — SYSTEM RUN SUCCESSFULLY")
