import os
import sys
import subprocess
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def run_step(name, cmd):
    print(f"\n▶ RUNNING: {name}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ FAILED: {name}")
        sys.exit(1)
    print(f"✅ COMPLETED: {name}")

print("\n🚀 MARKET AI — ONE BUTTON RUN\n")

# ===============================
# 1. COLLECT DAILY PRICES
# ===============================
run_step(
    "Daily Price Collection",
    "python tools/collect_daily_prices.py"
)

# ===============================
# 2. FEATURE ENGINEERING
# ===============================
run_step(
    "Feature Engineering",
    "python tools/compute_features.py"
)

# ===============================
# 3. DAILY LEARNING + SIGNAL LOG
# ===============================
run_step(
    "Daily Learning Metrics",
    "python tools/daily_learning_metrics.py"
)

# ===============================
# 4. WEEKLY PICKS (ONLY FRIDAY)
# ===============================
today = datetime.today().weekday()  # Monday=0, Friday=4

if today == 4:
    run_step(
        "Weekly Stock Selection",
        "python tools/generate_weekly_picks.py"
    )
else:
    print("\nℹ️ Not Friday — skipping weekly picks")

# ===============================
# 5. SYSTEM HEALTH CHECK
# ===============================
run_step(
    "System Health Check",
    "python tools/system_health_check.py"
)

# ===============================
# 6. LAUNCH DASHBOARD
# ===============================
print("\n🌐 Launching Dashboard...\n")
subprocess.Popen(
    "python -m streamlit run dashboard.py",
    shell=True
)

print("\n✅ SYSTEM RUN COMPLETE — DASHBOARD OPENING")
