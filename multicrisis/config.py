"""Central configuration for the multicrisis model.

All constants that could otherwise drift between runs are collected here.
Every value must either be traceable to a manuscript/literature source or
documented as an arbitrary implementation choice (e.g. RNG seed).
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Directory layout (package-relative; survives renaming the top-level folder)
# ---------------------------------------------------------------------------
PACKAGE_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PACKAGE_ROOT / "data"
RESULTS_DIR: Path = PACKAGE_ROOT / "results"
BASELINE_DATA_PATH: Path = DATA_DIR / "baseline_data_processed.csv"

def param_path(crisis_type: str) -> Path:
    """Path to a per-crisis severity-parameter CSV."""
    return DATA_DIR / f"{crisis_type}_params.csv"

# ---------------------------------------------------------------------------
# Random seed
# ---------------------------------------------------------------------------
# Arbitrary but fixed across all Monte Carlo runs. Set once, never re-seeded
# mid-task. Recorded in every run manifest and in MANUSCRIPT_CORRECTIONS.md.
RANDOM_SEED: int = 20260423  # YYYYMMDD of the seed decision

# ---------------------------------------------------------------------------
# Interaction multipliers (γ)
# ---------------------------------------------------------------------------
# Source: revised manuscript Table 1, with citations to Hassanzadeh 2020,
# Gleick 2014, Busby 2021, Bazilian 2011. Central values are used in Tier 3;
# tested ranges are used in Tier 2 (uniform sampling, independent per draw).
#
# Convention: γ ≥ 1 scales the compound supply-reduction fraction. γ = 1
# recovers additive-only interaction (Tier 1).

INTERACTION_PAIRS: tuple[tuple[str, str], ...] = (
    ("conflict", "cyber"),
    ("drought", "conflict"),
    ("energy", "cyber"),
    ("drought", "energy"),
)

GAMMA_CENTRAL: dict[tuple[str, str], float] = {
    ("conflict", "cyber"): 1.15,
    ("drought", "conflict"): 1.10,
    ("energy", "cyber"): 1.12,
    ("drought", "energy"): 1.08,
}

# Uniform sampling ranges for Tier 2 (lower, upper). Manuscript Table 1.
GAMMA_RANGES: dict[tuple[str, str], tuple[float, float]] = {
    ("conflict", "cyber"): (1.00, 1.25),
    ("drought", "conflict"): (1.00, 1.20),
    ("energy", "cyber"): (1.00, 1.20),
    ("drought", "energy"): (1.00, 1.15),
}

# ---------------------------------------------------------------------------
# Monte Carlo configuration
# ---------------------------------------------------------------------------
# Source: manuscript Section 2.7 ("parameters are varied within ±25% of base
# values ... 500 samples generated per analysis").
MC_N_DRAWS: int = 500
MC_PARAM_FRACTION: float = 0.25  # ±25 %
MC_SAMPLING: str = "uniform"  # uniform over [base*(1-frac), base*(1+frac)]

# ---------------------------------------------------------------------------
# Scenario enumeration
# ---------------------------------------------------------------------------
# Four crisis types, three severity levels each. Compound sizes 2/3/4 →
# 54 + 108 + 81 = 243 scenarios. Single-crisis scenarios are handled
# separately (Section 3.2 / Task 1).
CRISIS_TYPES: tuple[str, ...] = ("drought", "energy", "conflict", "cyber")
SEVERITIES: tuple[str, ...] = ("Optimistic", "Moderate", "Pessimistic")
COMPOUND_SIZES: tuple[int, ...] = (2, 3, 4)

# ---------------------------------------------------------------------------
# Crisis window
# ---------------------------------------------------------------------------
# Default forward-scenario window. Overridden by scripts that need other
# windows (e.g. Task 1 retrospective uses 2013–2016).
DEFAULT_CRISIS_YEARS: tuple[int, ...] = (2030, 2031, 2032)
