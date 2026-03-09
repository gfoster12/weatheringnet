# WeatheringNet — Methodological Decisions Log

**Location in repo:** `docs/DECISIONS.md`  
**Purpose:** Permanent record of every parameter choice, threshold selection, modeling
assumption, and operationalization decision made during WeatheringNet development.
Every entry must cite a source or explicitly mark a design choice as such.
Entries are numbered and immutable once merged to `main`; amendments add new entries
that reference the original.

**Maintainer:** Gabrielle Foster <https://orcid.org/0000-0003-2620-1065>  
**Schema version:** 0.2.0  
**Last updated:** 2026-03-09

---

## How to Read This File

Each entry follows the format:

```
### DECISION-NNN: [Short title]
- **Date:** YYYY-MM-DD
- **Status:** ACCEPTED | PROVISIONAL | UNDER REVIEW
- **Module(s):** [ALI / SDRS / DAG / Model / Dashboard / Synthetic / Cross-cutting]
- **Parameter(s) affected:** [yaml path(s) in synthetic_params.yaml or config files]
- **Decision:** [What was decided]
- **Rationale:** [Why — evidence cited]
- **Alternatives considered:** [What else was on the table]
- **Citation(s):** [Full reference(s)]
- **Review trigger:** [What new evidence would prompt revisiting this]
```

Provisional entries require a corresponding GitHub Issue before merging to `main`.

---

## Synthetic Data Strategy

### DECISION-001: Synthetic parameterization approach (no raw NHANES microdata)
- **Date:** 2025 (Phase 0 design session)
- **Status:** ACCEPTED
- **Module(s):** Cross-cutting
- **Parameter(s) affected:** `simulation.*`
- **Decision:** WeatheringNet uses a simulation study approach: synthetic cohorts
  are generated from distributions parameterized by published literature summary
  statistics, not raw NHANES microdata. The full pipeline runs without any
  restricted-access data files.
- **Rationale:** (1) Enables fully self-contained `make reproduce-paper` with zero
  data-access agreements required from reviewers or users. (2) Avoids NHANES
  licensing and DUA complexities during initial development and JOSS submission.
  (3) Precedent established in Foster (2023) master's essay. (4) Simulation studies
  parameterized from published summary statistics are a recognized methodological
  approach in epidemiology (e.g., microsimulation models in CISNET, CRCPDC).
- **Alternatives considered:** (a) Apply for NHANES Research Data Center access
  (rejected — 6–12 month delay incompatible with publication timeline). (b) Use
  public-use NHANES files directly (rejected — adds DVC complexity and prevents
  clean `make reproduce-paper` without user setup). (c) All of Us data (deferred
  to NHANES validation phase; richer demographic granularity but requires
  controlled-tier access).
- **Citation(s):** Foster G (2023), Johns Hopkins Bloomberg School of Public Health
  Master's Essay.
- **Review trigger:** All of Us data access approved; NHANES validation phase begins.

---

### DECISION-002: Random seed for reproducibility
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** Synthetic
- **Parameter(s) affected:** `simulation.random_seed`
- **Decision:** Fixed seed = 42 for all synthetic data generation.
- **Rationale:** Arbitrary but conventional; enables exact reproduction of all
  results in `make reproduce-paper`.
- **Alternatives considered:** None; seed choice is a design decision with no
  scientific consequences.
- **Citation(s):** N/A (design choice)
- **Review trigger:** Never (locked once paper is submitted).

---

### DECISION-003: Biomarker distribution family
- **Date:** 2026-03-09
- **Status:** PROVISIONAL
- **Module(s):** ALI, Synthetic
- **Parameter(s) affected:** `simulation.biomarker_distribution`
- **Decision:** Biomarker values are drawn from log-normal distributions parameterized
  to match the mean and high-risk prevalence values reported in Geronimus et al. (2006)
  Table 1, with parameters solved per stratum.
- **Rationale:** Biomarkers such as CRP, triglycerides, homocysteine, and creatinine
  clearance are empirically right-skewed in population data. Log-normal is the standard
  approximation used in NHANES-based simulation studies. The enforce_threshold_prevalence
  flag scales draws so that simulated % with high ALI score matches Table 1 values exactly.
- **Alternatives considered:** (a) Normal distributions (rejected — known to produce
  negative values for strictly positive biomarkers). (b) Empirical distributions from
  NHANES public-use files (deferred to validation phase). (c) Beta distributions for
  bounded biomarkers (considered for HbA1c and albumin; log-normal acceptable given
  observed ranges).
- **Citation(s):** Geronimus AT et al. Am J Public Health. 2006;96(5):826–833.
- **Review trigger:** Simulation diagnostics show poor fit between generated biomarker
  distributions and published summary statistics; revisit distribution family or add
  copula for correlated biomarkers.

---

### DECISION-004: Age strata population fractions
- **Date:** 2026-03-09
- **Status:** PROVISIONAL
- **Module(s):** Synthetic
- **Parameter(s) affected:** `population.race_sex_strata.*.approx_population_fraction`
- **Decision:** Race/sex stratum proportions are approximated from U.S. Census 2000
  adult population distribution, not from NHANES IV analytic weights.
- **Rationale:** Geronimus et al. (2006) uses NHANES IV (1999–2002) with complex
  analytic weights but does not report the weighted marginal proportions as a table.
  Census 2000 provides the closest public reference for the target population.
- **Alternatives considered:** Estimating proportions from NHANES IV public-use
  demographic files (deferred to validation phase as this requires microdata access).
- **Citation(s):** U.S. Census Bureau, Census 2000 Summary File 1, Table PCT12.
- **Review trigger:** NHANES validation phase; replace with weighted marginal estimates
  from NHANES 1999–2002 or 2013–2014 public-use files.

---

## Module 1 — Allostatic Load Index (ALI)

### DECISION-005: ALI biomarker algorithm selection
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI
- **Parameter(s) affected:** `allostatic_load.biomarker_algorithm`,
  `allostatic_load.biomarker_thresholds.*`
