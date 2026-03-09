# WeatheringNet — Master Build Checklist
## Academically Rigorous, Publication-Ready, Open Source

**Legend**
- 🤖 **Claude Code** — Terminal agent. Full codebase context, runs commands, self-corrects.
- 🖥️ **Cursor** — IDE agent. Real-time inline edits, notebook work, frontend, refactoring.
- 🧠 **YOU** — Scientific judgment. Cannot be delegated. These are the decisions that make the paper credible.
- ✅ **Checkpoint** — Stop and verify before proceeding. Gate between phases.

---

## PRE-WEEKEND PREP
*Complete before Friday night. ~2 hours.*

### Accounts & Identifiers
- [ ] 🧠 Create ORCID iD at orcid.org if you don't have one
  - This permanently links your name across papers, repos, software citations
- [ ] 🧠 Create Zenodo account at zenodo.org, connect to GitHub
  - Enables automatic DOI minting on tagged releases
- [ ] 🧠 Create GitHub repo: `weatheringnet` — public, MIT license, no template
- [ ] 🧠 Sign up for All of Us Researcher Workbench at allofus.nih.gov
  - This takes weeks to approve — start now regardless of weekend timeline
- [ ] 🧠 Register for ADI download at neighborhoodatlas.medicine.wisc.edu
  - Usually approved within 24 hours

### Your Synthetic Data System
- [ ] 🧠 Identify what your existing system outputs (format, fields, parameters)
- [ ] 🧠 Write down every parameter it currently uses — you will replace all of them with published values
- [ ] 🧠 Pull these papers and have them open this weekend:
  - Roberts & Erdei (2020) Autoimmun Rev — AID prevalence by race
  - Geronimus et al. (2006) Am J Public Health — ALI intercorrelations Table 2
  - Suglia et al. (2010) Psychol Trauma — cortisol by race/stress (your paper ref 34)
  - Khera et al. (2005) JAMA — CRP distributions by race/sex
  - Brew et al. (2022) Am J Epidemiol — HR=1.31 transgenerational AID (your paper study 3)
  - Lundgren et al. (2018) Acta Diabetol — HR=2.16 T1D prenatal stress (your paper study 4)
  - Simons et al. (2021) J Racial Ethn Health Disparities — inflammation by race (your paper ref 17)
  - Flegal et al. (2016) JAMA — BMI distributions by race/sex

### Install Tools
- [ ] 🤖 Install Claude Code: `npm install -g @anthropic-ai/claude-code`
- [ ] 🖥️ Install Cursor at cursor.sh — VS Code-based, sign in with GitHub
- [ ] 🧠 Install R + RStudio for mediation analysis (non-negotiable — do not use Python for this)
  - `install.packages(c("mediation", "dagitty", "survey", "tableone"))`

---

## PHASE 0 — FOUNDATIONS
*Friday Night, Hours 0–4*
*Goal: Repo is live, environment works, data is generating.*

### 0.1 Repository Setup
- [ ] 🤖 Push scaffold to GitHub:
  ```
  "Push the weatheringnet scaffold to GitHub. Initialize git,
  create initial commit with all existing files, push to origin main.
  Set up branch protection on main: require PR reviews, require
  status checks to pass. Create develop branch."
  ```
- [ ] 🤖 Configure pre-commit hooks:
  ```
  "Create .pre-commit-config.yaml with: black, ruff, mypy,
  and a custom hook that fails if any .xpt, .parquet, .csv,
  or .sas7bdat files are staged for commit.
  Run pre-commit install and verify it works on a test commit."
  ```
- [ ] 🤖 Create CITATION.cff:
  ```
  "Create CITATION.cff with Gabrielle Foster as author,
  ORCID placeholder, Johns Hopkins Bloomberg School of Public Health,
  MIT license, correct repo URL. Follow CFF v1.2.0 spec exactly."
  ```
- [ ] 🤖 Initialize DVC:
  ```
  "Initialize DVC with a local remote at /tmp/weatheringnet-dvc-remote.
  Add data/raw/, data/processed/, data/external/ to .dvcignore.
  Create dvc.yaml with stages: generate_synthetic, ali, sdrs, model, figures.
  Each stage should have defined deps and outs for reproducibility tracking."
  ```
- [ ] 🤖 Write the Makefile:
  ```
  "Write a Makefile with targets:
  - setup: install deps, pre-commit, dvc
  - synthetic: run synthetic cohort generation
  - ali: run ALI pipeline
  - sdrs: run SDRS pipeline  
  - model: train and evaluate model
  - figures: run paper_figures notebook
  - test: pytest with coverage
  - reproduce-paper: chains synthetic → ali → sdrs → model → figures
  - clean: remove processed data
  Each target should print what it's doing and fail loudly on error."
  ```
