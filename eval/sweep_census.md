# Structural-sweep FAILURE CENSUS -- clustered (round-3 probe #1)

Clusters the fail tail by failure family so we /eng-debug per CLASS (one representative),
not per filing. **structural-pass is an UPPER BOUND on robustness, NOT accuracy.** REPORTED-
only. Known families = confirm + count at scale; UNEXPLAINED families = the eng-debug targets.

- Full 10-K swept: **1656**; structural-pass 1418/1656 (85.6% -- UPPER BOUND, not accuracy)
- Full-10-K fails clustered: **238**; amendments (separate stratum): 173; drops: 16

| cluster (failure family) | n | known class? | representative accessions |
|---|---|---|---|
| lead_missing_low_cov(<0.85) | 99 | run-fragmentation / PART-glued / no-separator headers -- rounds 1-2 named | 0000950134-08-012257(ORCL), 0000858877-20-000010(CSCO), 0000858877-18-000011(CSCO), 0000858877-22-000013(CSCO) |
| empty(0_items) | 67 | **UNEXPLAINED -> eng-debug** | 0000950131-95-000441(USB), 0000950131-97-001484(USB), 0000950137-02-000971(USB), 0000950134-03-003243(USB) |
| lead_missing_high_cov(>=0.85) | 50 | **UNEXPLAINED -> eng-debug** | 0001193125-09-041126(BAC), 0000927628-15-000026(COF), 0000316709-25-000010(SCHW), 0000899051-26-000031(ALL) |
| drop_other | 16 | **UNEXPLAINED -> eng-debug** | 0000732717-94-000009(?), 0000950115-94-000073(?), 0000109198-94-000003(?), 0000060667-94-000015(?) |
| coverage_very_low(<0.15) | 14 | cross-reference index (integrated MD&A, e.g. GE/INTC) -- round-1 named | 0000050863-19-000007(INTC), 0000050863-21-000010(INTC), 0000050863-23-000006(INTC), 0000050863-25-000009(INTC) |
| coverage_partial(0.15-0.4) | 6 | **UNEXPLAINED -> eng-debug** | 0001193125-11-047229(DUK), 0000950134-03-003953(VZ), 0001193125-05-035141(EXC), 0000060667-08-000067(LOW) |
| header_not_self_headed | 2 | **UNEXPLAINED -> eng-debug** | 0000950137-08-009268(GIS), 0000912057-99-007381(COST) |

## /eng-debug targets (UNEXPLAINED clusters -- one representative each)

- **empty(0_items)** (n=67; filers: ADM, AIG, C, CMCSA, D, DE, EXC, GIS, HON, HSY, MCD, MS) -- rep `0000950131-95-000441` (USB)
- **lead_missing_high_cov(>=0.85)** (n=50; filers: AIG, ALL, BAC, COF, COP, DUK, ED, GE, IP, MCD, MMM, OXY) -- rep `0001193125-09-041126` (BAC)
- **coverage_partial(0.15-0.4)** (n=6; filers: DUK, EXC, LOW, VZ, WMT) -- rep `0001193125-11-047229` (DUK)
- **header_not_self_headed** (n=2; filers: COST, GIS) -- rep `0000950137-08-009268` (GIS)
