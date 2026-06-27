# Autoresearch Round 2 — Plan (REVIEW DOCUMENT — do NOT execute yet)

**Status:** plan only. No code touched, no execution. Awaiting review against the same bar as
round 1; only after it passes will execution be requested.

**Baseline:** the **new `main`** (round 1 merged — escalation apply-loop closed, eval grown to
21). **Iteration 0 re-measures A/B/C on this main first** — round-1's numbers are not assumed to
carry.

**This is a focused DELTA from round 1, not a re-author.** Everything in
`research/autoresearch-round-1-plan.md` still binds unchanged unless restated here:
- **Signals A / B / C** — A = stratified structural-pass (**UPPER BOUND on robustness, NOT
  accuracy**, labelled on every line), B = gold recall on the 5 human-audited char-gold, C =
  count of new named flagged-not-silent modes. Independence justifications + the forbidden-proxy
  list (presence recall, `needs_review` count, edgartools-alone) carry over verbatim.
- **Guards G1–G6** — offline suite green AND network-free (≥ committed baseline, currently 69);
  regex stays PRIMARY; fallback stays CONSERVATIVE; **char-gold stays 5, never auto-frozen** (G4);
  baseline integrity (G5); **never loosen the ruler** — invariant/scorer code is tighten-only,
  loosening auto-discards (G6).
- **One probe per iteration**, ROI order; **KEEP iff a real independent signal moves above noise
  AND the full guard passes, else DISCARD + document**; **~25-iteration bound**; STOP at the named
  common-mode ceiling / plateau / budget.
- **Findings & no-push:** narrative `research/round-2-findings.md`, new modes
  `research/round-2-failure-modes.md`, append-only `research/round-2-progress.json` (same schema
  as round 1). **Execution runs in a FRESH isolated worktree off the new `main`, is reviewed, then
  merged back; NEVER pushed.** `report.json` gitignored; `.env` never committed.

---

## 1. The round-2 headline — Signal D: an INDEPENDENT classification-correctness signal

Round 1 discarded the form-aware template fix even though it was **verified-correct**, because its
only benefit landed on the **forbidden proxies** (`extraction_failure` / `needs_review`) and **no
independent signal could see it** (§8 #1 of ANALYSIS, round-1 iter-2). Round 2's **first job** is
to build the missing thing: a signal that can independently verify *"for this form type, is item X
correctly judged present / legitimately-absent / incorporated-by-reference"* — **and that the loop
cannot move by editing the production classifier.**

### Signal D — definition

- **What it measures:** for a small **human-audited per-form-type reference**, the fraction of
  `(filing, item)` cells where the production pipeline's status **category** matches the human
  label's category. Categories: `present` / `legitimately-absent` / `incorporated-by-reference` /
  `extraction-failure`. Reported **per form type** (`10-K` vs `10-K/A`) **with N + Wilson CI**.
- **The reference — `eval/classification_gold.json` (NEW, human-only):** ~3 full `10-K` + ~3
  `10-K/A`, each **audited by READING the filing's actual structure** (TOC, the Part/Item headers
  the filing genuinely carries vs omits), labelling every canonical item key with its true
  category. **Audited and frozen exactly like `boundary_gold.json`:** human checkpoint, **out of
  the autoloop, never self-graded, never auto-frozen.** Each entry records its audit provenance
  (read-located, method-independent of `expectation()` — the same discipline that makes m2i /
  msft-1995 char-gold method-independent).
- **Load-bearing cells:** the signal's resolving power lives in the **amendment Part-I/II cells**
  (where the form-blind bug puts false `extraction-failure`s) and the **full-10-K control cells**
  (which must stay correct). N is small (like char-gold) → wide CIs → a delta counts only above
  noise; the few amendment cells are the ones that move.

### WHY Signal D is GENUINELY INDEPENDENT (the review-bar crux — answer it head-on)

1. **Human-labelled by reading the filing, not derived from production.** The reference is built
   from the filing's own TOC / Part structure, **never** from `expectation()`, `_classify_absent`,
   `needs_review`, or any extractor output. Changing the production classifier **cannot** change
   the reference — so the fix cannot move the signal tautologically.
2. **The loop cannot edit the ruler to pass.** `classification_gold.json` is human-only under a new
   guard **G7** (below): the loop may PROPOSE candidate labels but may NOT freeze them and may NOT
   edit frozen entries to make a change pass — that circularity is an **auto-discard** (the G6
   analog for the new ruler).