- **Decision:** Implement the Geronimus et al. (2006) 10-biomarker algorithm using
  NHANES IV high-risk thresholds. The 10 biomarkers are: systolic BP, diastolic BP,
  BMI, HbA1c, serum albumin, creatinine clearance, triglycerides, CRP, homocysteine,
  and total cholesterol.
- **Rationale:** Geronimus et al. (2006) is the canonical empirical paper operationalizing
  the weathering hypothesis using allostatic load. The 10-biomarker NHANES IV algorithm
  is the most widely replicated specification in the weathering literature. Using the
  same algorithm ensures WeatheringNet's synthetic results are directly comparable
  to the foundational empirical work the framework is designed to extend.
- **Alternatives considered:** (a) McEwen & Stellar (1993) original 10-marker algorithm
  (rejected — predates NHANES IV and uses different biomarker panel). (b) Seeman et al.
  (2010) 26-biomarker expanded algorithm (rejected — over-specifies for synthetic
  parameterization; many biomarkers lack race/sex-stratified published summary
  statistics). (c) Custom biomarker panel including cortisol, DHEA-S, IgM (retained
  as Module 1 extensions; these are additive to the Geronimus core algorithm, not
  replacements).
- **Citation(s):** Geronimus AT, Hicken M, Keene D, Bound J. "Weathering" and age
  patterns of allostatic load scores among Blacks and Whites in the United States.
  Am J Public Health. 2006;96(5):826–833. doi:10.2105/AJPH.2004.060749
- **Review trigger:** Publication of a new canonical weathering-specific ALI algorithm
  with NHANES 2017–2020 thresholds; or if NHANES validation phase shows systematic
  bias in the Geronimus thresholds for the target population.

---

### DECISION-006: ALI high-risk cutoff (score ≥ 4)
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI
- **Parameter(s) affected:** `allostatic_load.high_ali_cutoff`
- **Decision:** High allostatic load is defined as a score of ≥ 4 out of 10
  biomarkers in the high-risk range.
- **Rationale:** This threshold is explicitly used in Geronimus et al. (2006) Table 1
  ("% with high score") and is the most-cited operationalization of high allostatic
  load in the weathering literature. It balances specificity (not too many false
  positives at ≥1) and sensitivity (not too restrictive at ≥6+).
- **Alternatives considered:** ≥3 (more inclusive; inflates prevalence) or ≥5
  (more restrictive; appropriate for severe AL burden studies). Both are acceptable
  sensitivity analyses and should be reported as such in the paper.
- **Citation(s):** Geronimus AT et al. Am J Public Health. 2006;96(5):826–833.
- **Review trigger:** Sensitivity analysis shows results are substantially different
  under ≥3 or ≥5 thresholds; add robustness section to paper.

---

### DECISION-007: ALI biomarker high-risk thresholds (10 cut-points)
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI
- **Parameter(s) affected:** `allostatic_load.biomarker_thresholds.*`
- **Decision:** Use the exact high-risk cut-points from Geronimus et al. (2006)
  Table 1 footnote, derived from the worst quartile of the NHANES IV reference
  population. Values:
  - SBP > 127 mmHg
  - DBP > 80 mmHg
  - BMI > 30.9 kg/m²
  - HbA1c > 5.4%
  - Albumin < 4.2 g/dL
  - Creatinine clearance < 66 mg/dL
  - Triglycerides > 168 mg/dL
  - CRP > 0.41 mg/dL (≈ 4.1 mg/L)
  - Homocysteine > 9 µmol/L
  - Total cholesterol > 225 mg/dL
- **Rationale:** These are the published thresholds from the weathering paper that
  WeatheringNet is designed to operationalize. Using identical thresholds preserves
  comparability with Geronimus and all subsequent weathering literature that cites
  this algorithm.
- **Alternatives considered:** Using clinical reference ranges (e.g., AHA/ACC
  cardiovascular risk thresholds) rather than population-quartile cut-points.
  Rejected because population-quartile approach is the defining methodological
  feature of the Geronimus allostatic load algorithm and clinical thresholds would
  not reproduce published weathering findings.
- **Citation(s):** Geronimus AT et al. Am J Public Health. 2006;96(5):826–833.
  Table 1 footnote.
- **Review trigger:** Paper uses updated NHANES cycle for threshold derivation;
  update thresholds to match and bump schema version.

---

### DECISION-008: CRP unit convention (mg/dL vs mg/L)
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI
- **Parameter(s) affected:** `allostatic_load.biomarker_thresholds.crp.unit`,
  `crp.unit`
- **Decision:** The ALI calculator uses Geronimus (2006) CRP threshold of 0.41 mg/dL,
  which is equivalent to 4.1 mg/L. The CRP section (Section 3) reports Khera (2005)
  values in mg/L per Dallas Heart Study convention. Code must convert at runtime;
  the preferred internal unit is mg/L. The YAML documents both.
- **Rationale:** Geronimus (2006) reports CRP in mg/dL (older convention); Khera (2005)
  and current clinical literature uses mg/L. 1 mg/dL = 10 mg/L. This unit mismatch
  is a known source of errors in allostatic load implementation.
- **Alternatives considered:** N/A — this is a mandatory unit reconciliation, not
  a design choice.
- **Citation(s):** Geronimus AT et al. (2006); Khera A et al. JACC. 2005;46(3):464–469.
- **Review trigger:** Any time CRP values appear implausible in simulation diagnostics;
  check unit conversion first.

---

### DECISION-009: ALI score distributions (mean scores and % high score by stratum)
- **Date:** 2026-03-09
- **Status:** PROVISIONAL
- **Module(s):** ALI, Synthetic
- **Parameter(s) affected:** `allostatic_load.score_distributions.*`
- **Decision:** Mean ALI scores and % with high score (≥4) by race/sex/age group
  are read from Geronimus et al. (2006) Table 1. Values for specific strata
  (e.g., Black women ages 25–34: mean 1.8, 16% high score) are used as
  targets for the synthetic data generation process.
