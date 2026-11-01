"""Extension: have R&D spillovers changed since 2013? Plus the table of named firms.

Lucking, Bloom & Van Reenen (2019) let the paper's coefficients vary by five-year block from 1985 to
2015 and found spillovers in the 2010s as large as in the 1980s. This script carries that test forward:
the market-value and production-function equations of src/spillovers.py are re-estimated with the
spillover coefficients (and, in the production function, the own-R&D coefficient) allowed to differ
across three four-year blocks, 2013-2016, 2017-2020 and 2021-2024, and the marginal social and private
returns to R&D are recomputed for each block.

It also rebuilds the paper's Appendix Table A1 (closeness of IBM, Apple, Motorola and Intel) on
2000-2022 patents and today's SIC codes, and lists the spillover pools of well-known R&D spenders.

Reads data/processed/spill_panel.csv.gz (written by src/spillovers.py), firm_years.csv.gz and
tech_shares.csv.gz. Writes results/blocks_estimates.csv, blocks_returns.csv, named_closeness.csv,
named_firms.csv and blocks_coefficients.png.

Usage (from the repository root, after src/spillovers.py):
    python src/over_time.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "results"

BLOCKS = [(2013, 2016), (2017, 2020), (2021, 2024)]
POLY, GA_CAP, TRIM_Q, SIGMA = 6, 0.99, 0.005, 0.5   # same rules as src/spillovers.py
NAMED_YEAR = 2023      # year for the table of named firms
# SEC CIKs. The four firms of BSV Appendix Table A1, then other large R&D spenders.
A1 = {"IBM": "51143", "Apple": "320193", "Motorola Solutions": "68505", "Intel": "50863"}
NAMED = {"Alphabet": "1652044", "Microsoft": "789019", "Apple": "320193", "Meta Platforms": "1326801",
         "Intel": "50863", "Johnson & Johnson": "200406", "Merck": "310158", "Pfizer": "78003",
         "Eli Lilly": "59478", "Nvidia": "1045810", "Qualcomm": "804328", "Cisco": "858877", "IBM": "51143",
         "Advanced Micro Devices": "2488", "Ford": "37996", "General Motors": "1467858", "Tesla": "1318605",
         "Boeing": "12927", "Medtronic": "1613103", "Micron": "723125"}
# BSV Appendix Table A1 values (Compustat segments for SIC, 1970-1999 patents for TECH)
BSV_A1 = {("IBM", "Apple"): (0.65, 0.64), ("IBM", "Motorola Solutions"): (0.01, 0.46), ("IBM", "Intel"): (0.01, 0.76),
          ("Apple", "Motorola Solutions"): (0.02, 0.17), ("Apple", "Intel"): (0.00, 0.47),
          ("Motorola Solutions", "Intel"): (0.34, 0.46)}


def fe_ols(d, y, xs):
    """OLS with firm and year fixed effects (within transformation), SEs clustered by firm."""
    d = d.dropna(subset=[y] + xs).copy()
    X = pd.concat([d[xs], pd.get_dummies(d["year"], prefix="yr", drop_first=True, dtype=float)], axis=1)
    X = X - X.groupby(d["cik"]).transform("mean")
    Y = d[y] - d[y].groupby(d["cik"]).transform("mean")
    X = X.loc[:, X.abs().sum() > 1e-9]
    return sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cik"])[0]}), d


def interact(p, cols):
    """Split each column into one copy per block (zero outside the block)."""
    names = []
    for lo, hi in BLOCKS:
        inside = p["year"].between(lo, hi).astype(float)
        for c in cols:
            p[f"{c}_{lo}"] = p[c] * inside
            names.append(f"{c}_{lo}")
    return names


def blocks(p):
    """Block-specific coefficients for the value and production equations and the implied returns."""
    ga = p["ga"].clip(upper=p["ga"].quantile(GA_CAP))
    poly = []
    for k in range(1, POLY + 1):
        p[f"ga{k}"] = ga ** k
        poly.append(f"ga{k}")
    ind = ["ln_ind", "ln_ind_l"]
    v = p.dropna(subset=["ln_Q"])
    lo, hi = v["ln_Q"].quantile([TRIM_Q, 1 - TRIM_Q])
    v = v[v["ln_Q"].between(lo, hi)].copy()
    vx = interact(v, ["ln_spilltech", "ln_spillsic"])
    vres, vd = fe_ols(v, "ln_Q", poly + vx + ind)
    px = interact(p, ["ln_spilltech", "ln_spillsic", "ln_G"])
    pres, pd_ = fe_ols(p, "ln_sales", ["ln_ppe", "ln_costs"] + px + ind)

    rows, rets = [], []
    for eq, res, d, xs in [("value", vres, vd, vx), ("production", pres, pd_, px)]:
        for x in xs:
            var, lo = x.rsplit("_", 1)
            rows.append(dict(equation=eq, block=f"{lo}-{int(lo) + 3}", variable=var, coef=res.params[x],
                             se=res.bse[x], p=res.pvalues[x], n_obs=int(res.nobs), n_firms=d["cik"].nunique()))
    for lo, hi in BLOCKS:
        sub = pd_[pd_["year"].between(lo, hi)]
        yg = (sub["revenue"] / sub["G_l"]).median()
        a, b, c = f"ln_G_{lo}", f"ln_spilltech_{lo}", f"ln_spillsic_{lo}"
        cov = pres.cov_params()
        phi1, phi2, g3 = pres.params[a], pres.params[b], vres.params[c]
        msr = yg * (phi1 + phi2)
        mpr = yg * (phi1 - SIGMA * g3)
        rets.append(dict(block=f"{lo}-{hi}", median_Y_over_G=yg, phi1_own_rd=phi1, phi2_spilltech=phi2,
                         gamma3_spillsic_value=g3, social_return=msr,
                         social_se=yg * np.sqrt(cov.loc[a, a] + cov.loc[b, b] + 2 * cov.loc[a, b]),
                         private_return=mpr, private_se=yg * np.sqrt(cov.loc[a, a] + SIGMA ** 2 * vres.bse[c] ** 2),
                         ratio=msr / mpr))
    # Wald tests that the spillover coefficients are equal across the three blocks
    tests = []
    for eq, res, var in [("value", vres, "ln_spilltech"), ("value", vres, "ln_spillsic"),
                         ("production", pres, "ln_spilltech"), ("production", pres, "ln_G")]:
        names = [f"{var}_{lo}" for lo, _ in BLOCKS]
        R = np.zeros((2, len(res.params)))
        idx = [list(res.params.index).index(n) for n in names]
        R[0, idx[0]], R[0, idx[1]] = 1, -1
        R[1, idx[0]], R[1, idx[2]] = 1, -1
        w = res.wald_test(R, scalar=True)
        tests.append(dict(equation=eq, block="equal across blocks (Wald)", variable=var,
                          coef=float(w.statistic), se=np.nan, p=float(w.pvalue), n_obs=int(res.nobs),
                          n_firms=np.nan))
    rets = pd.DataFrame(rets)
    for c in ["social", "private"]:
        rets[f"{c}_ci_low"] = rets[f"{c}_return"] - 1.96 * rets[f"{c}_se"]
        rets[f"{c}_ci_high"] = rets[f"{c}_return"] + 1.96 * rets[f"{c}_se"]
    est = pd.DataFrame(rows + tests)
    est["n_firms"] = est["n_firms"].astype("Int64")
    return est, rets


def named_tables(p):
    """BSV Table A1 rebuilt, and the spillover pools of well-known R&D spenders."""
    fy = pd.read_csv(PROC / "firm_years.csv.gz", dtype={"cik": str, "sic": str})
    tech = pd.read_csv(PROC / "tech_shares.csv.gz", dtype={"cik": str})
    sic = fy.sort_values("year").drop_duplicates("cik", keep="last").set_index("cik")["sic"].str[:4]
    s = tech.pivot_table(index="cik", columns="cpc4", values="share", fill_value=0)
    s = s.div(np.sqrt((s ** 2).sum(axis=1)), axis=0)
    rows = []
    names = list(A1)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ta = float(s.loc[A1[a]] @ s.loc[A1[b]])
            bsv_sic, bsv_tech = BSV_A1[(a, b)]
            rows.append(dict(firm_a=a, firm_b=b, sic_a=sic.get(A1[a]), sic_b=sic.get(A1[b]),
                             SIC_now=float(sic.get(A1[a]) == sic.get(A1[b])), TECH_now=ta,
                             SIC_bsv=bsv_sic, TECH_bsv=bsv_tech))
    a1 = pd.DataFrame(rows)

    # Worked example: Intel's contribution to Apple's technology pool in the year after NAMED_YEAR
    full = pd.read_csv(PROC / "spill_panel.csv.gz", dtype={"cik": str})
    apple = full[(full["cik"] == A1["Apple"]) & (full["year"] == NAMED_YEAR + 1)].iloc[0]
    intel = full[(full["cik"] == A1["Intel"]) & (full["year"] == NAMED_YEAR)].iloc[0]
    t = float(s.loc[A1["Apple"]] @ s.loc[A1["Intel"]])
    pd.DataFrame([dict(year_of_pool=NAMED_YEAR + 1, TECH_apple_intel=t, intel_rd_stock_bn=intel["G"] / 1e3,
                       contribution_bn=t * intel["G"] / 1e3, apple_spilltech_bn=apple["spilltech_l"] / 1e3,
                       intel_share_of_pool=t * intel["G"] / apple["spilltech_l"])]).to_csv(
        OUT / "worked_example.csv", index=False, float_format="%.6f")

    # Named firms: own R&D, pools, and nearest technology neighbor among firms in the same year's sample
    # (other filers of the same CRSP firm, such as a predecessor company, are not neighbors)
    yr = p[p["year"] == NAMED_YEAR].set_index("cik")
    ss = s.reindex(sorted(yr.index)).dropna()
    nm = fy.sort_values("year").drop_duplicates("cik", keep="last").set_index("cik")["name"]
    link = pd.read_csv(PROC / "patent_bridge.csv", dtype={"cik": str})
    permcos = link.groupby("cik")["permco"].apply(set)
    out = []
    for label, cik in NAMED.items():
        if cik not in ss.index:
            print(f"  {label}: not in the {NAMED_YEAR} sample")
            continue
        same = [c for c in ss.index if permcos.get(c, set()) & permcos.get(cik, set())]
        sim = (ss @ ss.loc[cik]).drop(same).sort_values(ascending=False)
        rivals = int(((p["year"] == NAMED_YEAR) & (p["sic4"] == yr.loc[cik, "sic4"])).sum()) - 1
        out.append(dict(firm=label, sic4=yr.loc[cik, "sic4"], rd_flow_bn=yr.loc[cik, "rd"] / 1e3,
                        rd_stock_bn=yr.loc[cik, "G"] / 1e3, spilltech_bn=yr.loc[cik, "spilltech_l"] / 1e3,
                        spillsic_bn=yr.loc[cik, "spillsic_l"] / 1e3, same_sic_rivals=rivals,
                        nearest_tech_neighbor=nm.get(sim.index[0]), nearest_TECH=sim.iloc[0],
                        firms_with_TECH_over_half=int((sim > 0.5).sum())))
    return a1, pd.DataFrame(out).sort_values("rd_flow_bn", ascending=False)


def figure(est):
    sel = est[est["block"].str.match(r"^\d{4}-\d{4}$")]
    panels = [("value", "ln_spilltech", "Market value on ln SPILLTECH"),
              ("value", "ln_spillsic", "Market value on ln SPILLSIC"),
              ("production", "ln_spilltech", "Sales on ln SPILLTECH")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    for ax, (eq, var, title) in zip(axes, panels):
        r = sel[(sel.equation == eq) & (sel.variable == var)]
        x = np.arange(len(r))
        ax.errorbar(x, r["coef"], yerr=1.96 * r["se"], fmt="o", color="#1f5f99", capsize=4)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(r["block"], fontsize=8)
        ax.set_title(title, fontsize=10)
    axes[0].set_ylabel("Coefficient with 95% interval", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "blocks_coefficients.png", dpi=150)
    print("Wrote results/blocks_coefficients.png")


def main():
    p = pd.read_csv(PROC / "spill_panel.csv.gz", dtype={"cik": str, "sic": str, "sic4": str})
    print(f"Loaded spill_panel: {len(p):,} firm-years, {p['cik'].nunique():,} firms")
    est, rets = blocks(p)
    est.to_csv(OUT / "blocks_estimates.csv", index=False, float_format="%.6f")
    rets.to_csv(OUT / "blocks_returns.csv", index=False, float_format="%.6f")
    print(est.to_string(index=False))
    print(rets.T.to_string())
    a1, named = named_tables(p)
    a1.to_csv(OUT / "named_closeness.csv", index=False, float_format="%.3f")
    named.to_csv(OUT / "named_firms.csv", index=False, float_format="%.3f")
    print(a1.to_string(index=False))
    print(named.to_string(index=False))
    figure(est)


if __name__ == "__main__":
    main()
