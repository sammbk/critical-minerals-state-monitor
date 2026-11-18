"""Build the State Shock Ledger v0 from the raw public inputs.

Definition (docs/methods.md). For state s, commodity c, and month t,

    W[s,c,t] = N[s,c] * (p[c,t] - p[c,t-12])

is the annualized dollar windfall from the price change over the past twelve months, where
N[s,c] is the state's net position in the commodity: production minus consumption for
energy, and the quantity equivalent of cash receipts for agriculture (producer side only in
v0). N uses the average of the three calendar years before t (Gruss and Kebhaj 2019), so the
measure moves with prices, not with the state's own output response. W is reported in
dollars and as a percent of state GDP.

Outputs (data/clean/):
    ledger_monthly.csv    state x commodity x month, 2000-01 onward
    ledger_today.csv      daily energy nowcast at the latest EIA spot date
    ledger_outlook.csv    energy windfall implied by the latest EIA STEO price path
    positions.csv         net positions used for each weight year

    python code/02_build_ledger.py
"""

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
# SEDS federal offshore production areas; they belong to no state and are reported apart.
OFFSHORE = {"X3": "Federal offshore, Gulf of America", "X5": "Federal offshore, Pacific"}

# Pink Sheet column, unit label, and the ERS receipts series for agriculture.
PRICES = {
    "crude_oil": ("Crude oil, WTI", "$/bbl"),
    "natural_gas": ("Natural gas, US", "$/MMBtu"),
    "corn": ("Maize", "$/mt"),
    "soybeans": ("Soybeans", "$/mt"),
    "wheat": ("Wheat, US HRW", "$/mt"),
    "cattle": ("Beef **", "$/kg"),
}
ERS_SERIES = {
    "corn": "Cash receipts value, corn , all",
    "soybeans": "Cash receipts value, soybeans , all",
    "wheat": "Cash receipts value, wheat , all",
    "cattle": "Cash receipts value, cattle and calves , all",
}
START = "2000-01"
WEIGHT_YEARS = 3


# ---------------------------------------------------------------- inputs

def load_prices() -> pd.DataFrame:
    """Monthly nominal prices, one column per commodity, PeriodIndex."""
    d = pd.read_excel(RAW / "worldbank" / "CMO-Historical-Data-Monthly.xlsx",
                      sheet_name="Monthly Prices", header=4)
    d = d.rename(columns={d.columns[0]: "month"})
    d = d[d["month"].astype(str).str.match(r"^\d{4}M\d{2}$")]
    out = pd.DataFrame(index=pd.PeriodIndex(d["month"].str.replace("M", "-"), freq="M"))
    for c, (col, _) in PRICES.items():
        out[c] = pd.to_numeric(d[col].values, errors="coerce")
    return out


def load_energy_positions() -> pd.DataFrame:
    """Annual energy net positions by state from SEDS, in barrels and MMBtu."""
    d = pd.read_csv(RAW / "eia" / "Complete_SEDS.csv",
                    usecols=["MSN", "StateCode", "Year", "Data"])
    need = ["PAPRP", "PATCP", "HLTCP", "PCTCP", "SGICP", "NGMPB", "NGTCB"]
    d = d[d["MSN"].isin(need)].pivot_table(index=["StateCode", "Year"], columns="MSN",
                                          values="Data", aggfunc="sum").fillna(0.0)
    out = pd.DataFrame(index=d.index)
    # Crude production vs crude-priced petroleum consumption, thousand barrels -> barrels.
    # Hydrocarbon gas liquids (priced off natural gas and petrochemical markets), petroleum
    # coke, and refinery still gas (refinery-internal fuels whose cost is passed on to
    # product buyers) are excluded. Consumers pay roughly the crude price change per barrel
    # of product (docs/methods.md).
    oil_use = d["PATCP"] - d["HLTCP"] - d["PCTCP"] - d["SGICP"]
    out["crude_oil"] = (d["PAPRP"] - oil_use) * 1e3
    # Marketed gas production vs total gas consumption, billion Btu -> MMBtu.
    out["natural_gas"] = (d["NGMPB"] - d["NGTCB"]) * 1e3
    out = out.reset_index().melt(id_vars=["StateCode", "Year"], var_name="commodity",
                                 value_name="net_qty")
    return out.rename(columns={"StateCode": "state", "Year": "year"})


