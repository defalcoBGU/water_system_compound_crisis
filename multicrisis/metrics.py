"""Headline metrics extracted from per-draw Monte Carlo output.

All metrics are computed from the long-format per-draw DataFrames produced by
`run_montecarlo_tiered()`. This module does not re-run the model; it only
aggregates.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def percentile_ci(samples: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    """Percentile 1-α CI. Default 95 %."""
    lo = float(np.quantile(samples, alpha / 2))
    hi = float(np.quantile(samples, 1 - alpha / 2))
    return lo, hi


def fisher_r2_ci(r: float, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Fisher-transformed 1-α CI on R², given Pearson r and sample size."""
    if not np.isfinite(r) or abs(r) >= 1.0 or n < 4:
        return float("nan"), float("nan")
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    z_lo, z_hi = z - z_crit * se, z + z_crit * se
    r_lo, r_hi = np.tanh(z_lo), np.tanh(z_hi)
    # r² CI: square the endpoint closest to 0 vs farthest, respecting sign
    r2_lo = min(r_lo**2, r_hi**2)
    r2_hi = max(r_lo**2, r_hi**2)
    # If r crosses zero in the CI, lower R² bound is 0
    if r_lo * r_hi < 0:
        r2_lo = 0.0
    return float(r2_lo), float(r2_hi)


def worst_case_summary(tier_df: pd.DataFrame) -> dict[str, Any]:
    """Summarise the four-pessimistic worst-case scenario across draws."""
    four_pes = tier_df[tier_df["pes_count"] == 4].copy()
    if four_pes.empty:
        return {}
    # There should be exactly 1 four-pessimistic scenario × n_draws rows
    assert four_pes["name"].nunique() == 1, (
        f"expected 1 four-pessimistic scenario, got {four_pes['name'].nunique()}"
    )
    samples = four_pes["supply_reduction"].to_numpy()
    lo, hi = percentile_ci(samples)
    return {
        "name": four_pes["name"].iloc[0],
        "point_estimate": float(np.mean(samples)),
        "median": float(np.median(samples)),
        "ci_lo": lo,
        "ci_hi": hi,
        "std": float(np.std(samples, ddof=1)) if len(samples) > 1 else 0.0,
        "n_draws": int(len(samples)),
    }


def r2_pes_vs_wsi(tier_df: pd.DataFrame) -> dict[str, Any]:
    """R² of pessimistic-count → WSI increase across all scenarios, averaged over draws.

    Strategy: take the per-scenario MEAN over draws (tempering MC noise into
    a single point per scenario) and fit OLS across the 243 scenarios. This
    matches the manuscript's framing of a single reported R² for the
    scenario ensemble, not a distribution of R² per draw.

    Scenarios in which ALL draws produced renewable-supply collapse (NaN
    WSI) are excluded from the regression; the count is reported as
    `n_excluded` so the reader can assess how representative the regression
    is of the full 243-scenario ensemble.
    """
    mean_per_scenario = (
        tier_df.groupby("name")[["pes_count", "wsi_increase"]].mean().reset_index()
    )
    n_total = len(mean_per_scenario)
    valid = mean_per_scenario.dropna(subset=["wsi_increase"])
    n_excluded = n_total - len(valid)
    if len(valid) < 4:
        return {
            "r": float("nan"),
            "r_squared": float("nan"),
            "r2_ci_lo": float("nan"),
            "r2_ci_hi": float("nan"),
            "n_scenarios": int(n_total),
            "n_valid": int(len(valid)),
            "n_excluded": int(n_excluded),
        }
    x = valid["pes_count"].to_numpy()
    y = valid["wsi_increase"].to_numpy()
    r = stats.linregress(x, y).rvalue
    ci_lo, ci_hi = fisher_r2_ci(r, n=len(valid))
    return {
        "r": float(r),
        "r_squared": float(r**2),
        "r2_ci_lo": ci_lo,
        "r2_ci_hi": ci_hi,
        "n_scenarios": int(n_total),
        "n_valid": int(len(valid)),
        "n_excluded": int(n_excluded),
    }


def top_k_set(
    tier_df: pd.DataFrame, k: int = 15, by: str = "supply_reduction"
) -> pd.DataFrame:
    """Top-k scenarios by mean of `by` across draws."""
    mean_per_scenario = (
        tier_df.groupby(["name", "composition"])[by].mean().reset_index()
    )
    return mean_per_scenario.sort_values(by, ascending=False).head(k)


def security_dominance_check(tier_df: pd.DataFrame, k: int = 15) -> dict[str, Any]:
    """Inspect top-k composition for security-crisis dominance patterns.

    Returns three distinct dominance signals so the manuscript claim can be
    reported honestly per correction C9:
      - `strict_security_dominance`: top-k all contain pes conflict AND pes cyber
        (the manuscript's current wording)
      - `conflict_dominance`: top-k all contain pes conflict
      - `cyber_dominance`: top-k all contain pes cyber
    """
    top = top_k_set(tier_df, k=k)

    def pes_in(composition_str: str, crisis_type: str) -> bool:
        return f"{crisis_type}:Pessimistic" in composition_str.split("|")

    n_pes_conflict = int(sum(pes_in(c, "conflict") for c in top["composition"]))
    n_pes_cyber = int(sum(pes_in(c, "cyber") for c in top["composition"]))
    n_with_both = int(sum(
        pes_in(c, "conflict") and pes_in(c, "cyber") for c in top["composition"]
    ))

    return {
        "k": k,
        "n_with_pes_conflict_and_cyber": n_with_both,
        "n_with_pes_conflict": n_pes_conflict,
        "n_with_pes_cyber": n_pes_cyber,
        "strict_security_dominance": bool(n_with_both == k),
        "conflict_dominance": bool(n_pes_conflict == k),
        "cyber_dominance": bool(n_pes_cyber == k),
        "top_k_names": top["name"].tolist(),
    }


def top_k_overlap(
    tier_a: pd.DataFrame, tier_b: pd.DataFrame, k: int = 15
) -> dict[str, Any]:
    """Overlap between top-k sets of two tiers."""
    a = set(top_k_set(tier_a, k=k)["name"])
    b = set(top_k_set(tier_b, k=k)["name"])
    return {
        "k": k,
        "overlap": len(a & b),
        "tier_a_only": sorted(a - b),
        "tier_b_only": sorted(b - a),
    }


def interaction_amplification_stats(tier_df: pd.DataFrame) -> dict[str, Any]:
    """For Tiers 2/3: distribution of active γ products across scenarios.

    Uses the first draw's scenario rows (Tier 3 γ values are constant across
    draws; Tier 2 γ varies per draw but active_pair_count is fixed per
    scenario, so mean γ_product across draws is what we report for Tier 2).
    """
    if "gamma_product" not in tier_df.columns:
        return {}
    mean_per_scenario = tier_df.groupby("name")["gamma_product"].mean()
    n_with_interaction = int((mean_per_scenario > 1.0).sum())
    return {
        "mean_gamma_product": float(mean_per_scenario.mean()),
        "median_gamma_product": float(mean_per_scenario.median()),
        "max_gamma_product": float(mean_per_scenario.max()),
        "min_gamma_product": float(mean_per_scenario.min()),
        "n_scenarios_with_interaction": n_with_interaction,
        "n_total": int(len(mean_per_scenario)),
        "pct_with_interaction": 100.0 * n_with_interaction / len(mean_per_scenario),
    }
