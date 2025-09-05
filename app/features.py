# app/features.py
import os, joblib, pandas as pd
from sklearn.preprocessing import StandardScaler

PROCESSED = "data/processed.csv"
SCALER_X_FILE = "models/scaler_X.pkl"
SCALER_Y_FILE = "models/scaler_y.pkl"

def build_features(df: pd.DataFrame, target="Kp", max_lag=12):
    out = df.copy()
    for l in range(1, 4):
        out[f"{target}_lag{l}"] = out[target].shift(l)
    out = out.dropna().reset_index(drop=True)
    return out

def process_and_save():
    os.makedirs("models", exist_ok=True)
    if not os.path.exists("data/raw_data.csv"):
        return None
    df = pd.read_csv("data/raw_data.csv", parse_dates=["time_tag"])
    feats = build_features(df)
    feats.to_csv(PROCESSED, index=False)
    # Fit simple scalers for future use
    X_cols = [c for c in feats.columns if c not in ["time_tag","Kp"]]
    sx, sy = StandardScaler(), StandardScaler()
    sx.fit(feats[X_cols].values)
    sy.fit(feats[["Kp"]].values)
    joblib.dump(sx, SCALER_X_FILE)
    joblib.dump(sy, SCALER_Y_FILE)
    return PROCESSED
