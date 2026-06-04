"""Single-crisis impact functions.

Extracted from baseline_converted.py.py (the nbconvert export of baseline.ipynb).
Behaviour is preserved verbatim where possible — the only changes from the
original are (a) removal of silent fallback default dicts when the parameter
CSV lookup fails, so that genuine parameter errors surface instead of being
masked, and (b) docstring clean-up. Numerical outputs are byte-identical to
the original for matching inputs; this is verified by `task0_sanity_check.py`.

Sources for the per-severity parameters: drought_params.csv, energy_params.csv,
conflict_params.csv, cyber_params.csv in the repo root. Manuscript Supp
Tables S2 and S3 document the parameter provenance.
"""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd


SUPPLY_COLS = (
    "water_desalination_mcm",
    "capped_groundwater",
    "produced_by_kinneret_milion_m3",
    "capped_reuse",
    "total_produced_by_upper_water_milion_m3",
)
RENEWABLE_COLS = (
    "capped_groundwater",
    "produced_by_kinneret_milion_m3",
    "capped_reuse",
    "total_produced_by_upper_water_milion_m3",
)


def _recompute_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute total supply, renewable supply, surplus, WSI, DDR in place.

    Called at the end of each crisis function once the per-source adjustments
    have been made. Mirrors the inline block that appears five times in the
    original code (once per crisis function plus one helper).
    """
    supply_cols = [c for c in SUPPLY_COLS if c in df.columns]
    renewable_cols = [c for c in RENEWABLE_COLS if c in df.columns]

    df["total_supply_mcm"] = df[supply_cols].sum(axis=1, skipna=True)
    df["renewable_supply_mcm"] = df[renewable_cols].sum(axis=1, skipna=True)
    df["surplus_mcm"] = df["total_supply_mcm"] - df["total_demand"]
    df["wsi"] = np.where(
        df["renewable_supply_mcm"] > 0,
        df["total_demand"] / df["renewable_supply_mcm"],
        np.nan,
    )
    df["ddr"] = np.where(
        df["total_supply_mcm"] > 0,
        df["water_desalination_mcm"] / df["total_supply_mcm"],
        0,
    )
    return df


def _get_param(
    params: dict[str, dict[str, Any]], name: str, severity: str
) -> float:
    """Fetch a per-severity parameter. Raises if missing (no silent defaults)."""
    if name not in params or severity not in params[name]:
        raise KeyError(
            f"Parameter '{name}' / severity '{severity}' not in parameter CSV."
        )
    return float(params[name][severity])


def apply_drought_crisis(
    baseline_data: pd.DataFrame,
    crisis_years: Iterable[int],
    severity: str,
    params: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Apply drought effects: reduce surface (Kinneret) and groundwater."""
    result = baseline_data.copy()
    surface_factor = _get_param(params, "SurfaceWaterReduction", severity)
    ground_factor = _get_param(params, "GroundwaterReduction", severity)

    mask = result["year"].isin(crisis_years)
    if "produced_by_kinneret_milion_m3" in result.columns:
        result.loc[mask, "produced_by_kinneret_milion_m3"] *= surface_factor
    if "capped_groundwater" in result.columns:
        result.loc[mask, "capped_groundwater"] *= ground_factor
    return _recompute_totals(result)


