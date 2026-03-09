"""
Data source loaders for SDRS module.

Each loader downloads or reads a geospatial SDOH dataset and
standardizes it to a census-tract-level DataFrame with FIPS key.
"""

from __future__ import annotations
from enum import Enum
from pathlib import Path

import pandas as pd
from loguru import logger


class DataSource(str, Enum):
    ADI = "adi"
    SVI = "svi"
    EJSCREEN = "ejscreen"
    FARA = "fara"


# ── ADI ───────────────────────────────────────────────────────────────────────

def load_adi(data_dir: Path) -> pd.DataFrame:
    """
    Load Area Deprivation Index.

    ADI ranks neighborhoods by socioeconomic disadvantage on a 1–100 scale
    (100 = most deprived) at the census block group level.
    Download from: https://www.neighborhoodatlas.medicine.wisc.edu/

    Key columns returned:
        fips           : 12-digit FIPS (state+county+tract+blockgroup)
        adi_natrank    : national ADI percentile rank (1–100)
        adi_staternk   : state ADI rank
    """
    adi_file = data_dir / "adi" / "US_2021_ADI_Census_Block_Group_v3.2.csv"
    if not adi_file.exists():
        logger.warning(f"ADI file not found at {adi_file}. Download from neighborhoodatlas.medicine.wisc.edu")
        return pd.DataFrame(columns=["fips", "adi_natrank", "adi_staternk"])

    df = pd.read_csv(adi_file, dtype={"FIPS": str})
    df = df.rename(columns={
        "FIPS": "fips",
        "ADI_NATRANK": "adi_natrank",
        "ADI_STATERNK": "adi_staternk",
    })
    # Aggregate to census tract (first 11 digits of 12-digit FIPS)
    df["fips_tract"] = df["fips"].str[:11]
    return df[["fips", "fips_tract", "adi_natrank", "adi_staternk"]].dropna(subset=["adi_natrank"])


# ── SVI ───────────────────────────────────────────────────────────────────────

def load_svi(data_dir: Path, year: int = 2020) -> pd.DataFrame:
    """
    Load CDC Social Vulnerability Index.

    SVI captures 4 themes at census tract level:
        Theme 1: Socioeconomic Status
        Theme 2: Household Characteristics
        Theme 3: Racial & Ethnic Minority Status
        Theme 4: Housing Type & Transportation

    Download from: https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html

    Key columns returned:
        fips_tract : 11-digit census tract FIPS
        svi_total  : overall SVI percentile (0–1)
        svi_theme1–4 : individual theme percentiles
    """
    svi_file = data_dir / "svi" / f"SVI{year}_US.csv"
    if not svi_file.exists():
        logger.warning(f"SVI file not found at {svi_file}. Download from CDC ATSDR.")
        return pd.DataFrame(columns=["fips_tract", "svi_total"])

    df = pd.read_csv(svi_file, dtype={"FIPS": str})
    col_map = {
        "FIPS": "fips_tract",
        "RPL_THEMES": "svi_total",
        "RPL_THEME1": "svi_theme1_ses",
        "RPL_THEME2": "svi_theme2_household",
        "RPL_THEME3": "svi_theme3_minority",
        "RPL_THEME4": "svi_theme4_housing",
        "E_MINRTY": "n_minority",
        "E_POV150": "n_poverty_150pct",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    df = df.replace(-999, float("nan"))   # SVI uses -999 for missing

    keep = [c for c in col_map.values() if c in df.columns]
    return df[keep]


# ── EJScreen ──────────────────────────────────────────────────────────────────

def load_ejscreen(data_dir: Path) -> pd.DataFrame:
    """
    Load EPA EJScreen Environmental Justice Index.

    Captures pollution burden + demographic vulnerability.
    Critically relevant: paper cites Black women having highest PCB levels
    of any demographic (Background, Sociodemographic section).

    Key columns returned:
        fips_tract       : census tract FIPS
        ej_index         : composite EJ index percentile
        pcb_percentile   : PCB contamination percentile (paper-specific)
        air_toxics_cancer: air toxics cancer risk percentile
        pm25             : PM2.5 concentration
        traffic_prox     : traffic proximity percentile
    """
    ej_file = data_dir / "ejscreen" / "EJSCREEN_2023_Tracts_with_AS_CNMI_GU_VI.csv"
    if not ej_file.exists():
        logger.warning(f"EJScreen file not found at {ej_file}. Download from epa.gov/ejscreen")
        return pd.DataFrame(columns=["fips_tract", "ej_index"])

    df = pd.read_csv(ej_file, dtype={"ID": str}, low_memory=False)
    col_map = {
        "ID": "fips_tract",
        "P_EJ_SNPL": "ej_index",
        "P_PM25": "pm25_percentile",
        "P_CANCER": "air_toxics_cancer",
        "P_TRAF": "traffic_prox",
        "P_LDPNT": "lead_paint_percentile",
        "P_PWDIS": "wastewater_discharge",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    keep = [c for c in col_map.values() if c in df.columns]
    return df[keep]


# ── USDA FARA ─────────────────────────────────────────────────────────────────

def load_fara(data_dir: Path) -> pd.DataFrame:
    """
    Load USDA Food Access Research Atlas (food desert classification).

    Paper directly references food deserts as risk factor for AID:
    "...food deserts, lower access to quality healthcare, and lower rates
    of breastfeeding and lactation support." (Background section)

    Download from: https://www.ers.usda.gov/data-products/food-access-research-atlas/

    Key columns returned:
        fips_tract         : census tract FIPS
        food_desert_flag   : 1 = low income + low access (food desert)
        la_1_10            : low access at 1 mile (urban) or 10 miles (rural)
        pct_laccess_pop    : % population with low food access
    """
    fara_file = data_dir / "fara" / "FoodAccessResearchAtlasData2019.csv"
    if not fara_file.exists():
        logger.warning(f"FARA file not found at {fara_file}. Download from USDA ERS.")
        return pd.DataFrame(columns=["fips_tract", "food_desert_flag"])

    df = pd.read_csv(fara_file, dtype={"CensusTract": str})
    df = df.rename(columns={"CensusTract": "fips_tract"})

    # Food desert = low income AND low access
    if "LILATracts_1And10" in df.columns:
        df["food_desert_flag"] = df["LILATracts_1And10"]

    keep_cols = ["fips_tract", "food_desert_flag", "Urban",
                 "PovertyRate", "MedianFamilyIncome"]
    return df[[c for c in keep_cols if c in df.columns]]
