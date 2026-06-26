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

### Re-proposed after audit feedback (two rule corrections — still PROPOSED, not frozen)

The first proposal had two errors the auditor caught; both fixed and re-proposed:
- **Presence = HEADING-EXISTS, not content-substance.** A headed `Item X` section is **present**
  even if its content is "None." / "Not applicable" / "incorporated by reference to the proxy" —
  the registrant addressed the item in place. **Legitimately-absent** = no `Item X` heading in the
  filing **at all**. ("None" is an answer, not a missing section.)
- **Dropped the `incorporated-by-reference` category** (taxonomy mismatch). Production `Status` has
  only 3 values and no "incorporated"; a headed see-proxy Part III item is found by the segmenter →
  production `present`, so a separate gold category manufactured false mismatches. Folded into the
  **2-truth-category** scheme (present / legitimately-absent); `_GOLD_CAT` updated to drop the key.

Labels were **reconciled against measured production output** (header-occurrence counts + status):
where production is right (headed item → present) the gold agrees; where production is **wrong** the
gold says legitimately-absent and Signal D reports the mismatch. **Cells changed from proposal 1**
were all on the **full-10-K controls** (the amendments were already correct): apple 1B/4/6/9B/9C/16
and 10–14 → present; msft-2023 the same (1C stays legitimately-absent, no heading); msft-1996 10–13
→ present. **The two amendments are unchanged.**

**Measured Signal D vs the re-proposed gold (current, form-blind):**

| filing | form | Signal D | mismatches |
|---|---|---|---|
| apple-fy2024 | 10-K | **23/23** | none (clean control) |
| msft-fy2023 | 10-K | **22/23** | 1C (production flags a no-heading, pre-effective-date item as failure — a real error, constant) |
| msft-fy1996 | 10-K | **20/23** | 7A/9A/15 (pre-2001 era items production wrongly expects — real errors, constant) |
| chemed-amend-fy2024 | 10-K/A | **13/23** | 10 form-blind `extraction_failure`s on no-heading out-of-scope items |
| scwo-fy2025-amend | 10-K/A | **12/23** | 11 form-blind `extraction_failure`s |

The form-aware fix (probe #2, **post-freeze**) would lift the two amendments to **23/23** (the
form-blind failures become `legitimately_absent` → match) **while the full-10-K controls stay
fixed** (23/23, 22/23, 20/23 — their mismatches are real era-errors the fix does not touch). The
re-proposed gold also independently **catches real production errors** (1C date boundary, pre-2001
7A/9A/15) — evidence it is a ruler reading truth, not a copy of production. **Control 3a still
fires** (72 offline tests green network-free).

> **PAUSE — HUMAN-AUDIT CHECKPOINT (G7).** The proposed labels are **regression-anchors only, not
> trusted truth**, until the user audits and freezes them. **Signal D will gate the form-aware fix
> (probe #2) ONLY against the user-frozen reference — never against these agent-proposed labels.**
> Execution stops here for round-2 until the audit is returned. The `uncertain` lists in the gold
> flag the present-as-"None"-section vs legitimately-absent judgement calls for the auditor; the
> two amendments carry no uncertain cells (their structure is unambiguous).

---

## Iteration 2 — probe #2: re-attempt the form-aware `expectation()` fix → **KEEP** (legitimately earned against the frozen independent signal)

Reference **frozen by human audit 2026-06-26** (labels confirmed verbatim). Re-applied the
round-1 form-aware fix (thread `raw.form`; `/A` → Part I-II `OPTIONAL`; `template.py` + `pipeline.py`
only — not the segmenter/invariants/scorer).

**Measured against the frozen Signal D + the geometry control:**

| filing | role | Signal D before → after | Signal A (`struct_ok` / cov) |
|---|---|---|---|
| chemed-amend-fy2024 | AMENDMENT | **13/23 → 23/23** | True / 0.311 — **unchanged** |
| scwo-fy2025-amend | AMENDMENT | **12/23 → 23/23** | True / 0.885 — **unchanged** |
| apple-fy2024 | control | 23/23 → **23/23** | unchanged |
| msft-fy2023 | control | 22/23 → **22/23** (1C still mismatched) | unchanged |
| msft-fy1996 | control | 20/23 → **20/23** (7A/9A/15 still mismatched) | unchanged |

**All four KEEP criteria met (measured, not assumed):**
1. **Signal D rises on the amendment cells against the FROZEN reference** — chemed 13→23, scwo
   12→23 (the form-blind `extraction_failure`s become `legitimately_absent`, matching the
   heading-exists truth).
2. **Full-10-K controls byte-unchanged** — 23/23, 22/23, 20/23 identical; the control mismatches
   (1C, 7A/9A/15) are real era-errors the form-aware fix correctly does *not* touch.
3. **Signal A (UPPER BOUND, not accuracy) unchanged** — `struct_ok=True` everywhere, coverage
   identical (chemed stays 0.311). **I did NOT make coverage form-aware to manufacture an A gain
   (G6 honoured).**
4. **Guard G1–G7 green** — G1 offline **72 green network-free**; G4 char-gold 5; **G5 silent-failure
   still 0** (verified: both amendments stay `needs_review=True` for *better* reasons — chemed by
   coverage-implausible + low-confidence, scwo by the boundary cross-check on items 10/12/13 — so
   removing the false `extraction_failure` flood did NOT create a silent failure); G6 no
   invariant/scorer loosened; G7 the reference is frozen and was not edited to pass; G2/G3
   regex/fallback untouched.

**Decision: KEEP.** This is **round-1's discard resolved correctly**: round 1 discarded this
verified-correct fix because no independent signal could see it. Round 2 first *built* the
independent, human-audited Signal D — which can **refute** (control 3a) and which **independently
catches real production errors** (1C, 7A/9A/15) — and only then earned the fix, because that signal
moved on the amendments while the controls, the geometry, and the silent-failure guard all held.
Not a proxy; a ruler.

---

_(probe #3 stratified eval growth, #4 failure-mode discovery — next, then STOP + report.)_
