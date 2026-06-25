# Autoresearch Round 1 — Plan (REVIEW DOCUMENT — do NOT execute yet)

**Status:** plan only. No code touched. Awaiting your review against the stated bar; only
after it passes will execution be requested.

**Baseline:** current clean `main`.
**Execution model (later):** isolated git worktree branched from `main` → iterate →
review → merge back to `main`. **Never pushed.** `report.json` stays gitignored; `.env`
never committed; `boundary_gold.json` is human-only.

**Framing — structural-invariant-guided, no attribution layer.** There is deliberately no
per-task attribution/provenance-tracing layer, and the round does not need one. The
**verification tower is the targeting system**: structural invariants + decorrelated
cross-checks + char-exact human gold + the mutation battery decide where to aim and whether
a change helped. This plan is the *configuration*; the **domain brain** is the external
iteration playbook `ITERATION-PLAYBOOK-10k.md` (read), and
the loop is its one-liner: *baseline → analyze failures by bucket → ONE treatment → measure
above noise → keep iff a real signal improves AND guard passes → human-audit the gold →
repeat → stop at the named ceiling.*

**Engine note (honest divergence from `/autoresearch:plan`).** The planning wizard wants a
*single* mechanical number + a verify command + an immediate launch. I am **not** collapsing
to one number: the playbook (§0–§1) forbids a single blind metric because a hill-climber on a
blind proxy is Goodhart. This round keeps **three independent signals** and uses the engine
purely as the Modify→Verify→Keep/Discard executor, **not** as a single-metric hill-climber.
The engine is not rebuilt (playbook Tooling note).

---

## 1. CLIMBABLE METRICS — three INDEPENDENT signals

A kept change must move **at least one** of these *above noise* without degrading the others,
and pass the GUARD (§2). None may be gamed by a self-consistent or extraction-path-correlated
proxy. **Forbidden as primary signals** (Goodhart proxies the optimizer will wall-green):
`presence recall`, `needs_review` flag-count, and **any number derived from edgartools alone**
(edgartools is *inside* the extraction path as the Tier-2 fallback → correlated → that would be
self-consistency).

### Signal A — Stratified structural-pass rate — **UPPER BOUND on robustness, NOT accuracy**

- **Definition (label-free):** a filing passes iff its output geometry is sound — body
  non-empty, coverage plausible (round-trip fraction ≥ the coverage floor), spans
  non-overlapping, offsets monotonic, **round-trip byte-exact** against the source, every
  present big item {1, 1A, 7, 8} **starts with a real "Item N" header**, and the spans tile.
- **Reported stratified** by era / filer-type / sector / structure, **per stratum with N,
  never pooled** (pooling lets easy iXBRL hide the hard cases).
- **WHY it is an UPPER BOUND, not accuracy (label this on every report line):** it is a cheap
  net for the *gross* failure tail. It **cannot** see interior boundary drift, a scattered-tail
  drop (JPM Item 7 stub passes it), or a swallow that still covers > 40%. A right-header /
  wrong-end span **PASSES**. So "structural-pass = X%" means *"X% have a plausibly-tiled body
  with header-anchored big items"* — an **upper bound on robustness, not a correctness claim.**
  The report must print the words "UPPER BOUND — not accuracy" beside the number.
- **WHY independent (no self-consistency, not edgartools):** it is computed from the geometry
  of the output against the **source bytes** (round-trip, tiling, monotonicity) plus a literal
  header-token check. It never asks an extractor "are you right?", and it never consults
  edgartools or edgar-corpus. The source bytes are ground truth for *coverage*; the invariant
  can fail even when the regex is "confident". Independent of the segmentation decision.

### Signal B — Gold recall / `boundary_match_rate` on the human-audited char-exact gold

- **What:** `boundary_scores` (`sec10k/evalkit.py`) vs `eval/boundary_gold.json`, IoU ≥ 0.9,
  over the **5 human-audited filings** (apple-fy2024, ko-fy2023, msft-fy2023, m2i-fy2023,
  msft-fy1995). The **only** signal that turns a *wrong* boundary into a number.
- **WHY independent (decorrelated, sees the common-mode):** the gold is **human-labeled** —
  m2i by title-reading, msft-1995 by reading the SGML body and locating sections — so it is
  decorrelated from **both** regex AND edgartools. It sees through the common-mode that makes
  the regex↔edgartools cross-check only a *partial* gate (both header-anchored, they agree on
  big items and fail *together* on header errors). Independent of the production code's lineage.
