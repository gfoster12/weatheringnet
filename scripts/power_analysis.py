"""
WeatheringNet — DECISION-025 Power Analysis
============================================
Formal power analysis supporting the n=10,000 (development) / n=50,000 (paper)
two-tier synthetic cohort size decision.

Run:   python scripts/power_analysis.py
Requires: numpy, scipy

Reference: Schoenfeld DA. Biometrics. 1983;39(2):499-503.
"""

import numpy as np
from scipy.stats import chi2, norm

ALPHA = 0.05
TARGET_POWER = 0.80


def power_two_proportions(p1, p2, n1, n2, alpha=ALPHA):
    p_bar = (n1 * p1 + n2 * p2) / (n1 + n2)
    se_null = np.sqrt(p_bar * (1 - p_bar) * (1 / n1 + 1 / n2))
    se_alt = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z_crit = norm.ppf(1 - alpha)
    z_alt = abs(p1 - p2) / se_alt - z_crit * (se_null / se_alt)
    return norm.cdf(z_alt)


def power_cox_hr(hr, event_prob, n_exposed, n_unexposed, alpha=ALPHA):
    """Schoenfeld (1983) Cox proportional hazards power formula."""
    total_n = n_exposed + n_unexposed
    p_exp = n_exposed / total_n
    d = total_n * event_prob  # expected events
    ncp = np.sqrt(d * p_exp * (1 - p_exp)) * abs(np.log(hr))
    z_crit = norm.ppf(1 - alpha / 2)
    return norm.cdf(ncp - z_crit) + norm.cdf(-ncp - z_crit)


def power_correlation(r, n, alpha=ALPHA):
    """Fisher z-transform power for H0: rho=0."""
    z_r = np.arctanh(r)
    se = 1 / np.sqrt(n - 3)
    z_crit = norm.ppf(1 - alpha / 2)
    return norm.cdf(abs(z_r) / se - z_crit)


def run_power_analysis(n_total):
    strata_fracs = {
        "NHB_women": 0.068,
        "NHB_men": 0.059,
        "NHW_women": 0.356,
        "NHW_men": 0.342,
        "Hispanic_women": 0.085,
        "Hispanic_men": 0.090,
    }
    n = {k: int(v * n_total) for k, v in strata_fracs.items()}

    results = {}

    # A: ALI race disparity — smallest stratum: NHB women 25-34 vs NHW women 25-34
    n_nhb = n["NHB_women"] // 4
    n_nhw = n["NHW_women"] // 4
    results["A_ALI_disparity"] = power_two_proportions(0.16, 0.08, n_nhb, n_nhw)

    # B: SLE rate ratio AA vs NHW
    sle_prev = 0.00074
    n_aa = n["NHB_women"] + n["NHB_men"]
    n_nw = n["NHW_women"] + n["NHW_men"]
    results["B_SLE_rate_ratio"] = power_two_proportions(
        sle_prev * 2.15, sle_prev, n_aa, n_nw
    )

    # C: Discrimination → inflammation β=0.114
    results["C_discrim_inflammation"] = power_correlation(r=0.114, n=n_total)

    # D: SES susceptibility gate OR=21.073
    p_base = 0.471
    or_ses = 21.073
    p_high = (or_ses * p_base) / (1 - p_base + or_ses * p_base)
    results["D_SES_gate"] = power_two_proportions(
        p_high, p_base, n_total // 2, n_total // 2
    )

    # E: Transgenerational AID HR=1.31, 15% exposure, 2.1% event rate
    n_exp_E = int(0.15 * n_total)
    results["E_transgenerational_AID"] = power_cox_hr(
        hr=1.31, event_prob=0.021, n_exposed=n_exp_E, n_unexposed=n_total - n_exp_E
    )

    # F: DQ2/8 T1D subgroup HR=2.17, 5% DQ2/8, 25% stressed, 4% event rate
    n_dq28 = int(0.05 * n_total)
    n_str = int(0.25 * n_dq28)
    results["F_DQ28_T1D"] = power_cox_hr(
        hr=2.17, event_prob=0.04, n_exposed=n_str, n_unexposed=n_dq28 - n_str
    )

    # G: ZIP calibration GOF chi-square
    target = np.array([0.529, 0.307, 0.084, 0.084])
    alt = np.array([0.579, 0.287, 0.064, 0.074])
    ncp = n_total * np.sum((alt - target) ** 2 / target)
    chi2_crit = chi2.ppf(1 - ALPHA, df=3)
    results["G_ZIP_calibration"] = 1 - chi2.cdf(chi2_crit - ncp, df=3)

    return results


if __name__ == "__main__":
    print(f"{'Analysis':<35} {'n=10k':>8} {'n=50k':>8} {'80% at':>10}")
    print("-" * 65)
    r10 = run_power_analysis(10_000)
    r50 = run_power_analysis(50_000)
    labels = {
        "A_ALI_disparity": "ALI race disparity (OR=2.3)",
        "B_SLE_rate_ratio": "SLE rate ratio (RR=2.15)",
        "C_discrim_inflammation": "Discrimination→inflammation (β=0.114)",
        "D_SES_gate": "SES susceptibility gate (OR=21)",
        "E_transgenerational_AID": "Transgenerational AID (HR=1.31)",
        "F_DQ28_T1D": "DQ2/8 T1D subgroup (HR=2.17)",
        "G_ZIP_calibration": "ZIP calibration GOF (5pp)",
    }
    adequate_n = {
        "A": "10k",
        "B": "84k*",
        "C": "10k",
        "D": "10k",
        "E": "50k",
        "F": "50k",
        "G": "10k",
    }
    for i, (key, label) in enumerate(labels.items()):
        letter = chr(65 + i)
        pw10 = r10[key]
        pw50 = r50[key]
        flag10 = "✓" if pw10 >= TARGET_POWER else " "
        flag50 = "✓" if pw50 >= TARGET_POWER else " "
        print(
            f"  {letter}. {label:<33} {flag10}{pw10:.3f}  {flag50}{pw50:.3f}  {adequate_n[letter]:>8}"
        )
    print()
    print("* B (SLE): requires n≈84k. Resolved by composite AID outcome.")