- [ ] ✅ **CHECKPOINT**: `git log` shows clean initial commit. `pre-commit run --all-files` passes. `make help` works.

### 0.2 Synthetic Data Parameters
- [ ] 🧠 Open `configs/synthetic_params.yaml` and fill in EVERY value yourself from the papers you pulled
  - Do not delegate this. These numbers are your scientific claims.
  - For each value write the exact citation: author, year, journal, table/figure number
  - Parameters needed:
    - Race/ethnicity distribution (NHANES 2017-2020)
    - Biomarker means and SDs by race/sex for all 8 primary ALI biomarkers
    - Biomarker intercorrelation matrix (Geronimus 2006 Table 2)
    - Weathering effect sizes (race → biomarker differences)
    - AID prevalence by race (Roberts & Erdei 2020)
    - Outcome model coefficients (log HRs from Brew, Lundgren, Waldorf)
    - PTSD/depression prevalence by race (cite source)
    - Infection rate by race (Vahidy 2020 — your paper ref 32)
    - C-section rate by SES (Hederlingova — your paper study 6)
- [ ] 🧠 Write `DECISIONS.md` entry for every parameter choice that wasn't straightforward
  - Example: "Cortisol threshold: Used 20 μg/dL per Tsigos & Chrousos 2002. Alternative considered: 18 μg/dL from Suglia 2010. Chose 20 because it represents clinical elevated morning cortisol and has broader citation support."
- [ ] ✅ **CHECKPOINT**: Every value in synthetic_params.yaml has a citation. No placeholders. `DECISIONS.md` has at least 5 entries.

### 0.3 Synthetic Cohort Generation
- [ ] 🤖 Implement `scripts/generate_synthetic_cohort.py`:
  ```
  "Read configs/synthetic_params.yaml. Implement a synthetic cohort
  generator that:
  1. Generates N=10,000 maternal-offspring pairs
  2. Draws biomarkers from race/sex-stratified distributions
     using the exact means/SDs in the params file
  3. Imposes correlation structure via Cholesky decomposition
     using the Geronimus 2006 intercorrelation matrix
  4. Generates AID outcomes using the logistic outcome model
     with published log-HR coefficients
  5. Runs these validation checks and FAILS with a clear error
     if any fail:
     - Black women mean ALI > White women mean ALI (weathering direction)
     - Overall AID prevalence within 10% of Roberts & Erdei value
     - Black women AID rate > White women AID rate
     - Each biomarker mean within 1 SD of published value for each stratum
  6. Outputs synthetic_cohort.parquet + data_generation_report.md
     listing every validation check result with pass/fail
  All validation logic should be in a separate validate_synthetic_data()
  function that can be called independently."
  ```
- [ ] 🧠 Run the generator. Read `data_generation_report.md` yourself.
  - Are the validation checks passing?
  - Does the AID prevalence look right (7-9%)?
  - Does the Black-White ALI gap look plausible (not too large, not zero)?
  - Does the correlation between stress features and AID outcome look right?
- [ ] 🧠 If any validation check is borderline passing, investigate why — don't just move on
- [ ] ✅ **CHECKPOINT**: All validation checks PASS. data_generation_report.md is saved to git. You have personally reviewed the output distributions and they match your scientific expectations.

---

## PHASE 1 — CORE PIPELINE
*Saturday, Hours 0–5*
*Goal: ALI computes correctly, model trains, SHAP makes biological sense.*

### 1.1 Complete the Python Package
- [ ] 🤖 Implement `weatheringnet/model/features.py`:
  ```
  "Read the full weatheringnet package, especially model/__init__.py
  and the synthetic_params.yaml to understand the feature schema.
  Implement features.py with a FeatureBuilder class that:
  1. Takes the synthetic cohort dataframe as input
  2. Creates all features listed in configs/model_config.yaml
  3. Handles missing values with strategy documented in code comments
  4. Creates interaction terms: race * ali_score, sex * cortisol
     (these capture the sex/race-specific pathway differences from paper)
  5. Applies log transform to CRP and cortisol (right-skewed distributions)
  6. One-hot encodes race_ethnicity
  7. Returns X (features), y (outcome), feature_names list
  8. Has a FEATURE_GROUPS dict mapping each feature to its
     biological mechanism from the paper
  Document every transformation decision with the biological rationale."
  ```
