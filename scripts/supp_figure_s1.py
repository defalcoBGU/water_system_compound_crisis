"""Generate the updated Supplementary Figure S1: top-15 most severe scenarios at Tier 3."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from multicrisis.config import RESULTS_DIR

TASK2_DIR = RESULTS_DIR / "task2"
OUT_DIR = RESULTS_DIR / "supp_figures"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(TASK2_DIR / "tier3_scenario_results.csv")
    top = df.nlargest(15, "supply_reduction_mean").copy()
    top["short_name"] = top["composition"].apply(lambda c: "+".join(
        f"{t[0].upper()}{s[0]}" for t, s in (p.split(":") for p in c.split("|"))
    ))

    def pes_colour(n: int) -> str:
        return {4: "#d62728", 3: "#ff9f3f", 2: "#ffd166", 1: "#fff1a8", 0: "#fefae0"}.get(n, "#bbbbbb")

    colours = top["pes_count"].map(pes_colour)

    fig, ax = plt.subplots(figsize=(9, 7.5))
    y = range(len(top))
    bars = ax.barh(list(y), top["supply_reduction_mean"], xerr=(
        top["supply_reduction_mean"] - top["supply_reduction_ci_lo"],
        top["supply_reduction_ci_hi"] - top["supply_reduction_mean"],
    ), color=colours, edgecolor="black", linewidth=0.5, capsize=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(top["short_name"], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Supply reduction (%), Tier 3 mean ± 95% CI")
    ax.set_title("Supp Figure S1 — Top 15 most severe compound scenarios (Tier 3, n=500 draws)",
                 fontsize=11, fontweight="bold")
    ax.set_xlim(70, 100)
    ax.grid(axis="x", alpha=0.3)

    for bar, val in zip(bars, top["supply_reduction_mean"]):
        ax.text(float(val) + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}%", va="center", fontsize=8)

    legend_entries = [
        plt.Rectangle((0, 0), 1, 1, color=pes_colour(n), ec="black", lw=0.5, label=lbl)
        for n, lbl in ((4, "4 pessimistic crises"), (3, "3 pessimistic"),
                       (2, "2 pessimistic"), (1, "≤1 pessimistic"))
    ]
    ax.legend(handles=legend_entries, loc="lower right", fontsize=8)

    note = ("Scenario codes: D=Drought, E=Energy, C=Conflict, Y=Cyber; "
            "O=Optimistic, M=Moderate, P=Pessimistic.")
    fig.text(0.5, 0.01, note, ha="center", fontsize=8, style="italic")
    fig.tight_layout(rect=(0, 0.03, 1, 1))

    for ext in ("pdf", "png", "svg"):
        fig.savefig(OUT_DIR / f"figure_s1_top15_scenarios.{ext}",
                    dpi=160, bbox_inches="tight")
    plt.close(fig)

    top[["short_name", "name", "size", "pes_count", "mod_count", "opt_count",
         "gamma_product_mean", "supply_reduction_mean",
         "supply_reduction_ci_lo", "supply_reduction_ci_hi",
         "wsi_increase_mean", "gap_change_mean"]].to_csv(
        OUT_DIR / "table_s4_top15_tier3.csv", index=False)
    print(f"Wrote: figure_s1_top15_scenarios.pdf/png/svg and table_s4_top15_tier3.csv")
    print(f"Top-15 Tier 3 supply reductions: {top['supply_reduction_mean'].min():.2f}% to {top['supply_reduction_mean'].max():.2f}%")


if __name__ == "__main__":
    main()
