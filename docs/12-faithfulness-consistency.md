# Faithfulness & Consistency Metrics — Fit for Ground-Truth-Free 10-K Item Extraction

Synthesis of 7 faithfulness/consistency papers, mapped against **our** hardest problem:
verifying 10-K item extraction **without public ground truth**. Reads alongside
`06-confidence-and-silent-failure.md` (independent-oracle stack) and
`10-pipeline-architecture.md`.

## The framing that decides everything: we INDEX, we do not GENERATE

All 7 papers were built for **abstractive summarization / NLG**: a model *writes* new
text, and the metric asks "is the written text faithful to the source?". The dominant
failure they fight is *fabrication* — tokens in the output that have no support in the
source.

Our pipeline (`10`) does not fabrication-generate item bodies. Extraction is **indexing
into the source**: an item body is a `char_range` into the original filing, and our
free, hard oracle is **round-trip byte reconstruction** — concatenated spans + gaps must
reproduce the source byte-for-byte (`06` §2). When output text is provably a substring of
the source, the entire class of "is this sentence supported by the source?" questions is
**already answered by construction**. That is a stronger guarantee than any NLI/QA metric
below can offer, because those are *learned, noisy approximations* of exactly the property
we get *exactly and for free*.

So the blunt thesis: **for the indexing core of our pipeline, most of these metrics are
redundant at best and a TRAP at worst** (they re-introduce a learned-model dependency to
"check" something we already proved). Their real value concentrates in two narrow places:

- **(A) The LLM-escalation tier** (`10` stage 4) — the *one* place generation-like risk
  re-enters. When the LLM is asked to emit a boundary/label (even under "index-don't-
  generate" LIB prompting), it *can* drift into paraphrase or hallucinate a header that
  isn't there. Here a faithfulness check that the LLM's claimed span is actually
  source-grounded is genuinely useful.
- **(B) Attribution discipline** — not a metric but a *standard* (AIS) for how we present
  every extracted item: each item must be attributable to identified source spans. We
  already do this via `char_range` + provenance; AIS gives us the vocabulary and an
  evaluation protocol.

A second hard rule from `06` §"independent oracles only" governs adoption: **a method that
checks a model with the same/another model on the same input is self-consistency, and
self-consistency cannot catch confident systematic errors.** This immediately disqualifies
one paper (SelfCheckGPT) as a *validator* and demotes the QA-family to *escalation-only
soft signals*.

---

## Per-paper: core idea → signal → ADOPT vs TRAP

### 1. FactCC — NLI factual consistency via synthetic transformations
<https://arxiv.org/abs/1910.12840>

- **Core idea.** Train a weakly-supervised classifier on *synthetic* (claim, document)
  pairs: take source sentences, apply rule-based transformations (paraphrase, entity/
  number/pronoun swap, negation, sentence shuffle), and label the corrupted ones as
  inconsistent. The model learns to flag claims not entailed by the document.
- **Signal.** Binary consistent/inconsistent per claim, **plus span-level localization**
  (it extracts the supporting source span and the offending summary span).
- **ADOPT (the method, not the model).** Two things transfer directly. First, **span
  localization** is exactly our attribution shape — "point at the source bytes that
  support this." Second, and more important, **the synthetic-transformation training
  recipe IS our "validate-the-validator" plan** (`06` §"validate-the-validator"): inject
  perturbations into known-good filings (delete an item, swap order, truncate mid-item)
  and assert the checks fire. FactCC legitimizes this as a published methodology, and its
  transformation taxonomy (entity swap, number swap, negation) maps onto our perturbation
  set (item swap, boundary shift, byte drop). **Adopt the perturbation methodology; do
  NOT ship a FactCC classifier as a runtime oracle** — a learned consistency model on
  filings is itself an unvalidated approximation and would violate "independent oracles
  only" if used to grade extraction.
- **TRAP.** Using the *trained FactCC model* as a confidence signal. It was trained on
  CNN/DM news; on dense legal/financial prose it has no calibration, and a learned model
  that is confidently wrong is exactly the systematic-error case our rule forbids.

### 2. SummaC — NLI consistency at the right granularity
<https://arxiv.org/abs/2111.09525>

- **Core idea.** Off-the-shelf NLI worked poorly for inconsistency detection because of a
  **granularity mismatch**: NLI is trained sentence-pair, but the task is document-level.
  SummaC segments both source and summary into sentences, computes a full NLI entailment
  matrix (every summary sentence × every source sentence), and aggregates (max → Zero
  Shot, or a learned 1-D conv → Conv). Balanced acc 74.4% on the SummaC benchmark.
- **Signal.** A document-level consistency score from aggregated sentence-pair entailment
  probabilities; the entailment matrix itself is interpretable (which source sentence
  best supports each summary sentence).
- **ADOPT (narrow, escalation-only).** The **entailment-matrix idea is the right tool for
  one job**: when the LLM-escalation tier returns a *boundary* but we want to confirm the
  classified item body semantically matches its claimed item type (Item 1A reads like risk
  factors, Item 3 like legal proceedings), an NLI/entailment check of body-vs-header-claim
  is a cheap soft signal. This is a strictly better-grounded version of our `06` §5
  "content sanity keywords." Use as a **Medium-band soft signal**, never a gate.
- **TRAP.** The whole premise is "does the summary *say* something the source doesn't?" —
  a *fabrication* test. Our spans are literal source substrings, so summary-vs-source NLI
  is **vacuously near-entailment for the indexing core** and tells us nothing about the
  thing we actually get wrong (boundary placement / mislabelling). Do not spend NLI budget
  proving substrings entail their superset.

### 3. QAGS — QA-based faithfulness
<https://arxiv.org/abs/2004.04228>

- **Core idea.** If a summary is faithful, then a question generated from the summary
  should get the *same answer* whether answered against the summary or against the source.
  Generate questions from the summary, answer both ways, compare answers.
- **Signal.** Per-summary consistency score + which tokens/answers diverged
  (interpretable).
- **ADOPT (very narrow).** Useful **only** as a round-trip *semantic* check on
  LLM-escalation output where the LLM did more than index — e.g. if it ever emits a
  normalized item *title* or summary field, QAGS-style answer-agreement can flag a drifted
  title. Marginal for us.
- **TRAP.** Two traps. (a) It assumes the summary-vs-source setup; for literal spans the
  answers are trivially identical → no signal. (b) It is **expensive** (QG + 2× QA per
  item) — directly against our cost design (`05`, blended ≈$0.003–0.006/filing). Running
  QAGS over every item would dwarf extraction cost for a check the round-trip already
  subsumes.

### 4. QuestEval — reference-less QA, precision + recall
<https://arxiv.org/abs/2103.12693>

- **Core idea.** Reference-less metric combining **precision** (questions from the
  *summary*, answered from the *source* — are summary claims supported?) and **recall**
  (questions from the *source*, answered from the *summary* — did the summary capture the
  source?).
- **Signal.** Two-sided score: consistency (precision) + coverage/completeness (recall).
- **ADOPT (conceptual, not literal).** The **precision/recall *decomposition* maps cleanly
  onto two oracles we already have, and naming it this way sharpens our story**:
  - *Precision = "is every extracted span actually that item?"* → our dual-extractor
    agreement + content sanity (`06` §3, §5).
  - *Recall = "did we capture all of the source / drop nothing?"* → our **round-trip
    byte-reconstruction** (`06` §2), which is the *exact, free* version of QuestEval's
    learned recall.
  Adopt the **vocabulary** (precision vs recall of extraction) for the report; we already
  have stronger mechanisms for both.
- **TRAP.** Running QuestEval's actual QA models as our oracle. Its recall via QA is a
  lossy estimate of coverage; round-trip gives coverage *exactly*. Replacing an exact
  byte check with a learned QA approximation would be a strict downgrade.

### 5. QAFactEval — tuned QA factual consistency
<https://arxiv.org/abs/2112.08542>

- **Core idea.** A carefully-engineered QA-based metric; the paper's finding is that
  **component choice matters** — especially question generation, **answerability
  classification** (don't penalize unanswerable questions), and answer-overlap scoring.
  +14% over prior QA metrics on SummaC; QA and entailment signals are **complementary**.
- **Signal.** Best-in-class (at the time) QA-based factual-consistency score.
- **ADOPT (one durable lesson, not the metric).** The takeaway we keep: **"answerability
  classification is critical"** ≈ our principle that **"missing must be classified, never
  dropped"** (`06`). QAFactEval refuses to score questions the source can't answer; we
  refuse to treat an absent item as a failure when the template/DEI says it's
  legitimately absent. Same discipline. Also banks the **"entailment + QA are
  complementary"** result → justifies our *ensemble* of independent signals rather than
  betting on one.
- **TRAP.** Same as QAGS/QuestEval — summary-vs-source assumption + cost. Not a runtime
  oracle for us.

### 6. SelfCheckGPT — sampling self-consistency  ⚠️ DISQUALIFIED AS VALIDATOR
<https://arxiv.org/abs/2303.08896>

- **Core idea.** Zero-resource, black-box hallucination detection: sample the model
  multiple times on the same prompt; if it *knows* the fact, samples agree; if it
  hallucinates, samples diverge. Score = inconsistency across samples (via BERTScore / QA
  / n-gram / NLI / prompt variants).
- **Signal.** Per-sentence and passage-level hallucination likelihood from
  **self-agreement**, with **no source and no external reference**.
- **TRAP — and it is THE canonical case for our rigor rule.** SelfCheckGPT is pure
  **self-consistency**: it measures whether a model agrees *with itself*. Per `06`
  §"independent oracles only" and the global engineering-rigor rule, **self-consistency
  cannot catch confident systematic errors.** If our LLM-escalation tier is *consistently*
  wrong about a non-standard filing's Item 6 (e.g. always reads a `[Reserved]` placeholder
  as a real item), all samples agree, SelfCheckGPT reports high confidence, and the
  systematic error sails through. This is precisely the failure mode our whole validation
  layer exists to prevent. **Explicitly do NOT adopt as a validator.**
- **Narrow legitimate use (NOT validation).** Sampling *disagreement* is a fine cheap
  **escalation trigger / abstention signal**: if the LLM gives unstable boundaries across
  samples, that's a reason to *flag for an independent oracle or human review* — never a
  reason to *accept*. Used this way it routes work; it does not certify correctness. Keep
  the asymmetry strict: instability ⇒ distrust; stability ⇒ **proves nothing**.

### 7. AIS (Attributable to Identified Sources) — attribution *standard*
<https://arxiv.org/abs/2112.12870>

- **Core idea.** Not a metric — a **conceptual framework + human-eval standard**. A system
  output is AIS-valid if every shared piece of information is **attributable to an
  identified source**: a reader could verify the statement against the cited source. Comes
  with a two-stage human annotation protocol.
- **Signal.** A standard/definition (and a human-eval rubric), not an automatic number.
- **ADOPT — strongest conceptual fit of all 7.** AIS is essentially the *formal spec for
  what our output already promises*. Our every item ships `{char_range, signals[],
  provenance}` — i.e. it is **attributable to an identified source span by construction**.
  Because we index rather than generate, **we satisfy AIS trivially and provably**, which
  is a selling point: an indexing extractor is *born AIS-compliant*, whereas a generative
  summarizer must be *measured* for it and usually falls short. Concretely adopt:
  - Frame the output contract as "**every item is Attributable to Identified Sources** —
    here is the exact `char_range`," citing AIS as the standard we meet.
  - Borrow the **two-stage annotation protocol** for our 150-filing hand-labelled gold set
    (`08`): stage 1 "is the span interpretable/well-formed?", stage 2 "is it attributable
    to the right item?" — a clean rubric for human labellers.
- **TRAP.** Minimal. The only caution: AIS is a *standard*, not an automatic guard — it
  tells you *what* to verify, not *that* it's verified. Our automatic enforcement of AIS is
  the round-trip + char_range invariant, not AIS itself.

---

## Cross-cutting: which assume "summary vs source" and therefore mis-fit indexing

| Paper | Assumes generated≠source (fabrication test)? | Fit to our INDEXING core |
|---|---|---|
| FactCC | Yes | Method (synthetic perturbation, span localization) transfers; model does not |
| SummaC | Yes | Vacuous on literal substrings; entailment-matrix useful only for *label* check |
| QAGS | Yes (strongly) | Trivial-pass on substrings; expensive |
| QuestEval | Yes | P/R *framing* transfers; we already have exact versions |
| QAFactEval | Yes | One discipline (answerability) transfers; metric does not |
| SelfCheckGPT | **No source at all (self-consistency)** | **Disqualified as validator**; escalation-trigger only |
| AIS | It's the *standard for* attribution | **Best fit** — we satisfy it by construction |

The recurring trap: every QA/NLI metric here is a **learned, noisy estimator of "is the
output supported by the source."** Indexing answers that *exactly and for free* via
round-trip. Swapping an exact invariant for a learned approximation is always a downgrade,
and using a learned model to "validate" extraction reintroduces the confident-systematic-
error risk our rigor rule forbids.

---

## Which of these we ACTUALLY use, and for what

1. **AIS — adopted as our output contract + gold-labelling rubric.** Every emitted item is
   *Attributable to an Identified Source* span (`char_range` + provenance). We satisfy the
   standard by construction (indexing), and we borrow its two-stage annotation protocol for
   the 150-filing gold set (`08`). *This is the one we lean on hardest.*

2. **FactCC's synthetic-transformation recipe — adopted as "validate-the-validator."** Its
   corruption taxonomy (entity/number swap, negation, shuffle) is the published basis for
   our perturbation CI (delete/reorder/truncate an item → assert each oracle fires; `06`).
   We do **not** run a FactCC classifier at runtime.

3. **SummaC's entailment matrix — adopted as a Medium-band SOFT signal, escalation-only.**
   Used solely to check that an LLM-escalated item *body* semantically matches its claimed
   *item type* — a better-grounded `06` §5 content-sanity check. Never a gate; never run on
   the rules/CRF common case.

4. **QuestEval's precision/recall decomposition — adopted as VOCABULARY.** "Extraction
   precision" = dual-extractor + content sanity; "extraction recall" = round-trip coverage.
   We use the framing in the report; we already have exact mechanisms for both.

5. **QAFactEval's answerability discipline — adopted as a PRINCIPLE.** Mirrors "missing is
   classified, not dropped" (legitimately-absent vs extraction-failure). Also banks
   "entailment+QA are complementary" → justifies our independent-signal ensemble.

6. **SelfCheckGPT — explicitly NOT used as a validator.** Sampling stability *proves
   nothing* (cannot catch confident systematic errors → violates "independent oracles
   only"). Permitted use is the inverse only: sampling *instability* in the LLM tier is a
   cheap **escalation/abstention trigger** that routes an item to an independent oracle or
   human — never an acceptance signal.

7. **QAGS — not used** (subsumed by round-trip; cost-prohibitive; trivial-pass on literal
   spans).

**Net:** the indexing design means we already hold a *stronger, exact* guarantee
(round-trip + char_range = provable, free attribution) than these *learned, approximate*
faithfulness metrics provide. Their durable contributions for us are **AIS as a standard**,
**FactCC's perturbation methodology for validating our validators**, **a narrow
entailment/QA soft signal on the LLM-escalation tier only**, and a **sharper precision/
recall vocabulary** — all while SelfCheckGPT stands as the textbook example of the
self-consistency trap our rigor rule was written to avoid.

## Sources

- FactCC — <https://arxiv.org/abs/1910.12840>
- SummaC — <https://arxiv.org/abs/2111.09525>
- QAGS — <https://arxiv.org/abs/2004.04228>
- QuestEval — <https://arxiv.org/abs/2103.12693>
- QAFactEval — <https://arxiv.org/abs/2112.08542>
- SelfCheckGPT — <https://arxiv.org/abs/2303.08896>
- AIS (Attributable to Identified Sources) — <https://arxiv.org/abs/2112.12870>
