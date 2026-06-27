# Structural Sweep -- population robustness (UPPER BOUND, NOT accuracy)

Run: 2026-06-27 00:24 UTC. On-demand label-free sweep (`eval/structural_sweep.py`) over a pinned,
diverse stratified company sample. **structural-pass is an UPPER BOUND on robustness, NOT
accuracy** -- it catches gross failures (empty body, lead item dropped, no tiling,
implausible coverage) but is BLIND to interior boundary drift. The accuracy floor stays the
5 human-audited char-gold. REPORTED only: gates nothing, freezes no gold. Fast mode cannot
compute `needs_review`; flag-vs-silent on the fail tail comes from a separate full-pipeline
pass (see `sweep_fail_tail.md`).

- **HEADLINE -- full 10-K structural-pass: 1418/1656 (85.6%, 95% CI [83.9%, 87.2%])** (UPPER BOUND, not accuracy)
- 10-K/A amendments (separate stratum; legitimately lack Part I): 38/173 (22.0%, 95% CI [16.4%, 28.7%])
- Fetch/parse drops (logged, not silent): 16 of 1845

## Full 10-K structural-pass by era (UPPER BOUND, not accuracy)

| era | pass / n (95% CI) |
|---|---|
| html | 801/943 (84.9%, 95% CI [82.5%, 87.1%]) |
| ixbrl | 384/460 (83.5%, 95% CI [79.8%, 86.6%]) |
| sgml | 233/253 (92.1%, 95% CI [88.1%, 94.8%]) |

## Full 10-K structural-pass by sector (UPPER BOUND, not accuracy)

| sector | pass / n (95% CI) |
|---|---|
| auto | 15/15 (100.0%, 95% CI [79.6%, 100.0%]) |
| consumer_staples | 147/165 (89.1%, 95% CI [83.4%, 93.0%]) |
| energy | 87/137 (63.5%, 95% CI [55.2%, 71.1%]) |
| finance | 193/252 (76.6%, 95% CI [71.0%, 81.4%]) |
| healthcare | 178/192 (92.7%, 95% CI [88.1%, 95.6%]) |
| industrial | 202/232 (87.1%, 95% CI [82.1%, 90.8%]) |
| materials | 93/104 (89.4%, 95% CI [82.0%, 94.0%]) |
| retail | 133/142 (93.7%, 95% CI [88.4%, 96.6%]) |
| technology | 244/257 (94.9%, 95% CI [91.5%, 97.0%]) |
| telecom_media | 41/45 (91.1%, 95% CI [79.3%, 96.5%]) |
| utility | 85/115 (73.9%, 95% CI [65.2%, 81.1%]) |

## Gross-failure tail -- full 10-K (238 of 1656)

