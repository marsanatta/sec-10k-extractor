# Author The Round-2 Autoresearch Plan (Review Doc Only)

- **Datetime:** 2026-06-25 11:19:36
- **Summary:** Author (no execution) a focused DELTA round-2 plan whose headline is building a genuinely INDEPENDENT classification-correctness signal (Signal D), so the form-aware template fix round-1 discarded becomes legitimately earnable instead of circular.

## Prompt

> round 1 is merged and analyzed — time to author the round-2 plan. same as before: author it as a review DOC (i'll read it, you execute only after it passes), don't execute or touch code yet. write it to research/autoresearch-round-2-plan.md.
>
> this is a focused DELTA from round-1, not a full re-author — keep the exact same discipline (the three independent signals A structural-pass [labeled upper-bound-not-accuracy] / B gold recall / C new named modes; guards G1-G6 incl. offline green network-free, regex primary, fallback conservative, char-gold stays 5 never auto-frozen, G6 never-loosen-the-ruler; one probe per iteration; keep/discard + document-discards; ~25-iter bound). baseline is the NEW main (round-1 merged: escalation apply-loop closed, eval grown) — re-measure the signals on it first.
>
> the HEADLINE round-2 target — build the thing round-1 said was missing. round-1 discarded the form-aware template fix even though it was correct, because its only benefit landed on a forbidden proxy (extraction_failure / needs_review) and no independent signal could see it. so round-2's first job is to BUILD a genuinely independent CLASSIFICATION-CORRECTNESS signal — one that can independently verify "for this form type, is item X correctly judged present / absent / incorporated-by-reference". design it decorrelated from the production needs_review: e.g. a small HUMAN-AUDITED per-form-type expected-presence reference (a few 10-K and a few 10-K/A filings, hand-labeled which items should be present vs legitimately absent), audited like the char-gold and frozen the same way (human checkpoint, out of the autoloop, never self-graded). it must be a signal the loop CANNOT move by changing the production classifier — only by getting classification genuinely right.
>
> THEN — and only then — the form-aware template fix becomes legitimately earnable: with the new independent signal in place, re-attempt it and keep it iff it moves THAT signal (amendments correctly classified) AND a full-10-K control is unchanged AND the guard passes. if the new signal can't be made genuinely independent, say so and defer the form-aware fix again — don't fake the signal to justify the fix.
>
> secondary scope: more stratified eval growth (under-covered era / filer / sector / structure, accession-pinned) and more failure-mode discovery. regex stays primary, fallback conservative, char-gold 5, G6 rulers never loosened, structural-pass always labeled "upper bound, not accuracy".
>
> execution later runs in a fresh isolated worktree off the new main, writes findings to research/round-2-findings.md + round-2-failure-modes.md + an append-only research/round-2-progress.json, merges back after my review, never pushed — spell that out in the plan.
>
> i'll review it against the same bar, with special attention to one thing: is the new classification-correctness signal GENUINELY INDEPENDENT (human-audited, frozen, decorrelated from needs_review) — or just another proxy dressed up? if it's not truly independent, the whole form-aware earn is circular. write the plan doc, don't execute. /save-prompt

## What I Did

- Authored `research/autoresearch-round-2-plan.md` as a **review document only** (no execution, no
  code), structured as a focused DELTA from round 1 (signals A/B/C, guards G1-G6, one-probe-per-
  iteration, keep/discard+document, ~25-iter bound all carry over verbatim; baseline = the new
  merged main, re-measured at iteration 0).
- Designed the headline **Signal D — classification-correctness**: a human-audited per-form-type
  reference (`eval/classification_gold.json`, ~3 full 10-K + ~3 10-K/A, labelled by READING each
  filing's TOC/Part structure), frozen exactly like char-gold (human checkpoint, out of the
  autoloop, never self-graded). Metric = per-item category match-rate (present / legitimately-
  absent / incorporated-by-reference / extraction-failure) per form type, with N + Wilson CI.
- Made independence the centerpiece (the review-bar crux): the reference is read-located not
  production-derived; a new guard **G7** forbids the loop from freezing/editing it; and crucially
  it must be able to **REFUTE, not just confirm** -- a **mutation refutation control (3a)** (a
  deliberately-wrong classification must lower Signal D, always assemblable) plus an optional
  **full-scope-amendment control (3b)** (a /A that does amend Part I, which an over-broad rule
  would mis-classify). Added **STOP S4**: if Signal D can't be made genuinely independent, declare
  it and DEFER the form-aware fix again -- never fake the signal.
- Gated the form-aware template re-attempt (probe #2) on moving Signal D against the USER-frozen
  reference AND a full-10-K control unchanged AND Signal A unchanged (with an explicit refusal to
  loosen the coverage ruler to manufacture an A gain, G6) AND guard. Probe #1 (build Signal D)
  pauses at a human-audit checkpoint before the fix can be earned.
- Spelled out secondary scope (stratified eval growth, failure-mode discovery), the artifacts
  (round-2 findings / failure-modes / append-only progress.json + classification_gold.json + audit
  record), and the no-push execution model (fresh worktree off new main, merge after review, never
  pushed). Added a review-bar self-check table foregrounding Signal D independence.
- Did NOT execute and did NOT touch any pipeline code. Saved this prompt (Taipei time per project
  convention); left untracked for the user's batch commit.
