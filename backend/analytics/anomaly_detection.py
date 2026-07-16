"""
Anomaly Detection Engine
-------------------------
Uses Isolation Forest over structured work-order features (downtime,
cost, frequency) to flag abnormal maintenance patterns and outlier
assets. Also computes simple time-series frequency escalation per
equipment tag (risk escalation detection).
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


def detect_anomalies(work_orders: list[dict]) -> dict:
    if len(work_orders) < 5:
        return {"anomalies": [], "note": "Need at least 5 work orders for reliable anomaly detection."}

    df = pd.DataFrame(work_orders)
    for col in ("downtime_hours", "cost"):
        if col not in df.columns:
            df[col] = 0.0
    df["downtime_hours"] = pd.to_numeric(df["downtime_hours"], errors="coerce").fillna(0.0)
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0.0)

    freq = df.groupby("equipment_tag").size().rename("frequency")
    df = df.merge(freq, on="equipment_tag", how="left")

    features = df[["downtime_hours", "cost", "frequency"]].fillna(0)
    model = IsolationForest(contamination=0.15, random_state=42, n_estimators=150)
    preds = model.fit_predict(features)
    scores = model.decision_function(features)

    df["is_anomaly"] = preds == -1
    df["anomaly_score"] = -scores  # higher = more anomalous

    anomalies = df[df["is_anomaly"]].sort_values("anomaly_score", ascending=False)
    out = []
    for _, row in anomalies.iterrows():
        out.append({
            "equipment_tag": row.get("equipment_tag", "unknown"),
            "date": row.get("date", ""),
            "downtime_hours": float(row["downtime_hours"]),
            "cost": float(row["cost"]),
            "anomaly_score": round(float(row["anomaly_score"]), 3),
            "reason": "Unusual combination of downtime, cost, or maintenance frequency "
                      "relative to fleet baseline.",
        })

    escalation = (
        freq.sort_values(ascending=False).head(5).to_dict()
    )

    return {"anomalies": out[:20], "highest_frequency_assets": escalation}
