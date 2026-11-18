"""Download the public inputs into data/raw/.

Every source is free and needs no API key. Files already present are skipped,
so the script can be re-run after an interruption; pass --force to refresh.
A SHA-256 manifest is written so that provider revisions are detectable.

    python code/01_fetch.py [--force]
"""

import argparse
import hashlib
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (state-shock-ledger research pipeline)"}

# name -> (url, saved filename). Keep in sync with config/sources.yaml.
SOURCES = {
    # EIA State Energy Data System: production and consumption by state, 1960-latest year.
    "eia_seds": ("https://www.eia.gov/state/seds/CDF/Complete_SEDS.csv", "eia/Complete_SEDS.csv"),
    # EIA daily spot prices.
    "eia_wti_daily": ("https://www.eia.gov/dnav/pet/hist_xls/RWTCd.xls", "eia/RWTCd.xls"),
    "eia_henryhub_daily": ("https://www.eia.gov/dnav/ng/hist_xls/RNGWHHDd.xls", "eia/RNGWHHDd.xls"),
    # EIA daily NYMEX futures, contracts 1-4. Series end 2024-04-05; kept for backtesting.
    "eia_pet_futures_daily": ("https://www.eia.gov/dnav/pet/xls/PET_PRI_FUT_S1_D.xls", "eia/PET_PRI_FUT_S1_D.xls"),
    "eia_ng_futures_daily": ("https://www.eia.gov/dnav/ng/xls/NG_PRI_FUT_S1_D.xls", "eia/NG_PRI_FUT_S1_D.xls"),
    # EIA Short-Term Energy Outlook, monthly history and forecast (forward outlook in v0;
    # EIA stopped publishing free NYMEX futures after 2024-04-05).
    "eia_steo": ("https://www.eia.gov/outlooks/steo/xls/STEO_m.xlsx", "eia/STEO_m.xlsx"),
    # EIA monthly crude oil field production by state.
    "eia_crude_prod_state_monthly": (
        "https://www.eia.gov/dnav/pet/xls/PET_CRD_CRPDN_ADC_MBBL_M.xls", "eia/PET_CRD_CRPDN_ADC_MBBL_M.xls"),
    # BEA state GDP (SAGDP tables, annual).
    "bea_sagdp": ("https://apps.bea.gov/regional/zip/SAGDP.zip", "bea/SAGDP.zip"),
    # USDA ERS farm income: cash receipts by commodity and state (September 2026 release).
    "ers_farm_income": (
        "https://www.ers.usda.gov/media/29517/september-3-2026-release.zip", "ers/farm_income_2026-09-03.zip"),
    # BEA input-output accounts: all Make/Use/requirements tables, including the 2017
    # detail (402-industry) Use table used for the minerals user side.
    "bea_io_all": ("https://apps.bea.gov/industry/iTables%20Static%20Files/AllTablesIO.zip",
                   "bea/AllTablesIO.zip"),
    # USGS Minerals Yearbook 2022 tables (state mine production where disclosed).
    "usgs_myb_2022_copper": ("https://pubs.usgs.gov/myb/vol1/2022/myb1-2022-copper.xlsx",
                             "usgs/myb1-2022-copper.xlsx"),
    "usgs_myb_2022_zinc": ("https://pubs.usgs.gov/myb/vol1/2022/myb1-2022-zinc.xlsx",
                           "usgs/myb1-2022-zinc.xlsx"),
    "usgs_myb_2022_tin": ("https://pubs.usgs.gov/myb/vol1/2022/myb1-2022-tin.xlsx",
                          "usgs/myb1-2022-tin.xlsx"),
    # World Bank Commodity Price Data (Pink Sheet), monthly.
    "wb_pinksheet_monthly": (
        "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/"
        "CMO-Historical-Data-Monthly.xlsx", "worldbank/CMO-Historical-Data-Monthly.xlsx"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, tries: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, tries + 1):
        try:
            with requests.get(url, headers=UA, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if tmp.stat().st_size == 0:
                raise IOError("empty download")
            tmp.replace(dest)
            return
        except Exception as e:  # network errors are retried, then reported
            if attempt == tries:
                raise
            print(f"  retry {attempt} after error: {e}")
            time.sleep(5 * attempt)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download files already present")
    args = ap.parse_args()

    failed = []
    for name, (url, rel) in SOURCES.items():
        dest = RAW / rel
        if dest.exists() and not args.force:
            print(f"skip   {name} ({rel})")
            continue
        print(f"fetch  {name}")
        try:
            fetch(url, dest)
        except Exception as e:
            print(f"FAILED {name}: {e}")
            failed.append(name)

    with open(RAW / "CHECKSUMS.sha256", "w", encoding="utf-8") as f:
        for _, rel in SOURCES.values():
            p = RAW / rel
            if p.exists():
                f.write(f"{sha256(p)}  {rel}\n")

    if failed:
        print("Failed:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
