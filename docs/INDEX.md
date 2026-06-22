# Documentation Index (10k-expert)

Routing index for this repo's `docs/`. Used by the `10k-expert` skill to send a question
to the right doc. **Replaces the old flat `REFERENCES.md`** — instead of listing sources,
it routes *questions → docs*; each doc carries its own citations (L2). Navigate
L0 (category) → L1 (doc) → L2 (read the doc).

> Routing validated by a 10-question agent gate (10/10 correct, 2026-06-22). When docs
> change, re-run the gate via the `10k-expert` skill's maintenance step.

## L0 — Category map

| Category | Use when you're… | Docs |
|----------|------------------|------|
| **domain** | parsing a filing or handling a format/structure quirk of real 10-Ks | `01`, `04`, `07` |
| **design** | building the pipeline, the validation/confidence layer, or the UI | `10`, `06`, `09` |
| **evaluation** | building the eval harness, choosing metrics, sizing the eval set, or reasoning about cost/scale | `03`, `08`, `05`, `16` |
| **tooling** | deciding which open-source library to reuse vs build | `02` |
| **research** | needing the paper / external evidence behind a decision | `11`, `12`, `13`, `14`, `15`, `16`, `17` |
| **meta** | tracking research progress / the grounding scoreboard | `00` |

## Question → doc quick-lookup

| If the question is about… | Go to |
|---------------------------|-------|
| ticker→CIK→primary-doc resolution, EDGAR APIs, 10 req/s rate limit, User-Agent, txt/HTML/iXBRL eras, official Item 1–16 / Parts I–IV spec | `01` |
| which library to reuse (edgartools, secedgar, edgar-crawler), licenses, what no tool does | `02` |
| segmentation approaches overview + how to verify without ground truth (the survey) | `03` |
| concrete filings that break parsers; pathology catalog; example/hard-case filings (CIK/accession) | `04` |
| cost per filing, LLM vs CRF cost, scaling to 8k/90k, caching, throughput, storage | `05` |
| attaching confidence to items, preventing silent failures, independent-oracle validation, classifying missing items | `06` |
| using XBRL/iXBRL/DEI to validate Item 8 boundary or derive the expected-item template | `07` |
| eval-set size, strata, gold vs silver, EDGAR-CORPUS baseline | `08` |
| frontend, inspecting items, visualizing confidence/failures, tech stack for UI | `09` |
| the end-to-end pipeline architecture, stages, where the LLM is/ isn't used (capstone) | `10` |
| segmentation method papers (CRF, Cross-Segment BERT, LumberChunker, doc parsing) | `11` |
| faithfulness/consistency metrics (SummaC, SelfCheckGPT, QAGS, FactCC, AIS) | `12` |
| calibration, conformal prediction, constrained decoding (XGrammar), uncertainty/abstention | `13` |
| financial NLP, XBRL tagging (FiNER/FinTagging), Lazy Prices, cross-year consistency | `14` |
| LLM-as-judge reliability, judge/jury failure modes, judge policy | `15` |
| eval frameworks (Inspect AI), scorers, pass^k, statistical rigor / error bars, run_manifest | `16` |
| practical agentic-eval principles (HF workshop), hard verifiers vs judges | `17` |
| what's researched, confidence scoreboard, loop log | `00` |

---

## L1 — Per-doc routing entries

### `00-research-agenda.md` — Research agenda & confidence scoreboard  *(meta)*
- **Read when:** you need the status of the grounding research, per-area confidence, or the loop history.
- **Keywords:** scoreboard, confidence, agenda, stop criterion, loop log, coverage.
- **Answers e.g.:** "How confident are we overall?" · "Which areas are still weak?"
- **Key facts:** 9 areas + 7 reference deep-reads; overall ~93/100; residual is build-time.