- **Rationale:** Table 1 of Geronimus (2006) is the primary empirical calibration
  target for Module 1. Synthetic distributions are scaled until simulated strata
  match these targets within an acceptable tolerance (see `simulation.enforce_threshold_prevalence`).
- **Alternatives considered:** Using raw NHANES IV microdata to derive empirical
  distributions (deferred to validation phase).
- **Citation(s):** Geronimus AT et al. Am J Public Health. 2006;96(5):826–833.
  Table 1.
- **Review trigger:** Simulation calibration error exceeds 5 percentage points vs
  Table 1 targets; investigate distribution family or correlation structure.

---

### DECISION-010: Weathering race odds ratios for ALI (Black vs White by age/sex)
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI, DAG
- **Parameter(s) affected:** `allostatic_load.race_odds_ratios.*`
- **Decision:** Use the Black/White odds ratios for high ALI score from Geronimus
  et al. (2006) Table 2, age-adjusted within sex. Black women ages 25–34: OR 2.3;
  ages 35–44: OR 2.2; ages 45–54: OR 2.0; ages 55–64: OR 1.9. Black men ages
  25–34 through 55–64: ORs 1.5, 1.5, 1.4, 1.4.
- **Rationale:** These ORs are the direct empirical evidence for the weathering
  pattern — that Black-White disparities in allostatic load are largest in young
  adulthood and narrow (but persist) with age. This age-varying OR structure is
  the central finding that motivates the weathering hypothesis and must be
  reproduced in synthetic data validation.
- **Alternatives considered:** Using a single pooled age-adjusted OR (simpler but
  loses the age-varying pattern that is the core of the weathering hypothesis).
- **Citation(s):** Geronimus AT et al. Am J Public Health. 2006;96(5):826–833.
  Table 2.
- **Review trigger:** New weathering literature with larger NHANES samples updates
  these ORs substantially (>15% change in any stratum).

---

## Module 1 — C-Reactive Protein (CRP) Extension

### DECISION-011: CRP race/sex distribution parameters
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI
- **Parameter(s) affected:** `crp.*`
- **Decision:** Use Khera et al. (2005) Dallas Heart Study values for CRP
  distributions by race/sex. Median CRP: White men 1.7, Black men 2.1, White
  women 3.3, Black women 3.5 mg/L. Percent with CRP > 3 mg/L (AHA high-risk):
  White men 30.9%, Black men 39.7%, White women 51.2%, Black women 57.5%.
- **Rationale:** Khera (2005) is the most-cited source for race/sex-stratified
  CRP distributions in a U.S. adult population sample (n=2,749 Dallas Heart Study,
  ages 30–65). Fully adjusted ORs are available, enabling calibration of synthetic
  CRP distributions that account for BMI, smoking, and other confounders.
- **Alternatives considered:** NHANES III CRP values from Flegal or other NCHS sources
  (not used — less granular race/sex stratification for these specific subgroups).
- **Citation(s):** Khera A, McGuire DK, Murphy SA, et al. Race and gender differences
  in C-reactive protein levels. J Am Coll Cardiol. 2005;46(3):464–469.
  doi:10.1016/j.jacc.2005.04.051
- **Review trigger:** NHANES validation phase provides updated CRP distributions
  from a nationally representative sample.

---

### DECISION-012: CRP high-risk threshold (3 mg/L)
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI
- **Parameter(s) affected:** `crp.clinical_high_risk_threshold`
- **Decision:** CRP ≥ 3 mg/L is used as the clinical high-risk threshold for
  reporting purposes (separate from the ALI threshold of 0.41 mg/dL = 4.1 mg/L).
- **Rationale:** 3 mg/L is the American Heart Association / Centers for Disease
  Control consensus threshold for elevated cardiovascular risk (Pearson et al.,
  2003). This threshold is also used in Khera (2005) Table 4, enabling direct
  comparison of simulated prevalence with published values.
- **Alternatives considered:** None — this is a standard clinical threshold.
- **Citation(s):** Pearson TA et al. Markers of inflammation and cardiovascular
  disease. Circulation. 2003;107(3):499–511; Khera A et al. JACC. 2005.
- **Review trigger:** AHA/ACC guideline update changes the recommended CRP
  clinical threshold.

---

## Module 2 — Sociodemographic Risk Score (SDRS)

### DECISION-013: BMI distributions by race/sex
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI, SDRS, Synthetic
- **Parameter(s) affected:** `bmi.*`
- **Decision:** Use Flegal et al. (2016) NHANES 2013–2014 obesity prevalence values
  for obesity (BMI ≥ 30) and Class 3 obesity (BMI ≥ 40) by race/sex. Non-Hispanic
  Black women: 56.9% obese (95% CI 51.1–62.6), 16.8% Class 3. Non-Hispanic White
  women: 38.2% (95% CI 34.5–42.0), 8.9% Class 3. Non-Hispanic Black men: 37.4%,
  7.0% Class 3. Non-Hispanic White men: 34.7%, 5.0% Class 3. Hispanic women:
  45.7%, 7.7% Class 3. Hispanic men: 43.0%, 5.5% Class 3.
- **Rationale:** Flegal et al. (2016) JAMA is the most comprehensive national
  surveillance paper for BMI distributions by race/sex using NHANES 2013–2014.
  Age-adjusted estimates with confidence intervals are available for all major
  race/sex subgroups, enabling probabilistic synthetic BMI generation. The NHANES
  2013–2014 cycle is proximate to the Roberts (2020) AID rates data (2010–2016),
  supporting temporal alignment.
- **Alternatives considered:** Ogden et al. (2017) NHANES 2015–2016 (slightly more
  recent but less disaggregated by race/sex in published tables); Hales et al. (2020)
  NHANES 2017–2018 (more recent but post-dates the primary AID outcome data).
- **Citation(s):** Flegal KM, Kruszon-Moran D, Carroll MD, Fryar CD, Ogden CL.
  Trends in obesity among adults in the United States, 2005 to 2014. JAMA.
  2016;315(21):2284–2291. doi:10.1001/jama.2016.6458
