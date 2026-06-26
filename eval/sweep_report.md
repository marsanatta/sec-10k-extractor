# Structural Sweep -- population robustness (UPPER BOUND, NOT accuracy)

Run: 2026-06-26 11:20 UTC. On-demand label-free sweep (`eval/structural_sweep.py`) over a pinned,
diverse stratified company sample. **structural-pass is an UPPER BOUND on robustness, NOT
accuracy** -- it catches gross failures (empty body, lead item dropped, no tiling,
implausible coverage) but is BLIND to interior boundary drift. The accuracy floor stays the
5 human-audited char-gold. REPORTED only: gates nothing, freezes no gold. Fast mode cannot
compute `needs_review`; flag-vs-silent on the fail tail comes from a separate full-pipeline
pass (see `sweep_fail_tail.md`).

- **HEADLINE -- full 10-K structural-pass: 376/423 (88.9%, 95% CI [85.5%, 91.5%])** (UPPER BOUND, not accuracy)
- 10-K/A amendments (separate stratum; legitimately lack Part I): 6/40 (15.0%, 95% CI [7.1%, 29.1%])
- Fetch/parse drops (logged, not silent): 8 of 471

## Full 10-K structural-pass by era (UPPER BOUND, not accuracy)

| era | pass / n (95% CI) |
|---|---|
| html | 232/257 (90.3%, 95% CI [86.0%, 93.3%]) |
| ixbrl | 82/99 (82.8%, 95% CI [74.2%, 89.0%]) |
| sgml | 62/67 (92.5%, 95% CI [83.7%, 96.8%]) |

## Full 10-K structural-pass by sector (UPPER BOUND, not accuracy)

| sector | pass / n (95% CI) |
|---|---|
| auto | 9/9 (100.0%, 95% CI [70.1%, 100.0%]) |
| consumer_staples | 47/52 (90.4%, 95% CI [79.4%, 95.8%]) |
| energy | 27/38 (71.1%, 95% CI [55.2%, 83.0%]) |
| finance | 40/46 (87.0%, 95% CI [74.3%, 93.9%]) |
| healthcare | 52/54 (96.3%, 95% CI [87.5%, 99.0%]) |
| industrial | 45/55 (81.8%, 95% CI [69.7%, 89.8%]) |
| materials | 15/15 (100.0%, 95% CI [79.6%, 100.0%]) |
| retail | 45/49 (91.8%, 95% CI [80.8%, 96.8%]) |
| technology | 59/65 (90.8%, 95% CI [81.3%, 95.7%]) |
| telecom_media | 18/19 (94.7%, 95% CI [75.4%, 99.1%]) |
| utility | 19/21 (90.5%, 95% CI [71.1%, 97.3%]) |

## Gross-failure tail -- full 10-K (47 of 423)

