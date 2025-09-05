# app/api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.forecast_realtime import forecast_next_kp

app = FastAPI(title="AI Space Weather Guardian API")

# Allow Streamlit frontend (any origin for now; can restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "AI Space Weather Guardian API running"}

@app.get("/forecast")
def forecast():
    """Return forecasts for 1h, 3h, 6h horizons"""
    res = forecast_next_kp(horizons=(1, 3, 6))
    return {
        "forecasts": res["forecasts"],   # dict {"1h": val, "3h": val, "6h": val}
        "uncertainty_kp": res.get("uncertainty_kp", 0.3),
        "source": "railway-api"
    }
