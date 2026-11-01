# Bloom, Schankerman & Van Reenen (2013) on 2013–2024 data: findings

## In plain English

Bloom, Schankerman and Van Reenen showed that a company gains when firms working in the same technologies do more
research and loses when its product-market rivals do. This study reruns their four equations on US-listed
companies with SEC accounts, 2013–2024. The spillover pools are built from 1,887 patenting R&D firms, and the
main fixed-effects estimates use between 1,142 and 1,287 of them.

- **Neighbors' research still feeds a firm's patents.** Firms whose patent portfolios overlap with big research
  spenders (Apple with Alphabet, Intel with IBM, Merck with Bristol Myers Squibb) file more highly cited patents,
  holding their own R&D fixed. The coefficient, 0.485, is almost the paper's 0.468. Rivals' research has no effect
  on patents, as the theory predicts.
- **Rivals' research still costs market value, but less.** A 10% rise in the R&D of firms in the same industry goes
  with a 0.3% lower market value (the paper found 0.8%), and the estimate is just short of significance at 5%
  (p = 0.058).
- **The productivity and market-value gains from neighbors are not detectable within firms.** The technology pool
  barely moves inside a firm over twelve years, so the fixed-effects estimates are imprecise. The implied social
  return to R&D, −5.5%, has a 95% interval from −43.1% to 32.2%, which excludes the paper's 55% but also allows
  large positive returns.
- **Nothing changed across 2013–2016, 2017–2020 and 2021–2024.** Wald tests cannot reject that the coefficients are
  equal across the three blocks (p = 0.27, 0.78 and 0.60).

A friendlier tour is in the [README](../README.md); data and rules are in [TECHNICAL.md](../TECHNICAL.md).

**Key to the labels below.** *SPILLTECH* = R&D stocks of other firms weighted by technology closeness (TECH, the
uncentered correlation of CPC patent shares). *SPILLSIC* = R&D stocks of other firms in the same four-digit SIC
code. Both enter lagged one year and in logs (`ln_spilltech`, `ln_spillsic`). *ln_G* = log own R&D stock (15%
depreciation). *ga1* = R&D stock over assets (first term of the sixth-order polynomial). *ln_ppe*, *ln_costs* =
lagged log net PP&E and lagged log COGS plus SG&A. *ln_sales_l* = lagged log sales. *ln_pre_cites*,
*ln_pre_patents* = log mean 2000–2009 citations or patents (the pre-sample fixed effect). *Equations*: `value` = ln
Tobin's Q, `patents` = forward citations (or counts) to patents filed in the year, negative binomial unless marked
Poisson, `production` = log sales, `rd` = log R&D over sales. *FE* = firm fixed effects. Standard errors are
clustered by firm; `ci_low` and `ci_high` are 95% intervals. Dollar figures are millions unless a column ends in
`_bn` (billions). *BSV* = Bloom, Schankerman and Van Reenen. The `ratio` column in the returns tables is social over
private and is not meaningful when the social return is negative. In `blocks_estimates.csv` the Wald rows report
the chi-squared statistic in the `coef` column. Figures are rounded to three decimals from the CSVs.

## Every table the scripts produce

### build_counts.csv

| step | kept | dropped |
|---|---|---|
| SEC firm-years with total assets, fiscal 2010-2025 | 104,380 | 21,519 |
| Public-float facts matched to a 10-K in the FSDS | 80,517 | 36,921 |
| KPSS patents filed 2000-2022 (of all years) | 2,212,524 | 1,619,384 |
| ... with a permco | 2,212,524 | 0 |
| permco-CIK links by exact name (>= 3 patents or 10%) | 3,067 | 104 |
| permco-CIK links by leading words (>= 10 patents and 25%) | 167 | 260 |
| ... links kept with at least half the matches of the permco's best filer | 3,204 | 30 |
| permco-CIK links added by hand (parents of patent-holding subsidiaries) | 4 | 0 |
| KPSS patents filed 2000-2022 attributed to an SEC filer | 1,507,100 | 705,424 |
| SEC filers with a technology position (CPC shares) | 3,117 | 0 |
| CPC subclasses used in the technology positions | 662 | 0 |

### sample_counts.csv