- **Review trigger:** NHANES validation phase; replace with cycle-matched BMI
  distributions.

---

### DECISION-014: Midlife Black women BMI (FACHS supplement)
- **Date:** 2026-03-09
- **Status:** PROVISIONAL
- **Module(s):** ALI, Synthetic
- **Parameter(s) affected:** `bmi.midlife_NHB_women_fachs`
- **Decision:** Supplement Flegal (2016) BMI prevalence data with a mean BMI of
  34.7 kg/m² (SD 8.8) for midlife African American women from Simons et al. (2021)
  FACHS cohort (mean age 48.8).
- **Rationale:** Simons (2021) provides a mean BMI directly for the FACHS demographic
  (midlife Black women), which is a key simulation stratum. This supplements the
  prevalence-based Flegal (2016) data with a continuous mean/SD for log-normal
  parameterization within this stratum.
- **Alternatives considered:** Using only Flegal (2016) (acceptable for prevalence
  estimates but lacks SD for continuous generation).
- **Citation(s):** Simons RL et al. J Racial Ethn Health Disparities. 2021;8(2):339–349.
  doi:10.1007/s40615-020-00786-8; Flegal KM et al. JAMA. 2016.
- **Review trigger:** Inconsistency detected between FACHS-derived mean and Flegal
  prevalence-based estimates for this stratum in simulation diagnostics.

---

## Module 3 — Causal DAG

### DECISION-015: Racial discrimination → inflammation path coefficient
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** DAG
- **Parameter(s) affected:** `racial_discrimination.discrimination_to_inflammation.beta`,
  `simulation.dag_path_weights.racial_discrimination_to_inflammation`
- **Decision:** Use β = 0.114 (p < 0.05) as the standardized path coefficient
  from persistent racial discrimination to the 7-cytokine inflammatory index,
  derived from Simons et al. (2021) 8-year longitudinal analysis of FACHS.
- **Rationale:** Simons (2021) provides the strongest available longitudinal
  (not cross-sectional) estimate of the discrimination → inflammation pathway
  in a community-based sample of Black women — the primary WeatheringNet
  demographic. The 8-year persistent exposure measure (not a single-timepoint
  discrimination measure) aligns with the cumulative stress framework central to
  the weathering hypothesis.
- **Alternatives considered:** Cross-sectional estimates of discrimination →
  inflammation are available from other studies but are subject to reverse
  causation. The longitudinal design of Simons (2021) is preferred.
- **Citation(s):** Simons RL, Lei MK, Klopack E, Beach SR, Gibbons FX, Philibert RA.
  Racial discrimination, inflammation, and chronic illness among African American
  women at midlife: support for the weathering perspective. J Racial Ethn Health
  Disparities. 2021;8(2):339–349. doi:10.1007/s40615-020-00786-8
- **Review trigger:** New longitudinal studies provide updated β estimates for this
  pathway in a nationally representative sample.

---

### DECISION-016: Inflammation → chronic disease IRR
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** DAG
- **Parameter(s) affected:** `racial_discrimination.inflammation_to_chronic_disease.irr`,
  `simulation.dag_path_weights.inflammation_to_chronic_disease_irr`
- **Decision:** Use IRR = 1.251 (p < 0.01) for inflammation → number of chronic
  diseases, from Simons et al. (2021) Poisson regression.
- **Rationale:** Consistent with the DAG edge from inflammation to chronic disease
  count. IRR > 1 operationalizes the multiplicative relationship between
  inflammatory burden and disease count in a count outcome model, which is
  methodologically appropriate for a Poisson/negative binomial outcome.
- **Alternatives considered:** Using ORs from logistic regression for binary chronic
  disease presence (available but less nuanced than count IRR).
- **Citation(s):** Simons RL et al. J Racial Ethn Health Disparities. 2021;8(2):339–349.
- **Review trigger:** Sensitivity analysis with binary outcome shows substantially
  different conclusions.

---

### DECISION-017: SES → chronic disease OR — resolved interpretation after full paper review
- **Date (original):** 2026-03-09
- **Date (amended):** 2026-03-09
- **Status:** ACCEPTED — supersedes PROVISIONAL flag
- **Module(s):** DAG
- **Parameter(s) affected:** `racial_discrimination.ses_to_chronic_disease.or`,
  `simulation.dag_path_weights` (SES path)

#### What the SES variable actually is
SES in Simons (2021) is a 2-item standardized composite. Education is measured on a
6-point ordinal scale (0 = less than high school → 5 = postbaccalaureate); household
income is a continuous variable (past-year, all sources, all family members). Both scales
were independently z-scored and then averaged to produce a single composite SES measure.
This is a standard, defensible operationalization — not a problematic 10-item index.
The "unit" is therefore 1 SD of this standardized composite.

#### Why OR = 21.073 is not what it appeared to be
The OR = 21.073 is NOT from a standard logistic regression of SES on chronic disease
presence. Simons (2021) used a **zero-inflated Poisson (ZIP) model** (MPlus 8.0) because
the chronic disease count outcome had 53% structural zeros. A ZIP model has two
simultaneous components:
1. **Binary (inflation) component:** models membership in the "structural zero" class —
   subjects who are constitutionally not at risk for the outcome at all, irrespective of
   exposures. The OR from this component represents the odds of being in the *at-risk
   population* (vs. the structural zero class) per unit increase in the predictor.
2. **Count component:** models the number of chronic diseases among those who ARE at risk,
   yielding IRRs.

The OR = 21.073 comes from the **binary (inflation) component**. It is not an estimate of
"having ≥1 chronic disease vs. zero" in the conventional sense. It means: per 1 SD increase
in the SES composite, the odds that a FACHS respondent is in the *susceptible/at-risk
population* (rather than the structural zero class) are 21x higher. In plain terms: SES is
an extremely strong determinant of whether a midlife Black woman in this sample is in the
disease-vulnerable category at all.

