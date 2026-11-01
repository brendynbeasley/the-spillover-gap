# Technical notes

The technical companion to the [README](README.md). Every table the scripts write is collected in
[results/FINDINGS.md](results/FINDINGS.md); a review of the original paper's methods is in
[METHODS_REVIEW.md](METHODS_REVIEW.md).

## The original study

Nicholas Bloom, Mark Schankerman and John Van Reenen, "Identifying Technology Spillovers and Product Market
Rivalry," *Econometrica* 81(4), 2013, pp. 1347–1393. On 715 Compustat firms, 1981–2001, with technology closeness
from patent classes and product-market closeness from Compustat segments, the fixed-effects market-value equation
gives 0.381 (0.113) on ln SPILLTECH and −0.083 (0.032) on ln SPILLSIC (Table 3, column 2). The implied gross social
return to R&D is 55.0% against a private return of 20.7% (Table 9). I checked the coefficients against the CEP
Discussion Paper 675 text (revised December 2012) and the authors' replication log.

## Headline results

| Equation, fixed effects | Variable | Paper | This study | N (firms) |
|---|---|---|---|---|
| Market value | ln SPILLTECH | 0.381 (0.113) | 0.114 (0.106) | 9,407 (1,276) |
| Market value | ln SPILLSIC | −0.083 (0.032) | −0.031 (0.016) | 9,407 (1,276) |
| Citation-weighted patents | ln SPILLTECH | 0.468 (0.080) | 0.485 (0.111) | 6,278 (1,147) |
| Citation-weighted patents | ln SPILLSIC | 0.056 (0.037) | −0.011 (0.041) | 6,278 (1,147) |
| Production (sales) | ln SPILLTECH | 0.191 (0.046) | −0.077 (0.099) | 8,079 (1,142) |
| Production (sales) | ln SPILLSIC | −0.005 (0.011) | 0.006 (0.014) | 8,079 (1,142) |
| R&D / sales | ln SPILLTECH | 0.100 (0.076) | 0.471 (0.172) | 9,474 (1,287) |
| R&D / sales | ln SPILLSIC | 0.083 (0.034) | 0.015 (0.031) | 9,474 (1,287) |
| Marginal social return | | 55.0% | −5.5%, CI [−43.1%, 32.2%] | |
| Marginal private return | | 20.7% | 11.1%, CI [−2.5%, 24.8%] | |

The paper's social and private returns are its full Table 9 figures; mine use its symmetric-firm formulas
(section 6.5.2), whose paper values are 58% and 20.8%.

## Data

- **Accounts:** SEC Financial Statement Data Sets, quarterly zips `2011q3.zip` to `2026q2.zip` (60 files), 10-K
  filings, consolidated, non-dimensional us-gaap values. Fiscal years ending January to June are assigned to the
  previous calendar year.
- **Market value:** `EntityPublicFloat.parquet`, the dei:EntityPublicFloat facts from the SEC's XBRL company-facts
  bulk data, through the `DenyTranDFW/edgar_xbrl_companyfacts` mirror on Hugging Face. Each fact is joined to its
  10-K by accession number, so any value can be checked against the filing on EDGAR. I used the mirror because the
  SEC's own endpoints refused my requests while I was building the panel.
- **Patents:** `KPSS_2025.zip`, `Match_patent_permco_permno_2025.zip`, `Match_patent_cpc_2025.zip` (Kogan,
  Papanikolaou, Seru & Stoffman 2017, extended to 2025) and `g_assignee_disambiguated.tsv.zip` (PatentsView release
  of December 31, 2024).
- **Download URLs** are constants at the top of `src/build_panel.py`; the raw files were downloaded on November 1,
  2026.
- **Committed processed files** in `data/processed/`: `firm_years.csv.gz`, `patent_years.csv.gz`,
  `tech_shares.csv.gz`, `patent_bridge.csv` and `spill_panel.csv.gz`.

## Method (rules fixed before looking at results)

- **Linking patents to filers.** A KPSS firm (permco) is linked to an SEC filer whose current or former name equals
  the patents' normalized assignee name (at least 3 patents or 10% of the firm's patents), or failing that whose
  name is the assignee name's leading words (at least 10 patents and 25%). Because a permco's technology position
  goes to every filer linked to it, a link is kept only if the filer matches at least half as many of the permco's
  patents as the permco's best-matched filer; this removes stray links such as PTC Therapeutics on three of Amgen's
  patents while keeping renamed successors (Broadcom, Medtronic). This one filter was added after the first results,
  when the links were audited; the other rules here were fixed beforehand. Four links were added by hand for large
  R&D spenders whose parent and patent-holding subsidiary have different names (Alphabet, Dell Technologies and the
  two Marvell parents). Filers linked to the same permco are treated as one firm in the closeness matrices.
- **Technology position.** Fractional counts of each 2000–2022 patent over its distinct CPC subclasses, summed by
  firm and normalized to shares. TECH is the Jaffe uncentered correlation.
