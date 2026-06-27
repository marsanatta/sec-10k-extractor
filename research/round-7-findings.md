# Autoresearch Round 7 — Findings (extra diverse sweep + new-cluster resolution)

Goal (auto mode): run an EXTRA ~1000-filing sweep over a FULL-EDGAR-population stratified sample
(not the curated large-cap list), census the failures, re-rank, and resolve clusters one by one.

## The sweep — a diverse, population-stratified sample (the generalization arm)

`eval/collect_sweep2.py` drew from the full EDGAR index per (form, filing-year), stratified by era +
form, over-sampling the thin/hard cells, each stratum's raw population recorded for re-weighting.
**883 pinned, immutable accessions** (sgml 230 / early-html 180 / mid-html 170 / ixbrl 200 /
amendment 100; 10-KSB yielded only 3 — an edgartools index gap, honest), excluding the existing 1845.

**Result (`eval/sweep2_report.md`):**
- **Full 10-K structural-pass: 602/644 (93.5%, 95% CI [91.3%, 95.1%])** — UPPER BOUND on robustness,
  NOT accuracy. Consistent across eras: html 92.6%, ixbrl 94.6%, sgml 94.8%.
- Fetch/parse drops: **0 of 883** (the killable harness held; no zombie cascade).
- 10-K/A amendments 75/238 (31.5%) — expected-low (amendments legitimately lack Part I), separate stratum.

This is a more honest generalization number than the curated set, on filers the curated list never saw.

## Failure census (42 gross failures, `scratch/r7_census.py`)

| category | n | nature |
|---|---|---|
| `lead_item_1_missing` → **ABS / structured-finance trusts** | ~15 | NEW cluster (Santander/Carvana/Ally Auto, BMW Trust, SMART ABS, Hartford Funding) — Regulation AB |
| `lead_item_1_missing` → operating company | 16 | of which the **combined "Items 1 and 2"** sub-cluster (energy) is cleanly fixable; rest heterogeneous |
| `empty` (relax also found 0) | 7 | small-caps / niche banks (NOVINT, Republic Bancorp, Vornado, …) |
| `coverage` / `header` | 4 | structured products (MS Saturns, WaMu Mortgage) |

## RESOLVED — A4: combined "Items N and M" lead header (committed)

**Root cause (traced):** oil/gas filers combine Item 1 + Item 2 under a PLURAL header `Items 1 and 2.
Business and Properties` (the business IS the properties). The singular `_HEADER_RE` requires
`Item`+gap+digit, so the trailing **'s'** of `Items 1` breaks the match and BOTH items drop —
`lead_item_1_missing` with 1A/1B present but no 1 or 2 (Phillips 66, Permian, Adams, OXY, …).

**Fix:** if the lead is STILL missing after every relax pass, prepend it from the combined header
just before the current body start — a pure prepend that preserves existing spans (incl. A3 gains)
and only ADDS coverage, fired last so a lead another pass recovered is untouched (the prepend, not a
strict-merge, was forced by a 1-filing collateral the merge caused on `0000950129-05-001641`, whose
lead A2 already recovers — eng-debug'd and fixed).

**Verified (G9 cache, old A1+A2+A3 vs new +A4): identical=1716, lead-recovered=20, collateral=0.**
All 20 land on a literal `ITEMS 1 AND 2. BUSINESS AND PROPERTIES` header (snippet-confirmed, zero
false positives). Offline suite **96 passed / 1 skipped**, network-free.

**char-gold anchor LOCKED (human-audited):** `oxy-fy2020` (Occidental FY2020, `0000797468-21-000009`),
added to `eval/boundary_gold.json` with items {1:[8664,27960], 1A:[27960,73380], 7:[86334,248611],
8:[260374,555045]}. Item 1 is the combined Business+Properties section (Item 2 folded). Verified: fresh
`to_canonical(fetch_10k)` byte-identical to cache (offsets valid for the eval scorer); full-pipeline
`extract()` scores 4/4 IoU=1.0; non-vacuous — without A4 the lead is absent (would be 3/4). This is the
A4 RED→GREEN anchor, same discipline as usb-fy2010 for A3.

## Resolved / deferred clusters (honest)

- **ABS / Regulation-AB trusts (~15) — RESOLVED in round 8 (it was SEGMENTATION, not classification).**
  The round-7 email mis-framed this as classification. Tracing Santander showed the relaxed pass DOES
  recover all the separator-less `Item N  Title` one-liners — but the tolerant split DROPPED the
  out-of-order `Item 1B` (ABS shells list 1B after Items 2/3), so relax was not a strict superset and
  A3's dominance guard correctly rejected it. Fix (`round-8`): the tolerant split now drops an order-dip
  only when its key RECURS (a duplicate -> true cross-reference); a UNIQUE out-of-order key is a real
  mis-ordered header and is kept. G9 gate clean (identical=1731, recovery=6, collateral=0): Santander
  6→21 items, plus TWO round-5 'both' 7A-drops recovered as a free Probe-2 win; char-gold all IoU 1.0.
  **No human gold needed** — a clean G9-gated segmentation fix, the shared-split change round 5 had
  deferred as too risky (the gate made it safe to attempt).
## Tail re-check (the 42 first-sweep failures re-run with A4 + round-8 + the harness fix)

`eval/sweep2_tail_accessions.txt` re-segments the 42 gross failures with the current code: **7/42 now
pass** (was 0/42) — the 4 oil/gas combined-items (A4) and 3 Santander-type ABS (round-8). This lifts
the population structural-pass from 602/644 (93.5%) to ~609/644 (≈94.6%). Two harness/finding notes:
- **Harness fix (round-8):** A4 recovered Item 1 on Phillips 66 / Permian / Adams / Kinder Morgan, but
  the sweep's `_starts_with_header` predicate still flagged them `header:1` because it required the
  singular "item N" and so rejected the plural "ITEMS 1 AND 2." header A4 anchors on. Fixed (B5-style,
  REPORTED-only) so the structural-pass no longer undercounts the A4 recoveries.
- **The remaining 35 are CRF-territory or heterogeneous one-offs — no clean cluster left.** A SECOND ABS
  sub-type (BMW / Ally / SMART / Carvana / Hartford / DTE / PSE&G) lists its items in a *running prose
  paragraph* with "(a)/(b)" markers — `(a) Item 1. Business. (b) Item 1A. Risk Factors.` — NOT line-start
  headers, so no line-anchored regex can find them (CRF-territory, same ceiling as FM-4). The rest are
  scattered small-caps / old SGML / structured-product coverage — heterogeneous, not a fixable cluster.

## Disposition
- **A4 KEPT** (`sec10k/segment.py`), G9 zero-collateral, suite green; char-gold pending human bless.
- ABS classification fix + the EDGAR-blocked clusters: documented, deferred (one needs human gold, the
  others need EDGAR to recover). Branch `round7/extra-sweep`; nothing pushed.