3. **It can REFUTE, not only confirm** (this is what separates a ruler from a proxy). Two controls:
   - **(a) Mutation refutation (always assemblable — the validate-the-signal test).** Deliberately
     mis-classify a genuinely-present Part-I item as `legitimately-absent` and assert **Signal D
     DROPS** against the human reference. If a deliberately-wrong classification does **not** lower
     Signal D, the signal measures nothing and is rejected. (Analogous to the char-gold drift test
     and the boundary mutation battery.)
   - **(b) Full-scope-amendment refutation (real-data, if assemblable).** Include a `10-K/A` that
     **does** amend a Part-I/II item (a fuller-scope amendment), where the human reference says
     that item **is present**. A blanket "`/A` → Part I-II optional" rule would mis-classify it,
     and Signal D would **fall** — so the signal can *reject an over-broad form-aware rule*, not
     just reward it. **If no fuller-scope `/A` can be found** (all reachable `/A` are
     Part-III-only), say so plainly: control (a) still proves the signal can fall, but the
     real-data refutation is unavailable — note the limitation and **do not over-claim** the
     signal's discriminating power on the over-broad case.
4. **Decorrelated from `needs_review`.** `needs_review` is an OR flag over many drivers; Signal D
   is a per-item **category match against independent ground truth** — a different object. The fix
   could flip `needs_review` (forbidden proxy) without moving Signal D, and vice versa; only
   Signal D counts.

### Honest failure mode of Signal D (state it up front)

If Signal D **cannot be made genuinely independent** — concretely, if the human-audited reference
cannot be assembled method-independently (e.g. the only available signal ends up being a frozen
copy of production output), or control (a) cannot be made to fire — then Signal D is **a proxy
dressed up**, not a ruler. In that case: **declare it, do NOT use it to justify the form-aware
fix, and DEFER the fix again** (the round-1 outcome stands). **Never fake the signal to earn the
fix.** This is STOP condition **S4** (§5).

### New guard — G7 (classification-gold integrity)

| ID | Invariant | How checked |
|----|-----------|-------------|
| **G7** | `eval/classification_gold.json` is **human-audited + frozen**; loop may PROPOSE, never FREEZE or EDIT-to-pass | Assert the file changes only via the human-audit checkpoint (a dated audit prompt record, like the char-gold audit); assert no entry's category is copied from `expectation()` / extractor output (provenance must read "read-located from the filing"); the mutation refutation control (3a) must fire (a deliberately-wrong classification lowers Signal D) or the signal is rejected. Editing the gold to make a change pass = circular = **auto-discard**. |

---

## 2. Per-iteration SCOPE (ONE probe per iteration, ROI-ranked)

### #0 — Re-baseline on the new main (iteration 0)
Re-measure A (per stratum, UPPER BOUND not accuracy), B (gold 1.0/5 expected), C (0 new) on the
merged main; confirm the verifier batteries green (G1). Record before any probe.

### #1 — BUILD Signal D + its frozen human-audited reference + the refutation control *(the enabler)*
- Assemble ~3 full `10-K` + ~3 `10-K/A` (accession-pinned, immutable; reuse pinned set members
  where possible — apple/msft full 10-Ks, chemed-/A, scwo-/A); **propose** per-item category
  labels by reading each filing's TOC/Part structure; wire `classification_match_rate`
  (`sec10k/evalkit.py` scorer addition — *a scorer, governed by G6: it may only be added/tightened,
  never loosened to flatter a result*).
- Build the **mutation refutation control (3a)** and prove it fires.
- **HUMAN-AUDIT CHECKPOINT — execution PAUSES here.** The proposed labels are
  *regression-anchors only, not trusted truth*, until the user audits them (exactly the char-gold
  discipline, playbook §6). Signal D may gate the form-aware earn **only against the user-frozen
  reference**, never against agent-proposed-but-unaudited labels.
- **KEEP iff** Signal D is operational AND demonstrably independent (control 3a fires; reference is
  read-located, not production-derived) AND guard (G1–G7) green. **Else DISCARD/DEFER + document**
  (and S4 applies to the fix).

### #2 — RE-ATTEMPT the form-aware template fix *(now legitimately earnable — depends on #1)*
- Implement form-aware `expectation()` (thread `raw.form`; `/A` → Part I-II items `OPTIONAL`),
  exactly the round-1 change.
- **KEEP iff ALL hold:** (i) **Signal D improves** on the amendment cells against the
  **user-frozen** reference, above noise; (ii) the **full-10-K control cells are unchanged** (the
  fix must not perturb full-10-K classification — the decorrelated control); (iii) **Signal A
  (structural-pass, UPPER BOUND) is unchanged** — and we **do NOT** make coverage form-aware to
  manufacture an A gain (**G6 auto-discard**); (iv) guard G1–G7 green.
- **If #1 did not yield a genuinely independent Signal D → DEFER again** (S4); do not claim the fix.
- This is the explicit answer to round-1's open item: the fix becomes a KEEP **only** because an
  independent ruler now sees it — not because a proxy moved.

### #3 — Stratified eval growth *(Signal A resolving power + Signal C discovery)*
Add under-covered era / filer-type / sector / structure (accession-pinned, immutable), verified to
fetch on current code before pinning; report per-stratum (UPPER BOUND, not accuracy). Same as
round-1 probe (a).

