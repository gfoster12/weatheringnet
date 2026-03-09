"""
ALI Pipeline: End-to-end NHANES ingestion → ALI computation → stratified output.

Steps:
    1. Load NHANES cycles (2010–2020)
    2. Merge demographic + biomarker + BP files
    3. Apply survey weights
    4. Handle missing data
    5. Compute ALI via ALICalculator
    6. Stratify by race/sex/age
    7. Export results + summary stats
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml
from loguru import logger

from weatheringnet.ali.biomarkers import PRIMARY_ALI_BIOMARKERS
from weatheringnet.ali.calculator import ALICalculator, ScoringMethod

# NHANES racial classification codes (RIDRETH3)
RACE_MAP = {
    1: "Mexican_American",
    2: "Other_Hispanic",
    3: "Non_Hispanic_White",
    4: "Non_Hispanic_Black",
    6: "Non_Hispanic_Asian",
    7: "Other_Multiracial",
}

SEX_MAP = {1: "Male", 2: "Female"}

# NHANES cycles available for this pipeline
NHANES_CYCLES = [
    "2009-2010",
    "2011-2012",
    "2013-2014",
    "2015-2016",
    "2017-2018",
    "2019-2020",
]


def load_nhanes_cycle(data_dir: Path, cycle: str) -> pd.DataFrame:
    """
    Load and merge NHANES files for a single cycle.

    Merges:
        - DEMO_*.XPT  : demographics (age, sex, race, income, weights)
        - BPX_*.XPT   : blood pressure
        - BMX_*.XPT   : body measures (BMI)
        - GHB_*.XPT   : HbA1c
        - GLU_*.XPT   : fasting glucose
        - TCHOL_*.XPT : total cholesterol
        - CBC_*.XPT   : complete blood count (WBC)
        - CRP_*.XPT   : C-reactive protein
        - HSQ_*.XPT   : cortisol (not all cycles)
    """
    cycle_dir = data_dir / cycle
    if not cycle_dir.exists():
        logger.warning(
            f"Cycle directory not found: {cycle_dir}. Run download_nhanes.py first."
        )
        return pd.DataFrame()

    xpt_files = list(cycle_dir.glob("*.XPT")) + list(cycle_dir.glob("*.xpt"))
    if not xpt_files:
        logger.warning(f"No XPT files in {cycle_dir}")
        return pd.DataFrame()

    dfs = {}
    for f in xpt_files:
        try:
            dfs[f.stem.upper()] = pd.read_sas(f, format="xport", encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read {f.name}: {e}")

    # Merge on SEQN (participant ID)
    combined = None
    for name, df in dfs.items():
        if "SEQN" not in df.columns:
            continue
        df = df.set_index("SEQN")
        combined = (
            df
            if combined is None
            else combined.join(df, how="outer", rsuffix=f"_{name}")
        )

    if combined is None:
        return pd.DataFrame()

    combined["nhanes_cycle"] = cycle
    return combined.reset_index()


def preprocess_nhanes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and recode NHANES variables for ALI computation.
    """
    out = df.copy()

    # Recode race and sex
    if "RIDRETH3" in out.columns:
        out["race_ethnicity"] = out["RIDRETH3"].map(RACE_MAP)
    if "RIAGENDR" in out.columns:
        out["sex"] = out["RIAGENDR"].map(SEX_MAP)
    if "RIDAGEYR" in out.columns:
        out["age"] = out["RIDAGEYR"]

    # Pregnancy exclusion (pregnant individuals may have different biomarker ranges;
    # note: this is a separate analysis stratum, not a pure exclusion in weathering research)
    if "RIDEXPRG" in out.columns:
        out["pregnant"] = out["RIDEXPRG"] == 1

    # Survey weight for population-level estimates
    if "WTMEC2YR" in out.columns:
        out["survey_weight"] = out["WTMEC2YR"]

    # Compute NLR if WBC differential available
    if "LBXNENO" in out.columns and "LBXLYMNO" in out.columns:
        out["nlr"] = out["LBXNENO"] / out["LBXLYMNO"].replace(0, float("nan"))

    return out


def compute_stratified_ali(
    df: pd.DataFrame,
    method: ScoringMethod = "count",
    stratify_by: list[str] = ["race_ethnicity", "sex"],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute ALI scores and return individual + stratified summary results.

    Returns
    -------
    individual : pd.DataFrame
        Row-level ALI scores with demographic covariates.
    summary : pd.DataFrame
        Mean ALI by stratification group (for equity analysis).
    """
    calc = ALICalculator(biomarkers=PRIMARY_ALI_BIOMARKERS, method=method)
    individual = calc.fit_transform(df)

    valid_strata = [s for s in stratify_by if s in individual.columns]
    if valid_strata:
        summary = (
            individual.groupby(valid_strata)["ali_score"]
            .agg(["mean", "std", "median", "count"])
            .rename(
                columns={
                    "mean": "ali_mean",
                    "std": "ali_sd",
                    "median": "ali_median",
                    "count": "n",
                }
            )
            .reset_index()
        )
    else:
        summary = pd.DataFrame()

    return individual, summary


def run_ali_pipeline(config_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Main pipeline entry point. Reads config YAML and runs full ALI computation.

    Parameters
    ----------
    config_path : path to configs/ali_config.yaml

    Returns
    -------
    dict with keys: 'individual', 'summary', 'contributions'
    """
    config = yaml.safe_load(Path(config_path).read_text())
    data_dir = Path(config["data"]["raw_dir"])
    output_dir = Path(config["data"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    cycles = config.get("cycles", NHANES_CYCLES)
    method = config.get("scoring_method", "count")

    logger.info(f"Running ALI pipeline | cycles={cycles} | method={method}")

    all_cycles = []
    for cycle in cycles:
        logger.info(f"Loading NHANES cycle: {cycle}")
        raw = load_nhanes_cycle(data_dir, cycle)
        if raw.empty:
            continue
        processed = preprocess_nhanes(raw)
        all_cycles.append(processed)

    if not all_cycles:
        raise RuntimeError(
            "No NHANES data loaded. Run scripts/download_nhanes.py first."
        )

    combined = pd.concat(all_cycles, ignore_index=True)
    logger.info(
        f"Combined dataset: {len(combined):,} participants across {len(all_cycles)} cycles"
    )

    individual, summary = compute_stratified_ali(
        combined, method=method  # type: ignore[arg-type]
    )

    # Save outputs
    individual.to_parquet(output_dir / "ali_individual.parquet", index=False)
    summary.to_csv(output_dir / "ali_summary_by_group.csv", index=False)
    logger.info(f"ALI results saved to {output_dir}")

    return {"individual": individual, "summary": summary}
