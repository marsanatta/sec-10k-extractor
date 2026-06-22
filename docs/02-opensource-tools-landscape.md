# Open-Source Tooling Landscape for SEC 10-K Item Extraction

**研究日期 (Research date):** 2026-06-22
**來源數量 (Sources):** 18 (repos, PyPI, docs, papers — all URLs cited inline)
**信心程度 (Confidence):** 8/10 — qualitative verdicts verified against primary repos/docs; star counts and commit dates are point-in-time snapshots (2026-06-22) and decay.

---

## TL;DR

The 10-K item-extraction landscape splits cleanly into three layers that **do not overlap**: (1) **downloaders** that fetch raw filings but do zero item parsing (`sec-edgar-downloader`, `secedgar`, `python-edgar`); (2) **structural parsers** that split a filing into Items 1–16 (`edgartools`, `edgar-crawler`, `sec-api.io`, `itemseg`); and (3) **semantic / ML tooling** that produces element trees or LLM-derived artifacts but **not** regulatory items out of the box (`sec-parser`, `financial-datasets`).

**Only four tools actually do Item-level segmentation**, and each has a disqualifying caveat for a production, commercially-usable, *self-verifying* pipeline:

- **edgartools** — best ergonomics + multi-strategy detection, MIT, but emits **no confidence signal** and no documented success rate.
- **edgar-crawler** — battle-tested regex over 90k filings, but **GPL-3.0** (copyleft, a real constraint for internal/commercial reuse) and has a known Item-merge bug.
- **itemseg** — the academic SOTA (F1 ≈ 0.98), but **CC BY-NC** (NonCommercial — license-blocked for commercial use) and needs a GPU for its best model.
- **sec-api.io** — broadest item coverage incl. amendments, but **paid / closed-source**, leaves HTML entities unescaped.

**The gap no tool fills:** none ships a *verification layer* (structural invariants, round-trip reconstruction, ensemble disagreement flags, XBRL boundary cross-check) or a per-item *confidence score*. That is precisely the differentiating work to build.

---

## Comparison Table

