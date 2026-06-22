# Extract Design/Implementation/Verification Principles Into CLAUDE.md

- **Datetime:** 2026-06-22 18:09:19
- **Summary:** Use /10k-expert to route to the principle-owning docs, then distill the load-bearing design, implementation, and verification principles into .claude/CLAUDE.md as binding build rules that target top quality for ASSIGNMENT.md.

## Prompt

> now with /10k-expert extract the principles for design,implementation,verification for .claude/CLAUDE.md making sure it is perform best quality for this assignment.md /save-prompt

## What I Did

- Invoked the `/10k-expert` skill to route the three pillars to their owning docs: design → `docs/10` + `docs/06`; implementation → `docs/10` (stages/tech-stack) + `docs/02`/`07`; verification → `docs/16` + `docs/06`.
- Read those principle-dense docs (`10`, `06`, `16`) to ground the extraction in actual content rather than memory.
- Added a new **"SEC 10-K Extractor — Design / Implementation / Verification Principles"** section to `.claude/CLAUDE.md`, binding for all build work, with three subsections:
  - **Design:** index-don't-generate; layered ensemble (LLM last); validation layer is the differentiator; derive expected-item template from date+DEI; stable item IDs + cross-year consistency; cost discipline (~$0.003–0.006/filing, cache by accession, 10 req/s + UA).
  - **Implementation:** reuse-vs-build by license (edgartools MIT; reimplement CRF; avoid GPL/NC); structural CRF features; XGrammar-constrained escalation on a window; explicit output contract; classify missing items; three format eras, scope vision out.
  - **Verification:** independent oracles only; the cheap→expensive validation stack; LLM judge = non-gating flag only; conformal (Mondrian) confidence guarantee; Inspect-AI 4-scorer harness, grade state not path; honest reporting (clustered CIs, Abstention-Recall, pass^k, cost Pareto, run_manifest, no over-claiming); validate-the-validator.
- Pointed the section at `/10k-expert` + `docs/10` for detail/sources, so the rules stay short and the docs remain the source of truth.
- Nothing committed/pushed (per repo push policy).
