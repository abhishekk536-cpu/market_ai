import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_ai"))

DATA_DIR = os.path.join(BASE_DIR, "data")
PRICE_DIR = os.path.join(DATA_DIR, "prices")
FEATURE_DIR = os.path.join(DATA_DIR, "features")
STATE_DIR = os.path.join(BASE_DIR, "state")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

print("\n🔍 MARKET AI — SYSTEM HEALTH CHECK\n")

status_ok = True

# ===============================
# 1. UNIVERSE
# ===============================
universe_file = os.path.join(BASE_DIR, "universe", "all_equity.csv")

if os.path.exists(universe_file):
    universe = pd.read_csv(universe_file)
    print(f"✅ Universe loaded: {len(universe)} stocks")
    if len(universe) < 400:
        print("⚠️ Universe size looks low")
        status_ok = False
else:
    print("❌ Universe file missing")
    status_ok = False

# ===============================
# 2. PRICE FILES
# ===============================
if os.path.exists(PRICE_DIR):
    price_files = [f for f in os.listdir(PRICE_DIR) if f.endswith(".csv")]
    print(f"✅ Price files: {len(price_files)}")
    if len(price_files) < 400:
        print("⚠️ Price collection incomplete")
        status_ok = False
else:
    print("❌ Price directory missing")
    status_ok = False

# ===============================
# 3. FEATURE FILES
# ===============================
if os.path.exists(FEATURE_DIR):
    feature_files = [f for f in os.listdir(FEATURE_DIR) if f.endswith(".csv")]
    print(f"✅ Feature files: {len(feature_files)}")
    if len(feature_files) < 400:
        print("⚠️ Feature computation incomplete")
        status_ok = False
else:
    print("❌ Feature directory missing")
    status_ok = False

# ===============================
# 4. SIGNAL LOG
# ===============================
signal_log = os.path.join(REPORT_DIR, "signal_log.xlsx")

if os.path.exists(signal_log):
    df = pd.read_excel(signal_log)
    print(f"✅ Signals logged: {len(df)}")
    if len(df) < 50:
        print("⚠️ Signal history still building")
else:
    print("❌ Signal log missing")
    status_ok = False

# ===============================
# 5. DAILY LEARNING
# ===============================
daily_learning = os.path.join(REPORT_DIR, "daily_learning.xlsx")

if os.path.exists(daily_learning):
    dl = pd.read_excel(daily_learning)
    print(f"✅ Daily learning rows: {len(dl)}")
else:
    print("❌ Daily learning file missing")
    status_ok = False

# ===============================
# 6. WEEKLY PICKS (OPTIONAL)
# ===============================
weekly_picks = os.path.join(REPORT_DIR, "weekly_picks.xlsx")

if os.path.exists(weekly_picks):
    wp = pd.read_excel(weekly_picks)
    print(f"✅ Weekly picks generated: {len(wp)}")
else:
    print("ℹ️ Weekly picks not generated yet (OK early stage)")

# ===============================
# FINAL STATUS
# ===============================
print("\n==============================")

if status_ok:
    print("🟢 SYSTEM STATUS: HEALTHY")
else:
    print("🔴 SYSTEM STATUS: ATTENTION NEEDED")

print("==============================\n")
