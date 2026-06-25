from __future__ import annotations

import datetime
import json
import re
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
    scattered_item_check,
)
from sec10k.pipeline import extract

HERE = Path(__file__).parent
MANIFEST = HERE / "eval_set.json"
GOLD_FILE = HERE / "boundary_gold.json"
GOLD = json.loads(GOLD_FILE.read_text()) if GOLD_FILE.exists() else {}

_BIG = ("1", "1A", "7", "8")


def _start_correct(result) -> int:
    """Of the big items {1,1A,7,8} that are present, how many spans BEGIN with the matching
    'Item N' header. A cheap self-check that the start landed on a header -- NOT the audited
    char-gold (that stays at 5 filings); reported per filing for the covering table."""
    n = 0
    for k in _BIG:
        it = next((i for i in result.items if i.item == k and i.status.value == "present"), None)
        if it and it.text:
            head = re.sub(r"\s+", " ", it.text[:40]).strip().lower()
            if re.match(rf"item {k.lower()}[.:) ]", head):
                n += 1
    return n


def _tier(result) -> str:
    return (
        "fallback"
        if any("edgartools-fallback" in i.provenance.extractors
               for i in result.items if i.status.value == "present")
        else "regex"
    )


def _run_one(entry: dict) -> dict:
    result = extract(accession=entry["accession"])  # accession-pinned, immutable
    exp = entry.get("expected_present", [])
    s = result.summary
    g = GOLD.get(entry["id"])
    recall = presence_scores(result, exp)["recall"]
    return {
        "id": entry["id"],
        "company": entry.get("company", ""),
        "era": s.get("format_era"),
        "sector": entry.get("sector", ""),
        "filer_type": entry.get("filer_type", ""),
        "structure": entry.get("structure", ""),
        "expect_red": entry.get("expect_red", False),
        "note": entry.get("note", ""),
        "items_found": s.get("items_present"),
        "start_correct": _start_correct(result),
        "tier": _tier(result),
        "recall": recall,
        "pass": recall >= 1.0,
        "tail_probe": entry.get("tail_probe"),
        "tail_probe_item": entry.get("tail_probe_item"),
        "scattered": (scattered_item_check(result, entry["tail_probe_item"], entry["tail_probe"])
                      if entry.get("tail_probe") else None),
        "presence": presence_scores(result, exp),
        "signals": label_free_signals(result),
        "silent_failure": is_silent_failure(result, exp),
        "boundary": boundary_scores(result, g["items"]) if g else None,
        "escalation": {k: s.get(k) for k in (
            "escalation_candidates", "escalation_performed", "escalation_provider",
            "escalation_calls", "escalation_input_tokens", "escalation_output_tokens")},
        "summary": {k: s.get(k) for k in (
            "format_era", "items_present", "items_extraction_failure",
            "coverage_fraction", "item8_xbrl_found", "item8_xbrl_checked", "needs_review")},
    }


