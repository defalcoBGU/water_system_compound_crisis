"""Task 6 — Literature benchmark template (Supp Table S5).

Produces a template CSV with the modelled single-crisis impacts from the
present model (from references the paper already cites). The "published
impact" and "match category" columns are left blank for the user to fill
from the primary sources — per the no-invented-numbers rule, we do not
populate numeric values from memory.

For each of the four cited events (Texas 2021 energy-water cascade; Cape
Town 2018 Day Zero drought; Oldsmar 2021 water-treatment cyber attack;
Syrian pre-conflict drought/water stress), we report the modelled
single-crisis impact at the matching severity level using the existing
crisis-type parameter CSVs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from multicrisis.compound import scenario_name
from multicrisis.config import DEFAULT_CRISIS_YEARS, GAMMA_CENTRAL, BASELINE_DATA_PATH, DATA_DIR, RESULTS_DIR, param_path
from multicrisis.crises import (
    apply_conflict_crisis,
    apply_cyber_crisis,
    apply_drought_crisis,
    apply_energy_crisis,
    load_parameters,
)
from multicrisis.gamma import apply_gamma_to_metrics, tier1_scalar_metrics

OUTPUT_DIR = RESULTS_DIR / "task6"


def run_single(
    baseline: pd.DataFrame,
    crisis_type: str,
    severity: str,
    apply_fn,
    params: dict,
    crisis_years,
) -> dict[str, float]:
    """Return Tier 1 (single-crisis, no γ) metrics for one event severity."""
    result = apply_fn(baseline, list(crisis_years), severity, params)
    t1s, bs = tier1_scalar_metrics(baseline, result, crisis_years)
    m = apply_gamma_to_metrics(t1s, bs, gamma_prod=1.0)
    return {
        "supply_reduction_pct": round(float(m["supply_reduction"]), 2),
        "wsi_increase": round(float(m["wsi_increase"]), 4),
        "gap_change_mcm": round(float(m["gap_change"]), 2),
    }


EVENTS = [
    {
        "event": "2021 Texas winter storm (energy–water cascade)",
        "date": "2021-02",
        "crisis_type": "energy",
        "severity_anchor": "Pessimistic",
        "primary_ref": "Busby et al. 2021 (Ref 6)",
        "secondary_ref": "Flores et al. 2023 (Ref 8)",
    },
    {
        "event": "2018 Cape Town 'Day Zero' drought",
        "date": "2015-2018",
        "crisis_type": "drought",
        "severity_anchor": "Pessimistic",
        "primary_ref": "Pascale et al. 2020 (Ref 9)",
        "secondary_ref": "Booysen et al. 2019 (Ref 10)",
    },
    {
        "event": "2021 Oldsmar, Florida water-treatment cyber attack",
        "date": "2021-02",
        "crisis_type": "cyber",
        "severity_anchor": "Pessimistic",
        "primary_ref": "Hassanzadeh et al. 2020 (Ref 7)",
        "secondary_ref": "",
    },
    {
        "event": "Syrian pre-conflict water stress (drought + conflict)",
        "date": "2006-2011",
        "crisis_type": "conflict",
        "severity_anchor": "Pessimistic",
        "primary_ref": "Gleick 2014 (Ref 4)",
        "secondary_ref": "Van Loon et al. 2016 (Ref 11)",
    },
]

APPLY_FUNCTIONS = {
    "drought": apply_drought_crisis,
    "energy": apply_energy_crisis,
    "conflict": apply_conflict_crisis,
    "cyber": apply_cyber_crisis,
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_DATA_PATH)
    baseline["year"] = pd.to_numeric(baseline["year"], errors="coerce")
    params_by_type = {c: load_parameters(str(param_path(c)))
                       for c in ("drought", "energy", "conflict", "cyber")}

    rows = []
    for ev in EVENTS:
        crisis = ev["crisis_type"]
        apply_fn = APPLY_FUNCTIONS[crisis]
        params = params_by_type[crisis]
        row = {
            "event": ev["event"],
            "date": ev["date"],
            "primary_citation": ev["primary_ref"],
            "secondary_citation": ev["secondary_ref"],
            "published_impact": "[FILL FROM CITED PAPER — do NOT estimate]",
            "published_impact_units": "[e.g. % supply reduction, million people affected, $ billion loss]",
        }
        for sev in ("Optimistic", "Moderate", "Pessimistic"):
            m = run_single(baseline, crisis, sev, apply_fn, params, DEFAULT_CRISIS_YEARS)
            row[f"modelled_{sev.lower()}_supply_reduction_pct"] = m["supply_reduction_pct"]
            row[f"modelled_{sev.lower()}_wsi_increase"] = m["wsi_increase"]
        row["match_category"] = (
            "[FILL AFTER READING CITED PAPER: "
            "within range / model over-predicts / model under-predicts / "
            "different metric — direct comparison not possible]"
        )
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "table_s5_lit_benchmarks.csv", index=False)

    readme = [
        "# Task 6 — Supplementary Table S5 template",
        "",
        "`table_s5_lit_benchmarks.csv` contains the modelled single-crisis impacts",
        "at Optimistic / Moderate / Pessimistic severity for each of the four events",
        "cited in the manuscript. The `published_impact` and `match_category` columns",
        "are LEFT BLANK and must be filled by a co-author reading the primary",
        "sources. Do NOT estimate or paraphrase from memory — extract the",
        "quantitative figure verbatim and cite with page number.",
        "",
        "Per MANUSCRIPT_CORRECTIONS.md standing guidance (no invented numbers,",
        "solid references only), this script does not attempt to fill these cells.",
        "",
        "Instructions for filling the table:",
        "",
        "1. For each event row, locate the primary_citation paper and extract the",
        "   quoted impact figure with units (e.g., '% water supply disrupted', ",
        "   'million people affected', 'MCM/year decline').",
        "2. Align units with the model's modelled_*_supply_reduction_pct column",
        "   where possible. If units don't match, state this explicitly in the",
        "   match_category column.",
        "3. Choose match_category from: 'within range', 'model over-predicts by X%',",
        "   'model under-predicts by X%', or 'outside meaningful comparison — Y'.",
        "",
        "4. Where secondary_citation is non-empty, use it as a cross-check.",
        "",
        "Modelled numbers are reproducible by re-running `scripts/task6_lit_benchmark.py`.",
    ]
    (OUTPUT_DIR / "README.md").write_text("\n".join(readme) + "\n")
    print("Task 6 template generated at:")
    print(f"  {OUTPUT_DIR / 'table_s5_lit_benchmarks.csv'}")
    print(f"  {OUTPUT_DIR / 'README.md'}")
    print("\nUser action required: fill 'published_impact' and 'match_category' cells")
    print("from the primary citations. No estimation.")


if __name__ == "__main__":
    main()
