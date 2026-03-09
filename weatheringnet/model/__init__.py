"""
Model — AID risk prediction and SHAP-based explainability.

XGBoost-based transgenerational autoimmune disease risk predictor with
calibrated probabilities, fairness evaluation by race/sex, and SHAP
feature importances mapped to biological mechanisms from the paper.

Classes:
    AIDRiskModel    — XGBoost/logistic classifier with calibration and fairness.
    SHAPExplainer   — SHAP-based mechanistic interpretability layer.

Constants:
    FEATURE_MECHANISM_MAP — Maps model features to paper biological mechanisms.
"""

from weatheringnet.model.explainer import FEATURE_MECHANISM_MAP, SHAPExplainer
from weatheringnet.model.trainer import AIDRiskModel

__all__ = [
    "AIDRiskModel",
    "SHAPExplainer",
    "FEATURE_MECHANISM_MAP",
]