| Tool | Approach | Item-segmentation? | Maturity (as of 2026-06-22) | License | Key limitations | URL |
|---|---|---|---|---|---|---|
| **edgartools** (dgunning) | DOM + multi-strategy: TOC parse → header-pattern match → cross-reference-index detection; HTML→clean text/markdown; XBRL financials | **Yes** — `tenk["Item 1"]` bracket access; handles GE-style cross-ref layouts; resolves 10-Q Part I/II ambiguity | ~2.4k★, v5.38.0 (2026-06-21), ~3,970 commits, very active | **MIT** | No confidence signal / no published success rate; "remarkably diverse formats" still fail silently; item boundaries not validated | [github.com/dgunning/edgartools](https://github.com/dgunning/edgartools) · [edgartools.io](https://www.edgartools.io/edgartools-5/) |
| **edgar-crawler** (nlpaueb / lefterisloukas) | Regex anchor item→JSON; plaintext + HTML; toolkit behind EDGAR-CORPUS | **Yes** — splits 10-K/10-Q/8-K into item JSON sections | ~530★, ~95 commits, WWW 2025 paper | **GPL-3.0** (copyleft — constrains commercial reuse) | Known Item1/Item2 merge bug (issue #35); older 10-Qs may extract no items per part (falls back to whole-Part entries); regex-only ≈ 0.90 F1 ceiling | [github.com/nlpaueb/edgar-crawler](https://github.com/nlpaueb/edgar-crawler) |
| **itemseg** (hsinmin / NTU) | ML: line-by-line Sentence-BERT embeddings → Bi-LSTM BIO labeling (BERT4ItemSeg); CRF baseline (CPU); GPT4ItemSeg via LIB line-ID prompting | **Yes — best accuracy** (macro-F1 ≈ 0.9826 core items 1/1A/3/7; CRF ≈ 0.9818 CPU-only) | ~0★ (new), pip-installable `itemseg`, weights via `--get_resource`; arXiv 2502.08875 | **CC BY-NC** (NonCommercial — license-blocked for commercial use) | BERT model needs GPU; NonCommercial license; research-grade CLI; GPT path incurs API cost | [github.com/hsinmin/itemseg](https://github.com/hsinmin/itemseg) · [arxiv.org/abs/2502.08875](https://arxiv.org/pdf/2502.08875) |
| **sec-api.io** (Extractor API) | Hosted regex/proprietary item splitter; supports amendments (10-K/A, 10KSB) since 1994 | **Yes — broadest item coverage** (1, 1A, 1B, 1C, 2–8, 7A … 15) | Commercial SaaS; Python SDK `sec-api-python` ~309★, MIT *client* | **Paid / closed-source** (SDK MIT, service requires key) | Leaves HTML entities unescaped (`&#160;`); marks tables `##TABLE_START/##TABLE_END`; pre-SOX filings + scattered GE/Citigroup layouts unreliable; recent filings return "processing"; ongoing cost | [sec-api.io/docs](https://sec-api.io/docs/sec-filings-item-extraction-api) · [github.com/janlukasschroeder/sec-api-python](https://github.com/janlukasschroeder/sec-api-python) |
| **sec-parser** (Alphanome-AI) | DOM→semantic element TREE (`TopSectionTitle`, `TitleElement`, `TableElement`); HTML-only | **No (partial)** — emits semantic elements, NOT regulatory items; you must group elements into Items yourself | ~287★, 656 commits, **beta** | **MIT** | Not item-level; HTML-only; beta stability; no item boundaries delivered | [github.com/alphanome-ai/sec-parser](https://github.com/alphanome-ai/sec-parser) |
| **financial-datasets** (virattt) | LLM (GPT-4 Turbo) generates Q&A pairs from filing text; accepts `item_names=["Item 1","Item 7"]` | **No** — *consumes* item names but relies on upstream segmentation; purpose is synthetic Q&A, not segmentation | ~430★, v0.1.16 (2024-05-22), stale | **MIT** | Not a segmenter; LLM hallucination risk; API cost; no table/numeric handling | [github.com/virattt/financial-datasets](https://github.com/virattt/financial-datasets) |
| **sec-edgar-downloader** (jadchaar) | HTTP retrieval by ticker/CIK | **No** — download only | ~705★, v5.1.0 (2026-02-02), maintained | **MIT** | Pure downloader; no parsing | [github.com/jadchaar/sec-edgar-downloader](https://github.com/jadchaar/sec-edgar-downloader) |
| **secedgar** (sec-edgar org) | Bulk retrieval of company filings/forms | **No** — download only | ~1.4k★, v0.6.0 (2025-05-09) | **Apache-2.0** | Pure downloader; no item parsing | [github.com/sec-edgar/sec-edgar](https://github.com/sec-edgar/sec-edgar) |
| **python-edgar** (edouardswiac) | Builds master index from quarterly index files (metadata only) | **No** — index/metadata only, no filing content | ~354★, last commit 2021-02-05 (dormant) | **MIT** | Index only; dormant | [github.com/edouardswiac/python-edgar](https://github.com/edouardswiac/python-edgar) |
| **EDGAR-CORPUS** (dataset) | Pre-split item JSON for ~90k 10-Ks 1993–2020 (produced by edgar-crawler) | **Pre-segmented data**, no gold boundary labels | ECONLP@EMNLP 2021; HF `eloukas/edgar-corpus`; 6B+ tokens | Dataset (CC; check HF card) | Silver-quality (regex-split, inherits crawler bugs); no manual ground truth | [huggingface.co/datasets/eloukas/edgar-corpus](https://huggingface.co/datasets/eloukas/edgar-corpus) · [arxiv.org/abs/2109.14394](https://arxiv.org/abs/2109.14394) |

### Honorable mentions (found during search, not core)
- **edgar_analytics** (zoharbabin) — retrieves + computes GAAP/IFRS metrics from XBRL; financial-statement analytics, **not** item segmentation. [github.com/zoharbabin/edgar_analytics](https://github.com/zoharbabin/edgar_analytics)
- **ETL-SEC-EDGAR-10-k-Filings** (pChitral) — ETL focused only on the **MD&A (Item 7)** section across 10k companies; narrow, single-item. [github.com/pChitral/ETL-SEC-EDGAR-10-k-Filings](https://github.com/pChitral/ETL-SEC-EDGAR-10-k-Filings)
- **secfsdstools** — SEC DERA financial-statement datasets (XBRL), not item text. [pypi.org/project/secfsdstools](https://pypi.org/project/secfsdstools/)

---

## Critical Analysis: Where Each Item-Segmenter Fails

All four segmenters share one root weakness — **they fail silently on legacy / non-standard filings and emit no signal that they did so.** Known hard cases (from the Lu et al. 2025 paper and crawler issues) that defeat regex/header approaches:

- **Cross-reference / incorporation-by-reference layouts** (GE, Citigroup) where item content is scattered or pulled from exhibits — edgartools explicitly targets this; regex tools (edgar-crawler, sec-api.io) degrade here.
- **Mislabeled items** (e.g. Allstates WorldCargo 2002 labels "Controls and Procedures" as Item 14, not 9A).
- **Nested items** (Hub International 2006 nests Item 7A market-risk inside Item 7).
- **Out-of-order content** (part of Item 8 placed *after* Item 15).
- **Pre-SOX (pre-2002) filings** lacking standardized structure — sec-api.io documents this explicitly.
- **edgar-crawler Item1/Item2 merge** (issue #35) and missing-item fallback to whole-Part on older 10-Qs.

**Accuracy ceiling by approach** (Lu et al. 2025, arXiv 2502.08875, macro-F1 on core items): rule/regex **0.9048** < GPT4ItemSeg (LIB) **0.9552** < CRF **0.9818** ≈ BERT4ItemSeg **0.9826**. The lesson: **pure regex caps near 0.90**; the jump to 0.98 requires sequence labeling (CRF is CPU-only and nearly ties BERT).

---

## What to Reuse vs Build

### Reuse (don't reinvent)

1. **edgartools as the default ingestion + first-pass segmenter.** MIT, actively maintained (v5.38.0, 2026-06-21), best ergonomics (`filing.obj()`, `tenk["Item 1"]`), handles XBRL, HTML→clean-text/markdown, and the GE cross-reference case. Use it for the ~90–95% of filings that parse cleanly. This is the single highest-leverage reuse.
2. **EDGAR access plumbing via edgartools / sec-edgar-downloader** (both MIT) — no reason to hand-roll the 10 req/s rate limit, User-Agent header, and master-index logic.
3. **EDGAR-CORPUS (`eloukas/edgar-corpus`) as a silver baseline + bulk test corpus** — 90k pre-split filings to diff your segmenter against at scale (knowing it inherits regex bugs, so treat disagreements as candidate hard-cases, not gold).
4. **itemseg's CRF model *as an independent second opinion*** — CPU-only, F1 ≈ 0.98, ideal for an ensemble vote. **BUT** its **CC BY-NC license blocks commercial use** — verify your use case is non-commercial, or reimplement the CRF approach (the method is published; the trained weights are the licensed artifact). Do **not** ship the weights in a commercial product.

### Build (no tool fills these)

1. **A verification / confidence layer — the core differentiator.** No tool emits a confidence signal. Build:
   - **Structural invariants:** all expected items present? monotonic line order? char-ranges non-overlapping and covering the doc?
   - **Round-trip reconstruction:** reassembled items == original text (no lost/duplicated spans).
   - **Ensemble disagreement flag:** run edgartools + a regex/CRF pass; where they disagree on a boundary → emit a low-confidence flag instead of silently picking one.
   - **XBRL cross-check:** `data.sec.gov/api/xbrl/companyfacts` numeric facts MUST fall inside the detected **Item 8** boundary — a free, label-free independent boundary check.
2. **A normalization layer** that enforces a consistent item schema across SGML/HTML/XBRL eras so downstream consumers see one shape regardless of filing vintage.
3. **An LLM-LIB escalation path** (line-ID-based prompting, à la GPT4ItemSeg) applied *only* to the ambiguous-boundary minority flagged by the verification layer — keeps API cost layered and bounded. LIB indexes line-IDs rather than generating text, which defeats hallucination and the 512-token limit.

### License decision summary (critical for a commercial/internal pipeline)
- **Safe to embed:** edgartools (MIT), sec-edgar-downloader (MIT), secedgar (Apache-2.0).
- **Copyleft — avoid embedding, OK to run as a separate tool:** edgar-crawler (**GPL-3.0**).
- **NonCommercial — do NOT use commercially:** itemseg weights (**CC BY-NC**) — reimplement the method instead if commercial.
- **Paid / closed:** sec-api.io — fine as a benchmark oracle, not as a free dependency.

---

## Sources

- edgartools — https://github.com/dgunning/edgartools , https://www.edgartools.io/edgartools-5/ , https://pypi.org/project/edgartools/
- sec-parser — https://github.com/alphanome-ai/sec-parser
- edgar-crawler — https://github.com/nlpaueb/edgar-crawler
- itemseg + paper — https://github.com/hsinmin/itemseg , https://arxiv.org/pdf/2502.08875
- sec-api.io — https://sec-api.io/docs/sec-filings-item-extraction-api , https://github.com/janlukasschroeder/sec-api-python
- financial-datasets — https://github.com/virattt/financial-datasets
- sec-edgar-downloader — https://github.com/jadchaar/sec-edgar-downloader
- secedgar — https://github.com/sec-edgar/sec-edgar
- python-edgar — https://github.com/edouardswiac/python-edgar
- EDGAR-CORPUS — https://huggingface.co/datasets/eloukas/edgar-corpus , https://arxiv.org/abs/2109.14394
- edgar_analytics — https://github.com/zoharbabin/edgar_analytics
- ETL-SEC-EDGAR-10-k-Filings — https://github.com/pChitral/ETL-SEC-EDGAR-10-k-Filings
- secfsdstools — https://pypi.org/project/secfsdstools/
