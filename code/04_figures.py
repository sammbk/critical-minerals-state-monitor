"""Figures for the methods note.

    python code/04_figures.py   # -> docs/fig_states.pdf
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
DOCS = ROOT / "docs"

STATES = [("ND", "North Dakota"), ("TX", "Texas"), ("IA", "Iowa"), ("CA", "California")]
INK, MUTED, RULE, LINE = "#101418", "#80868c", "#e2e4e6", "#2a78d6"


def main() -> None:
    m = pd.read_csv(CLEAN / "ledger_monthly.csv")
    tot = m.groupby(["state", "month"])["windfall_pct_gdp"].sum().unstack("state")
    tot.index = pd.PeriodIndex(tot.index, freq="M").to_timestamp()

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "axes.edgecolor": RULE, "axes.labelcolor": INK,
                         "xtick.color": MUTED, "ytick.color": MUTED})
    fig, axes = plt.subplots(2, 2, figsize=(6.3, 3.9), sharex=True)
    for ax, (code, name) in zip(axes.flat, STATES):
        s = tot[code]
        ax.axhline(0, color="#c4c8cc", lw=0.8, zorder=1)
        ax.plot(s.index, s.values, color=LINE, lw=1.1, zorder=2)
        ax.set_title(name, loc="left", fontsize=8.5, color=INK, fontweight="bold", pad=4)
        ax.grid(axis="y", color=RULE, lw=0.5)
        ax.tick_params(length=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:+.0f}%" if v else "0%")
        ax.margins(x=0.01)
    fig.supylabel("Windfall, percent of state GDP", fontsize=8, color=MUTED, x=0.01)
    fig.tight_layout(pad=0.6, h_pad=1.0, w_pad=1.2)
    fig.savefig(DOCS / "fig_states.pdf")
    print("wrote docs/fig_states.pdf")


if __name__ == "__main__":
    main()
