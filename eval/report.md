# Evaluation Report

Self-built eval set; presence-level gold (conservative hand-labels). Rates are Wilson
95% CI -- small N means wide bars. Boundary match-rate uses a small char-exact gold on the
big items, per era (apple/ko/msft-2023 iXBRL regex-derived + human-audited; m2i iXBRL
title-labelled; msft-1995 SGML human-labeled-independent). See ANALYSIS.md for per-bucket.

## Headline

- **Presence-level silent-failure rate (lower is better): 0/7 (obs 0.00, 95% CI [0.00, 0.35])**
  (missed expected items with no flag; boundary correctness is the separate metric below)
- **Boundary match-rate @ IoU>=0.9 vs audited gold: 1.0 over 5 gold filings** (a wrong boundary shows up here as a number)
- Structural-ok: 7/7 (obs 1.00, 95% CI [0.65, 1.00])
- Coverage-plausible: 5/7 (obs 0.71, 95% CI [0.36, 0.92])
- Item-8 XBRL oracle ok: 4/7 (obs 0.57, 95% CI [0.25, 0.84])
- Needs-review (flagged): 6/7 (obs 0.86, 95% CI [0.49, 0.97])
- Mean presence recall: 1.0
- N filings: 7

## Per-filing

| id | era | present | recall | boundary@IoU0.9 | silent_fail | needs_review | item8_xbrl |
|----|-----|---------|--------|-----------------|-------------|--------------|-----------|
| apple-fy2024 | ixbrl | 23 | 1.0 | 1.0 (4/4) | False | False | 2/2 |
| ge-fy2023 | ixbrl | 23 | 1.0 | - | False | True | 0/3 |
| m2i-fy2023 | ixbrl | 23 | 1.0 | 1.0 (2/2) | False | True | 0/3 |
| msft-fy1995 | sgml | 14 | 1.0 | 1.0 (3/3) | False | True | 0/0 |
| chemed-amend-fy2024 | ixbrl | 2 | 1.0 | - | False | True | 0/0 |
| msft-fy2023 | ixbrl | 22 | 1.0 | 1.0 (4/4) | False | True | 2/2 |
| ko-fy2023 | ixbrl | 23 | 1.0 | 1.0 (4/4) | False | True | 2/2 |
