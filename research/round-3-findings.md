# Autoresearch Round 3 — Findings (REVIEW DOCUMENT — nothing merged, nothing pushed)

**Status:** executed in the `round3/sweep-1000` worktree (off `main` + the sweep harness merged in
locally). REPORTED-only: **no extractor fix implemented** (deliverable = evidence + ranked plan); no
gold edited/frozen/regenerated; no ruler loosened. Every structural-pass number is an **UPPER BOUND
on robustness, NOT accuracy** (it catches gross failures; it is blind to interior boundary drift —
the accuracy floor stays the 5 human-audited char-gold).

**Baseline:** post-merge `main` — the LLM escalation tier is present but **default-OFF** (measured:
no independent-signal gain; `research/llm-measurement-findings.md` on the measurement branch). The
sweep ran the deterministic regex tier only; the LLM was not in the loop.

---

## 0. Headline

| probe | result |
|---|---|
| #1 Scale the label-free sweep 471 → **1,656 full-10-K swept** (115 filers × 17-yr grid, 1,845 pinned) | **full-10-K structural-pass = 1,418/1,656 = 85.6%** (95% CI [83.9%, 87.2%]) — UPPER BOUND, not accuracy |
| #1 amendments (separate stratum) / drops | 38/173 (22.0%); **16 drops of 1,845** (after the harness fix, §C) |
| #2 `/eng-debug` every UNEXPLAINED cluster (per class, not per filing) | **5 clusters RCA'd — all TRACTABLE or harness/ingest gaps; NONE is the named ceiling** |
| #3 Ranked improvement plan | 3 extractor fixes + 2 harness/ingest fixes, each behind an independent KEEP-gate |
| harness robustness | timeout-cascade bug found + **fixed** (killable subprocess): drops 221 → 16 |

**The honest takeaways.**
1. **The number dipped — reported honestly.** 85.6% vs the 471-run's 88.9%. The bigger, denser sample
   (more pre-2001 SGML, more energy/industrial/financial filers, every-2-year grid back to 1994)
   surfaced more of the tail. Tighter CI (±1.6%) on a 3.5× larger denominator. UPPER BOUND, not
   accuracy.
2. **The failure tail is more RECOVERABLE than feared.** At 1,656-filing scale, **every** unexplained
   cluster traced to a *tractable* deterministic-tier defect or a *harness/ingest* gap — **the named
   common-mode ceiling (header-text-stripped, needs a decorrelated CRF extractor) did not appear as a
   distinct cluster.** The cluster I most feared was the ceiling — `empty (0 items)` — is actually a
   fixable separator-less-header regex gap. **So S4 (no tractable cluster → stop) does NOT fire.**
3. **Two "failures" are not extractor bugs at all** — a harness false-fail and an ingest index gap
   (§2d, §2e). One slightly *under*counts the 85.6%.

---

## 1. Probe #1 — scale + cluster census

- Sample scaled 471 → **1,845 pinned accessions** (1,837 full-10-K + 8 amendments at collection;
  expands to 173 amendments swept as multi-form filers resolved), 115 filers × 11 sectors × a denser
  1994–2025 grid (`eval/collect_accessions.py`, `eval/sweep_accessions.txt`). Accession-pinned +
  immutable; `K` didn't resolve (logged). Fresh run on current code (no stale records mixed).
- **Full-10-K structural-pass: 1,418/1,656 = 85.6% (95% CI [83.9%, 87.2%]) — UPPER BOUND on
  robustness, NOT accuracy.** Per-era / per-sector breakdown in `eval/sweep_report.md`.

**Clustered census** (`eval/sweep_census.md` via `eval/sweep_clusters.py`) — 238 full-10-K fails:

| cluster (failure family) | n | class | round-3 verdict |
|---|---|---|---|
| `lead_missing_low_cov(<0.85)` | 99 | KNOWN (run-frag / PART-glued / no-separator, rounds 1-2) | confirm + count |
| `empty(0_items)` | 67 | UNEXPLAINED → debugged | **TRACTABLE** (§2a) |
| `lead_missing_high_cov(≥0.85)` | 50 | UNEXPLAINED → debugged | **TRACTABLE** (§2b) |
| `drop_other` | 16 | UNEXPLAINED → debugged | **INGEST gap** (§2d) |
| `coverage_very_low(<0.15)` | 14 | KNOWN (cross-reference index, GE/INTC) | confirm + count |
| `coverage_partial(0.15-0.4)` | 6 | UNEXPLAINED → debugged | **TRACTABLE** (§2c) |
| `header_not_self_headed` | 2 | UNEXPLAINED → debugged | **MIXED** (1 harness false-fail + 1 TOC) (§2e) |

