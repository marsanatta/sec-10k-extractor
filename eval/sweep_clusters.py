"""Cluster the structural-sweep fail tail by failure family (round-3 probe #1 deliverable).

Reads eval/sweep_report.json, groups the full-10-K fails (+ drops) by a normalized failure family,
maps each family to an ALREADY-NAMED class (rounds 1-2 / sweep-1) or marks it UNEXPLAINED, and emits
eval/sweep_census.md. The UNEXPLAINED clusters are the /eng-debug targets -- root-cause ONE
representative per cluster, never per filing. REPORTED-only: reads the sweep, changes nothing.

Run:  python eval/sweep_clusters.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

# Failure families that rounds 1-2 / the first sweep already root-caused: confirm + COUNT at scale,
# do not re-debug. The rest are UNEXPLAINED -> /eng-debug one representative each.
KNOWN = {
    "coverage_very_low(<0.15)": "cross-reference index (integrated MD&A, e.g. GE/INTC) -- round-1 named",
    "lead_missing_low_cov(<0.85)": "run-fragmentation / PART-glued / no-separator headers -- rounds 1-2 named",
    "invariant_violation": "non-monotonic/overlap/tiling -- structural, flagged",
    "round_trip_fail": "round-trip byte mismatch -- structural, flagged",
    "TIMEOUT": "large-filing perf (wedged >90s) -- sweep-1 named",
}


def cluster_of(r: dict) -> str:
    if "error" in r:
        return "TIMEOUT" if "TIMEOUT" in r["error"] else "drop_other"
    reason = r.get("reason", "?")
    cov = r.get("coverage", 0) or 0
    if reason == "empty":
        return "empty(0_items)"
    if reason.startswith("coverage:"):
        return "coverage_very_low(<0.15)" if cov < 0.15 else "coverage_partial(0.15-0.4)"
    if reason == "lead_item_1_missing":
        return "lead_missing_high_cov(>=0.85)" if cov >= 0.85 else "lead_missing_low_cov(<0.85)"
    if reason.startswith("header:"):
        return "header_not_self_headed"
    if reason.startswith("invariant:"):
        return "invariant_violation"
    if reason == "round_trip":
        return "round_trip_fail"
    return reason


def main() -> int:
    data = json.loads((HERE / "sweep_report.json").read_text())
    recs = data["records"]
    tenk = [r for r in recs if "error" not in r and r.get("form") == "10-K"]
    amend = [r for r in recs if "error" not in r and r.get("form", "").endswith("/A")]
    drops = [r for r in recs if "error" in r]
    fails = [r for r in tenk if not r.get("pass")]

    clusters: dict[str, list] = defaultdict(list)
    for r in fails:
        clusters[cluster_of(r)].append(r)
    for r in drops:
        clusters[cluster_of(r)].append(r)

    n_tenk = len(tenk)
    n_pass = sum(1 for r in tenk if r.get("pass"))
    L = [
        "# Structural-sweep FAILURE CENSUS -- clustered (round-3 probe #1)",
        "",
        "Clusters the fail tail by failure family so we /eng-debug per CLASS (one representative),",
        "not per filing. **structural-pass is an UPPER BOUND on robustness, NOT accuracy.** REPORTED-",
        "only. Known families = confirm + count at scale; UNEXPLAINED families = the eng-debug targets.",
        "",
        f"- Full 10-K swept: **{n_tenk}**; structural-pass {n_pass}/{n_tenk} "
        f"({n_pass / n_tenk:.1%} -- UPPER BOUND, not accuracy)" if n_tenk else "- (no 10-K rows)",
        f"- Full-10-K fails clustered: **{len(fails)}**; amendments (separate stratum): {len(amend)}; "
        f"drops: {len(drops)}",
        "",
        "| cluster (failure family) | n | known class? | representative accessions |",
        "|---|---|---|---|",
    ]
    for name, rs in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        known = KNOWN.get(name, "**UNEXPLAINED -> eng-debug**")
        reps = ", ".join(f"{r['accession']}({r.get('company','?')})" for r in rs[:4])
        L.append(f"| {name} | {len(rs)} | {known} | {reps} |")

    unexplained = {k: v for k, v in clusters.items() if k not in KNOWN and k != "drop_other"}
    L += ["", "## /eng-debug targets (UNEXPLAINED clusters -- one representative each)", ""]
    if unexplained:
        for name, rs in sorted(unexplained.items(), key=lambda kv: -len(kv[1])):
            companies = sorted({r.get("company", "?") for r in rs})
            L.append(f"- **{name}** (n={len(rs)}; filers: {', '.join(companies[:12])}) -- "
                     f"rep `{rs[0]['accession']}` ({rs[0].get('company','?')})")
    else:
        L.append("- _(none -- every fail maps to an already-named class; S4 territory)_")

    out = "\n".join(L) + "\n"
    (HERE / "sweep_census.md").write_text(out, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
