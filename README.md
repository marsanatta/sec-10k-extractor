# SEC 10-K Item-level Structured Extractor

Extracts the individual SEC-specified items (Items 1–16 across Parts I–IV) from a raw 10-K filing
so each can be consumed independently — robust across the three format eras (legacy SGML, HTML,
modern iXBRL), self-verifying **without a public filing-level answer key**, and honest about where
it fails.

**Design in one line: _index, don't generate._** An item is a `char_range` into the filing's
canonical text — never LLM free-text — so every item round-trips back to the source bytes exactly.
A deterministic regex/anchor tier segments ~100% of the common case at **\$0 inference**; a
**validation layer** attaches calibrated confidence + provenance to every item and is the real
product (no existing segmenter emits confidence); an LLM tier is reserved for the
low-confidence-boundary minority and is deliberately deferred for cost discipline.

Full numbers, tradeoffs, and the verification story are in **[`ANALYSIS.md`](ANALYSIS.md)**.

---

## Live frontend

The web UI (submit/select a filing → inspect extracted items → see the source highlight,
calibrated confidence, which validation checks fired, and legitimate-absence vs extraction-failure)
is served by the dockerized app behind a **Cloudflare quick tunnel**. The public
`https://<…>.trycloudflare.com` URL is **ephemeral** (it rotates when the tunnel restarts), so it
is provided with the submission rather than hardcoded here; to mint your own, see
[Run it](#run-it) and read the URL from `docker compose logs cloudflared`.

The curated demo filings in the UI are **open** (no token). Free-form extraction (arbitrary
ticker/accession, or pasting filing text for mutation testing) is gated by an optional shared token
(`SEC10K_ACCESS_TOKEN`) so a public URL can't be used to hammer SEC's rate limit.

---

## Run it

**Prerequisite — SEC User-Agent.** SEC EDGAR requires a descriptive `User-Agent` (a name + email)
on every request. Copy `.env.example` to `.env` and set it:

```bash
cp .env.example .env
# .env:  SEC_EDGAR_USER_AGENT="Your Name you@example.com"
```

### A. Docker + public tunnel (what the frontend uses)

```bash
docker compose up --build            # app on :8000 + a Cloudflare quick tunnel
docker compose logs cloudflared      # read the public https://<…>.trycloudflare.com URL
```

### B. Local dev

```bash
pip install -e ".[api,dev]"
( cd web && npm install && npm run build )          # build the SPA into web/dist
SEC_EDGAR_USER_AGENT="Your Name you@example.com" uvicorn api.server:app --port 8000
# open http://localhost:8000
```

### C. Tests and the evaluation harness

```bash
python -m pytest -q                  # 73 offline unit tests — network-free, no User-Agent needed
SEC_EDGAR_USER_AGENT="Your Name you@example.com" python eval/run_eval.py   # on-demand EDGAR batch -> eval/report.md
```

The unit suite (incl. a boundary mutation battery, the escalation token ledger, and the Signal D
independence guard) is **fixture-based and never touches the network**. `eval/run_eval.py` is the
on-demand, accession-pinned batch that fetches from EDGAR and regenerates `eval/report.md`.

---

## What it produces

Per item: `{ item_id, part, item, title, text, char_range, status, confidence{band, score,
signals[]}, provenance{extractors[], checks_passed[], checks_failed[]} }`, plus a filing-level
summary (`needs_review`, coverage, the oracle/cross-check signals, the escalation ledger). `status`
is one of `present` / `legitimately_absent` / `extraction_failure` — a missing item is **classified,
never silently dropped**.

---

## Key design decisions

- **Index, don't generate.** Items are byte ranges into the canonical text; round-trip
  reconstruction is an enforced invariant, so coverage is provable.
- **Layered ensemble, LLM last.** Regex/anchor segmentation is **primary** (\$0, ~100% of the
  cooperative case). A **conservative** `edgartools` fallback recovers empty/collapsed segmentations
  by locating item heads back in our canonical (never copying foreign offsets). An
  **index-don't-generate LLM escalation** tier (windowed, closed item set, returns a line number that
  is mapped back to a char offset and *applied* to move the boundary) is wired and tested but its
  **provider stays deferred** for cost discipline — so measured token cost is **\$0**, with the
  capability ready the moment a provider is connected.
- **The validation layer is the product.** Every item carries calibrated confidence + provenance;
  a filing is allowed to be wrong **only if it says so** (`needs_review`). The headline metric is the
  silent-failure rate, not accuracy.