Known families (confirm + count, not re-debugged): `lead_missing_low_cov` (99) and
`coverage_very_low` (14) map to already-named rounds-1/2/sweep-1 classes.

---

## 2. Probe #2 — `/eng-debug` every UNEXPLAINED cluster (RCA, representative-per-class)

All RCAs are execution-traced against the **live canonical bytes** (independent ground truth), not
the segmenter's own output. **No fix implemented.**

### 2a. `empty (0 items)` — n=67 (USB, OXY, GIS, AIG, C, MS, …) → **TRACTABLE (regex gap)**
Separator-less headers (`ITEM 1A RISK FACTORS`, `ITEM\n7\n\nMANAGEMENT`, `ITEM 3 LEGAL PROCEEDINGS`).
`_HEADER_RE` (`sec10k/segment.py:17`) *requires* a separator (`. : ) – — -`) after the item number,
so `_find_headers` returns 0 → `segment()` returns `[]` → coverage 0.0. The headers are **physically
present** in the canonical (`normalize` does not strip them) — verified by direct search and by the
live regex no-matching `ITEM 1A RISK FACTORS` while matching the separator'd control. The fallback
also fails (`needs_fallback` rejects 2007/2016; SGML edgartools finds nothing). One filer-house-style
cause, **era-independent**, broader than any single filer. **NOT the header-stripped ceiling.**
*Fix in principle (not implemented):* accept `ITEM <num> <ws> (<TITLE-like>|EOL)` while keeping the
line-start anchor (which already excludes mid-prose `in Item 8 of this report`). *Guard:* require a
title-like follower (ALL-CAPS / known title keyword), validate zero new false headers on cooperative
filings; `_pick_body_run` prose-gap heuristic is the backstop.

### 2b. `lead_missing_high_cov (≥0.85)` — n=50 (BAC, COF, SCHW, GE, MMM, OXY, …) → **TRACTABLE (run-split)**
Item 1's body header **is** matched; it is discarded by run assembly. A forward cross-reference in
Item 1's prose (`see "\nItem 1A. Risk Factors…"`, `…in\nItem 8.`, `…in\nItem 2.`) lands at a line
start and is mis-matched as a header; that advances the canonical-order counter, so the real body
`Item 1A` (lower order) makes `_split_runs` (`segment.py:29-43`) sever the run, orphaning the
Item-1-bearing run; `_pick_body_run` (`segment.py:46-63`) then picks the larger downstream run that
begins at `1A` → key `"1"` absent. Coverage stays ~0.9 (spans tile `1A`→EOF). One shared mechanism,
era-independent; body Item 1 confirmed to be the genuine Business section. *Fix in principle:*
intruder-tolerant `_split_runs` (ignore a single out-of-order spike) / stitch the contiguous leading
orphan / reject in-prose `see…Item N`. *Guard:* never synthesize an absent Item 1 (amendments / IBR
shells); keep preferring body over TOC; bounded single-spike tolerance; keep the `{1,1A,7,8}`
self-check.

### 2c. `coverage_partial (0.15-0.4)` — n=6 (DUK, VZ, EXC, LOW, WMT) → **TRACTABLE (GE-family; FLAGGED, not silent)**
DUK rep (`0001193125-11-047229`, coverage 0.396): two cross-reference false headers wreck run
selection — **`Item 4-08(g)`** (a Regulation S-X citation *inside Item 8*, matched because `_SEP`
includes `-`, so `4-08(g)` parses as `item 4` + sep `-`) anchors a back-half run whose 415 KB of real
Item-8 financials out-scores the genuine front-half body run on max-prose; plus a `See\nItem 2.`
cross-ref forces the initial split. Result: spans start at offset 770062, tiling only the back 39.6%;
Items 1/1A/7/8 uncovered. Same family as the GE cross-reference-index case, here aggravated by the
hyphen separator. **Crucially flagged, not silent**: full `extract()` → `coverage_plausible=False`,
`needs_review=True`. The edgartools fallback *would* reconstruct at 0.980 coverage but
`needs_fallback` (`fallback.py:41-48`) returns False because no single span >50% (biggest 0.318).
*Fix in principle (any one helps):* (1) reject `Item N-<digit>` (kills the `4-08(g)` class —
surgical); (2) broaden `needs_fallback` to also fire on `"1" not in spans and rt_frac < MIN_COVERAGE`
(routes Duke-shape to the proven-0.980 fallback); (3) prefer the run that starts at the earliest
canonical order containing Item 1 (deepest, riskiest — needs a full A/B sweep). *Guard:* (1) must
target `\d-\d` not all dashes (real `Item 7 - MD&A` exists); (2) stays gated on the cheap coverage
signal so clean filings aren't pulled into the fallback.

