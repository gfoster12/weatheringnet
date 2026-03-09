"""
SDRS — Sociodemographic Risk Score module.

Combines Area Deprivation Index (ADI), CDC Social Vulnerability Index (SVI),
EPA EJScreen, and USDA Food Access Research Atlas (FARA) into a composite
census-tract-level risk score that operationalizes the sociodemographic
factors cited in Foster (2023).

Classes:
    SDRSScorer  — Builds and queries the composite SDRS at tract level.

Functions:
    load_adi        — Load Area Deprivation Index data.
    load_svi        — Load CDC Social Vulnerability Index data.
    load_ejscreen   — Load EPA EJScreen Environmental Justice data.
    load_fara       — Load USDA Food Access Research Atlas data.

Constants:
    DEFAULT_WEIGHTS — Component weights for the SDRS composite score.
    DataSource      — Enum of available SDOH data sources.
"""

from weatheringnet.sdrs.scorer import DEFAULT_WEIGHTS, SDRSScorer
from weatheringnet.sdrs.sources import (
    DataSource,
    load_adi,
    load_ejscreen,
    load_fara,
    load_svi,
)

__all__ = [
    "SDRSScorer",
    "DEFAULT_WEIGHTS",
    "DataSource",
    "load_adi",
    "load_svi",
    "load_ejscreen",
    "load_fara",
]
