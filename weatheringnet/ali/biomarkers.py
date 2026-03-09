"""
Biomarker definitions and clinical risk thresholds for Allostatic Load Index.

Each biomarker is mapped to:
    - NHANES variable code
    - Clinical risk threshold (high/low as appropriate)
    - Direction of risk (high or low value = risk)
    - Biological mechanism linking to stress/AID pathway

All thresholds sourced from referenced clinical guidelines.
"""

from dataclasses import dataclass
from enum import Enum


class RiskDirection(str, Enum):
    HIGH = "high"  # high value = elevated risk
    LOW = "low"  # low value = elevated risk


@dataclass
class BiomarkerConfig:
    name: str
    nhanes_code: str  # NHANES variable name
    risk_direction: RiskDirection
    risk_threshold: float  # Clinical cutpoint for count method
    unit: str
    mechanism: str  # Biological pathway from paper
    reference: str  # Clinical guideline source
    z_score_ref_mean: float | None = None
    z_score_ref_sd: float | None = None
    notes: str | None = None


# ── Neuroendocrine / HPA Axis ─────────────────────────────────────────────────

CORTISOL = BiomarkerConfig(
    name="serum_cortisol",
    nhanes_code="LBXCOT",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=20.0,  # μg/dL, elevated morning cortisol
    unit="μg/dL",
    mechanism="Primary HPA axis output; chronic elevation → epigenetic "
    "modifications in fetal glucocorticoid receptor genes (NR3C1). "
    "Directly cited in Facchi et al. and Hederlíngová et al. (paper studies 6, 10).",
    reference="Tsigos & Chrousos (2002) J Psychosom Res",
)

DHEAS = BiomarkerConfig(
    name="dheas",
    nhanes_code="LBXDHEAS",
    risk_direction=RiskDirection.LOW,
    risk_threshold=100.0,  # μg/dL; low DHEA-S = adrenal stress marker
    unit="μg/dL",
    mechanism="Adrenal hormone that promotes sex hormone levels and enhances "
    "immune function. Paper explicitly cites lower DHEA-S in PTSD/"
    "high-stress individuals (Background section).",
    reference="Maninger et al. (2009) Front Neuroendocrinol",
)

# ── Inflammatory Markers ──────────────────────────────────────────────────────

CRP = BiomarkerConfig(
    name="crp",
    nhanes_code="LBXCRP",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=3.0,  # mg/L; high-sensitivity CRP cutpoint
    unit="mg/L",
    mechanism="Acute-phase protein reflecting chronic low-grade inflammation. "
    "Paper cites Black children having >200% higher odds of "
    "inflammation vs. non-Black (Discussion, Infection/Inflammation). "
    "Key output of stress → TLR pathway → cytokine activation.",
    reference="Ridker (2003) Circulation; AHA/CDC Scientific Statement",
    z_score_ref_mean=1.5,
    z_score_ref_sd=2.1,
)

WBC = BiomarkerConfig(
    name="wbc",
    nhanes_code="LBXWBCSI",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=10.0,  # 10^3/μL
    unit="10³/μL",
    mechanism="Elevated WBC reflects immune system activation. Paper notes "
    "higher T-cell lymphocytes (including WBC subsets) circulating "
    "in high-stress/PTSD individuals (Background, Stress section).",
    reference="Bain et al. (2017) Dacie & Lewis Practical Haematology",
)

NLR = BiomarkerConfig(
    name="nlr",  # Computed: neutrophils / lymphocytes
    nhanes_code="COMPUTED",  # Derived from LBXNENO / LBXLYMNO
    risk_direction=RiskDirection.HIGH,
    risk_threshold=3.0,
    unit="ratio",
    mechanism="Neutrophil-to-Lymphocyte Ratio: systemic inflammatory marker. "
    "Elevated in chronic stress and predicts immune dysregulation "
    "consistent with T-cell phenotype shifts described in Liu et al. "
    "(paper study 5, CD4+/CD8+ ratio).",
    reference="Zahorec (2021) Bratisl Lek Listy",
)

# ── Metabolic / Cardiovascular ────────────────────────────────────────────────

