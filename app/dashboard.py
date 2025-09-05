# app/dashboard.py
import os
import sys
import requests
import pandas as pd
import streamlit as st
import altair as alt

# Allow "from app.xxx import ..." when run by Streamlit
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.advisor import risk_level, advisory_message, sector_advisory
from app.forecast_realtime import forecast_next_kp
from app.ingestion import fetch_latest_kp

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
API_URL = os.getenv("API_URL")  # Set to Railway API endpoint
st.set_page_config(page_title="AI Space Weather Guardian", layout="centered")

st.title("🌌 AI Space Weather Guardian")
st.caption("AI-powered **multi-horizon forecasts** of geomagnetic activity (**Kp**).")

def risk_badge(kp_val: float) -> str:
    lvl = risk_level(kp_val)
    color = {"Low": "#16a34a", "Medium": "#f59e0b", "High": "#ef4444"}[lvl]
    return f"<span style='background:{color}22;color:{color};padding:3px 8px;border-radius:8px;font-weight:600'>{lvl}</span>"

# ─────────────────────────────────────────────
# Latest Kp Index
# ─────────────────────────────────────────────
try:
    latest_kp = fetch_latest_kp()
except Exception:
    latest_kp = 2.0  # fallback safe default
st.metric("Latest Kp Index", f"{latest_kp:.2f}", delta=0.0)

# ─────────────────────────────────────────────
# Current Risk
# ─────────────────────────────────────────────
st.subheader("Current Risk Assessment")
st.markdown(f"**Level**: {risk_badge(latest_kp)}", unsafe_allow_html=True)
st.info(advisory_message(latest_kp))

# ─────────────────────────────────────────────
# Sector-Specific Advisories
# ─────────────────────────────────────────────
st.subheader("📡 Sector-Specific Advisories")
msgs = sector_advisory(latest_kp)
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("✈️ **Aviation**")
    if "⚠️" in msgs["Aviation"] or "Reroute" in msgs["Aviation"]:
        st.warning(msgs["Aviation"])
    else:
        st.success(msgs["Aviation"])

with c2:
    st.markdown("🛰 **Satellites**")
    if "⚠️" in msgs["Satellites"] or "safe-mode" in msgs["Satellites"]:
        st.warning(msgs["Satellites"])
    else:
        st.success(msgs["Satellites"])

with c3:
    st.markdown("⚡ **Energy Grids**")
    if "⚠️" in msgs["Energy"] or "risk" in msgs["Energy"].lower():
        st.warning(msgs["Energy"])
    else:
        st.success(msgs["Energy"])

# ─────────────────────────────────────────────
# Forecasts
# ─────────────────────────────────────────────
st.subheader("🔮 Forecasts (Kp) — 1h / 3h / 6h")
results, uncert, source = None, None, "api"

try:
    if API_URL:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        payload = r.json()
        results = payload.get("forecasts", {})
        uncert = float(payload.get("uncertainty_kp", 0.3))
        st.caption(f"🟢 Using API at [{API_URL}]({API_URL})")
    else:
        raise RuntimeError("API_URL not set")
except Exception as api_err:
    try:
        res = forecast_next_kp(horizons=(1, 3, 6))
        results = res["forecasts"]
        uncert = float(res.get("uncertainty_kp", 0.3))
        source = "local"
        st.warning("⚠️ Using local model fallback (API not available).")
    except Exception as local_err:
        st.error(
            "❌ Could not get forecasts via API or local model.\n\n"
            f"API error: {api_err}\nLocal error: {local_err}"
        )

if results:
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Best Model Forecasts**")
        for h, v in results.items():
            v = float(v)
            st.markdown(f"{h}: **{v:.2f} ± {uncert:.2f}** &nbsp; {risk_badge(v)}", unsafe_allow_html=True)

    with col2:
        peak_h = max(results, key=lambda k: results[k])
        peak_v = float(results[peak_h])
        st.write("**Advisory (Peak Horizon)**")
        st.markdown(f"Peak: **{peak_h}**")
        st.markdown(f"Kp Forecast: **{peak_v:.2f} ± {uncert:.2f}** &nbsp; {risk_badge(peak_v)}", unsafe_allow_html=True)
        st.caption(advisory_message(peak_v))

    st.caption(f"Forecast source: **{source}**")

    # ─────────────────────────────────────────
    # Chart
    # ─────────────────────────────────────────
    history = pd.DataFrame(
        {
            "Time": pd.date_range(end=pd.Timestamp.utcnow(), periods=24, freq="h"),
            "Kp": [latest_kp] * 24,
            "Type": "History",
        }
    )
    last_t = history["Time"].iloc[-1]
    items = sorted(((int(k[:-1]), float(v)) for k, v in results.items()), key=lambda x: x[0])
    f_times = [last_t + pd.Timedelta(hours=h) for h, _ in items]
    f_vals = [v for _, v in items]
    fdf = pd.DataFrame({"Time": f_times, "Kp": f_vals, "Type": "Forecast"})
    fdf["Kp_lo"] = fdf["Kp"] - uncert
    fdf["Kp_hi"] = fdf["Kp"] + uncert

    combined = pd.concat([history, fdf], ignore_index=True)

    base = alt.Chart(combined).encode(x="Time:T")
    hist_line = (
        base.transform_filter(alt.datum.Type == "History")
        .mark_line(color="#60a5fa")
        .encode(y=alt.Y("Kp:Q", title="Kp"))
    )
    band = alt.Chart(fdf).mark_area(opacity=0.2, color="#f59e0b").encode(
        x="Time:T", y="Kp_lo:Q", y2="Kp_hi:Q"
    )
    forecast_line = alt.Chart(fdf).mark_line(color="#f59e0b").encode(x="Time:T", y="Kp:Q")

    st.altair_chart((hist_line + band + forecast_line).properties(height=320), use_container_width=True)