- **Above-noise rule:** N = 5 → wide CIs. A delta counts only if it survives re-run; growth of
  the gold is **out of the autoloop** (G4 / §6 human checkpoint), never auto-frozen.

### Signal C — Count of NEW failure modes found (named, with accession + mechanism)

- **What:** number of *qualitatively distinct* breakages surfaced this round, each (i)
  **flagged-not-silent** (its `needs_review` fires — verified through the full pipeline, not
  fast-mode), (ii) **named** with mechanism + concrete accession, (iii) **distinct** from the
  already-named classes (run-fragmentation, header-text-stripped, no-separator, collapsed-SGML,
  10-K/A scope, scattered-item).
- **WHY independent:** it is an *enumeration*, not a self-graded score. A new mode lives
  precisely where signals **disagree** or where Signal A fails — it cannot be produced by an
  extractor agreeing with itself. It adds coverage knowledge, not a number to smooth; it is a
  **discovery** signal (find the tail), capped by §5.

---

## 2. THE GUARD — what must NOT regress (revert if it does)

Every kept change passes **all** of G1–G5. Each with how it is checked.

| ID | Invariant | How checked |
|----|-----------|-------------|
| **G1** | Offline fixture suite **green AND network-free**, ≥ the committed baseline (currently **67**, floor **65**) | Run `python -m pytest -q` with **`SEC_EDGAR_USER_AGENT` unset and no network**; assert exit 0 and count ≥ baseline. The suite is fixture/monkeypatch-based, so passing with the env var unset *proves* network-freeness. Red suite ⇒ verifier health regressed (playbook §1: `test_boundary_crosscheck.py` + `test_evalkit.py` batteries must stay green) ⇒ every other number suspect ⇒ revert. |
| **G2** | **Regex stays PRIMARY** | On the cooperative clean filings (apple/ko/msft-2023) assert `tier == "regex"` (no `edgartools-fallback` in `provenance.extractors`) **before and after**. If a change makes the fallback fire on a previously-clean filing, that is a regression even if a number rose. |
| **G3** | **Fallback stays CONSERVATIVE** | Assert the set of filings where `tier == "fallback"` does **not grow** beyond baseline; the fallback fires only on its existing guards (empty / single-item-collapsed-over-doc with lead missing), and where edgartools is *worse* (GE Item 7A parses to 560 KB > whole doc) the trigger still keeps the regex result. |
| **G4** | **Char-gold stays 5, NEVER auto-frozen** | Assert `len(boundary_gold.json) == 5` and the five ids unchanged; assert no gold entry's `source` becomes regex/edgartools/edgar-corpus-derived. The loop may **propose** gold candidates but may **not** freeze them — freezing requires the §6 human-audit checkpoint and is OUT of the autoloop. |
| **G5** | Baseline integrity | Correct filings stay **0 false-alarm** on the cross-check (playbook §2); **presence recall holds** — never trade a boundary gain for a dropped item. |
| **G6** | **Don't loosen the ruler** — invariant (`validate.py`) & scorer (`evalkit.py`) code may change **only to TIGHTEN or CORRECT, never LOOSEN** | The mutation/drift batteries (`tests/test_boundary_crosscheck.py` swallow/merge/swap, `tests/test_evalkit.py` 200-char drift) **still catch every injected fault**, AND the diff is asserted to relax **no** pass condition — no lowered coverage floor, IoU threshold, header check, or any acceptance gate. Any edit to an invariant or the scorer must keep the full battery green **and** be justified in the findings as a *tightening/correction*. |

**Why G6 — don't change the ruler.** Signal A is *defined by* the structural invariants in
`sec10k/validate.py`, and Signal B by the scorer `sec10k/evalkit.py:boundary_scores` — these
are the **rulers that judge every change**. A loop allowed to relax a coverage floor, an IoU
threshold, a header check, or any pass condition could make a change "pass" by **moving the
ruler**, not by improving the extraction — pure Goodhart, and circular (the metric grades
itself). So those files may be edited **only** to *tighten* (catch more) or *correct* (fix a
genuinely wrong threshold); the mutation/drift batteries must stay green; and the diff must
carry an explicit **"no pass-condition relaxed"** justification in
`research/round-1-findings.md`. **Any relaxation auto-discards the iteration** — loosening the
check that judges a change is circular.

---

## 3. PER-ITERATION SCOPE — ONE probe per iteration, ROI-ranked

One treatment per iteration (playbook §5.3). Ordered by ROI. `(a)–(d)` are your candidate
labels; the **number** is the ROI rank / likely run order.