SYSTOLIC_BP = BiomarkerConfig(
    name="systolic_bp",
    nhanes_code="BPXSY1",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=130.0,  # mmHg; ACC/AHA Stage 1 hypertension
    unit="mmHg",
    mechanism="HPA dysregulation downstream marker. Black population carries "
    "44% of hypertension burden globally. Paper cites chronic stress "
    "and HTN exposure early in life as malprogramming fetus for "
    "immune dysregulation (Facchi et al., study 10).",
    reference="Whelton et al. (2018) Hypertension ACC/AHA Guideline",
)

DIASTOLIC_BP = BiomarkerConfig(
    name="diastolic_bp",
    nhanes_code="BPXDI1",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=80.0,
    unit="mmHg",
    mechanism="See systolic_bp. Diastolic component of hypertension burden.",
    reference="Whelton et al. (2018) Hypertension ACC/AHA Guideline",
)

BMI = BiomarkerConfig(
    name="bmi",
    nhanes_code="BMXBMI",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=30.0,
    unit="kg/m²",
    mechanism="Metabolic stress proxy. Glucocorticoid excess drives visceral "
    "adiposity; chronic stress and metabolic dysfunction are "
    "co-occurring in weathering populations.",
    reference="WHO Obesity Classification",
)

HBA1C = BiomarkerConfig(
    name="hba1c",
    nhanes_code="LBXGH",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=5.7,  # % pre-diabetes cutpoint
    unit="%",
    mechanism="Metabolic stress / insulin resistance marker. Connected to T1D "
    "autoimmune risk — directly relevant given paper cites HLA-DQ2/8 "
    "cohort T1D risk (Lundgren et al., study 4).",
    reference="ADA Standards of Medical Care in Diabetes 2023",
)

GLUCOSE = BiomarkerConfig(
    name="fasting_glucose",
    nhanes_code="LBXGLU",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=100.0,  # mg/dL; IFG cutpoint
    unit="mg/dL",
    mechanism="Metabolic dysregulation; cortisol elevates blood glucose via "
    "gluconeogenesis — a direct HPA axis → metabolic link.",
    reference="ADA Standards of Medical Care in Diabetes 2023",
)

TOTAL_CHOLESTEROL = BiomarkerConfig(
    name="total_cholesterol",
    nhanes_code="LBXTC",
    risk_direction=RiskDirection.HIGH,
    risk_threshold=200.0,
    unit="mg/dL",
    mechanism="Cardiovascular/metabolic risk. Dyslipidemia co-occurs with "
    "chronic stress and inflammatory states.",
    reference="ATP III / ACC/AHA 2019 Cholesterol Guidelines",
)

# ── Immune Function ───────────────────────────────────────────────────────────

IGM = BiomarkerConfig(
    name="igm",
    nhanes_code="LBXIGG",  # NHANES IgG/IgM panel
    risk_direction=RiskDirection.HIGH,
    risk_threshold=300.0,  # mg/dL; elevated IgM
    unit="mg/dL",
    mechanism="Paper explicitly cites higher IgM in high-stress/PTSD — "
    "antibody produced by responses to foreign pathogen, elevated "
    "in immune hyperreactivity (Background, Stress section).",
    reference="Stojanovich & Marisavljevich (2008) Autoimmun Rev",
    notes="Not all NHANES cycles include IgM; use when available",
)

# ── Biomarker Registry ────────────────────────────────────────────────────────

BIOMARKER_REGISTRY: dict[str, BiomarkerConfig] = {
    "cortisol": CORTISOL,
    "dheas": DHEAS,
    "crp": CRP,
    "wbc": WBC,
    "nlr": NLR,
    "systolic_bp": SYSTOLIC_BP,
    "diastolic_bp": DIASTOLIC_BP,
    "bmi": BMI,
    "hba1c": HBA1C,
    "glucose": GLUCOSE,
    "total_cholesterol": TOTAL_CHOLESTEROL,
    "igm": IGM,
}

# Subset used for the primary ALI score (all with reliable NHANES coverage)
PRIMARY_ALI_BIOMARKERS = [
    "crp",
    "systolic_bp",
    "diastolic_bp",
    "bmi",
    "hba1c",
    "glucose",
    "total_cholesterol",
    "wbc",
]

# Extended ALI includes stress-specific neuroendocrine markers
EXTENDED_ALI_BIOMARKERS = PRIMARY_ALI_BIOMARKERS + ["cortisol", "dheas", "nlr", "igm"]
