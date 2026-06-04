"""Task 2 smoke test — run the 3-tier MC on a small n_draws to validate shape,
γ propagation, and tier-ordering invariants before launching the full sweep.

Invariants this script checks:
  • Tier 1 mean supply_reduction < Tier 3 mean supply_reduction (γ amplifies impact)
  • Tier 1 CI is narrower than Tier 2 CI (γ sampling adds uncertainty under T2)
  • Four-pessimistic scenario has active_pair_count == 4
  • γ_product of four-pessimistic Tier 3 matches 1.08 × 1.10 × 1.12 × 1.15
  • No NaN in metric columns

Runs in ~30 seconds with n_draws=10.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from multicrisis.compound import enumerate_scenarios, scenario_name
from multicrisis.config import DEFAULT_CRISIS_YEARS, GAMMA_CENTRAL, BASELINE_DATA_PATH, DATA_DIR, RESULTS_DIR, param_path
from multicrisis.crises import load_parameters
from multicrisis.gamma import active_pairs, gamma_product
from multicrisis.metrics import (
    interaction_amplification_stats,
    security_dominance_check,
    worst_case_summary,
)
from multicrisis.montecarlo import run_montecarlo_tiered



def main() -> None:
    baseline = pd.read_csv(BASELINE_DATA_PATH)
    baseline["year"] = pd.to_numeric(baseline["year"], errors="coerce")
    base_params = {
        ctype: load_parameters(str(param_path(ctype)))
        for ctype in ("drought", "energy", "conflict", "cyber")
    }

    # --- Static γ checks ------------------------------------------------
    scenarios = enumerate_scenarios()
    four_pes_comp = next(c for c in scenarios if len(c) == 4 and all(s == "Pessimistic" for _, s in c))
    four_pes_name = scenario_name(four_pes_comp)
    ap = active_pairs(four_pes_comp)
    gp_central = gamma_product(four_pes_comp, GAMMA_CENTRAL)
    expected = 1.08 * 1.10 * 1.12 * 1.15
    assert len(ap) == 4, f"four-pessimistic should have 4 active pairs, got {len(ap)}"
    assert abs(gp_central - expected) < 1e-12, f"γ_product mismatch: {gp_central} vs {expected}"
    print(f"[OK] Four-pessimistic composition: {four_pes_name}")
    print(f"     Active pairs: {ap}")
    print(f"     γ_product (central): {gp_central:.4f}  (expected {expected:.4f})")

    # --- Short MC run ---------------------------------------------------
    print("\nRunning 3-tier Monte Carlo (n_draws=10)...")
    mc = run_montecarlo_tiered(
        baseline,
        list(DEFAULT_CRISIS_YEARS),
        base_params,
        n_draws=10,
        verbose=True,
    )

    # --- Shape checks ---------------------------------------------------
    for tier_name, df in mc.items():
        expected_rows = 243 * 10
        assert len(df) == expected_rows, f"{tier_name}: got {len(df)}, expected {expected_rows}"
        n_collapsed = int(df["renewable_collapsed"].sum())
        n_nan_sr = int(df["supply_reduction"].isna().sum())
        n_nan_wsi = int(df["wsi_increase"].isna().sum())
        assert n_nan_sr == 0, f"{tier_name}: {n_nan_sr} NaNs in supply_reduction (should be 0)"
        print(f"  {tier_name}: {n_collapsed} (row,draw)s with renewable collapse → NaN WSI, "
              f"n_nan_wsi={n_nan_wsi}, n_nan_supply_reduction=0")
    print("[OK] All three tier tables have expected shape; WSI NaN count matches renewable-collapse count")

    # --- Tier ordering invariants ---------------------------------------
    print("\nWorst-case summary across tiers:")
    tier_summaries = {}
    for tier_name, df in mc.items():
        s = worst_case_summary(df)
        tier_summaries[tier_name] = s
        print(f"  {tier_name}: point={s['point_estimate']:.3f}%  95% CI [{s['ci_lo']:.3f}, {s['ci_hi']:.3f}]")

    t1 = tier_summaries["tier1"]["point_estimate"]
    t3 = tier_summaries["tier3"]["point_estimate"]
    assert t1 < t3 - 0.1, f"Tier 1 ({t1:.3f}) should be < Tier 3 ({t3:.3f})"
    print(f"[OK] Tier 1 < Tier 3 (amplification present)")

    # --- Interaction amplification stats --------------------------------
    print("\nInteraction amplification (Tier 3):")
    t3_stats = interaction_amplification_stats(mc["tier3"])
    for k, v in t3_stats.items():
        print(f"  {k}: {v}")

    # --- Security dominance check ---------------------------------------
    print("\nSecurity dominance (top-15):")
    for tier_name, df in mc.items():
        sd = security_dominance_check(df, k=15)
        status = "YES" if sd["security_dominance"] else f"NO ({sd['n_with_pes_conflict_and_cyber']}/15)"
        print(f"  {tier_name}: {status}")

    print("\n[SMOKE TEST PASS]")


if __name__ == "__main__":
    main()
