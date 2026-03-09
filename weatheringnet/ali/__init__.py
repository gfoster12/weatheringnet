"""
ALI — Allostatic Load Index module.

Computes cumulative physiological stress scores from NHANES biomarker data
using three scoring methods (count, z-score, PCA). Grounded in Seeman et al.
(1997) and Geronimus et al. (2006) weathering frameworks.

Classes:
    ALICalculator   — Fits and scores allostatic load from biomarker DataFrames.

Functions:
    run_ali_pipeline        — End-to-end NHANES ingestion → ALI computation.
    compute_stratified_ali  — ALI scores stratified by race/sex/age.
    load_nhanes_cycle       — Load a single NHANES cycle from XPT files.
    preprocess_nhanes       — Clean and recode NHANES variables.

Constants:
    BIOMARKER_REGISTRY      — Full registry of biomarker configs with thresholds.
    PRIMARY_ALI_BIOMARKERS  — 8-biomarker subset for the primary ALI score.
    EXTENDED_ALI_BIOMARKERS — 12-biomarker extended set with neuroendocrine markers.
"""

from weatheringnet.ali.biomarkers import (
    BIOMARKER_REGISTRY,
    EXTENDED_ALI_BIOMARKERS,
    PRIMARY_ALI_BIOMARKERS,
    BiomarkerConfig,
    RiskDirection,
)
from weatheringnet.ali.calculator import ALICalculator, ScoringMethod
from weatheringnet.ali.pipeline import (
    compute_stratified_ali,
    load_nhanes_cycle,
    preprocess_nhanes,
    run_ali_pipeline,
)

__all__ = [
    "ALICalculator",
    "ScoringMethod",
    "BIOMARKER_REGISTRY",
    "PRIMARY_ALI_BIOMARKERS",
    "EXTENDED_ALI_BIOMARKERS",
    "BiomarkerConfig",
    "RiskDirection",
    "run_ali_pipeline",
    "compute_stratified_ali",
    "load_nhanes_cycle",
    "preprocess_nhanes",
]
