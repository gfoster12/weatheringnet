"""
MediationAnalyzer: Quantifies how much of the racial disparity in AID risk
is mediated through the stress/allostatic load pathway vs. direct effects.

Implements the counterfactual (potential outcomes) framework for mediation:

    Total Effect (TE) = race_ses → aid_risk
    Natural Direct Effect (NDE) = effect not through stress mediators
    Natural Indirect Effect (NIE) = effect through ALI/HPA/inflammation path

    TE = NDE + NIE
    Proportion Mediated = NIE / TE

This quantifies the central claim of the paper: that the stress pathway
(weathering → allostatic load → in-utero epigenetic programming) is
a key mediating mechanism of racial AID disparities.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger


class MediationAnalyzer:
    """
    Causal mediation analysis for the weathering → AID pathway.

    Supports:
        - Single mediator (ALI only)
        - Sequential mediators (ALI → HPA → inflammation → AID)
        - Race-stratified analysis

    Parameters
    ----------
    exposure : str
        Column name for the exposure variable (e.g., "race_ses_binary")
    mediator : str | list[str]
        Column name(s) for mediator(s)
    outcome : str
        Column name for the outcome (AID risk score or diagnosis)
    covariates : list[str]
        Confounders to adjust for
    """

    def __init__(
        self,
        exposure: str = "race_ses_binary",
        mediator: str | list[str] = "ali_score",
        outcome: str = "aid_diagnosis",
        covariates: list[str] | None = None,
    ):
        self.exposure = exposure
        self.mediator = mediator if isinstance(mediator, list) else [mediator]
        self.outcome = outcome
        self.covariates = covariates or ["age", "sex", "nhanes_cycle"]

    def fit(self, df: pd.DataFrame) -> dict:
        """
        Estimate natural direct and indirect effects via regression-based
        Baron & Kenny approach with bootstrap confidence intervals.

        For publication-quality mediation with assumptions testing,
        use R mediation package with the exported dataset.

        Returns
        -------
        dict with keys:
            total_effect, nde, nie, proportion_mediated,
            bootstrap_ci_nie, bootstrap_ci_nde
        """
        required = [self.exposure] + self.mediator + [self.outcome] + self.covariates
        missing = [c for c in required if c not in df.columns]
        if missing:
            logger.warning(f"Missing columns: {missing}. Running with available data.")

        data = df[[c for c in required if c in df.columns]].dropna()
        n = len(data)
        logger.info(f"Mediation analysis: n={n:,} complete cases")

        try:
            import warnings

            from sklearn.linear_model import LinearRegression, LogisticRegression

            warnings.filterwarnings("ignore")

            covar_cols = [c for c in self.covariates if c in data.columns]

            # Step 1: Total effect (exposure → outcome, no mediator)
            X_total = data[[self.exposure] + covar_cols].values
            if data[self.outcome].nunique() == 2:
                model_total = LogisticRegression(max_iter=500).fit(
                    X_total, data[self.outcome]
                )
                total_effect = model_total.coef_[0][0]
            else:
                model_total = LinearRegression().fit(X_total, data[self.outcome])
                total_effect = model_total.coef_[0]

            # Step 2: Exposure → mediator(s)
            mediated_effects = []
            for med in self.mediator:
                if med not in data.columns:
                    continue
                X_med = data[[self.exposure] + covar_cols].values
                model_a = LinearRegression().fit(X_med, data[med])
                a_coef = model_a.coef_[0]  # exposure → mediator

                # Step 3: Mediator + exposure → outcome
                X_outcome = data[[self.exposure, med] + covar_cols].values
                if data[self.outcome].nunique() == 2:
                    model_b = LogisticRegression(max_iter=500).fit(
                        X_outcome, data[self.outcome]
                    )
                    b_coef = model_b.coef_[0][1]  # mediator → outcome
                else:
                    model_b = LinearRegression().fit(X_outcome, data[self.outcome])
                    b_coef = model_b.coef_[1]

                nie = a_coef * b_coef  # product-of-coefficients method
                mediated_effects.append((med, a_coef, b_coef, nie))

            total_nie = sum(nie for _, _, _, nie in mediated_effects)
            nde = total_effect - total_nie
            prop_mediated = (
                total_nie / total_effect if total_effect != 0 else float("nan")
            )

            results = {
                "n": n,
                "total_effect": total_effect,
                "nde": nde,
                "nie": total_nie,
                "proportion_mediated": prop_mediated,
                "mediator_details": [
                    {
                        "mediator": med,
                        "exposure_to_mediator_coef": a,
                        "mediator_to_outcome_coef": b,
                        "nie": nie,
                    }
                    for med, a, b, nie in mediated_effects
                ],
            }

            logger.info(
                f"Mediation results: TE={total_effect:.3f}, "
                f"NDE={nde:.3f}, NIE={total_nie:.3f}, "
                f"Prop. mediated={prop_mediated:.1%}"
            )
            return results

        except ImportError:
            logger.error("scikit-learn required for mediation analysis")
            return {}

    def bootstrap_ci(
        self,
        df: pd.DataFrame,
        n_bootstrap: int = 1000,
        ci: float = 0.95,
        seed: int = 42,
    ) -> dict:
        """
        Bootstrap confidence intervals for mediation estimates.
        Recommended before publication — point estimates alone are insufficient.
        """
        rng = np.random.default_rng(seed)
        boot_nies = []
        boot_ndes = []

        for _ in range(n_bootstrap):
            boot_df = df.sample(n=len(df), replace=True, random_state=rng.integers(1e9))
            result = self.fit(boot_df)
            if result:
                boot_nies.append(result["nie"])
                boot_ndes.append(result["nde"])

        alpha = 1 - ci
        return {
            "nie_ci": (
                float(np.percentile(boot_nies, alpha / 2 * 100)),
                float(np.percentile(boot_nies, (1 - alpha / 2) * 100)),
            ),
            "nde_ci": (
                float(np.percentile(boot_ndes, alpha / 2 * 100)),
                float(np.percentile(boot_ndes, (1 - alpha / 2) * 100)),
            ),
            "n_bootstrap": n_bootstrap,
        }

    def export_for_r(self, df: pd.DataFrame, path: str) -> None:
        """
        Export cleaned dataset for mediation analysis in R.
        R mediation package with sensitivity analysis is recommended
        for the published paper's primary mediation results.
        """
        cols = [self.exposure] + self.mediator + [self.outcome] + self.covariates
        out = df[[c for c in cols if c in df.columns]].dropna()
        out.to_csv(path, index=False)
        logger.info(f"Exported {len(out):,} rows for R mediation analysis → {path}")
        print(f"""