| accession | company | era | reason | items | cov | lead1 |
|---|---|---|---|---|---|---|
| 0000050863-23-000006 | INTC | ixbrl | coverage:0.01 | 22 | 0.015 | True |
| 0000050863-25-000009 | INTC | ixbrl | coverage:0.01 | 23 | 0.015 | True |
| 0000050863-26-000011 | INTC | ixbrl | coverage:0.01 | 23 | 0.012 | True |
| 0000773840-21-000015 | HON | ixbrl | coverage:0.01 | 5 | 0.007 | False |
| 0000040545-26-000008 | GE | ixbrl | coverage:0.01 | 23 | 0.015 | True |
| 0000040545-25-000015 | GE | ixbrl | coverage:0.01 | 23 | 0.014 | True |
| 0000040545-23-000023 | GE | ixbrl | coverage:0.01 | 22 | 0.013 | True |
| 0000040545-21-000011 | GE | ixbrl | coverage:0.01 | 21 | 0.009 | True |
| 0000040545-17-000010 | GE | html | coverage:0.01 | 21 | 0.007 | True |
| 0000040545-19-000014 | GE | html | coverage:0.01 | 21 | 0.006 | True |
| 0000040545-16-000145 | GE | html | coverage:0.01 | 20 | 0.007 | True |
| 0000050863-19-000007 | INTC | html | coverage:0.02 | 21 | 0.016 | True |
| 0000050863-21-000010 | INTC | ixbrl | coverage:0.02 | 21 | 0.016 | True |
| 0000797468-13-000011 | OXY | html | coverage:0.07 | 9 | 0.071 | False |
| 0000950134-03-003953 | VZ | html | coverage:0.25 | 12 | 0.248 | False |
| 0000060667-08-000067 | LOW | html | coverage:0.30 | 1 | 0.297 | False |
| 0001193125-05-035141 | EXC | html | coverage:0.31 | 11 | 0.306 | False |
| 0000104169-02-000004 | WMT | html | coverage:0.31 | 10 | 0.312 | False |
| 0000104169-00-000002 | WMT | sgml | coverage:0.36 | 11 | 0.365 | False |
| 0001193125-11-047229 | DUK | html | coverage:0.40 | 9 | 0.396 | False |
| 0000950131-95-000441 | USB | sgml | empty | 0 | 0.0 | False |
| 0000950131-97-001484 | USB | sgml | empty | 0 | 0.0 | False |
| 0000950137-02-000971 | USB | html | empty | 0 | 0.0 | False |
| 0000950134-03-003243 | USB | html | empty | 0 | 0.0 | False |
| 0000950134-05-003890 | USB | html | empty | 0 | 0.0 | False |
| 0000950124-07-001116 | USB | html | empty | 0 | 0.0 | False |
| 0001047469-03-007460 | C | html | empty | 0 | 0.0 | False |
| 0001047469-05-004988 | C | html | empty | 0 | 0.0 | False |
| 0001193125-09-041237 | C | html | empty | 0 | 0.0 | False |
| 0001193125-07-038505 | C | html | empty | 0 | 0.0 | False |
| 0001206774-11-000316 | C | html | empty | 0 | 0.0 | False |
| 0001206774-13-000852 | C | html | empty | 0 | 0.0 | False |
| 0000831001-25-000067 | C | ixbrl | empty | 0 | 0.0 | False |
| 0000831001-21-000042 | C | ixbrl | empty | 0 | 0.0 | False |
| 0000831001-26-000011 | C | ixbrl | empty | 0 | 0.0 | False |
| 0000831001-19-000027 | C | html | empty | 0 | 0.0 | False |
| 0000895421-23-000284 | MS | ixbrl | empty | 0 | 0.0 | False |
| 0001193125-19-051943 | MS | html | empty | 0 | 0.0 | False |
| 0000895421-21-000286 | MS | ixbrl | empty | 0 | 0.0 | False |
| 0000895421-26-000086 | MS | ixbrl | empty | 0 | 0.0 | False |
| 0000895421-25-000304 | MS | ixbrl | empty | 0 | 0.0 | False |
| 0001193125-05-052209 | PNC | html | empty | 0 | 0.0 | False |
| 0001193125-09-042518 | PNC | html | empty | 0 | 0.0 | False |
| 0001193125-11-051725 | PNC | html | empty | 0 | 0.0 | False |
| 0001193125-13-085012 | PNC | html | empty | 0 | 0.0 | False |
| 0001193125-17-062524 | PNC | html | empty | 0 | 0.0 | False |
| 0000005272-15-000002 | AIG | html | empty | 0 | 0.0 | False |
| 0000005272-26-000023 | AIG | ixbrl | empty | 0 | 0.0 | False |
| 0000797468-07-000027 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-11-000026 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-09-000015 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-15-000003 | OXY | html | empty | 0 | 0.0 | False |
| 0000047111-01-500079 | HSY | sgml | empty | 0 | 0.0 | False |
| 0000831001-23-000037 | C | ixbrl | empty | 0 | 0.0 | False |
| 0000831001-17-000038 | C | html | empty | 0 | 0.0 | False |
| 0000831001-15-000043 | C | html | empty | 0 | 0.0 | False |
| 0000005272-23-000007 | AIG | ixbrl | empty | 0 | 0.0 | False |
| 0000005272-25-000012 | AIG | ixbrl | empty | 0 | 0.0 | False |
| 0000950130-00-001710 | SLB | sgml | empty | 0 | 0.0 | False |
| 0000797468-01-500004 | OXY | sgml | empty | 0 | 0.0 | False |
| 0000797468-03-000111 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-17-000003 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-19-000004 | OXY | html | empty | 0 | 0.0 | False |
| 0000797468-05-000041 | OXY | html | empty | 0 | 0.0 | False |
| 0000040704-94-000020 | GIS | sgml | empty | 0 | 0.0 | False |
| 0000950123-10-064517 | GIS | html | empty | 0 | 0.0 | False |
| 0001193125-12-293636 | GIS | html | empty | 0 | 0.0 | False |
| 0001193125-14-260716 | GIS | html | empty | 0 | 0.0 | False |
| 0001193125-16-638404 | GIS | html | empty | 0 | 0.0 | False |
| 0001193125-18-209377 | GIS | html | empty | 0 | 0.0 | False |
| 0000007084-06-000401 | ADM | html | empty | 0 | 0.0 | False |
| 0000007084-08-000044 | ADM | html | empty | 0 | 0.0 | False |
| 0000773840-25-000010 | HON | ixbrl | empty | 0 | 0.0 | False |
| 0000950159-03-000238 | CMCSA | html | empty | 0 | 0.0 | False |
| 0000950159-04-000281 | CMCSA | html | empty | 0 | 0.0 | False |
| 0001564590-15-000777 | NEM | html | empty | 0 | 0.0 | False |
| 0001047469-09-002013 | XEL | html | empty | 0 | 0.0 | False |
| 0001193125-17-039639 | EXC | html | empty | 0 | 0.0 | False |
| 0001564590-21-008442 | D | ixbrl | empty | 0 | 0.0 | False |
| 0000063908-26-000035 | MCD | ixbrl | empty | 0 | 0.0 | False |
| 0000063908-25-000012 | MCD | ixbrl | empty | 0 | 0.0 | False |
| 0000063908-23-000012 | MCD | ixbrl | empty | 0 | 0.0 | False |
| 0000063908-21-000013 | MCD | ixbrl | empty | 0 | 0.0 | False |
| 0001558370-22-018703 | DE | ixbrl | empty | 0 | 0.0 | False |
| 0001104659-25-122321 | DE | ixbrl | empty | 0 | 0.0 | False |
| 0000773840-26-000013 | HON | ixbrl | empty | 0 | 0.0 | False |
| 0000773840-23-000013 | HON | ixbrl | empty | 0 | 0.0 | False |
| 0000950137-08-009268 | GIS | html | header:1 | 20 | 0.992 | True |
| 0000912057-99-007381 | COST | sgml | header:1 | 14 | 0.967 | True |
| 0000950134-08-012257 | ORCL | html | lead_item_1_missing | 18 | 0.803 | False |
| 0000858877-20-000010 | CSCO | ixbrl | lead_item_1_missing | 13 | 0.569 | False |
| 0000858877-18-000011 | CSCO | html | lead_item_1_missing | 12 | 0.566 | False |
| 0000858877-22-000013 | CSCO | ixbrl | lead_item_1_missing | 14 | 0.665 | False |
| 0000858877-25-000111 | CSCO | ixbrl | lead_item_1_missing | 14 | 0.55 | False |
| 0000006951-02-000002 | AMAT | html | lead_item_1_missing | 6 | 0.796 | False |
| 0000950135-08-007596 | ADI | html | lead_item_1_missing | 12 | 0.753 | False |
| 0000950123-10-107816 | ADI | html | lead_item_1_missing | 12 | 0.731 | False |
| 0001193125-09-041126 | BAC | html | lead_item_1_missing | 12 | 0.935 | False |
| 0000070858-21-000023 | BAC | ixbrl | lead_item_1_missing | 13 | 0.631 | False |
| 0000950123-11-018743 | BAC | html | lead_item_1_missing | 12 | 0.72 | False |
| 0000070858-23-000092 | BAC | ixbrl | lead_item_1_missing | 14 | 0.612 | False |
| 0000070858-26-000157 | BAC | ixbrl | lead_item_1_missing | 14 | 0.609 | False |
| 0000070858-25-000139 | BAC | ixbrl | lead_item_1_missing | 14 | 0.606 | False |
| 0000950123-07-001332 | GS | html | lead_item_1_missing | 12 | 0.692 | False |
| 0001193125-11-050049 | MS | html | lead_item_1_missing | 11 | 0.578 | False |
| 0001193125-13-077191 | MS | html | lead_item_1_missing | 12 | 0.696 | False |
| 0001193125-15-070443 | PNC | html | lead_item_1_missing | 1 | 0.837 | False |
| 0000927628-25-000092 | COF | ixbrl | lead_item_1_missing | 13 | 0.449 | False |
| 0000927628-15-000026 | COF | html | lead_item_1_missing | 19 | 0.906 | False |
| 0000927628-26-000024 | COF | ixbrl | lead_item_1_missing | 20 | 0.745 | False |
| 0000316709-25-000010 | SCHW | ixbrl | lead_item_1_missing | 22 | 0.896 | False |
| 0000899051-26-000031 | ALL | ixbrl | lead_item_1_missing | 22 | 0.931 | False |
| 0000950129-05-001641 | COP | html | lead_item_1_missing | 16 | 0.808 | False |
| 0000950134-09-003971 | VLO | html | lead_item_1_missing | 12 | 0.882 | False |
| 0001035002-13-000008 | VLO | html | lead_item_1_missing | 12 | 0.844 | False |
| 0001035002-15-000009 | VLO | html | lead_item_1_missing | 13 | 0.901 | False |
| 0000950134-03-004171 | WMB | html | lead_item_1_missing | 14 | 0.797 | False |
| 0000950123-11-019286 | MRK | html | lead_item_1_missing | 12 | 0.468 | False |
| 0000950123-11-018800 | AMGN | html | lead_item_1_missing | 3 | 0.722 | False |
| 0000097745-01-000012 | TMO | sgml | lead_item_1_missing | 14 | 0.618 | False |
| 0000950123-05-003146 | MO | html | lead_item_1_missing | 17 | 0.562 | False |
| 0001193125-11-047479 | GE | html | lead_item_1_missing | 11 | 0.61 | False |
| 0000040545-13-000036 | GE | html | lead_item_1_missing | 18 | 0.892 | False |
| 0001104659-09-009669 | MMM | html | lead_item_1_missing | 19 | 0.935 | False |
| 0000950117-01-000640 | HON | sgml | lead_item_1_missing | 8 | 0.65 | False |
| 0000928385-01-000795 | LMT | sgml | lead_item_1_missing | 14 | 0.821 | False |
| 0001090727-19-000006 | UPS | html | lead_item_1_missing | 19 | 0.853 | False |
| 0001193125-11-024531 | UNP | html | lead_item_1_missing | 13 | 0.823 | False |
| 0001193125-13-045658 | UNP | html | lead_item_1_missing | 11 | 0.489 | False |
| 0001104659-05-009425 | XEL | html | lead_item_1_missing | 1 | 0.975 | False |
| 0001104659-07-013272 | XEL | html | lead_item_1_missing | 2 | 0.848 | False |
| 0000950117-05-000925 | IP | html | lead_item_1_missing | 1 | 0.985 | False |
| 0001193125-07-042746 | IP | html | lead_item_1_missing | 16 | 0.913 | False |
| 0001193125-09-038657 | IP | html | lead_item_1_missing | 11 | 0.589 | False |
| 0001193125-11-046928 | IP | html | lead_item_1_missing | 11 | 0.573 | False |
| 0000051434-15-000009 | IP | html | lead_item_1_missing | 11 | 0.597 | False |
| 0001047469-05-004437 | CMCSA | html | lead_item_1_missing | 1 | 0.743 | False |
| 0000070858-17-000013 | BAC | html | lead_item_1_missing | 13 | 0.882 | False |
| 0000070858-15-000008 | BAC | html | lead_item_1_missing | 12 | 0.803 | False |
| 0000070858-13-000097 | BAC | html | lead_item_1_missing | 12 | 0.797 | False |
| 0000316709-26-000009 | SCHW | ixbrl | lead_item_1_missing | 22 | 0.904 | False |
| 0000950123-07-003026 | AIG | html | lead_item_1_missing | 11 | 0.452 | False |
| 0001047469-13-001390 | AIG | html | lead_item_1_missing | 1 | 0.988 | False |
| 0000086312-21-000011 | TRV | ixbrl | lead_item_1_missing | 20 | 0.805 | False |
| 0000086312-23-000011 | TRV | ixbrl | lead_item_1_missing | 21 | 0.796 | False |
| 0000086312-26-000065 | TRV | ixbrl | lead_item_1_missing | 22 | 0.803 | False |
| 0000004977-25-000047 | AFL | ixbrl | lead_item_1_missing | 20 | 0.825 | False |
| 0000034088-25-000010 | XOM | ixbrl | lead_item_1_missing | 19 | 0.923 | False |
| 0000034088-26-000045 | XOM | ixbrl | lead_item_1_missing | 19 | 0.915 | False |
| 0001628280-26-011402 | AFL | ixbrl | lead_item_1_missing | 20 | 0.828 | False |
| 0000797468-21-000009 | OXY | ixbrl | lead_item_1_missing | 19 | 0.952 | False |
| 0000950129-03-001563 | COP | html | lead_item_1_missing | 14 | 0.855 | False |
| 0000797468-25-000029 | OXY | ixbrl | lead_item_1_missing | 20 | 0.933 | False |
| 0001628280-26-009059 | OXY | ixbrl | lead_item_1_missing | 20 | 0.93 | False |
| 0000950134-04-002756 | COP | html | lead_item_1_missing | 15 | 0.809 | False |
| 0001104659-07-013338 | COP | html | lead_item_1_missing | 18 | 0.823 | False |
| 0001193125-15-059281 | COP | html | lead_item_1_missing | 18 | 0.87 | False |
| 0001193125-17-050077 | COP | html | lead_item_1_missing | 18 | 0.882 | False |
| 0001193125-13-065426 | COP | html | lead_item_1_missing | 18 | 0.878 | False |
| 0001163165-23-000006 | COP | ixbrl | lead_item_1_missing | 18 | 0.874 | False |
| 0001193125-19-043841 | COP | html | lead_item_1_missing | 18 | 0.902 | False |
| 0001163165-25-000012 | COP | ixbrl | lead_item_1_missing | 19 | 0.889 | False |
| 0001562762-21-000027 | COP | ixbrl | lead_item_1_missing | 17 | 0.866 | False |
| 0001163165-26-000009 | COP | ixbrl | lead_item_1_missing | 19 | 0.896 | False |
| 0001110805-03-000007 | VLO | html | lead_item_1_missing | 6 | 0.858 | False |
| 0000045012-25-000010 | HAL | ixbrl | lead_item_1_missing | 14 | 0.712 | False |
| 0000950134-04-003420 | VLO | html | lead_item_1_missing | 10 | 0.852 | False |
| 0000950134-05-004779 | VLO | html | lead_item_1_missing | 11 | 0.869 | False |
| 0001193125-07-039165 | VLO | html | lead_item_1_missing | 12 | 0.91 | False |
| 0001035002-17-000009 | VLO | html | lead_item_1_missing | 13 | 0.905 | False |
| 0001035002-19-000008 | VLO | html | lead_item_1_missing | 13 | 0.889 | False |
| 0000950134-99-001346 | VLO | sgml | lead_item_1_missing | 5 | 0.58 | False |
| 0001035002-21-000051 | VLO | ixbrl | lead_item_1_missing | 13 | 0.895 | False |
| 0001035002-11-000013 | VLO | html | lead_item_1_missing | 5 | 0.909 | False |
| 0000950134-95-000291 | WMB | sgml | lead_item_1_missing | 13 | 0.696 | False |
| 0001035002-25-000005 | VLO | ixbrl | lead_item_1_missing | 21 | 0.866 | False |
| 0001035002-23-000027 | VLO | ixbrl | lead_item_1_missing | 15 | 0.862 | False |
| 0001628280-26-011499 | VLO | ixbrl | lead_item_1_missing | 21 | 0.877 | False |
| 0001784031-23-000007 | APA | ixbrl | lead_item_1_missing | 20 | 0.838 | False |
| 0001784031-22-000009 | APA | ixbrl | lead_item_1_missing | 20 | 0.833 | False |
| 0002040266-25-000007 | APA | ixbrl | lead_item_1_missing | 21 | 0.835 | False |
| 0001841666-26-000015 | APA | ixbrl | lead_item_1_missing | 21 | 0.828 | False |
| 0000014272-17-000047 | BMY | html | lead_item_1_missing | 12 | 0.521 | False |
| 0000014272-26-000004 | BMY | ixbrl | lead_item_1_missing | 22 | 0.793 | False |
| 0001613103-15-000028 | MDT | html | lead_item_1_missing | 12 | 0.58 | False |
| 0000097745-07-000053 | TMO | html | lead_item_1_missing | 4 | 0.819 | False |
| 0000950131-03-001306 | BAX | html | lead_item_1_missing | 15 | 0.622 | False |
| 0001628280-26-007733 | BAX | ixbrl | lead_item_1_missing | 20 | 0.708 | False |
| 0001193125-14-426571 | BDX | html | lead_item_1_missing | 11 | 0.545 | False |
| 0000310764-96-000004 | SYK | sgml | lead_item_1_missing | 13 | 0.477 | False |
| 0000310764-07-000062 | SYK | html | lead_item_1_missing | 9 | 0.725 | False |
| 0001628280-22-030686 | BDX | ixbrl | lead_item_1_missing | 13 | 0.507 | False |
| 0000310764-09-000035 | SYK | html | lead_item_1_missing | 13 | 0.738 | False |
| 0000077476-21-000007 | PEP | ixbrl | lead_item_1_missing | 8 | 0.788 | False |
| 0000077476-23-000007 | PEP | ixbrl | lead_item_1_missing | 17 | 0.779 | False |
| 0000021076-96-000004 | CLX | sgml | lead_item_1_missing | 12 | 0.652 | False |
| 0000021076-98-000006 | CLX | sgml | lead_item_1_missing | 13 | 0.52 | False |
| 0000021076-00-000003 | CLX | sgml | lead_item_1_missing | 13 | 0.534 | False |
| 0000021076-02-000019 | CLX | html | lead_item_1_missing | 15 | 0.608 | False |
| 0000950129-06-008456 | SYY | html | lead_item_1_missing | 4 | 0.645 | False |
| 0000051434-26-000055 | IP | ixbrl | lead_item_1_missing | 22 | 0.878 | False |
| 0000950117-03-000884 | IP | html | lead_item_1_missing | 15 | 0.949 | False |
| 0001047469-99-012865 | IP | sgml | lead_item_1_missing | 14 | 0.932 | False |
| 0000089800-19-000004 | SHW | html | lead_item_1_missing | 20 | 0.774 | False |
| 0000089800-21-000010 | SHW | ixbrl | lead_item_1_missing | 19 | 0.806 | False |
| 0000788784-19-000005 | PEG | html | lead_item_1_missing | 19 | 0.857 | False |
| 0000788784-17-000003 | PEG | html | lead_item_1_missing | 19 | 0.839 | False |
| 0001193125-11-047330 | PEG | html | lead_item_1_missing | 11 | 0.643 | False |
| 0000788784-13-000003 | PEG | html | lead_item_1_missing | 19 | 0.849 | False |
| 0000788784-95-000002 | PEG | sgml | lead_item_1_missing | 10 | 0.653 | False |
| 0001047862-23-000038 | ED | ixbrl | lead_item_1_missing | 13 | 0.499 | False |
| 0001193125-15-054350 | ED | html | lead_item_1_missing | 11 | 0.569 | False |
| 0001047862-17-000029 | ED | html | lead_item_1_missing | 20 | 0.766 | False |
| 0001193125-13-069310 | ED | html | lead_item_1_missing | 2 | 0.914 | False |
| 0001193125-09-034924 | ED | html | lead_item_1_missing | 2 | 0.963 | False |
| 0001193125-11-042145 | ED | html | lead_item_1_missing | 11 | 0.585 | False |
| 0000023632-98-000024 | ED | sgml | lead_item_1_missing | 14 | 0.813 | False |
| 0000912057-02-011931 | ED | html | lead_item_1_missing | 14 | 0.92 | False |
| 0001109357-21-000022 | EXC | ixbrl | lead_item_1_missing | 13 | 0.422 | False |
| 0001193125-13-069749 | EXC | html | lead_item_1_missing | 12 | 0.607 | False |
| 0001193125-11-030543 | EXC | html | lead_item_1_missing | 12 | 0.657 | False |
| 0001193125-15-049964 | EXC | html | lead_item_1_missing | 12 | 0.604 | False |
| 0001193125-07-029587 | EXC | html | lead_item_1_missing | 12 | 0.643 | False |
| 0001193125-17-060413 | D | html | lead_item_1_missing | 16 | 0.792 | False |
| 0001193125-15-067777 | D | html | lead_item_1_missing | 12 | 0.8 | False |
| 0001628280-19-001107 | EXC | html | lead_item_1_missing | 3 | 0.48 | False |
| 0001326160-13-000009 | DUK | html | lead_item_1_missing | 18 | 0.894 | False |
| 0000092122-03-000074 | SO | html | lead_item_1_missing | 14 | 0.914 | False |
| 0001047469-03-008450 | MCD | html | lead_item_1_missing | 14 | 0.949 | False |
| 0000100885-21-000068 | UNP | ixbrl | lead_item_1_missing | 17 | 0.803 | False |
| 0000950134-03-002918 | UNP | html | lead_item_1_missing | 9 | 0.493 | False |
| 0000049826-21-000007 | ITW | ixbrl | lead_item_1_missing | 12 | 0.457 | False |
| 0000950123-11-019620 | ITW | html | lead_item_1_missing | 11 | 0.537 | False |
| 0000950123-11-010835 | NOC | html | lead_item_1_missing | 11 | 0.516 | False |
| 0000950134-09-002265 | NOC | html | lead_item_1_missing | 11 | 0.499 | False |
| 0000950124-07-000990 | NOC | html | lead_item_1_missing | 5 | 0.771 | False |
| 0000032604-16-000105 | EMR | html | lead_item_1_missing | 12 | 0.723 | False |
| 0000040545-09-000012 | GE | html | lead_item_1_missing | 11 | 0.538 | False |

