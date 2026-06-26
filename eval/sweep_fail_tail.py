"""Full-pipeline pass over the structural-sweep FAIL TAIL. Fast mode (segment-only) cannot
compute needs_review, so it cannot say whether a gross structural failure was FLAGGED or SILENT.
This runs the full pipeline (extract -> validate) on the failed true-10-Ks and records
needs_review: the headline check is that the silent-structural-failure count is ~0 (the
abstention gate holds at population scale). REPORTED only; reads sweep_report.json, writes
sweep_fail_tail.md. On-demand (network).

Run:  SEC_EDGAR_USER_AGENT="Name email" python eval/sweep_fail_tail.py
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sec10k.pipeline import extract

HERE = Path(__file__).parent


def _extract_with_timeout(acc: str, timeout: int = 90):
    """Run the full pipeline with a hard timeout so a wedged filing can't stall the tail pass."""
    box: dict = {}
    t = threading.Thread(target=lambda: box.__setitem__("r", extract(accession=acc)), daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError(f"extract wedged > {timeout}s")
    if "r" not in box:
        raise RuntimeError("extract failed without result")
    return box["r"]


def main() -> int:
    data = json.loads((HERE / "sweep_report.json").read_text())
    fails = [r for r in data["records"]
             if "error" not in r and r.get("form") == "10-K" and not r.get("pass")]
    ckpt = HERE / "sweep_fail_tail.json"  # resume + incremental (crash/stall-safe), gitignored
    done: dict = {}
    if ckpt.exists():
        try:
            done = {r["accession"]: r for r in json.loads(ckpt.read_text())}
        except Exception:
            done = {}
    rows = []
    for i, r in enumerate(fails, 1):
        acc = r["accession"]
        if acc in done:
            rows.append(done[acc])
            continue
        try:
            res = _extract_with_timeout(acc)
            s = res.summary
            row = {"accession": acc, "company": r.get("company", ""), "era": r.get("era"),
                   "reason": r["reason"], "needs_review": bool(s.get("needs_review")),
                   "items": s.get("items_present"), "cov": round(s.get("coverage_fraction", 0), 3)}
        except Exception as exc:
            row = {"accession": acc, "reason": r["reason"], "error": f"{type(exc).__name__}: {exc}"}
        rows.append(row)
        print(f"[{i}/{len(fails)}] {acc} "
              f"{row.get('error') or ('needs_review=' + str(row['needs_review']))}",
              file=sys.stderr, flush=True)
        if i % 5 == 0:
            ckpt.write_text(json.dumps(rows), encoding="utf-8")
    ckpt.write_text(json.dumps(rows), encoding="utf-8")
    measured = [r for r in rows if "error" not in r]
    silent = sum(1 for r in measured if not r["needs_review"])
    rd = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    L = [
        "# Structural-sweep FAIL TAIL -- full-pipeline flag status",
        "",
        f"Run: {rd}. Full pipeline (extract -> validate) on the {len(fails)} structural-FAILED full",
        "10-Ks, to recover the flag status fast mode cannot compute. The headline promise is that a",
        "gross structural failure is never SILENT -- it raises `needs_review`.",
        "",
        f"- **Silent structural failures (needs_review=False on a structural fail): {silent} / {len(measured)}**",
        f"- Flagged (needs_review=True): {len(measured) - silent} / {len(measured)}",
        "",
        "| accession | company | era | structural reason | needs_review | items | cov |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in measured:
        L.append(f"| {r['accession']} | {r['company'][:20]} | {r['era']} | {r['reason']} | "
                 f"{'FLAGGED' if r['needs_review'] else '**SILENT**'} | {r['items']} | {r['cov']} |")
    errs = [r for r in rows if "error" in r]
    if errs:
        L += ["", f"## Dropped ({len(errs)})", "", "| accession | error |", "|---|---|"]
        L += [f"| {r['accession']} | {r['error'][:80]} |" for r in errs]
    (HERE / "sweep_fail_tail.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
