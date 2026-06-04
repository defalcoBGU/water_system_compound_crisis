"""Task 5 — Response-mapping threshold ±20 % sensitivity.

Four response categories (manuscript Section 2.6):
  1. Supply Expansion: supply_reduction > 40 %
  2. Sustainability Measures: ΔWSI > 0.5
  3. Emergency Measures: gap worse than median of the ensemble
  4. Resilience Hardening: conflict or cyber at moderate+ severity

For the three numerically-threshold categories we vary the threshold by ±20 %
and report trigger frequency across the 243 scenarios. For Resilience
Hardening (severity-class threshold) we test three severity bars:
optimistic+, moderate+ (baseline), pessimistic only.

All runs use Tier 3 deterministic results.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from multicrisis.compound import apply_crisis_sequence, enumerate_scenarios, scenario_name
from multicrisis.config import DEFAULT_CRISIS_YEARS, GAMMA_CENTRAL, BASELINE_DATA_PATH, DATA_DIR, RESULTS_DIR, param_path
from multicrisis.crises import load_parameters
from multicrisis.gamma import apply_gamma_to_metrics, gamma_product, tier1_scalar_metrics

OUTPUT_DIR = RESULTS_DIR / "task5"

SUPPLY_THRESHOLD = 40.0
WSI_THRESHOLD = 0.5


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_DATA_PATH)
    baseline["year"] = pd.to_numeric(baseline["year"], errors="coerce")
    params = {c: load_parameters(str(param_path(c)))
              for c in ("drought", "energy", "conflict", "cyber")}

    # Deterministic Tier 3 sweep
    rows = []
    for comp in enumerate_scenarios():
        tier1_result = apply_crisis_sequence(baseline, list(DEFAULT_CRISIS_YEARS), comp, params)
        t1s, bs = tier1_scalar_metrics(baseline, tier1_result, DEFAULT_CRISIS_YEARS)
        gp = gamma_product(comp, GAMMA_CENTRAL)
        m = apply_gamma_to_metrics(t1s, bs, gp)

        severities_by_type = {t: s for t, s in comp}
        conflict_sev = severities_by_type.get("conflict", None)
        cyber_sev = severities_by_type.get("cyber", None)

        rows.append({
            "scenario_id": scenario_name(comp),
            "supply_reduction": m["supply_reduction"],
            "wsi_increase": m["wsi_increase"],
            "gap_change": m["gap_change"],
            "conflict_severity": conflict_sev or "None",
            "cyber_severity": cyber_sev or "None",
        })
    df = pd.DataFrame(rows)

    median_gap = float(df["gap_change"].median())

    # Threshold scenarios
    supply_levels = [SUPPLY_THRESHOLD * 0.8, SUPPLY_THRESHOLD, SUPPLY_THRESHOLD * 1.2]
    wsi_levels = [WSI_THRESHOLD * 0.8, WSI_THRESHOLD, WSI_THRESHOLD * 1.2]
    gap_levels = [median_gap * 0.8, median_gap, median_gap * 1.2]

    def severity_at_least(sev: str, bar: str) -> bool:
        order = {"None": -1, "Optimistic": 0, "Moderate": 1, "Pessimistic": 2}
        return order.get(sev, -1) >= order[bar]

    results = []
    for label, col, levels, rule in (
        ("Supply Expansion", "supply_reduction", supply_levels, lambda x, t: x > t),
        ("Sustainability Measures", "wsi_increase", wsi_levels, lambda x, t: x > t),
        ("Emergency Measures", "gap_change", gap_levels, lambda x, t: x < t),
    ):
        for level_name, level_val in zip(("low_80pct", "baseline_100pct", "high_120pct"), levels):
            freq = 100.0 * (df[col].map(lambda x: rule(x, level_val)).sum()) / len(df)
            results.append({
                "category": label,
                "threshold_label": level_name,
                "threshold_value": level_val,
                "trigger_frequency_pct": round(freq, 2),
            })

    # Resilience Hardening: severity-class thresholds
    for bar_name, bar in (("Optimistic+ (loose)", "Optimistic"),
                          ("Moderate+ (baseline)", "Moderate"),
                          ("Pessimistic only (tight)", "Pessimistic")):
        n = int(sum(
            severity_at_least(c, bar) or severity_at_least(cy, bar)
            for c, cy in zip(df["conflict_severity"], df["cyber_severity"])
        ))
        freq = 100.0 * n / len(df)
        results.append({
            "category": "Resilience Hardening",
            "threshold_label": bar_name,
            "threshold_value": bar,
            "trigger_frequency_pct": round(freq, 2),
        })

    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_DIR / "threshold_sensitivity.csv", index=False)

    # Figure S7: bar chart per category
    categories = result_df["category"].unique()
    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
    for ax, cat in zip(axes, categories):
        sub = result_df[result_df["category"] == cat]
        colors = ["#66b3ff", "#333333", "#ff6666"]
        ax.bar(sub["threshold_label"], sub["trigger_frequency_pct"], color=colors)
        ax.set_title(cat, fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Trigger frequency (% of scenarios)")
        ax.tick_params(axis="x", rotation=25, labelsize=8)
        for i, (_, r) in enumerate(sub.iterrows()):
            ax.text(i, r["trigger_frequency_pct"] + 1, f"{r['trigger_frequency_pct']:.1f}",
                    ha="center", fontsize=8)
    fig.suptitle("Supp Figure S7 — Response-threshold ±20 % sensitivity across 243 scenarios",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    for ext in ("pdf", "png", "svg"):
        fig.savefig(OUTPUT_DIR / f"figure_s7_response_threshold.{ext}",
                    dpi=160, bbox_inches="tight")
    plt.close(fig)

    log = ["Task 5 — Response-threshold ±20 % sensitivity"]
    log.append(f"Median gap_change across 243 Tier 3 scenarios: {median_gap:.2f} MCM")
    log.append("")
    log.append(result_df.to_string(index=False))
    (OUTPUT_DIR / "run.log").write_text("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    main()
