"""
ALI Calculator: Three scoring methods for allostatic load computation.

Methods:
    count_method    - Standard: count biomarkers exceeding risk thresholds
                      (Seeman et al. 1997; most widely cited in weathering lit)
    z_score_method  - Continuous: sum of z-scores relative to reference population
                      (Geronimus et al. 2006)
    pca_method      - Data-driven: first principal component of biomarker matrix
                      (exploratory; useful for sensitivity analysis)
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from weatheringnet.ali.biomarkers import (
    BIOMARKER_REGISTRY,
    PRIMARY_ALI_BIOMARKERS,
    RiskDirection,
)

ScoringMethod = Literal["count", "z_score", "pca"]


class ALICalculator:
    """
    Computes Allostatic Load Index scores from a biomarker DataFrame.

    Parameters
    ----------
    biomarkers : list[str]
        Keys from BIOMARKER_REGISTRY to include. Defaults to PRIMARY_ALI_BIOMARKERS.
    method : ScoringMethod
        Scoring method. Default is "count" (most interpretable, most cited).
    reference_group : str or None
        NHANES race/sex stratum to use as z-score reference (e.g., "White_Female").
        None uses full-sample statistics.
    """

    def __init__(
        self,
        biomarkers: list[str] = PRIMARY_ALI_BIOMARKERS,
        method: ScoringMethod = "count",
        reference_group: str | None = None,
    ):
        self.biomarkers = biomarkers
        self.method = method
        self.reference_group = reference_group
        self._scaler = StandardScaler()
        self._pca = PCA(n_components=1)

    def fit(self, df: pd.DataFrame, group_col: str | None = None) -> ALICalculator:
        """
        Fit reference statistics for z-score or PCA methods.

        Parameters
        ----------
        df : pd.DataFrame
            NHANES biomarker data. Columns must include NHANES codes or
            renamed biomarker names matching BIOMARKER_REGISTRY.
        group_col : str | None
            Column name for race/sex stratification (used when reference_group set).
        """
        X = self._extract_biomarker_matrix(df)

        if self.reference_group and group_col:
            ref_mask = df[group_col] == self.reference_group
            if ref_mask.sum() < 30:
                logger.warning(
                    f"Reference group '{self.reference_group}' has <30 observations. "
                    "Using full sample as reference."
                )
                self._scaler.fit(X)
            else:
                self._scaler.fit(X[ref_mask])
        else:
            self._scaler.fit(X)

        if self.method == "pca":
            X_scaled = self._scaler.transform(X)
            self._pca.fit(X_scaled)
            logger.info(
                f"PCA ALI — PC1 explains "
                f"{self._pca.explained_variance_ratio_[0]:.1%} of variance"
            )

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute ALI scores for each individual in df.

        Returns
        -------
        pd.DataFrame
            Original df with added columns:
            - ali_score       : primary ALI score
            - ali_score_count : count method score (always computed)
            - ali_missing_n   : number of missing biomarkers
            - ali_{biomarker} : individual biomarker risk flags (count method)
        """
        result = df.copy()
        X = self._extract_biomarker_matrix(df)

        # Count method (always compute for interpretability)
        risk_flags = self._count_method(X)
        for col in risk_flags.columns:
            result[col] = risk_flags[col].values
        result["ali_score_count"] = risk_flags.sum(axis=1)
        result["ali_missing_n"] = X.isnull().sum(axis=1)

        # Primary score by selected method
        if self.method == "count":
            result["ali_score"] = result["ali_score_count"]
        elif self.method == "z_score":
            result["ali_score"] = self._z_score_method(X)
        elif self.method == "pca":
            result["ali_score"] = self._pca_method(X)

        return result

    def fit_transform(
        self, df: pd.DataFrame, group_col: str | None = None
    ) -> pd.DataFrame:
        return self.fit(df, group_col).transform(df)

    # ── Private Methods ────────────────────────────────────────────────────────

    def _extract_biomarker_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract biomarker columns, handling both NHANES codes and friendly names."""
        cols = {}
        for key in self.biomarkers:
            config = BIOMARKER_REGISTRY[key]
            if config.nhanes_code in df.columns:
                cols[key] = df[config.nhanes_code]
            elif key in df.columns:
                cols[key] = df[key]
            else:
                logger.warning(
                    f"Biomarker '{key}' not found in DataFrame — will be NaN."
                )
                cols[key] = np.nan
        return pd.DataFrame(cols, index=df.index)

    def _count_method(self, X: pd.DataFrame) -> pd.DataFrame:
        """Binary risk flags: 1 if biomarker exceeds clinical threshold."""
        flags = pd.DataFrame(index=X.index)
        for key in self.biomarkers:
            config = BIOMARKER_REGISTRY[key]
            col = X[key] if key in X.columns else pd.Series(np.nan, index=X.index)
            if config.risk_direction == RiskDirection.HIGH:
                flags[f"ali_{key}"] = (col > config.risk_threshold).astype(float)
            else:
                flags[f"ali_{key}"] = (col < config.risk_threshold).astype(float)
            flags[f"ali_{key}"] = flags[f"ali_{key}"].where(col.notna(), other=np.nan)
        return flags

    def _z_score_method(self, X: pd.DataFrame) -> pd.Series:
        """Sum of z-scores; negative z-score for 'low = risk' biomarkers."""
        X_filled = X.fillna(X.mean())
        X_scaled = pd.DataFrame(
            self._scaler.transform(X_filled),
            columns=X.columns,
            index=X.index,
        )
        for key in self.biomarkers:
            config = BIOMARKER_REGISTRY.get(key)
            if config and config.risk_direction == RiskDirection.LOW:
                X_scaled[key] = -X_scaled[key]
        return X_scaled.sum(axis=1)

    def _pca_method(self, X: pd.DataFrame) -> pd.Series:
        """First principal component of scaled biomarker matrix."""
        X_filled = X.fillna(X.mean())
        X_scaled = self._scaler.transform(X_filled)
        scores = self._pca.transform(X_scaled)[:, 0]
        # Orient so higher = greater allostatic load
        if np.corrcoef(scores, X_filled.mean(axis=1))[0, 1] < 0:
            scores = -scores
        return pd.Series(scores, index=X.index)

    def biomarker_contributions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return mean biomarker risk flag rates by subgroup for equity analysis.

        Useful for understanding which biomarkers drive ALI disparities
        between race/sex groups.
        """
        result = self.transform(df)
        flag_cols = [
            c for c in result.columns if c.startswith("ali_") and c != "ali_score"
        ]
        return result[flag_cols].mean().sort_values(ascending=False)