- **Product market.** SIC is 1 when two filers share the four-digit SIC code on their latest 10-K, else 0.
- **R&D stock.** Perpetual inventory with 15% depreciation, starting value R&D/(0.05 + 0.15); isolated missing years
  are interpolated. Firms need positive R&D in at least four fiscal years. Fiscal 2010–2012 are burn-in, and outcomes
  run 2013–2024.
- **Pools.** Sums over all 1,887 sample R&D firms, lagged one year. A robustness version uses only the 528 firms with
  an R&D stock in every year 2012–2024.
- **Samples.** Estimation firms need median sales of at least $10 million. Public floats 50 times above or below the
  firm's median are set to missing. The top and bottom 0.5% of ln Q are dropped.
- **Estimation.** The value equation is

```math
\ln Q_{it} = \sum_{k=1}^{6} \beta_k g_{i,t-1}^{k} + \gamma_2 s^{T}_{i,t-1} + \gamma_3 s^{S}_{i,t-1} + \delta' x_{it} + \alpha_i + \tau_t + \varepsilon_{it}
```

  with $`Q = (\text{float} + \text{liabilities})/\text{assets}`$, $`g = G/A`$ capped at its 99th percentile,
  $`s^T = \ln \text{SPILLTECH}`$, $`s^S = \ln \text{SPILLSIC}`$, and $`x`$ the log of current and lagged sales of
  other SEC filers in the same four-digit SIC. Production uses log sales on lagged log net PP&E, lagged log
  (COGS + SG&A) and lagged log R&D stock; the R&D equation uses ln(R&D/sales). All three are within-firm OLS with year
  dummies and standard errors clustered by firm. Patents are a negative binomial for forward citations to patents
  filed in year t (2013–2020) on lagged log R&D stock, both lagged pools and lagged log sales, with the log
  2000–2009 mean (and a dummy for firms with none) as a fixed-effect proxy, year and two-digit SIC dummies (SIC
  groups with at least 20 firm-years), clustered by firm, started from Poisson estimates.
- **Returns.** With $`\psi_1`$ and $`\psi_2`$ from the production function and $`\gamma_3`$ from the value
  equation,

```math
\text{MSR} = \tfrac{Y}{G}(\psi_1 + \psi_2), \qquad \text{MPR} = \tfrac{Y}{G}(\psi_1 - 0.5\,\gamma_3)
```

  at the median of sales over lagged R&D stock (1.80). The MSR interval uses the production covariance matrix; the
  MPR interval treats the two equations as independent.
- **Extension.** The value and production equations are re-estimated with the spillover coefficients (and own R&D
  in production) split across 2013–2016, 2017–2020 and 2021–2024, with Wald tests of equality.

## Full test statistics

| Specification | ln SPILLTECH | ln SPILLSIC |
|---|---|---|
| Value, pooled OLS | 0.069 (0.016) | 0.001 (0.009) |
| Value, firm FE, TECH only | 0.042 (0.100) | |
| Value, firm FE, SIC only | | −0.028 (0.016) |
| Value, firm FE, pools from always-present firms | 0.188 (0.166) | −0.012 (0.043) |
| Patents, no fixed effect | 0.444 (0.117) | −0.014 (0.043) |
| Patents, pre-sample FE, patent counts | 0.270 (0.068) | −0.005 (0.028) |
| Production, pooled OLS | 0.120 (0.017) | −0.046 (0.011) |
| Production, firm FE, pools from always-present firms | −0.238 (0.137) | −0.011 (0.041) |
| R&D / sales, pooled OLS | 0.240 (0.040) | 0.390 (0.032) |

Poisson versions of the patent equation are in `results/main_estimates.csv`. Wald tests of equal coefficients
across the three blocks: value on ln SPILLTECH, p = 0.27; value on ln SPILLSIC, p = 0.78; production on ln
SPILLTECH, p = 0.60; production on own R&D, p = 0.81. Within-firm standard deviation net of year effects is 0.13
for ln SPILLTECH, 0.32 for ln SPILLSIC and 0.34 for ln Q.

## Reproducing the results

```bash
pip install -r requirements.txt
python src/build_panel.py      # downloads about 6 GB into data/raw/ on first run, writes data/processed/
python src/spillovers.py       # the four equations, returns, robustness, coefficients_vs_bsv.png
python src/over_time.py        # extension by block, named firms, blocks_coefficients.png
```

The last two run offline from the committed `data/processed/` files.

## References

- Bloom, N., Schankerman, M. & Van Reenen, J. (2013). Identifying technology spillovers and product market
  rivalry. *Econometrica* 81(4).
- Blundell, R., Griffith, R. & Van Reenen, J. (1999). Market share, market value and innovation in a panel of
  British manufacturing firms. *Review of Economic Studies* 66(3).
- Jaffe, A. (1986). Technological opportunity and spillovers of R&D. *American Economic Review* 76(5).
- Kogan, L., Papanikolaou, D., Seru, A. & Stoffman, N. (2017). Technological innovation, resource allocation, and
  growth. *Quarterly Journal of Economics* 132(2).
- Lucking, B., Bloom, N. & Van Reenen, J. (2019). Have R&D spillovers declined in the 21st century? *Fiscal
  Studies* 40(4).
