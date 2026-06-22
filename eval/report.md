# Evaluation Report

Self-built eval set; presence-level gold (conservative hand-labels). Rates are Wilson
95% CI -- small N means wide bars. Char-exact boundary F1 vs NTU itemseg is STRETCH.

## Headline

- **Presence-level silent-failure rate (lower is better): 0/7 (obs 0.00, 95% CI [0.00, 0.35])**
  (missed expected items with no flag; char-exact boundary-drift is STRETCH, not measured here)
- Structural-ok: 7/7 (obs 1.00, 95% CI [0.65, 1.00])
- Coverage-plausible: 4/7 (obs 0.57, 95% CI [0.25, 0.84])
- Item-8 XBRL oracle ok: 4/7 (obs 0.57, 95% CI [0.25, 0.84])
- Needs-review (flagged): 5/7 (obs 0.71, 95% CI [0.36, 0.92])
- Mean presence recall: 0.8571
- N filings: 7

## Per-filing

| id | era | present | recall | missing | silent_fail | needs_review | item8_xbrl |
|----|-----|---------|--------|---------|-------------|--------------|-----------|
| apple-fy2024 | ixbrl | 23 | 1.0 | - | False | False | 2/2 |
| ge-fy2023 | ixbrl | 23 | 1.0 | - | False | True | 0/3 |
| m2i-fy2023 | ixbrl | 0 | 0.0 | 1,1A,2,3,5,7,8,9,9A | False | True | 0/0 |
| msft-fy1995 | sgml | 14 | 1.0 | - | False | True | 0/0 |
| chemed-amend-fy2024 | ixbrl | 2 | 1.0 | - | False | True | 0/0 |
| msft-fy2023 | ixbrl | 22 | 1.0 | - | False | True | 2/2 |
| ko-fy2023 | ixbrl | 23 | 1.0 | - | False | False | 2/2 |
