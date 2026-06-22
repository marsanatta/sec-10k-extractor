from __future__ import annotations

import argparse
import json
import sys

from sec10k.pipeline import extract


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m sec10k", description="Extract items from a SEC 10-K filing"
    )
    p.add_argument("target", nargs="?", help="ticker or CIK (omit if using --accession)")
    p.add_argument("fiscal_year", nargs="?", type=int, default=None, help="fiscal year, e.g. 2024")
    p.add_argument("--accession", default=None, help="EDGAR accession number")
    p.add_argument("--json", action="store_true", help="emit the full JSON result")
    args = p.parse_args(argv)

    if not args.target and not args.accession:
        p.error("provide a ticker/CIK or --accession")

    result = extract(ticker_or_cik=args.target, fiscal_year=args.fiscal_year, accession=args.accession)

    if args.json:
        json.dump(result.to_dict(), sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0

    m, s = result.meta, result.summary
    print(f"{m.company} {m.form} FY{m.fiscal_year} [{m.format_era}] acc={m.accession}")
    print(
        f"present={s['items_present']} legit_absent={s['items_legitimately_absent']} "
        f"extraction_failure={s['items_extraction_failure']}  |  "
        f"structural_ok={s['structural_ok']} round_trip_ok={s['round_trip_ok']} "
        f"coverage={s['coverage_fraction']} low_conf={s['low_confidence_items']}"
    )
    for it in result.items:
        rng = f"{it.char_range[0]}-{it.char_range[1]}" if it.char_range else "-"
        print(
            f"  {it.status.value:<20} {it.confidence.band.value:<7} "
            f"Item {it.item:<3} {it.title[:38]:<38} [{rng}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
