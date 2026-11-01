# Methods review: Bloom, Schankerman and Van Reenen (2013)

**Paper.** Nicholas Bloom, Mark Schankerman and John Van Reenen, "Identifying Technology Spillovers and Product
Market Rivalry," *Econometrica* 81(4), July 2013, pp. 1347–1393, doi:10.3982/ECTA9466.

**Statistical focus.** Two things carry the paper. The first is the pair of fixed-effects coefficients in the
market-value equation (Table 3, column 2), 0.381 on technology spillovers and −0.083 on product-market rivals'
R&D, together with the matching coefficients in the patent, production and R&D equations. The second is the
calculation in Section 6.5 and Table 9 that turns those coefficients into a gross social return to R&D of 55.0%
against a private return of 20.7%.

**Review standard.** Current AEA Data and Code Availability Policy, and standard reporting of estimates,
uncertainty and sample construction for observational panel studies. For the returns calculation, the internal
consistency of the formulas and the explicitness of the assumptions behind them.

**What was read.** The full text of the CEP Discussion Paper No. 675 version, revised December 2012, which the
authors describe as a heavily revised version of their 2007 NBER working paper (w13060, whose abstract and
introduction I also read), including its appendices and Tables 1 to 10 and A1 to A4. The Econometric Society's
article page for the published version (abstract and citation). The authors' replication package posted with the
published article: its readme (dated July 30, 2013), the Stata program `BSV_replication.do` and the log file
`BSV_replication.log`. I did not read the typeset *Econometrica* article itself. The readme states that the
published numbers differ from the working-paper versions by about 5% on average because shares were no longer
rounded to whole percentiles; the coefficients I checked in the log (Table 3 columns 1, 2, 3, 4 and 6; Table 4
columns 1, 2, 3 and 5) agree with the December 2012 text to three decimals, so the values below should match the
published tables, but page and table numbers refer to the discussion paper.

## Methods summary

**Research design.** An observational firm-level panel. A two-stage oligopoly model (Section 2, Table 1) yields
sign predictions for how R&D by firms that are close in technology space and by firms that are close in product
markets should move a firm's market value, patents, productivity and R&D. The paper tests the six signed
predictions jointly by estimating four reduced-form equations on the same panel.

**Sampling strategy.** All US Compustat firms, 1980 to 2001, that could be matched to the NBER patent file and had
at least one patent granted since 1963, with at least four years of data (Section 3.4, Appendix B.4). No random
sampling; the population is listed, patenting firms.

**Sample size.** 715 firms (the number of clusters in the replication log); 9,944 firm-years in the market-value
equation, 9,023 in the patent equation, 9,935 in the production function and 8,579 in the R&D equation (Tables 3
to 6). The paper reports that sample firms' R&D was $79 billion in 1995, against $130 billion of total US
industrial R&D estimated by the NSF, or about 62% coverage (Appendix B.4).

**Inclusion and exclusion criteria.** At least one patent (needed for the technology position); some data in the
Compustat Segment File (needed for the product-market position); at least four observations. Exiting firms and
single-segment firms are kept. The patent equation stops in 1998 because of grant and citation lags.

**Independent and dependent variables.** The two key regressors are ln SPILLTECH, the R&D stocks of all other
firms weighted by the Jaffe uncentered correlation of patent shares over 426 USPTO classes (1970 to 1999 average),
and ln SPILLSIC, the same weighted by the correlation of sales shares over 597 four-digit industries (Compustat
segments, pooled 1993 to 2001). Both are lagged one year. Dependent variables are ln Tobin's Q, citation-weighted
patent counts, ln deflated sales and ln(R&D/sales). Controls include own R&D stock (15% depreciation), capital,
labor, a distance-weighted industry sales measure, year dummies and firm fixed effects.

**Statistical methods.** OLS with firm fixed effects and Newey-West standard errors allowing first-order serial
correlation (Tables 3, 5, 6); negative binomial with the Blundell-Griffith-Van Reenen pre-sample mean in place of
fixed effects and firm-clustered standard errors (Table 4); instrumental variables using federal and state R&D tax
prices weighted by the same distance matrices (final column of each table; control function with bootstrapped
standard errors for the patent equation). Market value is approximated by a sixth-order polynomial in the R&D to
capital ratio.

## Statistics extraction table

