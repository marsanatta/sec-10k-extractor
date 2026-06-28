# Measure Whether The Real LLM Escalation Tier Actually Helps (Before Round 3)

- **Datetime:** 2026-06-26 22:05:47
- **Summary:** Before building autoresearch round 3 on top of the LLM tier, MEASURE — against an independent frozen gold, never self-grading — whether the real Copilot escalation actually improves anything; report an honest verdict either way, and a "measured no" is a complete result.

## Prompt

> from copilot-llm worktree do this before we run autoresearch round-3, i want you to actually MEASURE whether the real copilot LLM escalation tier (feat/copilot-llm) helps — right now it's wired but nobody's proven it earns its keep, and the round-3 plan just assumes it as baseline. measure it first, in a fresh worktree, never push. round-3 waits until this is done — i don't want round-3 building on an unmeasured LLM baseline.
>
> start with the free deterministic pre-pass: run the eval / sweep filings with the LLM OFF (the deferred stub, $0) and collect, per filing, the escalation_candidates that run_escalation already records (present-not-HIGH boundaries + extraction_failures). that gives you two things for free — (a) the population trigger rate, i.e. how often the LLM would even fire and on which filings, and (b) the key check: do ANY of the human-gold filings trigger escalation? the whole difficulty is that the filings that trigger the LLM are the hard ones with no gold, while the gold filings are clean and don't trigger — so first find out if there's any overlap.
>
> then measure the marginal value before/after, on whatever ground-truth path exists, and the measurement MUST be against an independent reference, never the LLM grading itself:
> - if any gold filing triggers → that's a free before/after: run it LLM-on vs LLM-off and compare Signal D (classification-match vs the frozen gold) + Signal B (char-gold boundary). report the delta.
> - a deterministic mechanism anchor: build a fixture where the deterministic path produces a low-confidence boundary that is WRONG with a known-correct answer; assert LLM-on fixes it and LLM-off does not — proves the real model + the apply-loop work end-to-end, non-tautologically (fails without the LLM).
> - if you want real-filing benefit beyond the gold overlap: pick N triggering real filings and, instead of self-grading, PROPOSE a small targeted human reference for those specific escalated boundaries (the char-exact correct boundary, for me to audit) — do not freeze or score it yourself; that's a human checkpoint like char-gold / classification-gold.
>
> honesty bar, non-negotiable (same as rounds 1-2): the deterministic regex path stays primary, the LLM is escalation-only; you do NOT edit / freeze / regenerate boundary_gold.json or classification_gold.json; you measure against the independent frozen gold, never nominal, never the LLM's own confidence. report the result honestly whichever way it goes — if the LLM doesn't beat deterministic on the cases it fires on, write "measured: LLM gives no independent-signal improvement on these N escalation cases" and we keep it as an honest graceful-fallback tier, not a claimed win. a measured no is a complete result.
>
> also add the cheap observability hook round-3 will use: tag each sweep / extraction record with llm_touched (did escalation fire, what did it change) so the failure census can later reflect the LLM's footprint.
>
> deliverable: a short research/llm-measurement-findings.md with — the population trigger rate, whether any gold filing triggers, the fixture mechanism result, the before/after Signal-D/B delta where gold exists (or the proposed targeted reference for me to audit), and a clear verdict: does the LLM help, measured, or is it an honest no. worktree off main, show me the result, never push

## What I Did

- Ran the measurement in an isolated worktree (off main, never pushed), LLM-on vs LLM-off against the FROZEN gold — never letting the model grade itself.
- **Result was a measured NO:** every boundary-gold filing that the tier touched moved **zero** boundaries (ΔIoU 0.000, including the hard token-per-line and legacy-SGML cases); Signal D was unchanged by construction (the apply-loop nudges a present item's start, never a status). The trigger was over-broad — all filings triggered, ~100+ model calls produced only a couple of moves, both on non-gold filings (unverifiable).
- Built the non-tautological mechanism fixture (inject a wrong boundary → mock returns the correct line → assert the span moves to the known-correct offset at IoU ≥ 0.9) — proving the real model + apply-loop *work*, they simply never needed to on the gold where the deterministic path was already right.
- Wrote `research/llm-measurement-findings.md` with the honest verdict, added the `llm_touched` footprint tag, and set the tier **default-OFF** — kept as a measured, honest graceful-fallback opt-in, not a claimed win. This is the evidence behind the README/ANALYSIS "LLM tier built, then turned off by default" decision.