| step | kept | dropped |
|---|---|---|
| SEC filers with a patent-based technology position | 3,112 | 10,664 |
| ... reporting positive R&D in at least 4 fiscal years | 1,887 | 1,225 |
| firms with an R&D stock in every year 2012-2024 (robustness pools) | 528 | 0 |
| public floats dropped as scale errors (50x the firm's median) | 264 | 0 |
| firm-years 2013-2024 with an R&D stock and spillover pools | 15,101 | 0 |
| ... of firms with median sales of $10 million or more | 10,932 | 4,169 |
| market-value firm-years after trimming 0.5% tails of ln Q | 10,056 | 102 |
| patent-equation firm-years 2013-2020 | 6,278 | 0 |

### proximity_summary.csv

| statistic | value |
|---|---|
| firms | 1,887 |
| mean TECH over firm pairs | 0.116 |
| mean SIC over firm pairs | 0.086 |
| correlation of TECH and SIC over pairs | 0.505 |
| share of pairs with TECH > 0.5 | 0.098 |
| share of same-SIC pairs with TECH < 0.1 | 0.132 |
| share of all 10-K R&D in 2023 done by these firms | 0.895 |

### identifying_variation.csv

| variable | total_sd | within_firm_sd | within_firm_net_of_year_sd |
|---|---|---|---|
| ln_spilltech | 1.091 | 0.222 | 0.132 |
| ln_spillsic | 2.523 | 0.356 | 0.323 |
| ln_Q | 0.604 | 0.355 | 0.343 |
| ln_G | 1.899 | 0.440 | 0.363 |
| corr(ln_spilltech, ln_spillsic), levels | 0.456 |  |  |
| corr(ln_spilltech, ln_spillsic), within firm net of year | 0.328 |  |  |

### descriptives.csv

| variable | median | mean | sd | n |
|---|---|---|---|---|
| Tobin's Q (V/A) | 1.875 | 2.426 | 1.790 | 10,056 |
| Market value V | 1,226 | 18,011 | 106,707 | 10,056 |
| R&D stock G | 234.402 | 1,788 | 7,918 | 10,932 |
| R&D stock / assets | 0.402 | 4.547 | 172.945 | 10,450 |
| R&D flow R | 52.041 | 395.881 | 1,888 | 10,879 |
| SPILLTECH | 190,737 | 238,970 | 200,723 | 10,461 |
| SPILLSIC | 25,230 | 108,851 | 145,822 | 10,461 |
| Patents filed (2013-2020) | 4.000 | 63.351 | 369.293 | 6,278 |
| Forward citations to patents filed (2013-2020) | 6.000 | 381.449 | 4,599 | 6,278 |
| Sales Y | 326.858 | 3,829 | 17,118 | 10,589 |
| Sales / R&D stock | 1.800 | 8.198 | 245.453 | 8,079 |
| Total assets A | 531.563 | 6,539 | 26,463 | 10,923 |

### main_estimates.csv

| equation | spec | variable | coef | se | ci_low | ci_high | p | n_obs | n_firms |
|---|---|---|---|---|---|---|---|---|---|
| value | (1) pooled OLS | ln_spilltech | 0.069 | 0.016 | 0.038 | 0.101 | 0.000 | 9,407 | 1,276 |
| value | (1) pooled OLS | ln_spillsic | 0.001 | 0.009 | -0.017 | 0.019 | 0.938 | 9,407 | 1,276 |
| value | (1) pooled OLS | ga1 | 2.116 | 0.340 | 1.448 | 2.783 | 0.000 | 9,407 | 1,276 |
| value | (2) firm FE | ln_spilltech | 0.114 | 0.106 | -0.094 | 0.322 | 0.283 | 9,407 | 1,276 |
| value | (2) firm FE | ln_spillsic | -0.031 | 0.016 | -0.063 | 0.001 | 0.058 | 9,407 | 1,276 |
| value | (2) firm FE | ga1 | 0.820 | 0.334 | 0.165 | 1.475 | 0.014 | 9,407 | 1,276 |
| value | (3) firm FE, TECH only | ln_spilltech | 0.042 | 0.100 | -0.154 | 0.238 | 0.675 | 9,929 | 1,334 |
| value | (3) firm FE, TECH only | ga1 | 0.724 | 0.320 | 0.097 | 1.350 | 0.024 | 9,929 | 1,334 |
| value | (4) firm FE, SIC only | ln_spillsic | -0.028 | 0.016 | -0.060 | 0.004 | 0.084 | 9,407 | 1,276 |
| value | (4) firm FE, SIC only | ga1 | 0.827 | 0.334 | 0.173 | 1.480 | 0.013 | 9,407 | 1,276 |
| patents | (1) no fixed effect | ln_G | 0.830 | 0.083 | 0.667 | 0.993 | 0.000 | 6,278 | 1,147 |
| patents | (1) no fixed effect | ln_spilltech | 0.444 | 0.117 | 0.214 | 0.673 | 0.000 | 6,278 | 1,147 |
| patents | (1) no fixed effect | ln_spillsic | -0.014 | 0.043 | -0.100 | 0.071 | 0.740 | 6,278 | 1,147 |
| patents | (1) no fixed effect | ln_sales_l | 0.033 | 0.063 | -0.091 | 0.156 | 0.604 | 6,278 | 1,147 |
| patents | (1) no fixed effect, Poisson | ln_G | 0.570 | 0.163 | 0.251 | 0.889 | 0.000 | 6,278 | 1,147 |
| patents | (1) no fixed effect, Poisson | ln_spilltech | -0.513 | 0.539 | -1.571 | 0.544 | 0.341 | 6,278 | 1,147 |
| patents | (1) no fixed effect, Poisson | ln_spillsic | 0.258 | 0.177 | -0.090 | 0.605 | 0.146 | 6,278 | 1,147 |
| patents | (1) no fixed effect, Poisson | ln_sales_l | 0.487 | 0.267 | -0.036 | 1.010 | 0.068 | 6,278 | 1,147 |
| patents | (2) pre-sample FE | ln_G | 0.665 | 0.071 | 0.526 | 0.805 | 0.000 | 6,278 | 1,147 |
| patents | (2) pre-sample FE | ln_spilltech | 0.485 | 0.111 | 0.267 | 0.702 | 0.000 | 6,278 | 1,147 |
| patents | (2) pre-sample FE | ln_spillsic | -0.011 | 0.041 | -0.092 | 0.070 | 0.789 | 6,278 | 1,147 |
| patents | (2) pre-sample FE | ln_sales_l | -0.026 | 0.054 | -0.131 | 0.079 | 0.630 | 6,278 | 1,147 |
| patents | (2) pre-sample FE | ln_pre_cites | 0.269 | 0.039 | 0.193 | 0.345 | 0.000 | 6,278 | 1,147 |
| patents | (2) pre-sample FE, Poisson | ln_G | 0.163 | 0.159 | -0.149 | 0.475 | 0.305 | 6,278 | 1,147 |
| patents | (2) pre-sample FE, Poisson | ln_spilltech | -0.224 | 0.180 | -0.576 | 0.129 | 0.213 | 6,278 | 1,147 |
| patents | (2) pre-sample FE, Poisson | ln_spillsic | 0.072 | 0.060 | -0.045 | 0.189 | 0.230 | 6,278 | 1,147 |
| patents | (2) pre-sample FE, Poisson | ln_sales_l | 0.192 | 0.104 | -0.011 | 0.395 | 0.064 | 6,278 | 1,147 |
| patents | (2) pre-sample FE, Poisson | ln_pre_cites | 0.743 | 0.125 | 0.498 | 0.988 | 0.000 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts | ln_G | 0.572 | 0.053 | 0.469 | 0.676 | 0.000 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts | ln_spilltech | 0.270 | 0.068 | 0.137 | 0.403 | 0.000 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts | ln_spillsic | -0.005 | 0.028 | -0.060 | 0.050 | 0.862 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts | ln_sales_l | 0.049 | 0.036 | -0.022 | 0.121 | 0.176 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts | ln_pre_patents | 0.260 | 0.034 | 0.194 | 0.327 | 0.000 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts, Poisson | ln_G | 0.514 | 0.120 | 0.279 | 0.750 | 0.000 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts, Poisson | ln_spilltech | 0.250 | 0.086 | 0.082 | 0.418 | 0.004 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts, Poisson | ln_spillsic | -0.029 | 0.039 | -0.106 | 0.049 | 0.468 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts, Poisson | ln_sales_l | 0.169 | 0.088 | -0.003 | 0.341 | 0.054 | 6,278 | 1,147 |
| patents | (3) pre-sample FE, patent counts, Poisson | ln_pre_patents | 0.287 | 0.093 | 0.105 | 0.470 | 0.002 | 6,278 | 1,147 |
| production | (1) pooled OLS | ln_ppe | 0.213 | 0.017 | 0.180 | 0.246 | 0.000 | 8,079 | 1,142 |
| production | (1) pooled OLS | ln_costs | 0.548 | 0.029 | 0.491 | 0.604 | 0.000 | 8,079 | 1,142 |
| production | (1) pooled OLS | ln_G | 0.188 | 0.018 | 0.153 | 0.223 | 0.000 | 8,079 | 1,142 |
| production | (1) pooled OLS | ln_spilltech | 0.120 | 0.017 | 0.087 | 0.153 | 0.000 | 8,079 | 1,142 |
| production | (1) pooled OLS | ln_spillsic | -0.046 | 0.011 | -0.069 | -0.024 | 0.000 | 8,079 | 1,142 |
| production | (2) firm FE | ln_ppe | 0.130 | 0.033 | 0.065 | 0.196 | 0.000 | 8,079 | 1,142 |
| production | (2) firm FE | ln_costs | 0.528 | 0.056 | 0.417 | 0.638 | 0.000 | 8,079 | 1,142 |
| production | (2) firm FE | ln_G | 0.046 | 0.038 | -0.028 | 0.120 | 0.219 | 8,079 | 1,142 |
| production | (2) firm FE | ln_spilltech | -0.077 | 0.099 | -0.270 | 0.116 | 0.436 | 8,079 | 1,142 |
| production | (2) firm FE | ln_spillsic | 0.006 | 0.014 | -0.022 | 0.034 | 0.672 | 8,079 | 1,142 |
| production | (3) firm FE, TECH only | ln_ppe | 0.132 | 0.032 | 0.070 | 0.195 | 0.000 | 8,543 | 1,194 |
| production | (3) firm FE, TECH only | ln_costs | 0.516 | 0.051 | 0.416 | 0.617 | 0.000 | 8,543 | 1,194 |
| production | (3) firm FE, TECH only | ln_G | 0.048 | 0.037 | -0.024 | 0.119 | 0.193 | 8,543 | 1,194 |
| production | (3) firm FE, TECH only | ln_spilltech | -0.056 | 0.093 | -0.239 | 0.126 | 0.544 | 8,543 | 1,194 |
| value | (5) firm FE, pools from always-present firms | ln_spilltech | 0.188 | 0.166 | -0.136 | 0.513 | 0.255 | 9,044 | 1,214 |
| value | (5) firm FE, pools from always-present firms | ln_spillsic | -0.012 | 0.043 | -0.096 | 0.072 | 0.784 | 9,044 | 1,214 |
| production | (4) firm FE, pools from always-present firms | ln_ppe | 0.123 | 0.034 | 0.056 | 0.190 | 0.000 | 7,746 | 1,082 |
| production | (4) firm FE, pools from always-present firms | ln_costs | 0.533 | 0.058 | 0.418 | 0.647 | 0.000 | 7,746 | 1,082 |
| production | (4) firm FE, pools from always-present firms | ln_G | 0.051 | 0.040 | -0.027 | 0.130 | 0.200 | 7,746 | 1,082 |
| production | (4) firm FE, pools from always-present firms | ln_spilltech | -0.238 | 0.137 | -0.508 | 0.031 | 0.083 | 7,746 | 1,082 |
| production | (4) firm FE, pools from always-present firms | ln_spillsic | -0.011 | 0.041 | -0.091 | 0.069 | 0.787 | 7,746 | 1,082 |
| rd | (1) pooled OLS | ln_spilltech | 0.240 | 0.040 | 0.162 | 0.317 | 0.000 | 9,474 | 1,287 |
| rd | (1) pooled OLS | ln_spillsic | 0.390 | 0.032 | 0.328 | 0.451 | 0.000 | 9,474 | 1,287 |
| rd | (2) firm FE | ln_spilltech | 0.471 | 0.172 | 0.133 | 0.809 | 0.006 | 9,474 | 1,287 |
| rd | (2) firm FE | ln_spillsic | 0.015 | 0.031 | -0.046 | 0.076 | 0.636 | 9,474 | 1,287 |

### returns.csv

| source | median_Y_over_G | phi1_own_rd | phi2_spilltech | gamma3_spillsic_value | social_return | social_se | private_return | private_se | ratio | social_ci_low | social_ci_high | private_ci_low | private_ci_high |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| This study, 2013-2024 | 1.800 | 0.046 | -0.077 | -0.031 | -0.055 | 0.192 | 0.111 | 0.070 | -0.490 | -0.431 | 0.322 | -0.025 | 0.248 |
| BSV symmetric case (section 6.5.2) | 2.480 | 0.043 | 0.191 | -0.083 | 0.580 |  | 0.208 |  | 2.788 |  |  |  |  |
| Lucking, Bloom & Van Reenen 2019, 1985-2015 | 2.345 | 0.015 | 0.231 | -0.086 | 0.577 |  | 0.136 |  | 4.243 |  |  |  |  |

### blocks_estimates.csv

| equation | block | variable | coef | se | p | n_obs | n_firms |
|---|---|---|---|---|---|---|---|
| value | 2013-2016 | ln_spilltech | 0.035 | 0.122 | 0.776 | 9,407 | 1,276 |
| value | 2013-2016 | ln_spillsic | -0.026 | 0.018 | 0.153 | 9,407 | 1,276 |
| value | 2017-2020 | ln_spilltech | 0.063 | 0.117 | 0.595 | 9,407 | 1,276 |
| value | 2017-2020 | ln_spillsic | -0.029 | 0.017 | 0.089 | 9,407 | 1,276 |
| value | 2021-2024 | ln_spilltech | 0.064 | 0.112 | 0.571 | 9,407 | 1,276 |
| value | 2021-2024 | ln_spillsic | -0.033 | 0.017 | 0.050 | 9,407 | 1,276 |
| production | 2013-2016 | ln_spilltech | -0.154 | 0.125 | 0.217 | 8,079 | 1,142 |
| production | 2013-2016 | ln_spillsic | -0.006 | 0.015 | 0.711 | 8,079 | 1,142 |
| production | 2013-2016 | ln_G | 0.042 | 0.038 | 0.268 | 8,079 | 1,142 |
| production | 2017-2020 | ln_spilltech | -0.147 | 0.118 | 0.213 | 8,079 | 1,142 |
| production | 2017-2020 | ln_spillsic | 0.004 | 0.015 | 0.817 | 8,079 | 1,142 |
| production | 2017-2020 | ln_G | 0.045 | 0.039 | 0.239 | 8,079 | 1,142 |
| production | 2021-2024 | ln_spilltech | -0.133 | 0.113 | 0.240 | 8,079 | 1,142 |
| production | 2021-2024 | ln_spillsic | 0.013 | 0.015 | 0.355 | 8,079 | 1,142 |
| production | 2021-2024 | ln_G | 0.041 | 0.039 | 0.294 | 8,079 | 1,142 |
| value | equal across blocks (Wald) | ln_spilltech | 2.606 |  | 0.272 | 9,407 |  |
| value | equal across blocks (Wald) | ln_spillsic | 0.495 |  | 0.781 | 9,407 |  |
| production | equal across blocks (Wald) | ln_spilltech | 1.018 |  | 0.601 | 8,079 |  |
| production | equal across blocks (Wald) | ln_G | 0.419 |  | 0.811 | 8,079 |  |

### blocks_returns.csv

| block | median_Y_over_G | phi1_own_rd | phi2_spilltech | gamma3_spillsic_value | social_return | social_se | private_return | private_se | ratio | social_ci_low | social_ci_high | private_ci_low | private_ci_high |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2013-2016 | 1.906 | 0.042 | -0.154 | -0.026 | -0.213 | 0.257 | 0.105 | 0.075 | -2.024 | -0.718 | 0.292 | -0.042 | 0.252 |
| 2017-2020 | 1.772 | 0.045 | -0.147 | -0.029 | -0.180 | 0.224 | 0.107 | 0.070 | -1.687 | -0.619 | 0.259 | -0.031 | 0.244 |
| 2021-2024 | 1.692 | 0.041 | -0.133 | -0.033 | -0.155 | 0.207 | 0.097 | 0.068 | -1.599 | -0.560 | 0.250 | -0.036 | 0.230 |

### named_closeness.csv

| firm_a | firm_b | sic_a | sic_b | SIC_now | TECH_now | SIC_bsv | TECH_bsv |
|---|---|---|---|---|---|---|---|
| IBM | Apple | 3570 | 3571 | 0.000 | 0.869 | 0.650 | 0.640 |
| IBM | Motorola Solutions | 3570 | 3663 | 0.000 | 0.420 | 0.010 | 0.460 |
| IBM | Intel | 3570 | 3674 | 0.000 | 0.941 | 0.010 | 0.760 |
| Apple | Motorola Solutions | 3571 | 3663 | 0.000 | 0.721 | 0.020 | 0.170 |
| Apple | Intel | 3571 | 3674 | 0.000 | 0.899 | 0.000 | 0.470 |
| Motorola Solutions | Intel | 3663 | 3674 | 0.000 | 0.596 | 0.340 | 0.460 |

### named_firms.csv

| firm | sic4 | rd_flow_bn | rd_stock_bn | spilltech_bn | spillsic_bn | same_sic_rivals | nearest_tech_neighbor | nearest_TECH | firms_with_TECH_over_half |
|---|---|---|---|---|---|---|---|---|---|
| Alphabet | 7370 | 45.427 | 167.299 | 855.827 | 108.082 | 17 | MICROSOFT CORP | 0.978 | 166 |
| Meta Platforms | 7370 | 38.483 | 116.860 | 881.966 | 159.252 | 17 | ALPHABET INC. | 0.927 | 184 |
| Merck | 2834 | 30.531 | 90.051 | 435.806 | 422.534 | 127 | BRISTOL MYERS SQUIBB CO | 0.976 | 78 |
| Apple | 3571 | 29.915 | 108.414 | 883.550 | 20.496 | 4 | ALPHABET INC. | 0.927 | 159 |
| Microsoft | 7372 | 29.510 | 127.239 | 870.917 | 188.512 | 94 | ORACLE CORP | 0.989 | 157 |
| Intel | 3674 | 16.046 | 87.180 | 894.058 | 142.609 | 57 | INTERNATIONAL BUSINESS MACHINES CORP | 0.941 | 162 |
| Johnson & Johnson | 2834 | 15.085 | 75.737 | 233.904 | 421.202 | 127 | SHOCKWAVE MEDICAL, INC. | 0.957 | 49 |
| Pfizer | 2834 | 10.679 | 63.201 | 497.657 | 430.767 | 127 | ABBVIE INC. | 0.985 | 120 |
| Eli Lilly | 2834 | 9.313 | 41.230 | 437.084 | 455.009 | 127 | BRISTOL MYERS SQUIBB CO | 0.982 | 82 |
| Qualcomm | 3663 | 8.818 | 39.976 | 505.944 | 10.856 | 12 | NETGEAR, INC. | 0.966 | 67 |
| Nvidia | 3674 | 8.675 | 26.595 | 810.897 | 205.214 | 57 | AUTODESK, INC. | 0.971 | 122 |
| Cisco | 3576 | 7.551 | 41.863 | 584.053 | 12.995 | 7 | RIBBON COMMUNICATIONS INC. | 0.990 | 104 |
| IBM | 3570 | 6.775 | 39.934 | 936.092 | 25.375 | 2 | ORACLE CORP | 0.964 | 153 |
| Advanced Micro Devices | 3674 | 5.872 | 17.629 | 507.186 | 212.464 | 57 | PDF SOLUTIONS INC | 0.944 | 27 |
| Tesla | 3711 | 3.969 | 11.989 | 303.918 | 3.416 | 2 | BLOOM ENERGY CORP | 0.737 | 7 |
| Boeing | 3721 | 3.377 | 20.578 | 450.599 | 0.593 | 1 | TEXTRON INC | 0.730 | 3 |
| Micron | 3674 | 3.114 | 14.278 | 435.782 | 213.163 | 57 | EVERSPIN TECHNOLOGIES INC. | 0.958 | 29 |
| Medtronic | 3845 | 2.735 | 14.785 | 173.900 | 2.256 | 14 | NEUROPACE INC | 0.907 | 51 |

### worked_example.csv

| year_of_pool | TECH_apple_intel | intel_rd_stock_bn | contribution_bn | apple_spilltech_bn | intel_share_of_pool |
|---|---|---|---|---|---|
| 2024 | 0.899 | 87.180 | 78.344 | 966.346 | 0.081 |
