"""Task 1 — Retrospective grounding against the 2013–2016 Levant drought.

Shifts the single-crisis drought window from 2030–2032 to 2013–2016, runs
at Optimistic / Moderate / Pessimistic severities WITHOUT γ multipliers
and WITHOUT Monte Carlo, and compares modelled natural-source reduction to
observed reduction in the Israel Water Authority annual balance.

Baseline year for normalisation: 2012 (year immediately preceding the
observed drought onset). Natural-source definition per manuscript
Section 2.1: surface water (Kinneret) + groundwater (wells), excluding
desalination and treated wastewater reuse.

Parameters are NOT re-calibrated — this is a consistency check. The
discrepancy is reported as-is and interpreted per Handover §5.1.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from multicrisis.config import BASELINE_DATA_PATH, DATA_DIR, RESULTS_DIR, param_path
from multicrisis.crises import apply_drought_crisis, load_parameters

OUTPUT_DIR = RESULTS_DIR / "task1"

CRISIS_YEARS = [2013, 2014, 2015, 2016]
BASELINE_YEAR = 2012
SEVERITIES = ("Optimistic", "Moderate", "Pessimistic")


def natural_source(df: pd.DataFrame) -> pd.Series:
    """Surface (Kinneret) + groundwater (wells). Excludes reuse and desalination."""
    return (
        df["capped_groundwater"].fillna(0)
        + df["produced_by_kinneret_milion_m3"].fillna(0)
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_DATA_PATH)
    baseline["year"] = pd.to_numeric(baseline["year"], errors="coerce")
    drought_params = load_parameters(str(param_path("drought")))

    # Restrict to 2010-2018 for the retrospective figure
    window = baseline[(baseline["year"] >= 2010) & (baseline["year"] <= 2018)].copy()
    window = window.sort_values("year").reset_index(drop=True)
    window["natural_source_mcm"] = natural_source(window)

    base_2012_natural = float(
        window.loc[window["year"] == BASELINE_YEAR, "natural_source_mcm"].iloc[0]
    )
    base_2012_total = float(
        window.loc[window["year"] == BASELINE_YEAR, "total_supply_mcm"].iloc[0]
    )

    # Observed 2013-2016 mean
    obs_window = window[window["year"].isin(CRISIS_YEARS)]
    obs_natural_mean = float(obs_window["natural_source_mcm"].mean())
    obs_total_mean = float(obs_window["total_supply_mcm"].mean())
    observed_natural_reduction_pct = 100.0 * (1 - obs_natural_mean / base_2012_natural)
    observed_total_reduction_pct = 100.0 * (1 - obs_total_mean / base_2012_total)

    # Modelled: apply drought at each severity, without changing parameters.
    # The drought function multiplies the DataFrame values for the crisis
    # years by the severity factor. Since the DataFrame's 2013-2016 values
    # already reflect observed history, we instead construct a counterfactual
    # baseline by holding 2013-2016 natural sources at their 2012 values
    # (a pre-drought anchor), then apply the crisis. This matches the
    # manuscript's framing of "what Pessimistic drought would produce from a
    # pre-drought baseline."
    counterfactual = baseline.copy()
    cf_mask = counterfactual["year"].isin(CRISIS_YEARS)
    pre_drought_kinneret = float(
        baseline.loc[baseline["year"] == BASELINE_YEAR, "produced_by_kinneret_milion_m3"].iloc[0]
    )
    pre_drought_ground = float(
        baseline.loc[baseline["year"] == BASELINE_YEAR, "capped_groundwater"].iloc[0]
    )
    counterfactual.loc[cf_mask, "produced_by_kinneret_milion_m3"] = pre_drought_kinneret
    counterfactual.loc[cf_mask, "capped_groundwater"] = pre_drought_ground

    modelled_by_severity: dict[str, pd.DataFrame] = {}
    modelled_reductions: dict[str, dict[str, float]] = {}

    for sev in SEVERITIES:
        result = apply_drought_crisis(counterfactual, CRISIS_YEARS, sev, drought_params)
        result_window = result[(result["year"] >= 2010) & (result["year"] <= 2018)].copy()
        result_window["natural_source_mcm"] = natural_source(result_window)
        modelled_by_severity[sev] = result_window

        mod_natural_mean = float(
            result_window[result_window["year"].isin(CRISIS_YEARS)]["natural_source_mcm"].mean()
        )
        mod_total_mean = float(
            result_window[result_window["year"].isin(CRISIS_YEARS)]["total_supply_mcm"].mean()
        )
        modelled_reductions[sev] = {
            "natural_mean_mcm": mod_natural_mean,
            "total_mean_mcm": mod_total_mean,
            "natural_reduction_pct": 100.0 * (1 - mod_natural_mean / base_2012_natural),
            "total_reduction_pct": 100.0 * (1 - mod_total_mean / base_2012_total),
        }

    mod_pes = modelled_reductions["Pessimistic"]["natural_reduction_pct"]
    discrepancy_pp = mod_pes - observed_natural_reduction_pct
    if abs(discrepancy_pp) <= 3:
        direction = f"close agreement (within {discrepancy_pp:+.1f} pp)"
        verdict = (
            "close fit — modelled Pessimistic trajectory agrees with observed "
            "decline to within ±3 pp"
        )
    elif discrepancy_pp > 3:
        direction = f"model over-predicts by {discrepancy_pp:.1f} pp"
        verdict = (
            "appropriately conservative upper bound — the Pessimistic parameterisation "
            "exceeds the observed 2013–2016 decline, consistent with its intended role "
            "as an unmitigated-impact stress-test anchor rather than a prediction of "
            "operational outcomes (which in Israel are moderated by desalination "
            "substitution and groundwater preservation policy)"
        )
    else:
        direction = f"model under-predicts by {abs(discrepancy_pp):.1f} pp"
        verdict = (
            "direction-of-bias limitation — the Pessimistic parameterisation falls "
            "short of the observed 2013–2016 decline; future applications should "
            "consider widening the Pessimistic drought parameter"
        )

    # --- Table S8 data ---------------------------------------------------
    table_s8 = window[["year"]].copy()
    table_s8["observed_natural_source_mcm"] = window["natural_source_mcm"].to_numpy()
    table_s8["observed_total_supply_mcm"] = window["total_supply_mcm"].to_numpy()
    for sev in SEVERITIES:
        mw = modelled_by_severity[sev]
        table_s8[f"modelled_{sev.lower()}_natural_mcm"] = mw["natural_source_mcm"].to_numpy()
        table_s8[f"modelled_{sev.lower()}_total_mcm"] = mw["total_supply_mcm"].to_numpy()
    table_s8["percent_of_2012_baseline_natural_observed"] = (
        100.0 * table_s8["observed_natural_source_mcm"] / base_2012_natural
    )
    table_s8["percent_of_2012_baseline_total_observed"] = (
        100.0 * table_s8["observed_total_supply_mcm"] / base_2012_total
    )
    for sev in SEVERITIES:
        table_s8[f"percent_of_2012_natural_modelled_{sev.lower()}"] = (
            100.0 * table_s8[f"modelled_{sev.lower()}_natural_mcm"] / base_2012_natural
        )
    table_s8.to_csv(OUTPUT_DIR / "table_s8_retrospective_data.csv", index=False)

    # --- Scalars ---------------------------------------------------------
    scalars = {
        "BASELINE_YEAR_FOR_NORMALISATION": BASELINE_YEAR,
        "CRISIS_YEARS": CRISIS_YEARS,
        "BASELINE_2012_NATURAL_MCM": round(base_2012_natural, 2),
        "BASELINE_2012_TOTAL_MCM": round(base_2012_total, 2),
        "OBSERVED_2013_2016_NATURAL_MEAN_MCM": round(obs_natural_mean, 2),
        "OBSERVED_2013_2016_TOTAL_MEAN_MCM": round(obs_total_mean, 2),
        "OBSERVED_2013_2016_REDUCTION": round(observed_natural_reduction_pct, 1),
        "OBSERVED_2013_2016_TOTAL_REDUCTION": round(observed_total_reduction_pct, 1),
        "MODELLED_OPTIMISTIC_REDUCTION": round(
            modelled_reductions["Optimistic"]["natural_reduction_pct"], 1
        ),
        "MODELLED_MODERATE_REDUCTION": round(
            modelled_reductions["Moderate"]["natural_reduction_pct"], 1
        ),
        "MODELLED_2013_2016_REDUCTION": round(mod_pes, 1),  # Pessimistic (headline)
        "DISCREPANCY": round(discrepancy_pp, 1),
        "DIRECTION_OF_BIAS": direction,
        "CONSISTENCY_CHECK_VERDICT": verdict,
    }
    (OUTPUT_DIR / "scalars.json").write_text(json.dumps(scalars, indent=2))

    # --- Figure -----------------------------------------------------------
    fig, (ax_nat, ax_tot) = plt.subplots(1, 2, figsize=(14, 5))
    years = window["year"].to_numpy()

    # Observed series
    ax_nat.plot(years, window["natural_source_mcm"], "ko-", label="Observed (IWA 1990–2023)",
                markersize=5, linewidth=1.8, zorder=5)
    ax_tot.plot(years, window["total_supply_mcm"], "ko-", label="Observed (IWA 1990–2023)",
                markersize=5, linewidth=1.8, zorder=5)

    sev_colors = {"Optimistic": "#2ca02c", "Moderate": "#ff7f0e", "Pessimistic": "#d62728"}
    for sev in SEVERITIES:
        mw = modelled_by_severity[sev]
        ax_nat.plot(mw["year"], mw["natural_source_mcm"], "-o", color=sev_colors[sev],
                    markersize=4, linewidth=1.5, alpha=0.85,
                    label=f"Modelled drought, {sev}")
        ax_tot.plot(mw["year"], mw["total_supply_mcm"], "-o", color=sev_colors[sev],
                    markersize=4, linewidth=1.5, alpha=0.85,
                    label=f"Modelled drought, {sev}")

    for ax, ylabel, title in (
        (ax_nat, "Natural-source supply (MCM/yr)", "(a) Natural sources (Kinneret + wells)"),
        (ax_tot, "Total supply (MCM/yr)", "(b) Total system supply"),
    ):
        ax.axvspan(CRISIS_YEARS[0] - 0.5, CRISIS_YEARS[-1] + 0.5,
                   color="lightgrey", alpha=0.4, label="2013–2016 window")
        ax.axhline(base_2012_natural if ax is ax_nat else base_2012_total,
                   color="#555", linestyle=":", linewidth=1,
                   label="2012 baseline level")
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(alpha=0.3)
        ax.legend(loc="lower left", fontsize=8)

    fig.suptitle(
        "Task 1 — Retrospective grounding: modelled vs observed 2013–2016 Levant drought",
        fontsize=13, fontweight="bold")
    fig.tight_layout()
    for ext in ("pdf", "png", "svg"):
        fig.savefig(OUTPUT_DIR / f"figure_retrospective_grounding.{ext}",
                    dpi=160, bbox_inches="tight")
    plt.close(fig)

    # --- Run log ---------------------------------------------------------
    log_lines = [
        "Task 1 — Retrospective grounding (2013–2016 Levant drought)",
        "",
        f"Baseline year (pre-drought anchor): {BASELINE_YEAR}",
        f"  2012 natural-source supply: {base_2012_natural:.1f} MCM",
        f"  2012 total supply:          {base_2012_total:.1f} MCM",
        "",
        f"Observed 2013–2016 mean natural-source supply: {obs_natural_mean:.1f} MCM",
        f"Observed 2013–2016 mean total supply:          {obs_total_mean:.1f} MCM",
        f"Observed natural-source reduction vs 2012:     {observed_natural_reduction_pct:.2f}%",
        f"Observed total-supply reduction vs 2012:       {observed_total_reduction_pct:.2f}%",
        "",
        "Modelled reductions (natural source, no γ, no MC):",
    ]
    for sev in SEVERITIES:
        r = modelled_reductions[sev]
        log_lines.append(
            f"  {sev:12s}: natural {r['natural_reduction_pct']:5.2f}%, "
            f"total {r['total_reduction_pct']:5.2f}%"
        )
    log_lines.extend([
        "",
        f"Headline (Pessimistic) discrepancy (modelled − observed): {discrepancy_pp:+.2f} pp",
        f"Direction of bias: {direction}",
        f"Verdict: {verdict}",
    ])
    (OUTPUT_DIR / "run.log").write_text("\n".join(log_lines) + "\n")
    print("\n".join(log_lines))
    print(f"\nOutputs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