## Dropped (fetch/parse error, 16)

| accession | error |
|---|---|
| 0000732717-94-000009 | ValueError: No filing found for accession 0000732717-94-000009 |
| 0000950115-94-000073 | ValueError: No filing found for accession 0000950115-94-000073 |
| 0000109198-94-000003 | ValueError: No filing found for accession 0000109198-94-000003 |
| 0000060667-94-000015 | ValueError: No filing found for accession 0000060667-94-000015 |
| 0000950131-94-000539 | ValueError: No filing found for accession 0000950131-94-000539 |
| 0000354950-94-000001 | ValueError: No filing found for accession 0000354950-94-000001 |
| 0000702165-94-000008 | ValueError: No filing found for accession 0000702165-94-000008 |
| 0000912057-94-001480 | ValueError: No filing found for accession 0000912057-94-001480 |
| 0000066740-94-000010 | ValueError: No filing found for accession 0000066740-94-000010 |
| 0000040545-94-000003 | ValueError: No filing found for accession 0000040545-94-000003 |
| 0000950144-94-000600 | ValueError: No filing found for accession 0000950144-94-000600 |
| 0000950110-94-000233 | ValueError: No filing found for accession 0000950110-94-000233 |
| 0000890566-94-000092 | ValueError: No filing found for accession 0000890566-94-000092 |
| 0000086312-94-000008 | ValueError: No filing found for accession 0000086312-94-000008 |
| 0000019617-94-000048 | ValueError: No filing found for accession 0000019617-94-000048 |
| 0000024741-94-000033 | ValueError: No filing found for accession 0000024741-94-000033 |
