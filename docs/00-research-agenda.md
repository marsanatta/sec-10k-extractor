# Research Agenda & Confidence Scoreboard

Persistent state for the grounding research loop. Goal: reach ~100% confidence that we
can design a high-quality 10-K item-extraction pipeline meeting `ASSIGNMENT.md`. Each loop
iteration advances one or more agenda items, writes a doc here, and updates the scoreboard.

## Confidence scoreboard

Overall readiness to design the pipeline: **score updated each iteration**.

| # | Knowledge area | Doc | Status | Confidence (0-10) |
|---|----------------|-----|--------|-------------------|
| 1 | EDGAR access & 10-K file formats (txt/HTML/iXBRL), official Item 1–16 structure | `01-edgar-access-and-formats.md` | **done** | **9** |
| 2 | Open-source tooling landscape (reuse vs build) | `02-opensource-tools-landscape.md` | **done** | **8** |
| 3 | SOTA segmentation + evaluation WITHOUT ground truth | `03-sota-segmentation-and-eval.md` | **done** | **8** |
| 4 | Format-variance failure taxonomy (concrete breakers) | `04-format-variance-taxonomy.md` | **done** | **9** |
| 5 | Cost / latency / scalability of approaches (rule vs LLM, caching) | `05-cost-latency-scalability.md` | **done** | **8.5** |
| 6 | Confidence scoring & silent-failure detection design | `06-confidence-and-silent-failure.md` | **done** | **8** |
| 7 | iXBRL / structured-data exploitation for item boundaries | `07-ixbrl-structure-exploitation.md` | **done** | **9** |
| 8 | Eval-set construction strategy (which filings, gold subset size) | `08-eval-set-construction.md` | **done** | **9** |
| 9 | Frontend/UX for inspecting items + confidence/failures | `09-frontend-ux.md` | **done (design)** | **8** |
| — | **Capstone synthesis: end-to-end pipeline architecture** | `10-pipeline-architecture.md` | **done** | — |

**Overall confidence: ~93 / 100** — 9 core areas done + 7 curated-reference deep-reads
(`docs/11`–`17`) folded into the architecture. Capped below 100 on purpose: the residual is
**build-time validation, not research** (9 concrete open items in doc 10 — all closed by
building + measuring, not reading). Research grounding **exhausted**; loop concluded.

## Stop criterion