def load_ag_receipts() -> pd.DataFrame:
    """Annual cash receipts by state and commodity, dollars."""
    with zipfile.ZipFile(RAW / "ers" / "farm_income_2026-09-03.zip") as z:
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        d = pd.read_csv(z.open(name), low_memory=False, encoding="latin1",
                        usecols=["Year", "State", "VariableDescriptionTotal", "Amount"])
    rows = []
    for c, label in ERS_SERIES.items():
        s = d[d["VariableDescriptionTotal"].str.strip() == label.strip()]
        rows.append(pd.DataFrame({"state": s["State"], "year": s["Year"].astype(int),
                                  "commodity": c, "receipts": s["Amount"] * 1e3}))
    return pd.concat(rows, ignore_index=True)


def load_gdp() -> pd.DataFrame:
    """Annual current-dollar state GDP, dollars."""
    with zipfile.ZipFile(RAW / "bea" / "SAGDP.zip") as z:
        name = [n for n in z.namelist() if n.startswith("SAGDP2__ALL_AREAS")][0]
        d = pd.read_csv(z.open(name), encoding="latin1", low_memory=False)
    d = d[d["LineCode"] == 1]
    fips = d["GeoFIPS"].astype(str).str.strip().str.strip('"').str[:2]
    d = d.assign(state=fips.map(FIPS)).dropna(subset=["state"])
    years = [c for c in d.columns if str(c).isdigit()]
    g = d.melt(id_vars="state", value_vars=years, var_name="year", value_name="gdp")
    g["year"] = g["year"].astype(int)
    g["gdp"] = pd.to_numeric(g["gdp"], errors="coerce") * 1e6
    return g.dropna()




def load_daily_spot() -> pd.DataFrame:
    """Daily WTI crude oil and Henry Hub natural gas spot prices from EIA."""
    out = {}
    for c, f in [("crude_oil", "RWTCd.xls"), ("natural_gas", "RNGWHHDd.xls")]:
        d = pd.read_excel(RAW / "eia" / f, sheet_name="Data 1", header=2)
        out[c] = pd.Series(pd.to_numeric(d.iloc[:, 1], errors="coerce").values,
                           index=pd.to_datetime(d["Date"]))
    return pd.DataFrame(out).sort_index()


def load_steo() -> pd.DataFrame:
    """Monthly WTI and Henry Hub path (history and forecast) from the latest STEO."""
    d = pd.read_excel(RAW / "eia" / "STEO_m.xlsx", sheet_name="1tab", header=None)
    years = d.iloc[2, 2:].ffill()
    months = d.iloc[3, 2:]
    idx = pd.PeriodIndex([pd.Period(f"{m} {int(y)}", freq="M") for y, m in zip(years, months)])
    out = pd.DataFrame(index=idx)
    for c, code in [("crude_oil", "WTIPUUS"), ("natural_gas", "NGHHUUS")]:
        row = d[d.iloc[:, 0].astype(str) == code].iloc[0, 2:]
        out[c] = pd.to_numeric(row.values, errors="coerce")
    stamp = str(d.iloc[1, 1]).split("-")[-1].strip()
    out.attrs["vintage"] = stamp
    return out


# ---------------------------------------------------------------- positions

def positions(prices: pd.DataFrame) -> pd.DataFrame:
    """Net position N[s,c] for each weight year Y: mean over Y-3..Y-1.

    Energy is in physical units. Agriculture is receipts divided by the mean annual price
    over the same years, a quantity equivalent in the Pink Sheet unit (producer side only).
    """
    energy = load_energy_positions()
    ag = load_ag_receipts()
    ag = ag[ag["year"] >= 1990]
    annual_p = prices.groupby(prices.index.year).mean()
    ag["net_qty"] = ag["receipts"] / ag.apply(lambda r: annual_p.loc[r.year, r.commodity],
                                               axis=1)
    base = pd.concat([energy, ag[["state", "year", "commodity", "net_qty"]]])
    base = base[base["state"].isin(STATES + list(OFFSHORE))]

    first, last = 2000, pd.Timestamp.today().year + 1
    rows = []
    for (s, c), g in base.groupby(["state", "commodity"]):
        g = g.set_index("year")["net_qty"]
        for Y in range(first, last + 1):
            window = [y for y in range(Y - WEIGHT_YEARS, Y) if y in g.index]
            if not window:
                continue
            # Past the last data year, the latest available three years are used.
            if Y - 1 > g.index.max():
                window = sorted(g.index)[-WEIGHT_YEARS:]
            rows.append((s, c, Y, g.loc[window].mean(), f"{min(window)}-{max(window)}"))
    return pd.DataFrame(rows, columns=["state", "commodity", "weight_year", "net_qty",
                                       "weight_window"])


