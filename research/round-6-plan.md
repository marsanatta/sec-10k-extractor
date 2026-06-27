# Autoresearch Round 6 — Plan (FM-4: cross-reference-INDEX-TABLE filings)

**Status: PLAN ONLY — no code touched.** Baseline = clean `main` (has A1/A2/A3 + the round-5
char-gold). Work in worktree `round6/crossref-index` (derived from `main`); reviewed + merged,
never pushed. This plan is **grounded in a decisive read-only viability experiment already run**
(`scratch/r6_viability_B.py` + a GE/Citigroup spot-check), so its premise is evidence, not a guess.

## Target

FM-4 (ANALYSIS.md §6): filings whose body carries **no "Item N" headings**; items are located only
via an end-of-document **"FORM 10-K CROSS-REFERENCE INDEX"** table mapping `item → title → page
range`. Header-anchored tiers (regex + edgartools) find ~nothing (coverage <0.15) → flagged
(`needs_review`), **not silent**. The items ARE present (human-audited on `intc-fy2018`). RED anchor:
`intc-fy2018` (pinned in `eval_set.json`).

## (B) viability — RESULT (the decisive first experiment, already run)

Scan of the 1,735 cached canonicals for "CROSS-REFERENCE INDEX" + coverage <0.30 found **~30 FM-4
filings**, concentrated by filer house-style: **Citigroup `0000831001` ×7, `0000773840` ×4,
`0000063908` ×4, `0000040545` ×3**, plus a long tail. (My label "GE-class" was wrong — `0000831001`
is **Citigroup**, file 1-9924.)

**Verdict: (B) is VIABLE for PARTIAL, COARSE recovery — not dead, but not a clean full-recovery.**
Evidence (Citigroup FY2020 spot-check):
- The index table is clean and parseable: `1.\nBusiness\n4–31, 123–128, 131, …` → item → title → pages.
- **A subset of item titles DO appear as standalone body headings** (`Business`, `Risk Factors`,
  `Properties`, `Quantitative and Qualitative…`, `Controls and Procedures`, `Executive
  Compensation`, `Exhibits…`) — **~7–8 of 17 items**, not the 14 the crude prefix-match reported
  (it over-counted prose like `businesses. In addition,` / `businesses other than`).
- **Two honest limits this exposes:**
  1. **Partial coverage.** Only ~7–8 of 17 titles are findable as headings; the rest are integrated
     into prose with no anchor. Recovery is a subset, not the full template.
  2. **Coarse boundaries / scattered items.** The index maps Item 1 to *multiple* page ranges
     (`4–31, 123–128, 131, …`) — integrated MD&A means an item's content is **scattered**, so a
     title-anchored boundary captures only the *primary section start → next title*, not the full
     item. char-gold-ability is therefore uncertain (the "true" contiguous boundary is ill-defined).

## Approach to build (if approved): an ADDITIVE tier "T-index" — never touches the common case

Fires **only** when the header-anchored result has coverage < 0.15 (the FM-4 signature), so every
clean filing and every A1/A2/A3 filing is byte-identical by construction.
1. **Detect** the `CROSS-REFERENCE INDEX` table; parse `item → title` (ignore the page column — pages
   are stripped from the canonical, approach (A) is dead, verified in the TODO).
2. **Locate** each parsed title as a **standalone body heading** with a PROSE-REJECTING matcher: the
   line equals / tightly starts-with the title, is short, is not a sentence continuation, and is not
   the index/TOC occurrence itself. (The "businesses" false-positive class is the thing to beat.)
3. **Synthesize** boundaries between consecutive located titles (in document order). Items whose title
   is not found as a heading are **left absent + flagged**, never guessed. Boundaries are labelled
   COARSE (primary-section) in provenance.

## (1) Climbable INDEPENDENT signals (none is self-consistency)
- **`intc-fy2018` RED anchor flips RED → GREEN** on the human-labelled `expected_present` (the
  primary keep signal).
- **A new human-audited char-gold entry** for ONE cross-ref-index filing where a clean contiguous
  primary section exists (boundary IoU) — IF char-gold-able; if no item has a clean contiguous
  boundary, this signal is honestly N/A and recovery is presence-only.
- **Cluster recovery count** (how many of the ~30 FM-4 filings go from ~0 items to a meaningful set).
- **Structural-pass stays UPPER-BOUND-on-robustness, NOT accuracy, and monitored-only** — never a keep
  gate (a looser locator raises it on garbage → the proxy trap A1 round-3 already caught).

## (2) GUARD — DO NOT BREAK EXISTING FUNCTION (every item checked, can-fail)
- Offline fixture suite **green AND network-free** (currently **96 passed / 1 skipped**, `SEC_EDGAR_USER_AGENT` unset).
- regex stays PRIMARY; **A1/A2/A3 unchanged**; T-index only fires at coverage < 0.15.
- **G9 no-collateral-change proof**: re-segment the 1,735 cached canonicals offline; **ONLY the FM-4
  filings (coverage <0.15) may change; everything else byte-identical.** (Same tool that gated A1/A2/A3.)
- char-gold stays **human-only + frozen**, never auto-frozen from the locator's output.
- No ruler loosened in `validate.py` / `evalkit.py` (coverage thresholds, invariants TIGHTEN-only).

## (3) KEEP / DISCARD rule
KEEP iff **`intc-fy2018` flips RED → GREEN** AND a real independent signal improves (char-gold IoU on a
golded filing, or cluster presence-recovery on the human-labelled anchor) AND the GUARD holds (G9 zero
-collateral + suite green + A1/A2/A3 byte-identical). Otherwise **DISCARD + document** in findings.

## (4) STOP conditions
- The prose-vs-heading separation is unreliable (the locator admits false headings it can't filter) →
  the recovery is not trustworthy → **STOP, fold into CRF** (out of scope).
- No FM-4 filing has a clean contiguous primary section to char-gold AND presence-recovery on the anchor
  is the only signal → record as **presence-only partial recovery**, decide with the human whether that
  clears the keep bar.
- Recovery stays too partial/coarse to be worth the tier's complexity → **STOP, document as the FM-4
  ceiling**, defer to the decorrelated CRF (which subsumes this class + FM-2).
- Budget.

## (5) Where findings go
`research/round-6-findings.md` (the Modify→Verify→Keep/Discard trail). **Nothing pushed.**

## Honest framing (carried from the strategic discussion)
FM-4 is a HARD, ~1% tail; the no-silent-failure design already FLAGS it (not a correctness hole). The
(B) result confirms a **bounded, partial** win is available (not an A1/A2/A3-shaped clean cluster). This
round is worth one disciplined attempt because the recovered presence + a char-gold anchor would
strengthen the format-variance and verification story — but the STOP conditions above are real: if it
can't be cleanly char-golded or cleanly separated from prose, the right move is to document the ceiling
and stop, not to grind.
