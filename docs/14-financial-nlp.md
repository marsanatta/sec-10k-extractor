# Financial-NLP Anchors: XBRL Tagging Reliability + the Downstream Use Case (Lazy Prices)

研究日期: 2026-06-22
來源數量: 4 primary references (FiNER-139, Scalable LLM 10-K, FinTagging, Lazy Prices) + cross-reference to our doc 07
信心程度: High for FiNER-139 / FinTagging / Lazy Prices core findings (read from arXiv/NBER abstracts + author summaries). Medium for the Scalable-LLM paper's exact cost/accuracy numbers (abstract omits them) and for Lazy Prices' four exact similarity-measure names (published-paper detail, abstract did not enumerate them — flagged `[UNVERIFIED]` where so).

## TL;DR

These four papers do two jobs for us. The XBRL papers (**FiNER-139**, **FinTagging**) tell us *how reliable XBRL is as an oracle* for our Item-8 cross-check (doc 07): the answer is **XBRL is a strong but imperfect oracle** — numeric *extraction/identification* is near-solved and reliable, but *concept linking* (which us-gaap tag) is where both filers and LLMs err, so we must validate against the **cluster of facts**, not any single named concept (which doc 07 already says — corroborated, mildly tempered). The **Scalable-LLM 10-K** paper shows the standard "segment → LLM-rate at scale" pipeline that we are competing with, and exposes its weakness: no published accuracy/cost validation and a no-ground-truth design — exactly the gap our hybrid + label-free verification fills. **Lazy Prices** supplies the *why*: year-over-year **textual change** in a firm's own 10-K (especially Risk Factors, litigation, management discussion) predicts returns at up to **188 bps/month (~22%/yr)** — and that result is only computable if item boundaries are **segmented cleanly and consistently across years for the same company**. That hands us a new, sharp requirement: **cross-year boundary consistency** must be an evaluation dimension, not just per-filing correctness.

---

## 1. FiNER-139 — XBRL numeric entity tagging, and how reliable the tags are

