"""Build the firm-year panel for the spillover regressions: accounts, market value and patents.

Four public sources are joined, firm by firm:

  Accounts. The SEC Financial Statement Data Sets (FSDS), one zip per quarter, 2011q3 to 2026q2. Only
  10-K filings, consolidated full-year US-dollar values of standard us-gaap tags. A fiscal year ending
  July to December belongs to that calendar year, one ending January to June to the year before.
  When a fiscal year appears in two filings, the filing in which it is the current year wins.

  Market value. The public float (dei:EntityPublicFloat) that every 10-K reports on its cover page: the
  market value of the shares held by non-affiliates, measured at the end of the second fiscal quarter.
  It comes from the SEC's XBRL company-facts data, through a public mirror of that bulk file. Each value
  carries its SEC accession number and is joined to the 10-K it appeared on.

  Patents. Kogan, Papanikolaou, Seru & Stoffman (KPSS, 2017; data extended to 2025) assign every US
  patent owned by a listed firm to that firm's CRSP identifier (permco), with filing date, forward
  citations and CPC technology codes. CRSP identifiers are not public, so each permco is linked to an
  SEC filer (CIK) through the patents' disambiguated assignee names in PatentsView (USPTO, 12/31/2024
  release), matched to every name the filer has used on a 10-K.

  Technology position. Each firm's share of its 2000-2022 patents in each CPC subclass (about 650
  fields, close in coarseness to the 426 USPTO classes that Bloom, Schankerman and Van Reenen used).

Raw files (about 6 GB) are not committed; missing ones are downloaded into data/raw/. The outputs are
committed so that the analysis runs offline:
    data/processed/firm_years.csv.gz     one row per filer and fiscal year, 2010-2025
    data/processed/patent_years.csv.gz   patents and citations per filer and filing year, 2000-2022
    data/processed/tech_shares.csv.gz    each filer's share of patents by CPC subclass, 2000-2022
    data/processed/patent_bridge.csv     permco -> CIK links and the names that made them
    results/build_counts.csv             what was loaded, kept and dropped at each step

Usage (from the repository root):
    python src/build_panel.py
"""

import re
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "results"

YEARS = range(2010, 2026)                     # fiscal years covered by 10-Ks filed 2011q3-2026q2
QUARTERS = [f"{y}q{q}" for y in range(2011, 2027) for q in (1, 2, 3, 4)][2:-2]
PATENT_YEARS = range(2000, 2023)              # filing years used for technology position and the bridge
FSDS = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/{q}.zip"
KPSS = ("https://raw.githubusercontent.com/KPSS2017/"
        "Technological-Innovation-Resource-Allocation-and-Growth-Extended-Data/master/{f}")
PV = "https://zenodo.org/api/records/15783125/files/{f}/content"   # PatentsView 12/31/2024, CC-BY 4.0
FLOAT = ("https://huggingface.co/datasets/DenyTranDFW/edgar_xbrl_companyfacts/resolve/main/"
         "EntityPublicFloat.parquet")                               # mirror of SEC companyfacts, dei facts
HEADERS = {"User-Agent": "Brendyn Beasley research 83249437+brendynbeasley@users.noreply.github.com"}

DURATION = {  # tag -> measure, full-year (qtrs = 4) values
    "Revenues": "revenue", "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "RevenueFromContractWithCustomerIncludingAssessedTax": "revenue", "SalesRevenueNet": "revenue",
    "SalesRevenueGoodsNet": "revenue",
    "ResearchAndDevelopmentExpense": "rd",
    "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost": "rd",
    "CostOfRevenue": "cogs", "CostOfGoodsAndServicesSold": "cogs", "CostOfGoodsSold": "cogs",
    "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization": "cogs",
    "SellingGeneralAndAdministrativeExpense": "sga",
    "OperatingIncomeLoss": "opinc",
}
INSTANT = {  # tag -> measure, balance-sheet (qtrs = 0) values
    "Assets": "assets", "Liabilities": "liabilities",
    "LiabilitiesAndStockholdersEquity": "liab_equity",
    "StockholdersEquity": "equity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "equity_nci",
    "PropertyPlantAndEquipmentNet": "ppe",
    "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization": "ppe",
}
# Hand-checked links for the largest 2023 R&D spenders that name matching misses, because the listed
# parent's name differs from the subsidiary that holds the patents (permco -> SEC CIKs)
MANUAL_LINKS = {45483: ["1652044"],              # Google LLC patents -> Alphabet Inc. (parent since 2015)
                9833: ["1571996"],               # Dell Products L.P. -> Dell Technologies Inc.
                37731: ["1058057", "1835632"]}   # Marvell International Ltd. -> both Marvell parent filers
