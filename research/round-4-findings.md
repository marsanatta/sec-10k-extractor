# Autoresearch Round 4 — Findings (Step A so far)

REPORTED honestly. Step B (rulers) complete; Step A in progress. The headline so far is a **measured
DISCARD** that the guards caught — and a precise re-plan it produced. G9 + the structural-pass
demotion did exactly their job.

## A1 (separator-less header recogniser) — attempted, DISCARDED by G9

**Probe:** relax `_HEADER_RE` (`segment.py`) so the item number may be followed by whitespace + a
Title-Case/UPPER title word (`ITEM 1 Business`, `ITEM 7\n\nMANAGEMENT`) in addition to a separator,
keeping the line-start anchor + a `(?=[A-Z])` lookahead (to reject `Item 5 of the plan`).

**Offline result:** the A1 RED target flipped GREEN (separator-less headers found); the no-false-header
guard + control + all existing segment tests stayed green. Looked good.

**G9 result (the decisive gate):** re-segmenting the **1,734 cached canonicals** offline:
- intended recovery: **38 empty filings 0→N** (GIS 0→21, MCD 0→22, CMCSA, …) ✓
- **COLLATERAL: 156 clean filings with prior spans changed, MANY DEGRADED** — CVX 23→3, SHW 23→13,
  GS 20→12, TGT 20→12, SBUX 23→13, … ✗✗

→ **A1-v1 DISCARDED.** A looser regex raised the (label-free) structural-pass *and* the RED target,
but **degraded 100+ clean filings** — exactly the proxy trap the plan's structural-pass demotion + G9
were built to catch. **Note for the record: had we kept structural-pass as a keep gate, this would
have looked like a win.**

**Mechanism (traced, not guessed):** on CVX (clean) the relaxation admits ONE false header — a
line-start in-prose cross-reference `Item 10 Executive Officers` inside Item 1's prose. It is
**byte-identical to a real header**, so no regex can reject it; only the run-selection can, by canonical
order. That spurious high-order hit fragments `_split_runs`, and `_pick_body_run` then picks a tiny
run → 23→3.

## KEY FINDING: A1 and A2 are COUPLED

A1 (relax regex) cannot be made safe in isolation — it admits more in-prose cross-references, and only
A2 (run-selection hardening) can reject them. So they are **one probe, not two.**

## A1+A2-v1 (single-intruder-tolerant `_split_runs`) — attempted, DISCARDED

**Probe:** keep the A1 regex; make `_split_runs` drop a lone out-of-order spike (when the previous hit
is higher than both its predecessor and the current hit).

**Result:** fixed *some* (SHW 23→23, and GIS/MCD still recover) but **NOT mid-sequence intruders**
(CVX still 23→3, GS 20→12, TGT 20→12). → still has collateral → **DISCARDED.**

**Why it's incomplete — there are TWO intruder patterns:**
- **(a) spike-then-resume:** `…1, [10-intruder], 1A, 1B…` — the intruder is the *previous* hit; the
  current resumes. (single-intruder-tolerance handles this — SHW fixed.)
- **(b) mid-sequence dip:** `…14, [10-intruder], 15, 16` — the intruder is the *current* hit (CVX's
  `Item 10 Executive Officers` sits between Item 14 and Item 15). The single-intruder check fails here
  because the intruder's order (10) is below its predecessor (14), so `order >= cur[-2]` is false.

**Why the obvious fix (drop any local spike/dip) is WRONG:** it would also drop the body's first item
at the legitimate **TOC→body restart** (`…TOC-16, [body-1], body-1A…`): body-1 is lower than both
neighbors, so a neighbor-only rule deletes it. An intruder and a restart look identical to neighbor
checks.

## The CORRECT-fix design (the next probe)

Distinguish intruder from restart with a **one-element lookahead**: when the current hit causes an
order decrease, ask *"does the NEXT hit resume at/above the run's last (pre-dip) order?"*
- **yes →** the current was a lone intruder (CVX: after `Item 10`, `Item 15` resumes past `Item 14`) →
  drop it, continue the run.
- **no →** a genuine restart (TOC→body: after `body-1`, `body-1A` does NOT resume past `TOC-16`) →
  split.

This handles both (a) and (b) AND preserves the TOC→body split. It needs careful implementation +
a full G9 re-verification (the whole point: prove zero collateral on the 1,734 before keeping).

## A1+A2-v2 (one-element-lookahead `_split_runs`) — attempted, CONVERGING but still DISCARDED

**Probe:** the lookahead design above — on an order dip, drop the intruder iff the NEXT hit resumes
at/above the run's last order; else split (restart). Handles both intruder shapes (a) and (b).

