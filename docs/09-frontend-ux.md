# Frontend / Inspection UX (Design)

The assignment requires a publicly accessible web frontend where reviewers can submit or
select a filing, inspect extracted items, and **understand extraction confidence and
failure cases**. This is design-led (synthesised from the requirements + the confidence
model in `06-confidence-and-silent-failure.md`), not a literature item.

## User flows

1. **Select a filing** — by ticker/CIK + fiscal year, or paste an EDGAR accession/URL.
   Backend resolves to the primary document (`01-edgar-access-and-formats.md` path) and
   serves cached results if the accession was processed before.
2. **Run / load extraction** — show progress (resolve → normalize → segment → validate).
3. **Inspect items** — canonical Part I–IV / Item 1–16 navigator; click an item to read
   its extracted text with the source boundary highlighted.
4. **Understand confidence & failures** — filing-level summary + per-item bands with the
   *signals that fired* (provenance, never a bare number).

## Key components

- **Item navigator** — the canonical 16-item template rendered as a checklist, each item
  colour-coded: present-high / present-medium / present-flagged / legitimately-absent /
  extraction-failure. This makes "what's missing and why" the first thing reviewers see.
- **Boundary viewer** — extracted item text alongside the raw document with the
  start/end offsets highlighted, so a wrong boundary is visible, not hidden.
- **Confidence panel (per item)** — the checks from doc 06 with pass/fail: structural
  invariants, round-trip coverage, dual-extractor agreement (with the offset delta),
  XBRL Item-8 cross-check, content heuristics. Expandable "why this confidence".
- **Failure inspector** — lists flagged items with reason codes and cleanly separates
  `legitimately-absent` (DEI/template says optional or incorporated-by-reference) from
  `extraction-failure` (expected but not found). Disagreements show both extractors.
- **Examples gallery** — links the "works well" and "still hard" filings from
  `08-eval-set-construction.md` so reviewers can reproduce both success and failure.

## Tech-stack options (tradeoff)

| Option | Pros | Cons | Fit |
|--------|------|------|-----|
| **Streamlit / Gradio** | same language as pipeline, deploys to HF Spaces/Zeabur in minutes | limited control over boundary-highlight UX | fastest path; good enough for inspection |
| **FastAPI + minimal React/Next** | clean extraction API + full control over diff/highlight views | more build effort | best for the boundary viewer; recommended if time allows |

**Recommendation:** FastAPI backend exposing `POST /extract` → structured items + confidence
JSON, with a light React/Next frontend for the boundary-highlight view. If time-boxed,
ship Streamlit first (it can render the navigator + confidence panel adequately) and
upgrade the viewer later. Either way the API is the contract; the UI is a thin client.

## Deployment & cost

- Deploy to Zeabur / HF Spaces / Render with a public URL.
- Cache extraction results by accession (filings are immutable) → repeat views are free.
- Server-side EDGAR fetch honours 10 req/s + descriptive User-Agent.
- Pre-warm the cache for the eval-set filings so reviewer demos are instant.

## Maps to grading

Surfaces per-filing + per-item confidence, lets reviewers inspect any item's boundary,
shows failures honestly (legitimately-absent vs failure), and links concrete
works-well / still-hard examples — exactly the "inspect extracted items, understand
confidence or failure cases" requirement.
