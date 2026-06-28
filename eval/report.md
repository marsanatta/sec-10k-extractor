# Evaluation Report

Run: 2026-06-28 21:22 Asia/Taipei. On-demand EDGAR batch (accession-pinned); NOT part of the offline unit
suite. A CURATED covering set that EXERCISES specific era/filer/structure/sector axes (NOT
a random sample) -- the per-bucket tables show WHICH axis breaks. The broad-population
fully-extracted estimate is the separate random diverse batch in ANALYSIS.md (~78%). RED =
known failures tracked on purpose, not papered over.

## Headline

- **Covering-set non-RED pass (recall=1.0): 15/15 (obs 1.00, 95% CI [0.80, 1.00])** (curated axes; population estimate ~78% is the random batch in ANALYSIS.md)
- **RED cases (tracked failures): bac-fy2023, scwo-fy2025-amend, wmt-fy2003, amt-fy1997, ms-fy2024, hon-fy2024, oxy-fy2006, xom-fy2024, duk-fy2010, csco-fy2018, intc-fy2018, gis-fy2018**
- Presence silent-failure rate (lower better): 0/27 (obs 0.00, 95% CI [0.00, 0.12]) (PRESENCE-level only: missing gold keys; boundary-drift on present items is covered by the char-gold IoU, not this rate)
- Per-item status mismatches (era/by-ref/ABS vs human `expected_status`): 1/3 asserted statuses wrong
- Boundary match-rate @ IoU>=0.9 vs audited gold: 1.0 over 6 gold filings (per-era; gold stays human-audited)
- Structural-ok: 26/27 (obs 0.96, 95% CI [0.82, 0.99])  |  Coverage-plausible: 23/27 (obs 0.85, 95% CI [0.68, 0.94])
- Needs-review (flagged): 26/27 (obs 0.96, 95% CI [0.82, 0.99])  |  Mean recall: 0.8259  |  N: 27

## Covering set (raw, per filing)

