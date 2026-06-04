# Water System Compound Crisis Framework

This repository contains the code, input data, and analysis scripts used in the study:

**Bot, K., De Falco, N., Renn, J., and Weisbrod, N.**

*Compound Security–Climate Vulnerability of a Desalination-Dependent Water System: Scenario Analysis for Israel.*

Submitted to *Water Resources Research* (2026).

## Repository contents

The repository includes:

* Input datasets and parameter files used in the analysis (`data/`)
* Core modeling framework for compound crisis simulation (`multicrisis/`)
* Analysis scripts used to generate manuscript results (`scripts/`)
* Supporting notebooks (`notebooks/`)
* Reproducibility outputs and benchmark results (`results/`)

## Reproducing the analysis

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Run the complete analysis workflow:

```bash
bash run_all.sh
```

The workflow reproduces the scenario analysis, sensitivity analyses, uncertainty assessment, and supporting figures reported in the manuscript.

## Data availability

This repository contains the data, code, and scripts required to reproduce the analyses presented in the manuscript. The repository is provided for transparency and reproducibility during peer review and will be archived with a permanent DOI upon publication.

## License

MIT License.

## Contact

Natalie De Falco
Zuckerberg Institute for Water Research
Ben-Gurion University of the Negev
[defalco@bgu.ac.il](mailto:defalco@bgu.ac.il)


## What's in the box

```
multicrisis_framework/
├── README.md                       # this file
├── LICENSE                         # MIT
├── requirements.txt                # pinned Python dependencies
├── pyproject.toml                  # PEP 621 metadata
├── package.json                    # node deps for build_supplementary.js
├── run_all.sh                      # one-command pipeline runner
│
├── multicrisis/                    # core Python package
│   ├── __init__.py
│   ├── config.py                   # constants, γ values, seed, paths
│   ├── crises.py                   # 4 single-crisis impact functions
│   ├── compound.py                 # 243-scenario enumeration + sequencing
│   ├── gamma.py                    # γ amplification layer
│   ├── montecarlo.py               # ±25 % MC + tiered γ sampler
│   └── metrics.py                  # supply-reduction CI, R², top-15
│
├── scripts/                        # runnable analyses
│   ├── task0_sanity_check.py       # Tier 1 reproduction vs archived run
│   ├── task1_retrospective.py      # 2013–2016 Levant grounding
│   ├── task2_run_tiers.py          # full 500-draw × 3-tier sweep
│   ├── task2_smoke_test.py         # 10-draw shape/invariant check
│   ├── task3_wsi_convention.py     # WSI accounting-convention robustness
│   ├── task4_elasticity.py         # demand elasticity ±50 % sensitivity
│   ├── task5_threshold.py          # response-threshold ±20 % sensitivity
│   ├── task6_lit_benchmark.py      # literature impact comparison
│   ├── supp_figure_s1.py           # supplementary Top-15 figure
│   └── build_supplementary.js      # docx-js Supplementary builder
│
├── data/                           # input data (see Data sources below)
│   ├── baseline_data_processed.csv # Israel Water Authority 1990–2050
│   ├── drought_params.csv          # severity parameters per Supp Table S3
│   ├── energy_params.csv
│   ├── conflict_params.csv
│   ├── cyber_params.csv
│   └── compound_crisis_impact_summary.csv  # archived Tier 1 reference (task0)
│
├── docs/                           # manuscript + revision documentation
│   ├── multicrisis_manuscript_FINAL.docx
│   ├── multicrisis_supplementary_FINAL.docx
│   ├── MANUSCRIPT_CORRECTIONS.md   # 15 numbered corrections (C1–C15)
│   ├── FINAL_FILL_IN.md            # placeholder → computed-value map
│   ├── COWORK_HANDOVER.md          # remaining manual editorial tasks
│   ├── FIGURE_INSERTION_GUIDE.md   # caption text + file paths for new figures
│   └── MANIFEST.md                 # full inventory of revision outputs
│
└── results/                        # populated by running the scripts (gitignored)
```

