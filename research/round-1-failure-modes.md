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
