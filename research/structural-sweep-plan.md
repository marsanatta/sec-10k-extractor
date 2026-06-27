# Label-free Structural Sweep — Plan (REVIEW DOCUMENT — do NOT execute yet)

**Status:** plan only. No code, no execution. Awaiting review; only after it passes will execution
be requested. **Work in a fresh worktree off `main`; review; merge back; NEVER push.**

## 0. Goal — and what it is / is NOT

**Goal.** Turn "how robust is the extractor?" from *21 hand-picked filings* (N too small — Wilson
CI ±~20%, no population claim possible) into a **reproducible population number + a gross-failure
tail map across ~500 era/sector/structure-diverse EDGAR filings**, computed **label-free** (no human
labelling) so it can be committed and re-run from this repo.

**Why (the one concrete win):** ANALYSIS §8 currently cites a "~130-filing sweep, ~97%
structural-pass" that ran in a *separate worktree* — **not reproducible here**; the only committed
population signal is the §2.5 12-filing batch (~78%). A grader testing held-out filings will probe
exactly this. This sweep makes the population number **reproducible in-repo**.

> **IT IS AN UPPER BOUND ON ROBUSTNESS, NOT ACCURACY.** structural-pass only sees the *gross*
> failure tail (empty body, lead item dropped, no tiling, implausible coverage). It is **blind to
> interior boundary drift** — a right-header/wrong-end span PASSES. So it does **not** prove
> correctness; the accuracy floor stays the **5 human-audited char-gold**. Every reported number is
> labelled "UPPER BOUND, not accuracy". The number may well be ~80–95%, not 100% — that honest
> figure with a tail map beats a cherry-picked 100% on 21.

## 0b. Resolved design decisions (grill)

1. **Sampling frame = a diverse stratified company list.** ~40–60 hand-picked companies spanning
   sectors, their 10-Ks pulled across target years/eras. Controlled strata → per-stratum CIs are
   meaningful; fully reproducible (the list is pinned). The headline is honestly labelled
   **"diverse stratified sample — UPPER BOUND"**, NOT an unbiased random-EDGAR population estimate.
   *(Because the company list is curated, each company carries a hand-tagged sector, so per-sector
   slicing is feasible without deriving SIC at scale.)*