Source: [arXiv:2203.06482](https://arxiv.org/abs/2203.06482) (Loukas et al., ACL 2022).

**Core idea.** Reframes XBRL tagging as a word-level **named-entity-recognition** task over financial sentences: 1.1M annotated sentences, a label set of **139 entity types** (the 139 most frequent us-gaap concepts). The defining trait: *most of the tokens being tagged are numbers*, and the correct tag is determined by **context**, not by the token itself (the string "391" could be revenue, an asset, or a share count depending on surrounding words).

**Method / findings.**
- Plain BERT underperforms because **subword tokenization fragments numbers** ("391,035" splits into pieces), destroying the numeric signal. Word-level BiLSTMs beat it.
- Two fixes recover BERT: replace numeric expressions with **pseudo-tokens encoding the number's shape and magnitude** (so the model sees "a 6-digit number" rather than fragments).
- Their domain-pretrained **SEC-BERT** gives the best results.

**Implication for us (XBRL-as-oracle reliability).** FiNER-139 is the cleanest evidence that **numeric-fact identification in filings is a tractable, high-accuracy task** — which is exactly the part of XBRL our doc-07 Item-8 cross-check depends on (does a dense cluster of `us-gaap:*` numeric facts physically fall inside our Item-8 span?). The catch FiNER-139 surfaces: the *hard* part is choosing **which of the 139 tags** a number gets — i.e. concept disambiguation. For our purposes that is reassuring, because doc 07 already says to use the **cluster of facts** (not a specific concept like `us-gaap:Revenues`) for the boundary check. FiNER-139 confirms we are right to avoid relying on any single tag's identity: tag *identity* is the noisy dimension; tag *presence/location* is the reliable one. **Verdict: corroborates doc 07.**

---

## 2. FinTagging — full-taxonomy LLM XBRL benchmark, and where it breaks

Source: [arXiv:2505.20650](https://arxiv.org/abs/2505.20650).

**Core idea.** A benchmark for LLM XBRL tagging that, unlike prior simplified subsets (incl. FiNER-139's 139 tags), runs over the **full US-GAAP taxonomy — 10,000+ concepts** — and over **both text and tables**. It splits the task into two sequential subtasks:
- **FinNI** (Financial Numeric Identification): extract the numeric entities + their types from text/tables.
- **FinCL** (Financial Concept Linking): map each extracted entity to a concept in the full taxonomy.

**Key finding.** A sharp asymmetry: *"models generalize well in extraction, but struggle significantly with fine-grained concept linking."* I.e. **FinNI (find the number) is easy; FinCL (pick the right of 10,000 tags) is hard** — LLMs lack the "domain-specific, structure-aware reasoning" to navigate the taxonomy hierarchy.

**Implication for us.** This is the strongest temper on a naive "XBRL is ground truth" stance — but it temps the *concept-identity* axis, not the *offset/cluster* axis we actually use. Two consequences:
1. **Our Item-8 boundary cross-check stays valid.** It depends on FinNI-type signal (numeric facts exist and sit here), which both FiNER-139 and FinTagging show is reliable. We do not depend on FinCL-type signal (the exact concept), which is the unreliable part.
2. **Do not extend the XBRL oracle to concept-level claims.** If we ever wanted to validate *what* a number means (e.g. "this is total revenue"), FinTagging says that mapping is itself error-prone — for both the original filer (who chose the tag) and any LLM re-tagging it. So XBRL is an oracle for **"financial numbers live in this span"**, not for **"this number is concept X."** Doc 07's §2.3 limitation ("different filers tag the same fact under different concepts; filers add custom extensions") is independently confirmed by FinTagging. **Verdict: corroborates doc 07's cluster-based design; tempers any future concept-level oracle use.**

> Combined FiNER-139 + FinTagging takeaway for the oracle question: **XBRL is a high-reliability oracle for fact *presence and location* (what our boundary check needs) and a low-reliability oracle for fact *meaning/concept* (which we should not lean on).** Doc 07 is correctly scoped; this synthesis hardens that scoping with citations.

---

## 3. Scalable LLM 10-K framework — how others run extraction at scale, and the gap

Source: [arXiv:2409.17581](https://arxiv.org/abs/2409.17581).

**What it does.** An end-to-end, "no-code" pipeline to evaluate corporate performance from 10-Ks at scale, motivated by the impossibility of analysts manually reading the growing universe of filings. Three stages:
1. **Extraction & preprocessing** — auto-identify and **segment the SEC-required sections** (same segmentation problem we solve).
2. **LLM processing** — feed sections to **Cohere Command-R+** to generate quantitative ratings across dimensions (confidence, sustainability, innovation, workforce).
3. **Visualization** — interactive GUI with year-on-year comparison.

**What they got right.** The shape is the now-standard one and validates our overall architecture: **segment first, then run an LLM per section, then surface year-over-year.** The explicit year-on-year comparison feature is notable — it implies they, too, need consistent section boundaries across years (same requirement Lazy Prices forces, see §4).

**What they got wrong / what's missing.** The paper **publishes no accuracy validation, no cost-per-filing, and no ground-truth methodology** for the segmentation or the ratings — the abstract and figure list contain no benchmark. This is the central weakness and it is *the* gap we exploit:
- They treat the LLM ratings as outputs to *display*, not outputs to *verify*. There is no silent-failure detection, no boundary cross-check, no confidence gating.
- "Segment then LLM-rate" with **no label-free verification layer** is precisely the design our doc 06 (confidence/silent-failure) and doc 07 (XBRL cross-check) are built to beat.

**Cost/accuracy lesson vs our hybrid.** A single-pass commercial-LLM-over-every-section design is simple but (a) **unvalidated** and (b) **uncapped in cost** (one large-context LLM call per section per filing, at scale). Our hybrid — deterministic/rule-based segmentation first, XBRL + structural invariants as a free verification layer, and LLM **only on flagged low-confidence boundaries** (doc 07 §A step 3, doc 05) — is both cheaper (LLM is targeted, not blanket) and *checkable* (we can tell when it failed). **Verdict: validates our pipeline shape; their missing verification + cost discipline is our differentiator.** `[UNVERIFIED]` exact cost/accuracy — the paper does not report them, so this comparison is on design, not measured numbers.

---

## 4. Lazy Prices — the downstream use case that justifies clean, *stable* item boundaries

Source: [Cohen, Malloy & Nguyen, "Lazy Prices," *Journal of Finance* 75(3), 2020](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12885) (paywalled; findings from the [NBER w25084 author summary](https://www.nber.org/papers/w25084) and the published abstract).

**Core finding.** When a firm **changes the language** of its 10-K/10-Q relative to its *own prior filing*, that change predicts negative future returns. A long–short strategy — **buy the firms that did NOT change their language, short the firms that did** — earns **up to 188 basis points in monthly alpha (over 22% per year)**.

**What drives it.** The predictive power concentrates in changes to specific areas: the **risk-factor section (Item 1A)**, **litigation / legal proceedings (Item 3)**, and **management/executive-team discussion**. Changes also predict future earnings, profitability, news, and even bankruptcies.

**Why the alpha exists — investor inattention.** There is **no announcement effect** at filing time; the return only accrues *later* when the bad news surfaces via earnings/events. Investors are "lazy" — they do not read the year-over-year diffs, so the signal is slow to price in.

**Method (text comparison).** The signal is computed by measuring **document similarity between a firm's current filing and its own prior-year (or prior-quarter) filing** — a within-firm, across-time diff. The paper uses a battery of standard textual-similarity measures `[UNVERIFIED exact set — the published paper enumerates four: cosine similarity, Jaccard similarity, minimum edit distance, and Sorensen–Dice; the abstract/NBER summary I could fetch did not list them, so treat the specific four as the widely-cited published detail, not something I re-verified]`. The crucial mechanic for us: **the comparison is firm-to-itself-last-year**, and is most powerful when run **section-by-section** (a change buried in Risk Factors is more meaningful than the same number of changed words spread across boilerplate).

**Implication for us — this is the load-bearing one.** Lazy Prices is the canonical justification for why **item-level segmentation must be (a) clean and (b) consistent across years for the same company**:
1. **Section-level diffing requires section boundaries.** The signal is strongest *per item* (Risk Factors vs MD&A vs Legal). You cannot diff Item 1A year-over-year if your segmenter draws the Item 1A boundary differently in 2023 vs 2024 — the diff would be dominated by **boundary noise**, not real text change. A boundary that drifts by a paragraph manufactures a fake "change" and corrupts the signal.
2. **Cross-year stability is a distinct, harder requirement than per-filing correctness.** A segmenter can be individually correct on FY2023 and FY2024 yet still place the Item-7→Item-8 boundary one heading earlier in one year (e.g. because the filer reworded a sub-header), injecting spurious diff. For the Lazy Prices use case, *consistency between the two years matters as much as correctness of either*.
3. **This is the real customer of our output.** It reframes our deliverable: not "extract items from one 10-K," but "produce item spans **comparable across a company's filing history**," because that comparability is what a quant signal (or any longitudinal analysis) consumes.

---

## What changes in our design / requirements

1. **Add cross-year boundary consistency as a first-class evaluation dimension.** Today our eval (doc 08) scores per-filing item-boundary correctness. Add a **longitudinal metric**: for the same CIK across consecutive fiscal years, measure whether the *same* item (e.g. Item 1A) is segmented with **stable boundaries** — and, ideally, that the year-over-year **text-diff is dominated by genuine content change, not boundary shift**. Concretely: for a company's FY(n) and FY(n-1) filings, the segmenter-induced delta at the item edges should be near-zero on unchanged boilerplate. This is a *new* test set construction: same-company multi-year filing pairs.

2. **Treat boundary drift as a silent-failure mode.** A boundary that moves between years without the underlying text moving is a silent failure that per-filing eval will not catch (each filing looks fine alone). Flag it: if Item-X start/end shifts year-over-year but the surrounding anchor text (headers) did not, lower confidence and route to review (extends doc 06's silent-failure taxonomy + doc 07's disagreement-flag pattern).

3. **Keep the XBRL oracle scoped to presence/location, never concept identity.** FiNER-139 + FinTagging jointly confirm: use the *cluster* of numeric facts to validate the Item-8 span (reliable), and do **not** build any check that asserts a number's *meaning* via its us-gaap concept (unreliable for both filers and LLMs). No change to doc 07's mechanism — this just hardens the rationale with citations and forbids a tempting over-extension.

4. **Lead on the verification gap the Scalable-LLM paper leaves open.** That paper is a representative "segment + blanket-LLM, no validation, no cost cap" competitor. Our positioning and eval should explicitly demonstrate the two things it lacks: **label-free verification** (XBRL/structural invariants) and **targeted-LLM cost discipline** (LLM only on flagged boundaries). These become headline differentiators, not implementation footnotes.

5. **Expose stable item IDs in the output schema to support longitudinal diffing.** So a downstream Lazy-Prices-style consumer can line up Item 1A(FY2023) with Item 1A(FY2024) trivially, the output should carry a normalized item key (Part/Item number + canonical title) that is **stable across years and across filer-specific header wording** — making the segments comparable-by-construction.

---

## Sources

- [FiNER-139 — arXiv:2203.06482](https://arxiv.org/abs/2203.06482) — Loukas et al., XBRL numeric entity tagging as NER; 139 tags; numbers-are-context; SEC-BERT.
- [Scalable LLM 10-K framework — arXiv:2409.17581](https://arxiv.org/abs/2409.17581) — segment → Command-R+ rating → year-on-year GUI; no published accuracy/cost validation.
- [FinTagging — arXiv:2505.20650](https://arxiv.org/abs/2505.20650) — full US-GAAP (10k+ concepts) LLM XBRL benchmark; FinNI easy, FinCL (concept linking) hard.
- [Lazy Prices — Cohen, Malloy & Nguyen, *Journal of Finance* 75(3) 2020, DOI 10.1111/jofi.12885](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12885) (paywalled) — year-over-year 10-K text change predicts returns, up to 188 bps/month (~22%/yr); driven by Risk Factors / litigation / management; investor inattention. Findings via [NBER w25084](https://www.nber.org/papers/w25084).
- Cross-reference: this repo's `docs/07-ixbrl-structure-exploitation.md` (XBRL Item-8 cross-check), `docs/06-confidence-and-silent-failure.md`, `docs/08-eval-set-construction.md`, `docs/05-cost-latency-scalability.md`.
