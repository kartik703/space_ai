import os
import json
import numpy as np
import joblib
import torch
import torch.nn as nn

MODELS_DIR = "models"
SCALER_X = os.path.join(MODELS_DIR, "scaler_X.pkl")
SCALER_Y = os.path.join(MODELS_DIR, "scaler_y.pkl")
GRU_PTH = os.path.join(MODELS_DIR, "gru_model.pth")
BEST_JSON = os.path.join(MODELS_DIR, "model_best.json")

def models_available():
    return {
        "scaler_X": os.path.exists(SCALER_X),
        "scaler_y": os.path.exists(SCALER_Y),
        "gru": os.path.exists(GRU_PTH),
        "meta": os.path.exists(BEST_JSON),
    }

class GRUModel(nn.Module):
    def __init__(self, input_size=8, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers=num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, 1)
    def forward(self, x):
        out, _ = self.gru(x)
        out = out[:, -1, :]
        return self.fc(out)

def _fallback_forecast(horizons=(1,3,6)):
    # Conservative, safe fallback
    out = {f"{h}h": 2.2 for h in horizons}
    return {"forecasts": out, "model": "fallback", "uncertainty_kp": 0.4}

def forecast_next_kp(horizons=(1,3,6), seq_len=12):
    # If any required file missing → fallback to safe forecast
    if not all(models_available().values()):
        return _fallback_forecast(horizons)

    # Minimal synthetic last sequence: zeros (you can wire real features later)
    input_size = 8  # must match training; adjust to your feature count
    seq = np.zeros((1, seq_len, input_size), dtype=np.float32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = GRUModel(input_size=input_size)
    model.load_state_dict(torch.load(GRU_PTH, map_location=device))
    model.to(device).eval()

    forecasts = []
    with torch.no_grad():
        cur = torch.tensor(seq, dtype=torch.float32).to(device)
        for _ in horizons:
            yhat = model(cur).cpu().numpy().flatten()[0]
            forecasts.append(float(yhat))
            # roll forward (placeholder)
    # Inverse-scale target if scaler_y exists
    try:
        scaler_y = joblib.load(SCALER_Y)
        kp_vals = scaler_y.inverse_transform(np.array(forecasts).reshape(-1,1)).flatten()
        kp_vals = [float(v) for v in kp_vals]
    except Exception:
        kp_vals = [float(v) for v in forecasts]

    rmse_kp = 0.3
    try:
        if os.path.exists(BEST_JSON):
            with open(BEST_JSON, "r") as f:
                meta = json.load(f)
                rmse_kp = float(meta.get("rmse_kp", 0.3))
    except Exception:
        pass

    return {"forecasts": {f"{h}h": v for h, v in zip(horizons, kp_vals)},
            "model": "GRU", "uncertainty_kp": rmse_kp}
