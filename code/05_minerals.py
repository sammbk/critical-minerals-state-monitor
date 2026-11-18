"""Build the critical minerals layer: producer and user exposure by state.

Release 1.0 covers six metals with free monthly World Bank prices: aluminum, copper,
lead, nickel, tin and zinc. Potash and phosphate rock reach users mainly through
fertilizer and are added in the next release.

Producer exposure (value of mine output at current prices), from USGS, never imputed:
    copper   mine-level output of the leading mines (USGS Minerals Yearbook 2022,
             table 2), summed by state; the unlisted remainder stays national only
    zinc     Alaska (yearbook table 2); other producing states withheld by USGS
    nickel   Michigan: the Eagle mine is the only U.S. nickel mine, so the national
             mine figure for 2024 (Mineral Commodity Summaries 2026) is Michigan's
    lead     producing states known (MO, AK, ID), values withheld by USGS
    tin      no U.S. mine production
    aluminum primary smelter output by state not compiled in this release

User exposure (metal used by industries outside the mineral chain, at current prices):
    level    U.S. apparent consumption in 2024 (USGS Mineral Commodity Summaries 2026)
             times the latest 12-month average world price. BEA purchase values are
             not used for the level, because they include fabrication margins and, for
             nonferrous refining, precious metals.
    a[g, L]  2017 purchases of commodity group g per dollar of output in industry L,
             from the BEA 2017 detail Use table (before redefinitions, producers'
             prices), aggregated to BEA state GDP industry lines
    X[L, s]  state real output: real value added (chained 2017 dollars, SAGDP9),
             times the national 2017 output-to-value-added ratio of line L
    U[m, s]  = C[m] * P[m, now] * w[g(m), s] / sum_s w[g(m), s],
             w[g, s] = sum_L a[g, L] * X[L, s]
    groups   aluminum: 331313 + 33131B; copper: 331420 (refined copper is bought
             mostly by wire-rod and brass mills, which are in the chain); nickel,
             lead, zinc, tin: 212230 + 331410, which BEA does not split by metal, so
             the four share one state allocation in this release

The effect of a 10% world price rise is 0.1 * (producer - user), as a share of state
GDP. Outputs: data/clean/minerals_state.csv and data/clean/minerals_meta.json.

    python code/05_minerals.py
"""

import io
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"

STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL",
          "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE",
          "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD",
          "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
FIPS = dict(zip(["01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16",
                 "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
                 "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42",
                 "44", "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56", "00"],
                STATES + ["US"]))
MINERALS = ["aluminum", "copper", "lead", "nickel", "tin", "zinc"]
PINK = {"aluminum": "Aluminum", "copper": "Copper", "lead": "Lead", "nickel": "Nickel",
        "tin": "Tin", "zinc": "Zinc"}                      # all $/metric ton
GROUPS = {"aluminum": ["331313", "33131B"], "copper": ["331420"],
          "npzt": ["212230", "331410"]}                   # nickel, lead, zinc, tin
CHAIN = {"212230", "331410", "331420", "331313", "33131B"}
# BEA state GDP industry lines that partition the economy (government excluded).
LEAVES = [4, 5, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29,
          30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 52, 53, 54,
          55, 57, 58, 61, 62, 63, 64, 66, 67, 69, 71, 72, 73, 74, 77, 78, 80, 81, 82]
# U.S. apparent consumption in 2024, metric tons of metal content (USGS Mineral Commodity
# Summaries 2026, salient statistics; files in data/raw/usgs/). Nickel is apparent primary
# plus reported purchased scrap; copper is primary refined plus old scrap.
CONSUMPTION_2024 = {"aluminum": 5_830_000, "copper": 1_860_000, "lead": 1_410_000,
                    "nickel": 90_300 + 121_000, "tin": 34_600, "zinc": 808_000}
NICKEL_MINE_2024 = 7_490
# Producing states whose values USGS withholds (copper: yearbook 2022 text; zinc: table 3;
# lead: MCS 2026).
WITHHELD = {"copper": ["MT", "MO"], "zinc": ["ID", "MO", "NY", "TN"],
            "lead": ["MO", "AK", "ID"]}


# ---------------------------------------------------------------- prices

def prices() -> pd.DataFrame:
    """Monthly World Bank prices of the six metals, in dollars per metric ton."""
    d = pd.read_excel(RAW / "worldbank" / "CMO-Historical-Data-Monthly.xlsx",
                      sheet_name="Monthly Prices", header=4)
    d = d.rename(columns={d.columns[0]: "month"})
    d = d[d["month"].astype(str).str.match(r"^\d{4}M\d{2}$")]
    out = pd.DataFrame(index=pd.PeriodIndex(d["month"].str.replace("M", "-"), freq="M"))
    for m, col in PINK.items():
        out[m] = pd.to_numeric(d[col].values, errors="coerce")
    return out.dropna(how="all")


