# Segmentation Methods: 4 Papers Applied to 10-K Item Segmentation

**研究日期:** 2026-06-22
**來源數量:** 4 primary papers (arXiv, abstracts + key sections via ar5iv)
**信心程度:** High for each paper's method and reported numbers (quoted from ar5iv full-text); Medium for the *transfer* claims to our corpus (no 10-K-specific ablation exists for three of the four).

---

## TL;DR

Our mission: split a raw 10-K into the canonical Items 1–16 (Parts I–IV) **robustly under heavy
format variance** (pre-2001 SGML txt, HTML, iXBRL), behind a layered ensemble:
**regex/TOC anchors → CRF line-labeller → LLM "index-don't-generate" only on flagged boundaries**
(see `docs/10-pipeline-architecture.md`).

These four papers map cleanly onto that stack and mostly *validate* it rather than overturn it.
Koshorek and Cross-Segment BERT are the **academic parents of our CRF line-labeller** — they
establish that per-line/per-boundary binary classification is the right framing and that a *local
window* around a candidate boundary is sufficient (the reason our CRF sidesteps the 65k-token
problem entirely). LumberChunker is a **cautionary tale**: LLM content-shift chunking is exactly
what NOT to run over a whole 65k-token filing on cost/latency grounds — but its iterative
"point to where content shifts" prompt is the right shape for our *escalation* tier on flagged
spans. The Document Parsing survey is mostly **out of scope** (it solves pixel→structure for
scanned PDFs; EDGAR already ships text + tags) — it matters only as a guard for the PDF-exhibit
long tail.

Net: the papers **sharpen tactics inside the design we already have**; they do not change the
architecture. Score for "how much this sharpens the design": **6/10** (details below).

---

## Paper 1 — Koshorek et al., "Text Segmentation as a Supervised Learning Task" (NAACL 2018)

URL: https://arxiv.org/abs/1803.09337

**1-line core idea.** Reframe text segmentation from an *unsupervised* lexical-cohesion problem
into a *supervised* per-sentence binary classification: for each sentence, predict "does this
sentence end a segment?"

**Method.** Hierarchical Bi-LSTM. A lower two-layer Bi-LSTM turns each sentence's words (max-pooled)
into a sentence embedding; an upper two-layer Bi-LSTM runs over the sequence of sentence embeddings
and a final softmax emits *n−1* segment-end probabilities (binary label *yᵢ* = "sentence *i* ends a
segment"). Trained on **WIKI-727K** (727,746 Wikipedia articles, labels derived automatically from
the table-of-contents section breaks; 80/10/10 split; NLTK Punkt sentence tokenizer). Reported **Pk**
(lower = better): 22.13 on Wiki-727K and **18.24 on Wiki-50 vs GraphSeg 63.56** and random 52.65;
human Pk on Wiki-50 ≈ 14.97. (It does worse than specialized regex on the synthetic Choi set — Pk
26.26 vs GraphSeg ~5–7 — an early hint that synthetic benchmarks mislead.)

**What we ADOPT.**
- The **framing** is our framing: item segmentation = per-line/per-unit binary "boundary or not"
  sequence labeling, not topic clustering. This is the conceptual root of our CRF line-labeller and
  of the financial SOTA (`itemseg`, Lu 2025) that descends from it.
- The **labels-from-structure trick**: WIKI-727K gets ground truth free from the article TOC. Our
  analogue: derive silver labels from the filing's own TOC/header anchors and from EDGAR-CORPUS, so
  the CRF can be trained at scale without hand-labelling 90k filings (see `docs/08`).
- Confirmation that **a model "generalizes well to unseen natural text"** — i.e. a learned
  line-labeller is more robust to format variance than hand-tuned regex, which is precisely why the
  CRF is our *robust second opinion* over the regex/TOC primary.

**What's a TRAP / limitation for 10-K.**
- **Sentence-granularity + Pk objective is the wrong unit and the wrong metric for us.** 10-K item
  boundaries fall on *line/header starts*, not mid-paragraph sentence boundaries; and Pk tolerates
  near-misses, whereas a misplaced Item-7/Item-8 boundary that swallows the financial statements is
  a *hard* error we must catch exactly. We label *lines* (item boundary = line start) and evaluate
  with exact boundary F1 + our round-trip invariant, not Pk.
