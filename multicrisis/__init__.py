"""Multicrisis compound water-system vulnerability model.

Clean, reproducible implementation extracted from baseline_converted.py.py for
the Earth's Future revision. Adds γ interaction multipliers and Monte Carlo
sensitivity that were absent from the original notebook code.
"""

from multicrisis.config import RANDOM_SEED, GAMMA_CENTRAL, GAMMA_RANGES, INTERACTION_PAIRS

__all__ = ["RANDOM_SEED", "GAMMA_CENTRAL", "GAMMA_RANGES", "INTERACTION_PAIRS"]
