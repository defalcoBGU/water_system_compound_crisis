"""Monte Carlo sensitivity analysis with tiered γ treatment.

Implements the manuscript Section 2.7 specification:
  - Parameters varied within ±25% of base values (uniform sampling)
  - 500 samples per analysis
  - Same RNG state across all tiers per draw so Tier 1/2/3 comparisons are
    paired (Handover §9 anti-pattern #5)

Three tiers per draw:
  - Tier 1: γ = 1 for all pairs (additive-only)
  - Tier 2: γ sampled per draw from uniform ranges (Table 1)
  - Tier 3: γ at central estimates (Table 1)

Implementation note: γ is applied to scalar (crisis-year mean) summaries via
`gamma.apply_gamma_to_metrics`, not to full DataFrame time series. This is
~300× faster than rebuilding the DataFrame for each draw × scenario × tier
and is numerically exact for the three reported metrics.
"""

from __future__ import annotations

import copy
from typing import Any

import numpy as np
import pandas as pd

from multicrisis.compound import apply_crisis_sequence, enumerate_scenarios, scenario_name
from multicrisis.config import (
    GAMMA_CENTRAL,
    GAMMA_RANGES,
    MC_N_DRAWS,
    MC_PARAM_FRACTION,
    RANDOM_SEED,
)
from multicrisis.gamma import (
    active_pairs,
    apply_gamma_to_metrics,
    gamma_product,
    tier1_scalar_metrics,
)


# Which parameter names get ±25% sampling. Metadata fields like DurationYears
# and OPEXCostMultiplier are passed through unchanged because they don't
# affect the water balance arithmetic.
SAMPLED_PARAM_NAMES = frozenset({
    "SurfaceWaterReduction",
    "GroundwaterReduction",
    "NaturalSupplyFactor",
    "DesalCapacityFactor",
    "SupplyCapacityFactor",
    "AgriculturalDemandChange",
    "DomesticDemandChange",
    "IndustrialDemandChange",
    "DesalDowntimeFraction",
    "AffectedSupplyProportion",
})


def sample_params(
    base_params_by_type: dict[str, dict[str, dict[str, Any]]],
    rng: np.random.Generator,
    fraction: float = MC_PARAM_FRACTION,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Return a new params dict where each scalar parameter has been sampled
    uniformly from [base*(1-f), base*(1+f)].

    Supports negative base values (e.g. demand-change parameters in
    conflict_params.csv, which are negative percentages for sector demand
    reductions) by computing min/max after scaling.
    """
    sampled = copy.deepcopy(base_params_by_type)
    for _, param_dict in sampled.items():
        for param_name, severity_dict in param_dict.items():
            if param_name not in SAMPLED_PARAM_NAMES:
                continue
            for severity in list(severity_dict.keys()):
                base = severity_dict[severity]
                lo = base * (1 - fraction)
                hi = base * (1 + fraction)
                sample_lo, sample_hi = min(lo, hi), max(lo, hi)
                severity_dict[severity] = float(rng.uniform(sample_lo, sample_hi))
    return sampled


def sample_gamma(
    ranges: dict[tuple[str, str], tuple[float, float]],
    rng: np.random.Generator,
) -> dict[tuple[str, str], float]:
    """One uniform draw per pair, independent across pairs."""
    return {pair: float(rng.uniform(lo, hi)) for pair, (lo, hi) in ranges.items()}


def run_montecarlo_tiered(
    baseline_data: pd.DataFrame,
    crisis_years: list[int] | tuple[int, ...],
    base_params_by_type: dict[str, dict[str, dict[str, Any]]],
    n_draws: int = MC_N_DRAWS,
    seed: int = RANDOM_SEED,
    verbose: bool = True,
) -> dict[str, pd.DataFrame]:
    """Run the 3-tier Monte Carlo sweep.

    Returns a dict {"tier1": df, "tier2": df, "tier3": df} where each df has
    columns [name, composition, size, opt_count, mod_count, pes_count,
    active_pair_count, draw, supply_reduction, wsi_increase, gap_change,
    gamma_product, renewable_collapsed].
    """
    rng_params = np.random.default_rng(seed)
    rng_gamma = np.random.default_rng(seed + 1)

    scenarios = enumerate_scenarios()
    scenario_meta = [
        {
            "name": scenario_name(c),
            "composition": "|".join(f"{t}:{s}" for t, s in c),
            "size": len(c),
            "pes_count": sum(1 for _, s in c if s == "Pessimistic"),
            "mod_count": sum(1 for _, s in c if s == "Moderate"),
            "opt_count": sum(1 for _, s in c if s == "Optimistic"),
            "active_pair_count": len(active_pairs(c)),
        }
        for c in scenarios
    ]

    records: dict[str, list[dict[str, Any]]] = {"tier1": [], "tier2": [], "tier3": []}

    for draw in range(n_draws):
        if verbose and (draw % 25 == 0 or draw == n_draws - 1):
            print(f"  draw {draw+1:4d} / {n_draws}")

        sampled_params = sample_params(base_params_by_type, rng_params)
        sampled_gamma = sample_gamma(GAMMA_RANGES, rng_gamma)

        for composition, meta in zip(scenarios, scenario_meta):
            tier1_result = apply_crisis_sequence(
                baseline_data, crisis_years, composition, sampled_params
            )
            tier1_scalars, base_scalars = tier1_scalar_metrics(
                baseline_data, tier1_result, crisis_years
            )

            # Tier 1: γ = 1 (identity under amplify_reduction)
            m1 = apply_gamma_to_metrics(tier1_scalars, base_scalars, gamma_prod=1.0)
            records["tier1"].append({**meta, "draw": draw, **m1})

            # Tier 2: γ sampled per pair
            gp_t2 = gamma_product(composition, sampled_gamma)
            m2 = apply_gamma_to_metrics(tier1_scalars, base_scalars, gamma_prod=gp_t2)
            records["tier2"].append({**meta, "draw": draw, **m2})

            # Tier 3: γ at central values
            gp_t3 = gamma_product(composition, GAMMA_CENTRAL)
            m3 = apply_gamma_to_metrics(tier1_scalars, base_scalars, gamma_prod=gp_t3)
            records["tier3"].append({**meta, "draw": draw, **m3})

    return {k: pd.DataFrame(v) for k, v in records.items()}