- **Verify without public ground truth — independent oracles only** (detail in
  [`ANALYSIS.md` §5](ANALYSIS.md)): structural invariants + byte-exact round-trip (100% scope) →
  independent dual-extractor boundary cross-check → a decorrelated third source (`edgar-corpus`) →
  **char-exact human-audited boundary gold (5 filings, never auto-frozen)** → XBRL Item-8 oracle from
  the companyfacts API → **Signal D**, a human-audited, frozen per-form-type **classification** gold
  that independently catches real production errors. A **mutation battery** validates the validators.
- **Cost discipline by construction.** Deterministic tier does the work; the LLM touches only
  flagged boundaries on a cleaned window; results cache by accession (filings are immutable); EDGAR
  politeness (10 req/s + descriptive UA) is honored.

---

## Works well vs. still difficult (concrete cases)

These are **measured on an accession-pinned, immutable eval set** (`eval/eval_set.json`); the full
per-bucket table and failure analysis are in [`ANALYSIS.md` §2/§6](ANALYSIS.md).

**Works well (examples):**
- **Clean modern iXBRL** — Apple FY2024, Coca-Cola FY2023, Microsoft FY2023 (all items found,
  char-exact boundary gold 1.0).
- **Legacy SGML** — Microsoft FY1995/FY1996 (the pre-2001 era; FY1995 carries human-audited gold).
- **Collapsed body recovered via the fallback** — GE FY2009 (regex collapses → `edgartools`
  fallback tiles 16 items).
- **2001–2008 HTML and earlier middle eras** — covered post-round-1 (e.g. XOM FY2010).

**Still difficult / unreliable / unsupported (tracked, flagged — never silent):**
- **Dual-extractor common-mode — the named ceiling.** Morgan Stanley / Citigroup FY2024: the
  "Item N" labels live only in styled iXBRL spans that flatten away, so the regex **and** the
  `edgartools` fallback (both header-anchored) find **0 items**. Flagged, but unrecoverable without a
  decorrelated non-header / CRF extractor (out of scope).
- **Cross-reference index — GE FY2023.** Integrated MD&A + out-of-order item references → ~1.3%
  coverage; caught (`needs_review`), but not char-goldable by hand.
- **Scattered item — JPMorgan FY2023 Item 7.** A pointer-stub Item 7 whose real MD&A falls outside
  the span (tail dropped); invisible to recall, caught by a dedicated scattered-item probe.
- **Lead-item drops** — Bank-of-America FY2023 (run-fragmentation), WMT FY2003 (`PART I ITEM 1.`
  glued on one line), Honeywell FY2024 (no-separator headers).
- **Filing selection** — a ticker-by-year lookup can return a 10-K/A amendment instead of the full
  10-K; the eval pins the full filing by accession.

Every one of these is **flagged** (`needs_review`); the measured silent-failure rate is **0**.

---

## Cost, scalability, correctness

See [`ANALYSIS.md`](ANALYSIS.md): §3 (per-filing cost — deterministic tier \$0, escalation a
measured \$0 while deferred, projected ≈\$0.001–0.002/filing if wired), §4 (scalability — O(n)
stateless per filing, cache by accession, EDGAR rate limit is the real cap), §5 (the verification
tower), §6 (failure modes), §9 (the autoresearch close-out).

---

## Where AI helped

This repo was built in an AI-amplified workflow; the trail is first-class, not an afterthought:
- **[`prompts/`](prompts/)** — the key prompts, dated, verbatim, with a short "what I did" per
  record (planning, the Docker/frontend builds, the boundary-gold audit, each autoresearch round).
- **[`research/`](research/)** — the eval-driven **Modify→Verify→Keep/Discard autoresearch** rounds
  that hardened the system: round 1 (eval growth, the escalation apply-loop, the named-ceiling
  discovery, and an **honest anti-Goodhart discard**) and round 2 (building **Signal D** — an
  independent, human-audited classification ruler — and only *then* earning the form-aware template
  fix the discard had deferred). Each round logs findings + an append-only machine ledger.
- Reviewer discipline (verify-from-code, prove-independence-by-live-disagreement) was applied to
  every "passed / green / earned" claim before it was kept.

---

## Repo layout

```
sec10k/      pipeline: ingest -> normalize (canonical + offsets) -> segment -> validate -> schema
api/         FastAPI server (extract / demo / paste-text / eval report) + token gate
web/         React + Vite dark-theme frontend (item navigator, boundary viewer, confidence panel)
eval/        accession-pinned eval set, run_eval.py, boundary_gold.json + classification_gold.json (human-audited)
tests/       offline, network-free unit + mutation/independence-guard tests
docs/        design + grounding docs
prompts/     dated, verbatim key prompts (AI-collaboration trail)
research/     autoresearch round findings + append-only progress ledgers
ANALYSIS.md  the analysis report (performance, cost, scalability, verification, failure modes)
```

SEC filings are public-domain U.S. government data.
