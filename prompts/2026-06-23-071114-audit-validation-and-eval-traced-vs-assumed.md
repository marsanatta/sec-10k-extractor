# Audit The Validation Layer + Eval, With Traced-vs-Assumed Honesty

- **Datetime:** 2026-06-23 07:11:14
- **Summary:** User asked for a rigorous, honest walkthrough of the validation layer's checks and the eval methodology — explicitly requiring each claim be tagged as actually-traced-in-code vs assumed — before growing the eval set. No code changes.

## Prompt

> before we add more filings to the eval set i want to understand how your validation really works first, i havent read through it yet. dont change any code now.
>
> can you list all the checks your validation layer do, and for each one just tell me in simple words what kind of mistake it suppose to catch and how it decide pass or fail. also which filings are in the eval set now and why you pick those, and what kind of filings you didnt cover yet. then paste the current eval report and explain what each number mean, specially the silent failure one, what is it counting exactly.
>
> last thing run /10k-expert and compare, where your code match what the design doc say and where it already different or got skipped.
>
> one rule, your own CLAUDE.md say engineering rigor, so for each answer tell me if you actually traced it in the code or you just think it is like that but not verified. i rather have honest answer than a confident one /save-prompt

## What I Did

- Re-read the actual code (did NOT answer from memory): `validate.py`, `oracle.py`, `dual.py`, `segment.py`, `evalkit.py`, plus `eval/report.md` and `eval/eval_set.json`; loaded `/10k-expert` → `docs/06`, `docs/16` for the design claims. Tagged every statement [TRACED] vs [ASSUMED].
- **Key honest findings surfaced (traced):**
  - `structural_invariants` and `round_trip` are **tautologies** on the current segmenter (it always emits a contiguous tiling), so they can't fail on real output; the real structural detector is `coverage_plausible` (>=0.4).
  - `content_ok` only covers 7 of 23 items (rest pass vacuously); `title_match` is a weaker stand-in for the design's "independent 2nd extractor" (CRF = STRETCH); Item-8 XBRL oracle silently degrades to markers-only when companyfacts returns nothing.
  - Confidence scores (0.9/0.6/0.3) are hand-picked placeholders; conformal calibration not built.
  - **Silent-failure "0/7" is effectively N=2**: a silent failure is only possible on a `needs_review=False` filing, and only Apple+KO are unflagged (5/7 are flagged → trivially not silent). So the headline is weak evidence, honest CI upper bound 0.35.
  - Design-vs-code divergences: no Inspect-AI framework, no char-exact boundary-F1 gold, no clustered SE / abstention metrics / pass^k / silver baseline / conformal (all STRETCH or skipped); report discloses the boundary-F1 gap but not the others (a doc gap to fix).
- No code changed (per the user's instruction). This record itself is the only write.
