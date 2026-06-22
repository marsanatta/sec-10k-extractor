# 05 — Cost, Latency & Scalability

研究日期: 2026-06-22
來源數量: 11 primary/secondary sources
信心程度: High on prices & EDGAR limits (current official sources); Medium on per-filing token math (derived from word-count studies + the ~1 token ≈ 0.75 words rule, not a measured token census of the primary HTML document).

---

## TL;DR

- A **median 10-K is ~49,000 words (2013) / ~42,000 average (2017)** of clean body text ≈ **~55–65k tokens**; the distribution is heavy-tailed — small filings ~25k words (~33k tok), large banks/insurers/conglomerates run 100k–200k+ words (~130k–270k tok). ([CLS Blue Sky / Columbia Law](https://clsbluesky.law.columbia.edu/2016/05/05/the-ever-expanding-10-k-why-are-10-ks-getting-so-much-longer-and-does-it-matter/), [data-viz study, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0165410123000551))
- **Full-document-through-LLM costs ~$0.08 (Haiku) / ~$0.24 (Sonnet) / ~$0.40 (Opus) per median filing**, and 2–4× that on the long tail. At 8,000 filings that is **$640 / $1,920 / $3,200**; at 90k it is **$7,200 / $21,600 / $36,000**. This is the strategy to avoid as the default.
- The **recommended hybrid (regex + CRF on 100%, LLM only on the ~10–15% ambiguous-boundary minority, scoped to ~10% of the document) blends to ~$0.005–$0.01 per filing** — a **25–50× reduction** vs full-Sonnet, with accuracy that matches or beats full-doc LLM on the items that matter.
- **Pure rule/regex + CRF is effectively $0 inference** (CPU-only, CRF macro-F1 ~0.98 on core items) and runs in **tens of milliseconds to low single-digit seconds per filing**.
- **Ingestion ceiling is fixed by SEC: 10 requests/second per IP**, descriptive User-Agent required, 10-minute ban on breach. That caps a naive crawl at **~864k requests/day**; the full ~90k EDGAR-CORPUS is fetchable in **~2.5–5 hours of wall-clock at the limit** (more with retries), or instantly via the bulk ZIPs. **Filings are immutable → cache forever.**

---

## Research Plan (sub-questions)

1. How large is a typical 10-K (pages, words, tokens) and what is the small-vs-huge distribution?
2. What does each of the three extraction strategies cost per filing in LLM tokens?
3. What are current per-million-token prices across a cheap / mid / frontier tier?
4. What is the regex/CRF CPU cost and the EDGAR ingestion/throughput ceiling?
5. How does this scale: 1 filing, ~8,000 annual 10-Ks, full ~90k corpus? Storage footprint?

---

## 1. Size of a Typical 10-K Primary Document

### Words and pages (sourced)

| Metric | Value | Source |
|---|---|---|
| Median 10-K, 1996 | ~23,000 words | [CLS Blue Sky Blog (Columbia Law), 2016](https://clsbluesky.law.columbia.edu/2016/05/05/the-ever-expanding-10-k-why-are-10-ks-getting-so-much-longer-and-does-it-matter/) |
| Median 10-K, 2013 | **>49,000 words** | same |
| Average 10-K, ~2017 | **~42,000 words** (≈+200% since 1997) | [Data visualization in 10-K filings, ScienceDirect 2023](https://www.sciencedirect.com/science/article/abs/pii/S0165410123000551) |
| Typical page count | **80–200 pages** (large multinationals 200+, small filers ~100) | [AAA Accounting Horizons "Why are 10-K Filings So Long?"](https://publications.aaahq.org/accounting-horizons/article/30/1/1/2275/) |
| Verbatim-repeated text (median, 2013) | ~3,300 words | CLS Blue Sky Blog |
| Corpus scale | **>90,000 10-Ks, 1993–2020, "billions of tokens"** | [EDGAR-CORPUS, Loukas et al. ECONLP@EMNLP 2021](https://aclanthology.org/2021.econlp-1.2/) |

Note the median has kept rising since 2013 (post-2013 cyber/ESG/risk-factor disclosure), so a 2020s median body of **~45–55k words** is a reasonable planning figure.

### Words → tokens

Using the standard heuristic **1 token ≈ 0.75 English words** (i.e. tokens ≈ words × 1.333):

| Filing class | Words (body text) | ≈ Tokens (clean text) |
|---|---|---|
| Small filer (10th–25th pctile) | ~25,000 | **~33,000** |
| **Median filing (planning figure)** | **~49,000** | **~65,000** |
| Large filer (75th–90th pctile) | ~80,000 | ~107,000 |
| Huge filing — big bank / insurer / GE-style conglomerate | 150,000–200,000+ | **~200,000–270,000+** |

### Critical caveat: HTML markup inflates the raw document

The numbers above are **clean extracted body text**. The actual *primary HTML document* on EDGAR carries tags, inline styles, and large XBRL/iXBRL tables. **Raw HTML is commonly 2–4× the clean-text token count.** This matters enormously for Strategy (a): if you feed raw HTML you pay for the markup; if you feed cleaned text you cut input tokens ~50–75% before any other optimization. **Always strip to clean text/markdown before any LLM call.** (edgartools and edgar-crawler both emit cleaned text — see [doc 02](02-opensource-tools-landscape.md).)

---

## 2. LLM Cost Per Filing — Three Strategies

### Current representative prices (per million tokens, June 2026)

| Tier | Model (example) | Input $/Mtok | Output $/Mtok | Source |
|---|---|---|---|---|
| Cheap / small | Claude Haiku 4.5 | **$1.00** | **$5.00** | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Mid | Claude Sonnet 4.6 | **$3.00** | **$15.00** | same |
| Frontier | Claude Opus 4.8 | **$5.00** | **$25.00** | same |

Cost levers (official, stack-able): **Batch API −50%** on input+output (async, ≤24h); **prompt-cache reads = 10% of base input** (90% off); combined up to **~95% off**. Output is 5× input across all tiers. ([Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing); [Batch API](https://pristren.com/blog/anthropic-batch-api-guide/))

> Model selection (we lean Claude tiers) is finalized separately. The per-filing **token math** below is vendor-agnostic — swap any provider's $/Mtok into the same formulas and the *ordering* of the three strategies is unchanged because it is driven by **token volume**, not price.

### (a) Full-document-through-LLM

Feed the entire cleaned 10-K and ask for all 16 item boundaries. Assume **65k input tokens (median)** + **~3k output tokens** (JSON of item labels + char offsets; small because we index, not regenerate).

Cost = input_tok × in_price + output_tok × out_price.

| Model | Input cost (65k) | Output cost (3k) | **Per median filing** | **Huge filing (200k in / 5k out)** |
|---|---|---|---|---|
| Haiku 4.5 | $0.065 | $0.015 | **$0.080** | $0.225 |
| Sonnet 4.6 | $0.195 | $0.045 | **$0.240** | $0.675 |
| Opus 4.8 | $0.325 | $0.075 | **$0.400** | $1.125 |

**Why this is expensive and wasteful:**
- You pay for **100% of the document** when only the **~16 item-boundary regions** carry the labeling signal — the bulk of MD&A prose and the financial statements are paid for but contribute nothing to *where the boundaries are*.
- The long tail dominates total spend: a few hundred 100k–270k-token mega-filings cost 3–4× the median each.
- **lost-in-the-middle** degrades long-context boundary accuracy, so you pay frontier prices for *worse* boundary precision than a CPU CRF (see [doc 03](03-sota-segmentation-and-eval.md): GPT4ItemSeg F1 0.957 < CRF 0.982).
- Even with Batch −50%, median Sonnet is $0.12/filing → $10,800 for 90k. Still 20–50× the hybrid.

### (b) Escalation-only LLM (recommended hybrid)

Regex/CRF segments **100%** of filings. The LLM is invoked **only** when the cheap path emits a low-confidence flag (missing item, overlapping/ non-monotonic boundaries, round-trip mismatch, or ensemble disagreement — see [doc 06](06-confidence-and-silent-failure.md)). When invoked, it sees **only the ambiguous window(s)** (~the candidate boundary ± a few hundred lines), not the whole document, using **LIB line-ID prompting** (index lines, never regenerate text — defeats hallucination + the 512-token ceiling; see [doc 03](03-sota-segmentation-and-eval.md)).

Assume an escalated call touches **~7k input tokens** (≈10% of a median doc) + **~1k output** (line-IDs only), and that **~15% of filings escalate** (legacy SGML, cross-reference-index filings, exotic item ordering).

**Per escalated filing:**

| Model | Input (7k) | Output (1k) | **Per escalated call** |
|---|---|---|---|
| Haiku 4.5 | $0.007 | $0.005 | **$0.012** |
| Sonnet 4.6 | $0.021 | $0.015 | **$0.036** |
| Opus 4.8 | $0.035 | $0.025 | **$0.060** |

**Blended across ALL filings (15% escalation rate):**

| Model on the escalated 15% | **Blended $/filing** |
|---|---|
| Haiku 4.5 | **$0.0018** |
| Sonnet 4.6 | **$0.0054** |
| Opus 4.8 | **$0.0090** |

The CPU CRF/regex on the other 85% (and the cheap pass on all 100%) adds effectively $0 inference. With Batch −50% on the escalated calls, blended Sonnet drops to **~$0.0027/filing**.

### (c) Pure rule/regex + CRF (CPU-only)

No API calls. CRF (linear-chain over line-level features) and regex run on CPU. Inference cost = **~$0** (only the amortized cost of CPU seconds; see §3). Accuracy: **CRF macro-F1 ~0.982** on core items (1/1A/3/7), essentially tying BERT and far above rule-only regex (0.905). ([Lu et al. 2025, arXiv 2502.08875](https://arxiv.org/abs/2502.08875))

Limitation: no adaptability to *brand-new* item types (e.g. Item 1C Cybersecurity, added 2023) without retraining/rule edits — which is exactly the gap the escalation LLM in (b) fills cheaply.

### Per-strategy summary (median filing, mid-tier Sonnet)

| Strategy | LLM scope | $/median filing | $/8,000 filings | $/90,000 filings | Boundary accuracy |
|---|---|---|---|---|---|
| (a) Full-doc LLM | 100% of every doc | **$0.240** | $1,920 | $21,600 | ~0.957 F1 (worse, lost-in-middle) |
| (b) **Hybrid escalation** | ~10% of doc, ~15% of filings | **~$0.0054** | **~$43** | **~$486** | ≥0.982 (CRF) + LLM rescue on hard cases |
| (c) Regex + CRF | none | **~$0** | ~$0 | ~$0 | ~0.982 F1 (no new-item adaptability) |

**Hybrid is ~44× cheaper than full-Sonnet and recovers the hard cases that pure CRF silently misses.**

---

## 3. Throughput & Latency

### Regex / CRF per-filing CPU time

- Regex item-splitting + clean-text extraction: **single-digit to low tens of milliseconds** per filing (string scan over ~300KB–2MB of text).
- CRF decoding (Viterbi over line-level feature vectors, a few thousand lines/filing): **typically <1 s/filing on one CPU core**; Sentence-BERT-embedding variants add GPU/CPU embedding time (still sub-second to low-seconds on CPU). The CRF path is the high-ROI core precisely because it is CPU-cheap and parallelizes trivially across cores.
- Net: a single modern multicore box processes **thousands of filings/minute** on the CPU path — the LLM escalation calls and the EDGAR fetch are the only real bottlenecks, not the segmentation compute.

### EDGAR ingestion ceiling (the real throttle)

SEC fair-access policy (in force since 2021-07-27):

- **Hard limit: 10 requests/second per requester**, regardless of how many machines you spread across. ([SEC: new rate control limits](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits); [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data))
- **Descriptive `User-Agent` header required** (name + email), else requests are refused.
- **Breach → 10-minute IP ban**, extended if you keep hammering during the timeout.

Fetch math at the 10 req/s ceiling:

| Target | Requests (≈1–2 per filing: index + doc) | Time at 10 req/s |
|---|---|---|
| 1 filing | 1–2 | <1 s |
| 8,000 annual 10-Ks | ~12,000 | **~20 minutes** |
| 90,000 corpus | ~135,000 | **~3.75 hours** |
| Theoretical daily cap | 864,000 req/day | — |

Add ~20–40% for retries/backoff and metadata lookups. In practice the time roughly doubles, so plan **~40 min for 8k** and **~7–8 h for 90k** via the live API.

### Bulk download bypasses the per-request limit entirely

For corpus-scale jobs, **do not crawl** — pull the SEC bulk archives in a handful of requests:
- `submissions.zip` (all filing metadata) and `companyfacts.zip` (all XBRL facts) from `data.sec.gov`.
- Per-quarter master index `sec.gov/Archives/edgar/full-index/{YYYY}/QTR{n}/`.
- EDGAR-CORPUS itself is downloadable pre-split from HuggingFace (`eloukas/edgar-corpus`), skipping fetch + segmentation for historical data.

### Parallelism, batching, and caching

- **Fetch parallelism is capped at 10 req/s total** — adding workers does not raise the ceiling; it only helps you saturate it. Use a single shared token-bucket rate limiter across all workers.
- **LLM escalation calls parallelize freely** (provider-side concurrency), and **Batch API (−50%)** is ideal for corpus jobs where 24h latency is fine.
- **Filings are immutable once accepted** — an accession number's content never changes. → **cache aggressively and permanently**: cache (1) the raw fetched document, (2) the cleaned text, and (3) the segmentation result, all keyed by accession number. A re-run of the same filing should cost **$0 and zero EDGAR requests**. This is the single biggest scalability lever after avoiding full-doc LLM.

---

## 4. Scalability Scenarios & Storage

| Scenario | Fetch | Segmentation compute | LLM cost (hybrid Sonnet) | Wall-clock (live API) |
|---|---|---|---|---|
| **1 filing (interactive frontend)** | 1–2 req, <1 s | <1 s CPU | ~$0.005 expected (LLM only if flagged) | **~1–3 s end-to-end** |
| **All ~8,000 annual 10-Ks** | ~12k req | seconds-minutes (parallel CPU) | **~$43** | ~40 min (or minutes via bulk ZIP) |
| **Full EDGAR-CORPUS ~90k** | use bulk ZIP / HF | minutes-to-low-hours (parallel CPU) | **~$486** | ~7–8 h crawl, or near-instant via bulk |

For the **interactive single-filing** path, keep the LLM escalation **synchronous only when flagged** and cache results; a clean filing returns in a couple of seconds with $0 LLM cost.

### Storage footprint (order-of-magnitude)

Assume median cleaned text ~300–500 KB/filing; raw HTML ~1–3 MB/filing; segmented JSON ~ similar to clean text + offsets.

| Artifact | Per filing | 8,000 filings | 90,000 filings |
|---|---|---|---|
| Raw HTML (cache) | ~1–3 MB | ~8–24 GB | ~90–270 GB |
| Cleaned text | ~0.3–0.5 MB | ~2.4–4 GB | ~27–45 GB |
| Segmented item JSON | ~0.3–0.5 MB | ~2.4–4 GB | ~27–45 GB |
| **EDGAR-CORPUS reference** | — | — | **~5–6 GB compressed JSON** (HF dataset) |

90k filings with all three artifact tiers is on the order of **~150–360 GB** — trivially cheap on object storage (single-digit dollars/month). Storage is **never the constraint**; the 10 req/s fetch ceiling and the LLM-scope decision are.

---

## Recommended Cost-Disciplined Architecture

**Principle: the LLM is a rescue mechanism, not the segmenter.** Push 100% of filings through CPU-cheap deterministic paths first; spend tokens only where the cheap path is provably uncertain.

### Where the LLM is NOT used
- **Default segmentation of all 16 items** → regex multi-strategy (TOC → header pattern → cross-reference index) + **CRF line labeling** (F1 ~0.982, CPU). This handles ~85% of filings end-to-end at $0 inference.
- **Re-processing any previously-seen filing** → served from the **immutable cache** by accession number. $0, zero EDGAR requests.
- **Bulk historical backfill** → EDGAR-CORPUS / bulk ZIPs, not live crawl.
- **Item 8 (financial statements) boundary sanity check** → cross-validate against `companyfacts` XBRL numeric facts (free, deterministic), not an LLM.

### Where the LLM IS used (escalation only)
- A filing trips a **low-confidence flag**: missing expected item, non-monotonic / overlapping char-ranges, round-trip reconstruction mismatch, or ensemble (regex vs CRF) disagreement.
- When invoked, it sees **only the ambiguous window**, via **LIB line-ID prompting** (index lines, never regenerate text), and outputs only the corrected start line-IDs.
- **New/rare item types** (e.g. Item 1C Cybersecurity) the CRF wasn't trained on → cheap prompt edit instead of full retrain.
- Tier choice: **Haiku for the boundary-fix call by default** (the task is index selection, not reasoning), escalate to **Sonnet** only if Haiku's line-IDs fail the consistency re-parse. Reserve Opus for nothing in the steady state.

### Resulting blended cost per filing

| Component | Coverage | Cost |
|---|---|---|
| Regex + CRF (CPU) | 100% of filings | ~$0 |
| Cache hits (re-runs) | depends on traffic | $0 |
| LLM escalation (Haiku, ~10% of doc) | ~15% of filings | ~$0.0018/filing blended |
| LLM escalation (Sonnet fallback) | ~few % of filings | rounds the blend to ~$0.003–$0.006 |

**Blended steady-state cost ≈ $0.003–$0.006 per filing** (Batch API on the escalation path pushes the low end to ~$0.0025). That is **~40–80× cheaper than full-document Sonnet ($0.24)** and **~70–130× cheaper than full-document Opus ($0.40)**, while *exceeding* full-doc LLM accuracy on core items (CRF 0.982 > GPT4ItemSeg 0.957) and *recovering* the hard legacy cases that pure CRF would silently miss.

For the **full 90k corpus**, that is **~$270–$540 of LLM spend total** (vs ~$21,600 full-Sonnet / ~$36,000 full-Opus), plus ~$5/month storage and a one-time bulk download instead of a 7-hour crawl.

---

## Risks & Caveats

- **Token figures for the primary HTML document are derived, not measured.** They come from word-count studies (CLS Blue Sky, ScienceDirect) × the 0.75-words/token rule, on *clean body text*. Raw HTML and inline XBRL inflate this 2–4×. Before finalizing budgets, **run a token census on a sample of real primary documents** (cleaned vs raw) with the actual tokenizer of the chosen model. `[Recommended verification]`
- **Escalation rate (assumed 15%) is an estimate**, not measured on our corpus. The blended cost scales linearly with it — if 30% of filings escalate, hybrid Sonnet doubles to ~$0.011/filing (still ~22× cheaper than full-doc). Instrument the actual flag rate. `[UNVERIFIED rate]`
- **CRF CPU timing (<1 s/filing)** is a representative engineering figure from the line-labeling design, not a benchmarked number on our hardware. Embedding-based variants (Sentence-BERT) are slower; pure feature-CRF is faster. `[Benchmark before committing to interactive SLAs]`
- **EDGAR limit is per-IP, not per-key** (there are no keys). Distributing across IPs to beat 10 req/s violates the policy ("regardless of the number of machines") and risks bans. Bulk ZIP is the sanctioned scale path.
- **Prices change.** All $/Mtok figures are June 2026; re-check the [Anthropic pricing page](https://platform.claude.com/docs/en/about-claude/pricing) at build time.

---

## Conclusions

1. The cost question is decided by **token volume, not vendor**: feeding 65k–270k tokens/filing through any frontier model is the expensive default; touching ~7k tokens on ~15% of filings is not.
2. **Regex + CRF on CPU is the workhorse** (F1 ~0.982, ~$0, sub-second); the LLM is a **cheap escalation rescue** scoped to ambiguous windows via LIB prompting.
3. **Recommended blended cost ≈ $0.003–$0.006/filing**, vs ~$0.24 (full-Sonnet) / ~$0.40 (full-Opus) — a **40–130× reduction** with *better* core-item accuracy.
4. **The 10 req/s EDGAR ceiling and immutable-filing caching, not compute or storage, govern scale.** Use bulk ZIPs for corpus jobs; cache everything by accession number forever.

---

## Sources

- [CLS Blue Sky Blog (Columbia Law) — The Ever-Expanding 10-K (2016)](https://clsbluesky.law.columbia.edu/2016/05/05/the-ever-expanding-10-k-why-are-10-ks-getting-so-much-longer-and-does-it-matter/) — median 23k (1996) → 49k (2013) words; ~3,300 repeated words.
- [Data visualization in 10-K filings, ScienceDirect (2023)](https://www.sciencedirect.com/science/article/abs/pii/S0165410123000551) — ~42,000 avg words by 2017, ~+200% since 1997.
- [AAA Accounting Horizons — Why are 10-K Filings So Long? (2016)](https://publications.aaahq.org/accounting-horizons/article/30/1/1/2275/) — 80–200 page range; drivers of length.
- [EDGAR-CORPUS, Loukas et al., ECONLP@EMNLP 2021](https://aclanthology.org/2021.econlp-1.2/) — >90k 10-Ks, 1993–2020, billions of tokens.
- [Lu, Chien, Yen, Chen, NTU 2025 — 10-K Items Segmentation, arXiv 2502.08875](https://arxiv.org/abs/2502.08875) — CRF F1 0.982, BERT4ItemSeg 0.982, GPT4ItemSeg 0.957, regex 0.905; LIB prompting.
- [Anthropic / Claude API Pricing (official)](https://platform.claude.com/docs/en/about-claude/pricing) — Haiku 4.5 $1/$5, Sonnet 4.6 $3/$15, Opus 4.8 $5/$25 per Mtok; cache read = 10% of base; June 2026.
- [Anthropic Message Batches API — 50% discount](https://pristren.com/blog/anthropic-batch-api-guide/) — async ≤24h, −50% input+output.
- [SEC — New rate control limits to EDGAR](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits) — 10 req/s, effective 2021-07-27.
- [SEC — Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) — User-Agent requirement, 10-min ban, bulk submissions.zip / companyfacts.zip.
- [HuggingFace eloukas/edgar-corpus](https://huggingface.co/datasets/eloukas/edgar-corpus) — pre-split corpus download.
- Cross-references: [doc 02 — OSS tools](02-opensource-tools-landscape.md), [doc 03 — SOTA segmentation & eval](03-sota-segmentation-and-eval.md), [doc 06 — confidence & silent failure](06-confidence-and-silent-failure.md).