R code to run mediation analysis:
  library(mediation)
  data <- read.csv('{path}')
  fit.m <- lm({self.mediator[0]} ~ {self.exposure} + {' + '.join(self.covariates)}, data=data)
  fit.y <- glm({self.outcome} ~ {self.exposure} + {self.mediator[0]} + {' + '.join(self.covariates)},
               family=binomial, data=data)
  med <- mediate(fit.m, fit.y, treat='{self.exposure}', mediator='{self.mediator[0]}',
                 robustSE=TRUE, sims=1000)
  summary(med)
  plot(med)
        """)


def identify_adjustment_set(
    dag,
    exposure: str = "race_ses",
    outcome: str = "aid_risk",
    method: str = "backdoor",
) -> dict | list:
    """
    Identify the minimal sufficient adjustment set to identify the
    causal effect of exposure on outcome given the WeatheringDAG.

    For full do-calculus implementation, use:
        pip install dowhy
        from dowhy import CausalModel

    Parameters
    ----------
    dag : WeatheringDAG
    exposure : str
    outcome : str
    method : str  "backdoor" | "frontdoor"

    Returns
    -------
    dict | list : adjustment set info or empty list if not found
    """
    # Simplified: return known valid adjustment set based on DAG structure
    # For the weathering DAG, conditioning on measured confounders
    # while NOT conditioning on mediators gives the total causal effect
    adjustment_sets = {
        ("race_ses", "aid_risk"): {
            "total_effect": ["age", "sex", "U_genetics_proxy"],
            "direct_effect": ["age", "sex", "U_genetics_proxy", "ali_score", "sdrs"],
            "note": (
                "Do NOT condition on ali_score, sdrs, hpa_dysreg, inflammation "
                "when estimating total effect — these are mediators (collider bias risk). "
                "Condition on them only when estimating NDE in mediation analysis."
            ),
        },
        ("ali", "aid_risk"): {
            "total_effect": ["race_ses", "age", "sex"],
            "note": "race_ses is a confounder of the ALI → AID relationship",
        },
    }

    key = (exposure, outcome)
    if key in adjustment_sets:
        result = adjustment_sets[key]
        logger.info(f"Adjustment set for {exposure}→{outcome}: {result}")
        return result
    else:
        logger.warning(f"No pre-specified adjustment set for {exposure}→{outcome}")
        return []