| accession | company | era | reason | items | cov | lead1 |
|---|---|---|---|---|---|---|
| 0000050863-22-000007 | INTC | ixbrl | coverage:0.01 | 22 | 0.015 | True |
| 0000050863-25-000009 | INTC | ixbrl | coverage:0.01 | 23 | 0.015 | True |
| 0000040545-22-000008 | GE | ixbrl | coverage:0.01 | 22 | 0.012 | True |
| 0000040545-16-000145 | GE | html | coverage:0.01 | 20 | 0.007 | True |
| 0000040545-19-000014 | GE | html | coverage:0.01 | 21 | 0.006 | True |
| 0000040545-25-000015 | GE | ixbrl | coverage:0.01 | 23 | 0.014 | True |
| 0000050863-19-000007 | INTC | html | coverage:0.02 | 21 | 0.016 | True |
| 0000797468-13-000011 | OXY | html | coverage:0.07 | 9 | 0.071 | False |
| 0000732717-04-000205 | T | html | coverage:0.37 | 14 | 0.371 | False |
| 0001140361-10-007923 | TXN | html | empty | 0 | 0.0 | False |
| 0000950131-97-001484 | USB | sgml | empty | 0 | 0.0 | False |
| 0000950137-02-000971 | USB | html | empty | 0 | 0.0 | False |
| 0000950134-04-002667 | USB | html | empty | 0 | 0.0 | False |
| 0000950124-07-001116 | USB | html | empty | 0 | 0.0 | False |
| 0000950130-00-001710 | SLB | sgml | empty | 0 | 0.0 | False |
| 0000797468-04-000033 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-01-500004 | OXY | sgml | empty | 0 | 0.0 | False |
| 0000797468-07-000027 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-10-000020 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-16-000017 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-19-000004 | OXY | html | empty | 0 | 0.0 | False |
| 0001193125-18-209377 | GIS | html | empty | 0 | 0.0 | False |
| 0000950123-09-021887 | GIS | html | empty | 0 | 0.0 | False |
| 0001193125-12-293636 | GIS | html | empty | 0 | 0.0 | False |
| 0001193125-15-245476 | GIS | html | empty | 0 | 0.0 | False |
| 0000773840-22-000018 | HON | ixbrl | empty | 0 | 0.0 | False |
| 0000773840-25-000010 | HON | ixbrl | empty | 0 | 0.0 | False |
| 0000063908-22-000011 | MCD | ixbrl | empty | 0 | 0.0 | False |
| 0000063908-25-000012 | MCD | ixbrl | empty | 0 | 0.0 | False |
| 0001564590-22-006589 | D | ixbrl | empty | 0 | 0.0 | False |
| 0000912057-99-007381 | COST | sgml | header:1 | 14 | 0.967 | True |
| 0000858877-18-000011 | CSCO | html | lead_item_1_missing | 12 | 0.566 | False |
| 0000858877-21-000013 | CSCO | ixbrl | lead_item_1_missing | 13 | 0.67 | False |
| 0000070858-22-000062 | BAC | ixbrl | lead_item_1_missing | 14 | 0.611 | False |
| 0000070858-25-000139 | BAC | ixbrl | lead_item_1_missing | 14 | 0.606 | False |
| 0000034088-25-000010 | XOM | ixbrl | lead_item_1_missing | 19 | 0.923 | False |
| 0000797468-22-000008 | OXY | ixbrl | lead_item_1_missing | 13 | 0.937 | False |
| 0000797468-25-000029 | OXY | ixbrl | lead_item_1_missing | 20 | 0.933 | False |
| 0000950123-10-018679 | MRK | html | lead_item_1_missing | 12 | 0.466 | False |
| 0000014272-22-000051 | BMY | ixbrl | lead_item_1_missing | 17 | 0.678 | False |
| 0000077476-22-000010 | PEP | ixbrl | lead_item_1_missing | 17 | 0.77 | False |
| 0000040545-10-000010 | GE | html | lead_item_1_missing | 11 | 0.558 | False |
| 0000040545-13-000036 | GE | html | lead_item_1_missing | 18 | 0.892 | False |
| 0001104659-10-007295 | MMM | html | lead_item_1_missing | 19 | 0.939 | False |
| 0000950117-01-000640 | HON | sgml | lead_item_1_missing | 8 | 0.65 | False |
| 0000104169-03-000005 | WMT | html | lead_item_1_missing | 13 | 0.474 | False |
| 0001326160-13-000009 | DUK | html | lead_item_1_missing | 18 | 0.894 | False |

## Dropped (fetch/parse error, 8)

| accession | error |
|---|---|
| 0000070858-13-000097 | TIMEOUT after 90s (wedged fetch/parse/segment) |
| 0000070858-16-000137 | TIMEOUT after 90s (wedged fetch/parse/segment) |
| 0000092122-13-000014 | TIMEOUT after 90s (wedged fetch/parse/segment) |
| 0000092122-16-000126 | TIMEOUT after 90s (wedged fetch/parse/segment) |
| 0000092122-19-000006 | TIMEOUT after 90s (wedged fetch/parse/segment) |
| 0000950123-94-002010 | UnicodeEncodeError: 'charmap' codec can't encode character '\u26a0' in position  |
| 0000732712-22-000008 | TIMEOUT after 90s (wedged fetch/parse/segment) |
| 0000950123-06-009854 | TIMEOUT after 90s (wedged fetch/parse/segment) |