**G9 result (re-segment 1,734):** unchanged=1499, recovered(0→N)=**38**, improved(N→more)=**137**,
same-count-diff-boundary=25, **DEGRADED(N→fewer)=35**.
- The catastrophic cases are FIXED: **CVX 23→23, GS 20→20, TGT 20→20, SHW 23→22**; GIS still 0→21.
- Collateral degradations dropped **156 → 35**. Big improvement, approach validated.
- **But 35 degradations remain, some catastrophic** (ED 20→2, WMT-98 14→2, GS-07 12→4, SLB-03 16→5):
  the lookahead OVER-DROPS real headers in some structures (a third, not-yet-characterised pattern).
- 137 "improved" + 25 boundary-shifts are unclassified (some are legit separator-less recoveries;
  some boundary-shifts could threaten char-gold IoU — the char-gold gate was not even reached).

→ **DISCARDED** (35 degradations ≠ zero collateral). The approach is right and converging; it needs
one more refinement on the over-drop pattern (ED-class) + then the char-gold + no-false-header gates.

## A1 — KEPT (two-pass: strict, relaxed only on empty) ✅

The three full-relaxation probes failed because they applied the loose regex to EVERY filing, so the
cross-ref false-positives it admits over-widened clean filings. **The clean fix is to confine the
relaxation to the filings that need it:**
- **STRICT pass first** (separator-required) — byte-identical to before; clean filings are unaffected.
- **RELAXED pass ONLY when the strict pass yields 0 items** (the OXY/GIS empty cluster) — the
  separator-less recogniser + the intruder-tolerant (one-element-lookahead) run split.

**This makes G9 zero-collateral BY CONSTRUCTION** (a non-empty clean filing never reaches the relaxed
path). Verified on the 1,734 cached canonicals:
- **recovered (0→N) = 38** (the empty cluster, incl. GIS 0→21); **DEGRADED = 0; improved = 0;
  same-count-boundary-shift = 0.** Clean filings literally unchanged.
- **GIS char-gold IoU = 1.0000 on all of {1,1A,7,8}** (byte-exact to the frozen human gold); the 5
  clean char-gold are byte-unchanged (strict pass). No-false-header guard holds; all segment tests
  pass; offline suite 90 passed.

→ **A1 KEPT.** It recovers the `empty(0_items)` cluster with provably zero collateral. The separator-
less RED target is now a normal passing test.

## A2 — KEPT (conditional Item-1-missing retry) ✅

Same insight as A1: confine the intruder-tolerant run split to the filings that need it. A2's
intruders (in-prose cross-references like `Item 1A. Risk Factors` / `Item 4-08(g)`) PASS the strict
regex, so the strict pass DOES segment but drops the lead item. Trigger: **Item 1 missing** in the
strict result → retry the SAME strict hits with the one-element-lookahead intruder-tolerant split;
keep it ONLY if it recovers Item 1 without losing coverage (a clean filing has Item 1 → never
retries → G9 zero-collateral by construction; a genuinely Item-1-absent filing is never forced).

**Verified (A1-baseline vs A1+A2 on 1,735 cached):** Item-1-recovered = **72** filings (lead_missing
+ coverage_partial), **COLLATERAL (Item-1-present filings changed) = 0**, every changed filing
recovered Item 1. XOM 19→22 (Item 1 back), DUK 9→19 (Item 1 back). GIS char-gold IoU still
[1.0,1.0,1.0,1.0]; offline suite green; A2 RED target flipped to a normal passing test.

→ **A2 KEPT.** The "hard, coupled" run-selection problem fell to the same conditional-fallback shape
as A1 — recovering 72 lead-missing / partial-coverage filings with provably zero collateral.

## Disposition (Step A so far)
- **A1 KEPT** + **A2 KEPT** (`sec10k/segment.py`). Empty cluster + lead-missing/partial-coverage
  recovered cleanly (38 + 72 filings), provably zero collateral via the two-pass / conditional-retry
  shape. Three early over-widening attempts were discarded by G9 first.
- **The guards did their job:** G9 + the structural-pass demotion discarded **three** over-widening
  attempts that a label-free metric would have rewarded, before the clean two-pass passed. No degrading
  fix shipped. This is the methodology working end-to-end.
- **Round-3 under-scoped A1** — it needed the two-pass insight, not a one-line regex change. The
  full-relaxation approach (for the ~137 PARTIAL-segmentation filings that strict already handles) is
  **deferred / noted** — it requires the ED-class over-drop characterisation and is a separate,
  riskier probe; not needed to recover the empty cluster.
- **A2** (cross-ref intruder on filings that DO segment — `lead_missing_high_cov` / `coverage_partial`)
  and **A3** (ingest robustness) remain. Note: A2 is the same run-selection family; A3 is low-value
  (callers already handle the exception). Next priorities TBD with the human.
- `round4/a1` holds the kept A1; rulers (Step B) stand. Nothing merged, nothing pushed.
