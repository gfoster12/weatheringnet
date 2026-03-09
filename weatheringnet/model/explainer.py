"""
SHAPExplainer: Mechanistic interpretability layer for AID risk model.

Maps SHAP feature importances back to the biological mechanisms from the paper,
providing a direct bridge between ML predictions and causal biological pathways.

Feature → Mechanism mapping (grounded in paper):
    ali_score              → Weathering hypothesis (allostatic load)
    cortisol               → HPA axis dysregulation (Facchi et al., study 10)
    crp                    → TLR activation / chronic inflammation (Han et al., study 1)
    ptsd_depression_flag   → Psychological stress (Assad et al., study 7)
    infection_pregnancy    → Cross-reactivity / molecular mimicry (Waldorf, study 9)
    hla_dq2_8_flag         → Genetic predisposition (Lundgren et al., study 4)
    sdrs_score             → Structural racism / socioeconomic disadvantage
    sex_offspring          → Sex-specific susceptibility (Assad, study 7; Liu, study 5)
    csection_flag          → Peripartal stress / microbiome disruption (study 6)
    hydralazine_flag       → Race-based prescribing harm (paper Background)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

# Maps feature names to paper mechanisms (for publication-ready plots)
FEATURE_MECHANISM_MAP = {
    "ali_score": "Allostatic Load\n(Weathering)",
    "ali_score_count": "Allostatic Load\n(Count Method)",
    "cortisol": "HPA Axis\n(Glucocorticoids)",
    "dheas": "Adrenal Function\n(DHEA-S)",
    "crp": "Chronic Inflammation\n(CRP)",
    "wbc": "Immune Activation\n(WBC)",
    "nlr": "Immune Dysregulation\n(NLR)",
    "hba1c": "Metabolic Stress\n(HbA1c)",
    "systolic_bp": "HPA Downstream\n(Hypertension)",
    "sdrs_score": "Structural Racism\n(SDRS)",
    "ptsd_depression_flag": "Psychological Stress\n(PTSD/Depression)",
    "infection_pregnancy_icd": "Maternal Infection\n(Cross-Reactivity)",
    "severe_life_events_flag": "Severe Life Events\n(Prenatal Stress)",
    "hla_dq2_8_flag": "Genetic Risk\n(HLA-DQ2/8)",
    "csection_flag": "Peripartal Stress\n(C-Section)",
    "hydralazine_flag": "Race-Based Rx\n(Hydralazine)",
    "sex_offspring": "Sex-Specific\nSusceptibility",
    "race_ethnicity": "Race/Ethnicity\n(Structural Proxy)",
    "food_desert_flag": "Food Access\n(SDOH)",
    "pcb_percentile": "PCB Exposure\n(Environmental Racism)",
}


class SHAPExplainer:
    """
    SHAP-based explainability for the AID risk model.

    Parameters
    ----------
    model : AIDRiskModel
        Trained model instance
    feature_names : list[str]
        Feature column names
    """

    def __init__(self, model, feature_names: list[str]):
        self.model = model
        self.feature_names = feature_names
        self._explainer = None

    def fit(self, X_background: pd.DataFrame) -> SHAPExplainer:
        """Initialize SHAP explainer on background dataset."""
        try:
            import shap

            base_model = self.model._model
            # Unwrap CalibratedClassifier if needed
            if hasattr(base_model, "estimator"):
                base_model = base_model.estimator
            if hasattr(base_model, "calibrated_classifiers_"):
                base_model = base_model.calibrated_classifiers_[0].estimator

            self._explainer = shap.TreeExplainer(base_model)
            logger.info("SHAP TreeExplainer initialized")
        except (ImportError, Exception) as e:
            logger.warning(
                f"TreeExplainer failed ({e}), falling back to KernelExplainer"
            )
            import shap

            self._explainer = shap.KernelExplainer(
                self.model.predict_proba, shap.sample(X_background, 100)
            )
        return self

    def compute_shap_values(self, X: pd.DataFrame) -> np.ndarray:
        """Compute SHAP values for dataset X."""
        if self._explainer is None:
            raise RuntimeError("Call .fit() before .compute_shap_values()")
        shap_vals = self._explainer.shap_values(X)
        # For binary classification, return values for positive class
        if isinstance(shap_vals, list):
            return shap_vals[1]
        return shap_vals

    def global_importance(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Mean absolute SHAP values per feature — global importance.
        Annotated with biological mechanism from paper.
        """
        shap_vals = self.compute_shap_values(X)
        importance = pd.DataFrame(
            {
                "feature": self.feature_names,
                "mean_abs_shap": np.abs(shap_vals).mean(axis=0),
            }
        ).sort_values("mean_abs_shap", ascending=False)

        importance["mechanism"] = importance["feature"].map(FEATURE_MECHANISM_MAP)
        importance["rank"] = range(1, len(importance) + 1)
        return importance

    def pathway_importance(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate SHAP importance by biological pathway from paper.
        Shows relative contribution of each mechanistic pathway to predictions.

        Pathways (from paper's Results section):
            - Allostatic Load (weathering)
            - HPA Axis Dysregulation
            - Inflammatory / TLR Pathway
            - Genetic / Immunological
            - Sociodemographic / Structural
            - Sex-Specific
        """
        pathway_map = {
            "Allostatic Load": ["ali_score", "ali_score_count"],
            "HPA Axis": ["cortisol", "dheas", "hba1c", "systolic_bp", "diastolic_bp"],
            "Inflammatory / TLR": ["crp", "wbc", "nlr", "infection_pregnancy_icd"],
            "Psychological Stress": ["ptsd_depression_flag", "severe_life_events_flag"],
            "Genetic / Immunological": ["hla_dq2_8_flag"],
            "Sociodemographic / Structural": [
                "sdrs_score",
                "race_ethnicity",
                "food_desert_flag",
                "pcb_percentile",
                "hydralazine_flag",
            ],
            "Sex-Specific": ["sex_offspring", "csection_flag"],
        }

        importance = self.global_importance(X).set_index("feature")
        pathway_scores = {}
        for pathway, features in pathway_map.items():
            pathway_features = [f for f in features if f in importance.index]
            if pathway_features:
                pathway_scores[pathway] = importance.loc[
                    pathway_features, "mean_abs_shap"
                ].sum()
            else:
                pathway_scores[pathway] = 0.0

        return (
            pd.DataFrame.from_dict(
                pathway_scores, orient="index", columns=["shap_importance"]
            )
            .sort_values("shap_importance", ascending=False)
            .reset_index()
            .rename(columns={"index": "pathway"})
        )

    def plot_summary(self, X: pd.DataFrame, output_path: str | None = None) -> None:
        """Generate SHAP summary beeswarm plot (publication-ready)."""
        try:
            import matplotlib.pyplot as plt
            import shap

            shap_vals = self.compute_shap_values(X)
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_vals,
                X,
                feature_names=[
                    FEATURE_MECHANISM_MAP.get(f, f) for f in self.feature_names
                ],
                show=False,
            )
            plt.title(
                "Feature Contributions to Transgenerational AID Risk\n"
                "(SHAP Values — WeatheringNet)",
                fontsize=13,
            )
            plt.tight_layout()
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches="tight")
                logger.info(f"SHAP summary plot saved → {output_path}")
            else:
                plt.show()
        except ImportError:
            logger.error("shap and matplotlib required for plotting")

    def race_stratified_shap(
        self,
        X: pd.DataFrame,
        race_col: str = "race_ethnicity",
    ) -> pd.DataFrame:
        """
        Compute mean SHAP values stratified by race — reveals which features
        drive different model behavior across racial groups.
        This is the equity audit of the model.
        """
        shap_vals = self.compute_shap_values(X)
        shap_df = pd.DataFrame(shap_vals, columns=self.feature_names, index=X.index)
        shap_df[race_col] = X[race_col].values
        return shap_df.groupby(race_col)[self.feature_names].mean()
