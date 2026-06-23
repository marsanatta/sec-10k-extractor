from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path for `python eval/run_eval.py`

from sec10k.evalkit import (
    boundary_scores,
    fmt_rate,
    is_silent_failure,
    label_free_signals,
    presence_scores,
)
from sec10k.pipeline import extract

HERE = Path(__file__).parent
MANIFEST = HERE / "eval_set.json"
GOLD_FILE = HERE / "boundary_gold.json"
GOLD = json.loads(GOLD_FILE.read_text()) if GOLD_FILE.exists() else {}


def _run_one(entry: dict) -> dict:
    if entry.get("accession"):
        result = extract(accession=entry["accession"])
    else:
        result = extract(ticker_or_cik=entry["ticker"], fiscal_year=entry.get("fiscal_year"))
    exp = entry.get("expected_present", [])
    s = result.summary
    g = GOLD.get(entry["id"])
    return {
        "id": entry["id"],
        "company": entry.get("company", ""),
        "pathologies": entry.get("pathologies", []),
        "presence": presence_scores(result, exp),
        "signals": label_free_signals(result),
        "silent_failure": is_silent_failure(result, exp),
        "boundary": boundary_scores(result, g["items"]) if g else None,
        "summary": {
            k: s.get(k)
            for k in (
                "format_era", "items_present", "items_extraction_failure",
                "coverage_fraction", "item8_xbrl_found", "item8_xbrl_checked", "needs_review",
            )
        },
    }


def main(argv=None) -> int:
    entries = json.loads(MANIFEST.read_text())["filings"]
    rows = []
    for e in entries:
        t0 = time.monotonic()
        print(f"[eval] {e['id']} ...", file=sys.stderr, flush=True)
        try:
            rows.append(_run_one(e))
            print(f"[eval] {e['id']} done in {time.monotonic() - t0:.0f}s", file=sys.stderr, flush=True)
        except Exception as ex:  # one bad filing must not sink the whole report
            rows.append({"id": e["id"], "error": f"{type(ex).__name__}: {ex}"})
            print(f"[eval] {e['id']} ERROR: {ex}", file=sys.stderr, flush=True)

    ok = [r for r in rows if "error" not in r]
    n = len(ok)

    def rate(pred) -> str:
        return fmt_rate(sum(1 for r in ok if pred(r)), n)

    agg = {
        "n_filings": n,
        "errors": [r for r in rows if "error" in r],
        "silent_failure_rate": fmt_rate(sum(1 for r in ok if r["silent_failure"]), n),
        "structural_ok_rate": rate(lambda r: r["signals"]["structural_ok"]),
        "coverage_plausible_rate": rate(lambda r: r["signals"]["coverage_plausible"]),
        "item8_oracle_ok_rate": rate(lambda r: r["signals"]["item8_oracle_ok"]),
        "needs_review_rate": rate(lambda r: r["signals"]["needs_review"]),
        "mean_presence_recall": round(sum(r["presence"]["recall"] for r in ok) / n, 4) if n else 0.0,
    }
    brows = [r for r in ok if r.get("boundary")]
    mrs = [r["boundary"]["match_rate"] for r in brows if r["boundary"]["match_rate"] is not None]
    agg["boundary_gold_filings"] = len(brows)
    agg["boundary_match_rate_mean"] = round(sum(mrs) / len(mrs), 3) if mrs else None
    md = _render_md(agg, rows)
    (HERE / "report.json").write_text(json.dumps({"aggregate": agg, "filings": rows}, indent=2, default=str))
    (HERE / "report.md").write_text(md)
    print(md)
    return 0


def _render_md(agg: dict, rows: list[dict]) -> str:
    lines = [
        "# Evaluation Report",
        "",
        "Self-built eval set; presence-level gold (conservative hand-labels). Rates are Wilson",
        "95% CI -- small N means wide bars. Boundary match-rate uses a small INDEPENDENT",
        "char-exact gold (seed) keyed to the big items 1/1A/7/8.",
        "",
        "## Headline",
        "",
        f"- **Presence-level silent-failure rate (lower is better): {agg['silent_failure_rate']}**",
        "  (missed expected items with no flag; boundary correctness is the separate metric below)",
        f"- **Boundary match-rate @ IoU>=0.9 vs INDEPENDENT gold: {agg.get('boundary_match_rate_mean')}"
        f" over {agg.get('boundary_gold_filings', 0)} gold filings** (a wrong boundary shows up here as a number)",
        f"- Structural-ok: {agg['structural_ok_rate']}",
        f"- Coverage-plausible: {agg['coverage_plausible_rate']}",
        f"- Item-8 XBRL oracle ok: {agg['item8_oracle_ok_rate']}",
        f"- Needs-review (flagged): {agg['needs_review_rate']}",
        f"- Mean presence recall: {agg['mean_presence_recall']}",
        f"- N filings: {agg['n_filings']}",
        "",
    ]
    if agg["errors"]:
        lines += ["## Errors", ""] + [f"- {e['id']}: {e['error']}" for e in agg["errors"]] + [""]
    lines += [
        "## Per-filing",
        "",
        "| id | era | present | recall | boundary@IoU0.9 | silent_fail | needs_review | item8_xbrl |",
        "|----|-----|---------|--------|-----------------|-------------|--------------|-----------|",
    ]
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['id']} | ERROR: {r['error']} | | | | | | |")
            continue
        s, p, b = r["summary"], r["presence"], r.get("boundary")
        bstr = f"{b['match_rate']} ({b['matched']}/{b['total']})" if b else "-"
        lines.append(
            f"| {r['id']} | {s['format_era']} | {s['items_present']} | {p['recall']} | "
            f"{bstr} | {r['silent_failure']} | {s['needs_review']} | "
            f"{s['item8_xbrl_found']}/{s['item8_xbrl_checked']} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