Stop the loop when ALL hold:
- Every agenda area ≥ 8/10.
- We can name the concrete pipeline architecture (stages, fallbacks, where LLM is/ isn't used).
- We can name the eval strategy with specific metrics and a ground-truth-free validation plan.
- We can name the top failure modes and how each is detected (no silent failures).

## Loop log

- **2026-06-22 17:07** — Iteration 1 launched: 3 parallel research agents for areas 1–3.
- **2026-06-22 17:10** — Area 3 done (8/10): layered regex+TOC→CRF→LLM ensemble; validation = structural invariants + round-trip reconstruction + independent rule-vs-LLM agreement + XBRL companyfacts oracle. Areas 1–2 still running.
- **2026-06-22 17:11** — Area 2 done (8/10): reuse edgartools (MIT) + EDGAR-CORPUS silver baseline; reimplement CRF (itemseg is NonCommercial, edgar-crawler GPL-3.0); confirmed no tool emits confidence → verification layer is our differentiator. Independently corroborates area 3. Area 1 still running.
- **2026-06-22 17:16** — Area 1 done (9/10): live-verified CIK→primary-doc path, 10 req/s+UA rules, 3 format eras, date-keyed item template (1C FY2023+, Item 6 Reserved post-2021, Part III usually incorporated-by-reference). Iteration 1 complete; overall score ~58/100.
- **2026-06-22 17:16** — Iteration 2 launched: 3 agents for areas 5 (cost/scalability), 4+8 (hard-case filings + eval set), 7 (iXBRL exploitation). Area 6 (confidence/silent-failure design) drafted in-house from area 3 — no external research needed.
- **2026-06-22 17:23** — Area 5 done (8.5/10): hybrid ~$0.003–0.006/filing vs ~$0.24 full-Sonnet (40–130×) and higher accuracy; 10 req/s ingestion ceiling; cache by accession. Measure HTML token census + real escalation rate before locking budgets. Areas 4+8, 7 still running.
- **2026-06-22 17:28** — Area 7 done (9/10, live-verified): `ix:nonFraction` offsets cross-check Item 8 boundary; DEI cover tags (DocumentPeriodEndDate, EntitySmallBusiness, AmendmentFlag) give expected-template + legitimate-omission gate. Limits: anchors only financial back-matter, offsets FY2019+/FY2021+, treat XBRL as strong prior not ground truth. Areas 4+8 still running.
- **2026-06-22 17:33** — Areas 4 & 8 done (9/10 each): 12 byte-verified hard-case filings (MSFT FY1995 SGML, Apple FY2024 4-pathology iXBRL, GE FY2023 out-of-order, M2i SRC, Chemed 10-K/A); eval set N≈600 + 150 gold + 90k silver. Iteration 2 complete.
- **2026-06-22 17:33** — Iteration 3 (in-house synthesis): area 9 frontend design + capstone `10-pipeline-architecture.md`. Overall ~90/100. **Stop criterion met — loop concluded.** Residual = build-time validation, not research.
- **2026-06-22 17:4x** — User-curated reading list grounded: 7 reading agents → `docs/11`–`17` (+ `REFERENCES.md` index). Deepens areas 3/6/8, not new areas.
  - `15-llm-as-judge.md` done (8/10): JudgeBench (judge ≈ random on objective correctness) + Nine-Judges (panels don't fix correlated error) + Gaming-the-Judge (never feed generator rationale to judge) → LLM judge = non-gating last-resort flag only. Sources our "independent oracles only" rule.
  - `12-faithfulness-consistency.md` done (5/10): we index not generate → round-trip dominates learned NLI/QA metrics for the core. Adopt AIS as output contract, FactCC perturbations as validate-the-validator; SelfCheckGPT disqualified (self-consistency), usable only inverted as escalation trigger.
  - `14-financial-nlp.md` done (8/10): **NEW REQUIREMENT — cross-year boundary consistency** (Lazy Prices: YoY same-firm item-text diffs predict returns → boundaries must be stable across years; drift = silent-failure; emit stable item IDs). XBRL reliable for presence/location not meaning (FiNER/FinTagging). **→ integrate into doc 10 + eval dims (08/16) in consolidation pass.**
  - `11-segmentation-methods.md` done (6/10): validates 3-tier ensemble; tactics — CRF features must be structural (is-line-start/prior-item-seen/in-TOC), feed LLM tier a window in LumberChunker prompt shape (escalation-only; whole-doc = ~120 calls), train CRF on TOC-derived silver labels, scope vision parsing out.
  - `13-calibration-and-decoding.md` done (8/10): **Conformal prediction → provable confidence bands** (calibrate q̂ on gold, set-size = abstention trigger, α tunes escalation; stratify per era / Mondrian CP). **XGrammar constrained decoding → 100% valid escalation output**, deletes bad-JSON/invented-item class. Verbalized confidence = TRAP (overconfident); semantic-entropy probes = adopt if self-hosting. **→ upgrades doc 06.**
  - `17-agentic-evals-workshop.md` done (7/10): hard verifiers > LLM-judge (GAIA 2 precedent); reliability decomposes → **test run-to-run consistency + prompt robustness on LLM-LIB layer**; enforce a `run_manifest`; put cost/latency in the eval table; automated failure-cluster table; judge re-calibration trigger.
  - `16-eval-frameworks-and-rigor.md` done (8/10): Inspect AI 4-scorer harness; **Abstention-Recall = headline silent-failure metric**; pass^k reliability; filing-clustered CIs (150 gold = ±3–5% aggregate, wide on rare strata); cost/accuracy Pareto (HAL); `run_manifest`.
- **2026-06-22 17:37** — Loop re-fired; all 7 reading docs in. **Consolidation pass** folded cross-cutting upgrades into `10-pipeline-architecture.md` (cross-year consistency, conformal bands, XGrammar escalation, structural CRF features, judge policy, Inspect-AI harness spec). Overall **~93/100**. Research grounding exhausted (residual = build-time only). **Loop concluded — not rescheduling.**
