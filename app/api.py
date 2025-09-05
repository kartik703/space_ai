from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.forecast_realtime import forecast_next_kp, models_available

app = FastAPI(
    title="AI Space Weather Guardian API",
    description="Kp forecasts (1h/3h/6h) with simple uncertainty; safe fallback if models missing.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "AI Space Weather Guardian", "models": models_available()}

@app.get("/forecast")
def forecast(hours: str = "1,3,6"):
    try:
        horizons = tuple(int(h.strip()) for h in hours.split(",") if h.strip())
        return forecast_next_kp(horizons=horizons)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
