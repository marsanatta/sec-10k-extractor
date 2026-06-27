"""G9 — no-collateral-change population guard, computed CHEAPLY (cache canonicals, re-segment offline).

Segmentation is deterministic on the canonical bytes, and A1/A2 change ONLY segmentation, never fetch
or normalize. So we cache all sweep canonicals ONCE (the expensive, network step) and record their
pre-fix spans; then after each A-fix we RE-SEGMENT the cached canonicals OFFLINE and diff spans — zero
network, deterministic, seconds. A filing whose spans change but is NOT in the targeted cluster is a
candidate over-widening regression → G9 FAILS.

  baseline:  python eval/g9.py baseline   (one-time, network; reuses the killable sweep pool;
             writes eval/.g9_cache/<acc>.txt + eval/g9_baseline.json; resumable)
  diff:      python eval/g9.py diff <targeted_accessions.txt>   (OFFLINE; one accession per line;
             exits non-zero if any non-targeted filing's segmentation changed)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sec10k.ingest import fetch_10k
from sec10k.normalize import to_canonical
from sec10k.segment import segment

HERE = Path(__file__).parent
CACHE = HERE / ".g9_cache"
BASE = HERE / "g9_baseline.json"


def _spans(canonical: str):
    return [[k, s, e] for k, s, e in segment(canonical)]


def _g9_child(entry: dict, q) -> None:
    """Process target (killable via the sweep pool): fetch+canonicalize one filing, cache the
    canonical, hand back its pre-fix spans. Errors are recorded, never silent."""
    acc = entry["accession"]
    try:
        raw = fetch_10k(accession=acc)
        canon, _era = to_canonical(raw)
        cdir = Path(os.environ.get("G9_CACHE_DIR", str(CACHE)))
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / f"{acc}.txt").write_text(canon, encoding="utf-8")
        q.put({"accession": acc, "spans": _spans(canon), "len": len(canon)})
    except Exception as exc:
        q.put({"accession": acc, "error": f"{type(exc).__name__}: {exc}"})


def baseline() -> int:
    from eval.structural_sweep import _run_pool

    CACHE.mkdir(exist_ok=True)
    os.environ["G9_CACHE_DIR"] = str(CACHE)
    entries = [json.loads(line) for line in (HERE / "sweep_accessions.txt").read_text().splitlines()
               if line.strip()]
    results: dict = {}
    if BASE.exists():
        try:
            results = {r["accession"]: r for r in json.loads(BASE.read_text())["records"]}
        except Exception:
            results = {}
    todo = [e for e in entries if e["accession"] not in results]
    print(f"g9 baseline: {len(entries)} filings, {len(todo)} to do, {len(results)} cached",
          file=sys.stderr, flush=True)
    _run_pool(todo, int(os.getenv("SWEEP_WORKERS", "6")), int(os.getenv("SWEEP_TIMEOUT", "240")),
              results, len(entries), BASE, child=_g9_child)
    ok = sum(1 for r in results.values() if "error" not in r)
    print(f"g9 baseline done: {ok} canonicals cached, {len(results) - ok} errors", file=sys.stderr)
    return 0


def diff(targeted_path: str) -> int:
    base = json.loads(BASE.read_text())
    recs = {r["accession"]: r for r in base["records"] if "error" not in r}
    targeted = {ln.split()[0] for ln in Path(targeted_path).read_text().splitlines() if ln.strip()}
    changed, missing_cache = [], 0
    for acc, rec in recs.items():
        p = CACHE / f"{acc}.txt"
        if not p.exists():
            missing_cache += 1
            continue
        if _spans(p.read_text(encoding="utf-8")) != rec["spans"]:
            changed.append(acc)
    collateral = sorted(a for a in changed if a not in targeted)
    recovered = [a for a in changed if a in targeted]
    print(f"G9 diff vs baseline ({len(recs)} cached, {missing_cache} missing): "
          f"changed={len(changed)} | targeted-recovered={len(recovered)} | COLLATERAL={len(collateral)}")
    for a in collateral:
        print(f"  COLLATERAL (non-targeted filing changed): {a}")
    verdict = "PASS — no collateral change" if not collateral else "FAIL — over-widening (collateral change)"
    print(f"G9: {verdict}")
    return 1 if collateral else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    if cmd == "diff":
        raise SystemExit(diff(sys.argv[2]))
    raise SystemExit(baseline())
