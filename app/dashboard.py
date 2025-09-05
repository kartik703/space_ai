import os, sys
import requests
import pandas as pd
import streamlit as st
import altair as alt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.advisor import risk_level, advisory_message, sector_advisory
from app.forecast_realtime import forecast_next_kp

API_URL = os.getenv("API_URL")  # set on Streamlit Cloud; if unset we’ll fallback to local model

st.set_page_config(page_title="AI Space Weather Guardian", layout="centered")
st.title("🌌 AI Space Weather Guardian")
st.caption("AI-powered multi-horizon forecasts of geomagnetic activity (Kp).")

def risk_badge(kp_val: float) -> str:
    lvl = risk_level(kp_val)
    color = {"Low": "#16a34a", "Medium": "#f59e0b", "High": "#ef4444"}[lvl]
    return f"<span style='background:{color}22;color:{color};padding:3px 8px;border-radius:8px;font-weight:600'>{lvl}</span>"

# Minimal latest Kp (static placeholder for first deploy; you can wire real ingestion later)
latest_kp = 2.0
st.metric("Latest Kp Index", f"{latest_kp:.2f}", delta=0.0)

st.subheader("Current Risk Assessment")
st.markdown(f"**Level**: {risk_badge(latest_kp)}", unsafe_allow_html=True)
st.info(advisory_message(latest_kp))

st.subheader("📡 Sector-Specific Advisories")
msgs = sector_advisory(latest_kp)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("✈️ **Aviation**")
    st.success(msgs["Aviation"]) if "⚠️" not in msgs["Aviation"] else st.warning(msgs["Aviation"])
with c2:
    st.markdown("🛰 **Satellites**")
    st.success(msgs["Satellites"]) if "⚠️" not in msgs["Satellites"] else st.warning(msgs["Satellites"])
with c3:
    st.markdown("⚡ **Energy Grids**")
    st.success(msgs["Energy"]) if "⚡" not in msgs["Energy"] else st.warning(msgs["Energy"])

st.subheader("🔮 Forecasts (Kp) — 1h / 3h / 6h")
results, uncert, source = None, None, "api"
try:
    if API_URL:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        payload = r.json()
        results = payload.get("forecasts", {})
        uncert = float(payload.get("uncertainty_kp", 0.3))
    else:
        raise RuntimeError("API_URL not set")
except Exception:
    try:
        res = forecast_next_kp()
        results = res["forecasts"]
        uncert = float(res.get("uncertainty_kp", 0.3))
        source = "local"
        st.info("Using local model fallback (no API).")
    except Exception as ee:
        st.error(f"❌ Could not fetch forecasts via API or local model: {ee}")

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

    # Simple chart with future points
    hist = pd.DataFrame({"Time": pd.date_range(end=pd.Timestamp.utcnow(), periods=24, freq="H"),
                         "Kp": [latest_kp]*24, "Type":"History"})
    last_t = hist["Time"].iloc[-1]
    items = sorted(((int(k[:-1]), float(v)) for k, v in results.items()), key=lambda x: x[0])
    f_times = [last_t + pd.Timedelta(hours=h) for h, _ in items]
    f_vals  = [v for _, v in items]
    fdf = pd.DataFrame({"Time": f_times, "Kp": f_vals, "Type":"Forecast"})
    fdf["Kp_lo"] = fdf["Kp"] - (uncert or 0.0)
    fdf["Kp_hi"] = fdf["Kp"] + (uncert or 0.0)
    combined = pd.concat([hist, fdf])
    base = alt.Chart(combined).encode(x="Time:T")
    st.altair_chart(
        (base.transform_filter(alt.datum.Type=="History").mark_line(color="#60a5fa").encode(y="Kp:Q") +
         alt.Chart(fdf).mark_area(opacity=0.2, color="#f59e0b").encode(x="Time:T", y="Kp_lo:Q", y2="Kp_hi:Q") +
         alt.Chart(fdf).mark_line(color="#f59e0b").encode(x="Time:T", y="Kp:Q")
        ).properties(height=320),
        use_container_width=True
    )
