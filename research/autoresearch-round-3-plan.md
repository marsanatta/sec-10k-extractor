# Autoresearch Round 3 — Plan (REVIEW DOCUMENT — do NOT execute yet)

**Status:** plan only. No code touched, no execution. Awaiting review against the same bar as
rounds 1–2; only after it passes will execution be requested. **Work in a fresh worktree; review;
merge back; NEVER push.**

**Baseline:** the structural-sweep harness (`eval/structural_sweep.py`, branch
`eval/structural-sweep`, 88.9% headline committed) **plus** the real-Copilot escalation tier
(branch `feat/copilot-llm`). Round 3 assumes BOTH are merged to `main` first — it builds on the
committed sweep harness and may exercise the real LLM tier on a debugged miss. **Iteration 0
re-confirms the merged baseline** (offline suite green network-free; the 471-sweep number
reproduces) before any probe.

**This is a focused DELTA from rounds 1–2, not a re-author.** Everything in
`autoresearch-round-1-plan.md`, `autoresearch-round-2-plan.md`, and `structural-sweep-plan.md`
still binds unchanged unless restated here:
- **Signals A / B / C / D** carry over verbatim — A = stratified structural-pass (**UPPER BOUND on
  robustness, NOT accuracy**, labelled on every line), B = gold recall on the 5 human-audited
  char-gold, C = count of new named flagged-not-silent modes, D = classification-match-rate vs the
  frozen `classification_gold.json`. Independence justifications + the forbidden-proxy list
  (presence recall, `needs_review` count, `extraction_failure` count, edgartools-alone, coverage
  fraction) carry over.
- **Guards G1–G7** carry over (offline green network-free; regex PRIMARY; fallback CONSERVATIVE;
  char-gold = 5 never auto-frozen; baseline integrity; rulers tighten-only; classification-gold
  human-only). **No ruler — `MIN_COVERAGE`, the header checks, the invariants, the scorers — is
  loosened to make a miss "pass."**
- **One probe per iteration**, ROI order; **KEEP iff a real independent signal moves above noise
  AND the full guard passes, else DISCARD + document**; **~25-iteration bound**.

---

## 0. The ask, evaluated (why this is round 3, and the one correction)

The request: scale the sweep 471 → ~1000, track the misses during the run, `/eng-debug` **each**
miss to learn why it failed, and produce another improvement plan.

