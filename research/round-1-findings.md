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

## Iteration 2 — probe (b): form-type-aware `expectation()` → **DISCARD** (verified-correct, but moves no climbable signal)

**Change tried:** thread `raw.form` into `FilerProfile`; in `expectation()`, when the form ends
in `/A`, return `OPTIONAL` for Part I-II items (an amendment may amend only Part III, so Part I-II
absence is legitimate, not an extraction failure). Touched only `template.py` + `pipeline.py`
(classification) — **not** `validate.py` invariants or the scorer, so G6 is not implicated.

**Measured before → after (form-blind → form-aware):**

| filing | form | `extraction_failure` | `needs_review` | `structural_ok` / `coverage_plausible` |
|---|---|---|---|---|
| chemed-amend-fy2024 | 10-K/A | **10 → 0** | True → True | True / False — **unchanged** |
| scwo-fy2025-amend | 10-K/A | **11 → 0** | True → True | True / True — **unchanged** |
| apple-fy2024 (control) | 10-K | 0 → 0 | False → False | **unchanged** |
| msft-fy1996 (control) | 10-K | 3 → 3 | True → True | **unchanged** |

- **The fix is verified-correct.** The independent control passes exactly as the plan specified:
  amendments stop emitting Part-I/II `extraction_failure`s (10→0, 11→0) **while full 10-Ks are
  unchanged** (apple 0→0, msft-1996 3→3). It is not gaming anything.
- **But no climbable signal moved.** **Signal A is unchanged** — geometry (`structural_ok`,
  `round_trip_ok`, `coverage_plausible`) is template-independent, so reclassifying absent items
  cannot change structural-pass (chemed still fails coverage; scwo still passes geometry).
  **Signal B** unchanged. **Signal C** none. Even `needs_review` did not move (amendments stay
  flagged by *other* drivers), so the effect lands purely on the `extraction_failure` count — a
  member of the **deliberately-forbidden classification/presence proxy family**.
- **G1:** offline suite **67 green network-free *with* the fix** — no guard failure. The discard
  is purely the KEEP rule, not a broken guard.
- **Decision: DISCARD** (code reverted to the iter-1 committed state). Per the KEEP rule —
  and probe (b)'s own stated condition "Signal A rises on amendments" — no independent climbable
  signal improved, so it does not qualify.

**Meta-finding (the loop caught a flaw in its own approved plan):** probe (b)'s premise that the
form-type fix would *raise Signal A* was **wrong** — a template/classification fix is orthogonal
to structural geometry and can never move the label-free structural-pass signal. The fix's real
benefit (correct amendment classification) is **invisible to all three of this round's
independent signals**. I deliberately did **not** try to manufacture a Signal A gain by making
`coverage_plausible` form-aware for amendments — that would relax the coverage floor for a subset
to make them "pass", a textbook **G6 ruler-loosening** → auto-discard.

**Recommendation (carried out of this round):** the form-aware `expectation()` is a genuine
correctness improvement and should be adopted in a future round whose signal set includes a
**classification-correctness** metric (e.g. "amendment false-`extraction_failure` rate, with
full-10-K classification held fixed as the decorrelated control"). It is recorded here, not
merged, because this round's independent signals cannot see it — keeping the loop honest.

---

## Iteration 3 — probe (c): bounded structural sweep → **KEEP** (Signal C +2; named ceiling reached)

**Bounded N=3** (logged explicitly — no silent truncation), accession-pinned, each fetched and
measured on current code:

| swept filing | accession | items / tier | flagged? | verdict |
|---|---|---|---|---|
| amt-fy1997 | `0000927016-98-001444` | 1 / regex (cov 0.95) | `needs_review=True` | **confirmation** — GE-class collapsed-body (B2), new era/sector |
| ms-fy2024 | `0000895421-25-000304` | **0 / regex** (cov 0.0) | `needs_review=True` | **FM-2 NEW** — header-text-stripped common-mode (B3) — **the named ceiling** |
| hon-fy2024 | `0000773840-25-000010` | 7 / fallback (`struct_ok=False`, lead dropped) | `needs_review=True` | **FM-3 NEW** — no-separator header |

- **Signal C: +2** genuinely new flagged-not-silent classes (FM-2, FM-3), each with a concrete
  accession; amt-1997 is a confirmation (not counted). See `round-1-failure-modes.md`.
- **Signal A (breadth, UPPER BOUND not accuracy):** all three are structural-*fails* on current
  code — but **all flagged**, **0 silent**. The abstention gate holds on the swept tail.
- **Durability:** the 3 swept cases were added to `eval_set.json` as accession-pinned tracked
  REDs so the ceiling/confirmation cases are permanently measured (regression anchors).
- **Guard:** G1 unaffected (sweep is measurement-only, no code change) ✓ · G2/G3 no code change ✓
  · G4 gold = 5 ✓ · G5 existing filings untouched; all swept fails flagged (0 silent) ✓ · G6 no
  ruler change ✓.
- **Decision: KEEP** — Signal C +2, guard green.

**STOP condition S1 reached — the named ceiling.** FM-2 (Morgan Stanley FY2024) is the
**dual-extractor common-mode (B3)**: both the regex and the edgartools fallback are
header-anchored, so on an iXBRL filing whose "Item N" labels are presentation-only spans they
fail **together** → 0 items, flagged. No header-anchored tier can recover this; the only fix is a
**decorrelated non-header / CRF line-labeller — out of the 4-day scope.** The extraction-robustness
failure tail has reached the named ceiling; we disclose it and do not fake a green.

---
