# WeatheringNet 🧬

> A computational framework for quantifying transgenerational autoimmune disease risk from maternal stress accumulation, with a focus on racial health equity.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.placeholder.svg)](https://doi.org/)

---

## Overview

WeatheringNet operationalizes the **weathering hypothesis** (Geronimus, 1992) as a computational pipeline — translating theoretical frameworks on how structural racism, cumulative maternal stress, and epigenetic in-utero programming contribute to racial disparities in autoimmune disease (AID) incidence into a reproducible, open-source research tool.

The framework is grounded in the biological causal chain:

```
Structural Racism / SES Disadvantage
        ↓
Chronic Stress Accumulation (Weathering)
        ↓
HPA Axis Dysregulation + Elevated Glucocorticoids
        ↓
Epigenetic Modifications In Utero
   ├── TLR Dysregulation
   └── T-cell Phenotype Shifts (↓ CD4+/CD8+ ratio)
        ↓
Offspring Autoimmune Disease Predisposition
```

This framework was developed as a computational extension of:

> Foster, G. (2023). *Maternal Stress and In-Utero Autoimmune Disease Programming: Implications for Racial Health Inequities*. Master's Essay, Johns Hopkins Bloomberg School of Public Health.

---

## Modules

| Module | Description | Key Data Sources |
|--------|-------------|-----------------|
| [`ali/`](weatheringnet/ali/) | Allostatic Load Index computation from clinical biomarkers | NHANES 2010–2020 |
| [`sdrs/`](weatheringnet/sdrs/) | Sociodemographic Risk Score from geospatial SDOH data | ADI, SVI, EJScreen, USDA |
| [`causal/`](weatheringnet/causal/) | DAG specification, identification, and mediation analysis | Synthesized cohort |
| [`model/`](weatheringnet/model/) | Transgenerational AID risk prediction (XGBoost + SHAP) | OMOP CDM / All of Us |
| [`dashboard/`](weatheringnet/dashboard/) | Full-stack equity visualization dashboard | All modules |

---

## Quickstart

```bash
# Clone
git clone https://github.com/yourusername/weatheringnet.git
cd weatheringnet

# Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Download NHANES data
python scripts/download_nhanes.py --cycles 2010-2020

# Run ALI pipeline
python -m weatheringnet.ali.pipeline --config configs/ali_config.yaml

# Launch dashboard (requires Docker)
docker-compose up
```

---

## Repository Structure

```
weatheringnet/
├── weatheringnet/          # Core Python package
│   ├── ali/                # Module 1: Allostatic Load Index
│   ├── sdrs/               # Module 2: Sociodemographic Risk Score
│   ├── causal/             # Module 3: DAG + Mediation Analysis
│   ├── model/              # Module 4: Predictive Risk Model
│   └── dashboard/          # Module 5: Full-stack Dashboard
│       ├── backend/        # FastAPI
│       └── frontend/       # React + Tailwind
├── data/
│   ├── raw/                # Downloaded source data (gitignored)
│   ├── processed/          # Cleaned, merged datasets
│   └── external/           # Reference files (ICD codes, AID ontology)
├── notebooks/              # Exploratory analysis
├── scripts/                # Data download + utility scripts
├── tests/                  # Unit + integration tests
├── configs/                # YAML config files per module
├── docs/                   # Extended documentation
└── .github/workflows/      # CI/CD
```

---

## Data Sources

All data sources used in this project are publicly available:

| Dataset | Description | Access |
|---------|-------------|--------|
| [NHANES](https://www.cdc.gov/nchs/nhanes/) | National Health and Nutrition Examination Survey | Public |
| [ADI](https://www.neighborhoodatlas.medicine.wisc.edu/) | Area Deprivation Index | Free registration |
| [CDC SVI](https://www.atsdr.cdc.gov/placeandhealth/svi/) | Social Vulnerability Index | Public |
| [EPA EJScreen](https://www.epa.gov/ejscreen) | Environmental Justice Screening | Public |
| [USDA FARA](https://www.ers.usda.gov/data-products/food-access-research-atlas/) | Food Access Research Atlas | Public |
| [All of Us](https://allofus.nih.gov/) | NIH longitudinal cohort with SDOH + EHR | Registered researcher |
| [Roberts & Erdei 2020](https://doi.org/10.1016/j.autrev.2019.102423) | AID rate ratios by race/sex | Published paper |

---

## Ethical Considerations

This project works with race-stratified health data. We follow the principles outlined in:
- [Obermeyer et al. (2019)](https://doi.org/10.1126/science.aax2342) on algorithmic bias in healthcare
- [Vyas et al. (2020)](https://doi.org/10.1056/NEJMms2004740) on race as a variable in clinical algorithms
- NIH policies on the inclusion of women and minorities in research

Race is treated as a **social construct and structural variable** — a proxy for exposure to racism and systemic disadvantage — not a biological determinant.

---

## Citation

```bibtex
@software{foster_weatheringnet_2024,
  author  = {Foster, Gabrielle},
  title   = {WeatheringNet: A Computational Framework for Transgenerational Autoimmune Disease Risk},
  year    = {2024},
  url     = {https://github.com/yourusername/weatheringnet},
  version = {0.1.0}
}
```

---

## License

MIT License — see [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md)
