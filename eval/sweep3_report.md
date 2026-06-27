# Structural Sweep -- population robustness (UPPER BOUND, NOT accuracy)

Run: 2026-06-27 20:00 UTC. On-demand label-free sweep (`eval/structural_sweep.py`) over a pinned,
diverse stratified company sample. **structural-pass is an UPPER BOUND on robustness, NOT
accuracy** -- it catches gross failures (empty body, lead item dropped, no tiling,
implausible coverage) but is BLIND to interior boundary drift. The accuracy floor stays the
5 human-audited char-gold. REPORTED only: gates nothing, freezes no gold. Fast mode cannot
compute `needs_review`; flag-vs-silent on the fail tail comes from a separate full-pipeline
pass (see `sweep_fail_tail.md`).

- **HEADLINE -- full 10-K structural-pass: 605/656 (92.2%, 95% CI [89.9%, 94.0%])** (UPPER BOUND, not accuracy)
- 10-K/A amendments (separate stratum; legitimately lack Part I): 94/224 (42.0%, 95% CI [35.7%, 48.5%])
- Fetch/parse drops (logged, not silent): 0 of 880

## Full 10-K structural-pass by era (UPPER BOUND, not accuracy)

| era | pass / n (95% CI) |
|---|---|
| html | 336/369 (91.1%, 95% CI [87.7%, 93.6%]) |
| ixbrl | 115/120 (95.8%, 95% CI [90.6%, 98.2%]) |
| sgml | 154/167 (92.2%, 95% CI [87.1%, 95.4%]) |

## Full 10-K structural-pass by sector (UPPER BOUND, not accuracy)

| sector | pass / n (95% CI) |
|---|---|
| ? | 605/656 (92.2%, 95% CI [89.9%, 94.0%]) |

## Gross-failure tail -- full 10-K (51 of 656)