### #1 — (a) Stratified eval growth (accession-pinned, immutable) — *foundational, near-zero risk*
- **What:** add accession-pinned filings across under-covered strata (era / filer-type /
  sector / structure), each with hand-labelled `expected_present`; pin by **exact accession**
  (immutable, reproducible, sidesteps the 10-K/A selection bug). Residual hard cases enter as
  explicit tracked **RED**, not hidden.
- **Signal moved:** raises the *resolving power* of Signals A & C (per-stratum N) — it does not
  itself fix capability, which is why it runs first: it makes the next probes measurable.
- **Guard:** G1 (new filings must not need network in the offline suite — they live in the
  on-demand eval batch, not pytest), G4 (do **not** expand char-gold blindly), G5.
- **KEEP iff:** the new strata are measured and reported per-bucket with N; **DISCARD** a
  filing only if it cannot be accession-pinned or its `expected_present` can't be hand-labelled.

### #2 — (b) Form-type-aware `expectation()` fix — *highest CAPABILITY ROI*
- **The gap (code-confirmed):** `template.expectation()` keys only on `fiscal_year` +
  `smaller_reporting`; it is **form-blind** — it never reads `raw.form`, even though
  `RawFiling.form` is populated. So a Part-III-only **10-K/A** is judged as a broken full 10-K
  and emits a flood of false `extraction_failure`s — *flagged* but for the **wrong reason**.
- **The fix:** thread `raw.form` into `FilerProfile`; in `expectation()`, when the form ends in
  `/A`, return `MAYBE_INCORPORATED` / `OPTIONAL` for Part I–II items. Touches
  `template.py` + `pipeline.py` + `validate` provenance.
- **Signal moved:** Signal A on the amendment strata (false-failure items reclassified →
  structural-pass rises *correctly*); directly addresses the tracked **scwo-fy2025-amend RED**.
- **Independent check (anti-self-consistency):** assert amendment filings **stop** emitting
  Part-I `extraction_failure`s **while full 10-Ks are unchanged** (no full-10-K loses an
  expected item). The "unchanged full 10-K" half is the decorrelated control.
- **Guard:** G1 (re-label amendment unit cases), G2/G3 (segmenter untouched), G5.
- **KEEP iff:** Signal A rises on amendments AND full-10-K Signal A/B unchanged AND guard green.

### #3 — (c) Structural sweep over a stratified tail — *discovery engine for Signal C*
- **What:** a label-free structural sweep (`segment()`-only fast mode) over a stratified,
  accession-listed tail to **map the gross-failure tail** at population scale; full-pipeline
  spot-check the genuine fails to confirm `needs_review` fires (flagged-not-silent).
- **Signal moved:** Signal C (new named modes) + Signal A breadth (UPPER BOUND, per stratum).
- **Honest limit (state it):** fast mode **cannot** compute `needs_review` (needs the full
  validate stack) — so the sweep maps the *gross* tail only; flag status comes from the
  full-pipeline spot-check. Any sweep that bounds coverage (top-N, no-retry) must `log` what
  was dropped — no silent truncation.
- **Guard:** G1, G4 (sweep output is **never** frozen into gold), G5.
- **KEEP iff:** ≥ 1 genuinely new, named, flagged failure mode (Signal C) with a concrete
  accession; else **DISCARD** the sweep config and document that the tail held no new class
  (a high-value negative result).

### #4 — (d) Close the ESCALATION APPLY-LOOP — *functional-honesty fix, STRICTLY gated*
- **The gap (code-confirmed, `sec10k/escalation.py:89-93`):** `run_escalation` calls
  `client.adjudicate(...)` and sums `adj.input_tokens` / `adj.output_tokens`, but **never uses
  `adj.text`** to update the boundary. The model's answer (a line number, per
  `build_lib_prompt`) is **computed, paid for, and discarded** — so the escalation tier flags
  candidates but **fixes no boundary even if a real provider were wired**, and the existing
  `test_mock_client_token_ledger_is_summed` asserts only that the token ledger sums, **not**
  that a boundary moves. The tier is currently **decorative**.
- **The fix:** parse `adj.text` → line number → map it back to a **canonical char offset** →
  update the item's `char_range`; re-run the structural invariants on the new span so
  round-trip / tiling / monotonicity still hold. The real provider may **stay deferred**; the
  **apply-step + its test** make the tier genuinely functional instead of decorative.