#### Why the magnitude is actually plausible in this context
Four factors make OR = 21 interpretable rather than aberrant:
1. **ZIP binary interpretation**: this is disease *susceptibility*, not disease *burden*.
   The ZIP inflation OR has a fundamentally different meaning from a standard logistic OR
   and cannot be compared to ORs from conventional regression without this context.
2. **Restricted SES range in FACHS**: the sample is low-income (mean household income
   $30k–$35k/year) with 17.8% below 12th grade education. SES variation is compressed
   near the low end of the national distribution. Within a narrow low-SES range, even
   small absolute SES differences can produce steep risk gradients if there is a threshold
   effect — analogous to how a small temperature change near the freezing point has
   outsized physical consequences.
3. **Standardized composite SES**: the OR is expressed per 1 SD of the composite. In a
   sample with compressed SES range, 1 SD spans a clinically and socially meaningful
   contrast even if numerically modest.
4. **Midlife Black women, 8-year follow-up**: the FACHS sample was recruited in 1997 (Wave
   1) and blood was drawn in 2008 (Wave 5). At mean age 48.5, the cumulative exposure
   window is long enough for SES effects on disease susceptibility to be large.

#### Decision: do NOT use OR = 21.073 as a direct DAG count-model path weight
The OR = 21.073 is epidemiologically interpretable but operationally unusable as a standard
DAG path weight for two reasons:
- It is a ZIP binary component estimate, not a marginal SES → disease OR
- The synthetic data generator uses a continuous DAG / SEM structure, not a ZIP mixture
  model, so applying this OR directly would be category error

#### Decision: use a two-part implementation in the synthetic generator
The correct implementation in WeatheringNet's synthetic cohort generator is:

**Part A — Disease susceptibility gate (binary):**
Use OR = 21.073 per 1 SD SES composite to assign subjects to the "at-risk" vs.
"structural zero" pool at the start of simulation. This is a latent binary variable
determining whether a subject can accumulate chronic diseases. This component is
scientifically legitimate and should be used as documented.

**Part B — Disease count conditional on being at risk (count model): SES path is NULL**
Confirmed from Simons (2021) Results section (p. 11): *"the path from SES to the count
variable (number of illnesses) is not [significant]."* The count-component SES IRR is
explicitly non-significant and is not reported as a coefficient in Figure 1 or the text.

This is not a missing data problem or a placeholder — it is a substantive and reported
null finding. SES does not predict the *number* of chronic diseases once a person is
in the at-risk pool; it only determines whether they enter that pool at all.
The placeholder IRR = 0.88 used in the previous draft of this entry is **withdrawn**.

This null creates a theoretically coherent and DAG-important distinction:
- **SES → susceptibility gate (binary):** OR = 21.073 — whether you're in the
  disease-vulnerable population at all (access to care, material resources, neighborhood
  environment determining baseline vulnerability)
- **Inflammation → disease count (count):** IRR = 1.251 — once vulnerable, cumulative
  inflammatory burden drives how many diseases you develop (biological weathering mechanism)
- **SES → disease count (count):** not significant — SES does not influence disease
  accumulation rate *among those already at risk*; that pathway runs through inflammation

This dissociation should be highlighted in the WeatheringNet paper as supporting the
physiological weathering mechanism: SES sets the threshold for disease entry, but once
that threshold is crossed, it is the inflammatory burden — itself driven by discrimination
exposure — that determines the severity and multiplicity of disease.

#### Confirmed chronic disease count distribution (calibration target)
From Simons (2021) Results: n = 391 FACHS Black women at Wave 5.
- 0 diseases: n = 207 (52.9%) — structural zeros + at-risk zeros combined
- 1 disease:  n = 120 (30.7%)
- 2 diseases: n = 33  (8.4%)
- ≥3 diseases: n = 33  (8.4%) — note: 3+ pooled, exact upper tail unknown
These proportions are a calibration target for the synthetic chronic disease outcome
distribution. The 52.9% zero rate confirms the appropriateness of the ZIP model choice.

#### Updated YAML
The `ses_to_chronic_disease` entry in `synthetic_params.yaml` must reflect:
- Retain `zip_binary_or: 21.073` as the susceptibility gate
- Remove `zip_count_irr` entirely (null finding; no value to assign)
- Add the chronic disease count distribution as a calibration target

- **Alternatives considered:** Discarding OR = 21.073 entirely and substituting a
  population-level SES gradient (rejected — the ZIP binary component is scientifically
  correct for its purpose; discarding it loses information about SES as a disease
  susceptibility threshold).
- **Citation(s):** Simons RL et al. J Racial Ethn Health Disparities. 2021;8(2):339–349.
  doi:10.1007/s40615-020-00786-8; Mullahy J. Much ado about two: reconsidering
  retransformation and the two-part model in health econometrics. J Health Econ.
  1998;17(3):247–281 (ZIP model interpretation reference).
- **Review trigger:** Future meta-analysis or NHANES-based study directly estimates
  SES → chronic disease count conditional on disease presence; compare to null finding.
- **Action required:** None. DECISION-017 is fully resolved. No GitHub Issue needed.

---

### DECISION-018: Prenatal stress → offspring T1D hazard ratio
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** DAG
- **Parameter(s) affected:** `prenatal_stress_T1D.*`,
  `simulation.dag_path_weights.prenatal_stress_to_offspring_T1D_hr`
- **Decision:** Use HR = 2.17 (95% CI 1.1–4.3, p = 0.03) from Lundgren et al.
  (2018) as the primary estimate for the prenatal/early-life severe life events
  → offspring T1D pathway. This is the DQ2/8 high-risk cohort subgroup analysis
  for socioeconomic SLEs (unemployment, divorce, family conflict) occurring
  during or around pregnancy.
- **Rationale:** This HR = 2.17 is the closest confirmable source for the HR ≈ 2.16
  cited in Foster (2023). Lundgren (2018) is a prospective cohort study (DiPiS,
  n = 23,187) with pre-registered outcomes and HLA genotyping, providing one of
  the strongest designs for estimating prenatal stress effects on offspring
  autoimmune disease. The DQ2/8 subgroup is appropriate for WeatheringNet's
  focus on genetically susceptible populations under chronic stress.
