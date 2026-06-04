"""Task 2 — tiered Monte Carlo sweep over all 243 scenarios.

Produces, per tier {1, 2, 3}:
  - Per-scenario summary (one row per of 243 scenarios, means across draws)
  - Per-draw raw data (243 × n_draws rows, for distribution plots)
  - scalars.json with all placeholder values
  - Figure S2: three-panel distribution of worst-case supply reduction

All outputs go to `results/earth_future_revision/task2/`.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from multicrisis.config import (
    BASELINE_DATA_PATH,
    DATA_DIR,
    DEFAULT_CRISIS_YEARS,
    GAMMA_CENTRAL,
    GAMMA_RANGES,
    MC_N_DRAWS,
    MC_PARAM_FRACTION,
    RANDOM_SEED,
    RESULTS_DIR,
    param_path,
)
from multicrisis.crises import load_parameters
from multicrisis.gamma import active_pairs, gamma_product
from multicrisis.metrics import (
    interaction_amplification_stats,
    percentile_ci,
    r2_pes_vs_wsi,
    security_dominance_check,
    top_k_overlap,
    top_k_set,
    worst_case_summary,
)
from multicrisis.montecarlo import run_montecarlo_tiered

OUTPUT_DIR = RESULTS_DIR / "task2"


def per_scenario_summary(tier_df: pd.DataFrame) -> pd.DataFrame:
    """Mean and 95 % CI per scenario, one row per of 243 scenarios."""
    rows = []
    for name, grp in tier_df.groupby("name", sort=False):
        meta = grp.iloc[0][["composition", "size", "pes_count", "mod_count",
                             "opt_count", "active_pair_count"]].to_dict()
        sr = grp["supply_reduction"].to_numpy()
        wsi = grp["wsi_increase"].to_numpy()
        gc = grp["gap_change"].to_numpy()
        sr_lo, sr_hi = percentile_ci(sr)
        wsi_valid = wsi[np.isfinite(wsi)]
        wsi_lo, wsi_hi = (percentile_ci(wsi_valid) if wsi_valid.size > 0
                          else (float("nan"), float("nan")))
        rows.append({
            "name": name,
            **meta,
            "supply_reduction_mean": float(np.mean(sr)),
            "supply_reduction_ci_lo": sr_lo,
            "supply_reduction_ci_hi": sr_hi,
            "supply_reduction_std": float(np.std(sr, ddof=1)),
            "wsi_increase_mean": float(np.mean(wsi_valid)) if wsi_valid.size > 0 else float("nan"),
            "wsi_increase_ci_lo": wsi_lo,
            "wsi_increase_ci_hi": wsi_hi,
            "gap_change_mean": float(np.mean(gc)),
            "gamma_product_mean": float(grp["gamma_product"].mean()) if "gamma_product" in grp.columns else 1.0,
            "n_renewable_collapsed": int(grp["renewable_collapsed"].sum()),
        })
    return pd.DataFrame(rows)


def build_scalars(mc: dict[str, pd.DataFrame]) -> dict:
    """Build the scalars.json payload for manuscript placeholder fill-in."""
    out = {
        "run_metadata": {
            "random_seed": RANDOM_SEED,
            "n_draws": MC_N_DRAWS,
            "param_fraction": MC_PARAM_FRACTION,
            "crisis_years": list(DEFAULT_CRISIS_YEARS),
            "gamma_central": {f"{a}-{b}": v for (a, b), v in GAMMA_CENTRAL.items()},
            "gamma_ranges": {f"{a}-{b}": list(v) for (a, b), v in GAMMA_RANGES.items()},
        }
    }

    for tier_key, tier_df in mc.items():
        tier_n = tier_key[-1]  # "tier1" -> "1"
        worst = worst_case_summary(tier_df)
        r2 = r2_pes_vs_wsi(tier_df)
        dom = security_dominance_check(tier_df, k=15)
        amp = interaction_amplification_stats(tier_df)

        out[f"T{tier_n}_POINT_ESTIMATE"] = round(worst["point_estimate"], 3)
        out[f"T{tier_n}_CI_LO"] = round(worst["ci_lo"], 3)
        out[f"T{tier_n}_CI_HI"] = round(worst["ci_hi"], 3)
        out[f"T{tier_n}_WORST_CASE_SCENARIO"] = worst["name"]
        out[f"T{tier_n}_R2"] = round(r2["r_squared"], 4)
        out[f"T{tier_n}_R2_CI_LO"] = round(r2["r2_ci_lo"], 4)
        out[f"T{tier_n}_R2_CI_HI"] = round(r2["r2_ci_hi"], 4)
        out[f"T{tier_n}_R2_N_VALID"] = r2["n_valid"]
        out[f"T{tier_n}_STRICT_SECURITY_DOMINANCE"] = dom["strict_security_dominance"]
        out[f"T{tier_n}_CONFLICT_DOMINANCE"] = dom["conflict_dominance"]
        out[f"T{tier_n}_CYBER_DOMINANCE"] = dom["cyber_dominance"]
        out[f"T{tier_n}_TOP15_WITH_BOTH"] = dom["n_with_pes_conflict_and_cyber"]
        out[f"T{tier_n}_TOP15_WITH_PES_CONFLICT"] = dom["n_with_pes_conflict"]
        out[f"T{tier_n}_TOP15_WITH_PES_CYBER"] = dom["n_with_pes_cyber"]
        out[f"T{tier_n}_PCT_SCENARIOS_WITH_INTERACTION"] = (
            round(amp["pct_with_interaction"], 2) if amp else None
        )
        out[f"T{tier_n}_MEAN_GAMMA_PRODUCT"] = (
            round(amp["mean_gamma_product"], 4) if amp else 1.0
        )
        out[f"T{tier_n}_MAX_GAMMA_PRODUCT"] = (
            round(amp["max_gamma_product"], 4) if amp else 1.0
        )

    # Cross-tier top-15 overlaps
    out["T1_TOP15_OVERLAP_WITH_T3"] = top_k_overlap(mc["tier1"], mc["tier3"], k=15)["overlap"]
    out["T2_TOP15_OVERLAP_WITH_T3"] = top_k_overlap(mc["tier2"], mc["tier3"], k=15)["overlap"]

    return out


def plot_figure_s2(mc: dict[str, pd.DataFrame], path: Path) -> None:
    """Three-panel distribution of worst-case (four-pessimistic) supply reduction."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharex=True, sharey=True)
    x_lo, x_hi = 60, 100
    bins = np.linspace(x_lo, x_hi, 50)
    labels = [
        ("tier1", "Tier 1 (γ = 1, additive-only)"),
        ("tier2", "Tier 2 (γ ~ U, Table 1 ranges)"),
        ("tier3", "Tier 3 (γ at central values)"),
    ]
    for ax, (tier_key, label) in zip(axes, labels):
        df = mc[tier_key]
        fourpes = df[df["pes_count"] == 4]["supply_reduction"].to_numpy()
        ax.hist(fourpes, bins=bins, alpha=0.85, edgecolor="black", linewidth=0.5)
        mean = float(np.mean(fourpes))
        lo, hi = percentile_ci(fourpes)
        ax.axvline(mean, color="red", linestyle="--", linewidth=1.5,
                   label=f"Mean {mean:.2f}%")
        ax.axvline(lo, color="orange", linestyle=":", linewidth=1.2,
                   label=f"95% CI [{lo:.2f}, {hi:.2f}]")
        ax.axvline(hi, color="orange", linestyle=":", linewidth=1.2)
        ax.set_title(label)
        ax.set_xlabel("Supply reduction (%) — four-pessimistic scenario")
        ax.legend(fontsize=9, loc="upper left")
        ax.set_xlim(x_lo, x_hi)
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel("Frequency (n draws)")
    fig.suptitle(
        "Figure S2 — Monte Carlo distribution of worst-case supply reduction by tier",
        fontsize=13, fontweight="bold")
    fig.tight_layout()
    for ext in ("pdf", "png", "svg"):
        fig.savefig(path.with_suffix("." + ext), dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_DATA_PATH)
    baseline["year"] = pd.to_numeric(baseline["year"], errors="coerce")
    base_params = {
        ctype: load_parameters(str(param_path(ctype)))
        for ctype in ("drought", "energy", "conflict", "cyber")
    }

    print(f"Running tiered MC: {MC_N_DRAWS} draws × 243 scenarios × 3 tiers")
    print(f"  Seed: {RANDOM_SEED}")
    print(f"  Crisis years: {list(DEFAULT_CRISIS_YEARS)}")
    print(f"  Param fraction: ±{MC_PARAM_FRACTION*100:.0f}%")
    t0 = time.time()

    mc = run_montecarlo_tiered(
        baseline,
        list(DEFAULT_CRISIS_YEARS),
        base_params,
        n_draws=MC_N_DRAWS,
        seed=RANDOM_SEED,
        verbose=True,
    )

    elapsed = time.time() - t0
    print(f"\nCompleted in {elapsed:.1f} s ({elapsed/60:.1f} min)")

    # Write per-draw raw tables
    for tier_key, df in mc.items():
        df.to_csv(OUTPUT_DIR / f"{tier_key}_per_draw.csv", index=False)

    # Write per-scenario summaries
    for tier_key, df in mc.items():
        summ = per_scenario_summary(df)
        summ.to_csv(OUTPUT_DIR / f"{tier_key}_scenario_results.csv", index=False)

    # Scalars
    scalars = build_scalars(mc)
    scalars["runtime_seconds"] = round(elapsed, 1)
    (OUTPUT_DIR / "scalars.json").write_text(json.dumps(scalars, indent=2))

    # Figure S2
    plot_figure_s2(mc, OUTPUT_DIR / "figure_s2_tiered_mc")

    # Run log
    log_lines = [
        f"Task 2 run completed {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Seed: {RANDOM_SEED}",
        f"Draws: {MC_N_DRAWS}",
        f"Crisis years: {list(DEFAULT_CRISIS_YEARS)}",
        f"Runtime: {elapsed:.1f} s",
        "",
        "Headline (worst-case supply reduction, 4-pessimistic):",
    ]
    for tier in ("tier1", "tier2", "tier3"):
        pe = scalars[f"T{tier[-1]}_POINT_ESTIMATE"]
        lo = scalars[f"T{tier[-1]}_CI_LO"]
        hi = scalars[f"T{tier[-1]}_CI_HI"]
        log_lines.append(f"  {tier}: {pe}% (95% CI {lo}–{hi}%)")
    log_lines.append("")
    log_lines.append("Security dominance (top-15):")
    for tier in ("tier1", "tier2", "tier3"):
        tn = tier[-1]
        log_lines.append(
            f"  {tier}: strict={scalars[f'T{tn}_STRICT_SECURITY_DOMINANCE']}  "
            f"conflict-only={scalars[f'T{tn}_CONFLICT_DOMINANCE']}  "
            f"top15_with_both={scalars[f'T{tn}_TOP15_WITH_BOTH']}/15"
        )
    log_lines.append("")
    log_lines.append("R²(pes_count, wsi_increase):")
    for tier in ("tier1", "tier2", "tier3"):
        tn = tier[-1]
        log_lines.append(
            f"  {tier}: R² = {scalars[f'T{tn}_R2']} "
            f"(95% CI {scalars[f'T{tn}_R2_CI_LO']}–{scalars[f'T{tn}_R2_CI_HI']}, "
            f"n_valid = {scalars[f'T{tn}_R2_N_VALID']})"
        )
    (OUTPUT_DIR / "run.log").write_text("\n".join(log_lines) + "\n")

    # Echo to console
    print("\n" + "\n".join(log_lines))
    print(f"\nOutputs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
