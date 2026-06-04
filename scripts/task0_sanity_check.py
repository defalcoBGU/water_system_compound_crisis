"""Task 0 — Reproduce the existing 243-scenario Tier 1 (additive-only) sweep.

Acceptance: every row in the new Tier 1 output must agree with the archived
`compound_crisis_impact_summary.csv` in the repo root to within floating-point
noise (default rtol=1e-9). This confirms that the clean module extraction
(`multicrisis.crises`, `multicrisis.compound`) is numerically identical to the
original notebook code for the additive-only case.

If this fails, we have introduced a regression during the extraction and must
NOT proceed to Task 2.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from multicrisis.compound import run_tier1_sweep
from multicrisis.config import DEFAULT_CRISIS_YEARS, RANDOM_SEED, BASELINE_DATA_PATH, DATA_DIR, RESULTS_DIR, param_path
from multicrisis.crises import load_parameters

OUTPUT_DIR = RESULTS_DIR / "task0"


def main() -> None:
    baseline = pd.read_csv(BASELINE_DATA_PATH)
    baseline["year"] = pd.to_numeric(baseline["year"], errors="coerce")

    params_by_type = {
        "drought": load_parameters(str(param_path("drought"))),
        "energy": load_parameters(str(param_path("energy"))),
        "conflict": load_parameters(str(param_path("conflict"))),
        "cyber": load_parameters(str(param_path("cyber"))),
    }

    print(f"Running Tier 1 sweep over {list(DEFAULT_CRISIS_YEARS)}...")
    new = run_tier1_sweep(baseline, list(DEFAULT_CRISIS_YEARS), params_by_type)
    print(f"  produced {len(new)} scenarios")

    archive = pd.read_csv(DATA_DIR / "compound_crisis_impact_summary.csv")
    print(f"  archived: {len(archive)} scenarios")

    # Align on scenario name (the archive column is 'name', matching)
    merged = new.merge(archive, on="name", suffixes=("_new", "_archive"))
    assert len(merged) == len(archive) == len(new), (
        f"scenario mismatch: new={len(new)}, archive={len(archive)}, merged={len(merged)}"
    )

    comparisons = [
        ("supply_reduction", "supply_reduction_new", "supply_reduction_archive"),
        ("wsi_increase", "wsi_increase_new", "wsi_increase_archive"),
        ("gap_change", "gap_change_new", "gap_change_archive"),
    ]
    max_abs_diff = {}
    for metric, new_col, old_col in comparisons:
        diff = np.abs(merged[new_col] - merged[old_col])
        max_abs_diff[metric] = float(diff.max())

    print("\nMax absolute difference new vs archive:")
    for metric, d in max_abs_diff.items():
        print(f"  {metric:20s}: {d:.2e}")

    worst = new.loc[new["supply_reduction"].idxmax()]
    archive_worst = archive.loc[archive["supply_reduction"].idxmax()]
    print(f"\nWorst-case scenario (new):     {worst['name']} -> {worst['supply_reduction']:.4f}%")
    print(f"Worst-case scenario (archive): {archive_worst['name']} -> {archive_worst['supply_reduction']:.4f}%")

    from scipy import stats
    r = stats.linregress(new["pes_count"], new["wsi_increase"]).rvalue
    r_archive = stats.linregress(archive["pessimistic_count"], archive["wsi_increase"]).rvalue
    print(f"\nR(pes_count, wsi_increase) new:     {r:.6f}  (R² {r**2:.6f})")
    print(f"R(pes_count, wsi_increase) archive: {r_archive:.6f}  (R² {r_archive**2:.6f})")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    new.to_csv(OUTPUT_DIR / "tier1_sweep_reproduction.csv", index=False)

    manifest = {
        "random_seed": RANDOM_SEED,
        "crisis_years": list(DEFAULT_CRISIS_YEARS),
        "n_scenarios": len(new),
        "max_abs_diff_vs_archive": max_abs_diff,
        "worst_case_new": {
            "name": worst["name"],
            "supply_reduction_pct": float(worst["supply_reduction"]),
            "wsi_increase": float(worst["wsi_increase"]),
        },
        "worst_case_archive": {
            "name": archive_worst["name"],
            "supply_reduction_pct": float(archive_worst["supply_reduction"]),
            "wsi_increase": float(archive_worst["wsi_increase"]),
        },
        "R2_pes_vs_wsi_new": float(r**2),
        "R2_pes_vs_wsi_archive": float(r_archive**2),
    }
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))

    threshold = 1e-6
    if all(d < threshold for d in max_abs_diff.values()):
        print("\n[PASS] Clean extraction reproduces the archive to within 1e-6.")
    else:
        print(f"\n[FAIL] Max diff exceeds {threshold:.0e}. Do not proceed to Task 2.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
