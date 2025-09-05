# app/ingestion.py
import os, pandas as pd
from datetime import datetime

RAW = "data/raw_data.csv"

def update_dataset():
    os.makedirs("data", exist_ok=True)
    # Append a tiny synthetic row for now; replace with real NOAA ingestion
    row = {"time_tag": datetime.utcnow().isoformat(timespec="seconds"), "Kp": 2.0}
    df = pd.DataFrame([row])
    if os.path.exists(RAW):
        df.to_csv(RAW, mode="a", header=False, index=False)
    else:
        df.to_csv(RAW, index=False)
    return RAW

def fetch_noaa_kp():
    # For dashboard’s metric: use last few rows of our raw
    if os.path.exists(RAW):
        return pd.read_csv(RAW, parse_dates=["time_tag"])
    return pd.DataFrame({"time_tag": [pd.Timestamp.utcnow()], "Kp":[2.0]})