- [ ] 🤖 Implement `weatheringnet/model/evaluation.py`:
  ```
  "Implement ModelEvaluator class with:
  1. Standard metrics: AUROC, AUPRC, sensitivity, specificity, PPV, NPV
     with bootstrap 95% CIs (n=1000)
  2. Calibration assessment: Brier score, calibration curve plot,
     Hosmer-Lemeshow test
  3. FAIRNESS METRICS (these are primary results, not supplements):
     - AUROC stratified by race_ethnicity
     - AUROC stratified by sex_offspring
     - Calibration curves by race_ethnicity
     - Equalized odds: TPR and FPR by race
     - Demographic parity: prediction rate by race
     - Maximum disparity across race groups (single summary stat)
  4. generate_report() method returning a dict suitable for
     the paper's Table 3
  5. plot_all() method generating publication-ready figures
  Fairness metrics must be computed FIRST in the report,
  before overall metrics. This is a design choice that signals
  equity is primary."
  ```
- [ ] 🤖 Complete remaining module stubs:
  ```
  "Check all __init__.py files for any unimplemented imports.
  Create weatheringnet/causal/identification.py implementing
  identify_adjustment_set() as a complete function using
  the WeatheringDAG graph. Run the full test suite and fix failures."
  ```

### 1.2 ALI Pipeline Validation
- [ ] 🤖 Run ALI on synthetic cohort:
  ```
  "Run the ALI pipeline on the synthetic cohort.
  Generate a summary table by race/sex showing:
  mean ALI, SD, median, 95% CI, n.
  Also generate biomarker-level flag rates by race/sex.
  Save as data/processed/ali/ali_summary_by_group.csv"
  ```
- [ ] 🧠 Review the ALI summary table yourself:
  - Non-Hispanic Black Female should have highest mean ALI
  - The magnitude of the Black-White gap: is it consistent with Geronimus 2006?
  - Are individual biomarker flag rates plausible? (e.g., BP flags higher in Black women — matches paper Background)
  - Any biomarker showing unexpected direction? Investigate before proceeding.
- [ ] 🧠 Write DECISIONS.md entry: "ALI Validation — [date]. Observed Black-White ALI gap of [X] points on count method. Comparable to Geronimus 2006 report of [Y]. Proceeding."
- [ ] ✅ **CHECKPOINT**: ALI summary table reviewed and signed off by you. DECISIONS.md updated.

### 1.3 Model Training and SHAP Validation
- [ ] 🤖 Train model and generate SHAP:
  ```
  "Run the full model pipeline on the synthetic cohort:
  1. Build features using FeatureBuilder
  2. Run 5-fold stratified CV and print results
  3. Train final model on full training set
  4. Run ModelEvaluator — print fairness metrics first, then overall
  5. Generate SHAP global importance table
  6. Save: models/aid_risk_model_v1.pkl,
           data/processed/model_results/cv_results.json,
           data/processed/model_results/shap_importance.csv,
           data/processed/model_results/evaluation_report.json"
  ```
- [ ] 🧠 Review SHAP results — this is a critical scientific check:
  - `ali_score` should be in the top 3 features (if not, something is wrong with the feature engineering or outcome model)
  - `crp` or another inflammatory marker should appear prominently (paper mechanism)
  - `race_ethnicity` should not be the single dominant feature (if it is, the model is using race as a shortcut rather than the stress pathway — this needs investigation and discussion in the paper)
  - `hla_dq2_8_flag` should appear for the genetic pathway
  - Do the SHAP directions make biological sense? (higher ALI → higher risk, higher cortisol → higher risk)
- [ ] 🧠 Review fairness metrics:
  - Is AUROC comparable across race groups (within ~0.05)?
  - Are calibration curves similar across race groups?
  - If disparities exist in model performance, write a DECISIONS.md entry explaining the limitation and what it means for v1
- [ ] ✅ **CHECKPOINT**: SHAP results reviewed. Top features biologically sensible. Fairness metrics reviewed. You have written at least 3 DECISIONS.md entries from this section.

---

## PHASE 2 — CAUSAL ANALYSIS
*Saturday, Hours 5–7*
*Goal: DAG is publication-ready. Mediation results are in R.*

### 2.1 DAG Finalization
- [ ] 🖥️ Open `weatheringnet/causal/dag.py` in Cursor. Review every edge:
  - Is every edge in EDGES defensible from the paper?
  - Are there any edges you added to the scaffold that you're not confident in? Remove them.
  - Any edges missing that your paper's Results section implies? Add them.
  - This is a scientific document, not just code.
- [ ] 🖥️ In Cursor, add to `dag.py`:
  ```
  "Add a to_mermaid() method that exports the DAG in Mermaid
  diagram format, with nodes colored by type:
  - exposure: red
  - mediator: blue  
  - outcome: green
  - unmeasured: gray (dashed border)
  - mechanism: purple
  Also add a to_r_dagitty() method that exports valid R dagitty
  code that can be pasted directly into R."
  ```
- [ ] 🧠 Export the DAG to dagitty format and paste into dagitty.net
  - Verify it renders correctly
  - Use dagitty's built-in tools to verify: adjustment sets, testable implications
  - Screenshot this for your paper figures folder