**Verdict: accept — it maps directly onto a LITERAL Task-2 requirement** ("clearly list filings /
companies that are still difficult, unreliable, or unsupported, **with concrete failure cases**")
and onto Level-A rewards (failure modes honestly surfaced, edge-case handling, scalability
analysis). No basis to deny.

**One necessary correction — cluster, don't per-filing.** ~1000 filings ⇒ ~110 misses.
`/eng-debug` is a heavyweight 5-phase root-cause skill; running it on each of ~110 filings is
over-scoped and largely re-derives shared root causes. **The misses already cluster** — the sweep
tags every fail with its reason. The correct shape is: **group by reason → confirm + count the
already-named classes at scale → `/eng-debug` ONE representative of each UNEXPLAINED cluster.** Net:
~2–3 genuinely-new debug sessions, not ~110.

**Honest framing.** This is the same Modify→Verify→Keep/Discard loop, round 3. Expect a **mix**:
mostly **re-confirmation of known classes / the named common-mode ceiling** (a valid negative
result — "the tail is bounded"), plus possibly **1–2 new tractable fixes**. Any fix still earns a
KEEP only on an independent signal (A / B / D), never on coverage / `needs_review` /
`extraction_failure`.

**Honest cost.** 1000-sweep ~30–40 min (label-free, network-bound) + clustering (free, already
tagged) + ~2–3 `/eng-debug` + write-up. **1000 vs 471 barely moves the headline** (~88–89%); its
real value is a richer failure census + tighter rare-stratum CIs. That is the trade being made
explicit, not hidden.

---

## 1. The current 471 misses ALREADY cluster — the evidence for "cluster, don't per-filing"

From the committed `eval/sweep_report.md` (47 full-10-K fails + 8 drops). This is the load-bearing
grounding for §0's correction:

| cluster (sweep `reason`) | n | representative members | already a named class? | round-3 action |
|---|---|---|---|---|
| **`empty` (0 items)** | 21 | OXY ×6 (all eras), GIS ×4, USB ×4, HON ×2, MCD ×2, TXN, SLB, D | **partly** — header-text-stripped common-mode (MS/Citi). But OXY/GIS/USB recur across SGML+HTML+iXBRL → smells company-structural, maybe **not** the ceiling | **/eng-debug 1 rep (target #1)** — is it the ceiling, or a fixable normalization gap? |
| **`coverage:~0.01`** | 7 | GE ×4, INTC ×3 | **yes** — cross-reference index (GE FY2023, named) | confirm + count at scale |
| **`lead_item_1_missing`, high-cov (≥0.85)** | ~7 | XOM-25 (0.92), MMM-10 (0.94), DUK-13 (0.89), OXY-25 (0.93), GE-13 (0.89) | **no** — body tiles fine, only the LEAD Item 1 header is missed | **/eng-debug 1 rep (target #2)** — recoverable Item 1 header variant? |
| **`lead_item_1_missing`, low-cov** | ~9 | BAC ×2, WMT-03, HON-01, CSCO ×2, MRK, PEP, BMY | **yes** — run-fragmentation / PART-glued / no-separator (all named) | confirm + count |
| **`coverage:0.07/0.37`** | 2 | OXY-13, T-04 | borderline of the `empty` class | folds into target #1 |
| **`header:1`** | 1 | COST-99 | edge (body fine, Item 1 not self-headed) | note, low priority |
| **TIMEOUT (drop)** | 7 | BAC, MET, FRC large filings | **yes** — large-filing perf (named) | confirm + count |
| **`UnicodeEncodeError` (drop)** | 1 | a 1994 SGML | **harness** bug (Windows console), not pipeline | fix harness, re-run |

→ **47 fails collapse to ~2 genuinely-unexplained clusters.** The rest are already-named classes to
**confirm + count** at 1000-scale, not to debug 100×.

---

## 2. Per-iteration SCOPE (ONE probe per iteration, ROI-ranked)

### #0 — Re-baseline on merged main (iteration 0)
Confirm offline suite green network-free (G1); the 471-sweep reproduces; real-Copilot tier present
but `$0`-fallback when unset. Record before any probe.

### #1 — Scale the pinned sample 471 → ~1000 *(Signal A resolving power + a fuller miss census)*
- Extend `eval/sweep_accessions.txt` along the SAME stratified frame (over-sample the thin strata:
  pre-2001 SGML, the `ixbrl` era which is the weakest at 82.8%, and the `energy`/`industrial`
  sectors which are the weakest at 71%/82%). Accession-pinned, immutable, verified-fetchable before
  pinning.
- Re-run the committed sweep (resumable, incremental — already built). Headline stays labelled
  **UPPER BOUND, not accuracy.**
- **The miss-tracking the request asks for is already a property of the harness** — every fail is
  recorded with `{accession, era, sector, reason, items, cov, lead1}`. The only new step is a tiny
  **cluster-export** (group the fail records by `reason` into the §1 table shape) so the debug
  targets fall out mechanically. No new ruler, no production change.
- **KEEP** (report the bigger number) iff guard G1–G7 green and no ruler was touched. The number is
  expected to land ~87–90% — **report it honestly even if it dips**; a bigger denominator with a
  fuller tail map beats a flattering small-N figure.

### #2 — `/eng-debug` the UNEXPLAINED clusters (cluster reps, NOT per filing) *(Signal C + maybe a fix)*
- **Target #1 — the `empty` cluster** (OXY / GIS / USB, ~21 filings). Debug ONE representative
  (e.g. OXY FY2007 + cross-check OXY across eras, since OXY fails empty in SGML, HTML **and**
  iXBRL — that recurrence is the tell). The decisive question: **is this the named header-text-
  stripped common-mode ceiling (S1, out of scope), or a recoverable per-company / styled-markup
  normalization gap (a real, tractable fix)?** The root cause is shared across the cluster, so one
  debug resolves all ~21.
- **Target #2 — the high-coverage `lead_item_1_missing` sub-cluster** (XOM-25, MMM-10, DUK-13,
  OXY-25; coverage ≥0.85). Body tiles correctly; only the lead Item 1 header is missed. Debug one
  rep: **is there an Item 1 header variant the regex can conservatively recover** without widening
  the pattern on clean filings (G6)?
- **The already-named clusters are CONFIRMED + COUNTED, not debugged** — cross-ref index, run-
  fragmentation, PART-glued, no-separator, large-filing TIMEOUT each map to a prior round's named
  mode; the sweep just shows them at population scale.
- Output of this probe: each new cluster → `research/round-3-failure-modes.md` (mechanism +
  accession + flagged-not-silent evidence via a full-pipeline spot-check), and a **classification**
  of each cluster as **tractable-fix** vs **named-ceiling (S1)**.

### #3 — The improvement plan (ranked) *(the deliverable the request asks for)*
- Rank the candidate fixes that fell out of #2 by ROI, **each tagged tractable vs ceiling**, each
  with its earn-condition stated in advance:
  - A tractable normalization/header fix counts as a **KEEP only if Signal A (structural-pass)
    rises with the full guard held** — and **NOT** by loosening `MIN_COVERAGE` or widening the
    regex on clean filings (G6 auto-discard), and **NOT** credited to coverage/`needs_review`
    moving (forbidden proxies).
  - A boundary/classification fix counts as a KEEP only on **B (char-gold)** or **D
    (classification-gold)**, with controls held — exactly the round-2 discipline.
- If a cluster traces to the named common-mode ceiling, **document it as S1 and do NOT fake a fix**
  — "bounded, needs a decorrelated non-header/CRF extractor, out of scope" is the honest outcome
  and is itself a Task-2 "concrete failure case."

**ROI order:** #1 scale + cluster-export (cheap, enables everything) → #2 debug the 2 unexplained
clusters → #3 ranked improvement plan. Any actual fix implementation is a SEPARATE later iteration
under the standard KEEP/DISCARD gate — **this round's deliverable is the evidence + the plan, not
the fix.**

---

## 3. KEEP / DISCARD — unchanged

- **KEEP** iff a real independent signal (**A / B / C / D**) moves above noise **AND** guard
  (G1–G7) passes; **else DISCARD + document** (discards recorded in `round-3-findings.md` + a
  `"decision":"discarded"` record in `round-3-progress.json`).
- A miss "explained away" by relaxing a ruler is a **fail**, not a pass (G6). A cluster honestly
  classified as the named ceiling, with the fix deferred, is the discipline working — credit it.
- The bigger sweep number is reported as Signal A movement **only as UPPER BOUND on robustness** —
  it never becomes an accuracy claim.

## 4. THE GUARD — G1–G7 (carried over)

Exactly rounds 1–2. The sweep + the debug are **REPORTED-only**: they gate nothing, change no
production tier, and **never edit / freeze / regenerate** `boundary_gold.json` or
`classification_gold.json`. If a debug motivates an actual code fix, that fix is a separate
iteration that must pass the full guard — the debug itself only diagnoses.

## 5. STOP conditions

- **S1** — a cluster traces to the named common-mode ceiling (regex + edgartools both header-
  anchored fail together; needs a decorrelated non-header / CRF extractor — out of scope).
  Disclose, don't fake. **The `empty` cluster resolving to S1 is a likely and acceptable outcome.**
- **S2** — plateau on A / B / C / D across K iterations.
- **S3** — ~25-iteration budget.
- **S4 (round-3-specific)** — **the debug census shows no new tractable cluster** (every miss maps
  to an already-named class or to S1). Then the deliverable is the **confirmed, bounded failure-
  case list at population scale** — a complete, honest result — and the round STOPS without
  manufacturing a fix.

## 6. Findings, artifacts, and no-push (spelled out)

- `research/round-3-findings.md` — human narrative; per iteration: probe, signal deltas (A/B/C/D
  with N), guard status (G1–G7), KEEP / DISCARD, and *why*. Every structural-pass number labelled
  **"UPPER BOUND, not accuracy."**
- `research/round-3-failure-modes.md` — any new named mode + each cluster's tractable-vs-ceiling
  classification (mechanism + accession + flagged-not-silent evidence).
- `research/round-3-progress.json` — **append-only** machine ledger, same schema as rounds 1–2.
- The **scaled `eval/sweep_accessions.txt` + regenerated `eval/sweep_report.md`** (committed); the
  cluster-export table; `report.json`/`sweep_report.json` stay gitignored.
- The ranked improvement plan folds into **ANALYSIS.md §6 (failure modes)** + the README
  "still-difficult, concrete failure cases" list — the literal Task-2 artifact, now evidence-backed
  at population scale.
- **Execution runs in a FRESH isolated git worktree off the merged `main`; reviewed; merged back
  after review; NEVER pushed.** Gold files change only via the human checkpoint, never the autoloop.

## 7. How this meets the bar (self-check)

| Bar item | Where met |
|----------|-----------|
| Directly produces Task-2's "filings still difficult, with concrete failure cases" | §0 + §2 #2/#3 + §6 (folds into ANALYSIS §6 + README) |
| Signals independent; structural-pass labelled UPPER-BOUND-not-accuracy on every line | §0 + §1 + §3 (A/B/C/D carry over; sweep number never an accuracy claim) |
| Effort proportionate — no 110× wasted debug | §1 (47 fails → ~2 unexplained clusters) + §2 #2 (debug reps, not filings) |
| Any fix earned on an independent signal, not a proxy | §2 #3 + §3 (KEEP on A/B/D with controls; coverage/`needs_review`/`extraction_failure` forbidden) |
| Guard protects offline gate + human-gold floors; no ruler loosened | §4 (REPORTED-only) + G1/G4/G6/G7 carried over |
| Stop conditions real; honest negative result allowed | §5 S1 ceiling / S2 plateau / S3 budget / **S4 census-complete-no-new-tractable-cluster** |
| Scope bounded; nothing pushed | §2 one probe/iter; §6 fresh worktree, merged after review, never pushed |
