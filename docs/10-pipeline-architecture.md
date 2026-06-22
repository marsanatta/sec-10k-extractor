# Pipeline Architecture (Synthesis)

The capstone of the grounding loop: the concrete, end-to-end design distilled from
`docs/01`–`09`. If this design is buildable and its failure modes are all detectable,
the grounding goal is met.

**Thesis.** Treat item extraction as **indexing into the source, not generation**, behind
a **layered ensemble** (cheap rules → CRF → LLM only on flagged spans), wrapped in an
**independent-oracle validation layer** that attaches calibrated confidence to every item
and makes silent failure structurally impossible. The validation layer — not the
segmenter — is the differentiator, because no existing tool emits confidence.

## Stages

1. **Ingest & resolve** (`01`). ticker/CIK → `submissions.json` → primary document;
   honour 10 req/s + descriptive User-Agent; cache by accession (immutable). Detect
   format era (pre-2001 SGML txt / HTML / iXBRL) and the filing date.
2. **Normalize.** Parse to a canonical text + structure model, **preserving byte offsets**
   (round-trip depends on this). Reuse `edgartools` (MIT) for HTML/iXBRL; custom handling
   for legacy SGML txt.
3. **Derive expected-item template** (`07`). From filing date + DEI tags: Item 1C only
   FY2024+, Item 6 `[Reserved]` post-Feb-2021, smaller-reporting-company omissions
   (Item 7A), Part III usually incorporated-by-reference, 10-K/A amendment scope. This
   turns "missing item" from a false alarm into a conditional check.
4. **Segment — layered ensemble** (`02`,`03`):
   - **Primary:** TOC-anchor + regex header detection — handles ~95% of filings.
   - **Robust second opinion:** CRF line-labeller (reimplement the method — itemseg is
     NonCommercial; CPU-only, F1 ≈ 0.98), run independently.
   - **Escalation:** LLM with line-ID "index-don't-generate" (LIB) prompting **only** on
     low-confidence / disagreement boundaries and novel items. ~10% of the doc on ~15%
     of filings.
5. **Validate & score — the differentiator** (`06`): structural invariants → round-trip
   byte-reconstruction → independent dual-extractor agreement → XBRL Item-8 + DEI oracles
   → content heuristics. Emit a per-item confidence band + provenance; classify each
   absent item as legitimately-absent vs extraction-failure.
6. **Output.** Structured items as JSON — `{part, item, title, text, char_range,
   confidence, signals[], status}` — independently consumable, plus a filing-level
   confidence summary. Cache the result.

## Where the LLM is and is NOT used

NOT on the ~95% common case (rules + CRF win on both cost and accuracy: CRF F1 0.982 >
GPT4ItemSeg 0.957). LLM only on flagged boundaries / novel items. Blended **≈
$0.003–0.006 per filing** vs ~$0.24 full-Sonnet (`05`) — cheaper *and* more accurate.

## Evaluation strategy (`03`,`06`,`08`)

- **Label-free, on 100%:** structural invariants + round-trip + XBRL companyfacts Item-8
  cross-check + independent rule-vs-CRF agreement.
- **Stratified eval set N≈600** (era × filer-size × pathology); **150 hand-labelled gold**
  for calibration; **~90k EDGAR-CORPUS silver** as a scaled diff baseline (extended to
  FY2021–25 for Item 1C/Reserved).
- **Calibrate** confidence bands on gold; **validate-the-validator** by injecting
  perturbations (delete/reorder/truncate an item) and asserting each check fires.
- **Rigor rule:** independent oracles only — self-consistency cannot catch confident
  systematic errors.

## Top failure modes → detection (no silent failures)

| Failure mode | Example | Detection |
|---|---|---|
| Legacy regex over-capture (`ITEM 27(a)`, `ITEM 1`⊃`10–14`) | MSFT FY1995 | expected-template + dual-extractor disagreement |
| Part III incorporated-by-reference read as "missing" | Apple FY2024 | DEI/template → classify legitimately-absent |
| Styled-span / NBSP split headers | Apple FY2024 | DOM-aware parse + CRF line labels |
| Items out of canonical order | GE FY2023 cross-ref index | anchor-driven, never assume order |
| SRC legitimate omission (Item 7A) | M2i Global FY2023 | DEI `EntitySmallBusiness` gate |
| 10-K/A partial scope mislabelled | Chemed /A FY2024 | `AmendmentFlag` → relax completeness |
| XBRL fact offset misalignment | FY2019+ filers | treat XBRL as strong prior, not ground truth |
| Huge filing cost/latency blowup | GE 4.0 MB | streaming + escalation cost cap |

