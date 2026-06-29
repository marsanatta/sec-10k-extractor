# SEC 10-K Item-level Structured Extractor

Split a raw SEC **10-K** filing into its individual **items**, so each section can be read on its own.

> **Two terms, defined once:**
> - **10-K** — the annual report a US public company files with the SEC (the financial regulator).
> - **Item** — a numbered section the SEC requires, for example *Item 1 Business*, *Item 1A Risk Factors*, *Item 7 Management's Discussion (MD&A)*, *Item 8 Financial Statements*. A full 10-K has up to 23 items, spread across Parts I–IV.

This tool reads one 10-K and returns each item separately. For each item, it gives the exact location in the source text, a confidence score, and a clear status: found, legitimately missing, or failed to extract. It works across the three filing format eras. It checks its own output **without a public reference answer (ground truth)**, and it is honest about the cases it still cannot handle.

---

## Table of contents

- [The core idea](#the-core-idea)
- [What it produces](#what-it-produces)
- [Run it](#run-it)
- [Live frontend](#live-frontend)
- [How it works](#how-it-works)
- [Key design decisions](#key-design-decisions)
- [Works well (with examples)](#works-well-with-examples)
- [Known limitations (with examples)](#known-limitations-with-examples)
- [How quality is checked (no public reference answer)](#how-quality-is-checked-no-public-reference-answer)
- [Cost, scalability, correctness](#cost-scalability-correctness)
- [Repo layout](#repo-layout)
- [Where AI helped](#where-ai-helped)

---

## The core idea

**Index, don't generate.** An item is stored as a `char_range` — the start and end character positions of that item inside the filing's text. It is **never** free text written by a language model. Because we keep exact positions, joining all the items back together rebuilds the original document byte-for-byte. We call this the **round-trip** check, and it makes coverage provable.

The system has three layers. It always uses the cheap one first:

1. A **deterministic** layer (fixed rules: regular expressions and section anchors) runs on ~100% of filings at **$0** — no paid model call. (This is a **cost** statement, not an accuracy one: every filing passes through the rules tier for free; the robustness and accuracy numbers are in [`ANALYSIS.md`](ANALYSIS.md) §2.)
2. A **validation layer** then attaches a confidence score and a provenance record (which checks passed or failed) to every item. **This layer is the real product** — no existing item-splitter reports confidence.
3. A **language-model (LLM) layer** is available but **turned off by default**. We measured it and it gave **no improvement** on our verified examples, so the default path never calls it. (Details below and in [`ANALYSIS.md`](ANALYSIS.md) §7.)

Full numbers, trade-offs, and the verification story are in **[`ANALYSIS.md`](ANALYSIS.md)**.

---

## What it produces

For each item, the tool returns one record:

```json
{
  "item_id": "I.1",
  "part": "I",
  "item": "1",
  "title": "Business",
  "text": "...",
  "char_range": [1234, 5678],
  "status": "present",
  "confidence": { "band": "high", "score": 0.95, "signals": ["..."] },
  "provenance": { "extractors": ["anchor"], "checks_passed": ["..."], "checks_failed": [] }
}
```

It also returns one filing-level summary: a `needs_review` flag, the coverage, the oracle and cross-check results, and the LLM cost record (a running tally of calls and tokens).

The `status` field is always one of three values. A missing item is **classified, never silently dropped**:

| status | Meaning |
|--------|---------|
| `present` | The item was found. |
| `legitimately_absent` | The item is correctly missing (the filing's year or type never had it). |
| `extraction_failure` | The item should be there, but extraction failed. The system says so. |

---

## Run it

**Prerequisite — SEC User-Agent.** SEC EDGAR (the SEC's filing database) requires a descriptive `User-Agent` header — a name and email — on every request. Copy the example file and set it:

```bash
cp .env.example .env
# In .env, set:  SEC_EDGAR_USER_AGENT="Your Name you@example.com"
```

### Option A — Docker

```bash
docker compose up --build         # builds and starts the app on http://localhost:8000
```

### Option B — Local development

```bash
pip install -e ".[api,dev]"
( cd web && npm install && npm run build )    # build the web UI into web/dist
SEC_EDGAR_USER_AGENT="Your Name you@example.com" uvicorn api.server:app --port 8000
# then open http://localhost:8000
```

### Option C — Tests and the evaluation harness

```bash
python -m pytest -q     # 101 offline unit tests (100 pass, 1 skipped) — network-free, no User-Agent needed
SEC_EDGAR_USER_AGENT="Your Name you@example.com" python eval/run_eval.py   # on-demand EDGAR batch -> eval/report.md
```

The unit suite is fixture-based and never touches the network. It includes a boundary mutation battery, the LLM cost record, and the Signal D independence guard (all defined below). `eval/run_eval.py` is the on-demand batch that fetches pinned filings from EDGAR and regenerates `eval/report.md`.

---

## Frontend

The web UI lets you submit or select a filing, inspect each extracted item, and see the source highlight, the confidence score, which checks fired, and the present / legitimately-absent / failure status. See [Run it](#run-it) — the Docker app serves it on `http://localhost:8000`.

The demo filings in the UI are **open** (no token). Free-form extraction (any ticker or accession, or pasting filing text) is protected by an optional shared token (`SEC10K_ACCESS_TOKEN`), so an exposed endpoint cannot be used to overload SEC's rate limit.

---

## How it works

The pipeline has five stages: **ingest → normalize → segment → validate → schema**. The first stages turn a raw filing into canonical text with exact byte offsets, then split it into items by rules. The validation stage attaches confidence and provenance. The reasons for this shape are in [Key design decisions](#key-design-decisions).

The tool must handle three filing format eras:

- **SGML** — the old plain-text filing format, used before ~2001.
- **HTML** — the middle era.
- **iXBRL** — modern HTML with embedded financial-data tags.

The deterministic layer also handles several awkward header styles: token-per-line headers (`Item` and `1.` on separate lines), separator-less headers (`ITEM 1 BUSINESS`), and combined headers (`Items 1 and 2`). See the examples below.

---

## Key design decisions

Each decision below is backed by a reason or by measured evidence.

| Decision | Reason or evidence |
|----------|--------------------|
| **Index, don't generate** (items are character ranges, not generated text) | The round-trip rebuild is an enforced check, so coverage is provable and no text is invented. |
| **Deterministic rules first, LLM last** | Existing research shows a code/rules segmenter can run on ~100% of filings at $0 (a cost point, not an accuracy claim); the LLM is reserved for the flagged minority. |
| **The validation layer is the product** | No existing item-splitter reports confidence. The differentiator is calibrated confidence + provenance on every item, gated by `needs_review`. |
| **Independent oracles for verification — never self-consistency** | A model judging its own output cannot catch its own confident, systematic errors. Every check uses a source that does not share code with the extractor. |
| **Conservative `edgartools` fallback** (never copies foreign offsets) | It re-locates item heads in our own canonical text to keep the `char_range` contract, and only fires when the rules fail — so clean filings are untouched. |
| **Eval set built gradually, with strict statistics** | There is no public ground truth, so we built a stratified, accession-pinned covering set and report every rate with filing-clustered confidence intervals. |

### Decisions that changed (and why)

Two decisions were made one way, then updated based on evidence. We keep both stories because they show the design is evidence-driven, not fixed.

- **The LLM tier was built, then turned OFF by default.** We first built a real LLM escalation tier. Then we measured it (LLM-on vs LLM-off) against the frozen gold: it moved **zero** boundaries on every gold filing (ΔIoU 0.000), and fired 106 model calls for 2 changes that could not be verified. The deterministic path was already correct on the gold, so we changed the default to **off** and kept the tier as an honest, measured opt-in — not a claimed win.
- **The form-aware template fix was discarded, then earned back.** We found the expected-item template was "form-blind": it judged a Part-III-only 10-K/A amendment as a broken full 10-K. We implemented a form-aware fix — but in round 1 we **discarded it**, because its only benefit showed up in a metric the system could optimize directly (a Goodhart risk), with no independent signal confirming it. In round 2 we built an independent reference (Signal D, a human-audited classification gold) and only **then** kept the fix, because it moved that independent reference while the controls stayed unchanged.

---

## Works well (with examples)

These cases are reliable. Each row names a **real, accession-pinned filing** from `eval/eval_set.json` that is marked as a pass (`expect_red: false`).

| Case | Example filing | Result |
|------|----------------|--------|
| Clean modern iXBRL | Apple FY2024, Coca-Cola FY2023, Microsoft FY2023 | All items found; char-exact boundary match (match-rate 1.0 at IoU ≥ 0.9, mean IoU ≈ 1.0; IoU = intersection-over-union, a 0–1 overlap score). |
| Legacy SGML (pre-2001) | Microsoft FY1995 / FY1996 | Items found; FY1995 carries human-verified boundary gold. |
| Token-per-line headers (`Item` then `1.`) | M2i FY2023, 374Water FY2025 | A newline-tolerant rule recovers the items. |
| Collapsed body, recovered | GE FY2009 | The rules collapse the body → the `edgartools` fallback rebuilds the items. |
| Broken text source | JPMorgan FY2023 | A broken text extractor is detected → the HTML fallback recovers the items. |

> **Note on the harder header styles.** Separator-less and combined headers are also handled, and their boundaries are checked against human-verified gold. But their anchor filings (General Mills FY2018, Occidental FY2020) are **tracked as hard cases**, not listed here as clean passes — see [Known limitations](#known-limitations-with-examples) and [`ANALYSIS.md`](ANALYSIS.md) §2.

**Population evidence (not just hand-picked cases).** We ran two fresh, held-out batches of filings the system had never seen. The pass rates stayed in the same band, which shows the fixes generalize. The rate is computed over the full-10-K subset of each batch (amendments and non-10-K rows are excluded):

| Sample | Full 10-Ks measured | Structural-pass rate |
|--------|---------------------|----------------------|
| Held-out sweep 2 | 644 (of 883 fetched) | 93.5% (95% CI 91.3–95.1) |
| Held-out sweep 3 (fresh) | 656 (of 880 fetched) | 92.2% (95% CI 89.9–94.0) |

> *Structural-pass* is an **upper bound on robustness, not accuracy.** It only confirms the output is well-formed (non-empty, no overlaps, rebuilds the source, plausible coverage). The accuracy floor is the human-verified boundary-gold filings (see [How quality is checked](#how-quality-is-checked-no-public-reference-answer)).

---

## Known limitations (with examples)

These cases are still hard, unstable, or unsupported. They are listed **on purpose**. Every one is **detected and flagged** (`needs_review`) — none is a silent failure. The measured silent-failure rate is **0**.

| Case | Example filing | Status |
|------|----------------|--------|
| **Header text stripped (the named ceiling)** | Morgan Stanley FY2024 | The `Item N` labels live only in styled tags that are removed when the styling is stripped. Both the rule and the fallback are header-based, so both find **0 items**. **Unsupported** without a non-header model (see below). Flagged. |
| **Cross-reference index** | Intel FY2018, GE FY2023 | The body has no `Item N` headings; items are listed only in an end-of-document index table. Coverage drops to ~1–2%. **Unsupported** by the header approach (~1% of filings). Flagged. |
| **Scattered item** | JPMorgan FY2023, Item 7 | Item 7 is a short pointer stub; the real MD&A text sits outside the range. Recall cannot see this, so a dedicated scattered-item probe flags it. Tracked. |
| **Lead-item drop** | Bank of America FY2023, Walmart FY2003, Honeywell FY2024 | Item 1 / Item 7 dropped due to run-fragmentation, a joined-together `PART I ITEM 1.` line, or a no-separator header. Flagged. |
| **Separator-less header (hard anchor)** | General Mills FY2018 | A separator-less header (`ITEM 1 BUSINESS`); the boundary is char-gold-verified, but the filing is still tracked `expect_red` at the full-filing level. Tracked. |
| **Tolerant-split over-drop** | ~1.8% of filings (Item 7A) | When an in-prose cross-reference (e.g. "see Item 8") sits mid-run, the relaxed split skips a genuine item, so the segmenter conservatively keeps the strict partial result instead of recovering at the cost of Item 7A (~22 of 1,735 cached filings). Flagged (`needs_review`). Deferred — high blast-radius for a ~1.8% already-mitigated gain. |
| **Filing selection** | 374Water 10-K/A | A ticker-by-year lookup can return a 10-K/A amendment (Part III only) instead of the full 10-K. The eval pins the full filing by accession. Tracked. |

**The one fix that is genuinely out of scope:** the *named ceiling* above needs a **non-header extractor that fails differently from the rules** — for example a **CRF** (Conditional Random Field, a sequence-labeling model) that relies on structure (`is-line-start`, `prior-item-seen`) instead of the `Item N` text. This is large effort and documented as the stretch item. The point is that the system **flags** these filings instead of returning a broken result silently.

---

## How quality is checked (no public reference answer)

There is no public, filing-level reference answer (ground truth) for 10-K item boundaries. So every check below is **independent of the extractor** — a model judging its own output cannot catch a confident, systematic error. The checks run cheap-to-expensive:

1. **Structural rules + round-trip (100% of filings, no labels needed).** Items must be ordered, non-overlapping, and rebuild the source byte-for-byte.
2. **Independent dual-extractor cross-check.** A second tool (`edgartools`) supplies its own item text; we compare. *Honest limit:* both tools are header-based, so they share the same weakness — this gates big items, not the hard cases.
3. **Char-exact human gold (8 filings).** A human read the filing and marked each item's true boundary; we score overlap (IoU ≥ 0.9). Two of the eight (M2i, Microsoft FY1995) were labeled by a method independent of the rules, so their agreement is a genuine cross-check, not a circular result.
4. **XBRL Item-8 oracle.** A tagged financial fact, taken from the SEC's companyfacts API (**not** our output), must fall inside the extracted Item 8.
5. **Per-item status check (`expected_status`).** For a few filings we assert the correct *status* of named items, taken from a human-audited reference. Example: Microsoft FY1996 has no Item 7A (that item did not exist in 1996), so the system must mark it `legitimately_absent`, not `extraction_failure`. This catches mis-classification that a presence-only check cannot see.
6. **Signal D — classification gold.** A human-audited, frozen reference labels each item's true status by the objective rule "does the heading physically exist?". It independently catches real production errors (for example a date-boundary mistake on Item 1C).
7. **Validate-the-validator.** A mutation battery injects faults (swap, merge, truncate an item) into a known-good filing and asserts each check fires. A check that never fails is worthless.

The headline result is **silent-failure rate 0/27 on the curated set** (where the flag is measured against the gold) — the system is allowed to be wrong only when it says so. On the large population sweep we report structural-pass only (an upper bound); the flag-vs-silent check on the fail tail is reproducible via `eval/sweep_fail_tail.py`, but that population result is not committed as a report. Boundary match-rate is **1.0 at IoU ≥ 0.9 across the 6 eval-set gold filings** (mean IoU 0.996–1.000: Apple, Coca-Cola, Microsoft FY2023, M2i, Microsoft FY1995, General Mills FY2018); 8 char-gold in total (the other 2 — US Bancorp, Occidental — are fix-targets outside the covering set, see [`ANALYSIS.md`](ANALYSIS.md) §2), scoped per era.

---

## Cost, scalability, correctness

See [`ANALYSIS.md`](ANALYSIS.md) for the full numbers.

- **Cost (§3).** The deterministic path is **$0** per filing. The default extract path is also $0, because the LLM layer is off by default and was measured to add no gain on our gold. When an author chooses to enable it, the real Copilot call is about 13k input tokens per call, at a flat-rate quota, so the marginal dollar cost is ≈ 0.
- **Scalability (§4).** The deterministic path is O(n) over the text and stateless per filing, so it scales out in parallel. Results cache by accession. The real throughput limit is EDGAR's rate limit, not CPU or memory.
- **Correctness (§5–6).** Round-trip is enforced, so coverage is provable. Every item carries confidence and provenance. Missing items are classified, never dropped. The headline metric is the silent-failure rate (0), not raw accuracy.

---

## Repo layout

```
sec10k/      pipeline: ingest -> normalize (canonical text + offsets) -> segment -> validate -> schema
api/         FastAPI server (extract / demo / paste-text / eval report) + token gate
web/         React + Vite frontend (item navigator, boundary viewer, confidence panel)
eval/        accession-pinned eval set, run_eval.py, boundary_gold.json + classification_gold.json (human-audited)
tests/       offline, network-free unit + mutation / independence-guard tests
docs/        design and grounding docs
prompts/     dated, verbatim key prompts (the AI-collaboration trail)
research/    autoresearch round findings + append-only progress records
ANALYSIS.md  the analysis report (performance, cost, scalability, verification, failure modes)
```

SEC filings are public-domain U.S. government data.

---

## Where AI helped

This project was built with AI as a working partner. I guided the work through prompts and review, but AI did much of the heavy lifting — and a lot of the *checking*, including reviewing its own output. The full trail is in [`prompts/`](prompts/) (dated, verbatim prompts) and [`research/`](research/) (the autoresearch rounds). The main places AI helped:

1. **Understanding the domain.** I ran grounding research first to choose the methodology, and used AI to come up to speed quickly on what a 10-K filing is, how its items are structured, and how to *validate* an extraction when there is no public ground truth. I pushed for explanations I could actually check: *"use simpler to understand ones, with illustration and analogy."*

2. **The cost decision.** I questioned whether the tool even needed an LLM: *"i am curious why the 10k extractor need a llm? i thought we only need the pipeline."* AI confirmed, from existing research, that a deterministic code segmenter handles the common case at near-zero cost, and that the LLM could be added and tested later. This set the "deterministic-first, LLM-last" design.

3. **Autoresearch, with AI doing the loop and the review.** AI drove an eval-driven loop — run a population sweep, find a failure cluster, fix it, then check the eval set for regressions — round by round, and a separate reviewer session (a fresh AI reviewer, with no shared context) reviewed each round's output. My role was to watch the key metrics, discuss the important findings from each experiment, and make the final go / no-go call: a change was kept only when I was satisfied the independent signals held and nothing else regressed.

Every "passed" or "earned" claim was checked from the code — often by an independent AI reviewer — before it was kept.
