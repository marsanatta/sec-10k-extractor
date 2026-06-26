"""Stratified accession collector for the structural sweep. Walks a CURATED, diverse company
list (hand-tagged sector) and selects each company's 10-K nearest a set of target years that
deliberately OVER-SAMPLE the under-covered 2001-2018 middle era, plus a small 10-K/A stratum.

Emits a PINNED, immutable list (one JSON line per accession) so the sample is fixed and the sweep
is reproducible. The 'population robustness' number this feeds is a DIVERSE STRATIFIED SAMPLE,
UPPER BOUND -- not an unbiased random-EDGAR estimate.

Run:  SEC_EDGAR_USER_AGENT="Name email" python eval/collect_accessions.py [out_file] [limit_companies]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import edgar

from sec10k.config import get_user_agent

# Curated, diverse, mostly long-continuous-history companies (ticker, sector).
COMPANIES = [
    ("AAPL", "technology"), ("MSFT", "technology"), ("IBM", "technology"),
    ("INTC", "technology"), ("ORCL", "technology"), ("CSCO", "technology"), ("TXN", "technology"),
    ("JPM", "finance"), ("BAC", "finance"), ("WFC", "finance"), ("AXP", "finance"), ("USB", "finance"),
    ("XOM", "energy"), ("CVX", "energy"), ("SLB", "energy"), ("OXY", "energy"),
    ("JNJ", "healthcare"), ("PFE", "healthcare"), ("MRK", "healthcare"), ("ABT", "healthcare"),
    ("BMY", "healthcare"), ("LLY", "healthcare"),
    ("KO", "consumer_staples"), ("PG", "consumer_staples"), ("PEP", "consumer_staples"),
    ("CL", "consumer_staples"), ("MO", "consumer_staples"), ("GIS", "consumer_staples"),
    ("GE", "industrial"), ("BA", "industrial"), ("CAT", "industrial"), ("MMM", "industrial"),
    ("HON", "industrial"), ("EMR", "industrial"),
    ("WMT", "retail"), ("HD", "retail"), ("TGT", "retail"), ("MCD", "retail"), ("COST", "retail"),
    ("SO", "utility"), ("DUK", "utility"), ("D", "utility"),
    ("NEM", "materials"), ("APD", "materials"),
    ("T", "telecom_media"), ("VZ", "telecom_media"), ("DIS", "telecom_media"),
    ("F", "auto"),
]
# Over-sample the 2001-2018 middle (6 of 10 years fall there).
TARGET_YEARS = [1996, 1999, 2003, 2006, 2009, 2012, 2015, 2018, 2021, 2024]
AMEND_TICKERS = ["AAPL", "GE", "JPM", "PFE", "KO", "BA", "XOM", "WMT", "DIS", "MMM"]


def _fy(f) -> int | None:
    por = str(getattr(f, "period_of_report", "") or "")
    if len(por) >= 4 and por[:4].isdigit():
        return int(por[:4])
    fd = str(getattr(f, "filing_date", "") or "")
    return int(fd[:4]) if len(fd) >= 4 and fd[:4].isdigit() else None


def collect(companies) -> list[dict]:
    edgar.set_identity(get_user_agent())
    edgar.configure_http(timeout=60)
    out, seen = [], set()
    for ticker, sector in companies:
        try:
            filings = list(edgar.Company(ticker).get_filings(form="10-K"))
        except Exception as exc:
            print(f"  skip {ticker}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        by_fy: dict[int, object] = {}
        for f in filings:
            y = _fy(f)
            if y is not None:
                by_fy.setdefault(y, f)
        picked: set[int] = set()
        for Y in TARGET_YEARS:
            for yy in sorted(by_fy, key=lambda v: abs(v - Y)):
                if yy in picked or abs(yy - Y) > 2:
                    if abs(yy - Y) > 2:
                        break
                    continue
                acc = str(getattr(by_fy[yy], "accession_number", "") or "")
                if acc and acc not in seen:
                    seen.add(acc); picked.add(yy)
                    out.append({"accession": acc, "company": ticker, "sector": sector,
                                "target_year": Y, "fy": yy})
                break
        print(f"  {ticker}: {len(picked)} 10-Ks", file=sys.stderr)
    # small 10-K/A stratum (reported separately)
    for ticker in AMEND_TICKERS:
        sector = next((s for t, s in companies if t == ticker), "?")
        try:
            am = list(edgar.Company(ticker).get_filings(form="10-K/A"))
        except Exception:
            am = []
        for f in am[:1]:
            acc = str(getattr(f, "accession_number", "") or "")
            if acc and acc not in seen:
                seen.add(acc)
                out.append({"accession": acc, "company": ticker, "sector": sector, "stratum": "amendment"})
    return out


def main(argv: list[str]) -> int:
    out_file = Path(argv[1]) if len(argv) > 1 else Path(__file__).parent / "sweep_accessions.txt"
    limit = int(argv[2]) if len(argv) > 2 else None
    companies = COMPANIES[:limit] if limit else COMPANIES
    t0 = time.monotonic()
    rows = collect(companies)
    out_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(f"collected {len(rows)} accessions ({len(companies)} companies) in "
          f"{time.monotonic()-t0:.0f}s -> {out_file}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
