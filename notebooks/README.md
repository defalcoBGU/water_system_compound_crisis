# notebooks/

## `baseline_processing_ORIGINAL.ipynb`

This is the original Jupyter notebook used to produce `data/baseline_data_processed.csv` from the raw Israel Water Authority annual balance and the calibration/expansion CSVs in `data/intermediate/`. It is included here as the **audit trail** for the baseline-processing pipeline.

### Scope

The notebook contains many more cells than are strictly needed for the published baseline. It originated as a working notebook for the project and includes (in addition to baseline processing):

- Forward projection of supply and demand 2025–2050
- Trend and variability analysis on the historical record
- An earlier (pre-revision) version of the compound-crisis analysis with hard-coded parameter values

**Only the baseline-processing cells are authoritative for this manuscript revision.** The cells implementing crisis impact functions and compound scenario analysis are **superseded by `multicrisis/`** and should not be used to reproduce the published headline numbers; instead use the modular package in `multicrisis/` and the orchestration scripts in `scripts/`.

### How to identify the baseline-processing cells

The cells that produce `data/baseline_data_processed.csv` are characterised by:
- Loading `data/raw/dataset_25.09.25.xlsx` (or its CSV variant)
- Loading the calibration/expansion CSVs from `data/intermediate/`
- Column harmonisation (renaming raw header strings to canonical names)
- Forward projection using the adaptation-trigger rules
- Writing the integrated dataframe to `data/baseline_data_processed.csv`

A guided reading order: see `data/intermediate/baseline_methodology.md`, which documents the processing steps and the cells that implement each one.

### Why this is a notebook and not a script

The forward-projection logic involves several iterative steps (calibration, expansion, derived-indicator recomputation) that were developed incrementally during the original modelling pass. Re-engineering this into a clean Python module is on the project's future-work list but is out of scope for the current manuscript revision. The framework code in `multicrisis/` does not depend on this notebook — `baseline_data_processed.csv` is the single point of contact between the upstream processing and the downstream analysis.

### Running the notebook

The notebook was developed under Python 3.12.11 with the dependencies pinned in `../requirements.txt`. To run interactively:

```bash
pip install jupyter
cd notebooks/
jupyter notebook baseline_processing_ORIGINAL.ipynb
```

Note: the notebook references file paths relative to its original execution directory (the root of `multicrisis_year1/`). To re-run from this `notebooks/` location, paths like `"dataset_25.09.25.xlsx"` need to be edited to `"../data/raw/dataset_25.09.25.xlsx"`. This re-rooting is not strictly necessary for journal reproducibility — the audit trail is complete because `baseline_data_processed.csv` is provided as the final output of this processing — but is documented here for completeness.
