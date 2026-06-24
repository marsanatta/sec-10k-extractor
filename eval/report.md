# Evaluation Report

Run: 2026-06-24 23:46 Asia/Taipei. On-demand EDGAR batch (accession-pinned); NOT part of the offline unit
suite. A CURATED covering set that EXERCISES specific era/filer/structure/sector axes (NOT
a random sample) -- the per-bucket tables show WHICH axis breaks. The broad-population
fully-extracted estimate is the separate random diverse batch in ANALYSIS.md (~78%). RED =
known failures tracked on purpose, not papered over.

## Headline

- **Covering-set non-RED pass (recall=1.0): 14/14 (obs 1.00, 95% CI [0.78, 1.00])** (curated axes; population estimate ~78% is the random batch in ANALYSIS.md)
- **RED cases (tracked failures): bac-fy2023, scwo-fy2025-amend**
- Presence silent-failure rate (lower better): 0/16 (obs 0.00, 95% CI [0.00, 0.19])
- Boundary match-rate @ IoU>=0.9 vs audited gold: 1.0 over 5 gold filings (per-era; gold stays human-audited)
- Structural-ok: 16/16 (obs 1.00, 95% CI [0.81, 1.00])  |  Coverage-plausible: 14/16 (obs 0.88, 95% CI [0.64, 0.97])
- Needs-review (flagged): 15/16 (obs 0.94, 95% CI [0.72, 0.99])  |  Mean recall: 0.9062  |  N: 16

## Covering set (raw, per filing)

| filing | era | filer_type | sector | structure | items | start/4 | tier | recall | boundary | RED | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| apple-fy2024 | ixbrl | large_accelerated | technology | clean | 23 | 4/4 | regex | 1.0 | 1.0(4/4) |  | clean modern iXBRL |
| ko-fy2023 | ixbrl | large_accelerated | consumer_staples | clean | 23 | 4/4 | regex | 1.0 | 1.0(4/4) |  | clean modern iXBRL |
| msft-fy2023 | ixbrl | large_accelerated | technology | clean | 22 | 4/4 | regex | 1.0 | 1.0(4/4) |  | clean modern iXBRL |
| xom-fy2023 | ixbrl | large_accelerated | energy | clean | 22 | 4/4 | regex | 1.0 | - |  | energy, modern iXBRL |
| unh-fy2024 | ixbrl | large_accelerated | healthcare | clean | 23 | 4/4 | regex | 1.0 | - |  | healthcare, modern iXBRL |
| so-fy2023 | ixbrl | large_accelerated | utility | clean | 20 | 4/4 | regex | 1.0 | - |  | regulated utility, modern iXBRL |
| ge-fy2023 | ixbrl | large_accelerated | industrial | cross_reference_index | 23 | 4/4 | regex | 1.0 | - |  | cross-reference index; boundary ungoldable (see ANALYSIS) |
| ge-fy2009 | html | large_accelerated | industrial | collapsed_body | 16 | 4/4 | fallback | 1.0 | - |  | 2008-2012 HTML era; regex collapses Item 8 -> edgartools fallback recovers (regression anchor) |
| xom-fy2010 | html | large_accelerated | energy | html_era | 19 | 4/4 | regex | 1.0 | - |  | 2008-2012 HTML era, energy |
| m2i-fy2023 | ixbrl | smaller_reporting | small_cap | token_per_line_headers | 23 | 4/4 | regex | 1.0 | 1.0(2/2) |  | token-per-line 'Item\n1.' headers |
| scwo-fy2025 | ixbrl | smaller_reporting | clean_tech | token_per_line_headers | 21 | 4/4 | regex | 1.0 | - |  | SRC full 10-K; empty pre-fix, recovered by newline tolerance |
| jpm-fy2023 | ixbrl | large_accelerated | finance | scattered_item | 22 | 4/4 | regex | 1.0 | - |  | empty pre-fix (broken .text(), recovered by html-fallback). BUT Item 7 MD&A is SCATTERED: the span is a 396-char pointer stub; the real MD&A (Critical Accounting Estimates) is dropped -> scattered-item check RED. Tracked, not fixed (verification pass). |
| msft-fy1995 | sgml | legacy | technology | legacy_sgml | 14 | 3/4 | regex | 1.0 | 1.0(3/3) |  | pre-2001 SGML, no anchors |
| chemed-amend-fy2024 | ixbrl | large_accelerated | healthcare | amendment_10ka | 2 | 0/4 | regex | 1.0 | - |  | 10-K/A correctly handled as Part-III-only (expected_present empty) |
| bac-fy2023 | ixbrl | large_accelerated | finance | lead_item_drop | 14 | 2/4 | regex | 0.5 | - | **RED** | RED residual: extractor drops Item 1 (Business) and Item 7 (MD&A); flagged but recall < 1.0. NOT fixed this pass -- tracked. |
| scwo-fy2025-amend | ixbrl | smaller_reporting | clean_tech | amendment_10ka | 6 | 0/4 | regex | 0.0 | - | **RED** | RED residual: exposes the 10-K/A SELECTION issue -- if ticker-by-year grabs the /A (Part III only) instead of the 10-K you lose Part I-II. NOT fixed this pass -- tracked. |

## Per-bucket by era (which axis breaks)

| era | n | fully-extracted (recall=1.0) | RED |
|---|---|---|---|
| html | 2 | 2/2 | 0 |
| ixbrl | 13 | 11/13 | 2 |
| sgml | 1 | 1/1 | 0 |

## Per-bucket by structure (which axis breaks)

| structure | n | fully-extracted (recall=1.0) | RED |
|---|---|---|---|
| amendment_10ka | 2 | 1/2 | 1 |
| clean | 6 | 6/6 | 0 |
| collapsed_body | 1 | 1/1 | 0 |
| cross_reference_index | 1 | 1/1 | 0 |
| html_era | 1 | 1/1 | 0 |
| lead_item_drop | 1 | 0/1 | 1 |
| legacy_sgml | 1 | 1/1 | 0 |
| scattered_item | 1 | 1/1 | 0 |
| token_per_line_headers | 2 | 2/2 | 0 |

## Per-bucket by sector (which axis breaks)

| sector | n | fully-extracted (recall=1.0) | RED |
|---|---|---|---|
| clean_tech | 2 | 1/2 | 1 |
| consumer_staples | 1 | 1/1 | 0 |
| energy | 2 | 2/2 | 0 |
| finance | 2 | 1/2 | 1 |
| healthcare | 2 | 2/2 | 0 |
| industrial | 2 | 2/2 | 0 |
| small_cap | 1 | 1/1 | 0 |
| technology | 3 | 3/3 | 0 |
| utility | 1 | 1/1 | 0 |

## Scattered-item checks (item captured WHOLE, not just non-empty)

A late-MD&A probe must fall INSIDE the extracted item span; if it lands after the
span the tail was dropped (a non-contiguous-item failure even though the item is present).

| filing | item | tail probe | inside span? | verdict |
|---|---|---|---|---|
| jpm-fy2023 | 7 | Critical Accounting Estimates | False | **RED (tail dropped)** |
