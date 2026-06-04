#!/usr/bin/env bash
# Orchestrates the full multicrisis pipeline end-to-end.
# Expected wall-clock: ~12 minutes on a modern laptop, dominated by Task 2.
#
# Usage: bash run_all.sh
#
# All outputs land in results/. Failed tasks abort the pipeline (set -e).

set -euo pipefail

# Run from the directory containing this script so the package-relative paths
# in multicrisis/config.py resolve correctly even if invoked from elsewhere.
cd "$(dirname "$0")"

# Sanity: confirm we're in a venv with the required deps.
python -c "import numpy, pandas, scipy, matplotlib" || {
  echo "ERROR: required packages not installed. Run 'pip install -r requirements.txt' first." >&2
  exit 1
}

mkdir -p results

echo "================================================================"
echo "  Task 0 — bit-exact Tier 1 reproduction check"
echo "================================================================"
python scripts/task0_sanity_check.py

echo
echo "================================================================"
echo "  Task 1 — retrospective grounding against 2013–2016 Levant drought"
echo "================================================================"
python scripts/task1_retrospective.py

echo
echo "================================================================"
echo "  Task 2 — 500-draw, three-tier Monte Carlo over 243 scenarios"
echo "  (this is the long one — expect ~10 minutes)"
echo "================================================================"
python scripts/task2_run_tiers.py

echo
echo "================================================================"
echo "  Task 3 — alternative WSI-convention robustness check"
echo "================================================================"
python scripts/task3_wsi_convention.py

echo
echo "================================================================"
echo "  Task 4 — demand-elasticity ±50 % sensitivity"
echo "================================================================"
python scripts/task4_elasticity.py

echo
echo "================================================================"
echo "  Task 5 — response-threshold ±20 % sensitivity"
echo "================================================================"
python scripts/task5_threshold.py

echo
echo "================================================================"
echo "  Task 6 — literature-impact comparison (modelled side only)"
echo "================================================================"
python scripts/task6_lit_benchmark.py

echo
echo "================================================================"
echo "  Supplementary Figure S1 — Top-15 Tier 3 scenarios"
echo "================================================================"
python scripts/supp_figure_s1.py

echo
echo "All tasks complete. Outputs in results/"
echo "Headline numbers in results/task2/scalars.json"