- [ ] 🧠 In R, run:
  ```r
  library(dagitty)
  dag <- dagitty('[paste exported dagitty string]')
  # Verify adjustment sets
  adjustmentSets(dag, exposure="race_ses", outcome="aid_risk")
  adjustmentSets(dag, exposure="ali", outcome="aid_risk")
  # Check testable implications
  impliedConditionalIndependencies(dag)
  ```
  - Are the adjustment sets what you expected?
  - Do the conditional independencies make biological sense?
  - Write DECISIONS.md entry with the identified adjustment set you'll use
- [ ] ✅ **CHECKPOINT**: DAG renders in dagitty.net. Adjustment sets verified in R. At least one DECISIONS.md entry from this section.

### 2.2 Mediation Analysis in R
*This section is entirely YOUR work. Do not delegate the analysis or interpretation.*
- [ ] 🧠 Export data for R:
  ```python
  # In Python
  from weatheringnet.causal.mediation import MediationAnalyzer
  m = MediationAnalyzer(
      exposure="race_black",
      mediator=["ali_score"],
      outcome="aid_diagnosis",
      covariates=["age", "sex_offspring"]
  )
  m.export_for_r(df, "data/processed/mediation_input.csv")
  ```
- [ ] 🧠 Run mediation in R:
  ```r
  library(mediation)
  library(survey)  # for weighted analysis
  
  data <- read.csv("data/processed/mediation_input.csv")
  
  # Step 1: Mediator model (exposure → ALI)
  fit.m <- lm(ali_score ~ race_black + age + sex_offspring, data=data)
  summary(fit.m)  # Check: race_black should be positive and significant
  
  # Step 2: Outcome model (exposure + mediator → AID)
  fit.y <- glm(aid_diagnosis ~ race_black + ali_score + age + sex_offspring,
               family=binomial(link="logit"), data=data)
  summary(fit.y)  # Check: ali_score should be positive and significant
  
  # Step 3: Mediation
  set.seed(42)
  med.out <- mediate(fit.m, fit.y,
                     treat="race_black",
                     mediator="ali_score",
                     robustSE=TRUE,
                     sims=1000)
  summary(med.out)
  
  # Step 4: Sensitivity analysis (Imai et al. 2010 — required for publication)
  sens.out <- medsens(med.out, rho.by=0.1, effect.type="indirect", sims=100)
  summary(sens.out)
  plot(sens.out)  # Save this plot — goes in paper supplement
  ```
- [ ] 🧠 Record these values in `results/mediation_results.json` (create manually):
  - ACME (Average Causal Mediation Effect) with 95% CI
  - ADE (Average Direct Effect) with 95% CI  
  - Total Effect with 95% CI
  - Proportion mediated with 95% CI
  - Sensitivity: ρ value at which ACME crosses zero (robustness indicator)
- [ ] 🧠 Interpret the results:
  - Is the proportion mediated consistent with weathering hypothesis?
  - Is the sensitivity ρ value large enough to claim robustness?
  - What does the residual direct effect tell you about pathways not captured?
  - Write a 2-paragraph interpretation in DECISIONS.md
- [ ] ✅ **CHECKPOINT**: R mediation script runs without errors. All four mediation quantities recorded. Sensitivity analysis complete. Your interpretation is written.

---

## PHASE 3 — BACKEND + SDRS
*Saturday, Hours 7–10*
*Goal: API serves real results. SDRS builds from public data.*

### 3.1 SDRS Pipeline
- [ ] 🤖 Download and build SDRS:
  ```
  "Download SVI 2020 from CDC ATSDR and EJScreen 2023 from EPA.
  Both are direct downloads, no auth required.
  Run the SDRS pipeline using SDRSScorer with these two sources.
  Validate: print the 10 highest-SDRS census tracts — they should be
  in known high-deprivation urban areas (Detroit, Chicago South Side,
  rural Mississippi, etc.).
  Print the 10 lowest — they should be in known affluent suburban areas.
  Save to data/processed/sdrs_tracts.parquet"
  ```
- [ ] 🧠 Review the 10 highest and 10 lowest SDRS tracts yourself
  - Do you recognize them as high/low deprivation areas?
  - If not, investigate the normalization logic
  - This is your face validity check — it belongs in the paper
- [ ] 🧠 Write DECISIONS.md entry: "SDRS Face Validity Check — [date]. Top 10 SDRS tracts include [list]. These align with known high-deprivation areas per [cite]. Proceeding."
- [ ] 🤖 Add ADI to SDRS when registration approves:
  ```
  "When ADI CSV is available at data/external/adi/,
  rerun SDRSScorer with ADI included and verify the
  face validity check still holds. Update DECISIONS.md."
  ```