| accession | company | era | reason | items | cov | lead1 |
|---|---|---|---|---|---|---|
| 0000891020-08-000059 | NORTHRIM BANCORP INC | html | coverage:0.14 | 20 | 0.136 | True |
| 0000950137-08-004734 | PRINCIPAL LIFE INCOME FU | html | coverage:0.38 | 3 | 0.377 | False |
| 0001282695-10-000076 | CORTS TRUST II FOR FORD  | html | coverage:0.39 | 18 | 0.391 | True |
| 0001193125-15-113095 | CABCO SERIES 2004-101 TR | html | coverage:0.39 | 20 | 0.394 | True |
| 0001564590-19-005208 | AMERICA FIRST MULTIFAMIL | html | empty | 0 | 0.0 | False |
| 0000721371-23-000060 | CARDINAL HEALTH INC | ixbrl | empty | 0 | 0.0 | False |
| 0001564590-22-007615 | HANMI FINANCIAL CORP | ixbrl | empty | 0 | 0.0 | False |
| 0001564590-16-013066 | TRUSTMARK CORP | html | empty | 0 | 0.0 | False |
| 0001393905-10-000122 | WHITE DENTAL SUPPLY, INC | html | empty | 0 | 0.0 | False |
| 0001140361-08-013970 | YALE INDUSTRIAL PRODUCTS | html | empty | 0 | 0.0 | False |
| 0001140361-08-006920 | SYMYX TECHNOLOGIES INC | html | empty | 0 | 0.0 | False |
| 0001193125-06-080457 | TIVO INC | html | empty | 0 | 0.0 | False |
| 0001068238-05-000225 | STRUCTURED OBLIGATIONS C | html | empty | 0 | 0.0 | False |
| 0001393905-09-000129 | Commercial E-Waste Manag | html | empty | 0 | 0.0 | False |
| 0000950168-00-000727 | TWENTY SERVICES INC | sgml | empty | 0 | 0.0 | False |
| 0000804191-01-500004 | VALUE HOLDINGS INC | sgml | empty | 0 | 0.0 | False |
| 0001013255-00-000097 | NOMURA ASSET SECURITIES  | sgml | empty | 0 | 0.0 | False |
| 0000042293-95-000003 | GOLDEN WEST FINANCIAL CO | sgml | empty | 0 | 0.0 | False |
| 0001046375-00-500006 | ADVANCED TOBACCO PRODUCT | sgml | empty | 0 | 0.0 | False |
| 0000912057-00-009519 | BELLSOUTH TELECOMMUNICAT | sgml | empty | 0 | 0.0 | False |
| 0001005150-00-000896 | USA DIGITAL INC | sgml | empty | 0 | 0.0 | False |
| 0001193125-22-091063 | SANTANDER DRIVE AUTO REC | html | header:1 | 21 | 0.64 | True |
| 0001654954-19-002109 | ISSUER DIRECT CORP | html | lead_item_1_missing | 1 | 0.447 | False |
| 0001566011-20-000003 | PBF Holding Co LLC | html | lead_item_1_missing | 19 | 0.881 | False |
| 0001829126-23-003566 | KB Global Holdings Ltd | ixbrl | lead_item_1_missing | 15 | 0.817 | False |
| 0001193125-22-185030 | Nissan Auto Receivables  | html | lead_item_1_missing | 6 | 0.657 | False |
| 0001104659-25-023418 | Hyundai Auto Receivables | html | lead_item_1_missing | 5 | 0.633 | False |
| 0001213900-24-040541 | SAFE & GREEN HOLDINGS CO | ixbrl | lead_item_1_missing | 8 | 0.649 | False |
| 0001991774-25-000004 | Consumers 2023 Securitiz | html | lead_item_1_missing | 11 | 0.624 | False |
| 0001630924-19-000007 | CAPITAL AUTO RECEIVABLES | html | lead_item_1_missing | 5 | 0.691 | False |
| 0001437749-24-008777 | CREATIVE REALITIES, INC. | ixbrl | lead_item_1_missing | 8 | 0.676 | False |
| 0001565146-21-000010 | Gulf Coast Ultra Deep Ro | html | lead_item_1_missing | 19 | 0.585 | False |
| 0001387131-19-001900 | Western New England Banc | html | lead_item_1_missing | 10 | 0.632 | False |
| 0001003815-17-000002 | BCTC IV ASSIGNOR CORP | html | lead_item_1_missing | 14 | 0.596 | False |
| 0001144204-13-018370 | HYUNDAI ABS FUNDING CORP | html | lead_item_1_missing | 3 | 0.613 | False |
| 0001140361-11-017573 | TRIAD GUARANTY INC | html | lead_item_1_missing | 3 | 0.699 | False |
| 0000950123-11-030116 | First National Master No | html | lead_item_1_missing | 3 | 0.768 | False |
| 0001169232-05-001375 | TECHNITROL INC | html | lead_item_1_missing | 17 | 0.984 | False |
| 0000950144-08-001550 | Deerfield Capital Corp. | html | lead_item_1_missing | 13 | 0.673 | False |
| 0000950124-08-001630 | CAPITAL AUTO RECEIVABLES | html | lead_item_1_missing | 3 | 0.54 | False |
| 0000950134-06-001846 | CULLEN FROST BANKERS INC | html | lead_item_1_missing | 11 | 0.463 | False |
| 0000950137-06-003767 | PRINCIPAL LIFE INCOME FU | html | lead_item_1_missing | 6 | 0.444 | False |
| 0000950137-07-004855 | Principal Life Income Fu | html | lead_item_1_missing | 3 | 0.427 | False |
| 0000067716-07-000045 | MDU RESOURCES GROUP INC | html | lead_item_1_missing | 11 | 0.548 | False |
| 0001193125-07-042881 | VALERO GP HOLDINGS LLC | html | lead_item_1_missing | 17 | 0.825 | False |
| 0000950124-01-001548 | CONSUMERS ENERGY CO | sgml | lead_item_1_missing | 10 | 0.859 | False |
| 0000818089-98-000008 | NTS PROPERTIES PLUS LTD | sgml | lead_item_1_missing | 12 | 0.698 | False |
| 0000077242-97-000003 | PG ENERGY INC | sgml | lead_item_1_missing | 8 | 0.804 | False |
| 0000055458-00-000007 | KERR MCGEE CORP | sgml | lead_item_1_missing | 13 | 0.418 | False |
| 0001067310-99-000003 | DIRECTRIX INC | sgml | lead_item_1_missing | 12 | 0.827 | False |
| 0001058926-00-000002 | RURAL ELECTRIC COOPERATI | sgml | lead_item_1_missing | 7 | 0.935 | False |