def _bucket(ok: list[dict], key: str) -> list[tuple]:
    out = {}
    for r in ok:
        b = out.setdefault(r.get(key) or "(none)", {"n": 0, "pass": 0, "red": 0})
        b["n"] += 1
        b["pass"] += 1 if r["pass"] else 0
        b["red"] += 1 if r["expect_red"] else 0
    return sorted(out.items())


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
    reds = [r for r in ok if r["expect_red"]]
    greens = [r for r in ok if not r["expect_red"]]

    def rate(pred) -> str:
        return fmt_rate(sum(1 for r in ok if pred(r)), n)

    agg = {
        "n_filings": n,
        "errors": [r for r in rows if "error" in r],
        "fully_extracted_rate": fmt_rate(sum(1 for r in greens if r["pass"]), len(greens)),
        "red_cases": [r["id"] for r in reds],
        "silent_failure_rate": fmt_rate(sum(1 for r in ok if r["silent_failure"]), n),
        "structural_ok_rate": rate(lambda r: r["signals"]["structural_ok"]),
        "coverage_plausible_rate": rate(lambda r: r["signals"]["coverage_plausible"]),
        "needs_review_rate": rate(lambda r: r["signals"]["needs_review"]),
        "mean_presence_recall": round(sum(r["recall"] for r in ok) / n, 4) if n else 0.0,
        "buckets_by_era": _bucket(ok, "era"),
        "buckets_by_structure": _bucket(ok, "structure"),
        "buckets_by_sector": _bucket(ok, "sector"),
    }
    brows = [r for r in ok if r.get("boundary")]
    mrs = [r["boundary"]["match_rate"] for r in brows if r["boundary"]["match_rate"] is not None]
    agg["boundary_gold_filings"] = len(brows)
    agg["boundary_match_rate_mean"] = round(sum(mrs) / len(mrs), 3) if mrs else None

    run_date = (datetime.datetime.utcfromtimestamp(time.time()) + datetime.timedelta(hours=8)).strftime(
        "%Y-%m-%d %H:%M Asia/Taipei")
    md = _render_md(agg, rows, run_date)
    (HERE / "report.json").write_text(
        json.dumps({"aggregate": agg, "filings": rows}, indent=2, default=str), encoding="utf-8")
    (HERE / "report.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def _render_md(agg: dict, rows: list[dict], run_date: str) -> str:
    lines = [
        "# Evaluation Report",
        "",
        f"Run: {run_date}. On-demand EDGAR batch (accession-pinned); NOT part of the offline unit",
        "suite. A CURATED covering set that EXERCISES specific era/filer/structure/sector axes (NOT",
        "a random sample) -- the per-bucket tables show WHICH axis breaks. The broad-population",
        "fully-extracted estimate is the separate random diverse batch in ANALYSIS.md (~78%). RED =",
        "known failures tracked on purpose, not papered over.",
        "",
        "## Headline",
        "",
        f"- **Covering-set non-RED pass (recall=1.0): {agg['fully_extracted_rate']}** "
        "(curated axes; population estimate ~78% is the random batch in ANALYSIS.md)",
        f"- **RED cases (tracked failures): {', '.join(agg['red_cases']) or 'none'}**",
        f"- Presence silent-failure rate (lower better): {agg['silent_failure_rate']}",
        f"- Boundary match-rate @ IoU>=0.9 vs audited gold: {agg.get('boundary_match_rate_mean')}"
        f" over {agg.get('boundary_gold_filings', 0)} gold filings (per-era; gold stays human-audited)",
        f"- Structural-ok: {agg['structural_ok_rate']}  |  Coverage-plausible: {agg['coverage_plausible_rate']}",
        f"- Needs-review (flagged): {agg['needs_review_rate']}  |  Mean recall: {agg['mean_presence_recall']}"
        f"  |  N: {agg['n_filings']}",
        "",
    ]
    if agg["errors"]:
        lines += ["## Errors", ""] + [f"- {e['id']}: {e['error']}" for e in agg["errors"]] + [""]

    lines += [
        "## Covering set (raw, per filing)",
        "",
        "| filing | era | filer_type | sector | structure | items | start/4 | tier | recall | boundary | RED | note |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['id']} | ERROR: {r['error']} | | | | | | | | | | |")
            continue
        b = r.get("boundary")
        bstr = f"{b['match_rate']}({b['matched']}/{b['total']})" if b else "-"
        red = "**RED**" if r["expect_red"] else ""
        lines.append(
            f"| {r['id']} | {r['era']} | {r['filer_type']} | {r['sector']} | {r['structure']} | "
            f"{r['items_found']} | {r['start_correct']}/4 | {r['tier']} | {r['recall']} | {bstr} | {red} | {r['note']} |"
        )

    for title, key in (("era", "buckets_by_era"), ("structure", "buckets_by_structure"),
                       ("sector", "buckets_by_sector")):
        lines += ["", f"## Per-bucket by {title} (which axis breaks)", "",
                  f"| {title} | n | fully-extracted (recall=1.0) | RED |", "|---|---|---|---|"]
        for name, b in agg[key]:
            lines.append(f"| {name} | {b['n']} | {b['pass']}/{b['n']} | {b['red']} |")

    scat = [r for r in rows if "error" not in r and r.get("scattered")]
    if scat:
        lines += ["", "## Scattered-item checks (item captured WHOLE, not just non-empty)", "",
                  "A late-MD&A probe must fall INSIDE the extracted item span; if it lands after the",
                  "span the tail was dropped (a non-contiguous-item failure even though the item is present).",
                  "", "| filing | item | tail probe | inside span? | verdict |", "|---|---|---|---|---|"]
        for r in scat:
            sc = r["scattered"]
            inside = sc["inside"]
            verdict = ("PASS (whole)" if inside else
                       "**RED (tail dropped)**" if inside is False else "n/a (absent)")
            lines.append(f"| {r['id']} | {r['tail_probe_item']} | {r['tail_probe']} | {inside} | {verdict} |")

    lines += _render_token_ledger(rows)
    return "\n".join(lines) + "\n"


def _render_token_ledger(rows: list[dict]) -> list[str]:
    """Per-filing LLM-escalation token ledger. Measured, not estimated: 'index-don't-generate'
    means $0/0-token on the cooperative path, and the LLM fires only on confidence-gated
    escalation. With the deferred stub no call is made, so calls/tokens are an honest measured
    0 ('escalation not exercised') -- a real client populates the same columns when wired."""
    er = [r for r in rows if "error" not in r and r.get("escalation")]
    if not er:
        return []
    provider = next((r["escalation"].get("escalation_provider") for r in er), "deferred")
    performed = any(r["escalation"].get("escalation_performed") for r in er)
    tot_cand = tot_calls = tot_in = tot_out = 0
    body = []
    for r in er:
        e = r["escalation"]
        ncand = len(e.get("escalation_candidates") or [])
        calls = e.get("escalation_calls") or 0
        tin = e.get("escalation_input_tokens") or 0
        tout = e.get("escalation_output_tokens") or 0
        tot_cand += ncand
        tot_calls += calls
        tot_in += tin
        tot_out += tout
        body.append(f"| {r['id']} | {ncand} | {calls} | {tin} | {tout} | "
                    f"{e.get('escalation_performed')} |")
    note = (f"Provider = `{provider}`. " + (
        "**Escalation NOT exercised on this set** -- the client is the deferred stub, so triggers "
        "fire and candidates are recorded but no LLM call is made: calls/tokens are a measured 0, "
        "not an estimate. Wire a real client (GitHub Copilot SDK) to populate these columns."
        if not performed else
        "A real client was wired; calls/tokens below are summed from its per-call usage payloads."))
    return [
        "", "## LLM escalation token ledger (measured)", "",
        "Index-don't-generate: $0/0-token on the cooperative path; the LLM fires only on the",
        "confidence-gated escalation minority. Calls are made for present low-confidence",
        "boundaries (the LIB prompt indexes around an existing span); missing-item 'find'",
        "escalation is a separate, unbuilt path and is not called here.", "",
        note, "",
        "| filing | escalation candidates | calls | input tokens | output tokens | performed |",
        "|---|---|---|---|---|---|",
        *body,
        f"| **total** | {tot_cand} | {tot_calls} | {tot_in} | {tot_out} | {performed} |",
    ]


if __name__ == "__main__":
    raise SystemExit(main())
