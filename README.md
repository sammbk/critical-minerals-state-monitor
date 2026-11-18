# State Shock Ledger

When world prices for oil, natural gas, grain, or cattle move, income moves between U.S.
states. The State Shock Ledger measures each state's gain or loss from those price
movements, in dollars and as a share of state GDP, and projects the energy windfall forward
using EIA's price outlook. It is built entirely from public federal and World Bank data.

**Status: prototype v0 (2026-10-08).** Research prototype, not an official statistic.

## What v0 covers

| | |
|---|---|
| States | 50 states plus DC; federal offshore production reported separately |
| Commodities | Crude oil, natural gas (both sides of the market); corn, soybeans, wheat, cattle (producer side) |
| History | Monthly, 2000-01 to the latest World Bank month |
| Nowcast | Daily for energy (EIA spot prices) |
| Outlook | Energy windfall implied by the latest EIA Short-Term Energy Outlook |
| Views | Latest, history, and a price scenario (oil and gas sliders) |

**Release 1.0 of the Critical Minerals State Monitor (2026-11-18)** adds a critical minerals
layer for six metals with free World Bank monthly prices (aluminum, copper, lead, nickel, tin,
zinc): each state's exposure as a producer (USGS mine output where published; withheld
figures are excluded, never imputed) and as a user (2024 U.S. apparent consumption allocated
across states with BEA 2017 input-output purchases and state real industry output). Build it
with `python code/05_minerals.py` and `python code/06_build_monitor.py`; the page is
`dashboard/monitor/index.html`. Method notes are in the docstring of `code/05_minerals.py`.

Next: potash and phosphate rock (fertilizer channel), primary aluminum output by state,
Local Projections of pass-through, and a price floor and stockpile scenario tool.

## Method

See the methods note, [docs/methods.pdf](docs/methods.pdf) (source: `docs/methods.tex`).
In one line: a state's windfall is its net position in each commodity (production minus
consumption, averaged over the three prior years) times the twelve-month change in the
world price, summed over commodities.

## Reproduce

Python 3.11+ with `pandas`, `numpy`, `requests`, `openpyxl`, `xlrd`, `matplotlib`; a TeX
distribution with `latexmk` for the methods note.

```
python code/01_fetch.py            # public inputs -> data/raw/ (no API keys)
python code/02_build_ledger.py     # -> data/clean/*.csv
python code/03_build_dashboard.py  # -> dashboard/index.html
python code/04_figures.py          # -> docs/fig_states.pdf; then latexmk -pdf docs/methods.tex
```

`data/raw/CHECKSUMS.sha256` records the inputs used; a mismatch after re-fetching means a
provider revised a series.

## Layout

```
code/        fetch, build, and dashboard scripts
data/raw/    downloaded inputs (not tracked)
data/clean/  ledger outputs (tracked)
dashboard/   template.html (source), index.html (standalone build), fragment.html
docs/        methods note (LaTeX source and PDF) and its figure
```

## Sources

- U.S. Energy Information Administration: State Energy Data System; daily WTI and Henry
  Hub spot prices; Short-Term Energy Outlook; NYMEX futures (through 2024-04-05, for
  backtesting).
- USDA Economic Research Service: Farm Income and Wealth Statistics (cash receipts by
  state and commodity).
- World Bank: Commodity Price Data (Pink Sheet), monthly.
- U.S. Bureau of Economic Analysis: GDP by state (SAGDP).

Author: Samson M'boueke.