MINOR_LINK = 0.5   # a filer must match at least half as many of a permco's patents as its best filer (my rule)
# Legal-form words dropped from the end of names before matching (judgment list)
SUFFIXES = {"INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "LTD", "LIMITED", "LLC", "LP",
            "PLC", "NV", "SA", "AG", "SE", "AB", "ASA", "HOLDINGS", "HOLDING", "GROUP", "THE"}


def fetch(url, path):
    """Return path, downloading url there first (via a temporary name) if it is missing."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  downloading {path.name} ...")
        time.sleep(0.3)
        r = requests.get(url, headers=HEADERS, timeout=3600)
        if r.status_code != 200 or len(r.content) < 1000:
            raise SystemExit(f"download failed ({r.status_code}): {url}")
        tmp = path.with_suffix(path.suffix + ".part")
        tmp.write_bytes(r.content)
        tmp.rename(path)
    return path


def normalize(name):
    """Upper case, no punctuation, no trailing legal-form words: 'Apple Inc.' -> 'APPLE'."""
    if not isinstance(name, str):
        return ""
    s = name.upper().split(" /")[0]
    s = re.sub(r"/[A-Z]{1,4}/?\s*$", "", s).replace("&", " AND ")   # SEC state tags: 'QUALCOMM INC/DE'
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    words = s.split()
    while words and words[-1] in SUFFIXES:
        words.pop()
    if words and words[0] == "THE":
        words = words[1:]
    return " ".join(words)


def read_quarter(q):
    """10-K headers and the tagged values this study uses, from one FSDS quarter."""
    with zipfile.ZipFile(fetch(FSDS.format(q=q), RAW / "sec" / f"{q}.zip")) as z:
        sub = pd.read_csv(z.open("sub.txt"), sep="\t", dtype=str, usecols=[
            "adsh", "cik", "name", "former", "sic", "countryba", "form", "period", "filed"])
        sub = sub[sub["form"] == "10-K"]
        header = z.open("num.txt").readline().decode().strip().split("\t")
        cols = ["adsh", "tag", "version", "ddate", "qtrs", "uom", "coreg", "value"]
        cols += ["segments"] if "segments" in header else []
        keep = set(sub["adsh"])
        parts = []
        for c in pd.read_csv(z.open("num.txt"), sep="\t", dtype=str, usecols=cols,
                             chunksize=2_000_000, quoting=3, on_bad_lines="skip"):
            dur = c["tag"].isin(DURATION) & (c["qtrs"] == "4")
            ins = c["tag"].isin(INSTANT) & (c["qtrs"] == "0")
            c = c[(dur | ins) & (c["uom"] == "USD") & c["coreg"].isna()
                  & c["version"].str.startswith("us-gaap") & c["adsh"].isin(keep)]
            if "segments" in c:
                c = c[c["segments"].isna()]
            parts.append(c[["adsh", "tag", "ddate", "value"]])
    num = pd.concat(parts).merge(sub[["adsh", "cik", "period", "filed"]], on="adsh")
    print(f"  {q}: {len(sub):,} 10-K filings, {len(num):,} values kept")
    return sub, num


def fiscal_year(dates):
    """The SEC frames rule: a year ending January-June belongs to the previous calendar year."""
    d = pd.to_datetime(dates, format="%Y%m%d", errors="coerce")
    return d.dt.year - (d.dt.month <= 6).astype(int)


def sec_accounts(counts):
    """Firm-year accounts, the 10-K behind each, each filer's latest SIC code, and its names."""
    subs, nums = zip(*[read_quarter(q) for q in QUARTERS])
    sub, d = pd.concat(subs, ignore_index=True), pd.concat(nums, ignore_index=True)
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    d = d.dropna(subset=["value"])
    end = pd.to_datetime(d["ddate"], format="%Y%m%d", errors="coerce")
    period = pd.to_datetime(d["period"], format="%Y%m%d", errors="coerce")
    d["year"] = fiscal_year(d["ddate"])
    d["current"] = ((end - period).abs().dt.days <= 31).astype(int)
    d["measure"] = d["tag"].map(DURATION | INSTANT)
    # Largest value among a measure's tags within a filing, then the preferred filing per firm-year
    per = d.groupby(["cik", "year", "measure", "adsh", "current", "filed", "ddate"])["value"].max().reset_index()
    best = per.sort_values(["current", "ddate", "filed"]).drop_duplicates(["cik", "year", "measure"], keep="last")
    panel = best.pivot_table(index=["cik", "year"], columns="measure", values="value").reset_index()
    # Total liabilities, where not tagged, as total liabilities and equity minus equity
    eq = panel["equity_nci"].fillna(panel["equity"])
    panel["liabilities"] = panel["liabilities"].fillna(panel["liab_equity"] - eq)
    n0 = len(panel)
    panel = panel[panel["year"].isin(YEARS) & panel["assets"].notna()]
    counts.append(("SEC firm-years with total assets, fiscal 2010-2025", len(panel), n0 - len(panel)))
    info = sub.sort_values("filed").drop_duplicates("cik", keep="last")[["cik", "name", "sic", "countryba"]]
    panel = panel.merge(info, on="cik", how="left")
    # The 10-K in which each fiscal year is the current year (used to place each public float)
    sub["year"] = fiscal_year(sub["period"])
    filings = sub[["adsh", "cik", "year"]].drop_duplicates("adsh")
    names = pd.concat([sub[["cik", "name"]], sub[["cik", "former"]].rename(columns={"former": "name"})])
    names["key"] = names["name"].map(normalize)
    names = names[names["key"].str.len() >= 2].drop_duplicates(["cik", "key"])
    print(f"SEC: {len(panel):,} firm-years, {panel['cik'].nunique():,} filers, {len(names):,} distinct name keys")
    return panel, filings, names


