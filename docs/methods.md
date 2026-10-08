# Methods note, State Shock Ledger v0

Samson M'boueke, 2026-10-08. Working document.

## Measure

For state *s*, commodity *c*, and month *t*, the windfall is

    W[s,c,t] = N[s,c,Y] * (p[c,t] - p[c,t-12])

where `p` is the world benchmark price and `N[s,c,Y]` is the state's net position in the
commodity for calendar year *Y* of month *t*. `W` is an annualized dollar flow: the change
in the value of a year of the state's net position caused by the price change over the
last twelve months. The state total is the sum over commodities, and the share of GDP
divides by current-dollar state GDP for year *Y* (the latest BEA year is carried forward).

The construction adapts the IMF commodity terms-of-trade database (Gruss and Kebhaj 2019),
which weights world commodity prices by country net exports to proxy windfall income gains
and losses, from countries to U.S. states.

### Net positions

Positions are the average of the three calendar years before *Y* (Y-3 to Y-1). Lagged
weights keep the measure driven by prices, not by the state's own output response. Past
the last data year, the latest three available years are used.

| Commodity | Net position | Unit | Price |
|---|---|---|---|
| Crude oil | SEDS crude production (PAPRP) minus crude-priced petroleum use: total petroleum consumption (PATCP) less hydrocarbon gas liquids (HLTCP), petroleum coke (PCTCP), and refinery still gas (SGICP) | barrels | WTI |
| Natural gas | SEDS marketed production (NGMPB) minus total consumption (NGTCB) | MMBtu | Henry Hub |
| Corn, soybeans, wheat, cattle | ERS cash receipts divided by the mean world price over the same years (producer side only) | Pink Sheet unit | Maize; Soybeans; Wheat, US HRW; Beef |

**Why the petroleum exclusions.** Hydrocarbon gas liquids (ethane, propane) are mostly
petrochemical feedstocks priced off natural gas and petrochemical markets, not crude.
Petroleum coke and still gas are refinery-internal fuels whose cost is passed to buyers of
refined products, often in other states. Without the exclusions, refining and
petrochemical states (Louisiana, Texas) appear to bear costs that are actually passed on.
In 2024 the exclusions remove 1.68 billion of 7.49 billion barrels of U.S. petroleum use
(gas liquids 1.37 billion, still gas 0.23 billion, petroleum coke 0.08 billion).

**Consumer pass-through for oil.** Consumers are assumed to pay roughly the crude price
change per barrel of refined product. Refining margins, taxes, and regional price
differences are ignored in v0.

### Views

- **History:** monthly, Pink Sheet prices, twelve-month change.
- **Latest:** energy uses the latest EIA daily spot price against the mean of the same
  seven-day window one year earlier; agriculture uses the latest Pink Sheet month.
- **Outlook:** the latest EIA STEO monthly WTI and Henry Hub path against the mean of the
  last twelve months of Pink Sheet prices, valued at current positions.
- **Scenario:** user-chosen oil and gas prices against the same twelve-month base.

## Interpretation and limits

1. **Gross value, not income.** `W` values production and use at benchmark prices. It is
   an upper bound on the income change accruing in the state: part of the windfall goes to
   owners, royalty holders, and shareholders elsewhere (Feyrer, Mansur and Sacerdote 2017
   estimate the local share for oil and gas), and wellhead prices differ from WTI and
   Henry Hub (Rocky Mountain gas trades at a discount, which inflates gas-state swings such
   as Wyoming's in 2008 to 2009).
2. **Agriculture is producer side only.** The farm share of retail food spending is small
   and pass-through is slow, so the consumer side is second order at monthly frequency. It
   is planned for a later version. Feed use by livestock states is not netted out.
3. **Federal offshore.** Production in federal offshore areas (SEDS codes X3, X5) belongs
   to no state and is reported separately. Its windfall accrues to producers and, through
   royalties, the federal government.
4. **Coal, copper, potash** are not in v0. Coal needs a U.S. coal price series (domestic
   coal is contract-priced); copper and potash need state production data, which USGS often
   withholds for confidentiality.
5. **Futures.** EIA stopped publishing free NYMEX futures after 2024-04-05, so the v0
   outlook uses EIA's STEO forecast. Licensed futures and options data would allow
   market-implied outlooks with uncertainty bands.

## Validation plan (Paper 1)

The ledger is useful to the extent that windfalls predict state outcomes. Paper 1 will
estimate Local Projections of state employment, personal income, prices, and tax revenue
on the windfall (state and time fixed effects, 2000 to 2025), report horizon-by-horizon
responses for 0 to 24 months, and test whether the net measure outperforms production-only
and consumption-only exposures. The estimated responses then become the dashboard's
"consequences" panel.

## References

- Gruss, B. and S. Kebhaj (2019). Commodity Terms of Trade: A New Database. IMF WP/19/21.
- Feyrer, J., E. Mansur and B. Sacerdote (2017). Geographic Dispersion of Economic Shocks:
  Evidence from the Fracking Revolution. American Economic Review 107(4).
- Jordà, Ò. (2005). Estimation and Inference of Impulse Responses by Local Projections.
  American Economic Review 95(1).
