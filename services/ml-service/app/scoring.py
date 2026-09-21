"""
Inference: LightGBM risk score (isotonic-calibrated), IsolationForest
novelty channel (Tier 2, deliberately NOT blended into risk_score -- see
docs/model-card.md), and SHAP -> reason-code explanation.

Model artifacts are loaded once at process startup (see main.py lifespan),
not per-request -- this is what keeps /score under ~50ms.
"""
from __future__ import annotations

import json
import math
import os

import joblib
import pandas as pd
import shap

from app.config import settings
from app.features import build_feature_vector, FEATURE_TO_REASON_CODE

_STATE: dict = {}


def load_artifacts():
    d = settings.model_dir
    model = joblib.load(os.path.join(d, "model.pkl"))
    iso = joblib.load(os.path.join(d, "isoforest.pkl"))
    iso_cols = joblib.load(os.path.join(d, "isoforest_columns.pkl"))
    with open(os.path.join(d, "metrics.json")) as f:
        metrics = json.load(f)

    raw_lgbm = model.calibrated_classifiers_[0].estimator
    explainer = shap.TreeExplainer(raw_lgbm)

    _STATE.update({
        "model": model,
        "iso": iso,
        "iso_cols": iso_cols,
        "metrics": metrics,
        "explainer": explainer,
        "version": metrics.get("version", "v1.0.0"),
        "thresholds": {
            "low": metrics["threshold_low"],
            "high": metrics["threshold_high"],
            "decline": metrics["threshold_decline"],
        },
    })
    return _STATE


def is_loaded() -> bool:
    return "model" in _STATE


def hot_swap(model, iso, iso_cols, version: str, metrics: dict) -> None:
    """Promote a newly retrained model into the live serving path. Called
    only after the caller has already checked the new model's holdout
    PR-AUC is >= the incumbent's -- the gate lives in main.py's
    /internal/retrain, this function just performs the swap."""
    raw_lgbm = model.calibrated_classifiers_[0].estimator
    explainer = shap.TreeExplainer(raw_lgbm)
    _STATE.update({
        "model": model,
        "iso": iso,
        "iso_cols": iso_cols,
        "metrics": metrics,
        "explainer": explainer,
        "version": version,
        "thresholds": {
            "low": metrics["threshold_low"],
            "high": metrics["threshold_high"],
            "decline": metrics["threshold_decline"],
        },
    })


def _action_for(score: float) -> str:
    t = _STATE["thresholds"]
    if score < t["low"]:
        return "APPROVE"
    if score < t["high"]:
        return "STEP_UP"
    if score < t["decline"]:
        return "REVIEW"
    return "DECLINE"


def _anomaly_score(X: pd.DataFrame) -> float:
    iso = _STATE["iso"]
    cols = _STATE["iso_cols"]
    row = X[cols]
    # decision_function: higher = more normal. Sigmoid-compress the negated
    # value into (0, 1), where 1 = highly anomalous. Scale factor chosen so
    # typical IsolationForest decision_function magnitudes (~-0.2..0.2) map
    # to a usable spread; see docs/model-card.md for the calibration note.
    raw = float(iso.decision_function(row)[0])
    return 1.0 / (1.0 + math.exp(raw * 18.0))


def score_application(app_dict: dict) -> dict:
    X = build_feature_vector(app_dict)
    model = _STATE["model"]

    risk_score = float(model.predict_proba(X)[:, 1][0])
    anomaly_score = _anomaly_score(X)
    action = _action_for(risk_score)

    explainer = _STATE["explainer"]
    shap_values = explainer.shap_values(X)
    if isinstance(shap_values, list):
        contrib = shap_values[1][0]  # class-1 (fraud) contributions
    else:
        contrib = shap_values[0]

    pairs = list(zip(X.columns, X.iloc[0].values, contrib))
    pairs.sort(key=lambda p: -abs(p[2]))
    top5 = pairs[:5]

    shap_top = []
    reason_codes = []
    for feat, val, c in top5:
        direction = "increases_risk" if c > 0 else "decreases_risk"
        shap_top.append({
            "feature": feat,
            "value": float(val) if not pd.isna(val) else None,
            "contribution": float(c),
            "direction": direction,
        })
        if c > 0:
            code = FEATURE_TO_REASON_CODE.get(feat)
            if code and code not in reason_codes:
                reason_codes.append(code)

    if action == "DECLINE" and not reason_codes:
        reason_codes.append("NOVEL_PATTERN_UNSCORED")

    return {
        "risk_score": round(risk_score, 5),
        "anomaly_score": round(anomaly_score, 5),
        "action": action,
        "reason_codes": reason_codes,
        "shap_top": shap_top,
        "model_version": _STATE["version"],
    }