### `01-edgar-access-and-formats.md` — EDGAR access & 10-K formats  *(domain)*
- **Read when:** fetching a filing, resolving a ticker/CIK, hitting rate limits, or handling a filing's file format/era; checking the official item structure.
- **Keywords:** ingestion / fetch / download a filing, EDGAR, CIK, ticker, submissions.json, companyfacts, full-text search (EFTS), 10 req/s, rate limit, User-Agent, primary document, accession, SGML txt, HTML, iXBRL, Regulation S-K, Form 10-K, Items 1–16, Parts I–IV, Item 1C, Item 6 Reserved, incorporated by reference, expected-item template.
- **Answers e.g.:** "How do I get the primary 10-K document URL from a ticker?" · "What's the EDGAR rate limit and header policy?" · "When did Item 1C appear?"
- **Key facts:** ticker→company_tickers.json→CIK→submissions.json→Archives path; ≤10 req/s + descriptive UA; three format eras; date-keyed item template.

### `02-opensource-tools-landscape.md` — Open-source tooling  *(tooling)*
- **Read when:** deciding what to reuse vs build; checking a library's license or capabilities.
- **Keywords:** edgartools, secedgar, sec-edgar-downloader, sec-parser, edgar-crawler, sec-api.io, itemseg, EDGAR-CORPUS, license, MIT, GPL, NonCommercial, reuse vs build.
- **Answers e.g.:** "Which library should I use for ingestion?" · "Is edgar-crawler safe to embed?" · "Does any tool emit confidence?"
- **Key facts:** reuse edgartools (MIT) + EDGAR-CORPUS silver; reimplement CRF (itemseg NC, edgar-crawler GPL-3.0); no tool emits confidence → our differentiator.

### `03-segmentation-and-eval-survey.md` — SOTA segmentation + ground-truth-free eval survey  *(evaluation)*
> file: `03-sota-segmentation-and-eval.md`
- **Read when:** you want the *survey / menu* of segmentation approaches AND validation-without-ground-truth techniques. **Disambiguation:** `03` = the overview/menu of techniques; for the operational design that turns them into per-item confidence signals, go to `06`.
- **Keywords:** segmentation, CRF, BERT, regex anchors, TOC, ensemble, index-don't-generate (LIB), structural invariants, round-trip, dual-extractor agreement, XBRL oracle, self-consistency trap.
- **Answers e.g.:** "What segmentation approach is most robust?" · "How do I validate extraction with no ground truth?"
- **Key facts:** layered regex+TOC→CRF→LLM; validators = invariants + round-trip + independent agreement + XBRL oracle; self-consistency can't catch systematic errors.

### `04-format-variance-taxonomy.md` — Format-variance taxonomy + example filings  *(domain)*
- **Read when:** handling a filing that breaks a parser, or you need concrete hard-case filings to test against.
- **Keywords:** pathology, regex over-capture (Item 27(a), Item 1⊃10–14), styled-span/NBSP headers, out-of-order items, incorporated by reference, smaller reporting company, 10-K/A amendment, example filings, CIK, accession, MSFT FY1995, Apple FY2024, GE FY2023, M2i, Chemed.
- **Answers e.g.:** "Which filings break a naive Item 1 regex?" · "Give me a hard-case iXBRL filing." · "What real filing has Part III incorporated by reference?"
- **Key facts:** 12 byte-verified hard cases mapped to extraction steps; the eval seeds.

### `05-cost-latency-scalability.md` — Cost / latency / scalability  *(evaluation)*
- **Read when:** estimating cost, choosing where to spend LLM calls, or planning corpus-scale runs.
- **Keywords:** cost per filing, token count, LLM pricing, hybrid, escalation rate, throughput, 10 req/s, caching by accession, 8000 filings, 90k EDGAR-CORPUS, storage, Pareto.
- **Answers e.g.:** "How much to process 8000 10-Ks?" · "Is full-document-LLM affordable?" · "What's the ingestion ceiling?"
- **Key facts:** hybrid ~$0.003–0.006/filing vs ~$0.24 full-LLM (40–130×); 10 req/s; cache by accession; measure HTML token census + escalation rate before locking budgets.