### #4 — Failure-mode discovery *(Signal C)*
Bounded sweep (logged N, no silent truncation) over a stratified tail for new flagged-not-silent
modes; full-pipeline spot-check confirms the flag. Same as round-1 probe (c).

**ROI order:** #1 Signal D build (the enabler) → #2 form-aware earn (depends on #1) → #3 eval
growth → #4 discovery.

---

## 3. KEEP / DISCARD — unchanged, with Signal D specifics

- **KEEP** iff a real independent signal (**A / B / C / D**) moves above noise **AND** guard
  (G1–G7) passes; **else DISCARD + document** (discards recorded in full in
  `round-2-findings.md` and as a `"decision":"discarded"` record in `round-2-progress.json`).
- **The form-aware fix counts as a KEEP ONLY if it moves Signal D** (independent classification
  ground truth) with the full-10-K control held fixed — **never** if it only moves
  `extraction_failure` / `needs_review` (still forbidden proxies).
- **Signal D itself counts as "built" only if its refutation control (3a) fires** — a signal that
  can only rise is a proxy and is rejected.

---

## 4. THE GUARD — G1–G6 (round 1) + G7 (round 2)

G1–G6 exactly as round 1 (offline green network-free ≥ baseline; regex primary; fallback
conservative; char-gold = 5 never auto-frozen; baseline integrity; don't-loosen-the-ruler). **G7**
adds classification-gold integrity (§1). The rulers — `validate.py` invariants, `evalkit.py`
scorers (now including `classification_match_rate`), `boundary_gold.json`, and
`classification_gold.json` — are all **tighten-only / human-only**; loosening or editing-to-pass
any of them **auto-discards** the iteration.

---

## 5. STOP conditions

- **S1** — named common-mode ceiling (FM-2-class: regex + edgartools both header-anchored fail
  together; needs a decorrelated non-header / CRF extractor — out of scope). Disclose, don't fake.
- **S2** — plateau on A / B / C / D (no above-noise gain across K iterations).
- **S3** — ~25-iteration budget.
- **S4 (round-2-specific)** — **if Signal D cannot be made genuinely independent** (reference not
  assemblable method-independently, or the mutation refutation control cannot be made to fire),
  **STOP the form-aware earn and document the deferral honestly** — do not proceed to probe #2,
  and do not fake the signal. The round-1 discard then stands as the correct outcome.

---

## 6. Findings, artifacts, and no-push (spelled out)

- `research/round-2-findings.md` — human narrative; every iteration: probe, the signal deltas
  (A/B/C/**D**, with N), guard status (G1–G7), KEEP / DISCARD, and *why* (discards in full). Every
  structural-pass number labelled **"UPPER BOUND, not accuracy."**
- `research/round-2-failure-modes.md` — new named modes (mechanism + accession + flagged-not-silent
  evidence).
- `research/round-2-progress.json` — **append-only** machine ledger, same schema as round 1, with
  `signals_before`/`signals_after` extended to carry `classification_match_rate` (per form type).
- `eval/classification_gold.json` — **NEW human-audited frozen reference** (committed, human-only),
  plus a dated audit prompt record documenting the read-located provenance (mirrors the char-gold
  audit record).
- **Execution runs in a FRESH isolated git worktree off the new `main`; reviewed; merged back to
  `main` after review; NEVER pushed.** `boundary_gold.json` and `classification_gold.json` change
  only via the human checkpoint, never the autoloop.

---

## 7. How this meets the bar (self-check — special attention: Signal D independence)

| Bar item | Where met |
|----------|-----------|
| Signals independent; no self-consistency; structural-pass labelled upper-bound-not-accuracy | §0 (A/B/C carry over) + §1 (D is human-read ground truth, not production-derived) |
| **Signal D genuinely independent (human-audited, frozen, decorrelated from `needs_review`) — not a proxy dressed up** | §1 WHY-independent points 1–4 + **the refutation controls (3a always; 3b if assemblable)** — D can *fall*, proving it is a ruler; **G7** forbids editing it to pass; **S4** defers the fix if independence can't be shown |
| Form-aware earn is legitimate, not circular | §2 #2 — KEEP gated on **Signal D** (independent) + full-10-K control unchanged + A unchanged (no G6 coverage-loosen) + guard; **deferred again (S4) if D isn't independent** |
| Guard protects offline gate + human-gold floors | G1 (offline green network-free) + G4 (char-gold 5, never auto-frozen) + **G7** (classification-gold human-only) + G6 (rulers tighten-only) |
| Stop conditions real | §5 S1 ceiling / S2 plateau / S3 budget / **S4 defer-if-not-independent** |
| Scope bounded | §2 one probe/iter; §5 budget |
| Discards documented honestly | §3 + §6 (`round-2-findings.md` + append-only `round-2-progress.json`) |
| Char-gold stays 5; rulers never loosened; regex primary; offline green | G1–G7; §2 #2 (iii) refuses the coverage-loosen |
