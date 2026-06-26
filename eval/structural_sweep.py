"""Label-free STRUCTURAL SWEEP over a stratified set of pinned 10-K accessions.

Computes a population-scale **structural-pass rate** -- an UPPER BOUND on robustness, NOT
accuracy. It runs the regex tier only (fetch -> to_canonical -> segment) and re-uses the
production invariants (structural_invariants, round_trip, MIN_COVERAGE); it invents no new ruler
and gates nothing. It CANNOT see interior boundary drift (a right-header/wrong-end span passes),
so structural-pass != correct extraction. Fast mode also cannot compute needs_review, so it maps
the GROSS-failure tail only; a separate full-pipeline pass on the fail tail recovers flag status.

REPORTED-only: never edits/freezes any gold, never feeds a production decision. On-demand
(network); NOT part of the offline CI gate.

Run:  SEC_EDGAR_USER_AGENT="Name email" python eval/structural_sweep.py [accessions_file] [limit]
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sec10k.evalkit import wilson_ci
from sec10k.ingest import fetch_10k
from sec10k.normalize import to_canonical
from sec10k.segment import segment
from sec10k.validate import MIN_COVERAGE, round_trip, structural_invariants

HERE = Path(__file__).parent
_BIG = ("1", "1A", "7", "8")


def _starts_with_header(canonical: str, start: int, key: str) -> bool:
    head = re.sub(r"\s+", " ", canonical[start:start + 48]).strip().lower()
    return bool(re.match(rf"(?:part\s+[ivx]+\s+)?item\s+{re.escape(key.lower())}[.:)\s]", head))


def structural_pass(spans: list[tuple[str, int, int]], canonical: str) -> tuple[bool, str]:
    """The label-free structural-pass predicate (UPPER BOUND on robustness, NOT accuracy).
    Returns (passed, reason). `reason` is the FIRST failing check (for the tail map), or "ok".
    Re-uses the production invariants only -- no relaxed thresholds, no new ruler."""
    if not spans:
        return False, "empty"
    ranges = [(s, e) for _, s, e in spans]
    struct = structural_invariants(ranges)
    if not all(struct.values()):
        bad = ",".join(k for k, v in struct.items() if not v)
        return False, f"invariant:{bad}"
    rt_ok, rt_frac = round_trip(ranges, canonical)
    if not rt_ok:
        return False, "round_trip"
    if rt_frac < MIN_COVERAGE:
        return False, f"coverage:{rt_frac:.2f}"
    by_key = {k: (s, e) for k, s, e in spans}
    if "1" not in by_key:
        return False, "lead_item_1_missing"
    for k in _BIG:
        if k in by_key and not _starts_with_header(canonical, by_key[k][0], k):
            return False, f"header:{k}"
    return True, "ok"


def sweep_one(entry: dict) -> dict:
    """Fast-mode segment of one accession; never raises (errors are recorded as a row)."""
    acc = entry["accession"]
    try:
        raw = fetch_10k(accession=acc)
        canonical, era = to_canonical(raw)
        spans = segment(canonical)
        ranges = [(s, e) for _, s, e in spans]
        _, rt_frac = round_trip(ranges, canonical) if ranges else (False, 0.0)
        ok, reason = structural_pass(spans, canonical)
        return {
            "accession": acc, "company": entry.get("company", raw.company),
            "form": raw.form, "sector": entry.get("sector", "?"), "era": era,
            "structure_guess": reason if not ok else "clean",
            "pass": ok, "reason": reason, "items": len(spans),
            "coverage": round(rt_frac, 3), "lead1": "1" in {k for k, _, _ in spans},
        }
    except Exception as exc:  # network/parse failure -> an honest dropped row, never silent
        return {"accession": acc, "sector": entry.get("sector", "?"),
                "error": f"{type(exc).__name__}: {exc}"}


def _rate(rows: list[dict]) -> str:
    n = len(rows)
    k = sum(1 for r in rows if r.get("pass"))
    if not n:
        return "0/0 (n/a)"
    c, h = wilson_ci(k, n)
    return f"{k}/{n} ({k / n:.1%}, 95% CI [{max(0, c - h):.1%}, {min(1, c + h):.1%}])"


def _bucket(rows: list[dict], key: str) -> list[tuple[str, str]]:
    out: dict[str, list] = {}
    for r in rows:
        out.setdefault(r.get(key) or "?", []).append(r)
    return [(name, _rate(rs)) for name, rs in sorted(out.items())]


def render(records: list[dict], run_date: str) -> str:
    ok = [r for r in records if "error" not in r]
    errs = [r for r in records if "error" in r]
    tenk = [r for r in ok if r.get("form") == "10-K"]
    amend = [r for r in ok if r.get("form", "").endswith("/A")]
    L = [
        "# Structural Sweep -- population robustness (UPPER BOUND, NOT accuracy)",
        "",
        f"Run: {run_date}. On-demand label-free sweep (`eval/structural_sweep.py`) over a pinned,",
        "diverse stratified company sample. **structural-pass is an UPPER BOUND on robustness, NOT",
        "accuracy** -- it catches gross failures (empty body, lead item dropped, no tiling,",
        "implausible coverage) but is BLIND to interior boundary drift. The accuracy floor stays the",
        "5 human-audited char-gold. REPORTED only: gates nothing, freezes no gold. Fast mode cannot",
        "compute `needs_review`; flag-vs-silent on the fail tail comes from a separate full-pipeline",
        "pass (see `sweep_fail_tail.md`).",
        "",
        f"- **HEADLINE -- full 10-K structural-pass: {_rate(tenk)}** (UPPER BOUND, not accuracy)",
        f"- 10-K/A amendments (separate stratum; legitimately lack Part I): {_rate(amend)}",
        f"- Fetch/parse drops (logged, not silent): {len(errs)} of {len(records)}",
        "",
        "## Full 10-K structural-pass by era (UPPER BOUND, not accuracy)",
        "", "| era | pass / n (95% CI) |", "|---|---|",
    ]
    for name, rate in _bucket(tenk, "era"):
        L.append(f"| {name} | {rate} |")
    L += ["", "## Full 10-K structural-pass by sector (UPPER BOUND, not accuracy)",
          "", "| sector | pass / n (95% CI) |", "|---|---|"]
    for name, rate in _bucket(tenk, "sector"):
        L.append(f"| {name} | {rate} |")
    fails = [r for r in tenk if not r["pass"]]
    L += ["", f"## Gross-failure tail -- full 10-K ({len(fails)} of {len(tenk)})", "",
          "| accession | company | era | reason | items | cov | lead1 |", "|---|---|---|---|---|---|---|"]
    for r in sorted(fails, key=lambda r: r["reason"]):
        L.append(f"| {r['accession']} | {r.get('company','')[:24]} | {r['era']} | {r['reason']} | "
                 f"{r['items']} | {r['coverage']} | {r['lead1']} |")
    if errs:
        L += ["", f"## Dropped (fetch/parse error, {len(errs)})", "",
              "| accession | error |", "|---|---|"]
        for r in errs:
            L.append(f"| {r['accession']} | {r['error'][:80]} |")
    return "\n".join(L) + "\n"


def _run_with_timeout(entry: dict, timeout: int = 90) -> dict:
    """Run sweep_one in a daemon thread with a hard wall-clock timeout, so ONE wedged
    fetch/parse/segment cannot stall the whole sweep. A hung filing is abandoned (the daemon
    thread is left to die with the process) and recorded as a TIMEOUT drop -- honest, not silent."""
    box: dict = {}
    t = threading.Thread(target=lambda: box.__setitem__("r", sweep_one(entry)), daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return {"accession": entry["accession"], "sector": entry.get("sector", "?"),
                "error": f"TIMEOUT after {timeout}s (wedged fetch/parse/segment)"}
    return box.get("r", {"accession": entry["accession"], "error": "no result"})


def _worker(entry: dict) -> dict:
    """Top-level (picklable) process-pool worker: one filing, with the internal hard timeout so a
    wedged fetch/parse/segment cannot stall its worker (or the sweep)."""
    return _run_with_timeout(entry, int(os.getenv("SWEEP_TIMEOUT", "90")))


def _write(out_json: Path, records: list[dict]) -> None:
    run_date = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    out_json.write_text(json.dumps({"run_date": run_date, "records": records}, indent=2),
                        encoding="utf-8")


def main(argv: list[str]) -> int:
    acc_file = Path(argv[1]) if len(argv) > 1 else HERE / "sweep_accessions.txt"
    limit = int(argv[2]) if len(argv) > 2 else None
    # 6 worker processes: each spends most of its time on parse/segment, so aggregate EDGAR
    # request rate stays well under SEC's 10 req/s. Tune via SWEEP_WORKERS.
    workers = int(os.getenv("SWEEP_WORKERS", "6"))
    entries = [json.loads(line) for line in acc_file.read_text().splitlines() if line.strip()]
    if limit:
        entries = entries[:limit]
    out_json = HERE / "sweep_report.json"
    results: dict[str, dict] = {}  # resume: reuse already-computed records (crash/stall-safe)
    if out_json.exists():
        try:
            results = {r["accession"]: r for r in json.loads(out_json.read_text()).get("records", [])}
        except Exception:
            results = {}
    todo = [e for e in entries if e["accession"] not in results]
    total, n = len(entries), len(results)
    print(f"sweep: {total} filings, {len(todo)} to do, {len(results)} resumed, {workers} workers",
          file=sys.stderr, flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_worker, e): e for e in todo}
        for fut in as_completed(futs):
            e = futs[fut]
            try:
                r = fut.result()
            except Exception as exc:  # a worker that DIED (not just timed out) -> honest drop, logged
                r = {"accession": e["accession"], "sector": e.get("sector", "?"),
                     "error": f"POOL:{type(exc).__name__}: {exc}"}
            results[e["accession"]] = r
            n += 1
            tag = (f"ERR:{r['error'][:32]}" if "error" in r
                   else ("PASS" if r["pass"] else f"FAIL:{r['reason']}"))
            print(f"[{n}/{total}] {e['accession']} ({e.get('company','?')}/{e.get('target_year','?')}) {tag}",
                  file=sys.stderr, flush=True)
            if n % 10 == 0:
                _write(out_json, list(results.values()))  # checkpoint -> stall/crash-safe + resumable
    recs = list(results.values())
    _write(out_json, recs)
    run_date = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    (HERE / "sweep_report.md").write_text(render(recs, run_date), encoding="utf-8")
    print(render(recs, run_date))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
