"""Compound crisis enumeration and sequential application.

Enumerates the 243 scenarios (4 crisis types × 3 severities, subset sizes
2/3/4) and applies each as a sequence of single-crisis operations. This is
the additive-only (Tier 1) compound model: no γ interaction multipliers.
The γ layer is applied separately in `multicrisis.gamma`.
"""

from __future__ import annotations

from itertools import combinations, product
from typing import Any

import numpy as np
import pandas as pd

from multicrisis.config import COMPOUND_SIZES, CRISIS_TYPES, SEVERITIES
from multicrisis.crises import CRISIS_FUNCTIONS


def apply_crisis_sequence(
    baseline_data: pd.DataFrame,
    crisis_years: list[int] | tuple[int, ...],
    sequence: list[tuple[str, str]],
    params_by_type: dict[str, dict[str, dict[str, Any]]],
) -> pd.DataFrame:
    """Apply a sequence of (crisis_type, severity) pairs, each stacking on the last.

    Order within the sequence does not materially change the outcome because
    each single-crisis function multiplies source columns and re-computes
    totals from scratch. Verified in the sanity-check script.
    """
    result = baseline_data.copy()
    for crisis_type, severity in sequence:
        apply_fn = CRISIS_FUNCTIONS[crisis_type]
        result = apply_fn(result, crisis_years, severity, params_by_type[crisis_type])
    return result


def enumerate_scenarios(
    crisis_types: tuple[str, ...] = CRISIS_TYPES,
    severities: tuple[str, ...] = SEVERITIES,
    sizes: tuple[int, ...] = COMPOUND_SIZES,
) -> list[list[tuple[str, str]]]:
    """Produce the full list of scenario compositions.

    Default arguments yield 4C2·3² + 4C3·3³ + 4C4·3⁴ = 54 + 108 + 81 = 243.
    """
    out: list[list[tuple[str, str]]] = []
    for size in sizes:
        for subset in combinations(crisis_types, size):
            for severity_combo in product(severities, repeat=size):
                out.append(list(zip(subset, severity_combo)))
    return out


def scenario_name(composition: list[tuple[str, str]]) -> str:
    """Canonical name, matches baseline_converted.py.py convention."""
    return "+".join(f"{t.capitalize()}({s})" for t, s in composition)


def scenario_impact_metrics(
    baseline_data: pd.DataFrame,
    result: pd.DataFrame,
    crisis_years: list[int] | tuple[int, ...],
) -> dict[str, float]:
    """Compute the three scalar impact metrics for one scenario over crisis years.

    Metrics are means over the crisis_years window (matches the original
    run_compound_crisis_analysis convention).
    """
    base = baseline_data[baseline_data["year"].isin(crisis_years)]
    post = result[result["year"].isin(crisis_years)]
    if base.empty or post.empty:
        return {
            "supply_reduction": np.nan,
            "wsi_increase": np.nan,
            "gap_change": np.nan,
        }
    base_supply = base["total_supply_mcm"].mean()
    post_supply = post["total_supply_mcm"].mean()
    supply_reduction = 100.0 * (base_supply - post_supply) / base_supply

    wsi_increase = np.nan
    if "wsi" in base.columns and "wsi" in post.columns:
        wsi_increase = post["wsi"].mean() - base["wsi"].mean()

    gap_change = np.nan
    if "surplus_mcm" in base.columns and "surplus_mcm" in post.columns:
        gap_change = post["surplus_mcm"].mean() - base["surplus_mcm"].mean()

    return {
        "supply_reduction": supply_reduction,
        "wsi_increase": wsi_increase,
        "gap_change": gap_change,
    }


def run_tier1_sweep(
    baseline_data: pd.DataFrame,
    crisis_years: list[int] | tuple[int, ...],
    params_by_type: dict[str, dict[str, dict[str, Any]]],
) -> pd.DataFrame:
    """Run all 243 scenarios at Tier 1 (additive-only, γ = 1). Returns a tidy DataFrame.

    Columns: name, composition, size, opt_count, mod_count, pes_count,
    supply_reduction, wsi_increase, gap_change.
    """
    rows = []
    for comp in enumerate_scenarios():
        result = apply_crisis_sequence(baseline_data, crisis_years, comp, params_by_type)
        metrics = scenario_impact_metrics(baseline_data, result, crisis_years)
        severities_in_comp = [s for _, s in comp]
        rows.append({
            "name": scenario_name(comp),
            "composition": "|".join(f"{t}:{s}" for t, s in comp),
            "size": len(comp),
            "opt_count": severities_in_comp.count("Optimistic"),
            "mod_count": severities_in_comp.count("Moderate"),
            "pes_count": severities_in_comp.count("Pessimistic"),
            **metrics,
        })
    return pd.DataFrame(rows)
