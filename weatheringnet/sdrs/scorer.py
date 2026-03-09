"""
SDRSScorer: Combines ADI, SVI, EJScreen, and FARA into a composite
Sociodemographic Risk Score (SDRS) at the census tract level.

The SDRS operationalizes the sociodemographic risk factors explicitly
enumerated in the paper's Background section into a single linkable score.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger
from sklearn.preprocessing import MinMaxScaler

from weatheringnet.sdrs.sources import load_adi, load_ejscreen, load_fara, load_svi

# Component weights — can be overridden via config
# Default weights reflect paper's emphasis on stress/inflammation pathways
DEFAULT_WEIGHTS = {
    "adi_natrank": 0.25,  # SES disadvantage — primary weathering driver
    "svi_total": 0.25,  # Multi-domain vulnerability
    "ej_index": 0.25,  # PCB/pollution — explicitly cited for Black women
    "food_desert_flag": 0.15,  # Diet/formula — cited as early AID risk
    "svi_theme3_minority": 0.10,  # Racial minority concentration (structural racism proxy)
}


class SDRSScorer:
    """
    Builds a census-tract-level Sociodemographic Risk Score by merging
    all SDOH data sources and computing a weighted composite.

    Parameters
    ----------
    data_dir : Path
        Root directory containing subdirectories: adi/, svi/, ejscreen/, fara/
    weights : dict | None
        Component weights for composite score. Defaults to DEFAULT_WEIGHTS.
    """

    def __init__(self, data_dir: Path | str, weights: dict | None = None):
        self.data_dir = Path(data_dir)
        self.weights = weights or DEFAULT_WEIGHTS
        self._scaler = MinMaxScaler()
        self._tract_scores: pd.DataFrame | None = None

    def build(self) -> pd.DataFrame:
        """
        Load all data sources, merge on FIPS tract, compute SDRS.

        Returns
        -------
        pd.DataFrame
            One row per census tract with columns:
            - fips_tract
            - sdrs_score       : composite 0–100 score
            - sdrs_{component} : individual normalized component scores
        """
        logger.info("Loading SDOH data sources...")

        adi = load_adi(self.data_dir)
        svi = load_svi(self.data_dir)
        ej = load_ejscreen(self.data_dir)
        fara = load_fara(self.data_dir)

        # Aggregate ADI to tract level (mean of block groups within tract)
        if "fips_tract" in adi.columns:
            adi_tract = adi.groupby("fips_tract")["adi_natrank"].mean().reset_index()
        else:
            adi_tract = pd.DataFrame(columns=["fips_tract", "adi_natrank"])

        # Merge all sources on fips_tract
        merged = svi
        for df, key in [(adi_tract, "ADI"), (ej, "EJScreen"), (fara, "FARA")]:
            if not df.empty and "fips_tract" in df.columns:
                merged = merged.merge(df, on="fips_tract", how="left")
                logger.info(f"Merged {key}: {len(merged):,} tracts")

        # Normalize components to 0–100 and compute weighted composite
        component_cols = [c for c in self.weights if c in merged.columns]
        if not component_cols:
            logger.error("No SDRS component columns found in merged data.")
            return pd.DataFrame()

        X = merged[component_cols].copy()
        X_norm = pd.DataFrame(
            self._scaler.fit_transform(X.fillna(X.mean())) * 100,
            columns=[f"sdrs_{c}" for c in component_cols],
            index=merged.index,
        )

        # Weighted sum
        weights_used = {c: self.weights[c] for c in component_cols}
        total_weight = sum(weights_used.values())
        sdrs_score = sum(
            X_norm[f"sdrs_{c}"] * (w / total_weight) for c, w in weights_used.items()
        )

        merged["sdrs_score"] = sdrs_score
        result = pd.concat(
            [merged[["fips_tract"]], X_norm, merged[["sdrs_score"]]], axis=1
        )
        self._tract_scores = result

        logger.info(f"SDRS built for {len(result):,} census tracts")
        logger.info(
            f"SDRS mean={result['sdrs_score'].mean():.1f}, sd={result['sdrs_score'].std():.1f}"
        )
        return result

    def lookup(self, fips_tracts: pd.Series) -> pd.Series:
        """
        Return SDRS scores for a series of census tract FIPS codes.
        Useful for linking SDRS to individual-level cohort data.
        """
        if self._tract_scores is None:
            raise RuntimeError("Call .build() before .lookup()")
        mapping = self._tract_scores.set_index("fips_tract")["sdrs_score"]
        return fips_tracts.map(mapping)

    def quintile_map(self) -> pd.DataFrame:
        """
        Assign SDRS quintiles (Q1=lowest risk, Q5=highest risk).
        Q4–Q5 tracts represent the highest-disadvantage, highest-weathering areas.
        """
        if self._tract_scores is None:
            raise RuntimeError("Call .build() before .quintile_map()")
        df = self._tract_scores.copy()
        df["sdrs_quintile"] = pd.qcut(df["sdrs_score"], q=5, labels=[1, 2, 3, 4, 5])
        return df