def public_float(filings, counts):
    """Public float reported on each 10-K cover, placed in the fiscal year of that 10-K."""
    f = pd.read_parquet(fetch(FLOAT, RAW / "float" / "EntityPublicFloat.parquet"),
                        columns=["accn", "form", "unit", "val_dec", "source_folder", "end"])
    n0 = len(f)
    f = f[f["form"].isin(["10-K", "10-K/A"]) & (f["unit"] == "USD")].copy()
    f["cik"] = f["source_folder"].str.extract(r"CIK0*(\d+)_", expand=False)
    f["float"] = pd.to_numeric(f["val_dec"].astype(str), errors="coerce")
    f = f.merge(filings.rename(columns={"adsh": "accn"}), on=["accn", "cik"], how="inner")
    f = f[f["float"] > 0].sort_values("end").drop_duplicates(["cik", "year"], keep="last")
    counts.append(("Public-float facts matched to a 10-K in the FSDS", len(f), n0 - len(f)))
    print(f"Public float: {len(f):,} firm-years from {n0:,} facts")
    return f[["cik", "year", "float"]]


def patents(counts):
    """KPSS patents filed 2000-2022 with filing year, citations, permco, CPC subclasses, assignee name."""
    k = pd.read_csv(fetch(KPSS.format(f="KPSS_2025.zip"), RAW / "patents" / "KPSS_2025.zip"),
                    usecols=["patent_num", "filing_date", "cites"])
    k["fyear"] = k["filing_date"] // 10000
    n0 = len(k)
    k = k[k["fyear"].isin(PATENT_YEARS)]
    counts.append(("KPSS patents filed 2000-2022 (of all years)", len(k), n0 - len(k)))
    n0 = len(k)
    m = pd.read_csv(fetch(KPSS.format(f="Match_patent_permco_permno_2025.zip"),
                          RAW / "patents" / "Match_patent_permco_permno_2025.zip"),
                    usecols=["patent_num", "permco"]).drop_duplicates("patent_num")
    k = k.merge(m, on="patent_num", how="inner")
    counts.append(("... with a permco", len(k), n0 - len(k)))
    c = pd.read_csv(fetch(KPSS.format(f="Match_patent_cpc_2025.zip"), RAW / "patents" / "Match_patent_cpc_2025.zip"))
    c = c[c["patent_num"].isin(set(k["patent_num"]))].dropna(subset=["cpc"])
    c["cpc4"] = c["cpc"].str.split(";").map(lambda codes: sorted({x.strip()[:4] for x in codes if len(x.strip()) >= 4}))
    k = k.merge(c[["patent_num", "cpc4"]], on="patent_num", how="left")
    path = fetch(PV.format(f="g_assignee_disambiguated.tsv.zip"), RAW / "patents" / "g_assignee_disambiguated.tsv.zip")
    a = pd.read_csv(path, sep="\t", dtype=str, usecols=["patent_id", "assignee_sequence",
                                                        "disambig_assignee_organization"])
    a = a[a["assignee_sequence"] == "0"]
    a["patent_num"] = pd.to_numeric(a["patent_id"], errors="coerce")
    a = a.dropna(subset=["patent_num"]).astype({"patent_num": "int64"})
    k = k.merge(a[["patent_num", "disambig_assignee_organization"]], on="patent_num", how="left")
    k["key"] = k["disambig_assignee_organization"].map(normalize)
    print(f"KPSS: {len(k):,} patents filed 2000-2022 at {k['permco'].nunique():,} listed firms; "
          f"{k['cpc4'].notna().mean():.1%} have CPC codes, {k['key'].str.len().gt(0).mean():.1%} an assignee name")
    return k


