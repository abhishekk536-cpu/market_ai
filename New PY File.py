import os
import json
from datetime import date, datetime

# -------------------------------
# HELPERS
# -------------------------------
def run(cmd):
    print(f"\n▶ RUNNING: {cmd}")
    code = os.system(cmd)
    if code != 0:
        print("❌ STEP FAILED:", cmd)
        exit(1)

# -------------------------------
# STATE FILES
# -------------------------------
STATE_DIR = "market_ai/state"
os.makedirs(STATE_DIR, exist_ok=True)

LAST_RUN_FILE = f"{STATE_DIR}/last_run.json"
LAST_WEEKLY_FILE = f"{STATE_DIR}/last_weekly.json"

TODAY = date.today().isoformat()
WEEKDAY = datetime.today().weekday()  # Monday=0, Friday=4

# -------------------------------
# DAILY RUN LOCK
# -------------------------------
if os.path.exists(LAST_RUN_FILE):
    with open(LAST_RUN_FILE, "r") as f:
        last = json.load(f)
        if last.get("date") == TODAY:
            print("⏹ Already ran today. Exiting.")
            exit(0)

# -------------------------------
# STEP SEQUENCE (DAILY)
# -------------------------------
print("\n🚀 MARKET AI — DAILY PIPELINE STARTED")

run("python tools/filter_by_market_cap.py")
run("python tools/collect_daily_prices.py")
run("python tools/compute_features.py")
run("python tools/daily_learning_metrics.py")
run("python tools/generate_daily_excel.py")

# -------------------------------
# WEEKLY CONDITION
# -------------------------------
run_weekly = False

if WEEKDAY == 4:  # Friday
    run_weekly = True

if os.path.exists(LAST_WEEKLY_FILE):
    with open(LAST_WEEKLY_FILE, "r") as f:
        last_weekly = json.load(f)
        if last_weekly.get("date") == TODAY:
            run_weekly = False

# -------------------------------
# WEEKLY RUN
# -------------------------------
if run_weekly:
    print("\n📅 WEEKLY MODE ACTIVATED")
    run("python tools/generate_weekly_picks.py")

    with open(LAST_WEEKLY_FILE, "w") as f:
        json.dump({"date": TODAY}, f)

# -------------------------------
# SAVE DAILY LOCK
# -------------------------------
with open(LAST_RUN_FILE, "w") as f:
    json.dump({"date": TODAY}, f)

print("\n✅ MARKET AI — PIPELINE COMPLETED SUCCESSFULLY")
