# Assess Whether Cross-Reference-Index-Table Filings (INTC-style) Are Worth Handling

- **Datetime:** 2026-06-27 03:29:07
- **Summary:** While auditing the INTC RED anchor, the user asked whether there are many filings like INTC (items located only via an end-of-document "cross-reference index" table, no body "Item N" headings) — if so it would be worth handling — and asked to save the prompt.

## Prompt

> are there a lot of cases that will be like intc this case which use index table for items? if yes, then worth to handle this case /save-prompt

## What I Did

- Answered with DATA, not a guess: grepped the G9 canonical cache (1,422 of 1,845 cached at query time) for a "cross-reference index" heading and mapped hits to filers.
- Finding: **~15 of 1,422 (~1%)**, and **all 15 are index-ONLY** (fewer than 5 body "Item N." headers), but concentrated in just **3-4 distinct filers** — GE (×7), MCD (×4), HON (×4), plus INTC (in the round-3 `coverage_very_low` cluster, n≈14). So it is **filer house-style, NOT widespread**.
- Recommendation (honest, per the user's own "if a lot → worth it" criterion): **NOT worth handling this round.** It is (a) small (~1%) and concentrated in a handful of filers, and (b) the HARDEST class — the body has no "Item N" headings, so the header-anchor approach fundamentally cannot find body items; recovering them would require parsing the cross-reference index table (item→page) AND mapping page numbers to char offsets via page-break markers in the canonical — a different, involved mechanism, ceiling-adjacent. Round-4's A1 (separator-less headers, n=67) and A2 (cross-ref intruder, n=50) are bigger and far easier wins.
- Disposition: keep it pinned-RED (the INTC anchor) and documented honestly as a known failure class; revisit IF a bigger sweep shows the prevalence growing, or if a clean page-marker→offset approach is built. Noted the feasible-but-involved approach for a future round.
- Saved this prompt; did not change code. (The GIS FY2018 char-gold proposal also came back in parallel and will be presented to the user for B2 audit next.)