def gdp_for_year(gdp: pd.DataFrame, years: pd.Series, states: pd.Series) -> np.ndarray:
    """State GDP for each year, carrying the latest BEA year forward."""
    g = gdp.set_index(["state", "year"])["gdp"]
    last = gdp.groupby("state")["year"].max()
    y = np.minimum(years.values, states.map(last).fillna(0).astype(int).values)
    return np.array([g.get((s, yy), np.nan) for s, yy in zip(states.values, y)])


# ---------------------------------------------------------------- ledger

def build() -> None:
    """Build net positions and the monthly, latest and outlook ledgers, and write them to
    data/clean/.
    """
    CLEAN.mkdir(parents=True, exist_ok=True)
    prices = load_prices()
    pos = positions(prices)
    gdp = load_gdp()
    pos.to_csv(CLEAN / "positions.csv", index=False)

    # Monthly ledger.
    dp = (prices - prices.shift(12)).loc[START:]
    long = dp.stack().rename("dprice").reset_index()
    long.columns = ["month", "commodity", "dprice"]
    long["weight_year"] = long["month"].dt.year
    m = long.merge(pos, on=["commodity", "weight_year"])
    m["windfall_usd"] = m["net_qty"] * m["dprice"]
    m["gdp"] = gdp_for_year(gdp, m["weight_year"], m["state"])
    m["windfall_pct_gdp"] = 100 * m["windfall_usd"] / m["gdp"]
    m["month"] = m["month"].astype(str)
    cols = ["state", "month", "commodity", "net_qty", "dprice", "windfall_usd",
            "windfall_pct_gdp", "weight_window"]
    m.sort_values(["state", "month", "commodity"])[cols].to_csv(
        CLEAN / "ledger_monthly.csv", index=False, float_format="%.6g")

    # Daily energy nowcast: latest spot vs the average of the same calendar window a year
    # earlier (+-3 trading days) to damp single-day noise.
    spot = load_daily_spot()
    asof = spot.dropna().index.max()
    year_ago = spot.loc[asof - pd.Timedelta(days=368): asof - pd.Timedelta(days=362)].mean()
    now = spot.loc[asof]
    pos_now = pos[pos["weight_year"] == asof.year]
    rows = []
    for c in ["crude_oil", "natural_gas"]:
        p = pos_now[pos_now["commodity"] == c].copy()
        p["price_now"], p["price_year_ago"] = now[c], year_ago[c]
        p["windfall_usd"] = p["net_qty"] * (now[c] - year_ago[c])
        rows.append(p)
    t = pd.concat(rows)
    t["gdp"] = gdp_for_year(gdp, pd.Series([asof.year] * len(t)), t["state"])
    t["windfall_pct_gdp"] = 100 * t["windfall_usd"] / t["gdp"]
    t.insert(0, "asof", asof.date().isoformat())
    t.drop(columns=["weight_year"]).to_csv(CLEAN / "ledger_today.csv", index=False,
                                          float_format="%.6g")

    # Outlook: windfall implied by the STEO price path, relative to the last twelve months
    # of realized prices.
    steo = load_steo()
    last_obs = prices["crude_oil"].dropna().index.max()
    base = prices.loc[last_obs - 11: last_obs, ["crude_oil", "natural_gas"]].mean()
    path = steo.loc[last_obs + 1:]
    o = []
    for c in ["crude_oil", "natural_gas"]:
        pc = pos[(pos["commodity"] == c)]
        for month, price in path[c].items():
            p = pc[pc["weight_year"] == min(month.year, pc["weight_year"].max())].copy()
            p["month"], p["steo_price"], p["base_price"] = str(month), price, base[c]
            p["windfall_usd"] = p["net_qty"] * (price - base[c])
            o.append(p)
    o = pd.concat(o)
    years = pd.Series(pd.PeriodIndex(o["month"], freq="M").year, index=o.index)
    o["gdp"] = gdp_for_year(gdp, years, o["state"])
    o["windfall_pct_gdp"] = 100 * o["windfall_usd"] / o["gdp"]
    o.insert(0, "steo_vintage", steo.attrs["vintage"])
    o.drop(columns=["weight_year"]).to_csv(CLEAN / "ledger_outlook.csv", index=False,
                                          float_format="%.6g")

    print(f"monthly rows {len(m):,}; prices through {last_obs}; "
          f"daily spot as of {asof.date()}; STEO {steo.attrs['vintage']}")


if __name__ == "__main__":
    build()
