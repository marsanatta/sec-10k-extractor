# Confidence Scoring & Silent-Failure Detection (Design)

Synthesised from area 3 (SOTA eval) and areas 1–2. This is the differentiator the
assignment rewards: no existing tool emits confidence, and every naive segmenter fails
*silently* on legacy/non-standard filings. Our pipeline must (a) attach a calibrated
confidence to every extracted item, and (b) make silent failure structurally impossible.

## Principle: independent oracles only

Per the engineering-rigor rule, **self-consistency is not validation**. An LLM judging its
own output cannot catch *confident systematic* errors. Every confidence signal below is
either a hard structural fact or an **independent** second method — never the same model
re-checking itself.

## The validation stack → confidence signals

Ordered cheap→expensive. Each emits a pass/fail (or a numeric agreement) that feeds the
per-item and per-filing confidence.

1. **Structural invariants (free, hard gate).** Items appear in canonical order; each
   expected item present exactly once; spans are non-overlapping; the union of spans +
   inter-item gaps covers the source with no dropped bytes. Any violation = critical flag.

2. **Round-trip reconstruction (free, proves completeness).** Because extraction is
   *indexing* into the source (not generation), concatenating every span in source order
   (including the headers/gaps between them) must reproduce the source **byte-for-byte**.
   A mismatch proves text was dropped or duplicated. Note: round-trip proves *coverage*,
   not *correct labelling* — so it must be paired with the next signals.

3. **Independent dual-extractor agreement (cheap, catches mislabelling).** Run a
   rule/anchor extractor and an independent method (CRF line-labeller, or LLM on flagged
   regions). Where their item boundaries agree within tolerance → high confidence; where
   they disagree → flag the boundary for escalation/review. Must be *methodologically
   independent* to count as a real check.

4. **External structured-data oracles (label-free, the only true ground truth).**
   - **XBRL / iXBRL facts must fall inside Item 8.** Tagged numeric financial facts that
     land outside the extracted Item 8 (Financial Statements) span ⇒ that boundary is wrong.
   - **DEI tags + filing date ⇒ expected-item template.** Derive which items *should*
     exist (Item 1C only FY2023+, Item 6 `[Reserved]` post-2021, Part III usually
     incorporated-by-reference) and which are *legitimately* absent (smaller reporting
     company may omit Item 7A and run 2-year financials). Compare extracted items to the
     template to flag anomalies — while distinguishing legitimate omission from a miss.

5. **Per-item content sanity (cheap heuristics).** Expected length ranges and signature
   keywords (Item 1A "Risk Factors" should read like risks; Item 3 "Legal Proceedings"
   should mention legal matters). Weak signals, useful for catching gross mislabels.

## Confidence aggregation

Combine signals into a per-item confidence band, surfaced in the frontend:

- **High** — passes all hard gates (1, 2), dual-extractor agreement (3), and no oracle
  conflict (4).
- **Medium** — hard gates pass but a soft signal disagrees (boundary offset within a
  fuzzy window, a content heuristic fails, template anomaly that may be legitimate).
- **Low / needs-review** — any hard-gate failure, oracle conflict, or extractor
  disagreement beyond tolerance. Never emitted as "done" silently.

Per-filing confidence = aggregate of item bands + whether the full-coverage round-trip
held. Both the per-item and per-filing values, plus *which signals fired*, are shown to
the user (provenance, not a bare number).

## Making silent failure impossible

- **Every item carries confidence + provenance.** Which extractor produced it, which
  checks passed/failed. No item is emitted without this envelope.
- **"Missing" is always classified, never dropped.** An absent item is labelled either
  `legitimately-absent` (template/DEI says optional or incorporated-by-reference) or
  `extraction-failure` (template expects it, not found) — different handling, both visible.
- **Validate-the-validator.** Inject synthetic perturbations into known-good filings
  (delete an item, swap two items' order, drop a chunk mid-item) and assert each check
  fires. This is a CI test — a validator that never fails is worthless.
- **Calibrate on a small stratified gold set.** Hand-label a gold subset (see
  `08-eval-set-construction.md`) to map signal combinations → empirical accuracy, so the
  confidence bands mean something rather than being guessed weights.

## Anti-patterns (explicitly avoided)

- LLM-judges-its-own-extraction as the *primary* validator (confident systematic errors
  survive it).
- Treating round-trip success as proof of correctness (it only proves coverage).
- Silently coercing a missing/extra item into the canonical template without flagging.