### 3.2 Backend Wired to Real Data
- [ ] 🤖 Wire backend to real pipeline outputs:
  ```
  "Update dashboard/backend/main.py:
  1. On startup, load data/processed/ali/ali_summary_by_group.csv
     into memory and serve it from /api/ali/summary
  2. Load models/aid_risk_model_v1.pkl and serve predictions
     from /api/model/predict using real model inference
  3. Load data/processed/model_results/shap_importance.csv
     and serve from /api/model/shap/global
  4. Add startup health checks that fail loudly if any
     required file is missing
  5. Add request logging with loguru
  6. Write integration tests for every endpoint that
     verify the response schema and that values are
     in expected ranges (risk score 0-1, etc.)"
  ```
- [ ] 🤖 Write full API test suite:
  ```
  "Write tests/integration/test_api.py using FastAPI TestClient.
  Test every endpoint:
  - /api/health: status 200
  - /api/ali/summary: returns groups with ali_mean > 0
  - /api/ali/disparities: Black-White gap is positive (weathering direction)
  - /api/model/predict: risk score between 0 and 1, disclaimer present
  - /api/causal/dag: returns nodes and edges matching WeatheringDAG
  - /api/equity/aid-rates: all rate ratios > 1 for listed diseases
  The disparity direction test is a scientific assertion, not just
  a schema check."
  ```
- [ ] ✅ **CHECKPOINT**: `pytest tests/integration/` passes. API runs with `uvicorn`. Disparity direction test passes.

---

## PHASE 4 — DASHBOARD FRONTEND
*Sunday, Hours 0–4*
*Use Cursor exclusively for this phase.*

### 4.1 Project Setup
- [ ] 🖥️ In Cursor terminal:
  ```bash
  cd weatheringnet/dashboard/frontend
  npm create vite@latest . -- --template react-ts
  npm install
  npm install @tanstack/react-query axios recharts reactflow
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  ```
- [ ] 🖥️ In Cursor, create `src/api/client.ts`:
  ```
  "Create a typed API client using axios that calls all
  WeatheringNet backend endpoints. Include TypeScript interfaces
  for every response type. Add error handling that surfaces
  API errors clearly in the UI."
  ```

### 4.2 Core Components
Build each component in Cursor using inline chat (Cmd+K or Ctrl+K):

- [ ] 🖥️ `src/components/ALIDisparityChart.tsx`:
  ```
  "Grouped bar chart using Recharts showing mean ALI ± 95% CI
  by race/sex group. Non-Hispanic Black bars highlighted in
  a distinct color. X-axis: race/sex groups. Y-axis: mean ALI score.
  Error bars for CI. Caption: 'Source: NHANES-parameterized synthetic
  cohort. See Methods.' Include a small legend explaining the
  weathering hypothesis in 1 sentence. Mobile responsive."
  ```
- [ ] 🖥️ `src/components/DAGVisualization.tsx`:
  ```
  "Interactive DAG using ReactFlow. Fetch nodes and edges from
  /api/causal/dag. Color nodes by type field:
  exposure=red, mediator=cornflowerblue, outcome=green,
  unmeasured=lightgray with dashed border, mechanism=purple.
  Clicking a node shows a tooltip with its label and mechanism description.
  Include a legend. Layout: hierarchical left-to-right.
  This will appear as Figure 1 in the paper — make it clean."
  ```
- [ ] 🖥️ `src/components/AIDRateRatios.tsx`:
  ```
  "Horizontal bar chart using Recharts showing AID rate ratios
  from /api/equity/aid-rates. Sorted by rate ratio descending.
  Vertical reference line at 1.0 (parity). Bars colored by
  significance. X-axis: rate ratio. Y-axis: disease name.
  95% CI whiskers. Caption cites Roberts & Erdei 2020.
  This is Figure 2 in the paper."
  ```
- [ ] 🖥️ `src/components/RiskCalculator.tsx`:
  ```
  "Risk prediction form calling /api/model/predict.
  Input fields for: ALI score (slider 0-12), SDRS score (slider 0-100),
  toggles for clinical flags (PTSD, infection, HLA, C-section, hydralazine),
  race/sex dropdowns.
  Output: circular risk gauge (0-100%), risk category badge,
  pathway breakdown bar chart (6 pathways from paper).
  Prominent disclaimer box in yellow: research tool only,
  not for clinical use.
  This is a demonstration component — label it clearly as such."
  ```
- [ ] 🖥️ `src/components/SHAPImportance.tsx`:
  ```
  "Horizontal bar chart of global SHAP feature importances
  from /api/model/shap/global. Top 15 features only.
  Features labeled with their biological mechanism (use the
  mechanism field from the API response).
  Color bars by pathway category matching the pathway map
  from the paper. This is Figure 3 in the paper."
  ```