# ---------------------------------------------------------------- BEA

def sagdp(table: str) -> pd.DataFrame:
    """One BEA state GDP table (SAGDP2 or SAGDP9) for all states, with state codes."""
    with zipfile.ZipFile(RAW / "bea" / "SAGDP.zip") as z:
        name = [n for n in z.namelist() if n.startswith(f"{table}__ALL_AREAS")][0]
        d = pd.read_csv(z.open(name), encoding="latin1", low_memory=False)
    d = d.dropna(subset=["LineCode"])
    d["state"] = d["GeoFIPS"].astype(str).str.strip().str.strip('"').str[:2].map(FIPS)
    return d.dropna(subset=["state"])


def expand(spec: str) -> list[str]:
    """Expand a BEA NAICS specification such as '3361-3363, 3364' into a list of codes."""
    spec = spec.replace("3364-3466", "3364-3366")          # typo in the BEA file
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out += [str(i) for i in range(int(a), int(b) + 1)]
        elif part.isdigit():
            out.append(part)
    return out


def leaf_map(g2: pd.DataFrame) -> dict[str, int]:
    """Map NAICS prefixes to the state GDP industry lines that partition the economy."""
    lines = g2[g2["LineCode"].isin(LEAVES)][["LineCode", "IndustryClassification"]]
    pref = {}
    for _, r in lines.drop_duplicates("LineCode").iterrows():
        for p in expand(str(r["IndustryClassification"])):
            pref[p] = int(r["LineCode"])
    return pref


def match(code: str, pref: dict[str, int]):
    """State GDP line for an input-output industry code, by its longest matching NAICS prefix."""
    for k in range(6, 1, -1):
        if code[:k] in pref:
            return pref[code[:k]]
    return None


def use_table() -> tuple[pd.DataFrame, pd.Series]:
    """BEA 2017 detail Use table (industries only) and total industry output."""
    with zipfile.ZipFile(RAW / "bea" / "AllTablesIO.zip") as z:
        b = z.read("IOUse_Before_Redefinitions_PRO_2017_Detail.xlsx")
    d = pd.read_excel(io.BytesIO(b), sheet_name="2017", header=None)
    cols = d.iloc[5, 2:].astype(str).tolist()
    body = d.iloc[6:, :]
    body.index = body.iloc[:, 0].astype(str).str.strip()
    body = body.iloc[:, 2:]
    body.columns = cols
    body = body.iloc[:, :cols.index("T001")]          # industries only; final demand dropped
    body = body.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return body, body.loc["T008"]


# ---------------------------------------------------------------- build

