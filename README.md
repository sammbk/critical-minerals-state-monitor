# Critical Minerals State Monitor

When world prices for critical minerals move, the effects reach U.S. states through two
channels: the states that mine and process those minerals, and the industries that use
them. The Critical Minerals State Monitor measures each state's exposure on both sides, in
dollars and as a share of state GDP, for all fifty states and the District of Columbia. It
is built entirely from public federal and World Bank data, with open code.

**Site:** https://sammbk.github.io/critical-minerals-state-monitor/

**Status: release 1.0 (2026-11-18).** Research tool, not an official statistic.

## Release 1.0

| | |
|---|---|
| States | 50 states plus DC |
| Minerals | Aluminum, copper, lead, nickel, tin, zinc (all on the final 2025 U.S. List of Critical Minerals; free monthly World Bank prices) |
| Producer exposure | Value of mine output at the latest 12-month average world price, from USGS state and mine data where published. Figures USGS withholds are excluded, never imputed. |
| User exposure | 2024 U.S. apparent consumption (USGS) at the current price, allocated across states by BEA 2017 input-output purchases per dollar of output and state real output by industry |
| Net effect | One tenth of producer minus user value, as a percent of state GDP: a first-round accounting measure of a 10% price rise |
| Views | National overview (map, rankings, the six metals at a glance) and a profile for every state |

Known limits of this release: USGS publishes state production for few metals and states;
BEA groups nickel, lead, zinc and tin into one industry, so they share one state
allocation; primary aluminum output by state is not yet compiled. Full method notes are in
the docstring of `code/05_minerals.py` and on the site.

Next: potash and phosphate rock (fertilizer channel), primary aluminum by state, local
projection estimates of price pass-through, and a price floor and stockpile scenario tool.

## Reproduce

Python 3.11+ with `pandas`, `numpy`, `requests`, `openpyxl`, `xlrd`, `matplotlib`; a TeX
distribution with `latexmk` for the methods note.

```
python code/01_fetch.py            # public inputs -> data/raw/ (no API keys)
python code/05_minerals.py         # critical minerals -> data/clean/minerals_*
python code/06_build_monitor.py    # -> dashboard/monitor/ (the published site)
```

Scripts `02` to `04`, `dashboard/` outside `monitor/`, and `docs/` hold earlier
development work on energy and agricultural prices (October 2026); they are not part of
the published site.

A few USGS files must be saved by hand into `data/raw/usgs/` because the USGS site does not
serve them to scripts: `myb1-2021-nickel.xlsx` and the Mineral Commodity Summaries 2026
PDFs for aluminum, copper, lead, nickel, tin and zinc (`mcs2026-<metal>.pdf`).
`data/raw/CHECKSUMS.sha256` records the inputs used; a mismatch after re-fetching means a
provider revised a series.

## Layout

```
code/               fetch and build scripts
data/raw/           downloaded inputs (not tracked)
data/clean/         outputs (tracked)
dashboard/monitor/  the published site (built by code/06_build_monitor.py)
dashboard/, docs/   earlier energy and agriculture work (not published)
```

## Sources

- U.S. Geological Survey: Minerals Yearbook (copper, zinc, tin 2022; nickel 2021); Mineral
  Commodity Summaries 2026.
- U.S. Bureau of Economic Analysis: 2017 input-output Use table (detail, before
  redefinitions); GDP and real value added by state and industry (SAGDP2, SAGDP9).
- World Bank: Commodity Price Data (Pink Sheet), monthly.

## Citation and license

Cite as: Samson M'boueke, *Critical Minerals State Monitor*, release 1.0, November 18, 2026,
https://sammbk.github.io/critical-minerals-state-monitor/ (see `CITATION.cff`).

Code is released under the MIT License (`LICENSE`). Input data are from the public sources
above and remain subject to their providers' terms.