def vote(hits, total, method):
    """Patents per (permco, CIK) pair among name matches."""
    v = (hits.groupby(["permco", "cik"]).agg(matched=("patent_num", "nunique"),
                                             assignee=("disambig_assignee_organization", "first"),
                                             sec_name=("name", "first")).reset_index())
    v = v.join(total, on="permco")
    v["method"] = method
    return v


def bridge(k, names, panel, counts):
    """Link each permco to the SEC filers whose names match its patents' assignee names."""
    total = k.groupby("permco")["patent_num"].nunique().rename("permco_patents")
    exact = vote(k.merge(names[["cik", "key", "name"]], on="key", how="inner"), total, "exact")
    n0 = len(exact)
    # An exact-name link needs at least 3 patents or 10% of the permco's patents
    exact = exact[(exact["matched"] >= 3) | (exact["matched"] >= 0.1 * exact["permco_patents"])]
    counts.append(("permco-CIK links by exact name (>= 3 patents or 10%)", len(exact), n0 - len(exact)))
    # Second pass for permcos still unlinked: the filer's name is the leading words of the assignee's
    # ("ORACLE" in "ORACLE INTERNATIONAL"); the longest such name wins and must cover 25% of the patents.
    rest = k[~k["permco"].isin(exact["permco"]) & k["key"].str.contains(" ")]
    keys = rest[["key"]].drop_duplicates()
    keys["prefix"] = keys["key"].str.split().map(lambda w: [" ".join(w[:i]) for i in range(len(w) - 1, 0, -1)])
    keys = keys.explode("prefix")
    keys = keys[keys["prefix"].str.len() >= 5].merge(names[["key", "cik", "name"]].rename(columns={"key": "prefix"}),
                                                    on="prefix")
    keys["words"] = keys["prefix"].str.count(" ")
    keys = keys[keys["words"] == keys.groupby("key")["words"].transform("max")]
    prefix = vote(rest.merge(keys[["key", "cik", "name"]], on="key"), total, "leading words")
    n0 = len(prefix)
    prefix = prefix[(prefix["matched"] >= 10) & (prefix["matched"] >= 0.25 * prefix["permco_patents"])]
    counts.append(("permco-CIK links by leading words (>= 10 patents and 25%)", len(prefix), n0 - len(prefix)))
    # A permco's technology position is given to every filer linked to it, so a filer that matches only a
    # sliver of a permco's patents (PTC Therapeutics on 3 of Amgen's) must not inherit the whole portfolio:
    # each link needs at least half the matches of that permco's best-matched filer
    named = pd.concat([exact, prefix], ignore_index=True)
    n0 = len(named)
    named = named[named["matched"] >= MINOR_LINK * named.groupby("permco")["matched"].transform("max")]
    counts.append(("... links kept with at least half the matches of the permco's best filer", len(named),
                   n0 - len(named)))
    manual = pd.DataFrame([dict(permco=pc, cik=c, matched=0, method="manual") for pc, ciks in MANUAL_LINKS.items()
                           for c in ciks])
    manual = manual.join(total, on="permco")
    counts.append(("permco-CIK links added by hand (parents of patent-holding subsidiaries)", len(manual), 0))
    votes = pd.concat([named, manual], ignore_index=True)
    # Each permco-year goes to one filer: the linked filer with accounts nearest that year, ties to more matches
    py = k[["permco", "fyear"]].drop_duplicates().merge(votes[["permco", "cik", "matched"]], on="permco")
    span = panel.groupby("cik")["year"].agg(["min", "max"]).reset_index()
    py = py.merge(span, on="cik", how="left")
    py["gap"] = (py["min"] - py["fyear"]).clip(lower=0) + (py["fyear"] - py["max"]).clip(lower=0)
    py["gap"] = py["gap"].fillna(99)
    py = py.sort_values(["gap", "matched"], ascending=[False, True]).drop_duplicates(["permco", "fyear"], keep="last")
    print(f"Bridge: {votes['permco'].nunique():,} permcos linked to {votes['cik'].nunique():,} SEC filers")
    return votes, py[["permco", "fyear", "cik"]]