### 2d. `drop_other` — n=16 (legacy 1994 filings) → **INGEST/HARNESS gap (not malformed input)**
The raising members are **1994 Q1/Q2 SGML** filings (Corning, Chemical Banking, St Paul, …). The
exception is `ingest.py:58` `ValueError("No filing found…")` because edgartools' full-index coverage
is **hardcoded to start at 1994 Q3** (`available_quarters` floor `(1994,3)`), so anything filed
1994-Q1/Q2 is unreachable via `get_by_accession_number`. The filings **exist live on EDGAR** (direct
archive `…/{cik}/{accession}.txt` → HTTP 200, ~290 KB) — so it is **not** malformed/encoding, **not**
a normalize bug. Same single cause. **Severity sub-finding:** in the *sweep* this is graceful (logged
error row), but in **production `extract()` the `ValueError` propagates UNCAUGHT** — an unreachable
filing aborts the whole call instead of returning a flagged per-filing error. *Fix in principle:*
(safe minimum) make ingest failures a graceful per-filing `fetch_failure`/`needs_review` instead of
an uncaught raise; (coverage fix, optional) direct-archive fallback in `fetch_10k` for pre-1994-Q3.

### 2e. `header_not_self_headed` — n=2 → **MIXED: 1 harness false-fail + 1 TOC mis-select**
- **COST `0000912057-99-007381` (SGML) = a SWEEP-PREDICATE FALSE FAIL.** The header is
  `ITEM 1--BUSINESS` (double-hyphen). Production `_HEADER_RE` accepts `-` and correctly found the
  item; but the sweep's *own* verification `_starts_with_header` (`structural_sweep.py:40`) uses
  `item\s+{k}[.:)\s]`, which does **not** include `-`, so it falsely fails a filing whose extraction
  is fine. → **the 85.6% is a slight UNDERCOUNT.** *Fix:* align the sweep check's separator set with
  production `_HEADER_RE` (a harness correction, not a ruler loosening).
- **GIS `0000950137-08-009268` (HTML) = TOC mis-selected as body** (spans land on whitespace inside
  the Table of Contents; `head=''`). Same cross-reference/TOC family as §2b/§2c. Tractable via the
  same run-selection hardening.

---

## 3. Probe #3 — ranked improvement plan (for a future IMPLEMENT round; nothing done here)

Each candidate is gated, in advance, on an **independent** signal — never coverage / `needs_review` /
`extraction_failure` (forbidden proxies), never by loosening a ruler (G6 auto-discard). One probe per
iteration, fresh worktree, KEEP iff a real independent signal (A structural-pass UPPER-BOUND / B
char-gold / C new named mode / D classification) moves above noise AND the full guard passes.

| rank | fix | clusters addressed | UPPER-BOUND footprint | KEEP gate (independent) | risk |
|---|---|---|---|---|---|
| **1** | Relax `_HEADER_RE` to accept separator-less `ITEM N <title/EOL>` (keep line-start anchor) | `empty(0_items)` | **~67/1656** | Signal A rises on empty cluster; **B (5 char-gold) stay 1.0**; clean filings unchanged | moderate |
| **2** | Cross-ref-intruder run-selection hardening (intruder-tolerant `_split_runs` / reject `Item N-<digit>` / broaden `needs_fallback`) | `lead_missing_high_cov` + `coverage_partial` + GIS TOC | **~56/1656** | Signal A rises on these; **B byte-exact (Item 1 spans)**; no TOC-as-body regressions | moderate–high (lever 3 needs full A/B) |
| **3** | Ingest robustness: graceful per-filing error in `extract()` (+ optional pre-1994-Q3 archive fallback) | `drop_other` | ~16/1656 | A on the subset; **no silent miss introduced** (still `needs_review`) | low (safe minimum) / moderate (archive) |
| 4 (harness) | Align sweep `_starts_with_header` separators with `_HEADER_RE` | `header_not_self_headed` (COST) | ~corrects undercount | re-run sweep; report the corrected (slightly higher) number | low |

