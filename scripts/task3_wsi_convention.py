"""Task 3 — Alternative WSI-convention robustness check.

Under the manuscript convention:
    WSI = demand / renewable_supply
    renewable_supply = natural + reuse      (desalination excluded)

Under the alternative convention:
    WSI_alt = demand / renewable_alt
    renewable_alt = natural + desalination  (reuse excluded)

For each of the 243 scenarios (deterministic Tier 3, no Monte Carlo) we
compute ΔWSI under both conventions and report:
  - Spearman ρ between the two ΔWSI orderings
  - Overlap count of the top-15 most severe scenarios
  - Scatter plot (Supp Figure S6)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from multicrisis.compound import apply_crisis_sequence, enumerate_scenarios, scenario_name
from multicrisis.config import DEFAULT_CRISIS_YEARS, GAMMA_CENTRAL, BASELINE_DATA_PATH, DATA_DIR, RESULTS_DIR, param_path
from multicrisis.crises import load_parameters
from multicrisis.gamma import gamma_product

OUTPUT_DIR = RESULTS_DIR / "task3"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_DATA_PATH)
    baseline["year"] = pd.to_numeric(baseline["year"], errors="coerce")
    params = {c: load_parameters(str(param_path(c)))
              for c in ("drought", "energy", "conflict", "cyber")}
    crisis_years = list(DEFAULT_CRISIS_YEARS)

    # Baseline crisis-year means under each convention
    base_cy = baseline[baseline["year"].isin(crisis_years)]
    base_demand = float(base_cy["total_demand"].mean())
    base_renew_current = float(base_cy["renewable_supply_mcm"].mean())
    # Alt renewable = total - reuse (i.e. natural + desalination)
    base_renew_alt = float((base_cy["total_supply_mcm"] - base_cy["capped_reuse"]).mean())
    wsi_base_current = base_demand / base_renew_current
    wsi_base_alt = base_demand / base_renew_alt

    rows = []
    for comp in enumerate_scenarios():
        tier1_result = apply_crisis_sequence(baseline, crisis_years, comp, params)
        tier1_cy = tier1_result[tier1_result["year"].isin(crisis_years)]
        demand_t1 = float(tier1_cy["total_demand"].mean())
        renew_current_t1 = float(tier1_cy["renewable_supply_mcm"].mean())
        renew_alt_t1 = float((tier1_cy["total_supply_mcm"] - tier1_cy["capped_reuse"]).mean())

        gp = gamma_product(comp, GAMMA_CENTRAL)

        # Under the surviving-fraction γ formulation: each aggregate supply
        # is divided by γ_product to reach Tier 3.
        renew_current_t3 = renew_current_t1 / gp
        renew_alt_t3 = renew_alt_t1 / gp

        wsi_current_t3 = demand_t1 / renew_current_t3 if renew_current_t3 > 0 else float("nan")
        wsi_alt_t3 = demand_t1 / renew_alt_t3 if renew_alt_t3 > 0 else float("nan")

        delta_wsi_current = wsi_current_t3 - wsi_base_current
        delta_wsi_alt = wsi_alt_t3 - wsi_base_alt

        rows.append({
            "scenario_id": scenario_name(comp),
            "size": len(comp),
            "pes_count": sum(1 for _, s in comp if s == "Pessimistic"),
            "gamma_product": gp,
            "delta_wsi_current_convention": delta_wsi_current,
            "delta_wsi_alt_convention": delta_wsi_alt,
        })
    df = pd.DataFrame(rows)

    # Ranks for both conventions
    df["rank_current"] = df["delta_wsi_current_convention"].rank(ascending=False, method="min").astype(int)
    df["rank_alt"] = df["delta_wsi_alt_convention"].rank(ascending=False, method="min").astype(int)

    valid = df.dropna(subset=["delta_wsi_current_convention", "delta_wsi_alt_convention"])
    rho, p = stats.spearmanr(valid["delta_wsi_current_convention"], valid["delta_wsi_alt_convention"])
    rho_val = float(rho)

    # Top-15 overlap
    top15_current = set(df.nlargest(15, "delta_wsi_current_convention")["scenario_id"])
    top15_alt = set(df.nlargest(15, "delta_wsi_alt_convention")["scenario_id"])
    overlap = len(top15_current & top15_alt)

    df.to_csv(OUTPUT_DIR / "wsi_comparison.csv", index=False)

    scalars = {
        "RHO": round(rho_val, 3),
        "P_VALUE": float(p),
        "N_VALID": int(len(valid)),
        "N_EXCLUDED": int(len(df) - len(valid)),
        "TOP15_OVERLAP_CONVENTIONS": overlap,
        "BASELINE_WSI_CURRENT_CONVENTION": round(wsi_base_current, 4),
        "BASELINE_WSI_ALT_CONVENTION": round(wsi_base_alt, 4),
    }
    (OUTPUT_DIR / "scalars.json").write_text(json.dumps(scalars, indent=2))

    # Figure S6
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(valid["delta_wsi_current_convention"], valid["delta_wsi_alt_convention"],
               c=valid["pes_count"], cmap="viridis", s=30, alpha=0.8, edgecolor="k",
               linewidth=0.3)
    lim_lo = float(min(valid["delta_wsi_current_convention"].min(),
                       valid["delta_wsi_alt_convention"].min())) * 1.05
    lim_hi = float(max(valid["delta_wsi_current_convention"].max(),
                       valid["delta_wsi_alt_convention"].max())) * 1.05
    ax.plot([lim_lo, lim_hi], [lim_lo, lim_hi], "r--", linewidth=1, alpha=0.6,
            label="Identity")
    ax.set_xlabel("ΔWSI (current convention: renewable = natural + reuse)")
    ax.set_ylabel("ΔWSI (alternative convention: renewable = natural + desalination)")
    ax.set_title(f"Supp Figure S6 — WSI convention comparison across 243 scenarios "
                 f"(Spearman ρ = {rho_val:.3f})")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    cbar = plt.colorbar(ax.collections[0], ax=ax)
    cbar.set_label("Number of pessimistic crises")
    fig.tight_layout()
    for ext in ("pdf", "png", "svg"):
        fig.savefig(OUTPUT_DIR / f"figure_s6_wsi_convention.{ext}",
                    dpi=160, bbox_inches="tight")
    plt.close(fig)

    log = [
        "Task 3 — Alternative WSI-convention robustness check",
        f"Spearman ρ (current vs alt): {rho_val:.4f}  (p = {p:.3g})",
        f"Top-15 overlap: {overlap} / 15",
        f"Baseline WSI (current convention): {wsi_base_current:.4f}",
        f"Baseline WSI (alt convention):     {wsi_base_alt:.4f}",
    ]
    (OUTPUT_DIR / "run.log").write_text("\n".join(log) + "\n")
    print("\n".join(log))
    if rho_val < 0.6:
        print("\n[WARNING] ρ < 0.6 — manuscript one-sentence claim in Section 2.2 needs revision.")
    elif rho_val >= 0.8:
        print("\n[OK] ρ ≥ 0.8 — scenario-ranking-preserved claim is strongly supported.")
    else:
        print(f"\n[BORDERLINE] 0.6 ≤ ρ < 0.8 — scenario ranking partially preserved.")


if __name__ == "__main__":
    main()