- **Alternatives considered:** (a) Total cohort HR = 1.67 (more conservative;
  appropriate for sensitivity analysis). (b) After-pregnancy total cohort
  HR = 2.07 (post-natal stress; less directly relevant to prenatal programming
  hypothesis). (c) DQ2/8 after-pregnancy HR = 4.98 (very large; treated as
  upper-bound sensitivity scenario).
- **Citation(s):** Lundgren M, Ellström K, Elding Larsson H; DiPiS study group.
  Influence of early-life parental severe life events on the risk of type 1
  diabetes in children: the DiPiS study. Acta Diabetol. 2018;55(8):797–804.
  doi:10.1007/s00592-018-1150-y. PMID: 29752553.
- **Review trigger:** Larger prospective cohort or meta-analysis updates the
  prenatal stress → T1D HR estimate.

---

### DECISION-019: Transgenerational autoimmune disease HR (Brew 2022)
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** DAG
- **Parameter(s) affected:** `autoimmune_disease.transgenerational.*`,
  `simulation.dag_path_weights.bereavement_to_offspring_AID_hr`
- **Decision:** Use HR = 1.31 (95% CI 1.06–1.62) for the G2 paternal childhood
  bereavement → G3 offspring autoimmune diseases (onset ≥ 3 years) pathway.
  This is the WeatheringNet causal DAG's primary transgenerational edge.
- **Rationale:** Brew et al. (2022) is a 3-generation Swedish cohort study
  (n = 453,516) — the largest available study directly estimating the
  transgenerational transmission of stress effects to offspring autoimmune disease
  risk. The paternal bereavement → G3 AID association is not mediated by SES or
  mood disorders, pointing toward epigenetic or neuroimmunological transmission
  mechanisms independent of social pathways.
- **Alternatives considered:** Using maternal pathway HR = 1.15 for early-onset
  asthma (more modest effect, partially mediated by SES and mood disorders,
  and outcome is asthma rather than autoimmune disease specifically). The paternal
  HR is used as the primary estimate for AID; the maternal pathway is retained
  as a secondary DAG edge.
- **Citation(s):** Brew BK, Lundholm C, Vieira AR, Almqvist C. Early-life adversity
  due to bereavement and risk of inflammatory diseases in the next generation.
  Am J Epidemiol. 2022;191(1):38–48. doi:10.1093/aje/kwab208.
- **Review trigger:** Replication in a non-Swedish (particularly U.S. or
  racially diverse) cohort; updated meta-analytic estimate.

---

### DECISION-020: AID race rate ratios
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** DAG
- **Parameter(s) affected:** `autoimmune_disease.prevalence.race_rate_ratios.*`
- **Decision:** Use Roberts & Erdei (2020) race-specific AID rate ratios vs.
  Caucasian: African American SLE rate ratio ~2.15x, polymyositis/dermatomyositis
  ~2.0x, RA ~1.0x. Native American RA ~2.4x, alopecia areata ~5.5x, primary
  biliary cirrhosis ~3.0x.
- **Rationale:** Roberts (2020) is a comprehensive 7-year nationwide analysis
  (2010–2016) specifically designed to characterize racial disparities in AID rates
  using a consistent methodology across diseases. The data cover the same temporal
  range as the synthetic cohort target period.
- **Alternatives considered:** Lim et al. (2010) lupus race ratios (older, smaller
  sample); Helmick et al. (2008) arthritis prevalence (does not provide race-stratified
  AID-specific rates). Roberts (2020) is the most comprehensive current source.
- **Citation(s):** Roberts MH, Erdei E. Comparative United States autoimmune disease
  rates for 2010–2016 by sex, geographic region, and race. Autoimmun Rev.
  2020;19(1):102423. doi:10.1016/j.autrev.2019.102423.
- **Review trigger:** Updated CDC/NHIS surveillance data with more granular race
  stratification for AID.

---

## Module 1 — Prenatal Stress / HPA Axis

### DECISION-021: Prenatal cortisol distributions by race (Suglia 2010)
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI
- **Parameter(s) affected:** `cortisol_prenatal.*`
- **Decision:** Use Suglia et al. (2010) ACCESS cohort values for cortisol
  distributions in Black and Hispanic pregnant women (~28 weeks). Black women:
  morning cortisol 14.9 nmol/L (SD 9.1); diurnal slope −1.43 (SD 0.9).
  Hispanic women: 15.9 nmol/L (SD 7.8); slope −1.73 (SD 0.8).
- **Rationale:** Suglia (2010) is the primary empirical source linking cumulative
  stress to cortisol dysregulation specifically in Black and Hispanic pregnant women
  in an urban cohort — the exact population of interest for WeatheringNet's prenatal
  stress module. The ACCESS cohort is urban Boston, consistent with the SDOH
  exposure scenario in the synthetic data.
- **Alternatives considered:** NHANES has salivary cortisol data from 2013 onward
  but does not oversample by gestational status. Suglia (2010) is the best available
  stratified source for pregnant women specifically.
- **Citation(s):** Suglia SF, Staudenmayer J, Cohen S, Enlow MB, Rich-Edwards JW,
  Wright RJ. Cumulative stress and cortisol disruption among Black and Hispanic
  pregnant women in an urban cohort. Psychol Trauma. 2010;2(4):326–334.
  doi:10.1037/a0018953.
- **Review trigger:** Study with larger n and NHANES-representative sampling of
  cortisol in pregnant women by race.

---

### DECISION-022: Stress → cortisol regression — race-specific effect (Suglia 2010)
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** ALI, DAG
- **Parameter(s) affected:** `cortisol_prenatal.stress_cortisol_regression_Black_women.*`
- **Decision:** Implement the stress → cortisol blunting association for Black women
  only (β_T1 = −0.19, β_T2 = −0.20, β_slope = +0.25). No significant association
  is implemented for Hispanic women per Suglia (2010).