- **THE GATE — an INDEPENDENT boundary-correction check (mutation-battery style, NOT token
  accounting):** the test must
  1. take a known-good filing that has char-exact gold (or a known-correct offset),
  2. **inject a deliberately-WRONG boundary** for an item,
  3. have a **mock client return the CORRECT line**,
  4. assert the item's span **actually MOVES to the correct position**, checked against the
     **char-exact gold / known-correct offset at IoU ≥ 0.9** — **NOT** that tokens accrued.

  **If the corrected span cannot be proven against an independent reference, the apply-loop is
  NOT claimed to work.** This reuses the validate-the-validator discipline (inject fault →
  assert the mechanism corrects it): a check that can't fail on a wrong input isn't verifying.
- **ROI honesty:** with the provider **deferred**, this moves **no** real-run Signal A/B (no
  call → no apply); its value is **functional honesty** (decorative → functional) + closing a
  *verified* code gap, proven by the gold-checked mutation test. Ranked last on metric-ROI,
  but high on correctness/honesty — stated plainly.
- **Guard:** G1 (existing token-ledger test stays green; **deferred behavior unchanged** — no
  call ⇒ no apply ⇒ spans identical), G2/G3 (regex/fallback untouched), G4, G5.
- **KEEP iff:** the injected-wrong → mock-correct → span-moves-to-gold test passes AND deferred
  behavior is byte-identical to baseline AND guard green; else **DISCARD** + document.

---

## 4. KEEP / DISCARD rule

- **KEEP** a change iff **≥ 1 independent climbable signal improves above noise** (Signal A
  per-stratum, or Signal B gold recall, or Signal C a genuinely new *named* mode) **AND the
  full GUARD (G1–G5) passes.**
- **DISCARD** otherwise — and **document the discard honestly** in `research/` (what was tried,
  which signal failed to move / which guard tripped, hypothesis why). A discard is a *result*,
  not a failure. (Precedent: the scout run discarded a coverage win that broke `start_correct`
  — the anti-Goodhart discipline working.)
- **Anti-gaming:** a number that moves only on a **forbidden proxy** (presence recall,
  `needs_review` count, edgartools-only) does **not** count as improvement.
- **Above-noise:** gold N is small — re-run / propose more gold (human checkpoint) before
  trusting a delta; structural-pass deltas reported per stratum with N.

---

## 5. STOP conditions (bounded, ~25 iterations)

- **S1 — Named common-mode ceiling reached.** When the remaining failure tail traces to the
  **dual-extractor common-mode** (regex + edgartools both header-anchored, failing *together* —
  B3; e.g. MS / Citi FY2024 header-text-stripped iXBRL with zero literal "Item N" tokens) or to
  **GE-class ungoldable** integrated/header-less filings (B2), **STOP and disclose as a named
  ceiling.** The only fix is a **decorrelated non-header / CRF line-labeller** — **out of the
  4-day scope.** Do not fake a green on these.
- **S2 — Plateau.** Signal A (per stratum) and Signal B (gold) show no above-noise gain across
  K consecutive iterations.
- **S3 — Budget.** Hard cap **~25 iterations**.
- Every stop is **disclosed**, never hidden.

---

## 6. Where findings are written + no-push

- This plan: `research/autoresearch-round-1-plan.md`.
- **Human narrative:** `research/round-1-findings.md` — the prose log: for each iteration the
  probe, the three signal deltas (with N), guard status, **KEEP / DISCARD**, and *why*
  (discards documented in full). Mirror a one-line entry per iteration into `prompts/`
  (playbook §5.7).
- **Machine-readable state-of-record:** `research/round-1-progress.json` — **append-only**
  (one JSON record per iteration, appended atomically) so partial progress **survives a crash**
  and the loop's mid-run state is trackable / queryable / **resumable**, not just prose. The
  prose `round-1-findings.md` stays the human narrative; this JSON is the structured source of
  truth for resume — the two must agree. **Schema (one record per iteration):**
  ```json
  {
    "iter": 7,
    "probe": "b",                          // a | b | c | d
    "target": "0001140361-25-000000",      // accession / stratum / item under treatment
    "signals_before": {
      "structural_pass_by_stratum": { "sgml": "46/57", "html": "64/73", "ixbrl": "3/4" },
      "gold_recall": 1.0,
      "new_modes_count": 6
    },
    "signals_after": {
      "structural_pass_by_stratum": { "sgml": "46/57", "html": "66/73", "ixbrl": "3/4" },
      "gold_recall": 1.0,
      "new_modes_count": 6
    },
    "decision": "kept",                    // kept | discarded
    "reason": "amendment Part-I false-failures reclassified; full 10-Ks unchanged; guards green",
    "guards_ok": true
  }
  ```
  Append-only means a kept *and* a discarded iteration both leave a record — a discard is
  written with `"decision": "discarded"` and the failing signal/guard in `reason`, so the
  ledger is a complete audit trail, not just the wins.