| filing | era | filer_type | sector | structure | items | start/4 | tier | recall | boundary | RED | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| apple-fy2024 | ixbrl | large_accelerated | technology | clean | 23 | 4/4 | regex | 1.0 | 1.0(4/4) |  | clean modern iXBRL |
| ko-fy2023 | ixbrl | large_accelerated | consumer_staples | clean | 23 | 4/4 | regex | 1.0 | 1.0(4/4) |  | clean modern iXBRL |
| msft-fy2023 | ixbrl | large_accelerated | technology | clean | 22 | 4/4 | regex | 1.0 | 1.0(4/4) |  | clean modern iXBRL |
| xom-fy2023 | ixbrl | large_accelerated | energy | clean | 22 | 4/4 | regex | 1.0 | - |  | energy, modern iXBRL |
| unh-fy2024 | ixbrl | large_accelerated | healthcare | clean | 23 | 4/4 | regex | 1.0 | - |  | healthcare, modern iXBRL |
| so-fy2023 | ixbrl | large_accelerated | utility | clean | 23 | 4/4 | regex | 1.0 | - |  | regulated utility, modern iXBRL |
| ge-fy2023 | ixbrl | large_accelerated | industrial | cross_reference_index | 23 | 4/4 | regex | 1.0 | - |  | cross-reference index; boundary ungoldable (see ANALYSIS) |
| ge-fy2009 | html | large_accelerated | industrial | collapsed_body | 19 | 4/4 | regex | 1.0 | - |  | 2008-2012 HTML era; regex collapses Item 8 -> edgartools fallback recovers (regression anchor) |
| xom-fy2010 | html | large_accelerated | energy | html_era | 19 | 4/4 | regex | 1.0 | - |  | 2008-2012 HTML era, energy |
| m2i-fy2023 | ixbrl | smaller_reporting | small_cap | token_per_line_headers | 23 | 4/4 | regex | 1.0 | 1.0(2/2) |  | token-per-line 'Item\n1.' headers |
| scwo-fy2025 | ixbrl | smaller_reporting | clean_tech | token_per_line_headers | 21 | 4/4 | regex | 1.0 | - |  | SRC full 10-K; empty pre-fix, recovered by newline tolerance |
| jpm-fy2023 | ixbrl | large_accelerated | finance | scattered_item | 21 | 4/4 | regex | 1.0 | - |  | empty pre-fix (broken .text(), recovered by html-fallback). BUT Item 7 MD&A is SCATTERED: the span is a 396-char pointer stub; the real MD&A (Critical Accounting Estimates) is dropped -> scattered-item check RED. Tracked, not fixed (verification pass). |
| msft-fy1995 | sgml | legacy | technology | legacy_sgml | 14 | 3/4 | regex | 1.0 | 1.0(3/3) |  | pre-2001 SGML, no anchors |
| chemed-amend-fy2024 | ixbrl | large_accelerated | healthcare | amendment_10ka | 2 | 0/4 | regex | 1.0 | - |  | 10-K/A correctly handled as Part-III-only (expected_present empty) |
| bac-fy2023 | ixbrl | large_accelerated | finance | lead_item_drop | 2 | 2/4 | regex | 0.25 | - | **RED** | RED residual: extractor drops Item 1 (Business) and Item 7 (MD&A); flagged but recall < 1.0. NOT fixed this pass -- tracked. |
| scwo-fy2025-amend | ixbrl | smaller_reporting | clean_tech | amendment_10ka | 6 | 0/4 | regex | 0.0 | - | **RED** | RED residual: exposes the 10-K/A SELECTION issue -- if ticker-by-year grabs the /A (Part III only) instead of the 10-K you lose Part I-II. NOT fixed this pass -- tracked. |
| msft-fy1996 | sgml | legacy | technology | legacy_sgml | 14 | 3/4 | regex | 1.0 | - |  | Probe-a eval growth (round 1): 2nd pre-2001 SGML data point after msft-fy1995; clean structural-pass on current code (items 1/7/8 header-anchored, coverage 0.93). |
| wmt-fy2003 | html | large_accelerated | retail | part_glued_lead_item | 13 | 2/4 | regex | 0.8 | - | **RED** | Probe-a eval growth (round 1): fills retail sector + 2001-2008 HTML era. RED: Item 1 dropped because 'PART I ITEM 1.' shares one physical line, defeating the line-start anchor (Item 1A legitimately absent pre-2005). FLAGGED (needs_review), not silent. |
| amt-fy1997 | sgml | legacy | reit | collapsed_body | 1 | 0/4 | regex | 0.0 | - | **RED** | Probe-c sweep (round 1): collapsed-body SGML reit -- one item swallows the doc (cov 0.95), lead Item 1 absent. Confirmation of the GE-class B2 collapsed-body across a new era/sector. FLAGGED (needs_review), not silent. |
| ms-fy2024 | ixbrl | large_accelerated | finance | header_text_stripped_ixbrl | 0 | 0/4 | regex | 0.0 | - | **RED** | Probe-c sweep (round 1): NAMED CEILING (S1). 'Item N' labels live only in styled iXBRL spans .text() flattens -> 0 items via regex AND edgartools fallback (both header-anchored = dual-extractor common-mode B3). FLAGGED (0 items, needs_review). Unrecoverable without a decorrelated non-header/CRF extractor (out of 4-day scope). |
| hon-fy2024 | ixbrl | large_accelerated | industrial | no_separator_headers | 9 | 0/4 | fallback | 0.5 | - | **RED** | Probe-c sweep (round 1): no-separator header 'ITEM 1  Title' -> regex finds 0; edgartools fallback partially rescues (7 items) but structural_ok=False and lead Item 1 dropped. FLAGGED (needs_review), not silent. |
| oxy-fy2006 | html | large_accelerated | energy | separator_less_header | 13 | 3/4 | regex | 0.75 | - | **RED** | Round-4 A1 RED anchor (empty cluster). RED: house-style headers carry NO separator after the number ('ITEM 1A RISK FACTORS', 'ITEM
7

Management'), so _HEADER_RE matches 0 -> segment() empty. PROPOSED expected_present pending human audit. CAVEAT: Item 1 heading is COMBINED 'ITEMS 1 AND 2 BUSINESS AND PROPERTIES' (no standalone Item 2); Item 7A folded into Item 7 (no standalone heading). A1 must flip this RED->GREEN. |
| xom-fy2024 | ixbrl | large_accelerated | energy | crossref_intruder_lead_drop | 22 | 4/4 | regex | 1.0 | - | **RED** | Round-4 A2 RED anchor (lead_missing_high_cov). RED: an in-prose 'see Item 1A. Risk Factors' cross-reference inside Item 1 prose is mis-matched as a header, _split_runs severs the run, _pick_body_run picks the downstream run starting at 1A -> Item 1 dropped (coverage ~0.9). Item 6 legitimately absent ('[Reserved]' era). A2 must flip RED->GREEN; char-gold Item-1 span must stay byte-exact. |
| duk-fy2010 | html | large_accelerated | utility | crossref_regsx_false_header | 19 | 4/4 | regex | 1.0 | - | **RED** | Round-4 A2 RED anchor (coverage_partial). RED: 'Item 4-08(g)' (a Regulation S-X citation inside Item 8) is mis-matched as an Item-4 header (because _SEP includes '-'), anchoring a back-half run that out-scores the real front-half body on max-prose -> only ~39.6% covered, Items 1/1A/7/8 uncovered. FLAGGED (needs_review=True), NOT silent. A2 must flip RED->GREEN. |
| csco-fy2018 | html | large_accelerated | technology | run_fragmentation_lead_drop | 20 | 4/4 | regex | 1.0 | - | **RED** | Round-4 PINNED RED anchor (lead_missing_low_cov = run-fragmentation, a KNOWN class named in rounds 1-2). NOT an A1/A2 fix target this round -> EXPECTED TO STAY RED; pinned so any future change is measured and so G9 has it as a known-failing baseline. |
| intc-fy2018 | html | large_accelerated | technology | crossref_index | 21 | 4/4 | regex | 1.0 | - | **RED** | Round-4 PINNED RED anchor (cross-reference-INDEX-TABLE class: body has NO 'Item N' headings; items located only via an end-of-doc 'FORM 10-K CROSS-REFERENCE INDEX' mapping item->page). HUMAN-AUDITED: the items ARE PRESENT (interpretation A) -> this is a REAL extraction miss, not legitimate absence. NOT an A1/A2/A3 target this round (header-anchored tiers structurally cannot find headingless body items); EXPECTED TO STAY RED until the index-table handler is built (plan: research/todo-exploration-crossref-index-handling.md). ~1% of the 1656 sweep, concentrated in GE/MCD/HON/INTC. |
| gis-fy2018 | html | large_accelerated | consumer_staples | separator_less_header | 19 | 4/4 | regex | 1.0 | 1.0(4/4) | **RED** | Round-4 A1 RED anchor WITH human-audited char-gold (boundary_gold.json gis-fy2018, frozen 2026-06-27). Clean STANDALONE separator-less headers (ITEM 1 / ITEM 1A / ITEM 7 / ITEM 8) -> segment() currently returns 0 (empty). A1 must flip RED->GREEN AND hit the char-gold at IoU 1.0. |

## Per-bucket by era (which axis breaks)

| era | n | fully-extracted (recall=1.0) | RED |
|---|---|---|---|
| html | 8 | 6/8 | 6 |
| ixbrl | 16 | 12/16 | 5 |
| sgml | 3 | 2/3 | 1 |

## Per-bucket by structure (which axis breaks)

| structure | n | fully-extracted (recall=1.0) | RED |
|---|---|---|---|
| amendment_10ka | 2 | 1/2 | 1 |
| clean | 6 | 6/6 | 0 |
| collapsed_body | 2 | 1/2 | 1 |
| cross_reference_index | 1 | 1/1 | 0 |
| crossref_index | 1 | 1/1 | 1 |
| crossref_intruder_lead_drop | 1 | 1/1 | 1 |
| crossref_regsx_false_header | 1 | 1/1 | 1 |
| header_text_stripped_ixbrl | 1 | 0/1 | 1 |
| html_era | 1 | 1/1 | 0 |
| lead_item_drop | 1 | 0/1 | 1 |
| legacy_sgml | 2 | 2/2 | 0 |
| no_separator_headers | 1 | 0/1 | 1 |
| part_glued_lead_item | 1 | 0/1 | 1 |
| run_fragmentation_lead_drop | 1 | 1/1 | 1 |
| scattered_item | 1 | 1/1 | 0 |
| separator_less_header | 2 | 1/2 | 2 |
| token_per_line_headers | 2 | 2/2 | 0 |

## Per-bucket by sector (which axis breaks)

| sector | n | fully-extracted (recall=1.0) | RED |
|---|---|---|---|
| clean_tech | 2 | 1/2 | 1 |
| consumer_staples | 2 | 2/2 | 1 |
| energy | 4 | 3/4 | 2 |
| finance | 3 | 1/3 | 2 |
| healthcare | 2 | 2/2 | 0 |
| industrial | 3 | 2/3 | 1 |
| reit | 1 | 0/1 | 1 |
| retail | 1 | 0/1 | 1 |
| small_cap | 1 | 1/1 | 0 |
| technology | 6 | 6/6 | 2 |
| utility | 2 | 2/2 | 1 |

## Scattered-item checks (item captured WHOLE, not just non-empty)

A late-MD&A probe must fall INSIDE the extracted item span; if it lands after the
span the tail was dropped (a non-contiguous-item failure even though the item is present).

| filing | item | tail probe | inside span? | verdict |
|---|---|---|---|---|
| jpm-fy2023 | 7 | Critical Accounting Estimates | False | **RED (tail dropped)** |

## Signal D -- classification-correctness (REPORTED, non-gating)

Per-item production status vs the FROZEN human-audited reference
`eval/classification_gold.json` (heading-exists rule). Reported only -- it gates nothing,
never feeds `needs_review`, never regenerates the gold. Mismatches = where production
disagrees with the human truth (proof the reference is an independent ruler).

| filing | form | Signal D | mismatched cells |
|---|---|---|---|
| apple-fy2024 | 10-K | 23/23 | none |
| msft-fy2023 | 10-K | 22/23 | 1C |
| chemed-amend-fy2024 | 10-K/A | 23/23 | none |
| scwo-fy2025-amend | 10-K/A | 23/23 | none |
| msft-fy1996 | 10-K | 20/23 | 7A, 9A, 15 |

## LLM escalation token ledger (measured)

Index-don't-generate: $0/0-token on the cooperative path; the LLM fires only on the
confidence-gated escalation minority. Calls are made for present low-confidence
boundaries (the LIB prompt indexes around an existing span); missing-item 'find'
escalation is a separate, unbuilt path and is not called here.

Provider = `deferred`. **Escalation NOT exercised on this set** -- the client is the deferred stub, so triggers fire and candidates are recorded but no LLM call is made: calls/tokens are a measured 0, not an estimate. Wire a real client (GitHub Copilot SDK) to populate these columns.

| filing | escalation candidates | calls | input tokens | output tokens | performed |
|---|---|---|---|---|---|
| apple-fy2024 | 1 | 0 | 0 | 0 | False |
| ko-fy2023 | 3 | 0 | 0 | 0 | False |
| msft-fy2023 | 11 | 0 | 0 | 0 | False |
| xom-fy2023 | 2 | 0 | 0 | 0 | False |
| unh-fy2024 | 4 | 0 | 0 | 0 | False |
| so-fy2023 | 3 | 0 | 0 | 0 | False |
| ge-fy2023 | 23 | 0 | 0 | 0 | False |
| ge-fy2009 | 9 | 0 | 0 | 0 | False |
| xom-fy2010 | 5 | 0 | 0 | 0 | False |
| m2i-fy2023 | 6 | 0 | 0 | 0 | False |
| scwo-fy2025 | 4 | 0 | 0 | 0 | False |
| jpm-fy2023 | 5 | 0 | 0 | 0 | False |
| msft-fy1995 | 6 | 0 | 0 | 0 | False |
| chemed-amend-fy2024 | 2 | 0 | 0 | 0 | False |
| bac-fy2023 | 12 | 0 | 0 | 0 | False |
| scwo-fy2025-amend | 4 | 0 | 0 | 0 | False |
| msft-fy1996 | 6 | 0 | 0 | 0 | False |
| wmt-fy2003 | 8 | 0 | 0 | 0 | False |
| amt-fy1997 | 12 | 0 | 0 | 0 | False |
| ms-fy2024 | 12 | 0 | 0 | 0 | False |
| hon-fy2024 | 16 | 0 | 0 | 0 | False |
| oxy-fy2006 | 9 | 0 | 0 | 0 | False |
| xom-fy2024 | 2 | 0 | 0 | 0 | False |
| duk-fy2010 | 7 | 0 | 0 | 0 | False |
| csco-fy2018 | 5 | 0 | 0 | 0 | False |
| intc-fy2018 | 21 | 0 | 0 | 0 | False |
| gis-fy2018 | 5 | 0 | 0 | 0 | False |
| **total** | 203 | 0 | 0 | 0 | False |