- **It needs labeled training data and a GPU** for the LSTM. Our CRF baseline gets ~the same job
  done on CPU (Lu 2025: CRF macro-F1 ≈ 0.978–0.982 ≈ BERT 0.983), so we do **not** reimplement the
  LSTM — Koshorek is the *idea* we inherit, not the *architecture* we ship.
- Synthetic-benchmark caveat (its Choi result) reinforces our rule: **evaluate on real EDGAR
  filings stratified by era/pathology, never on a synthetic mix** (`docs/08`).

**Does it scale to 65k tokens?** Yes, structurally — it never encodes the whole document at once; it
processes a *sequence of sentence embeddings*, which is cheap. This is the property our CRF preserves.

---

## Paper 2 — Lukasik et al., "Text Segmentation by Cross Segment Attention" (EMNLP 2020)

URL: https://arxiv.org/abs/2004.14535

**1-line core idea.** Decide each candidate boundary *independently* from only a **local window of
tokens to its left and right** — no whole-document encoding needed.

**Method.** Three variants compared: (a) **Cross-Segment BERT** — feed BERT the *L* word-pieces
before the candidate break and *R* after, separated by `[SEP]`, and binary-classify "boundary
here?"; primary config is **128–128 word-pieces** (max 255/side, inside BERT's 512 limit). (b)
**BERT+Bi-LSTM** — BERT-encode each sentence, then a Bi-LSTM over sentence vectors. (c)
**Hierarchical BERT** — sentence `[CLS]` vectors through a document-level transformer. Reported:
Wiki-727K **F1 66.0**, RST-DT F1 95.0, Choi F1 99.9 / Pk 0.07 — "state-of-the-art, reducing error
rates by a large margin," and "models with many fewer parameters." Authors note the local window
"might be sub-optimal, as longer-distance linguistic artifacts are likely to help locating breaks,"
and flag Choi data leakage.