- New named failure modes: `research/round-1-failure-modes.md` (mechanism + accession +
  flagged-not-silent evidence).
- **Execution later in an isolated worktree branched from `main`; reviewed; merged back to
  `main`; NEVER pushed.** `report.json` gitignored; `report.md` committed; `.env` never
  committed; `boundary_gold.json` changed only via the §-human checkpoint.

---

## 7. The loop, one iteration (operational)

1. **Baseline** the three signals; confirm the verifier batteries
   (`test_boundary_crosscheck.py` + `test_evalkit.py`) are green (G1).
2. **Analyze** which stratum / bucket (B1–B6) drags the signal down.
3. **Apply ONE treatment** (§3).
4. **Re-measure** all three signals (above noise).
5. **KEEP iff** a signal improves AND the guard passes; else **DISCARD + document** (§4).
6. **Human-audit** any *proposed* gold — never auto-freeze (G4 / playbook §6).
7. **Log** to `research/` + `prompts/`.

---

## 8. Executable mapping (for when it runs — engine config)

- **Scope (loop may modify):** `sec10k/template.py`, `sec10k/validate.py`, `sec10k/segment.py`,
  `sec10k/escalation.py`, `eval/eval_set.json`, `eval/*.py`, `tests/*`.
  **Out of scope (never modified by the loop):** `eval/boundary_gold.json` (human-only), the
  frozen accession lists, `sec10k/fallback.py` conservativeness, the regex-primary ordering.
- **The rulers — in scope but TIGHTEN-ONLY (G6).** `sec10k/validate.py` (the structural
  invariants = Signal A) and `sec10k/evalkit.py` (`boundary_scores` = Signal B) are
  *ruler-protected*: the loop may edit them **only to TIGHTEN or CORRECT, never to LOOSEN** a
  pass condition. They are the rulers that judge every change; relaxing one to make a change
  "pass" is circular and **auto-discards** the iteration (G6). `evalkit.py` is therefore listed
  under `eval/*.py` for completeness but is governed by G6, not free to edit.
- **Metric:** the **three independent signals** of §1 — *not* a single blind number (playbook
  §0–§1 forbids it).
- **Direction:** A ↑ (per stratum, upper-bound-labelled), B ↑ (gold recall), C ↑ (new named
  modes, enumerated — not smoothed).
- **Verify (each independent):** `python -m pytest -q` (verifier health, network-free) +
  `python eval/run_eval.py` (Signals A/B on the pinned set) + the structural sweep (Signal A
  breadth + Signal C).
- **Guard:** G1–G5 (§2).

---

## 9. How this meets the review bar (self-check)

| Your bar | Where met |
|----------|-----------|
| Every metric independent — no self-consistency | §1: A = source-byte geometry; B = human gold (decorrelated from regex+edgartools); C = enumeration where signals disagree. Forbidden proxies named. |
| Structural-pass labelled upper-bound-not-accuracy | §1 Signal A — the words are mandated on every report line; the blind spots (interior drift, scattered tail, > 40% swallow) are listed. |
| Not edgartools-alone (it's in the extraction path) | §1 forbidden-proxies clause; Signal B uses human gold; the decorrelated third source is edgar-corpus, never edgartools-alone. |
| Guard protects the offline gate + the human-gold floor | §2 G1 (green + network-free ≥ 65) and G4 (gold stays 5, never auto-frozen), plus G2/G3/G5. |
| Escalation-apply gates on a real boundary-correction check, not token accounting | §3 #4 GATE: inject-wrong → mock-correct → assert span **moves to gold** at IoU ≥ 0.9; explicitly "NOT that tokens accrued"; if unprovable against an independent reference, not claimed. |
| Stop conditions real | §5 S1 named common-mode / GE-class ceiling (out of scope), S2 plateau, S3 ~25-iteration budget. |
| Scope bounded | §3 one probe per iteration; §8 scope allow/deny list; §5 budget. |
| Discards documented honestly | §4 + §6 `research/round-1-findings.md` (and `round-1-progress.json` records discards too). |
| Mid-run state machine-trackable / resumable | §6 `research/round-1-progress.json` — append-only structured ledger alongside the prose; survives a crash. |
| Ruler not moved to pass a change | §2 **G6** + §8 — invariant/scorer code is tighten-only; mutation/drift batteries must stay green + a "no pass-condition relaxed" assertion; loosening **auto-discards**. |
