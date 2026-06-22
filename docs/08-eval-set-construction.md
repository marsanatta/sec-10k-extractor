# 08 — Evaluation-Set Construction: Stratified Sample + Gold/Silver Calibration

研究日期: 2026-06-22
信心程度: Medium-High. The stratification design and gold/silver calibration method are grounded in the verified pathologies of `04-format-variance-taxonomy.md` and in EDGAR-CORPUS / itemseg primary sources. The specific counts are an engineering proposal (defensible, but a design choice — tune to labeling budget). Statistical claims about CI width are exact (binomial); the per-stratum N is a recommendation, not a derived optimum.

## The core problem

There is **no public, filing-level ground truth** for 10-K item boundaries at scale. The largest labeled set is Lu et al. 2025 (NTU itemseg): **3,737 manually-annotated 10-Ks, FY2001–2019** (im.ntu.edu.tw/~lu/data/itemseg/) — but it predates Item 1C (2023), Item 6 `[Reserved]` (2021), and modern iXBRL, and it excludes pre-2001 SGML. So the eval strategy is **three-tier**:

1. **GOLD** — small, hand-labeled, char-exact item boundaries. The only true ground truth. Used to *calibrate* everything else.
2. **SILVER** — large, machine-labeled (EDGAR-CORPUS, ~90k filings). Cheap, broad coverage, **known-noisy** (regex split, has the Item1+Item2 merge bug, issue #35). Used as a baseline to **diff against**, not to score against directly.
3. **STRUCTURAL** — label-free invariants (monotonic ranges, doc-coverage, round-trip reconstruction, Item-8 vs XBRL companyfacts). Runs on 100% of filings, no labeling cost. (Detailed in `06-confidence-and-silent-failure.md`.)

## Why diff-against-silver works without trusting silver

EDGAR-CORPUS is wrong in **predictable, enumerable** ways (Item1+Item2 merge; chokes on pre-2001 SGML; misses 1C/reserved). So:
- **Agreement** between our extractor and silver on an *easy* filing = weak positive signal (both could share the same regex blind spot — beware self-consistency, see below).
- **Disagreement** is the high-value signal: it localizes exactly the filings where at least one of us is wrong. We then route those disagreements to **gold labeling** or **structural checks**.
- The gold subset **calibrates** the silver: by hand-labeling a sample of *both* agreements and disagreements, we measure silver's true precision/recall **per stratum**, then use that as a correction factor when reading silver-vs-us aggregate numbers. Without gold, "we agree with silver 94% of the time" is uninterpretable — silver itself might be 80% correct.

> Engineering-rigor guard (from CLAUDE.md): **never use self-consistency as validation.** If our extractor and the silver baseline share a regex lineage, agreement proves nothing. Gold must be labeled **independently** of both the production code and the silver toolkit, and the Item-8/XBRL check must use companyfacts (a different data source) — not our own boundary output.

---

## A. Stratification design

Three orthogonal axes. We stratify on the cross-product but collapse impossible/rare cells.

### Axis 1 — Format era (the S1/S2/S3 stressor)
| Era | Definition | Notes |
|---|---|---|
| E1 pre-2001 SGML | plaintext `.txt`, all-caps ITEM, no anchors | EDGAR-CORPUS covers 1993+; SGML is its weakest tier |
| E2 early/mid HTML | ~2001–2010, `dNNk.htm`/`.txt` transition | tag soup, `<PAGE>` artifacts |
| E3 mature HTML | ~2011–2018 | clean-ish HTML, pre-iXBRL-mandate |
| E4 inline-XBRL | 2019+ (iXBRL phased mandate) | styled-span headers, fact layer available |

### Axis 2 — Filer size (the long-tail stressor)
| Size | Proxy | Why it matters |
|---|---|---|
| F1 Large accelerated | mega-cap, huge TOC, cross-ref index (GE/JPM) | size + reordering |
| F2 Accelerated | typical S&P mid | the "normal" case |
| F3 Smaller reporting co (SRC) | cover checkbox; 2-yr financials; Item 7A stub | the EDGAR-CORPUS long tail; most edge cases live here |

### Axis 3 — Pathology (the S4/S5 stressor) — from `04-format-variance-taxonomy.md`
P1 Part III incorporated-by-reference · P2 Item 6 `[Reserved]` · P3 Item 1C present · P4 Item 7A omitted (SRC) · P5 10-K/A amendment · P6 huge filing + cross-ref index · P7 no-TOC-anchors · P8 styled-span/NBSP headers · P9 reordered/fragmented headers (Item 1 vs 10–16 trap) · P0 "clean" control (no known pathology).

---

## B. Proposed eval set — counts

Design target: every (era × pathology) cell that can exist has ≥ enough filings to estimate a per-cell pass rate with a usable confidence interval, plus a control stratum and an over-sample of the hard tail.

### B.1 SILVER pool (no manual labeling)
- **Full EDGAR-CORPUS: ~90,000 filings (1993–2020)** — used *only* as the diff baseline + to draw stratified samples from. Not scored directly.
- Extend silver to FY2021–FY2025 by running EDGAR-CRAWLER ourselves on ~the most recent 5 years of large+SRC filers (≈ another 30–40k), because EDGAR-CORPUS stops at 2020 and **all of P2/P3 (Reserved / 1C) live after 2020**. This is the only way silver covers the newest pathologies.

### B.2 EVAL set (the scored sample drawn from silver + targeted hand-picks)
Stratified draw, oversampling pathologies (they are rare in a uniform draw):

| Stratum | Per-cell N | Cells | Subtotal |
|---|---|---|---|
| Era control (E1–E4 × clean P0) | 40 | 4 | 160 |
| Filer size (F1,F2,F3 × clean P0) | 40 | 3 | 120 |
| Pathology cells (P1–P9), drawn across eras where each can occur | 30 | 9 | 270 |
| Hard-tail hand-picks (the literature cases + GE/JPM/Apple/M2i/Chemed from doc 04) | — | — | 50 |
| **Total EVAL N** | | | **≈ 600** |

600 is small enough to run our full pipeline + structural checks repeatedly during development, large enough that each ~30-filing pathology cell gives a binomial 95% CI of roughly ±18 pp at p≈0.5 (tighter near the extremes) — adequate to detect a stratum the extractor *systematically* fails, which is the goal. (For publication-grade pass-rate point estimates you would 3–5× the per-cell N; for catching regressions during dev, 30 is the right ROI.)

### B.3 GOLD subset (hand-labeled, char-exact)
- **Size: 150 filings** (25% of the 600 EVAL set), allocated:
  - 10 per pathology cell P1–P9 = 90 (so every pathology has gold)
  - 10 per era E1–E4 control = 40
  - all 20 hard-tail hand-picks fully labeled = 20
- Label **char-offset start/end per item** (Items 1–16 incl. 1A/1B/1C/7A/9A/9B as present), plus per-item flags: `reserved`, `incorporated_by_reference`, `omitted_SRC`, `amended_only`. Two annotators, adjudicate disagreements, report **Krippendorff's α** on boundary agreement (target α > 0.8 before trusting the labels).
- 150 is the floor at which each pathology has 10 gold examples — enough to (a) measure our extractor's per-pathology precision/recall and (b) measure **silver's** per-pathology error rate, which is what calibrates the diff.

### B.4 Why these numbers (sanity)
- 600 EVAL keeps a full dev-loop pass under a few minutes and well under EDGAR's 10 req/s ban threshold if re-fetching (most should be cached locally).
- 150 GOLD ≈ 1–2 annotator-weeks at ~30 filings/day with char-offset tooling — the binding constraint is labeling time, so gold is deliberately the smallest tier that still covers every pathology with n=10.

---

## C. The calibration loop (how gold calibrates silver, step by step)

1. **Run silver** (EDGAR-CORPUS labels) and **our extractor** on all 600 EVAL filings → per-item boundaries from each.
2. **Diff** them per item → mark each filing as *agree* / *disagree* per item.
3. **On the 150 GOLD filings**, compare BOTH silver and ours against the hand labels:
   - Compute **our** per-stratum precision/recall/boundary-IoU.
   - Compute **silver's** per-stratum precision/recall — this is the **calibration table** (e.g., "silver recall on E1/SGML = 0.61; silver merges Item1+Item2 in X% of F2 filings").
4. **Apply the calibration table** to the other 450 EVAL filings: when we read "we agree with silver on 94% of E3/large filings", we correct it by silver's known accuracy on that stratum to estimate our *true* accuracy — without having labeled all 450.
5. **Route disagreements** on the 450 ungolded filings: a disagreement where silver is known-weak (e.g., SGML, Item1+Item2) → trust ours pending a structural check; a disagreement where silver is known-strong → flag for spot gold-labeling. This is **active-labeling**: the next gold filings to label are the disagreements that the calibration table can't adjudicate.
6. **Structural invariants run on 100%** as the independent third vote (no labels needed): coverage, monotonicity, round-trip reconstruction, Item-8 range vs XBRL companyfacts numeric facts. A filing that passes structural checks but disagrees with silver is strong evidence *silver* is wrong → candidate to *correct the silver baseline* and grow gold.

Net: gold is the anchor, silver is the broad-but-biased ruler, structural checks are the label-free cross-check, and the diff between them is the engine that decides where to spend the next unit of expensive hand-labeling.

## D. Metrics to report

- Per-item **boundary IoU** / exact-match start-line accuracy (the itemseg metric: macro-F1 over core items 1/1A/3/7).
- **Per-stratum** pass rate with binomial 95% CI (so a weak era/pathology is visible, not averaged away).
- **Silver-disagreement rate** per stratum (proxy for "where to look").
- **Silent-failure rate**: filings returning 0 items or non-covering ranges *without* a low-confidence flag (target → 0; this is the headline number, see `06-confidence-and-silent-failure.md`).
- **Calibration table**: silver precision/recall per stratum (the artifact that makes the 450 unlabeled filings interpretable).

## E. Concrete seed filings for GOLD (already verified, from doc 04)

| Pathology | Filing | CIK | Accession |
|---|---|---|---|
| E1 SGML / P7 no-anchors / P9 regex trap | Microsoft FY1995 | 789019 | 0000891020-95-000433 |
| E2 early HTML | Microsoft FY2006 | 789019 | 0001193125-06-180008 |
| E4 iXBRL / P1 IBR / P2 Reserved / P3 1C / P8 styled-span | Apple FY2024 | 320193 | 0000320193-24-000123 |
| F3 SRC / P4 Item 7A omitted | M2i Global FY2023 | 1753373 | 0001493152-24-014827 |
| P5 amendment | Chemed 10-K/A FY2024 | 19584 | 0001562762-25-000070 |
| F1 huge / P6 cross-ref index | GE FY2023 | 40545 | 0000040545-24-000027 |
| literature boundary-order cases | Allstates WorldCargo FY2002; Hub Intl FY2006; Alt. Asset Mgmt Acq. FY2007 | (per itemseg paper) | — |

These 6+3 are the spine of the 20 hard-tail hand-picks; expand each pathology to n=10 by drawing same-pathology siblings from the silver pool (FTS gives thousands per pathology, e.g. 5,479 "Item 1C. Cybersecurity" 10-Ks in H1-2024 alone).