**What we ADOPT.**
- **This is the strongest theoretical justification for our whole approach.** Self-attention cost is
  quadratic in input length; encoding a 65k-token 10-K end-to-end is infeasible/expensive. Cross-
  Segment BERT proves you don't have to — a **fixed local window (e.g. 128 tokens each side) around
  each candidate header is enough** to classify the boundary. Our CRF does the analogous thing with
  per-line features; if we ever swap the CRF for a transformer, this is the exact recipe (and the
  one Lu 2025's BERT4ItemSeg already follows: line embeddings, never the whole doc).
- The **window is also how the LLM escalation tier should be fed**: don't hand the model the whole
  filing; hand it a windowed span around the flagged boundary. Cheap, in-budget, and aligned with
  index-don't-generate.
- "Many fewer parameters, good performance" → reinforces choosing the **cheapest model that hits
  the F1 bar** (CRF) over the heaviest.

**What's a TRAP / limitation for 10-K.**
- The authors' own caveat — **local windows miss long-range cues** — bites us on the cases that
  matter most: distinguishing a *real* `ITEM 7.` header from a cross-reference "see Item 7" or a
  TOC line requires knowing position-in-document and what came before. So the window classifier must
  carry **structural features** (is-line-start, in-TOC-region, prior-item-seen, distance-from-doc-
  start), not just raw text. Our CRF already encodes these; a naive 128–128 text-only window would
  regress on exactly the GE-cross-reference / merged-Item-1+2 failure modes.
- **128–128 word-pieces is a Wikipedia-prose tuning.** 10-K headers are short, table-dense, and
  whitespace-noisy; the right window for us is "the candidate line ± a few lines," not 128 prose
  tokens. Treat the number as a *pattern*, not a constant.
- Choi F1 99.9 is **leakage-inflated** (authors say so) — ignore it; the honest signal is Wiki-727K
  F1 66.0, i.e. real natural-text segmentation is hard, which is why we keep the regex/TOC primary
  for the easy 95% and reserve learning for the hard tail.

**Does it scale to 65k tokens?** This is *the* paper that says yes by construction — O(boundaries ×
window), linear, not O(doc²). Directly underwrites our cost story (`docs/05`).

---

## Paper 3 — Duarte et al., "LumberChunker: Long-Form Narrative Document Segmentation" (2024)

URL: https://arxiv.org/abs/2406.17526

**1-line core idea.** Use an LLM to *dynamically* chunk a document by iteratively asking it where
content begins to shift, yielding variable-size semantically-coherent chunks.

**Method.** Concatenate sequential passages into a group until the group exceeds a token threshold
**θ ≈ 550 tokens** (tuned), then prompt the LLM to return the ID of the first passage where content
shifts; restart the next group from that passage and repeat to the end. LLM = **Gemini 1.0-Pro**.
Benchmark = **GutenQA** (100 Project Gutenberg books, 3000 "needle-in-a-haystack" QA pairs, ~30
high-quality Qs/book). Result: **DCG@20 62.09 vs 54.72 recursive chunking = +7.37%** retrieval gain,
beating other chunkers and a Gemini-1.5-Pro long-context baseline. **Cost/latency is the headline
caveat: 95–1,628 seconds per document of iterative LLM calls vs 0.1–0.6 s for recursive chunking**;
authors explicitly state it "requires the use of an LLM, which automatically renders it more
expensive and slower."

**What we ADOPT.**
- The **prompt shape** for our escalation tier: "here are sequential candidate passages with IDs;
  return the ID where the content shifts" is exactly **index-don't-generate at the boundary level**
  — the model points to a line ID, it does not rewrite text. This is more robust than asking an LLM
  to "extract Item 7," and it matches our LIB (line-ID-based) prompting plan.
- The empirical confirmation that **LLM content-shift detection genuinely beats fixed/recursive
  chunking on coherence** (+7.37% downstream) — justifying the LLM tier's *existence* for the
  genuinely ambiguous boundaries and novel items (Item 1C) where rules and CRF disagree.

**What's a TRAP / limitation for 10-K — and it's a big one.**
- **NEVER run LumberChunker over a whole 65k-token filing.** At θ≈550 tokens/group, a 65k-token
  10-K is ~120 sequential LLM calls *per filing*, and the paper measures up to **1,628 s/doc**. That
  is the antithesis of our cost target (~$0.003–0.006/filing, `docs/05`) and would blow latency by
  3–4 orders of magnitude vs the CRF (CPU, sub-second). LumberChunker is the **concrete proof of why
  the LLM must be the escalation tier on ~10% of spans, not the primary segmenter.**
- It chunks for **retrieval coherence**, not for **named-item boundaries**. Its objective ("where
  does narrative content shift") is not "where does Item 1A end and Item 1B begin" — a 10-K Item
  boundary is a *structural/regulatory* fact, often with little semantic shift (e.g. Item 1B
  `[None]`, Item 6 `[Reserved]`). LLM content-shift would happily mis-split mid-Risk-Factors or
  miss a `[Reserved]` stub. So we constrain the LLM with the **expected-item template** (`docs/07`)
  and only ask it to *adjudicate a flagged boundary*, never to discover the item structure freely.
- Narrative-book benchmark (GutenQA) has **zero format variance** vs our SGML/HTML/iXBRL spread —
  its results don't transfer to robustness claims; we take only the prompt pattern.

**Does it scale to 65k tokens?** **No** — that's the whole point. It is sequential, LLM-bound, and
the authors report up to 1,628 s/doc. Use only on bounded, pre-flagged spans.

---

## Paper 4 — Zhang et al., "Document Parsing Unveiled" — survey of layout/OCR-free parsing (2024)

URL: https://arxiv.org/abs/2410.21169

**1-line core idea.** Survey of how to turn *unstructured/scanned* documents into machine-readable
structure, taxonomized into **(a) modular pipelines** (layout detection → OCR → table/formula
recognition) vs **(b) unified OCR-free VLMs** (end-to-end image→structure, e.g. Donut/Nougat/GOT
lineage).

**Method/scope.** Covers layout analysis and recognition of heterogeneous content (text, tables,
math, figures); two-branch taxonomy (pipeline vs VLM). Key challenges named: robustness to **complex
layouts**, reliability of VLM parsing (hallucination), and **inference efficiency**. Conclusion is
even-handed: both paradigms remain viable depending on document type; VLMs simplify the pipeline but
trade away reliability and speed on dense/complex pages.

**What we ADOPT.**
- Mostly a **negative result for us, which is useful**: it confirms that **for EDGAR HTML/iXBRL we
  do NOT need any of this.** EDGAR's primary documents already carry machine-readable text + DOM tags
  (and, post-2009, iXBRL facts). Pixel→structure parsing is solving a problem we don't have; pulling
  in LayoutLMv3/Donut/Nougat for the common case would be pure overkill and added failure surface.
- The survey's "complex layout robustness" and "VLM reliability/hallucination" warnings **generalize
  to our table handling**: financial statements (Item 8) are dense multi-column tables, and the
  survey's caution that VLM/OCR-free parsing is least reliable on exactly these is a reason to keep
  Item 8 boundaries anchored on **structure + the XBRL companyfacts oracle** (`docs/07`), not on any
  vision model.

**What's a TRAP / limitation for 10-K.**
- **Scope mismatch.** This is a *PDF/scanned-image* discipline. Treating a 10-K as an image to be
  OCR-parsed throws away the tags EDGAR already gives us and is strictly worse on cost, latency, and
  fidelity. The only legitimate use is the **long tail of PDF-only exhibits** (some EX-99 press
  releases, scanned attachments) where there is genuinely no text layer — and even then it's an
  exhibit-extraction concern, not Item 1–16 segmentation.
- VLM hallucination risk directly violates our index-don't-generate principle. Reserve, gate behind
  "no text layer detected," and validate any VLM output against round-trip/structure invariants.

**Does it scale to 65k tokens?** N/A — different modality (images/pages). Irrelevant to the main path.

---

## What changes in our design

Net assessment: **the papers confirm the architecture and sharpen four tactics; they change no
stage.** Concretely:

1. **CRF features must be structural, not just local text (from Paper 2's own caveat).** Add/keep
   `is_line_start`, `in_TOC_region`, `prior_items_seen`, `distance_from_doc_start`, `next_header_id`
   features so the line-labeller resolves the long-range cases (GE cross-reference, merged
   Item 1+2) that a pure local window provably misses. This is the single highest-value change.
2. **Feed the LLM escalation tier a *window*, in the LumberChunker prompt shape, never the whole
   doc.** Standardize the escalation prompt as "here are candidate lines with IDs spanning the
   flagged boundary ± context; return the line ID where Item X ends / Item Y begins" — index, don't
   generate. Cap the window so per-call cost stays inside `docs/05` budget. This codifies *why*
   LumberChunker-style chunking is banned as a primary and welcomed as an adjudicator.
3. **Train the CRF on structure-derived silver labels at scale (Koshorek's labels-from-TOC trick).**
   Use filing TOC/header anchors + EDGAR-CORPUS to generate training labels without hand-annotating;
   reserve the 150 hand-labelled gold for calibration only (`docs/08`).
4. **Metric discipline (from Papers 1 & 2's benchmark caveats).** Do NOT adopt Pk or synthetic-
   benchmark F1 as our headline; keep **exact-boundary F1 + round-trip byte-reconstruction +
   XBRL Item-8 containment** on a real, era-stratified EDGAR eval set. Treat Choi-style numbers as
   leakage-inflated and irrelevant.
5. **Explicitly scope OUT layout/OCR/VLM parsing (Paper 4).** Document that vision parsing is only a
   gated fallback for text-layer-absent PDF exhibits, never on the HTML/iXBRL Item-segmentation path.

What does **not** change: the three-tier ensemble, CRF-on-CPU as the robust workhorse, LLM-as-
escalation-only, the validation/confidence layer as the real differentiator. None of the four papers
provides a 10-K-specific result that would justify promoting the LLM tier or adding a vision tier;
the 10-K-specific authority remains Lu et al. 2025 (`itemseg`, `docs/03`).

---

## Sources

- Koshorek et al., "Text Segmentation as a Supervised Learning Task," NAACL 2018 — https://arxiv.org/abs/1803.09337
- Lukasik et al., "Text Segmentation by Cross Segment Attention," EMNLP 2020 — https://arxiv.org/abs/2004.14535
- Duarte et al., "LumberChunker: Long-Form Narrative Document Segmentation," 2024 — https://arxiv.org/abs/2406.17526
- Zhang et al., Document Parsing survey (layout / OCR-free), 2024 — https://arxiv.org/abs/2410.21169
- Internal: `docs/03-sota-segmentation-and-eval.md`, `docs/05-cost-latency-scalability.md`, `docs/07-ixbrl-structure-exploitation.md`, `docs/08-eval-set-construction.md`, `docs/10-pipeline-architecture.md`
