# SOTA: 10-K Item Segmentation & Ground-Truth-Free Evaluation

**研究日期:** 2026-06-22
**來源數量:** ~25 primary sources (papers, OSS repos, SEC APIs)
**信心程度:** High for (A) segmentation lineage and OSS verdicts; High for (B) reference-free validation techniques. All arXiv IDs and OSS verdicts below were verified in prior research passes. Numbers quoted from paper abstracts/tables; a handful are snippet-level and flagged `[snippet]`.

---

## TL;DR

- **Most robust segmentation approach:** a **layered ensemble** — cheap regex/anchor + TOC parsing handles ~95% of filings; a **CRF or BERT line-labeling** model (item boundaries coincide with line starts, so sequence-labeling sidesteps the 512-token limit) handles format variance; an **LLM with line-ID-based (LIB) "index-don't-generate" prompting** is reserved for the ambiguous-boundary minority and for newly-introduced items (e.g. Item 1C cybersecurity, 2023). This matches the published SOTA (NTU `itemseg`, Lu et al. 2025), where CRF (F1≈0.978–0.982, CPU-only) essentially ties BERT (≈0.983) and beats rule-based regex (≈0.905).
- **Strongest ground-truth-free validators:** (1) **structural invariants** — canonical item order, each item present exactly once, non-overlapping char ranges, full-coverage (no dropped bytes); (2) **round-trip / reconstruction** — if extraction is *indexing* (pointers into source), reassembly must equal the original byte-for-byte, giving a lossless guarantee for completeness; (3) **cross-extractor agreement** — run rule-based vs LLM independently and measure boundary disagreement as a confidence/data-quality flag; (4) **XBRL companyfacts cross-modality check** — exact numeric facts from `data.sec.gov` *must* fall inside the Item 8 boundary, the only true external oracle available with zero labeling cost. Add a **validate-the-validator** step (inject known perturbations, confirm each check fires).

---

## (A) State-of-the-Art Approaches to Segmenting Long Financial/Legal Documents

The goal: split a raw 10-K into the canonical Items (Items 1–16 across Parts I–IV: Item 1 Business, 1A Risk Factors, 1B/1C, 2 Properties, 3 Legal, 4 Mine Safety; 5–9 incl. 7 MD&A, 7A Market Risk, 8 Financial Statements; 9A Controls, 9B, 9C; 10–14 governance; 15–16 exhibits). Approaches below run from cheapest/most brittle to most flexible/most expensive.

### A.1 Anchor / regex item-boundary detection

Pattern-match item headers (`ITEM 1.`, `Item 1A.`, case/whitespace/punctuation variants) and slice between consecutive anchors. This is the historical baseline.

