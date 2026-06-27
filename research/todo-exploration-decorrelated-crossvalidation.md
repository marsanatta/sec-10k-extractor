# TODO / Exploration — decorrelated cross-validation in the pipeline

**Status:** exploration note, NOT scheduled work. No code. Captures an evaluated idea + the path so a
future round doesn't re-litigate it.

## The question
The pipeline's two in-path extractors — regex (`segment.py`) and the edgartools fallback — both
header-anchored, so they are CORRELATED and can be confidently wrong together (the common-mode /
silent-failure risk). Should we add a genuinely DECORRELATED third cross-check *inside* the pipeline?

## Verdict
**The concept is right (it's the project's core thesis), but `edgar-corpus` specifically is the wrong
tool for a LIVE in-pipeline tier.** We already evaluated it — `eval/edgar_corpus_spike.py` IS the
evaluation (a 3-way boundary cross-check: us vs edgartools vs edgar-corpus; it did catch edgartools
diverging on xom-fy2010, spread 107840). Why it must stay an out-of-band audit, not a live tier:

1. **Coverage:** `eloukas/edgar-corpus` is **1993–2020 only** → null on modern (2021+) filings, exactly
   the hardest era. A signal that vanishes on the modern era can't be an in-pipeline check.
2. **Lossy / text-only / approximate:** it cleans the text, so boundaries are approximate against OUR
   canonical → can't correct an offset; as a flag it false-positives across the two text spaces.
3. **Heavy hot-path dependency:** live use = per-filing HF `load_dataset` (`datasets<3`, large
   downloads) → breaks cost discipline + the O(n) stateless-per-filing design.
4. **Cross-text-space alignment is itself error-prone** → a NEW correlated-error source (the aligner).
5. **Consuming the auditor:** wiring an independent check into production makes it no longer
   independent — its value is precisely being out-of-band.

## The three-tier path (if/when we invest in decorrelated cross-validation)
- **(A) The real in-pipeline decorrelated extractor = a CRF non-header line-labeller.** Structural
  features (`is-line-start`, `prior-item-seen`, `in-TOC`) → method-decorrelated from the header-anchor
  family, works on modern filings, emits spans. This is the named answer to the common-mode ceiling
  (MS/Citi). Cost: reimplement + train on silver labels. Currently STRETCH / out-of-scope.
- **(B) Cheap win — promote the edgar-corpus spike from one-off → a STANDING eval cross-check** on the
  1993–2020 overlap subset: REPORTED-only, repeatable, disagreements flagged for human audit. Keeps it
  out of the hot path but makes the decorrelated audit part of the standing eval (eval-depth credit).
- **(C) Cheapest lever already in-pipeline — extend the XBRL/DEI oracle coverage** (`sec10k/oracle.py`):
  it is the one truly-independent in-path signal today, but only covers Item 8 + presence.

**Recommendation if revisited:** do (B) for cheap repeatable audit, (C) to strengthen the live
independent signal, and treat (A) as the long-horizon answer to the common-mode ceiling. Do NOT wire
edgar-corpus per-filing.