def main():
    OUT.mkdir(exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)
    counts = []
    panel, filings, names = sec_accounts(counts)
    flt = public_float(filings, counts)
    panel = panel.merge(flt, on=["cik", "year"], how="left")
    k = patents(counts)
    votes, link = bridge(k, names, panel, counts)

    # Technology position: fractional count of each patent over its distinct CPC subclasses, built per
    # permco over all 2000-2022 patents and given to every filer linked to that permco (so Google's
    # pre-2015 patents count toward Alphabet, which became the filer in 2015)
    t = k.dropna(subset=["cpc4"])[["permco", "patent_num", "cpc4"]].explode("cpc4").dropna()
    t["w"] = 1 / t.groupby("patent_num")["cpc4"].transform("size")
    tech = t.groupby(["permco", "cpc4"])["w"].sum().reset_index()
    tech = tech.merge(votes[["permco", "cik"]].drop_duplicates(), on="permco")
    tech = tech.groupby(["cik", "cpc4"])["w"].sum().reset_index()
    tech["share"] = tech["w"] / tech.groupby("cik")["w"].transform("sum")

    k = k.merge(link, on=["permco", "fyear"], how="left")
    counts.append(("KPSS patents filed 2000-2022 attributed to an SEC filer", int(k["cik"].notna().sum()),
                   int(k["cik"].isna().sum())))
    k = k.dropna(subset=["cik"])
    py = (k.groupby(["cik", "fyear"]).agg(patents=("patent_num", "size"), cites=("cites", "sum"))
          .reset_index().rename(columns={"fyear": "year"}))
    counts.append(("SEC filers with a technology position (CPC shares)", tech["cik"].nunique(), 0))
    counts.append(("CPC subclasses used in the technology positions", tech["cpc4"].nunique(), 0))
    print(f"Technology position: {tech['cik'].nunique():,} filers over {tech['cpc4'].nunique():,} CPC subclasses")

    cols = ["cik", "year", "name", "sic", "countryba", "revenue", "rd", "cogs", "sga", "opinc", "assets",
            "liabilities", "equity", "ppe", "float"]
    panel[cols].sort_values(["cik", "year"]).to_csv(PROC / "firm_years.csv.gz", index=False,
                                                    compression="gzip", float_format="%.6g")
    py.sort_values(["cik", "year"]).to_csv(PROC / "patent_years.csv.gz", index=False, compression="gzip")
    tech[["cik", "cpc4", "share"]].sort_values(["cik", "cpc4"]).to_csv(
        PROC / "tech_shares.csv.gz", index=False, compression="gzip", float_format="%.6g")
    votes.sort_values("matched", ascending=False).to_csv(PROC / "patent_bridge.csv", index=False)
    pd.DataFrame(counts, columns=["step", "kept", "dropped"]).to_csv(OUT / "build_counts.csv", index=False)
    print(pd.DataFrame(counts, columns=["step", "kept", "dropped"]).to_string(index=False))
    print(f"Wrote data/processed/: firm_years ({len(panel):,} rows), patent_years ({len(py):,}), "
          f"tech_shares ({len(tech):,}), patent_bridge ({len(votes):,})")


if __name__ == "__main__":
    main()
