"""γ interaction-multiplier layer — surviving-fraction formulation.

Applied on top of a Tier 1 (additive-only) scenario result to produce Tier 2
(γ sampled) or Tier 3 (γ at central estimates) outputs.

Mathematical convention (documented in results/earth_future_revision/
MANUSCRIPT_CORRECTIONS.md, entry C1):

    σ_tier1      = S_tier1 / S_baseline         (surviving fraction, Tier 1)
    σ_tier       = σ_tier1 / ∏ γ_{i,j,active}   (γ divides surviving supply)
    S_tier       = S_baseline × σ_tier
    R_tier       = 1 − σ_tier                   (supply-reduction fraction)

Applied separately to total supply and renewable supply. Demand carries
through from Tier 1 unchanged — γ scope is supply only (manuscript §2.2).

This is the unique formulation in which
  - γ ≥ 1 amplifies impact (σ_tier ≤ σ_tier1),
  - γ = 1 recovers Tier 1 exactly,
  - R_tier is bounded in [1 − 1/γ, 1] with no clamping artifacts,
  - No WSI denominator collapses to zero for finite γ,
  - The corresponding WSI propagates cleanly as WSI_tier = WSI_tier1 × γ.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

from multicrisis.config import GAMMA_CENTRAL, INTERACTION_PAIRS


def active_pairs(composition: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return the subset of documented γ pairs whose both members are in the composition."""
    present = {crisis_type for crisis_type, _ in composition}
    return [pair for pair in INTERACTION_PAIRS if pair[0] in present and pair[1] in present]


def gamma_product(
    composition: list[tuple[str, str]],
    gamma_values: dict[tuple[str, str], float] = GAMMA_CENTRAL,
) -> float:
    """Product of γ values across all active pairs in this composition."""
    product = 1.0
    for pair in active_pairs(composition):
        product *= gamma_values[pair]
    return product


def apply_gamma_to_metrics(
    tier1_scalars: dict[str, float],
    baseline_scalars: dict[str, float],
    gamma_prod: float,
) -> dict[str, float]:
    """Amplify Tier 1 supply metrics to a higher tier's γ-product.

    Parameters
    ----------
    tier1_scalars : dict with keys
        'total_supply_mcm', 'renewable_supply_mcm', 'total_demand'
        (crisis-year means from the Tier 1 post-crisis DataFrame)
    baseline_scalars : dict with same keys (crisis-year means of baseline)
    gamma_prod : float ≥ 1
        Product of active γ values for this scenario composition

    Returns
    -------
    dict with keys:
        'supply_reduction' (%), 'wsi_increase', 'gap_change',
        'gamma_product', 'renewable_collapsed' (bool — degenerate cases)
    """
    base_total = baseline_scalars["total_supply_mcm"]
    base_renew = baseline_scalars["renewable_supply_mcm"]
    base_demand = baseline_scalars["total_demand"]

    t1_total = tier1_scalars["total_supply_mcm"]
    t1_renew = tier1_scalars["renewable_supply_mcm"]
    t1_demand = tier1_scalars["total_demand"]

    # Surviving fractions under Tier 1
    sigma_total_t1 = t1_total / base_total if base_total > 0 else 1.0
    sigma_renew_t1 = t1_renew / base_renew if base_renew > 0 else 1.0

    # γ divides the surviving fraction (equivalent to dividing supply by γ)
    sigma_total_tier = sigma_total_t1 / gamma_prod
    sigma_renew_tier = sigma_renew_t1 / gamma_prod

    s_total_tier = base_total * sigma_total_tier
    s_renew_tier = base_renew * sigma_renew_tier

    supply_reduction_pct = 100.0 * (1.0 - sigma_total_tier)

    # WSI uses Tier-1 demand (γ scope is supply only)
    if s_renew_tier > 0:
        wsi_tier = t1_demand / s_renew_tier
        renewable_collapsed = False
    else:
        wsi_tier = float("nan")
        renewable_collapsed = True

    wsi_base = base_demand / base_renew if base_renew > 0 else float("nan")
    wsi_increase = wsi_tier - wsi_base if np.isfinite(wsi_tier) and np.isfinite(wsi_base) else float("nan")

    gap_tier = s_total_tier - t1_demand
    gap_base = base_total - base_demand
    gap_change = gap_tier - gap_base

    return {
        "supply_reduction": supply_reduction_pct,
        "wsi_increase": wsi_increase,
        "gap_change": gap_change,
        "gamma_product": gamma_prod,
        "renewable_collapsed": renewable_collapsed,
    }


def tier1_scalar_metrics(
    baseline_data,
    tier1_result,
    crisis_years: Iterable[int],
) -> tuple[dict[str, float], dict[str, float]]:
    """Extract the crisis-year means needed by `apply_gamma_to_metrics`.

    Returns (tier1_scalars, baseline_scalars).
    """
    years_list = list(crisis_years)
    base_cy = baseline_data[baseline_data["year"].isin(years_list)]
    post_cy = tier1_result[tier1_result["year"].isin(years_list)]
    baseline_scalars = {
        "total_supply_mcm": float(base_cy["total_supply_mcm"].mean()),
        "renewable_supply_mcm": float(base_cy["renewable_supply_mcm"].mean()),
        "total_demand": float(base_cy["total_demand"].mean()),
    }
    tier1_scalars = {
        "total_supply_mcm": float(post_cy["total_supply_mcm"].mean()),
        "renewable_supply_mcm": float(post_cy["renewable_supply_mcm"].mean()),
        "total_demand": float(post_cy["total_demand"].mean()),
    }
    return tier1_scalars, baseline_scalars