def build() -> None:
    """Build producer and user exposure by state and metal and write the outputs to data/clean/."""
    CLEAN.mkdir(parents=True, exist_ok=True)
    p = prices()
    last = p["copper"].dropna().index.max()
    p_now = p.loc[last - 11: last].mean()
    p_prev = p.loc[last - 23: last - 12].mean()

    group_of = {"aluminum": "aluminum", "copper": "copper", "nickel": "npzt", "lead": "npzt",
                "zinc": "npzt", "tin": "npzt"}

    # Direct purchase coefficients by state GDP industry line.
    use, output = use_table()
    g2, g9 = sagdp("SAGDP2"), sagdp("SAGDP9")
    pref = leaf_map(g2)
    line_of = {c: match(c, pref) for c in use.columns}
    dropped = {}
    purch = {}
    for g, rows in GROUPS.items():
        row = use.loc[rows].sum()
        row = row[[c for c in row.index if c not in CHAIN]]
        unmatched = [c for c in row.index if line_of.get(c) is None]
        dropped[g] = float(row[unmatched].sum() / row.sum())
        purch[g] = row.groupby(pd.Series({c: line_of.get(c) for c in row.index})).sum()
    out_line = output.groupby(pd.Series(line_of)).sum()
    us = g2[(g2["state"] == "US") & g2["LineCode"].isin(LEAVES)].set_index("LineCode")
    va17 = pd.to_numeric(us["2017"], errors="coerce")
    ratio = (out_line / va17).replace([np.inf, -np.inf], np.nan)

    years = [c for c in g9.columns if str(c).isdigit()]
    real = g9[g9["LineCode"].isin(LEAVES)].copy()
    vals = real[years].apply(pd.to_numeric, errors="coerce")
    year = max(y for y in years if vals[y].notna().mean() > 0.9)
    real["rva"] = vals[year]
    suppressed = int(real["rva"].isna().sum())
    real = real[real["state"].isin(STATES)]
    real["X"] = real["rva"].fillna(0.0) * real["LineCode"].map(ratio).fillna(0.0)
    X = real.pivot_table(index="state", columns="LineCode", values="X", aggfunc="sum").fillna(0.0)

    gdp = g2[(g2["LineCode"] == 1) & g2["state"].isin(STATES)].set_index("state")
    gdp = pd.to_numeric(gdp[year], errors="coerce") * 1e6

    rows, ind_rows = [], []
    for m in MINERALS:
        g = group_of[m]
        a = (purch[g] / out_line).reindex(X.columns).fillna(0.0)
        w = (X * a).sum(axis=1)
        user = CONSUMPTION_2024[m] * p_now[m] * w / w.sum()
        contrib = (X * a) * (CONSUMPTION_2024[m] * p_now[m] / w.sum())
        ind_rows.append(contrib.stack().rename("user_usd").reset_index().assign(mineral=m))
        for s in STATES:
            rows.append({"state": s, "mineral": m, "user_usd": float(user.get(s, 0.0))})
    df = pd.DataFrame(rows)
    names = g2.drop_duplicates("LineCode").set_index("LineCode")["Description"].str.strip()
    ind = pd.concat(ind_rows)
    ind = ind[ind["user_usd"] > 0]
    ind["industry"] = ind["LineCode"].map(names)
    ind[["state", "mineral", "LineCode", "industry", "user_usd"]].to_csv(
        CLEAN / "minerals_state_industry.csv", index=False, float_format="%.6g")

    # Producer side.
    prod = pd.Series(0.0, index=pd.MultiIndex.from_product([STATES, MINERALS]))
    status = pd.Series("none", index=prod.index)
    t2 = pd.read_excel(RAW / "usgs" / "myb1-2022-copper.xlsx", sheet_name="T2", header=None)
    for _, r in t2.iloc[7:].iterrows():
        loc = str(r.iloc[4])
        st = re.search(r",\s*([A-Z]{2})\s*$", loc)
        q = pd.to_numeric(r.iloc[12], errors="coerce")
        if st and pd.notna(q):
            prod[(st.group(1), "copper")] += q * p_now["copper"]
            status[(st.group(1), "copper")] = "reported"
    zt = pd.read_excel(RAW / "usgs" / "myb1-2022-zinc.xlsx", sheet_name="T2", header=None)
    ak = float(zt[zt.iloc[:, 0].astype(str).str.strip() == "Alaska"].iloc[0, 4])
    prod[("AK", "zinc")] = ak * p_now["zinc"]
    status[("AK", "zinc")] = "reported"
    prod[("MI", "nickel")] = NICKEL_MINE_2024 * p_now["nickel"]
    status[("MI", "nickel")] = "reported"
    for m, sts in WITHHELD.items():
        for s in sts:
            if status[(s, m)] == "none":
                status[(s, m)] = "withheld"
    for s in STATES:
        status[(s, "aluminum")] = "not compiled"

    df["producer_usd"] = [prod[(s, m)] for s, m in zip(df["state"], df["mineral"])]
    df["producer_status"] = [status[(s, m)] for s, m in zip(df["state"], df["mineral"])]
    df["gdp_usd"] = df["state"].map(gdp)
    for k in ["producer", "user"]:
        df[f"{k}_pct_gdp"] = 100 * df[f"{k}_usd"] / df["gdp_usd"]
    df["net_10pct_pct_gdp"] = 0.1 * (df["producer_pct_gdp"] - df["user_pct_gdp"])
    df.to_csv(CLEAN / "minerals_state.csv", index=False, float_format="%.6g")

    meta = {
        "prices_through": str(last), "gdp_year": int(year),
        "price_now_12m_avg": {m: round(float(p_now[m]), 1) for m in MINERALS},
        "price_change_12m_pct": {m: round(float(100 * (p_now[m] / p_prev[m] - 1)), 1)
                                 for m in MINERALS},
        "purchases_outside_matched_lines_share": {g: round(v, 4) for g, v in dropped.items()},
        "state_industry_cells_suppressed": suppressed,
        "national_user_usd": {m: float(df[df.mineral == m]["user_usd"].sum()) for m in MINERALS},
        "national_producer_reported_usd": {m: float(df[df.mineral == m]["producer_usd"].sum())
                                           for m in MINERALS},
    }
    (CLEAN / "minerals_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ["prices_through", "gdp_year",
                                           "purchases_outside_matched_lines_share",
                                           "state_industry_cells_suppressed"]}, indent=1))


if __name__ == "__main__":
    build()