## Tech stack

Python; `edgartools` (ingest/normalize); `sklearn-crfsuite`/`python-crfsuite` (CRF); an
LLM tier (lean Claude) for escalation only; FastAPI + React/Streamlit frontend (`09`);
deploy Zeabur / HF Spaces; cache by accession.

## Refinements from the curated reading list (`docs/11`–`17`)

The reading list confirmed the architecture and added concrete upgrades — **no stage was
overturned**.

**Segmentation (`11`).** CRF features must be *structural* (`is-line-start`,
`prior-item-seen`, `in-TOC`), not text-only — local-window classifiers miss long-range
cues like GE's cross-reference index. The escalation LLM receives a *window* in
LumberChunker's "return the line ID where content shifts" shape, never the whole filing
(~120 calls/doc). Train the CRF on TOC-derived silver labels; scope vision/layout parsing
out (EDGAR ships text+tags).

**Confidence model upgrade (`12`,`13`) — supersedes the hand-weighted bands in `06`.**
- **Conformal prediction (split / Mondrian).** Calibrate a threshold `q̂` on the gold set
  to give each confidence band a distribution-free coverage guarantee; prediction-set size
  becomes the abstention/escalation trigger and `α` tunes the escalation rate. **Stratify
  `q̂` per format era** (filings aren't exchangeable) or legacy failures hide behind good
  average coverage.
- **XGrammar constrained decoding.** The escalation LLM emits only grammar-valid
  `{item_id ∈ closed set, line_ref ∈ doc range}` → 100% structurally valid output,
  mechanically enforcing index-don't-generate and deleting the bad-JSON / invented-item
  failure class. (Validity ≠ correctness — oracles still judge labelling.)
- **AIS** is the output contract our `char_range`+provenance already satisfies. **FactCC's
  synthetic perturbations** become the validate-the-validator CI. **SelfCheckGPT and
  verbalized confidence are banned as acceptance signals** (self-consistency / systematic
  overconfidence) — usable only inverted as escalation triggers; semantic-entropy probes
  only if self-hosting.

**New first-class requirement (`14`): cross-year boundary consistency.** Lazy Prices shows
YoY same-firm item-text diffs predict returns — which only holds if boundaries are stable
across years. ⇒ emit **stable item IDs**, treat **boundary drift as a silent-failure
mode**, and add **same-company multi-year pairs as an eval dimension**. Keep XBRL scoped to
fact presence/location, not meaning (FiNER-139 / FinTagging).

**LLM-judge policy (`15`): non-gating, last-resort flag only.** JudgeBench (judge ≈ random
on objective correctness) and Nine-Judges (a panel ≈ 2 independent votes, can't fix
correlated error) make the judge a "look here" signal, never "this is correct." Never feed
the generator's rationale to the judge (Gaming-the-Judge: up to +90% false positives).

**Eval harness spec (`16`,`17`).** Inspect AI structure (`Task = Dataset + Solver +
Scorer`): four independent scorers — structural-invariant + round-trip (100%), XBRL Item-8
(independent source), gold boundary-F1 (150). Report a **bundle, not one number**:
per-stratum F1 with **filing-clustered** CIs (±3–5% aggregate, explicitly wide on rare
strata 1C/7A), **Abstention-Recall as the headline silent-failure metric**, **pass^k**
reliability across re-runs of the nondeterministic escalation, and **cost/accuracy on the
same Pareto table** (HAL). Enforce a **`run_manifest`** (model build, temp, seed, harness)
— "the model is not the agent." Add prompt-perturbation robustness + automated
failure-cluster review.

## Open items that require BUILDING, not more research

These are why honest confidence caps below 100 until implementation: (a) HTML primary-doc
token census, (b) real LLM escalation rate on our corpus, (c) byte-level alignment of
`ix:nonFraction` facts to extracted text, (d) per-item vs umbrella Part III pointer
sentences, (e) a Part-III-only 10-K/A scope case, (f) the conformal `α` / escalation
threshold + per-filing pass predicate, (g) the 150-filing gold-labeling protocol, (h)
pass^k measurement of escalation nondeterminism, (i) run-to-run + prompt-robustness testing
of the LLM-LIB layer. Each is closed by building the pipeline and measuring on the eval set
— not by reading more.