| Statistic | Value and unit | Source location | What it measures | What it does not establish |
|---|---|---|---|---|
| Market value on ln SPILLTECH, fixed effects | 0.381 (s.e. 0.113), elasticity | Table 3, col. 2 | Percent change in Tobin's Q for a 1% rise in technology neighbors' R&D stock, within firm | That the link is causal; that it is a knowledge flow rather than common technological opportunity (addressed only by the IV column) |
| Market value on ln SPILLSIC, fixed effects | −0.083 (s.e. 0.032), elasticity | Table 3, col. 2 | Percent change in Tobin's Q for a 1% rise in product-market rivals' R&D stock | How much of the loss is lost output versus lower prices (needed later and assumed) |
| Same, without firm effects | −0.064 (0.013) and 0.053 (0.007) | Table 3, col. 1 | Cross-sectional associations, both opposite to the theory | Anything about spillovers; shown to motivate fixed effects |
| Same, IV with tax-price instruments | 1.079 (0.192) and −0.235 (0.109); first-stage F 112.5 and 42.8 | Table 3, col. 6 | Effect when spillover pools are moved by other firms' tax-induced R&D | Instrument validity beyond the paper's checks on state credit timing (Appendix B.3.2) |
| Citation-weighted patents on ln SPILLTECH / ln SPILLSIC | 0.468 (0.080) / 0.056 (0.037) | Table 4, col. 2 | Knowledge production response to the two pools | Patent quality beyond citations; strategic patenting is acknowledged as a reason SPILLSIC need not be zero |
| Production function on ln SPILLTECH / ln SPILLSIC | 0.191 (0.046) / −0.005 (0.011) | Table 5, col. 2 | Revenue productivity response | Physical productivity, since output is deflated sales with industry, not firm, prices |
| Own R&D stock elasticity in production | 0.043 (0.007) | Table 5, col. 2 | Private output elasticity of R&D capital | The full private return, which also includes business stealing |
| R&D intensity on ln SPILLSIC | 0.083 (0.034) | Table 6, col. 2 | Strategic complementarity in R&D | Robust complementarity: the IV column gives −0.022 (0.071) |
| Correlation of TECH and SIC over firm pairs | 0.469; 0.319 for changes in the logged pools | Section 3.9 | How separately the two closeness measures vary | That the residual variation is free of measurement error |
| Social and private return, symmetric case | 58% and 20.8% at median Y/G = 2.48 | Section 6.5.2, equations (6.5) and (6.6) | 2.48 × (0.043 + 0.191) and 2.48 × (0.043 + 0.042) | Uncertainty; no standard errors are given for either return |
| Social and private return, full calculation | 55.0% and 20.7%, wedge 34.3 points | Table 9, row 1 | Simulated marginal returns over heterogeneous firms with amplification | Net returns; depreciation of social and private knowledge is not netted out |
| Alternative returns | Mahalanobis 73.7% vs 27.6%; IV 59.4% vs 39.3% | Table 9, rows 2 and 3 | Sensitivity to the distance metric and to instrumenting | Which version is preferred on statistical grounds |
| Returns by size quartile | Social 67.1% (largest) to 47.3% (smallest); private 20.5% to 21.1% | Table 9, rows 4 to 7 | Smaller firms sit in technological niches and spill less | A significance test of the difference between quartiles |

## Interpretation notes

- The paper is careful to say that only the value equation identifies business stealing, and only the R&D
  equation identifies strategic complementarity or substitution (Section 2). The headline social-private wedge
  therefore leans on a single coefficient, −0.083, for the private side.
- The private return requires the parameter σ, the share of a rival-induced fall in market value that comes from
  lost output. It is set to one half and argued to be conservative (footnote 45, Appendix G), not estimated.
- The returns use the production-function elasticity (0.191), not the much larger market-value elasticity, for
  the social side (footnote 44). This is a deliberate and stated choice.
- Fixed effects reverse the signs of both spillover coefficients relative to pooled OLS (Table 3, columns 1 and 2).
  The paper treats this as evidence that unobserved firm heterogeneity biases the cross-section; it also means the
  results rest on within-firm changes in the pools over two decades.
- Product-market closeness is measured from 1993 to 2001 segment data and applied back to 1981 (footnote 21). The
  paper reports robustness to alternative timing and to Bureau van Dijk sales data, but the measure is not
  contemporaneous for the first half of the sample.

## Unanswered questions

- Standard errors or confidence intervals for the social and private returns, and for their difference, are not
  reported, although the coefficient covariances needed for a delta-method interval exist.
- The equations are estimated separately; the returns combine coefficients from the production and value
  equations without a stated treatment of their covariance.
- The paper does not show how the results change if firms with very large R&D stocks (IBM, for instance) are
  dropped, which matters because pools are sums of other firms' stocks.
- How sensitive is σ = 1/2 to market structure across the 597 industries? The paper argues it is an upper bound
  under isoelastic demand and constant marginal cost but gives no industry-level evidence.

## Items requiring expert verification

- Whether the final *Econometrica* tables match the December 2012 discussion paper in every cell. The replication
  log matches the coefficients I checked, but Table 9 was not checked against the log.
- The validity of the tax-price instruments, which depends on a reading of the state R&D tax-credit literature
  (Appendix B.3.2) that a public-finance specialist should confirm.
- Whether Newey-West errors with one lag are adequate for a 20-year panel with persistent regressors. The authors
  argue in the replication program that clustering is over-conservative; the clustered IV standard errors in the
  log are larger (for example, 0.313 instead of 0.192 on ln SPILLTECH in Table 3, column 6, and −0.235 becomes
  insignificant at 5% with a clustered s.e. of 0.162).
- No published correction or formal comment on the paper was found. The authors' own update, Lucking, Bloom and
  Van Reenen (2019, *Fiscal Studies*), re-estimates the model on 1985–2015 data and reports a market-value
  coefficient of 0.324 on technology spillovers and −0.086 on rivals' R&D, and a social return of 57.7% against a
  private return of 13.6%.

On how this repository relates to the paper: the rerun here uses SEC filings, PatentsView and KPSS patent data for
2013–2024, a binary same-SIC measure of product-market closeness, public float in place of full equity market
value, and a production function with costs instead of employment. It asks the paper's question again with
different and coarser data, so its numbers are a fresh estimate, not a check of the published ones.