**Known classes — confirmed + counted at scale, NOT re-debugged, NOT fixed here:** cross-reference
index (`coverage_very_low`, GE/INTC), run-fragmentation / PART-glued / no-separator
(`lead_missing_low_cov`), large-filing TIMEOUT (now isolated by the killable harness, §C). The named
**ceiling S1** (dual-extractor header-stripped common-mode, MS/Citi) — **did not surface as a distinct
cluster in this 1,656 sample**; the fixes above recover filings whose header text is *present*, a
different population than the stripped-header ceiling.

---

## 4. Probe #1b — SWEEP HARNESS bug: RCA + FIX (the "fix sweep issues" mandate)

The first full run dropped **1,135/1,845** (1,131 TIMEOUT) and reached only 660 swept.
- **RCA (traced, not guessed):** the 90s timeout fired *below* the 73–99s `to_canonical` time of
  1M+ char filings; the harness's daemon-**thread** timeout **cannot kill** a CPU-bound parse, so each
  slow filing leaked a zombie thread churning a core. Over an 85-min run the zombies saturated the box
  and **cascaded healthy filings into timeouts too** — 94 distinct filers dropped ~17 each (whole
  filers, not giants). Standalone re-test proved the "dropped" normal filings parse in <7 s; only the
  genuine giants are slow.
- **FIX (harness code, authorized as a sweep-infra fix):** replaced the daemon-thread timeout with a
  **killable `multiprocessing.Process` per filing** that is `terminate()`d on timeout — actually
  killing the runaway parse, so no zombie, no cascade (`eval/structural_sweep.py`). Re-ran: **drops
  221 → 16**, swept 660 → 1,656. Validated live (former cascade victims like LMT now return real
  results).
- **Scalability finding (honest, feeds ASSIGNMENT's scalability ask):** `to_canonical` is
  **super-linear on 1M+ char filings** (73–99 s; a handful of giant bank/retail filings exceed even a
  180 s budget → the 16 honest drops). A production sweep/batch must bound per-filing CPU and isolate
  giants — the killable-process pattern is the right shape; a `to_canonical` perf pass (or a size
  guard) is a separate future item.

---

## 5. Guards held + disposition

- **REPORTED-only; no extractor fix implemented** (deliverable = evidence + plan). `boundary_gold` /
  `classification_gold` untouched. No ruler loosened (the §2e harness-check alignment is a
  *correction* toward production `_HEADER_RE`, listed as a plan item, not applied).
- Structural-pass labelled **UPPER BOUND, not accuracy** throughout; accuracy floor stays the 5
  char-gold.
- **LLM default-off baseline:** the sweep ran deterministic; `llm_touched` is wired so the census can
  show the LLM footprint — confirmed near-zero (tier off + measured no-gain).
- **S4 does NOT fire:** five unexplained clusters were found and **all are tractable or harness/ingest
  gaps** — the honest outcome is a ranked plan with real fixable work, not a "bounded-tail, nothing to
  do" stop. The named ceiling did not even appear as a distinct cluster.
- **Nothing merged from this worktree; nothing pushed.** Only the LLM tier (default-off) is on `main`.
  The sweep-harness-merge decision and these round-3 fixes are left for review.

## 6. What I did NOT do / verify
- Implemented no fix (by design); footprint columns are UPPER-BOUND cluster sizes, not measured
  recovery rates (a relaxed regex's true recovered-pass-rate + precision cost need implement + A/B).
- Proved each cluster's root cause on representatives (per class), not every member filing.
- 85.6% is an UPPER BOUND on a diverse stratified sample (not unbiased random-EDGAR); it is also a
  slight *under*count due to the §2e sweep-predicate `--`-separator false-fail. Per-stratum CIs are
  wide on rare strata. 16 giant filings are honest drops (super-linear `to_canonical`), not silent.