2. **Form-type = full-10-K headline + 10-K/A as a SEPARATE stratum.** The headline structural-pass
   number is over true `10-K`s only (interpretable — the extractor's main job). Amendments are still
   fetched and reported as their own row (they legitimately lack Part I → structural-fail for a
   non-bug reason; reporting them separately keeps it honest without dragging the headline).
3. **Size = staged.** Build the pinned accession list for up to ~1000, but **run ~500 first**
   (~1 h) to validate the harness + get the headline (aggregate CI ~±3–4%). **Extend the SAME pinned
   list toward 1000 only if rare-stratum CIs** (pre-2001 SGML, 2001–2008 HTML) are still too wide.
   Over-sample the 2001–2018 middle either way.

## 1. The metric — structural-pass (precisely, label-free)

Per filing, computed from `segment()` output + the existing invariants (no `validate.assess`, no
XBRL, no confidence — that's what makes it fast). A filing **passes** iff ALL hold:
- `segment(canonical)` returns a non-empty body;
- `structural_invariants(ranges)` all True (monotonic, non-overlapping, tiling) — `sec10k/validate.py:28`;
- `round_trip(ranges, canonical)` ok AND its coverage fraction ≥ `MIN_COVERAGE` (0.4) —
  `validate.py:41`;
- **lead Item 1 present** AND each present big item {1,1A,7,8} starts with its own `Item N` header.

Reported **per stratum (era / sector / structure) with N + a Wilson 95% CI** (`evalkit.wilson_ci`),
**never pooled**. The harness re-uses the production invariants directly, so the predicate is the
same one Signal A uses — no new ruler invented.

## 2. What gets built (committed harness)

- `eval/collect_accessions.py` — a **stratified accession collector**: walk EDGAR submissions for a
  fixed company list across target years/eras, emit a pinned, immutable list. Honours 10 req/s +
  descriptive User-Agent. Output committed as `eval/sweep_accessions.txt` (so the sample is fixed
  and reproducible, not re-sampled each run).
- `eval/structural_sweep.py` — the **fast-mode sweep**: for each accession,
  `fetch_10k → to_canonical → segment()` → compute the §1 predicate → record `{accession, era,
  sector?, structure-guess, pass, coverage, lead1, items, reason-if-fail}`. Bounded concurrency,
  per-filing timeout, and **logs every dropped/errored filing** (no silent truncation). Writes
  `eval/sweep_report.md` (committed) + `eval/sweep_report.json` (gitignored, like `report.json`).
- A small **offline unit test** (`tests/`) for the pass/fail predicate on **synthetic** spans: a
  clean tiling passes; an empty / collapsed-single-item / lead-missing case fails. This
  validates-the-verifier (the sweep's own verdict logic) and keeps the offline gate honest.

## 3. Scope / scale

- **Run ~500 first (staged, §0b.3), extensible to ~1000.** Drawn from the **diverse stratified
  company list (§0b.1)** — each company's 10-Ks across eras (pre-2001 SGML / 2001-2008 HTML /
  2009-2018 HTML-iXBRL / 2019-2025 iXBRL — deliberately **over-sampling the under-covered 2001-2018
  middle**). Sliced by **era × hand-tagged sector × structure-guess**; sector comes from the curated
  list (real), structure is a best-effort tag from the result. **Headline over true 10-Ks; 10-K/A as
  a separate row (§0b.2).**
- **Fast mode only** (`segment()`-level), because the full pipeline (`edgartools .obj()` + XBRL per
  filing) is ~45 s/filing and irrelevant to structural geometry. Fast mode ≈ 5–10 s/filing → ~500
  in ~1 h, network-bound.
- **Honest limit of fast mode (stated in the report):** it **cannot** compute `needs_review`, so it
  cannot say whether a gross fail was *flagged* vs *silent*. A **targeted full-pipeline pass on the
  fail tail** (the handful that fail) recovers flag status and confirms the abstention-gate holds at
  population scale.

## 4. Discipline / guards (non-negotiable — same contract as the autoresearch rounds)

- **REPORTED-only.** The sweep gates nothing, feeds no production decision, and **never edits,
  freezes, or regenerates** `boundary_gold.json` or `classification_gold.json`. It reads, it reports.
- **Char-gold stays 5; classification-gold stays FROZEN human-only.** Untouched.
- **No ruler loosened (G6).** `validate.py` invariants and `evalkit` scorers are reused as-is;
  `MIN_COVERAGE` and the header checks are **not** relaxed to make the population number look better.
- **Regex stays PRIMARY, fallback CONSERVATIVE** — the sweep runs `segment()` (the regex tier)
  directly; it does not change the production tiers.
- **Offline suite stays green AND network-free** (`SEC_EDGAR_USER_AGENT` unset still passes) — the
  new harness is on-demand/network, NOT in the CI gate; only its synthetic predicate test is offline.
- **Every structural-pass number labelled "UPPER BOUND on robustness, NOT accuracy."**
- **No silent truncation** — dropped/errored/rate-limited filings are logged and counted; the
  denominator is honest.

## 5. Outputs + where the number lands

- `eval/sweep_report.md` — population structural-pass per stratum (with N + Wilson CI), the
  gross-failure tail (accession + reason), and the fast-mode caveat.
- **ANALYSIS.md §2.5** — replace the external/uncommitted "~130-filing ~97%" reference with the
  **committed, reproducible** sweep number (labelled UPPER BOUND), citing `eval/structural_sweep.py`.
- Any **genuinely new failure mode** the tail surfaces → `research/round-2-failure-modes.md` (or a
  sweep-specific notes file), flagged-not-silent confirmed via the §3 full-pipeline tail pass.

## 6. Honest caveats (restated for the reviewer)
- UPPER BOUND, not accuracy — does not touch the correctness story (still 5 char-gold).
- The number may be unflattering (~80–95%); that is the point — honest > cherry-picked.
- Per-stratum CIs are wide on rare strata (small N per bucket) even at total N=500 — stated, never
  over-claimed.
- On-demand network; not reproducible offline; sample is the pinned `sweep_accessions.txt`.

## 7. Execution model + bound
Fresh worktree off `main` → build harness + collector → collect the pinned list → run the bounded
sweep (~500, target ~1 h) → full-pipeline pass on the fail tail → write report + fold into ANALYSIS
→ commit on the branch → **report for review; NEVER push; merge back only after review.** If EDGAR
rate-limits or flakes, log the drops and report the honest denominator — do not pad or fake.

## 8. What this does NOT do
- Does not change the production pipeline, the confidence layer, or any gold.
- Does not raise accuracy — it raises *population breadth + reproducibility of the robustness claim*.
- Does not run in CI (network).
