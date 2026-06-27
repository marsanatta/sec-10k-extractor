# Structural Sweep -- population robustness (UPPER BOUND, NOT accuracy)

Run: 2026-06-27 10:56 UTC. On-demand label-free sweep (`eval/structural_sweep.py`) over a pinned,
diverse stratified company sample. **structural-pass is an UPPER BOUND on robustness, NOT
accuracy** -- it catches gross failures (empty body, lead item dropped, no tiling,
implausible coverage) but is BLIND to interior boundary drift. The accuracy floor stays the
5 human-audited char-gold. REPORTED only: gates nothing, freezes no gold. Fast mode cannot
compute `needs_review`; flag-vs-silent on the fail tail comes from a separate full-pipeline
pass (see `sweep_fail_tail.md`).

- **HEADLINE -- full 10-K structural-pass: 602/644 (93.5%, 95% CI [91.3%, 95.1%])** (UPPER BOUND, not accuracy)
- 10-K/A amendments (separate stratum; legitimately lack Part I): 75/238 (31.5%, 95% CI [25.9%, 37.7%])
- Fetch/parse drops (logged, not silent): 0 of 883

## Full 10-K structural-pass by era (UPPER BOUND, not accuracy)

| era | pass / n (95% CI) |
|---|---|
| html | 352/380 (92.6%, 95% CI [89.6%, 94.9%]) |
| ixbrl | 87/92 (94.6%, 95% CI [87.9%, 97.7%]) |
| sgml | 163/172 (94.8%, 95% CI [90.4%, 97.2%]) |

## Full 10-K structural-pass by sector (UPPER BOUND, not accuracy)

| sector | pass / n (95% CI) |
|---|---|
| ? | 602/644 (93.5%, 95% CI [91.3%, 95.1%]) |

## Gross-failure tail -- full 10-K (42 of 644)

| accession | company | era | reason | items | cov | lead1 |
|---|---|---|---|---|---|---|
| 0001277277-06-000350 | WaMu Mortgage Pass-Throu | html | coverage:0.34 | 1 | 0.341 | False |
| 0001068238-13-000116 | STRUCTURED PROD TIERS CO | html | coverage:0.39 | 20 | 0.39 | True |
| 0000903423-13-000205 | MS STRUCTURED SATURNS SE | html | coverage:0.39 | 20 | 0.388 | True |
| 0001387131-20-004506 | NOVINT TECHNOLOGIES INC | html | empty | 0 | 0.0 | False |
| 0001558370-24-003170 | REPUBLIC BANCORP INC /KY | ixbrl | empty | 0 | 0.0 | False |
| 0001562762-24-000057 | NORWOOD FINANCIAL CORP | ixbrl | empty | 0 | 0.0 | False |
| 0001022368-07-000024 | SCHIFF NUTRITION INTERNA | html | empty | 0 | 0.0 | False |
| 0001104659-06-012410 | VORNADO REALTY TRUST | html | empty | 0 | 0.0 | False |
| 0000902873-96-000014 | ABS INDUSTRIES INC /DE/ | sgml | empty | 0 | 0.0 | False |
| 0001004878-98-000021 | APPLIED COMPUTER TECHNOL | sgml | empty | 0 | 0.0 | False |
| 0000913570-99-000005 | VENTURE LENDING & LEASIN | sgml | header:8 | 14 | 0.977 | True |
| 0001615774-19-005533 | QPAGOS | html | lead_item_1_missing | 14 | 0.908 | False |
| 0001193125-23-086145 | Santander Drive Auto Rec | html | lead_item_1_missing | 6 | 0.616 | False |
| 0001193125-23-086154 | Santander Drive Auto Rec | html | lead_item_1_missing | 6 | 0.71 | False |
| 0001903756-23-000002 | Carvana Auto Receivables | html | lead_item_1_missing | 6 | 0.713 | False |
| 0001658566-24-000018 | Permian Resources Corp | ixbrl | lead_item_1_missing | 21 | 0.769 | False |
| 0000002178-23-000038 | ADAMS RESOURCES & ENERGY | ixbrl | lead_item_1_missing | 20 | 0.834 | False |
| 0001387131-21-003179 | BANK OF SOUTH CAROLINA C | html | lead_item_1_missing | 1 | 0.545 | False |
| 0001396440-25-000018 | Main Street Capital CORP | ixbrl | lead_item_1_missing | 4 | 0.444 | False |
| 0001493152-21-008856 | Clean Energy Technologie | html | lead_item_1_missing | 19 | 0.89 | False |
| 0001193125-25-063848 | SANTANDER DRIVE AUTO REC | html | lead_item_1_missing | 6 | 0.624 | False |
| 0001988880-25-000006 | DTE Electric Securitizat | html | lead_item_1_missing | 11 | 0.754 | False |
| 0001785489-20-000015 | Ally Auto Receivables Tr | html | lead_item_1_missing | 5 | 0.711 | False |
| 0001174947-13-000120 | PPlus Trust Series LTD-1 | html | lead_item_1_missing | 3 | 0.648 | False |
| 0001534701-18-000065 | Phillips 66 | html | lead_item_1_missing | 19 | 0.864 | False |
| 0001144204-10-015339 | MACE SECURITY INTERNATIO | html | lead_item_1_missing | 14 | 0.92 | False |
| 0001551163-16-000354 | Blow & Drive Interlock C | html | lead_item_1_missing | 11 | 0.851 | False |
| 0001144204-16-090936 | CDF Funding, Inc. | html | lead_item_1_missing | 4 | 0.878 | False |
| 0000929638-13-000218 | BMW Vehicle Owner Trust  | html | lead_item_1_missing | 4 | 0.673 | False |
| 0001193125-16-630179 | SMART ABS Series 2015-3U | html | lead_item_1_missing | 3 | 0.753 | False |
| 0000930413-08-001713 | PSE&G Transition Funding | html | lead_item_1_missing | 13 | 0.838 | False |
| 0000930413-06-006423 | Hartford Life Global Fun | html | lead_item_1_missing | 2 | 0.645 | False |
| 0000930413-06-006342 | Hartford Life Global Fun | html | lead_item_1_missing | 2 | 0.646 | False |
| 0001140361-09-008437 | ACCELLENT INC | html | lead_item_1_missing | 7 | 0.752 | False |
| 0001144204-07-014837 | Atlas Energy Resources,  | html | lead_item_1_missing | 2 | 0.955 | False |
| 0001014108-06-000060 | KINDER MORGAN ENERGY PAR | html | lead_item_1_missing | 18 | 0.81 | False |
| 0000950124-99-002298 | LASON INC | sgml | lead_item_1_missing | 14 | 0.764 | False |
| 0000792989-00-000006 | DSI REALTY INCOME FUND I | sgml | lead_item_1_missing | 13 | 0.857 | False |
| 0000950135-97-005202 | TRANSITION SYSTEMS INC | sgml | lead_item_1_missing | 15 | 0.98 | False |
| 0000950135-95-002023 | IMMUNOGEN INC | sgml | lead_item_1_missing | 13 | 0.541 | False |
| 0000018540-97-000035 | WEST TEXAS UTILITIES CO | sgml | lead_item_1_missing | 13 | 0.83 | False |
| 0000844048-96-000003 | DSI REALTY INCOME FUND X | sgml | lead_item_1_missing | 13 | 0.864 | False |
