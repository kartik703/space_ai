# app/ingestion.py
import os
import requests
import pandas as pd
from datetime import datetime

NOAA_KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
RAW = "data/raw_data.csv"


def update_dataset() -> str:
    """
    Fetch from NOAA and append to raw_data.csv.
    Falls back to a synthetic row if NOAA unavailable.
    Returns the path to the raw CSV.
    """
    os.makedirs("data", exist_ok=True)

    try:
        r = requests.get(NOAA_KP_URL, timeout=15)
        r.raise_for_status()
        data = r.json()

        df = pd.DataFrame(data)
        df["time_tag"] = pd.to_datetime(df["time_tag"], utc=True)
        df["kp_index"] = pd.to_numeric(df["kp_index"], errors="coerce")

    except Exception as e:
        print(f"[WARN] NOAA fetch failed: {e}")
        # fallback synthetic row
        row = {"time_tag": datetime.utcnow(), "kp_index": 2.0}
        df = pd.DataFrame([row])

    # Append or write
    if os.path.exists(RAW):
        df.to_csv(RAW, mode="a", header=False, index=False)
    else:
        df.to_csv(RAW, index=False)

    return RAW


def fetch_noaa_kp() -> pd.DataFrame:
    """
    Load cached Kp data from raw_data.csv.
    Returns a DataFrame with [time_tag, kp_index].
    """
    if os.path.exists(RAW):
        return pd.read_csv(RAW, parse_dates=["time_tag"])
    else:
        return pd.DataFrame(
            {"time_tag": [pd.Timestamp.utcnow()], "kp_index": [2.0]}
        )


def fetch_latest_kp() -> float:
    """
    Return the most recent Kp index.
    """
    df = fetch_noaa_kp()
    if not df.empty:
        return float(df["kp_index"].iloc[-1])
    return 2.0
