# Autoresearch Round 1 — Findings (human narrative)

Branch: `autoresearch/round-1` (isolated worktree, off `main` @ `1e91cb9`). **NOT pushed, NOT
merged** — for review. Loop governed by `research/autoresearch-round-1-plan.md`; one probe per
iteration in ROI order (a → b → c → d); KEEP iff a real independent signal improves above noise
AND guard G1–G6 passes, else DISCARD + document.

> **Every structural-pass number in this document is an UPPER BOUND on robustness, NOT
> accuracy** (plan §1 Signal A): it is a label-free net for the *gross* failure tail; it cannot
> see interior boundary drift, scattered-tail drops, or a >40%-covering swallow. The only
> accuracy floor is the 5 human-audited char-gold filings (Signal B).

Signal A operationalized per filing = `structural_ok ∧ round_trip_ok ∧ coverage_plausible`
(label-free invariants from `validate.py`) **and** lead Item 1 present **and** big items
{1,1A,7,8} that are present each start with their own "Item N" header (`start_correct`).
Reported per stratum with N, never pooled.

---

## Iteration 0 — Baseline

- **Signal A (UPPER BOUND, not accuracy):** geometry-pass **14/15** (the one fail is an
  amendment that legitimately lacks Part I → low coverage). `ge-fy2023` dropped on a transient
  EDGAR disconnect (N=15); it is the GE-class B2 ceiling and would structural-fail regardless.
- **Signal B gold recall:** **1.0 over 5** human-audited filings.
- **Silent-failure:** 0/15. **G1:** offline suite 67 green, network-free.

## Iteration 1 — probe (a): stratified eval growth → **KEEP**

Added two accession-pinned, immutable filings filling real strata gaps (verified to fetch +
extract on current code before pinning):

| new filing | accession | stratum filled | result on current code |
|---|---|---|---|
| `msft-fy1996` | `0000891020-96-001130` | 2nd pre-2001 **SGML** | clean **structural-pass**; items 1/7/8 header-anchored; coverage 0.93; recall 1.0 |
| `wmt-fy2003` | `0000104169-03-000005` | **retail** sector + **2001–2008 HTML** era | **structural-FAIL** (full Signal A): lead Item 1 dropped (PART-glued); coverage 0.474; recall 0.8; **flagged** (`needs_review`) |

- **Signal A (UPPER BOUND, not accuracy):** geometry-pass **16/17**; **full** Signal A (incl.
  lead-Item-1-present) **15/17** — `wmt-fy2003` passes the 3 geometry invariants but fails the
  lead-item component (Item 1 dropped). Per-stratum: retail **1/1 (new)**, sgml **2/2**, html
  **3/3**, ixbrl 11/12 — existing strata **unchanged** (G5).
- **Signal B gold recall:** **1.0 over 5** (unchanged; gold stays 5, not auto-frozen — G4).
- **Signal C:** **+1 — FM-1 PART-glued lead-item drop** (`wmt-fy2003`), flagged-not-silent, a
  class not previously named in this repo (see `round-1-failure-modes.md`).
- **Guard:** G1 67 green network-free ✓ · G2 existing clean filings stay `regex` ✓ · G3 fallback
  did not fire on the new filings ✓ · G4 gold = 5 ✓ · G5 existing filings unchanged, silent 0/17
  ✓ · G6 no ruler change ✓.
- **Decision: KEEP** — Signal A resolving power up **and** Signal C +1, guard fully green.
- **Honesty note:** `ge-fy2023` again hit a transient EDGAR `RemoteProtocolError` (consistent
  flaky fetch on that ~4 MB filing); excluded from N, not a code signal.

---
