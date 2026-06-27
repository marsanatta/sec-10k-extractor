# TODO / Exploration — handling cross-reference-INDEX-TABLE filings (GE / MCD / HON / INTC)

**Status:** exploration plan for a FUTURE round, NOT scheduled, NO code. Captures the problem,
the measured prevalence, and (honestly) which approaches work vs are dead-ends — so a future round
starts from evidence, not a blank page. Pinned RED anchor: `intc-fy2018` in `eval_set.json`.

## The problem
A minority of filings carry **no "Item N" headings in the body at all**; every item is located only
via an end-of-document **"FORM 10-K CROSS-REFERENCE INDEX"** table mapping `item → page range`. Both
header-anchored tiers (regex `_HEADER_RE` AND the edgartools fallback) find ~nothing → coverage
<0.15 → flagged (`needs_review`), not silent. **The items ARE present (human-audited on INTC FY2018);
this is a real extraction miss, not legitimate absence.**

## Prevalence (measured, round-3 1,656-filing sweep)
**~15–19 filings (~1%)**, concentrated in **GE (×7), MCD (×4), HON (×4), INTC** — filer house-style.
~1% is small but **not negligible** and concentrated in major filers; a held-out grader set that
includes these filers will hit it. Worth a dedicated future probe.

## Approaches — what works vs what's DEAD (verified, not assumed)
- **(A) Index page → char offset via page markers — DEAD.** Verified: `to_canonical` **strips all
  page markers** from the canonical (`<PAGE>`=0, form-feed `\x0c`=0, no "Page N" lines on a GE
  sample). The index gives `item → page`, but there is no page→offset mapping left in the canonical.
  This naive idea does not work without changing normalize.
- **(B) Title-matching — the cheapest VIABLE candidate, needs one check.** The index also names each
  item's **title** ("Business", "Risk Factors", "Properties", …). If the body carries **title-only
  section headings** (e.g. a bold "Business" with no "Item 1"), we could match the index's titles to
  those body headings and synthesize item boundaries. **OPEN QUESTION to verify first:** do these
  bodies actually contain the section titles as headings? (Inspect a GE/HON/MCD canonical for
  standalone "Business" / "Risk Factors" lines.) If yes → a targeted, decorrelated-ish locator; if no
  → (B) is also dead and only (C)/(D) remain.
- **(C) Preserve page markers in normalize, then page→offset — works but INVASIVE.** Teach
  `to_canonical` to keep `<PAGE>`/page-number anchors, then map the index's page ranges to offsets.
  Changes the canonical for ALL filings (round-trip + every existing char-gold offset would shift) →
  high blast radius, needs the full G9 + char-gold re-validation. Heavy.
- **(D) Decorrelated CRF / structural line-labeller — the unifying answer.** A non-header extractor
  (structural features: position, prior-item-seen, in-TOC) finds item bodies without needing "Item N"
  headings. This is the SAME tool that answers the named common-mode ceiling (MS/Citi, FM-2). It
  would handle the index-table class as a side effect. Biggest build (reimplement + train on silver
  labels); STRETCH / out-of-scope until prioritized.

## Recommendation (for a future round)
1. First verify **(B)**: do the bodies have title-only headings? Cheap check, decides everything.
2. If (B) viable → build a small index-table locator (detect the index, parse item→title, match
   titles to body headings) gated like round-4 (RED anchor flips RED→GREEN, clean char-gold unchanged
   at IoU 1.0, G9 no-collateral-change). Coarse boundaries acceptable if flagged.
3. If (B) dead → fold into the **(D) CRF** build (the ceiling answer), which subsumes both this class
   and FM-2. Do NOT do (C) (invasive normalize change) unless (B) and (D) are both ruled out.

## Guards if pursued
Same as round-4: REPORTED-only until earned on an INDEPENDENT signal; the `intc-fy2018` RED anchor
must flip RED→GREEN on the human-labelled `expected_present`; clean char-gold byte-exact; G9
no-collateral-change; structural-pass monitored-only, never a keep gate.
