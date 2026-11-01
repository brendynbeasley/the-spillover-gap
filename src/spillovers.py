"""Bloom, Schankerman & Van Reenen (2013) on 2013-2024 US data: technology spillovers vs. product rivalry.

Reads the panel built by src/build_panel.py and

  1. builds each firm's R&D stock (perpetual inventory, 15% depreciation, as in the paper),
  2. measures closeness between every pair of firms in technology space (TECH, the Jaffe uncentered
     correlation of their CPC patent shares) and in product-market space (SIC, here 1 when two firms
     share a 4-digit SIC code and 0 otherwise),
  3. forms the two spillover pools, SPILLTECH = sum_j TECH_ij G_j and SPILLSIC = sum_j SIC_ij G_j,
  4. estimates the paper's four equations (market value, citation-weighted patents, production
     function, R&D intensity) with firm and year fixed effects, and
  5. turns the coefficients into the paper's marginal social and private returns to R&D.

Writes results/sample_counts.csv, descriptives.csv, proximity_summary.csv, main_estimates.csv,
returns.csv, coefficients_vs_bsv.png, and data/processed/spill_panel.csv.gz (used by over_time.py).

Usage (from the repository root):
    python src/spillovers.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import warnings

from statsmodels.discrete.discrete_model import NegativeBinomial, Poisson

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "results"

DELTA = 0.15           # R&D depreciation rate (BSV section 3.4, following Hall, Jaffe & Trajtenberg 2005)
GROWTH = 0.05          # pre-sample R&D growth for the starting stock R_0 / (g + delta) (Hall 1990 convention)
MIN_RD_YEARS = 4       # BSV keep firms with at least four observations
FIRST, LAST = 2013, 2024   # outcome years; 2010-2012 are burn-in for the R&D stocks
PATENT_LAST = 2020     # last filing year for the patent equation (later filings are still being granted)
PRESAMPLE = (2000, 2009)   # pre-sample patenting for the Blundell-Griffith-Van Reenen fixed effect
POLY = 6               # BSV approximate ln(1 + gamma G/A) with a sixth-order polynomial in G/A
GA_CAP = 0.99          # G/A is capped at its 99th percentile before the polynomial (my rule)
TRIM_Q = 0.005         # drop the top and bottom 0.5% of ln(Tobin's Q) as likely data errors (my rule)
FLOAT_JUMP = 50        # a public float 50x above or below the firm's median is a tagging-scale error (my rule)
MIN_SALES = 10         # estimation firms need median sales of at least $10 million (my rule; pools use all firms)
SIGMA = 0.5            # share of a rival-induced value loss that is lost output (BSV footnote 45)

# Bloom, Schankerman & Van Reenen (2013), baseline fixed-effects columns (Tables 3-6 and 9), for comparison
BSV = {("value", "ln_spilltech"): (0.381, 0.113), ("value", "ln_spillsic"): (-0.083, 0.032),
       ("patents", "ln_spilltech"): (0.468, 0.080), ("patents", "ln_spillsic"): (0.056, 0.037),
       ("production", "ln_spilltech"): (0.191, 0.046), ("production", "ln_spillsic"): (-0.005, 0.011),
       ("rd", "ln_spilltech"): (0.100, 0.076), ("rd", "ln_spillsic"): (0.083, 0.034)}


def load():
    fy = pd.read_csv(PROC / "firm_years.csv.gz", dtype={"cik": str, "sic": str})
    py = pd.read_csv(PROC / "patent_years.csv.gz", dtype={"cik": str})
    tech = pd.read_csv(PROC / "tech_shares.csv.gz", dtype={"cik": str})
    print(f"Loaded {len(fy):,} SEC firm-years, {len(py):,} firm patent-years, "
          f"technology shares for {tech['cik'].nunique():,} filers")
    return fy, py, tech


def rd_stocks(fy, tech, counts):
    """R&D stock G_t = R_t + (1 - delta) G_{t-1} for firms that patent and report R&D."""
    d = fy[fy["cik"].isin(set(tech["cik"]))]
    counts.append(("SEC filers with a patent-based technology position", d["cik"].nunique(),
                   fy["cik"].nunique() - d["cik"].nunique()))
    pos = d[d["rd"] > 0].groupby("cik")["year"].nunique()
    keep = pos[pos >= MIN_RD_YEARS].index
    counts.append((f"... reporting positive R&D in at least {MIN_RD_YEARS} fiscal years", len(keep),
                   d["cik"].nunique() - len(keep)))
    rows = []
    for cik, g in d[d["cik"].isin(keep) & d["rd"].notna()].groupby("cik"):
        r = g.set_index("year")["rd"].clip(lower=0)
        r = r.reindex(range(r.index.min(), r.index.max() + 1)).interpolate()   # fill isolated gaps
        stock = None
        for year, flow in r.items():
            stock = flow / (GROWTH + DELTA) if stock is None else flow + (1 - DELTA) * stock
            rows.append((cik, year, stock))
    g = pd.DataFrame(rows, columns=["cik", "year", "G"])
    print(f"R&D stocks: {g['cik'].nunique():,} firms, {len(g):,} firm-years")
    return g


def closeness(tech, firms, sic):
    """TECH (Jaffe uncentered correlation of CPC shares) and SIC (same 4-digit code) for the firm list.

    Two filers linked to the same CRSP firm (a company and the holding company that replaced it, such as
    Google Inc. and Alphabet) are the same firm, so their closeness is set to zero."""
    s = tech[tech["cik"].isin(firms)].pivot_table(index="cik", columns="cpc4", values="share", fill_value=0)
    s = s.reindex(firms).fillna(0).to_numpy()
    s = s / np.linalg.norm(s, axis=1, keepdims=True)
    tec = s @ s.T
    codes = sic.reindex(firms).fillna("none").to_numpy()
    sicm = ((codes[:, None] == codes[None, :]) & (codes[:, None] != "none")).astype(float)
    np.fill_diagonal(tec, 0)
    np.fill_diagonal(sicm, 0)
    link = pd.read_csv(PROC / "patent_bridge.csv", dtype={"cik": str})
    pos = {c: i for i, c in enumerate(firms)}
    for _, grp in link[link["cik"].isin(pos)].groupby("permco"):
        idx = [pos[c] for c in grp["cik"].unique()]
        for a in idx:
            for b in idx:
                if a != b:
                    tec[a, b] = sicm[a, b] = 0
    return tec, sicm


def build_panel(fy, py, tech, counts):
    """One row per sample firm-year with R&D stock, both spillover pools and the outcome variables."""
    g = rd_stocks(fy, tech, counts)
    firms = sorted(g["cik"].unique())
    sic = fy.sort_values("year").drop_duplicates("cik", keep="last").set_index("cik")["sic"].str[:4]
    tec, sicm = closeness(tech, firms, sic)
    iu = np.triu_indices(len(firms), 1)
    prox = pd.DataFrame([("firms", len(firms)), ("mean TECH over firm pairs", tec[iu].mean()),
                         ("mean SIC over firm pairs", sicm[iu].mean()),
                         ("correlation of TECH and SIC over pairs", np.corrcoef(tec[iu], sicm[iu])[0, 1]),
                         ("share of pairs with TECH > 0.5", (tec[iu] > 0.5).mean()),
                         ("share of same-SIC pairs with TECH < 0.1", (tec[iu][sicm[iu] == 1] < 0.1).mean()),
                         ("share of all 10-K R&D in 2023 done by these firms",
                          fy.loc[(fy["year"] == 2023) & fy["cik"].isin(firms), "rd"].sum()
                          / fy.loc[fy["year"] == 2023, "rd"].sum())],
                        columns=["statistic", "value"])
    prox.to_csv(OUT / "proximity_summary.csv", index=False, float_format="%.6f")
    print(prox.to_string(index=False))

    pools = []
    gw = g.pivot_table(index="year", columns="cik", values="G").reindex(columns=firms)
    # Robustness: pools built only from firms with an R&D stock in every year 2012-2024, so that firms
    # entering and leaving the SEC data do not move anyone's pool
    always = gw.loc[FIRST - 1:LAST].notna().all().to_numpy()
    counts.append((f"firms with an R&D stock in every year {FIRST - 1}-{LAST} (robustness pools)", int(always.sum()), 0))
    for year, row in gw.iterrows():
        vec = row.fillna(0).to_numpy()
        pools.append(pd.DataFrame({"cik": firms, "year": year, "spilltech": tec @ vec, "spillsic": sicm @ vec,
                                   "spilltech_bal": tec @ (vec * always), "spillsic_bal": sicm @ (vec * always)}))
    pools = pd.concat(pools)
    # Industry demand control: sales of all other SEC filers in the firm's 4-digit SIC that year
    s = fy.dropna(subset=["revenue"]).assign(sic4=lambda x: x["sic"].str[:4])
    tot = s.groupby(["sic4", "year"])["revenue"].sum().rename("sic_sales").reset_index()

    p = g.merge(pools, on=["cik", "year"]).merge(fy, on=["cik", "year"], how="left")
    p["sic4"] = p["sic"].str[:4]
    p = p.merge(tot, on=["sic4", "year"], how="left")
    p["indsales"] = p["sic_sales"] - p["revenue"].fillna(0)
    p = p.merge(py, on=["cik", "year"], how="left").fillna({"patents": 0, "cites": 0})
    pre = py[py["year"].between(*PRESAMPLE)].groupby("cik")[["cites", "patents"]].sum() / (PRESAMPLE[1] - PRESAMPLE[0] + 1)
    for c in ["cites", "patents"]:
        p[f"pre_{c}"] = p["cik"].map(pre[c]).fillna(0)
        p[f"ln_pre_{c}"] = np.log(p[f"pre_{c}"].where(p[f"pre_{c}"] > 0)).fillna(0)
        p[f"pre_zero_{c}"] = (p[f"pre_{c}"] == 0).astype(int)
    m = 1e6   # dollars -> $ millions
    for c in ["G", "spilltech", "spillsic", "indsales", "revenue", "rd", "assets", "liabilities", "ppe",
              "cogs", "sga", "float"]:
        p[c] = p[c] / m
    med = p.groupby("cik")["float"].transform("median")
    bad = (p["float"] / med > FLOAT_JUMP) | (med / p["float"] > FLOAT_JUMP)
    counts.append(("public floats dropped as scale errors (50x the firm's median)", int(bad.sum()), 0))
    p.loc[bad, "float"] = np.nan
    p["V"] = p["float"] + p["liabilities"]
    p["Q"] = p["V"] / p["assets"]
    p["costs"] = p["cogs"] + p["sga"].fillna(0)
    lag = p[["cik", "year", "G", "spilltech", "spillsic", "spilltech_bal", "spillsic_bal", "indsales", "assets", "revenue", "ppe", "costs"]].copy()
    lag["year"] += 1
    p = p.merge(lag, on=["cik", "year"], how="left", suffixes=("", "_l"))
    logs = {"ln_spilltech": "spilltech_l", "ln_spillsic": "spillsic_l", "ln_spilltech_bal": "spilltech_bal_l",
            "ln_spillsic_bal": "spillsic_bal_l", "ln_ind": "indsales",
            "ln_ind_l": "indsales_l", "ln_G": "G_l", "ln_Q": "Q", "ln_sales": "revenue", "ln_sales_l": "revenue_l",
            "ln_ppe": "ppe_l", "ln_costs": "costs_l"}
    for new, old in logs.items():
        p[new] = np.log(p[old].where(p[old] > 0))
    p["ln_rd_sales"] = np.log((p["rd"] / p["revenue"]).where((p["rd"] > 0) & (p["revenue"] > 0)))
    p["ga"] = p["G_l"] / p["assets_l"].where(p["assets_l"] > 0)
    p = p[p["year"].between(FIRST, LAST)]
    counts.append((f"firm-years {FIRST}-{LAST} with an R&D stock and spillover pools", len(p), 0))
    n0 = len(p)
    p = p[p.groupby("cik")["revenue"].transform("median") >= MIN_SALES]
    counts.append((f"... of firms with median sales of ${MIN_SALES} million or more", len(p), n0 - len(p)))
    p.to_csv(PROC / "spill_panel.csv.gz", index=False, compression="gzip", float_format="%.6g")
    print(f"Panel: {len(p):,} firm-years, {p['cik'].nunique():,} firms, {FIRST}-{LAST}")
    return p


def fe_ols(d, y, xs, fe=True):
    """OLS with firm and year fixed effects (within transformation), SEs clustered by firm."""
    d = d.dropna(subset=[y] + xs).copy()
    yd = pd.get_dummies(d["year"], prefix="yr", drop_first=True, dtype=float)
    X = pd.concat([d[xs], yd], axis=1)
    Y = d[y]
    if fe:
        X = X - X.groupby(d["cik"]).transform("mean")
        Y = Y - Y.groupby(d["cik"]).transform("mean")
        X = X.loc[:, X.abs().sum() > 1e-9]
    else:
        X = sm.add_constant(X)
    res = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cik"])[0]})
    return res, d


def value_terms(p):
    """Columns for the sixth-order polynomial in lagged R&D stock / assets."""
    cap = p["ga"].quantile(GA_CAP)
    ga = p["ga"].clip(upper=cap)
    for k in range(1, POLY + 1):
        p[f"ga{k}"] = ga ** k
    return [f"ga{k}" for k in range(1, POLY + 1)]


def record(rows, eq, spec, res, d, names):
    for v in names:
        if v in res.params:
            rows.append(dict(equation=eq, spec=spec, variable=v, coef=res.params[v], se=res.bse[v],
                             ci_low=res.params[v] - 1.96 * res.bse[v], ci_high=res.params[v] + 1.96 * res.bse[v],
                             p=res.pvalues[v], n_obs=int(res.nobs), n_firms=d["cik"].nunique()))


def main():
    warnings.simplefilter("ignore")   # statsmodels overflow warnings during likelihood search
    OUT.mkdir(exist_ok=True)
    counts = []
    fy, py, tech = load()
    p = build_panel(fy, py, tech, counts)
    spill = ["ln_spilltech", "ln_spillsic"]
    ind = ["ln_ind", "ln_ind_l"]
    rows = []

    # 1. Market value (BSV Table 3): ln Q on the G/A polynomial and the two lagged pools
    poly = value_terms(p)
    v = p.dropna(subset=["ln_Q"])
    lo, hi = v["ln_Q"].quantile([TRIM_Q, 1 - TRIM_Q])
    n0 = len(v)
    v = v[v["ln_Q"].between(lo, hi)]
    counts.append(("market-value firm-years after trimming 0.5% tails of ln Q", len(v), n0 - len(v)))
    specs = {"(1) pooled OLS": (spill, False), "(2) firm FE": (spill, True),
             "(3) firm FE, TECH only": (["ln_spilltech"], True), "(4) firm FE, SIC only": (["ln_spillsic"], True)}
    for spec, (xs, fe) in specs.items():
        res, d = fe_ols(v, "ln_Q", poly + xs + ind, fe)
        record(rows, "value", spec, res, d, xs + ["ga1"])
        if spec == "(2) firm FE":
            value_res, value_d = res, d

    # 2. Patents (BSV Table 4): negative binomial, pre-sample mean scaling for fixed effects.
    #    Started from Poisson estimates (the negative binomial does not converge from zero on these counts);
    #    the Poisson pseudo-ML estimates are kept as a robustness check.
    pt = p[(p["year"] <= PATENT_LAST)].dropna(subset=["ln_G", "ln_sales_l"] + spill).copy()
    yd = pd.get_dummies(pt["year"], prefix="yr", drop_first=True, dtype=float)
    sd = pd.get_dummies(pt["sic"].str[:2], prefix="sic2", drop_first=True, dtype=float)
    sd = sd.loc[:, sd.sum() >= 20]
    base = ["ln_G", "ln_spilltech", "ln_spillsic", "ln_sales_l"]
    groups = pd.factorize(pt["cik"])[0]
    for spec, dep, extra in [("(1) no fixed effect", "cites", []),
                             ("(2) pre-sample FE", "cites", ["ln_pre_cites", "pre_zero_cites"]),
                             ("(3) pre-sample FE, patent counts", "patents", ["ln_pre_patents", "pre_zero_patents"])]:
        X = sm.add_constant(pd.concat([pt[base + extra], yd, sd], axis=1))
        po = Poisson(pt[dep], X).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": groups})
        nb = NegativeBinomial(pt[dep], X).fit(start_params=np.append(po.params.to_numpy(), 0.5), method="newton",
                                              maxiter=100, disp=0, cov_type="cluster", cov_kwds={"groups": groups})
        print(f"  patents {spec}: negative binomial converged = {nb.mle_retvals['converged']}")
        record(rows, "patents", spec, nb, pt, base + extra[:1])
        record(rows, "patents", spec + ", Poisson", po, pt, base + extra[:1])
    counts.append((f"patent-equation firm-years {FIRST}-{PATENT_LAST}", len(pt), 0))

    # 3. Production function (BSV Table 5): ln sales on lagged capital, variable costs, R&D stock, pools
    prod_x = ["ln_ppe", "ln_costs", "ln_G"]
    for spec, (xs, fe) in {"(1) pooled OLS": (spill, False), "(2) firm FE": (spill, True),
                           "(3) firm FE, TECH only": (["ln_spilltech"], True)}.items():
        res, d = fe_ols(p, "ln_sales", prod_x + xs + ind, fe)
        record(rows, "production", spec, res, d, prod_x + xs)
        if spec == "(2) firm FE":
            prod_res, prod_d = res, d

    # Robustness for value and production: pools from firms present in every year
    bal = {"ln_spilltech_bal": "ln_spilltech", "ln_spillsic_bal": "ln_spillsic"}
    vb = v.drop(columns=spill).rename(columns=bal)
    res, d = fe_ols(vb, "ln_Q", poly + spill + ind)
    record(rows, "value", "(5) firm FE, pools from always-present firms", res, d, spill)
    res, d = fe_ols(p.drop(columns=spill).rename(columns=bal), "ln_sales", prod_x + spill + ind)
    record(rows, "production", "(4) firm FE, pools from always-present firms", res, d, prod_x + spill)

    # 4. R&D intensity (BSV Table 6)
    for spec, fe in {"(1) pooled OLS": False, "(2) firm FE": True}.items():
        res, d = fe_ols(p, "ln_rd_sales", spill + ind, fe)
        record(rows, "rd", spec, res, d, spill)

    est = pd.DataFrame(rows)
    est.to_csv(OUT / "main_estimates.csv", index=False, float_format="%.6f")
    print(est.to_string(index=False))

    # 5. Social and private returns (BSV equations 6.5-6.6, symmetric firms, at the median Y/G)
    yg = (prod_d["revenue"] / prod_d["G_l"]).median()
    phi1, phi2 = prod_res.params["ln_G"], prod_res.params["ln_spilltech"]
    cov = prod_res.cov_params()
    g3, g3se = value_res.params["ln_spillsic"], value_res.bse["ln_spillsic"]
    msr = yg * (phi1 + phi2)
    msr_se = yg * np.sqrt(cov.loc["ln_G", "ln_G"] + cov.loc["ln_spilltech", "ln_spilltech"]
                          + 2 * cov.loc["ln_G", "ln_spilltech"])
    mpr = yg * (phi1 - SIGMA * g3)
    mpr_se = yg * np.sqrt(cov.loc["ln_G", "ln_G"] + SIGMA ** 2 * g3se ** 2)   # the two equations treated as independent
    ret = pd.DataFrame([dict(source="This study, 2013-2024", median_Y_over_G=yg, phi1_own_rd=phi1,
                             phi2_spilltech=phi2, gamma3_spillsic_value=g3, social_return=msr, social_se=msr_se,
                             private_return=mpr, private_se=mpr_se, ratio=msr / mpr),
                        dict(source="BSV symmetric case (section 6.5.2)", median_Y_over_G=2.48, phi1_own_rd=0.043,
                             phi2_spilltech=0.191, gamma3_spillsic_value=-0.083, social_return=0.58,
                             private_return=0.208, ratio=0.58 / 0.208),
                        dict(source="Lucking, Bloom & Van Reenen 2019, 1985-2015", median_Y_over_G=2.345,
                             phi1_own_rd=0.015, phi2_spilltech=0.231, gamma3_spillsic_value=-0.086,
                             social_return=0.577, private_return=0.136, ratio=0.577 / 0.136)])
    for c in ["social", "private"]:
        ret[f"{c}_ci_low"] = ret[f"{c}_return"] - 1.96 * ret[f"{c}_se"]
        ret[f"{c}_ci_high"] = ret[f"{c}_return"] + 1.96 * ret[f"{c}_se"]
    ret.to_csv(OUT / "returns.csv", index=False, float_format="%.6f")
    print(ret.T.to_string())

    # Descriptive statistics in the paper's Table 2 layout ($ millions, nominal)
    desc = {"Tobin's Q (V/A)": v["Q"], "Market value V": v["V"], "R&D stock G": p["G"], "R&D stock / assets": p["ga"],
            "R&D flow R": p["rd"], "SPILLTECH": p["spilltech_l"], "SPILLSIC": p["spillsic_l"],
            "Patents filed (2013-2020)": pt["patents"],
            "Forward citations to patents filed (2013-2020)": pt["cites"], "Sales Y": p["revenue"],
            "Sales / R&D stock": prod_d["revenue"] / prod_d["G_l"], "Total assets A": p["assets"]}
    pd.DataFrame([dict(variable=k, median=s.median(), mean=s.mean(), sd=s.std(), n=int(s.notna().sum()))
                  for k, s in desc.items()]).to_csv(OUT / "descriptives.csv", index=False, float_format="%.3f")
    variation(v)
    pd.DataFrame(counts, columns=["step", "kept", "dropped"]).to_csv(OUT / "sample_counts.csv", index=False)
    print(pd.DataFrame(counts, columns=["step", "kept", "dropped"]).to_string(index=False))
    figure(est)


def variation(v):
    """How much each variable moves within a firm once firm and year averages are removed (market-value sample)."""
    rows, within = [], {}
    for c in ["ln_spilltech", "ln_spillsic", "ln_Q", "ln_G"]:
        d = v.dropna(subset=[c])
        w = d[c] - d.groupby("cik")[c].transform("mean")
        within[c] = w - w.groupby(d["year"]).transform("mean")
        rows.append(dict(variable=c, total_sd=d[c].std(), within_firm_sd=w.std(), within_firm_net_of_year_sd=within[c].std()))
    both = pd.concat([within["ln_spilltech"], within["ln_spillsic"]], axis=1).dropna()
    rows.append(dict(variable="corr(ln_spilltech, ln_spillsic), levels", total_sd=v[["ln_spilltech", "ln_spillsic"]].corr().iloc[0, 1]))
    rows.append(dict(variable="corr(ln_spilltech, ln_spillsic), within firm net of year", total_sd=both.corr().iloc[0, 1]))
    pd.DataFrame(rows).to_csv(OUT / "identifying_variation.csv", index=False, float_format="%.6f")
    print(pd.DataFrame(rows).to_string(index=False))


def figure(est):
    """Side by side: the paper's fixed-effects coefficients and this study's, with 95% intervals."""
    main_spec = {"value": "(2) firm FE", "patents": "(2) pre-sample FE", "production": "(2) firm FE", "rd": "(2) firm FE"}
    labels = {"value": "Market value", "patents": "Patents (cites)", "production": "Sales (productivity)",
              "rd": "R&D / sales"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, var, title in zip(axes, ["ln_spilltech", "ln_spillsic"],
                              ["Technology spillovers, ln SPILLTECH", "Product rivals' R&D, ln SPILLSIC"]):
        for i, eq in enumerate(main_spec):
            b, s = BSV[(eq, var)]
            ax.errorbar(b, i + 0.15, xerr=1.96 * s, fmt="s", color="#888888", capsize=3,
                        label="BSV 1981-2001" if i == 0 else None)
            r = est[(est.equation == eq) & (est.spec == main_spec[eq]) & (est.variable == var)].iloc[0]
            ax.errorbar(r.coef, i - 0.15, xerr=1.96 * r.se, fmt="o", color="#1f5f99", capsize=3,
                        label="This study 2013-2024" if i == 0 else None)
        ax.axvline(0, color="black", lw=0.8)
        ax.set_title(title, fontsize=10)
        ax.set_yticks(range(4))
        ax.set_yticklabels([labels[e] for e in main_spec])
        ax.invert_yaxis()
    axes[1].legend(fontsize=8, loc="upper left")
    fig.supxlabel("Coefficient (elasticity) with 95% interval", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "coefficients_vs_bsv.png", dpi=150)
    print("Wrote results/coefficients_vs_bsv.png")


if __name__ == "__main__":
    main()