- **What works:** a *broad-start, robust-end* pattern pair — e.g. detect the **start** of Item 7 generously, then anchor the **end** on the next header (Item 7A / Item 8). Line-anchored matching (require the header to begin a line) kills most false positives from cross-references in body text.
- **Performance ceiling:** Lu et al. (2025) measure rule-based regex at **macro-F1 ≈ 0.9048** on core items — clearly below ML. Earlier work is worse and instructive: Brown & Tucker (2011) regex recovered only **73%** of MD&A; Campbell et al. (2014) regex+HTML-scoring hit **65% recall / 98% precision** — but *only on the ~65% of filings that parse at all*. **The dominant failure mode is silent failure on legacy/edge-case filings**, not loud crashes.
- **Known OSS bug illustrating the risk:** `edgar-crawler` (nlpaueb) regex pipeline merges **Item 1 + Item 2** on some filings (issue #35). Treat any single-tool regex output as a *silver* baseline, not gold.
- **Tradeoff:** near-zero cost, fully interpretable, fast; but brittle to the long tail (cross-reference-style TOCs, items placed out of order, items embedded inside other items).

### A.2 Table-of-contents-driven splitting

Parse the filing's TOC (often a `<table>` of item titles + anchors/page refs), then use it as a map to locate each item body.

- `edgartools` (the best OSS base, see A.3) uses **multi-strategy resolution**: TOC parse → header-pattern fallback → *cross-reference-index detection* (handles GE-style filings whose body says "see Part II, Item 7" instead of repeating the header).
- **Academic analogue — FinTOC shared task** (FNP workshop, 2019–2023): the canonical financial-document-structure task. Corpus is financial **prospectuses (PDF)**, deliberately chosen because *prospectuses often lack a usable TOC* — exactly the hard case. Two subtasks worth reusing as a design idea: **Title Detection (TD, metric=F1)** and **TOC Generation (hierarchical nesting depth, metric=harmonic mean of Inex-F1 and Inex level-accuracy)**. **Key design lesson: report boundary-correctness separately from hierarchy-depth-correctness — they are different failure modes.** (ISPRAS won 2022 EN/FR with TD F1 ≈ 0.900 EN, degrading to ≈0.558 ES — TOC quality is language/format-sensitive `[snippet]`.)
- **Tradeoff:** when a clean TOC exists this is the most reliable map; but many 10-Ks have malformed, partial, or cross-reference TOCs, so TOC parsing must *fall back* gracefully, never be the sole strategy.

### A.3 DOM / structure-based segmentation of HTML / iXBRL

Modern EDGAR filings (HTML era ≈2001+) are tagged documents; the DOM already encodes headings, tables, and (for iXBRL) machine-readable facts. Exploit structure instead of treating the doc as a flat string.

- **`edgartools`** (dgunning, MIT, ~2.4k★, used at hedge funds) — **recommended base**. `filing.obj()["Item 1"]`. Gives XBRL access + HTML→clean-text/markdown. *Caveat: no confidence signal* — you must add your own validation layer.
- **`sec-parser`** (alphanome-ai, MIT, beta) — produces a **semantic-element tree** (`TitleElement`, `TableElement`, `TopSectionTitle`); HTML-only; you group elements into items yourself. Good when you want structural control.
- **`sec-api.io`** — commercial/paywalled; leaves HTML entities unescaped (`Management&#8217;s`) and marks tables `##TABLE_START`.
- **Tradeoff:** DOM structure is far more reliable than flat-string regex *for HTML-era filings*, but pre-2001 filings are SGML-wrapped plaintext with no helpful tags — you need a **normalization layer** that produces a consistent internal representation across SGML/HTML/iXBRL before segmenting.

### A.4 Layout / ML models (document segmentation, sequence labeling)

Frame segmentation as **supervised sequence labeling over lines** (BIO-style tags marking item boundaries). This is the published SOTA lineage.

- **Modeling lineage:** TextTiling (Hearst 1997, unsupervised lexical-cohesion depth scores — classic baseline) → **Koshorek et al. (NAACL 2018, arXiv 1803.09337)** reframed segmentation as a *supervised* task (WIKI-727K, hierarchical neural labeling) → **Lukasik et al. (EMNLP 2020, arXiv 2004.14535) "Text Segmentation by Cross Segment Attention"** (Cross-Segment BERT looks at k tokens left/right of each candidate break — cheap and strong; direct design parent of the financial model below).
- **Financial SOTA — Lu, Chien, Yen, Chen (NTU, 2025), "Utilizing PLMs and LLMs for 10-K Items Segmentation" (arXiv 2502.08875; repo `github.com/hsinmin/itemseg`).** THE authoritative source. Dataset: **3,737 manually-annotated 10-Ks, FY2001–2019**.
  - **BERT4ItemSeg** (best, **macro-F1 ≈ 0.9826** on core items 1/1A/3/7): line-by-line Sentence-BERT embeddings → Bi-LSTM sequence labeling with modified BIO tags. *Because item boundaries coincide with line starts, the 512-token BERT limit is never hit.* Needs GPU; runs locally, no API cost.
  - **CRF baseline: macro-F1 ≈ 0.9788–0.9818, CPU-only** — essentially ties BERT. This is the pragmatic high-ROI core.
  - **GPT4ItemSeg: macro-F1 ≈ 0.9552–0.9567** (see A.5).
- **Layout/vision models** (LayoutLMv3, Donut, DocFormer; survey arXiv 2410.21169) target **scanned/PDF** documents where you must recover structure from pixels. For EDGAR HTML/iXBRL — which already carries text + tags — these are generally **overkill**; reserve them for PDF-only inputs (e.g. some exhibits or prospectuses).
- **Tradeoff:** CRF gives ~0.98 F1 on CPU with no API cost — the best accuracy-per-dollar. BERT adds a fraction of a point for a GPU dependency. Both need training data (the NTU annotated set exists). Neither *automatically* adapts to brand-new item types without retraining — that's where LLMs earn their place.

### A.5 LLM-based extraction (chunking, structured output, hallucination, cost)

LLMs are flexible (adapt to new items via a prompt edit) but bring the long-document and hallucination problems. The winning pattern is **index-don't-generate**.

- **LIB (Line-ID-Based) prompting — GPT4ItemSeg** (Lu et al. 2025): prepend an integer **line-ID** to each line; ask the model to output **only the START line-ID per item**; reconstruct each item's text from the original lines by line-ID. This **defeats hallucination** (the model never emits document text, only indices) and **defeats the context limit** (truncate each line to its first *L* words for the prompt). An output-parser **rejects and reruns** if line-IDs are inconsistent (non-monotonic, missing). **5 few-shot examples optimal** (accuracy plateaus after). Adapts to Item 1C (2023 cyber) via prompt edit alone.
- **LumberChunker** (Duarte et al., EMNLP 2024 Findings, arXiv 2406.17526): iteratively prompt an LLM to find the content-shift point in a sliding group of passages (+7.37% DCG@20 retrieval). Designed for **narrative RAG chunking**, not labeled-item filings — relevant as a technique, not a drop-in.
- **Long-doc LLM failure modes to instrument against:** *lost-in-the-middle* attention dilution; **tables split** so header rows lose their numeric labels; **clauses split across chunks** → partial-context reasoning; **hallucinated boundaries** whenever text is generated rather than indexed.
- **Mitigations that work:** (a) **index, don't generate** (LIB line-IDs) — biggest single win; (b) **constrained decoding** (XGrammar arXiv 2411.15100, Outlines, llguidance) to force in-range line-IDs / valid JSON by logit-masking — *guarantees well-formedness, NOT correctness*; (c) **round-trip reconstruction** check (see B.2); (d) **structural invariants** (see B.1).
- **Cost/tradeoff:** full-LLM segmentation is unnecessary for accuracy (CRF already ≈0.98) and is the most expensive + highest-variance option. Its real value is **adaptability** (new items, weird formats) and **boundary disambiguation on the hard minority**. So spend LLM tokens *only* where cheaper layers disagree or abstain.

### A.6 Recommended robust architecture

```
raw filing (SGML / HTML / iXBRL)
   └─ normalization layer  → consistent line-indexed internal form
        └─ Layer 0: regex anchors + TOC parse        (≈95% of filings, ~free)
        └─ Layer 1: CRF line-labeling (CPU, F1≈0.98) (format-variance robustness)
        └─ Layer 2: LLM-LIB (index-don't-generate)   (ambiguous minority + new items)
   └─ consensus / disagreement detection  → per-item confidence
   └─ validation harness (Section B)       → invariants + round-trip + XBRL + judge
```

The recurring lesson across every source: **naive parsers fail *silently* on legacy edge cases. Silent failure is THE risk to instrument** — which is why (B) is the hard, decisive part of the assignment.

---

## (B) Evaluating Extraction Quality WITHOUT Public Ground Truth

No public per-item gold labels exist for arbitrary filings (the NTU set covers 3,737 filings FY2001–2019, not your stream). The strategy: **stack independent, cheap, mechanically-checkable validators**, each catching a different error class, then escalate uncertain filings to human review. Below, ordered roughly by strength/cost.

### B.1 Structural invariants (cheapest, catches gross errors)

Mechanical checks on the segmentation output that must hold for any correct parse:

1. **Canonical order:** extracted items appear in the canonical sequence (1, 1A, 1B, 1C, 2, 3, 4, 5, …, 16). A non-monotonic ordering ⇒ likely mis-boundary. *(Caveat: rare legitimate exceptions exist — see B.7 hard cases — so flag, don't hard-fail.)*
2. **Presence & multiplicity:** each *expected* item present **exactly once** (account for filing-year schema: 1C only from 2023; some items legitimately "Not applicable" / incorporated by reference). Duplicate item ⇒ split error; missing required item ⇒ merge error.
3. **Non-overlap:** item char-ranges are **pairwise disjoint**. Overlap ⇒ a boundary is wrong.
4. **Full coverage:** the union of item ranges + inter-item gaps covers the whole body **with no dropped characters**. Track *unassigned* text; a large unassigned span ⇒ a missed boundary.
5. **Monotonic line IDs:** if using LIB, start-line-IDs strictly increase; the output-parser already enforces this and reruns on violation.

**Metrics:** % filings passing all invariants; per-invariant failure rate; distribution of unassigned-character fraction (should be ~0). These are *necessary, not sufficient* — they catch structural breakage but not a perfectly-shaped-but-mislabeled parse.

### B.2 Round-trip / reconstruction checks (lossless guarantee for completeness)

**Principle:** input → extract → reconstruct input; compare. Heritage: back-translation / cycle consistency; round-trip consistency correlates with extraction accuracy.

- **The decisive property:** when extraction is **indexing** (output = pointers into the source, item text reassembled from original bytes), reconstruction must equal the original **byte-for-byte** (modulo defined inter-item whitespace). This gives a **lossless guarantee** — round-trip catches *dropped, duplicated, or reordered* content **with certainty**. This is exactly why the LIB / line-ID design is so strong: completeness becomes provable, not estimated.
- **Critical caveat (do not over-claim):** round-trip does **NOT** catch **wrong-label** errors — *right text under the wrong item number*. Reconstruction is perfect even when Item 7 content is labeled Item 8. So **pair round-trip (completeness) with an independent correctness check** (B.3–B.5).
- **Metric:** exact-match reconstruction rate (target 100% for indexing extractors); for generative extractors, normalized edit distance / character-overlap between reconstruction and source (any gap = lost or hallucinated text).

### B.3 Cross-validation between two independent extractors (agreement)

Run a **rule-based** extractor (regex/edgartools) and an **LLM** extractor independently; measure agreement. **Disagreement is a free, label-free data-quality signal.**

- **Boundary agreement metrics:** for each item, compare start/end offsets. Report **exact-boundary match rate**, **boundary offset distribution** (median chars apart), and **Jaccard/IoU of character ranges** per item. Aggregate: % filings where all item boundaries agree within ε.
- **Decision rule:** agree ⇒ high confidence, auto-accept; disagree ⇒ low confidence, route to LLM-LIB tie-break and/or human spot-check. This is the practical realization of "ensemble/consensus across regex | CRF | LLM ⇒ low-confidence flag."
- **Why two genuinely-independent methods:** they fail on *different* inputs (regex on weird headers; LLM on long/ambiguous context). Agreement is therefore meaningful evidence; **a self-consistency check using the same formula as production would pass even when both are wrong** — avoid that trap (use *independent* methods, not the same method twice).

### B.4 XBRL / companyfacts cross-modality check (the only true external oracle)

iXBRL embeds **machine-readable financial facts** inside the human-readable HTML. SEC's `data.sec.gov/api/xbrl/companyfacts/CIK{...}.json` returns exact numeric facts (revenue, assets, etc.) with their tags.

- **The check:** every financial fact from companyfacts **must fall inside the Item 8 (Financial Statements) boundary** (and MD&A figures inside Item 7). If a tagged revenue number lands outside your Item 8 range, the **Item 8 boundary is wrong** — verified against an *independent modality* at **zero labeling cost**. This is the closest thing to true ground truth available for arbitrary filings.
- **Strength/limits:** strong and external, but only covers the **financially-tagged items** (≈ Item 7/8 region), not the narrative items (1A Risk Factors, etc.). XBRL also has its own calculation-relationship validation (a processor checks a tagged fact = sum of its children; SEC runs XULE/DQC rules) — orthogonal evidence the facts themselves are coherent.
- **Related benchmarks** showing XBRL is a *hard, discriminating* oracle: **FiNER-139** (Loughran-McDonald-adjacent fin-NLP; 139 XBRL tags, SEC-BERT ≈82 micro-F1), **FNXL** (2,794 tags), **FinTagging** (best LLMs ≤17% on concept-linking) — XBRL grounding is non-trivial, so passing it is meaningful.

### B.5 LLM-as-judge with calibration caveats

Use an LLM to judge *correctness* (does this text body match its item label?), **but only on the cheap, decisive signal: the boundary/title lines**, not whole-item re-reading.

- **Targeted use:** feed the judge the item header + first/last few lines and ask "is this the start of Item 7 MD&A?" Catches **wrong-label** errors that round-trip (B.2) structurally cannot.
- **Calibration caveats (must instrument):** LLM judges are **miscalibrated and biased** (self-preference, position bias, verbosity bias); a confident "looks right" is not evidence. Mitigations: use a *different* model family than the extractor (reduce correlated error); ask for a discrete verdict + brief justification (not a vibes score); calibrate the judge against the small gold set (B.6) and report its own precision/recall before trusting it; treat low-confidence judge outputs as *route-to-human*, not *auto-reject*.
- **Don't let the judge be the sole gate** — it's one independent vote among invariants, round-trip, cross-extractor, and XBRL.

### B.6 Build a small hand-labeled gold set (anchors everything else)

You cannot escape labeling *some* data — but you need only a **small, well-chosen** set to (a) measure the pipeline and (b) calibrate the judge.

- **Composition:** ~50–200 filings, **stratified** by era (pre-2001 SGML vs HTML vs recent iXBRL), filer size, and *known-hard cases* (B.7). Over-sample hard cases — random sampling wastes labels on easy filings.
- **Reuse existing labels:** the **NTU itemseg dataset (3,737 annotated 10-Ks FY2001–2019)** is a ready-made gold set for the years it covers — use it directly for model/metric validation; hand-label only what it doesn't cover (very recent filings, Item 1C, your specific filers).
- **Metrics on the gold set:** per-item **boundary F1** (token/char-level), **exact item-match accuracy**, **macro-F1** (weights rare items — don't let Item 1/7 dominate). Mirror the literature so numbers are comparable: NTU core-item macro-F1 reference points are **regex ≈0.905, CRF ≈0.978–0.982, BERT ≈0.983, GPT-LIB ≈0.955–0.957.**

### B.7 Spot-check sampling + named hard cases

- **Stratified spot-check:** continuously sample a small % of *production* output for human review, **stratified by confidence band** — oversample the low-confidence / high-disagreement filings (B.3) where errors concentrate. This estimates real-world precision without labeling everything.
- **Named hard filings to keep as permanent regression cases** (all published segmenters miss these):
  - **Allstates WorldCargo 2002 10-K** — labels "Controls and Procedures" as **Item 14** instead of 9A.
  - **Hub International 2006** — Item 7A market risk **nested inside Part II of Item 7**.
  - **Alternative Asset Management Acquisition 2007** — part of Item 8 placed **after Item 15** (out of canonical order — breaks the B.1 order invariant *legitimately*, which is why order is a flag not a hard-fail).
- These force the harness to distinguish *real* anomalies from *parser bugs*.

### B.8 Validate-the-validator (give the harness its own ground-truth-free recall)

The checks themselves can be silently broken. **Inject synthetic perturbations with KNOWN answers** into correct filings and confirm each check **fires**:

- delete an item → presence invariant must fire;
- swap two boundaries → order + XBRL checks must fire;
- duplicate a paragraph → round-trip must fire;
- mislabel a header → LLM-judge / cross-extractor must fire.

This yields a **sensitivity/recall measure for the harness itself** with no external labels. It is the single most under-used technique and directly attacks the assignment's core risk: a validator that passes everything because it's broken.

### B.9 Confidence scoring & silent-failure detection (putting it together)

Combine the signals into a **per-item confidence score** and an **abstention policy**:

- **Signals:** all-invariants-pass (B.1), round-trip exact (B.2), cross-extractor agreement (B.3), XBRL-in-bounds (B.4), judge verdict (B.5).
- **Selective prediction / conformal abstention** (survey: Campos et al., TACL 2024, arXiv 2405.01976; NER conformal arXiv 2601.16999; pipeline-aware PASC arXiv 2605.18812): produce a **prediction set** of plausible boundaries at a calibrated risk level; when the set is large / signals disagree, **abstain and flag for review**. Report a **risk-coverage curve** (accuracy on the auto-accepted fraction vs how much you abstain).
- **Silent-failure detection = the whole point:** the dangerous case is *confident wrong* output. Note that **SelfCheckGPT-style self-consistency CANNOT catch confident systematic errors** (all samples agree but are wrong — exactly a deterministic mis-segmenter's failure). Only **independent oracles** (XBRL B.4, cross-extractor B.3, gold set B.6) catch those. Design the harness so that *no single point of agreement can hide a systematic error.*

### B.10 Evaluation summary table

| Technique | Catches | Misses | Cost | External oracle? |
|---|---|---|---|---|
| Structural invariants (B.1) | order/dup/overlap/coverage breaks | correct-shape mislabels | ~0 | No |
| Round-trip reconstruction (B.2) | dropped/dup/reordered text (provably, if indexing) | wrong-label errors | ~0 | No (self) |
| Cross-extractor agreement (B.3) | boundary disagreement | shared blind spots | low | No (2 methods) |
| XBRL companyfacts (B.4) | wrong Item 7/8 boundary | narrative items | low | **Yes** |
| LLM-judge on boundaries (B.5) | wrong-label errors | miscalibration/bias | medium | No |
| Gold set (B.6) | true F1/accuracy | only covered filings | high (labeling) | **Yes** |
| Spot-check (B.7) | real-world precision | unsampled errors | medium | **Yes (human)** |
| Validate-the-validator (B.8) | broken checks | unmodeled perturbations | low | synthetic |

**Recommended minimal harness for an A-grade answer:** invariants + round-trip (free completeness) **paired with** XBRL-in-bounds + cross-extractor agreement (independent correctness) + a small stratified gold set to calibrate, all wrapped in validate-the-validator. That stack covers both error classes (completeness *and* label correctness) with at most one small labeling investment.

---

## Risks / Caveats

- **Self-consistency trap:** never validate with the same formula/method as production — it passes when both are wrong. Use *independent* modalities (this is in the user's global engineering rules and is the #1 eval pitfall here).
- **Round-trip ≠ correctness:** it guarantees completeness, not labels. Easy to over-claim.
- **LLM-judge is not ground truth:** miscalibrated; one vote, not the verdict.
- **Order invariant has legitimate exceptions** (out-of-order Item 8) — flag, don't hard-fail.
- **XBRL only covers tagged (financial) items** — narrative items (1A, etc.) have no equivalent oracle; rely on cross-extractor + spot-check there.
- **Pre-2001 SGML filings** have no helpful tags — normalization layer is mandatory before any of this works.
- A few benchmark numbers (FinTOC ISPRAS, exact CRF figure) are **snippet-level**, not re-read from the source tables — verify against the papers before quoting in a deliverable.

---

## Sources

**Segmentation (A):**
- Lu, Chien, Yen, Chen, "Utilizing PLMs and LLMs for 10-K Items Segmentation," 2025 — arXiv **2502.08875**; repo `github.com/hsinmin/itemseg`; dataset `im.ntu.edu.tw/~lu/data/itemseg/`. **[authoritative]**
- Koshorek et al., "Text Segmentation as a Supervised Learning Task," NAACL 2018 — arXiv **1803.09337**.
- Lukasik et al., "Text Segmentation by Cross Segment Attention," EMNLP 2020 — arXiv **2004.14535**.
- Hearst, "TextTiling," 1997.
- Duarte et al., "LumberChunker," EMNLP 2024 Findings — arXiv **2406.17526**.
- Loukas et al., "EDGAR-CORPUS," ECONLP@EMNLP 2021 — aclanthology 2021.econlp-1.2; EDGAR-CRAWLER (WWW 2025) `github.com/nlpaueb/edgar-crawler` (Item1+Item2 merge bug, issue #35).
- FinTOC shared task overview, FNP 2022 — aclanthology 2022.fnp-1.12 (ISPRAS 2022.fnp-1.13).
- Brown & Tucker (2011); Campbell et al. (2014) — MD&A regex-extraction precedents.
- OSS: `edgartools` (dgunning, MIT); `sec-parser` (alphanome-ai, MIT); `sec-api.io` (commercial).
- Document-parsing survey — arXiv **2410.21169**; LayoutLMv3 / Donut / DocFormer.

**Evaluation without ground truth (B):**
- Round-trip / cycle consistency; "knowledge restoration" verbalize-then-NLI — arXiv **2601.15037**.
- SelfCheckGPT (self-consistency, and its limit on systematic errors), Manakul et al., EMNLP 2023 — arXiv **2303.08896**.
- SummaC (NLI faithfulness matrix), Laban et al., TACL 2022 — arXiv **2111.09525**; QAGS (arXiv **2004.04228**); QuestEval (arXiv **2103.12693**); FactCC (arXiv **1910.12840**); AIS (arXiv **2112.12870**).
- Constrained decoding: XGrammar (arXiv **2411.15100**), Outlines, llguidance.
- Conformal/selective prediction: Campos et al. TACL 2024 (arXiv **2405.01976**); NER conformal (arXiv **2601.16999**); PASC pipeline-aware (arXiv **2605.18812**).
- XBRL-as-oracle: `data.sec.gov/api/xbrl/companyfacts`; FiNER-139 (aclanthology 2022.acl-long.303); FNXL (arXiv **2306.03723**); FinTagging (arXiv **2505.20650**).
- Quant motivation: Cohen, Malloy, Nguyen, "Lazy Prices," J. Finance 2020 (NBER w25084) — per-item YoY similarity ⇒ item segmentation is the upstream dependency.

**EDGAR access constraints:** 10 req/s hard limit (10-min IP ban if exceeded); `User-Agent` with name+email required; `data.sec.gov/api/xbrl/{companyfacts,companyconcept,frames}`; full-text search `efts.sec.gov` (electronic filings 2001+); bulk `submissions.zip` / `companyfacts.zip`.