### `06-confidence-and-silent-failure.md` — Confidence & silent-failure design  *(design)*
- **Read when:** designing how each item gets a confidence, how silent failures are prevented, or how missing items are handled. **Disambiguation:** `06` = the operational confidence/validation *design*; for the survey of techniques see `03`; for the statistical-guarantee layer (conformal) see `13`.
- **Keywords:** confidence band, provenance, silent failure, structural invariants, round-trip reconstruction, dual-extractor agreement, XBRL/DEI oracle, legitimately-absent vs extraction-failure, validate-the-validator, independent oracles only.
- **Answers e.g.:** "How do I attach confidence to an item?" · "How do I make silent failure impossible?" · "How do I tell a legitimately-missing item from a miss?"
- **Key facts:** layered validation stack → confidence bands + provenance; missing items classified, never dropped; self-consistency banned as a validator.

### `07-ixbrl-structure-exploitation.md` — iXBRL / structured-data exploitation  *(domain)*
- **Read when:** using XBRL/iXBRL/DEI tags to validate boundaries or derive the expected-item template.
- **Keywords:** iXBRL, ix:nonFraction, us-gaap, companyfacts, FilingSummary.xml, R-files, DEI, DocumentPeriodEndDate, EntitySmallBusiness, AmendmentFlag, Item 8 cross-check, expected template, presence/location not meaning.
- **Answers e.g.:** "Can XBRL validate the Item 8 boundary?" · "How do I know which items a filing should have?" · "How reliable is XBRL as an oracle?"
- **Key facts:** tagged facts must fall inside Item 8; DEI tags → template + legitimate-omission gate; offsets only FY2019+/FY2021+; treat XBRL as strong prior, not ground truth.

### `08-eval-set-construction.md` — Eval-set construction  *(evaluation)*
- **Read when:** designing the evaluation set — size, strata, gold/silver split, calibration.
- **Keywords:** eval set, stratified, gold subset, silver baseline, EDGAR-CORPUS, calibration, strata (era × filer-size × pathology), N≈600, 150 gold.
- **Answers e.g.:** "How big should the gold set be?" · "How do I use EDGAR-CORPUS as a baseline?" · "What strata do I sample?"
- **Key facts:** N≈600 stratified + 150 hand-labeled gold + ~90k silver; gold calibrates silver; label-free checks on 100%.

### `09-frontend-ux.md` — Frontend / inspection UX  *(design)*
- **Read when:** designing the web UI to submit/select filings and inspect items + confidence + failures.
- **Keywords:** frontend, web UI, item navigator, boundary viewer, confidence panel, failure inspector, Streamlit, Gradio, FastAPI, React, deploy, Zeabur, HF Spaces.
- **Answers e.g.:** "How should the UI show confidence?" · "What tech stack for the frontend?" · "How do reviewers inspect a failure?"
- **Key facts:** item navigator (present/absent/flagged), boundary viewer, confidence panel with provenance, failure inspector; FastAPI+React or Streamlit; cache by accession.

### `10-pipeline-architecture.md` — Pipeline architecture (capstone)  *(design)*
- **Read when:** you need the end-to-end blueprint, the stage list, or where the LLM is/ isn't used; START HERE before implementing.
- **Keywords:** architecture, pipeline stages, ingest, normalize, expected-item template, segment, ensemble, validate, output JSON, hybrid, escalation-only LLM, failure-mode table, tech stack, open items, cross-year consistency, conformal, XGrammar.
- **Answers e.g.:** "What's the overall design?" · "Where does the LLM run?" · "What are the top failure modes and how are they detected?"
- **Key facts:** 6 stages, indexing-not-generation, layered ensemble, validation differentiator; refinements from docs 11–17 folded in; 9 build-time open items.

### `11-segmentation-methods.md` — Segmentation method papers  *(research)*
- **Read when:** justifying the segmentation approach or CRF/LLM tactics from the literature.
- **Keywords:** Koshorek, Cross-Segment BERT, LumberChunker, Document Parsing survey, line-labeling, local window, content-shift chunking, structural CRF features.
- **Answers e.g.:** "What paper backs local-window boundary detection?" · "Why escalation-only LLM?"
- **Key facts:** local window suffices (Cross-Segment BERT); LumberChunker = whole-doc LLM is ~120 calls → escalation-only; CRF features must be structural.

