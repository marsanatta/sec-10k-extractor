# Autoresearch Round 2 — Findings (human narrative)

Branch: `autoresearch/round-2` (fresh isolated worktree, off the new `main` @ `daf015b`). **NOT
pushed, NOT merged** — for review. Loop governed by `research/autoresearch-round-2-plan.md`; one
probe per iteration, ROI order #1→#2→#3→#4; KEEP iff a real independent signal (A/B/C/**D**) moves
above noise AND guard G1–G7 passes, else DISCARD + document.

> **Every structural-pass number is an UPPER BOUND on robustness, NOT accuracy** (plan §1
> Signal A). The accuracy floors are the 5 human-audited char-gold (Signal B) and the
> human-audited classification reference (Signal D), once frozen.

---

## Iteration 0 — Baseline (new main, `daf015b`)

Re-measured on the merged main (same commit as this worktree's base; eval run minutes earlier):
- **Signal A (UPPER BOUND, not accuracy):** structural-ok **19/20** (N=20; `ge-fy2023` transient
  EDGAR drop, the B2-ceiling filing). Per-stratum unchanged from the round-1 merge.
- **Signal B gold recall:** **1.0 over 5** human-audited char-gold.
- **Signal C:** 0 new this round (baseline).
- **Signal D:** not yet built (this round's headline).
- **G1:** offline suite **69 green, network-free**. **G4:** char-gold **5**.

## Iteration 1 — probe #1: BUILD Signal D (classification-correctness) → **KEEP** (built + independent); then **PAUSE for human audit**

**What was built:**
- **The scorer** `classification_match_rate` (`sec10k/evalkit.py`): per-item, does the production
  status category (`present` / `ok-absent` / `failure`) match the human reference category
  (`present` / `legitimately-absent` / `incorporated-by-reference`, the latter two collapsing to
  `ok-absent`)? Reported per form type. **Decorrelated from `needs_review`** — it compares
  classification to independent ground truth, item by item, not to any production flag. (A scorer,
  governed by G6: added, never loosened.)
- **The PROPOSED reference** `eval/classification_gold.json` — 3 full `10-K` (apple-fy2024,
  msft-fy2023, msft-fy1996) + 2 `10-K/A` (chemed-amend-fy2024, scwo-fy2025-amend), 23 cells each.
  **Labels were read-located from each filing's raw Part/Item structure in the canonical bytes —
  NOT from the production classifier or `result.items`.** The two amendments are the load-bearing
  cases:
  - **chemed-amend** (8.7 KB) contains ONLY Part II Item 5 + Part IV Item 15 → 21 cells
    `legitimately-absent` (out of the amendment's scope), 2 `present`.
  - **scwo-amend** contains Part III Items 10–14 (present as body — the amendment supplies what the
    original incorporated) + Item 15 → 6 `present`, 17 `legitimately-absent`. (Note the contrast:
    Part III is `present` here vs `incorporated-by-reference` in a full 10-K.)

**Independence proven (the review-bar crux):**
- **Control 3a (mutation refutation) FIRES** (`tests/test_classification.py`): flipping a
  genuinely-`present` item to `legitimately_absent` **lowers Signal D** — so the signal can
  *refute*, not merely confirm. A signal that could only rise would be a proxy; this one falls when
  classification goes wrong. ✓
- The form-blind-bug shape is captured: a gold `ok-absent` cell that production calls `failure`
  scores as a **mismatch** — exactly the amendment cell the form-aware fix would correct.
- **Control 3b (real-data full-scope `/A`)**: chemed-amend *does* amend a Part II item (Item 5),
  but the extractor finds it (`present`), so it does not exercise the "present-but-dropped → falsely
  excused" path. **No filing in this small set has a present-but-dropped Part-I/II item on a `/A`**,
  so the real-data over-broad-rule refutation is **unavailable** — stated honestly. Control 3a still
  proves the signal can fall; the real-data 3b is a noted limitation, not a claimed capability.

**Decision: KEEP** (probe #1) — Signal D is operational AND demonstrably independent (3a fires,
reference read-located), guard green (G1 **72 green network-free**; G4 char-gold 5; G6 scorer
added-not-loosened; G7 the reference is PROPOSED, frozen nothing; regex/fallback untouched).

> **PAUSE — HUMAN-AUDIT CHECKPOINT (G7).** The proposed labels are **regression-anchors only, not
> trusted truth**, until the user audits and freezes them. **Signal D will gate the form-aware fix
> (probe #2) ONLY against the user-frozen reference — never against these agent-proposed labels.**
> Execution stops here for round-2 until the audit is returned. The `uncertain` lists in the gold
> flag the present-as-"None"-section vs legitimately-absent judgement calls for the auditor; the
> two amendments carry no uncertain cells (their structure is unambiguous).

---

_(probe #2 form-aware fix, #3 eval growth, #4 discovery — deferred until the reference is frozen.)_
