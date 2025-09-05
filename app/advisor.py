from typing import Dict, Tuple

LOW_MAX = 4.0
MED_MAX = 6.0

def risk_level(kp: float) -> str:
    if kp < LOW_MAX: return "Low"
    if kp < MED_MAX: return "Medium"
    return "High"

def advisory_message(kp: float) -> str:
    lvl = risk_level(kp)
    if lvl == "Low":
        return "✅ No significant space weather impact expected."
    if lvl == "Medium":
        return "⚠️ Moderate geomagnetic activity. GPS/HF may degrade; slight satellite drag possible."
    return "🚨 High storm risk! Potential disruptions to satellites, aviation (HF/GNSS), and power grids."

def sector_advisory(kp: float) -> Dict[str, str]:
    lvl = risk_level(kp)
    if lvl == "Low":
        return {"Aviation":"Normal ops. No significant HF/GNSS risk.",
                "Satellites":"Nominal environment; minimal radiation/drag.",
                "Energy":"No geomagnetic disturbances expected."}
    if lvl == "Medium":
        return {"Aviation":"Polar ops: possible HF blackouts, GNSS dips. Plan alternates.",
                "Satellites":"Slight drag/comms degradation possible. Heighten monitoring.",
                "Energy":"Minor GICs at high latitudes possible. Review standby procedures."}
    return {"Aviation":"Reroute polar flights if feasible. Expect HF/GNSS unreliability.",
            "Satellites":"Elevated radiation risk; consider safe-mode windows.",
            "Energy":"⚡ Heightened GIC risk. Engage storm procedures & load-balancing."}
