"""Task 4 — Demand elasticity ±50 % sensitivity.

For each sector-specific Pessimistic demand-change parameter (from
conflict_params.csv), scale by 0.5 and 1.5 independently and record the
effect on the four-pessimistic worst-case supply reduction.

Parameters tested (Pessimistic-severity values only; the four-pessimistic
scenario uses all Pessimistic severities by definition):
  - AgriculturalDemandChange (base −0.30)
  - DomesticDemandChange (base −0.10)
  - IndustrialDemandChange (base −0.20)

All runs deterministic (no MC), Tier 3 γ values applied.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from multicrisis.compound import apply_crisis_sequence
from multicrisis.config import DEFAULT_CRISIS_YEARS, GAMMA_CENTRAL, BASELINE_DATA_PATH, DATA_DIR, RESULTS_DIR, param_path
from multicrisis.crises import load_parameters
from multicrisis.gamma import apply_gamma_to_metrics, gamma_product, tier1_scalar_metrics

OUTPUT_DIR = RESULTS_DIR / "task4"


PARAMS_TO_TEST = [
    ("conflict", "AgriculturalDemandChange"),
    ("conflict", "DomesticDemandChange"),
    ("conflict", "IndustrialDemandChange"),
]
SCALES = (0.5, 1.0, 1.5)


def run_with_scaled_param(
    baseline: pd.DataFrame,
    base_params: dict,
    crisis_type: str,
    param_name: str,
    severity: str,
    scale: float,
) -> dict[str, float]:
    """Return 4-pessimistic headline metrics (Tier 3) with the given param scaled.

    Reports supply_reduction, wsi_increase, and gap_change because demand-change
    parameters do not affect supply_reduction (they modify demand, not supply)
    but do affect WSI and the supply-demand gap.
    """
    params = copy.deepcopy(base_params)
    base_val = params[crisis_type][param_name][severity]
    params[crisis_type][param_name][severity] = base_val * scale

    comp = [("drought", "Pessimistic"), ("energy", "Pessimistic"),
            ("conflict", "Pessimistic"), ("cyber", "Pessimistic")]
    tier1_result = apply_crisis_sequence(baseline, list(DEFAULT_CRISIS_YEARS), comp, params)
    t1s, bs = tier1_scalar_metrics(baseline, tier1_result, DEFAULT_CRISIS_YEARS)
    gp = gamma_product(comp, GAMMA_CENTRAL)
    m = apply_gamma_to_metrics(t1s, bs, gp)
    return {
        "supply_reduction": float(m["supply_reduction"]),
        "wsi_increase": float(m["wsi_increase"]),
        "gap_change": float(m["gap_change"]),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_DATA_PATH)
    baseline["year"] = pd.to_numeric(baseline["year"], errors="coerce")
    base_params = {c: load_parameters(str(param_path(c)))
                   for c in ("drought", "energy", "conflict", "cyber")}

    severity = "Pessimistic"
    rows = []
    for crisis_type, param_name in PARAMS_TO_TEST:
        base_val = base_params[crisis_type][param_name][severity]
        row = {
            "parameter_name": f"{crisis_type}.{param_name}.{severity}",
            "base_value": base_val,
        }
        metric_values: dict[str, dict[float, float]] = {
            "supply_reduction": {}, "wsi_increase": {}, "gap_change": {},
        }
        for scale in SCALES:
            worst = run_with_scaled_param(
                baseline, base_params, crisis_type, param_name, severity, scale,
            )
            for metric, val in worst.items():
                metric_values[metric][scale] = val
                row[f"{metric}_at_{scale:g}x".replace(".", "_")] = round(val, 4)
        # Range across the three scales, for each metric
        for metric in metric_values:
            vals = list(metric_values[metric].values())
            row[f"{metric}_range"] = round(max(vals) - min(vals), 4)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "table_s6_demand_elasticity.csv", index=False)

    most_sensitive_supply = df.loc[df["supply_reduction_range"].idxmax()]
    most_sensitive_wsi = df.loc[df["wsi_increase_range"].idxmax()]
    most_sensitive_gap = df.loc[df["gap_change_range"].idxmax()]
    scalars = {
        "NOTE": (
            "Demand-change parameters do not affect supply_reduction (they modify "
            "demand, not supply). WSI and gap_change are the informative metrics."
        ),
        "MOST_SENSITIVE_PARAM_FOR_SUPPLY_REDUCTION": most_sensitive_supply["parameter_name"],
        "MAX_SUPPLY_REDUCTION_RANGE_PP": float(most_sensitive_supply["supply_reduction_range"]),
        "MOST_SENSITIVE_PARAM_FOR_WSI_INCREASE": most_sensitive_wsi["parameter_name"],
        "MAX_WSI_INCREASE_RANGE": float(most_sensitive_wsi["wsi_increase_range"]),
        "MOST_SENSITIVE_PARAM_FOR_GAP_CHANGE": most_sensitive_gap["parameter_name"],
        "MAX_GAP_CHANGE_RANGE_MCM": float(most_sensitive_gap["gap_change_range"]),
        "BASELINE_WORST_CASE_SUPPLY_REDUCTION": float(df["supply_reduction_at_1x"].iloc[0]),
    }
    (OUTPUT_DIR / "scalars.json").write_text(json.dumps(scalars, indent=2))

    log = ["Task 4 — Demand elasticity ±50 % sensitivity (4-pessimistic, Tier 3)", ""]
    log.append(
        "Note: demand-change parameters do NOT affect supply_reduction (they modify\n"
        "demand, not supply). WSI and gap_change are the informative metrics below."
    )
    log.append("")
    for metric_label, key in (
        ("Supply reduction (%)", "supply_reduction"),
        ("WSI increase (absolute)", "wsi_increase"),
        ("Gap change (MCM)", "gap_change"),
    ):
        log.append(f"--- {metric_label} ---")
        log.append(f"{'Parameter':50s} {'base':>10s} {'x0.5':>10s} {'x1.0':>10s} {'x1.5':>10s} {'range':>10s}")
        for _, r in df.iterrows():
            log.append(
                f"{r['parameter_name']:50s} "
                f"{r['base_value']:10.3f} "
                f"{r[f'{key}_at_0_5x']:10.3f} "
                f"{r[f'{key}_at_1x']:10.3f} "
                f"{r[f'{key}_at_1_5x']:10.3f} "
                f"{r[f'{key}_range']:10.4f}"
            )
        log.append("")
    log.append(
        f"Most sensitive for supply_reduction: {scalars['MOST_SENSITIVE_PARAM_FOR_SUPPLY_REDUCTION']} "
        f"(range {scalars['MAX_SUPPLY_REDUCTION_RANGE_PP']:.3f} pp)"
    )
    log.append(
        f"Most sensitive for wsi_increase:     {scalars['MOST_SENSITIVE_PARAM_FOR_WSI_INCREASE']} "
        f"(range {scalars['MAX_WSI_INCREASE_RANGE']:.4f})"
    )
    log.append(
        f"Most sensitive for gap_change:       {scalars['MOST_SENSITIVE_PARAM_FOR_GAP_CHANGE']} "
        f"(range {scalars['MAX_GAP_CHANGE_RANGE_MCM']:.2f} MCM)"
    )
    (OUTPUT_DIR / "run.log").write_text("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    main()
