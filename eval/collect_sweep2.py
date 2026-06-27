"""Round-7 stratified accession collector for the EXTRA ~1000-filing sweep.

Unlike collect_accessions.py (a curated ~120 large-cap list), this draws from the FULL EDGAR
population per (form, filing-year) via edgartools' bulk index, so the sample spans house-styles,
sectors, and filer sizes a curated list misses. It STRATIFIES by format era + form variant and
deliberately over-samples the under-covered/hard cells (pre-2001 SGML, amendments, small-biz),
while RECORDING each stratum's raw population so the structural-pass can be re-weighted to an
unbiased population estimate (precise per-stratum AND honest overall).

Emits a PINNED, immutable JSON-lines list (seeded RNG) excluding the existing sweep accessions, so
the sample is fixed and the sweep reproducible. The structural-pass it will feed is an UPPER BOUND
on robustness, NOT char-exact accuracy.

Run: SEC_EDGAR_USER_AGENT="Name email" python eval/collect_sweep2.py [out_file]
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import edgar

from sec10k.config import get_user_agent

HERE = Path(__file__).resolve().parent
SEED = 20260627

# (stratum, form, [filing-year range inclusive], target N) -- N over-samples the hard/thin cells.
STRATA = [
    ("sgml_pre2001",  "10-K",   (1994, 2001), 230),
    ("early_html",    "10-K",   (2002, 2009), 180),
    ("mid_html",      "10-K",   (2010, 2018), 170),
    ("ixbrl_modern",  "10-K",   (2019, 2025), 200),
    ("amendment",     "10-K/A", (1998, 2025), 100),
    ("smallbiz",      "10-KSB", (1998, 2008), 120),
]


def _existing() -> set[str]:
    accs = set()
    p = HERE / "sweep_accessions.txt"
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                accs.add(json.loads(ln)["accession"])
    return accs


def _pool(form: str, y0: int, y1: int) -> list[dict]:
    rows = []
    for y in range(y0, y1 + 1):
        try:
            df = edgar.get_filings(form=form, year=y).to_pandas()
        except Exception as exc:
            print(f"    {form} {y}: skip ({type(exc).__name__})", file=sys.stderr)
            continue
        if df is None or len(df) == 0:
            continue
        for r in df[["accession_number", "cik", "company", "filing_date"]].itertuples(index=False):
            rows.append({"accession": str(r[0]), "cik": int(r[1]) if r[1] else 0,
                         "company": str(r[2]), "filing_date": str(r[3])})
    return rows


def main(argv: list[str]) -> int:
    out_file = Path(argv[1]) if len(argv) > 1 else HERE / "sweep2_accessions.txt"
    edgar.set_identity(get_user_agent())
    edgar.configure_http(timeout=60)
    rng = random.Random(SEED)
    existing = _existing()
    print(f"excluding {len(existing)} existing accessions", file=sys.stderr)

    picked, seen = [], set()
    for name, form, (y0, y1), n in STRATA:
        t0 = time.monotonic()
        pool = [r for r in _pool(form, y0, y1)
                if r["accession"] not in existing and r["accession"] not in seen]
        raw_pop = len(pool)
        rng.shuffle(pool)
        take = pool[:n]
        for r in take:
            seen.add(r["accession"])
            r.update({"stratum": name, "form": form, "stratum_population": raw_pop,
                      "stratum_sampled": len(take)})
            picked.append(r)
        print(f"  {name:14s} {form:7s} {y0}-{y1}: pop={raw_pop} sampled={len(take)} "
              f"({time.monotonic()-t0:.0f}s)", file=sys.stderr)

    out_file.write_text("\n".join(json.dumps(r) for r in picked) + "\n", encoding="utf-8")
    print(f"\nwrote {len(picked)} pinned accessions -> {out_file}", file=sys.stderr)
    # stratum summary
    from collections import Counter
    c = Counter(r["stratum"] for r in picked)
    print("strata:", dict(c), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