- **Rationale:** Suglia (2010) found a significant inverse relationship between
  cumulative stress and morning cortisol among Black women but not Hispanic women.
  This race-differential effect is theoretically important: it may reflect
  differential HPA axis sensitization/habituation under chronic cumulative stress —
  consistent with the weathering hypothesis's prediction of accelerated physiological
  dysregulation in Black women under sustained stress exposure.
- **Alternatives considered:** Applying a uniform stress → cortisol pathway to all
  racial groups (rejected — would obscure the race-differential dysregulation
  that is central to the weathering hypothesis).
- **Citation(s):** Suglia SF et al. Psychol Trauma. 2010;2(4):326–334.
- **Review trigger:** Replication study with larger diverse sample examines whether
  stress → cortisol blunting is specific to Black women or applies more broadly.

---

### DECISION-023: Cumulative stress prevalence for synthetic cohort
- **Date:** 2026-03-09
- **Status:** ACCEPTED
- **Module(s):** Synthetic
- **Parameter(s) affected:** `cortisol_prenatal.cumulative_stress_prevalence.*`
- **Decision:** Black pregnant women: 41% high, 35% medium, 24% low cumulative
  stress. Hispanic pregnant women: 13% high, 30% medium, 57% low.
- **Rationale:** These prevalence values from Suglia (2010) Table 1 are used to
  initialize the stress distribution in the synthetic pregnant subpopulation.
  The large difference between Black (41% high) and Hispanic (13% high) stress
  prevalence reflects structural determinants of chronic stress that WeatheringNet
  aims to capture through the SDRS module.
- **Alternatives considered:** No other study provides equivalent race-stratified
  cumulative stress prevalence in a pregnant cohort.
- **Citation(s):** Suglia SF et al. Psychol Trauma. 2010;2(4):326–334. Table 1.
- **Review trigger:** More recent national data on stress prevalence in pregnant
  women by race (e.g., PRAMS or Listening to Mothers surveys with stress measures).

---

## Cross-Cutting / Design Decisions

### DECISION-024: Simulation DAG path weights — calibration protocol and acceptance criteria
- **Date:** 2026-03-09
- **Status:** PROVISIONAL — closes after first successful `make reproduce-paper` run
- **Module(s):** DAG, Model, Synthetic
- **Parameter(s) affected:** `simulation.dag_path_weights.*`

#### Decision
The path weights in `simulation.dag_path_weights` are initialized from published effect
estimates (HRs, ORs, β coefficients) from source papers. They are treated as calibration
starting points, not fixed parameters. Calibration adjusts these weights iteratively until
simulated marginal distributions match all acceptance criteria below, then locks them for
the paper. Final calibrated values replace the initial values in `synthetic_params.yaml`
and are documented in DECISION-024-REVISION-001.

#### Rationale
Published estimates from observational studies reflect specific populations, time periods,
and confounder adjustment sets that differ from the synthetic cohort design. Applying them
directly as SEM structural weights will produce synthetic marginals that deviate from
calibration targets. Iterative calibration is standard practice in microsimulation and
decision-analytic modeling (Briggs et al., 2012). The goal is internal consistency of the
synthetic data — not exact recovery of the original study samples.

#### Calibration targets and acceptance tolerances
All criteria must be met simultaneously at n=10,000 (development) or n=50,000 (paper):

| Target | Source | Metric | Tolerance |
|--------|--------|--------|-----------|
| % high ALI score by race/sex/age | Geronimus2006 Table 1 | Each cell ±3 pp | Hard |
| Black/White OR for high ALI by sex/age | Geronimus2006 Table 2 | Each OR within ±15% | Hard |
| % CRP > 3 mg/L by race/sex | Khera2005 Table 4 | Each cell ±4 pp | Hard |
| Chronic disease count distribution | Simons2021 Results | χ²(df=3) p > 0.05 | Hard |
| % high cumulative stress by race (pregnant) | Suglia2010 Table 1 | Each cell ±5 pp | Soft |
| Composite AID prevalence by race | Roberts2020 | Race rate ratio ±0.2 | Soft |

Hard criteria must be met before paper submission. Soft criteria are documented if not met,
with explanation in the paper's limitations section.

#### Calibration procedure (to be executed in Phase 0.3)
1. Run `make reproduce-paper` at n=10,000 with initial path weights
2. Extract simulated marginals using `weatheringnet calibration check` CLI target (to build)
3. For each Hard criterion failure: adjust the corresponding DAG path weight by ±10% and
   re-run; repeat until within tolerance or until 20 iterations exhausted
4. If any Hard criterion cannot be met after 20 iterations, flag as CALIBRATION FAILURE,
   open a GitHub Issue, and escalate to distribution family review (see DECISION-003)
5. Document final calibrated weights in DECISION-024-REVISION-001 with a comparison table
   of initial vs. final values and the iteration count required for each