### `12-faithfulness-consistency.md` — Faithfulness/consistency metrics  *(research)*
- **Read when:** evaluating the LLM-escalation output or choosing an attribution/consistency metric.
- **Keywords:** SummaC, SelfCheckGPT, QAGS, QuestEval, QAFactEval, FactCC, AIS, NLI, QA-based, attribution, self-consistency trap.
- **Answers e.g.:** "Is SelfCheckGPT a valid validator?" · "What's the attribution standard for our output?"
- **Key facts:** we index→round-trip dominates these for the core; adopt AIS as output contract, FactCC perturbations as CI; SelfCheckGPT disqualified (self-consistency).

### `13-calibration-and-decoding.md` — Calibration & constrained decoding  *(research)*
- **Read when:** giving confidence a statistical guarantee, forcing valid LLM output, or choosing an uncertainty/abstention signal.
- **Keywords:** conformal prediction, Mondrian, coverage guarantee, abstention, XGrammar, constrained/structured decoding, verbalized confidence, semantic entropy probes.
- **Answers e.g.:** "How do I make confidence bands provable?" · "How do I guarantee valid escalation JSON?" · "Is asking the LLM its confidence trustworthy?"
- **Key facts:** conformal (stratify per era) → provable bands + abstention; XGrammar → 100% valid output; verbalized confidence = trap; SEP if self-hosting.

### `14-financial-nlp.md` — Financial NLP / signal  *(research)*
- **Read when:** reasoning about XBRL tagging reliability or the downstream use case that sets requirements.
- **Keywords:** FiNER-139, FinTagging, Scalable LLM 10-K, Lazy Prices, cross-year consistency, stable item IDs, presence/location not meaning, year-over-year text diff.
- **Answers e.g.:** "Why does cross-year boundary consistency matter?" · "How reliable is XBRL for fact meaning?"
- **Key facts:** Lazy Prices → cross-year consistency is a first-class requirement (stable item IDs; drift = silent failure); XBRL reliable for presence/location, not meaning.

### `15-llm-as-judge.md` — LLM-as-judge & failure modes  *(research)*
- **Read when:** deciding whether/how to use an LLM judge in the eval.
- **Keywords:** MT-Bench, G-Eval, Prometheus 2, JudgeBench, PoLL, Nine Judges Two Votes, self-preference bias, Gaming the Judge, jury, correlated error, judge policy.
- **Answers e.g.:** "Can a panel of judges fix correlated error?" · "Can I gate correctness on an LLM judge?"
- **Key facts:** judge ≈ random on objective correctness (JudgeBench); panels ≈ 2 independent votes (Nine Judges); judge = non-gating flag only; never feed it the generator's rationale.

### `16-eval-frameworks-and-rigor.md` — Eval frameworks & statistical rigor  *(evaluation/research)*
- **Read when:** building the eval harness, picking scorers/metrics, or reporting uncertainty honestly.
- **Keywords:** Inspect AI, Task/Solver/Scorer, scorers, F1, pass^k, abstention-recall, AURC, conformal threshold, clustered standard error, error bars, HAL, cost tracking, run_manifest.
- **Answers e.g.:** "What scorers should the harness have?" · "Is 150 gold filings enough for tight per-stratum F1?" · "How do I report CIs?"
- **Key facts:** 4 independent scorers; Abstention-Recall = silent-failure metric; pass^k; filing-clustered CIs (150 gold = ±3–5% aggregate, wide on rare strata); cost on the same table.

### `17-agentic-evals-workshop.md` — Agentic-evals workshop notes  *(research)*
- **Read when:** you want practical, transferable eval methodology and anti-gaming practice.
- **Keywords:** hard verifiers vs LLM-judge, GAIA 2, reliability decomposition, run-to-run consistency, prompt robustness, run_manifest, failure clustering, living benchmark.
- **Answers e.g.:** "Should I use a hard verifier or an LLM judge?" · "What reliability dimensions am I missing?"
- **Key facts:** hard verifiers > judges (GAIA 2); test run-to-run + prompt robustness on the LLM tier; enforce a run_manifest; cost/latency in the eval table.

---

## Sources

This index routes questions to docs; **each doc lists its own primary sources** (SEC
endpoints, GitHub repos, datasets, arXiv papers, example filings). For the consolidated
external reading list with URLs, see the per-doc citations and the curated list embedded in
docs `11`–`17`.