- [ ] 🖥️ `src/App.tsx`:
  ```
  "Tabbed layout with 5 tabs:
  Overview (intro text + AID rate ratios),
  Allostatic Load (ALI disparity chart),
  Causal Model (DAG visualization),
  Prediction Model (SHAP importance),
  Risk Calculator (disclaimer-prominent form).
  Header: WeatheringNet title, version, link to paper, link to GitHub.
  Footer: citation, license, data sources.
  Clean academic aesthetic — white background, minimal color,
  publication-style typography."
  ```
- [ ] ✅ **CHECKPOINT**: `npm run dev` serves the dashboard. All 5 tabs load data from the API. No console errors. You have viewed every chart and verified the data looks correct.

### 4.3 Dashboard Accessibility and Disclaimer Review
- [ ] 🧠 Review the Risk Calculator component personally:
  - Is the disclaimer prominent enough?
  - Could a clinician misuse this?
  - Add any additional warnings your judgment requires
- [ ] 🧠 Review the DAG visualization:
  - Does it communicate the causal story clearly?
  - Would an epidemiologist reading it understand what's claimed and what's assumed?
  - Is it clear which nodes are unmeasured?

---

## PHASE 5 — REPRODUCIBILITY INFRASTRUCTURE
*Sunday, Hours 4–7*

### 5.1 Paper Figures Notebook
- [ ] 🖥️ In Cursor, create `notebooks/paper_figures.ipynb`:
  ```
  "Create a Jupyter notebook with these sections,
  each clearly labeled with the figure number:

  Figure 1: DAG (export from dag.to_mermaid(), render with mermaid-py)
  Figure 2: ALI violin plot by race/sex from ali_individual.parquet
  Figure 3: SHAP summary beeswarm plot from saved model + synthetic data
  Figure 4: Mediation diagram (manual matplotlib — boxes and arrows
            showing TE, NDE, NIE with the actual numbers from R output)
  Figure 5: AID rate ratios (horizontal bar, Roberts & Erdei data)
  Table 1: Study characteristics (from paper — manual entry)
  Table 2: ALI summary by group (from ali_summary_by_group.csv)
  Table 3: Model evaluation + fairness metrics

  Each figure cell:
  - Loads from data/processed/ (no data wrangling in notebook)
  - Sets matplotlib style to 'seaborn-v0_8-whitegrid'
  - Uses figure size (7, 5) for single column, (14, 5) for double
  - Saves to figures/figure_N.pdf AND figures/figure_N.png at 300 DPI
  - Has a markdown cell above it with the figure caption"
  ```
- [ ] 🧠 Fill in Figure 4 mediation numbers yourself from your R output
- [ ] 🧠 Run the notebook end-to-end: `jupyter nbconvert --to notebook --execute notebooks/paper_figures.ipynb`
  - Do all figures render?
  - Would Figure 1-3 be acceptable as journal figures?
  - Are the captions accurate and complete?

### 5.2 Reproduce-Paper Pipeline Test
- [ ] 🤖 Test full reproduction from scratch:
  ```
  "Run 'make reproduce-paper' from a completely clean state:
  - Delete data/processed/ entirely
  - Run make reproduce-paper
  - Verify it completes successfully
  - Verify all figures exist in figures/
  - Verify all processed data files exist
  Fix every error until it runs clean.
  Then run it a second time — it should be idempotent."
  ```
- [ ] 🤖 Docker test:
  ```
  "Build and run the full docker-compose stack.
  Verify:
  - API health check passes at localhost:8000/api/health
  - Frontend loads at localhost:3000
  - All API endpoints return valid data
  - pytest passes inside the container
  Fix any docker-specific issues."
  ```
- [ ] ✅ **CHECKPOINT**: `make reproduce-paper` runs clean twice in a row. Docker stack comes up cleanly. This is the publishability gate.

### 5.3 Environment Locking
- [ ] 🤖 Lock the environment:
  ```
  "Generate requirements.lock using pip-compile from pyproject.toml.
  Generate requirements-dev.lock for dev dependencies.
  Add both to git. Update the README setup instructions to use
  pip install -r requirements.lock for exact reproducibility.
  Also run 'pip-audit requirements.lock' and fix any known
  security vulnerabilities."
  ```

---

## PHASE 6 — DOCUMENTATION
*Sunday, Hours 7–9*

### 6.1 Technical Documentation
- [ ] 🤖 Generate API reference with mkdocs:
  ```
  "Install mkdocs, mkdocstrings[python], mkdocs-material.
  Create mkdocs.yml with navigation covering all 5 modules.
  Create docs/ pages for: Getting Started, ALI Module,
  SDRS Module, Causal Module, Model Module, API Reference,
  Data Sources, Ethical Considerations.
  Run 'mkdocs build' and verify it completes without errors.
  Run 'mkdocs gh-deploy' to publish to GitHub Pages."
  ```