#### Alternatives considered
Using published estimates as fixed parameters without calibration (rejected — risks
producing implausible marginal distributions whose failures would undermine the
simulation study's validity claims).

- **Citation(s):** Briggs AH, Claxton K, Sculpher MJ. Decision Modelling for Health
  Economic Evaluation. Oxford: Oxford University Press; 2012. Chapter 6 (calibration).
- **Action required:** Build `weatheringnet calibration check` CLI target in Phase 0.3.
  Run calibration. Complete DECISION-024-REVISION-001.
- **Review trigger:** After first successful `make reproduce-paper` run. DECISION-024 is
  not closeable until DECISION-024-REVISION-001 exists.

---

### DECISION-025: n_synthetic — two-tier design (development n=10,000 / paper n=50,000)
- **Date:** 2026-03-09
- **Status:** ACCEPTED — supersedes PROVISIONAL flag; power analysis complete
- **Module(s):** Synthetic
- **Parameter(s) affected:** `population.n_synthetic`, `simulation.n_synthetic`

#### Decision
A two-tier n strategy is adopted:
- **Development and iteration runs:** n = 10,000 (fast; adequate for 4 of 7 key analyses)
- **Final paper run:** n = 50,000 (required for 3 analyses that are underpowered at n=10k)

`population.n_synthetic` in `synthetic_params.yaml` stores 10,000 as the default.
The final paper run overrides via CLI: `make reproduce-paper N=50000`.

#### Power analysis results (α = 0.05, target power = 0.80)
Formal power analysis conducted 2026-03-09 using Schoenfeld (1983) for Cox models,
two-proportion z-test for rate ratios, Fisher z-transformation for correlations,
and non-central chi-square for calibration GOF. All methods implemented in Python/SciPy.

| Analysis | Effect size | n=10,000 | n=50,000 | Verdict |
|----------|-------------|----------|----------|---------|
| A. ALI race disparity (NHB vs NHW women 25–34) | OR = 2.3 | **0.912** | >0.99 | ✓ Adequate at 10k |
| B. SLE individual rate ratio (AA vs NHW) | RR = 2.15 | 0.295 | 0.642 | ✗ Underpowered — see below |
| C. Discrimination → inflammation path | β = 0.114 | **1.000** | 1.000 | ✓ Adequate at 10k |
| D. SES susceptibility gate | OR = 21.073 | **1.000** | 1.000 | ✓ Adequate at 10k |
| E. Transgenerational AID (HR = 1.31) | HR = 1.31 | 0.287 | **0.878** | ✓ Adequate at 50k |
| F. DQ2/8 T1D subgroup (HR = 2.17) | HR = 2.17 | 0.323 | **0.918** | ✓ Adequate at 50k |
| G. ZIP calibration (5 pp deviation) | χ²(df=3) | **1.000** | 1.000 | ✓ Adequate at 10k |

#### Analysis B — SLE individual outcome is underpowered at any feasible n
SLE population prevalence is 74/100,000 (0.074%). At n=10,000 only ~7 total SLE cases
are expected; at n=50,000 only ~37. Adequate power for SLE RR=2.15 requires n ≈ 84,000 —
not computationally practical as a synthetic cohort. This is a structural constraint of
rare-disease simulation, not a sample size failure.

**Resolution for Analysis B:** Use a composite autoimmune disease (AID) outcome
aggregating all conditions from Roberts (2020). Composite AID prevalence ≈ 400–800/100,000
depending on conditions included, making it ~5–10× more powered than SLE alone. SLE as an
individual outcome is demoted to a supplementary sensitivity analysis with a power
limitation caveat disclosed in the paper methods.

#### Analysis E — Transgenerational HR = 1.31 is modest and needs events
At n=10,000 and event probability 2.1%, expected AID events = 210 — superficially
adequate. However, with only 15% bereavement exposure prevalence, the exposed group
contributes only ~31 events, leaving the Cox model underpowered for HR=1.31. At n=50,000
(~1,050 total events, ~158 exposed events) power reaches 87.8%.

#### Analysis F — DQ2/8 subgroup requires n=50,000 to provide adequate subgroup size
DQ2/8 high-risk prevalence ≈ 5%. At n=10,000 the DQ2/8 subgroup is n≈500. With T1D
event rate 4% in this group, only 20 events are expected — insufficient for Cox model
power against HR=2.17. Minimum DQ2/8 subgroup n for 80% power = 1,744, requiring total
n ≈ 34,800. At n=50,000 the DQ2/8 subgroup n = 2,500, expected events = 100, power = 91.8%.

#### Stratum sizes at the development and paper runs
At n=10,000: NHB women 680 (~170/age group), NHB men 590 (~147/age group) — adequate
for ALI age-trend analyses even in the smallest stratum.
At n=50,000: All strata have ≥500 per age group; no stratum is sparse.

#### Alternatives considered
- n=1,000: rejected (insufficient ALI stratum sizes, NHB women 25-34 n≈17)
- n=10,000 only: rejected for paper run (fails E and F)
- n=100,000: not required (n=50,000 resolves all issues except SLE individual, which
  is resolved structurally by composite outcome)

- **Citation(s):** Schoenfeld DA. Sample-size formula for the proportional-hazards
  regression model. Biometrics. 1983;39(2):499–503. doi:10.2307/2531021.
  Power analysis code committed to `scripts/power_analysis.py`.
- **Review trigger:** Never — this decision is locked. Override n via CLI only.

---

## References

All full citations are maintained in `docs/references.bib`. The citation keys
used in this document and in `configs/synthetic_params.yaml` resolve to entries there.

| Key | Full Citation |
|-----|--------------|
| Geronimus2006 | Geronimus AT, Hicken M, Keene D, Bound J. Am J Public Health. 2006;96(5):826–833. doi:10.2105/AJPH.2004.060749 |
| Roberts2020 | Roberts MH, Erdei E. Autoimmun Rev. 2020;19(1):102423. doi:10.1016/j.autrev.2019.102423 |
| Khera2005 | Khera A, McGuire DK, Murphy SA, et al. J Am Coll Cardiol. 2005;46(3):464–469. doi:10.1016/j.jacc.2005.04.051 |
| Suglia2010 | Suglia SF et al. Psychol Trauma. 2010;2(4):326–334. doi:10.1037/a0018953 |
| Brew2022 | Brew BK et al. Am J Epidemiol. 2022;191(1):38–48. doi:10.1093/aje/kwab208 |
| Simons2021 | Simons RL et al. J Racial Ethn Health Disparities. 2021;8(2):339–349. doi:10.1007/s40615-020-00786-8 |
| Flegal2016 | Flegal KM et al. JAMA. 2016;315(21):2284–2291. doi:10.1001/jama.2016.6458 |
| Lundgren2018 | Lundgren M et al. Acta Diabetol. 2018;55(8):797–804. doi:10.1007/s00592-018-1150-y |
| Foster2023 | Foster G. Master's Essay. Johns Hopkins Bloomberg School of Public Health. 2023. |

---

*End of DECISIONS.md — v0.2.0. All amendments must add new numbered entries.*