def apply_energy_crisis(
    baseline_data: pd.DataFrame,
    crisis_years: Iterable[int],
    severity: str,
    params: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Apply energy effects: reduce desalination capacity."""
    result = baseline_data.copy()
    desal_factor = _get_param(params, "DesalCapacityFactor", severity)

    mask = result["year"].isin(crisis_years)
    result.loc[mask, "water_desalination_mcm"] *= desal_factor
    return _recompute_totals(result)


def apply_conflict_crisis(
    baseline_data: pd.DataFrame,
    crisis_years: Iterable[int],
    severity: str,
    params: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Apply conflict effects: reduce all supply sources + sector-specific demand."""
    result = baseline_data.copy()
    supply_factor = _get_param(params, "SupplyCapacityFactor", severity)
    ag_change = _get_param(params, "AgriculturalDemandChange", severity)
    dom_change = _get_param(params, "DomesticDemandChange", severity)
    ind_change = _get_param(params, "IndustrialDemandChange", severity)

    mask = result["year"].isin(crisis_years)
    for col in SUPPLY_COLS:
        if col in result.columns:
            result.loc[mask, col] *= supply_factor

    # Sector-specific demand changes where per-sector columns exist
    sector_cols = {
        "Agricultural (milion m3)": ag_change,
        "Domestic (milion m3)": dom_change,
        "Industrial (milion m3)": ind_change,
    }
    for col, change in sector_cols.items():
        if col in result.columns:
            result.loc[mask, col] *= 1 + change

    # Total-demand update
    demand_cols = [
        "Agricultural (milion m3)",
        "Domestic (milion m3)",
        "Industrial (milion m3)",
        " Water for the environment (milion m3)",
        "       Other suppliers ",
    ]
    available = [c for c in demand_cols if c in result.columns]
    if available:
        has_valid = (result.loc[mask, available].sum(axis=1, skipna=True) > 0).any()
    else:
        has_valid = False

    if has_valid:
        result["total_demand"] = result[available].sum(axis=1, skipna=True)
    else:
        # Projected years: no per-sector breakdown, apply weighted average.
        # Weighting (0.60 ag / 0.25 dom / 0.15 ind) is from baseline_converted.py.py
        # and reflects Israel's typical demand composition at projection time.
        weighted = 0.60 * ag_change + 0.25 * dom_change + 0.15 * ind_change
        result.loc[mask, "total_demand"] *= 1 + weighted

    result["total_demand_mcm"] = result["total_demand"]
    return _recompute_totals(result)


def apply_cyber_crisis(
    baseline_data: pd.DataFrame,
    crisis_years: Iterable[int],
    severity: str,
    params: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Apply cyber effects: desalination downtime + infrastructure impact.

    Natural sources are impacted at half the "affected proportion" rate; this
    reflects the partial dependency of natural-source delivery on SCADA-style
    control systems (see manuscript Section 2.3 on cyber vulnerability
    propagation through control infrastructure).
    """
    result = baseline_data.copy()
    desal_downtime = _get_param(params, "DesalDowntimeFraction", severity)
    affected = _get_param(params, "AffectedSupplyProportion", severity)

    mask = result["year"].isin(crisis_years)
    if "water_desalination_mcm" in result.columns:
        result.loc[mask, "water_desalination_mcm"] *= 1 - desal_downtime
    for col in ("capped_reuse",):
        if col in result.columns:
            result.loc[mask, col] *= 1 - affected
    for col in ("capped_groundwater", "produced_by_kinneret_milion_m3",
               "total_produced_by_upper_water_milion_m3"):
        if col in result.columns:
            result.loc[mask, col] *= 1 - affected * 0.5
    return _recompute_totals(result)


CRISIS_FUNCTIONS = {
    "drought": apply_drought_crisis,
    "energy": apply_energy_crisis,
    "conflict": apply_conflict_crisis,
    "cyber": apply_cyber_crisis,
}


def load_parameters(filepath: str) -> dict[str, dict[str, Any]]:
    """Load a per-severity parameter CSV. Schema: Parameter, Optimistic, Moderate, Pessimistic.

    Raises if the file cannot be read — callers must not swallow errors,
    because silent fallbacks produced the "close enough" defaults in the
    original code that this module deliberately removes.
    """
    df = pd.read_csv(filepath)
    if "Parameter" not in df.columns:
        raise ValueError(f"Parameter CSV {filepath} missing 'Parameter' column.")
    out: dict[str, dict[str, Any]] = {}
    for _, row in df.iterrows():
        name = row["Parameter"]
        out[name] = {
            col: float(row[col])
            for col in df.columns
            if col != "Parameter" and pd.notna(row[col])
        }
    return out