- [ ] 🖥️ In Cursor, write `docs/ARCHITECTURE.md`:
  ```
  "Write ARCHITECTURE.md with:
  1. A Mermaid diagram showing module dependencies and data flow
  2. A section for each module explaining inputs, outputs,
     and where the biological assumptions live in the code
  3. A section on the synthetic data approach explaining
     why it's scientifically valid for this use case
  4. A section on the causal assumptions and their limitations"
  ```

### 6.2 The Model Card
*Write this yourself. Every word matters.*
- [ ] 🧠 Create `docs/MODEL_CARD.md` following Mitchell et al. (2019) format:
  - **Model Details**: what it predicts, algorithm, training data, version
  - **Intended Use**: population-level health equity research only
  - **Out-of-Scope Use**: individual clinical decisions, insurance, hiring — be explicit
  - **Factors**: performance varies by race/sex — describe the evaluated subgroups
  - **Metrics**: report the fairness metrics from evaluation.py results
  - **Training Data**: synthetic cohort description, published parameters cited
  - **Quantitative Analyses**: the stratified performance table
  - **Ethical Considerations**: race as structural variable, limitations of synthetic data, absence of real clinical validation
  - **Caveats and Recommendations**: what a researcher should and should not conclude from this model
- [ ] 🧠 Read the Model Card out loud to yourself
  - Could a non-specialist misuse this tool based on what's written?
  - Would a health equity researcher trust this based on what's written?
  - Revise until both are true.

### 6.3 DECISIONS.md Audit
- [ ] 🧠 Read every DECISIONS.md entry you've written this weekend
  - Is the reasoning clear for each one?
  - Are all citations complete (author, year, journal)?
  - Add any decisions you made but didn't write down
  - This document should tell the story of every methodological choice in the paper
- [ ] 🧠 The minimum acceptable DECISIONS.md has entries for:
  - [ ] Choice of count method as primary ALI score
  - [ ] Every biomarker included/excluded and why
  - [ ] Clinical thresholds for each biomarker
  - [ ] SDRS component weights
  - [ ] Synthetic data outcome model derivation
  - [ ] Mediation analysis interpretation
  - [ ] Model fairness threshold decisions
  - [ ] Any validation check that was borderline

### 6.4 README Final Pass
- [ ] 🧠 Write the README yourself — do not delegate this
  - One paragraph: what problem does this solve and why does it matter
  - Explicit statement: "Race is treated as a structural and social variable, a proxy for exposure to racism and socioeconomic disadvantage, not a biological determinant."
  - Status table (synthetic vs. real data, planned vs. complete)
  - Quickstart that actually works (test it before writing it)
  - Known limitations section — be honest
  - How to contribute
- [ ] 🤖 Have Claude Code verify the README's quickstart:
  ```
  "Follow the README quickstart instructions exactly as written,
  in a fresh directory. Report every step that fails or is unclear."
  ```

---

## PHASE 7 — PRE-RELEASE CHECKS
*Sunday evening*

### 7.1 Test Suite Final Run
- [ ] 🤖 Final test suite:
  ```
  "Run the full test suite with coverage.
  Ensure:
  - Unit test coverage > 70% for ali/, causal/, model/
  - All integration tests pass
  - All scientific validation tests pass
  - No tests are skipped without a documented reason
  Print a coverage report and identify the 3 most important
  uncovered functions to add tests for."
  ```
- [ ] 🤖 Add the 3 missing tests identified above
- [ ] ✅ **CHECKPOINT**: `pytest tests/ --cov` shows >70% coverage. Zero test failures. Zero warnings that aren't documented.

### 7.2 Security and Ethics Audit
- [ ] 🤖 Security scan:
  ```
  "Run bandit on the weatheringnet package and pip-audit on
  requirements.lock. Fix any high-severity findings.
  Document any medium-severity findings in SECURITY.md with
  the rationale for accepting or deferring them."
  ```
- [ ] 🧠 Personal ethics review checklist:
  - [ ] Does any component produce outputs that could harm Black patients if misused?
  - [ ] Is the synthetic data labeled clearly everywhere it appears?
  - [ ] Is it impossible to mistake the Risk Calculator for a validated clinical tool?
  - [ ] Are all data sources properly attributed?
  - [ ] Could any visualization be misread to suggest race is biological?
  - [ ] Is the Model Card honest about limitations?

### 7.3 The Stranger Test
- [ ] 🧠 Find one person — developer or researcher — who has not seen this project
  - Give them only the GitHub URL
  - Ask them to: clone it, run `make reproduce-paper`, and tell you what broke
  - Fix everything they report
  - This is the most important quality check of the weekend

