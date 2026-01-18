import os
import pandas as pd

DATA_DIR = "market_ai/data/prices"

for file in os.listdir(DATA_DIR):
    if not file.endswith(".csv"):
        continue

    path = f"{DATA_DIR}/{file}"
    df = pd.read_csv(path)

    if "date" in df.columns:
        df = df.drop_duplicates(subset=["date"], keep="last")
        df.to_csv(path, index=False)

print("✅ Duplicate dates removed")
