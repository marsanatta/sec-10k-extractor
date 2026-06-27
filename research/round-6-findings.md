# Autoresearch Round 6 — Findings (FM-4 cross-reference-index)

**Outcome: STOPPED at the decisive viability experiment. (B) the title-locator is DEAD for the RED
anchor; FM-4 genuinely needs the decorrelated CRF (approach D), which is out of scope.** No production
code was touched; nothing built; nothing pushed. This is the discipline working — a cheap read-only
experiment killed an approach before any tier was built, exactly as A1's three over-widening probes
were discarded by G9 before a clean fix shipped.

## What the experiments established (read-only, evidence not assumption)

### 1. The cluster exists and the index table is parseable (B looked promising at first)
`scratch/r6_viability_B.py` over the 1,735 cache: **~30 FM-4 filings** (CROSS-REFERENCE INDEX +
coverage <0.30), concentrated by filer house-style — **Citigroup `0000831001` ×7** (not GE — the
earlier "GE-class" label was wrong), `0000773840` ×4, `0000063908` ×4, `0000040545` ×3. The index
table is clean (`Item 1. Business … / Item 1A. Risk Factors …`). A crude prefix-match reported up to
14/17 item titles as "standalone body headings".

### 2. The crude count was inflated, and the RED anchor's failure is BOUNDARY, not presence
The pinned RED anchor is `intc-fy2018` (Intel FY2018, `0000050863-19-000007`, `expected_present`
= [1,1A,7,8]). Tracing the **current** `segment()` on it (canonical fetched + cached for the round):
- It returns **21 keys (1–16), but every span sits in [492446, 500468]** — i.e. **inside the
  CROSS-REFERENCE INDEX TABLE itself** (which begins at 492214). The regex matched the table's
  `Item N. Title` lines and tiled them; **coverage = 0.016 (1.6%)**, the entire body (0–492000) is
  uncovered. So presence is *already* "green" (the keys exist, from the table) — **the real failure is
  the boundary/coverage**, flagged `needs_review`, not silent. My plan's "intc RED→GREEN on
  expected_present" framing was a misread: presence was never the problem.

### 3. The decisive kill: intc's body has NO tileable item structure
The body is a **thematically reorganized "integrated report"**, not an item-ordered 10-K. Its standalone
uppercase headings are Intel's own themes — `A YEAR IN REVIEW`, `OUR STRATEGY`, `MAKE THE WORLD'S BEST
SEMICONDUCTORS`, `HUMAN CAPITAL`, `OPPORTUNITIES`, `CHALLENGES` — not item titles. Locating the real
section starts by title gives positions that are **scattered and OUT OF CANONICAL ITEM ORDER**:

```
Item 1 @12118 → Item 7 (MD&A) @66819 → 7A @128384 → 1A (Risk Factors) @153021
→ Item 2 (Properties) @225395 → Item 8 @232716 → Item 3 (Legal) @448951
```

MD&A precedes Risk Factors; Properties precedes the financial statements. **There is no monotonic
tiling**, and each title also occurs multiple times (TOC + real section + cross-references). A
title-locator would emit overlapping, out-of-order garbage — it cannot produce correct boundaries, and
there is no clean contiguous section to char-gold.

### 4. The non-intc filers fail the same way — the STOP is class-wide, not anchor-specific
Checked the cleaner-looking filers (line-start title-heading match + monotonic-order test), since the
crude (B) count had flagged them at 13–14/17:
- **`0000773840` ×4** (the richest, 13 titles): **NOT monotonic** — Item 7 (MD&A) @44645 precedes 1A
  @71056, and Items 2/3/4/5 cluster inside ~1,250 chars (159591–160841), i.e. a TOC/list, not real
  section bodies. Not tileable.
- **Citigroup `0000831001` ×7: 0** line-start title headings (the earlier 13–14 were prose
  `businesses…` false-positives). Not tileable.
- **`0000063908` ×4**: its 9 title headings all sit in 5272–7771 — the **TABLE OF CONTENTS**, not the
  body. Not tileable.

So the crude (B) count was inflated by three things — **prose false-positives, TOC occurrences, and a
loose `startswith`**. Once a heading must be line-start AND the items must tile in canonical order,
**no FM-4 filing in the cache qualifies.** The STOP is a property of the class, not of intc alone.

## Why this is a genuine STOP (not a gap to grind)
- **(A) page→offset is dead** (verified earlier: `to_canonical` strips page markers).
- **(B) title-locator is dead for the anchor** (this round: items scattered/out-of-order, body
  thematically reorganized, titles non-unique). It might partially help cleaner filers (Citigroup), but
  the gate is anchored on intc, and the same integrated-report scattering applies to the class.
- **(C) preserve page markers in normalize** is invasive (shifts every existing char-gold offset) and
  still leaves scattered items — not worth the blast radius.
- **(D) decorrelated CRF / structural line-labeller** is the only approach that can find scattered,
  header-less item bodies. It is the SAME tool the named common-mode ceiling (FM-2) needs, and is
  **STRETCH / out-of-scope** per `docs/` and `research/todo-exploration-crossref-index-handling.md`.

## Disposition
- **FM-4 stays a documented, FLAGGED (not silent) limitation** (ANALYSIS.md §6). This round upgrades it
  from "asserted hard" to **"empirically proven CRF-territory: the body has no tileable item structure,
  the index only page-maps, and pages are stripped."**
- The honest call from the strategic discussion holds: the segmenter's clean-win era (A1/A2/A3) is over;
  FM-4 is not a clean win, and the no-silent-failure design already covers it. Effort is better spent on
  the verification story (char-gold floor) than on grinding this tail.
- `round6/crossref-index`: only `research/round-6-plan.md` + this findings doc. **No production code
  touched; offline suite untouched; nothing pushed.**