### 7.4 Release
- [ ] 🤖 Final commit and tag:
  ```
  "Create a final commit with message:
  'v1.0.0 — ALI pipeline on synthetic cohort, causal DAG,
  mediation analysis, predictive model with fairness evaluation,
  full-stack dashboard, reproducible pipeline'
  Tag as v1.0.0 and push to GitHub.
  Verify Zenodo auto-triggers and creates a DOI.
  Update CITATION.cff with the Zenodo DOI once issued."
  ```
- [ ] 🧠 Zenodo confirmation:
  - Visit zenodo.org and confirm the v1.0.0 release was archived
  - Copy the DOI and add it to README and CITATION.cff
  - The repo now has a permanent citable identifier

---

## POST-WEEKEND (WEEK 1-2)

### Paper Draft
- [ ] 🖥️ In Cursor, draft `paper/manuscript_draft.md`:
  ```
  "Write a methods paper draft for PLOS Computational Biology.
  Sections: Abstract, Background, Methods, Results, Discussion,
  Conclusion, Data Availability. ~3500 words.
  The methods section should describe every module.
  The results section uses the actual numbers from
  data/processed/model_results/evaluation_report.json
  and results/mediation_results.json.
  Every claim needs a citation. Flag [CITE] where a
  citation is needed that I need to add."
  ```
- [ ] 🧠 Rewrite the abstract yourself
  - The abstract is what gets accepted or rejected at triage
  - It needs your voice and your scientific judgment
  - Structure: background (1 sentence), gap (1 sentence), what you did (2 sentences), key finding (1-2 sentences), implication (1 sentence)

### Real Data Pipeline (Parallel Track)
- [ ] 🧠 Submit All of Us data access request with your project description
- [ ] 🤖 Update `ali/pipeline.py` to handle real NHANES XPT files when ready:
  ```
  "Download one NHANES cycle (2017-2018) and run the ALI pipeline
  on real data. Compare the real results to the synthetic cohort
  results. Document any differences in DECISIONS.md."
  ```
- [ ] 🧠 When real NHANES ALI results are available, update the README status table

### JOSS Submission (When Ready)
- [ ] 🧠 Write `paper/joss_paper.md` — max 1000 words, describes software only
- [ ] 🤖 Verify JOSS submission requirements:
  ```
  "Read https://joss.theoj.org/about and verify the weatheringnet
  repo meets all submission requirements: license, documentation,
  tests, installation instructions, statement of need."
  ```
- [ ] 🧠 Submit to JOSS — review happens in public on GitHub Issues

---

## ONGOING MAINTENANCE CHECKLIST
*For every subsequent contribution*

- [ ] 🧠 Every new biomarker needs: NHANES code, clinical threshold, mechanism docstring, literature citation, unit test
- [ ] 🧠 Every new causal edge needs: evidence citation in the edge tuple, corresponding test in test_dag.py
- [ ] 🧠 Every new feature in the model needs: biological justification, entry in FEATURE_GROUPS dict, SHAP validation that direction is correct
- [ ] 🤖 Before every PR merge: `make test` passes, `make reproduce-paper` passes
- [ ] 🧠 Monthly: review open issues, update DECISIONS.md with any methodological discussions that happened in GitHub issues

---

## PUBLICATION READINESS CHECKLIST
*Do not submit until every box is checked*

### Code Quality
- [ ] `make reproduce-paper` runs clean from scratch
- [ ] Docker-compose up serves working application
- [ ] pytest coverage >70%, zero failures
- [ ] pre-commit passes on all files
- [ ] No hardcoded paths, no API keys in code

### Scientific Rigor
- [ ] Every biomarker threshold has a literature citation in the code
- [ ] Every synthetic data parameter has a citation in synthetic_params.yaml
- [ ] Every causal edge has a citation in dag.py
- [ ] DECISIONS.md has entries for every methodological choice
- [ ] Mediation sensitivity analysis (E-values or ρ) is complete
- [ ] Fairness metrics are primary results, not supplementary
- [ ] Limitations section is honest and specific (not generic)

### Transparency
- [ ] Synthetic vs. real data is clearly labeled everywhere
- [ ] Model Card is complete and honest
- [ ] Zenodo DOI exists
- [ ] CITATION.cff is complete with ORCID
- [ ] Data provenance is documented for every source

### Ethics
- [ ] Race is consistently treated as structural/social, never biological
- [ ] Risk Calculator disclaimer is prominent and unambiguous
- [ ] Model Card explicitly states out-of-scope uses
- [ ] No component could cause direct harm if misused by a non-expert

### Community Readiness
- [ ] GitHub Issues has at least 5 `good-first-issue` tickets
- [ ] CONTRIBUTING.md explains the evidence standard for contributions
- [ ] mkdocs site is live on GitHub Pages
- [ ] README has a working quickstart (tested by someone else)
