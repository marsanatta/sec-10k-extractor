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

## Deferred / blocked clusters (honest)

- **ABS / Regulation-AB trusts (~15) — classification, not segmentation; BLOCKED on human gold.**
  Confirmed: these are asset-backed 10-Ks (Item 1112/1114/1117… the Reg-AB "Item 1100" series; standard
  Item 1 Business is legitimately-absent for a passive trust). The right fix is form/filer-aware
  classification (legitimately-absent vs extraction-failure), gated on the INDEPENDENT Signal D
  (`classification_gold`) — which is **human-only and cannot be auto-frozen** (anti-Goodhart). So this
  fix is earnable ONLY against a human-audited ABS classification entry — a hard blocker for auto mode.
  Already flagged `needs_review` (not silent).
- **`empty` (7) + other operating `lead_item_1_missing` (QPAGOS, Clean Energy, …) — EDGAR-blocked.**
  These sweep2 filings are not in the local cache; investigating them needs fresh EDGAR fetches, and
  EDGAR began returning **403 (rate-limited)** after the 883-sweep + investigation volume (eng-debug'd:
  transient backoff, not a code bug). Deferred until the limit clears.

## Disposition
- **A4 KEPT** (`sec10k/segment.py`), G9 zero-collateral, suite green; char-gold pending human bless.
- ABS classification fix + the EDGAR-blocked clusters: documented, deferred (one needs human gold, the
  others need EDGAR to recover). Branch `round7/extra-sweep`; nothing pushed.
