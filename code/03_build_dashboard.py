"""Package data/clean/ into the dashboard.

Writes two files from dashboard/template.html:
    dashboard/index.html     standalone page for static hosting
    dashboard/fragment.html  the same page without the document skeleton, for hosts
                             that supply their own (for embedding in another page)

    python code/03_build_dashboard.py
"""

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
DASH = ROOT / "dashboard"

ENERGY = ["crude_oil", "natural_gas"]
AG = ["corn", "soybeans", "wheat", "cattle"]
NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
    "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
    "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "X3": "Federal offshore, Gulf of America", "X5": "Federal offshore, Pacific",
}


def r(x, nd):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), nd)


def main() -> None:
    m = pd.read_csv(CLEAN / "ledger_monthly.csv")
    t = pd.read_csv(CLEAN / "ledger_today.csv")
    o = pd.read_csv(CLEAN / "ledger_outlook.csv")
    pos = pd.read_csv(CLEAN / "positions.csv")

    months = pd.period_range(m["month"].min(), m["month"].max(), freq="M").astype(str).tolist()
    last_month = months[-1]
    asof = t["asof"].iloc[0]
    year = int(asof[:4])

    # GDP implied by the build (windfall / share), latest year used.
    g = t.dropna(subset=["gdp"]).groupby("state")["gdp"].first()

    hist = {}
    for (s, c), d in m.groupby(["state", "commodity"]):
        d = d.set_index("month").reindex(months)
        hist.setdefault(s, {})[c] = {
            "u": [r(v / 1e6, 1) for v in d["windfall_usd"]],
            "p": [r(v, 4) for v in d["windfall_pct_gdp"]],
        }

    latest = {}
    for _, row in t.iterrows():
        latest.setdefault(row.state, {})[row.commodity] = [
            r(row.windfall_usd / 1e6, 1), r(row.windfall_pct_gdp, 4)]
    lm = m[(m["month"] == last_month) & (m["commodity"].isin(AG))]
    for _, row in lm.iterrows():
        latest.setdefault(row.state, {})[row.commodity] = [
            r(row.windfall_usd / 1e6, 1), r(row.windfall_pct_gdp, 4)]

    out_months = sorted(o["month"].unique())
    oe = o.groupby(["state", "month"])[["windfall_usd", "windfall_pct_gdp"]].sum(min_count=1)
    outlook = {"months": out_months, "steo": {}}
    for c in ENERGY:
        outlook["steo"][c] = [r(v, 3) for v in
                              o[o["commodity"] == c].groupby("month")["steo_price"].first()
                              .reindex(out_months)]
    for s in oe.index.get_level_values(0).unique():
        d = oe.loc[s].reindex(out_months)
        outlook[s] = {"u": [r(v / 1e6, 1) for v in d["windfall_usd"]],
                      "p": [r(v, 4) for v in d["windfall_pct_gdp"]]}

    p_now = pos[pos["weight_year"] == year]
    positions = {}
    for _, row in p_now.iterrows():
        positions.setdefault(row.state, {})[row.commodity] = [r(row.net_qty, 0),
                                                              row.weight_window]

    prices = t.groupby("commodity")[["price_now", "price_year_ago"]].first()
    base = o.groupby("commodity")["base_price"].first()

    data = {
        "meta": {"asof": asof, "lastMonth": last_month, "firstMonth": months[0],
                 "steo": o["steo_vintage"].iloc[0], "built": date.today().isoformat()},
        "months": months,
        "energy": ENERGY, "ag": AG,
        "names": NAMES,
        "gdp": {s: r(v, -6) for s, v in g.items()},
        "spot": {c: r(prices.loc[c, "price_now"], 3) for c in ENERGY},
        "yearAgo": {c: r(prices.loc[c, "price_year_ago"], 3) for c in ENERGY},
        "base": {c: r(base[c], 3) for c in ENERGY},
        "positions": positions,
        "latest": latest,
        "hist": hist,
        "outlook": outlook,
    }
    blob = json.dumps(data, separators=(",", ":"), allow_nan=False)

    tpl = (DASH / "template.html").read_text(encoding="utf-8")
    page = tpl.replace("/*__DATA__*/null", blob)
    (DASH / "fragment.html").write_text(page, encoding="utf-8")
    (DASH / "index.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, '
        'viewport-fit=cover">\n</head>\n<body>\n' + page + "\n</body>\n</html>\n",
        encoding="utf-8")
    print(f"dashboard written: {len(page) / 1e6:.2f} MB, months {months[0]}..{last_month}, "
          f"daily as of {asof}")


if __name__ == "__main__":
    main()
