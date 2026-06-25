# Autoresearch Round 1 — New Failure Modes (Signal C)

Each entry must be: (i) **flagged-not-silent** (its `needs_review` fires, verified through the
full pipeline — not fast-mode), (ii) **named** with mechanism + concrete accession, (iii)
**distinct** from the already-named classes (run-fragmentation, header-text-stripped,
no-separator, collapsed-SGML, 10-K/A scope, scattered-item). A mode that is merely a re-sighting
of a named class is logged as a confirmation, not a *new* mode (Signal C counts only genuinely
new classes).

---

## FM-1 — PART-glued lead-item drop (iteration 1, probe a)

- **Accession:** `0000104169-03-000005` (WAL MART STORES INC, FY2003, retail, HTML 2001–2008 era).
- **Mechanism:** the Part heading sits on the **same physical line** as Item 1 —
  `PART I ITEM 1. BUSINESS …` — so `PART I ` sits between the newline and `ITEM`, defeating the
  segmenter's line-start anchor `^[ \t>]*item`. Item 1 is never anchored; segmentation starts at
  the next clean header, **dropping Item 1** (Item 1A is *legitimately* absent — Risk Factors
  weren't required until FY2005, correctly classified by `expectation()`).
- **Measured (current code, regex tier):** items 2,3,4,5,6,7,7A,8,… present; **Item 1 missing**;
  coverage 0.474; the 3 geometry invariants (`structural_ok`, `round_trip_ok`,
  `coverage_plausible`) all **pass**, but the **lead-Item-1-present** component of full Signal A
  **fails**. Presence recall 0.8 (missed Item 1).
- **Flagged-not-silent:** `needs_review=True` (the `n_fail>0` driver fires) — the system does not
  silently return the broken segmentation. **Silent-failure rate stays 0/17.**
- **Distinct from named classes?** Yes — not run-fragmentation (the headers don't fragment into
  runs; Item 1's header simply isn't line-anchorable), not header-text-stripped (the "Item 1"
  token *is* present, just glued to PART), not collapsed-SGML, not 10-K/A, not scattered-item.
  **New named class for this repo.** (Independently corroborates a class the external scout run
  saw; surfaced here on a pinned accession, flagged.)
- **Fix candidate (NOT implemented this round):** tolerate an optional `(?:part[ \t]+[ivx]+[ \t]*)?`
  prefix before `item` in the header regex, recording the header start at the `item` token (a
  named group) so the span begins at "ITEM 1", not "PART I". Out of this iteration's one-probe
  scope; logged for a future round.

## FM-2 — header-text-stripped iXBRL common-mode (iteration 3, probe c) — **the named ceiling**

- **Accession:** `0000895421-25-000304` (Morgan Stanley, FY2024, finance, iXBRL).
- **Mechanism:** the "Item N" labels live only in **styled iXBRL spans** that `.text()` flattens
  away, leaving just the section *titles* — the literal "Item N" token is absent from the
  canonical. Both extractors are **header-anchored**, so the regex finds nothing **and the
  edgartools fallback also finds nothing**.
- **Measured (current code):** **0 items extracted**, `tier=regex` (fallback produced nothing
  either), `coverage_plausible=False`, `needs_review=True`.
- **Flagged-not-silent:** yes — 0 items + `needs_review=True`; the system does not silently
  return a broken/empty segmentation.
- **Distinct from named classes?** Yes — this repo names the common-mode only as a *partial-gate
  caveat* (§5.2 of ANALYSIS), never as a concrete filing class. **New named class**, and it is the
  **dual-extractor common-mode (playbook B3)** reached by a mainstream FY2024 large-cap.
- **CEILING (STOP S1):** neither header-anchored tier can recover this. The only fix is a
  **decorrelated, non-header second extractor (CRF line-labeller)** — **out of the 4-day scope**.
  This is the round's named ceiling; we disclose it, we do not fake a green.

## FM-3 — no-separator header (iteration 3, probe c)

- **Accession:** `0000773840-25-000010` (Honeywell, FY2024, industrial, iXBRL).
- **Mechanism:** headers render as `ITEM 1   About Honeywell` with **no `.`/`:` separator** after
  the number; the segmenter's `_HEADER_RE` requires a trailing separator, so regex finds **0
  headers** in a clean canonical.
- **Measured (current code):** regex 0 → **edgartools fallback partially rescues (7 items)**,
  `tier=fallback`, but `structural_ok=False` (the 7 don't tile cleanly) and **lead Item 1 dropped**;
  coverage 0.64; `needs_review=True`.
- **Flagged-not-silent:** yes.
- **Distinct from named classes?** Yes — not in this repo's named set. **New named class.**
- **Fix candidate (NOT this round):** relax the trailing-separator requirement (allow 2+ spaces +
  capitalized title), gated behind the run-selection prose filter to avoid false positives in
  prose ("item 1 of the agreement"). Risky; logged for a future round.

## Confirmation (not a new mode) — collapsed-body SGML

- **Accession:** `0000927016-98-001444` (American Tower, FY1997, reit, SGML). 1 item swallows the
  doc (coverage 0.954), lead Item 1 absent, `needs_review=True`. This is the **GE-class
  collapsed-body (B2)** already named in this repo (cf. `ge-fy2009`) — logged as a **confirmation
  across a new era/sector**, not counted toward Signal C.