## Quick start

Requires Python 3.11+ (tested on 3.12.11) and Node.js 18+ (only if you want to rebuild the Supplementary docx).

```bash
# 1. Create + activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Verify the install with the bit-exact Tier 1 reproduction test
python scripts/task0_sanity_check.py

# Expected output (last line):
#   [PASS] Clean extraction reproduces the archive to within 1e-6.

# 4. Run the full pipeline (~12 minutes on a modern laptop)
bash run_all.sh
```

Outputs land in `results/` — one subdirectory per task plus `supp_figures/` for the regenerated Supplementary Figure S1.

## Reproducing the manuscript headline numbers

After running `bash run_all.sh`, the headline numbers in `multicrisis_manuscript_FINAL.docx` correspond to fields in:

| Section | Number | Source file |
|---|---|---|
| Abstract / §3.5 | Tier 3 worst-case 88.62 % (95 % CI 84.70–92.04) | `results/task2/scalars.json` → `T3_POINT_ESTIMATE`, `T3_CI_LO`, `T3_CI_HI` |
| §3.3 | R² 0.508 (95 % CI 0.416–0.593) | `results/task2/scalars.json` → `T3_R2`, `T3_R2_CI_LO`, `T3_R2_CI_HI` |
| §3.2 | 60 % modelled vs 10.8 % observed, 2013–2016 | `results/task1/scalars.json` |
| §2.2 | WSI-convention Spearman ρ = 0.970 | `results/task3/scalars.json` → `RHO` |

The full per-tier scenario CSVs live in `results/task2/{tier1,tier2,tier3}_per_draw.csv` (large) and `results/task2/{tier1,tier2,tier3}_scenario_results.csv` (per-scenario summaries).

## How to adapt to a different system

The framework is designed for re-parameterisation, not direct transfer. To apply to another water system:

1. **Replace `data/baseline_data_processed.csv`** with a 60-year annual balance for your system. The required columns are: `year`, `water_desalination_mcm`, `capped_groundwater`, `produced_by_kinneret_milion_m3`, `capped_reuse`, `total_produced_by_upper_water_milion_m3`, `total_demand`, plus the per-sector demand columns referenced in `multicrisis/crises.py` if you want demand-side effects under conflict scenarios.

2. **Edit the four `data/*_params.csv` files** to reflect system-specific severity parameters. Justify each value with a literature source (see Supp Table S3 of the manuscript for the Israel-specific anchors).

3. **Edit `multicrisis/config.py`** if you need to override γ central values, sampling ranges, the random seed, the Monte Carlo draw count, or the crisis-year window.

4. **Re-run `bash run_all.sh`** — all results regenerate from the new inputs.

## Data sources

The Israel baseline is the [Israel Water Authority annual balance](https://www.gov.il/en/departments/water_authority) 1990–2023, projected to 2050 by the original notebook in `multicrisis_year1/baseline.ipynb` (not included here; the processed output is what this framework consumes).

The γ multipliers and severity parameters come from the manuscript's reference list. See `docs/MANUSCRIPT_CORRECTIONS.md` entries C1, C9, and C10 for the mathematical convention and parameter provenance.

## Reproducibility guarantees

- **Random seed**: `multicrisis/config.RANDOM_SEED = 20260423`. Set once, threaded through every `np.random.default_rng()` instance. Same seed across all tiers per draw, so tier comparisons are paired.
- **No invented numbers**: every parameter in `data/*.csv` and `multicrisis/config.py` is traceable to a literature source documented in the manuscript or supplementary materials.
- **Bit-exact Tier 1 reproduction**: `scripts/task0_sanity_check.py` confirms the Tier 1 (additive-only) sweep matches the archived `data/compound_crisis_impact_summary.csv` to within 1e-14 (machine epsilon).

## Citing

If you use this framework, please cite the manuscript and link to this repository.

## License

MIT. See `LICENSE`.

## Contact

Natalie De Falco — `defalco@bgu.ac.il` (corresponding author)
