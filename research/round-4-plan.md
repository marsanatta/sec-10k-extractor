# Round 4 — Implement Plan (REVIEW DOCUMENT — do NOT execute yet)

**Status:** plan only. No code touched, no execution, nothing pushed. This is the FIRST implement
round — it executes the tractable fixes round-3 discovered (`research/round-3-findings.md`). Awaiting
review against the same bar as rounds 1-3; only after approval will execution be requested in a fresh
worktree off `main`.

**Baseline:** post-merge `main` (LLM tier default-OFF) + the round-3 findings. The five failure
clusters and their root causes are taken as given from round-3 (all traced to live canonical bytes).

---

## 0. The one ordering decision: **B before A** (the verify-without-ground-truth crux)

Round-3 named the steps A (fix) → B (anchor) → C (perf). **We invert to B → A → C.** Reason: a fix is
only "kept" if an INDEPENDENT signal says it improved. Today the only thing that knows the *correct*
boundary for a failing filing is a human — not production output. So we must build the independent
ruler (RED regression anchors + char-gold + needs_review guards) **first**, then fix against it.
Fixing first and verifying against production output is self-consistency — exactly what the project
forbids. **B is the measuring instrument; A is the action. Build the ruler before you cut.**

```
B (build independent rulers)  →  A (fix, one probe/iter, measured RED->GREEN)  →  C (perf, alongside)
```

---

## 1. Signals — KEEP evidence vs monitored-only (the proxy-trap fix)

A fix is KEPT only on signals that can actually **FAIL** on a wrong fix. Signals that only ever rise —
or that can rise on garbage — are MONITORED and REPORTED, never a keep gate. This matters because A1
relaxes a regex, and a looser regex is the classic way a fix "passes" while quietly adding false
matches.

**KEEP evidence (each can REFUTE a bad fix — these gate the keep):**
- **B — char-gold IoU** on `boundary_gold.json` (human-audited, frozen): the fix must keep the clean
  spans **byte-exact (IoU 1.0)**. Can fail.
- **D — classification-match** vs frozen `classification_gold.json`. Can fail.
- **RED anchors** in `eval_set.json` (`expect_red: true`): the fix flips its anchor **RED→GREEN on an
  independently human-labelled `expected_present`**, never on frozen output. Can fail (the fix may not
  recover it, or may break another anchor).
- **B4 no-false-header control + G9 no-collateral-change** (§6): the looser regex must add **NO** false
  header on clean fixtures and change the segmentation of **NO** untargeted filing. Can fail.

**Monitored-only — REPORTED, NEVER a keep gate:**
- **A — structural-pass** (label-free, **UPPER BOUND on robustness, NOT accuracy**, 1,656 sweep). A
  looser regex that matches MORE headers **raises structural-pass even when the new matches are FALSE
  positives** — being label-free, it literally cannot tell "found more correct items" from "found more
  garbage". So it is a number we watch and report, **never evidence to keep a fix**.
- **C — count of new named flagged-not-silent modes** (a discovery metric, not a keep gate).

**Forbidden as KEEP evidence:** coverage fraction, `needs_review` count, `extraction_failure` count,
edgartools-alone, any gold auto-frozen from production, **and structural-pass alone**.

---

## 2. STEP B — build the independent rulers (do FIRST)

Each sub-step is cheap-to-expensive. **The non-negotiable rule: every `expected` value is independent
human ground truth, NEVER the current (wrong) production output.**

- **B1 — eval_set RED anchors (cheap, do all).** Add the 5 cluster representatives to `eval_set.json`
  with `expect_red: true` + a human-light `expected_present` (which items SHOULD be present — not
  char-exact offsets): OXY `0000797468-07-000027` (empty), XOM `0000034088-25-000010` +
  DUK `0001193125-11-047229` (cross-ref family), a `lead_missing_low_cov` member, an INTC
  `coverage_very_low` member. These pin the failures so any future change is measured.
- **B2 — char-gold, 1-2 only (expensive, HUMAN audit checkpoint).** Promote the cleanest empty-class
  filing (OXY-style: filing is clean, only the header recogniser fails → correct Item 1/1A/7/8 offsets
  are unambiguous and human-labellable). **PAUSE here — the agent PROPOSES offsets; the human audits +
  freezes** (exactly the char-gold discipline; char-gold stays small, human-only, never auto-frozen).
  Do NOT char-gold cases where the body is genuinely mis-segmented (DUK) — there the spans are wrong,
  so a clean offset gold is hard; those stay eval_set anchors only.
- **B3 — silent-failure guards.** For the FLAGGED-not-silent cases (DUK coverage_partial), add a test
  asserting `needs_review == True` — "known-hard filing must not silently pass." This is the
  Abstention-Recall / no-silent-failure guard at the unit level.
- **B4 — synthetic mutation/unit tests (network-free, into offline CI).** The strongest tests are
  *synthetic*, derived from the FIX invariant, not the real filing:
  - inject a separator-less header (`ITEM 7\n\nMANAGEMENT`) into a clean fixture → assert Item 7 is
    found AND a cooperative fixture gains NO false header (regression boundary);
  - inject an in-prose cross-reference (`see "\nItem 1A. ..."`) into a clean fixture → assert Item 1
    is still found.
- **B5 — route the non-boundary cases out of gold/eval.** #4 (1994 ingest gap) → an ingest-robustness
  unit test (unreachable accession → graceful `needs_review`, not an uncaught raise). #5 (COST `--`
  false-fail) → a harness unit test (`_starts_with_header` accepts the `-`/`--` separator that
  production `_HEADER_RE` already accepts). Neither belongs in char-gold/eval.

**KEEP B iff** the rulers are independent (labels human-sourced, not production-derived) AND the
mutation controls actually FIRE (a deliberately-wrong case lowers the signal). Else the ruler is a
dressed-up proxy — reject it.

---

## 3. STEP A — implement the fixes (do SECOND, ONE probe per iteration, ROI order)

Each iteration: a fresh worktree off `main`, one fix, measured against Step B's rulers, full guard.

- **A1 — separator-less header recogniser** (`empty` cluster, ~67 the biggest). Relax `_HEADER_RE`
  (`segment.py:17`) to accept `ITEM <num> <ws> (TITLE-like | EOL)` while KEEPING the line-start anchor.
  **KEEP iff (all three CAN-FAIL gates pass):** (i) the B1/B2 OXY anchor flips **RED→GREEN** on the
  human-labelled `expected_present`; (ii) the 5 char-gold stay **byte-exact IoU 1.0** (B); (iii) clean
  fixtures gain **no false header** (B4) **and G9 no-collateral-change passes** (only the targeted
  `empty`-cluster filings' segmentation changes). Structural-pass is reported, **not** a gate.
- **A2 — cross-reference-intruder run-selection hardening** (`lead_missing_high_cov` ~50 +
  `coverage_partial` ~6 + GIS TOC). Intruder-tolerant `_split_runs` / reject `Item N-<digit>` (the
  Reg S-X `4-08(g)` class) / broaden `needs_fallback`. **KEEP iff:** the XOM/DUK anchors flip
  **RED→GREEN AND** char-gold Item-1 spans stay **byte-exact** (B) **AND** no TOC-as-body regression
  (B4) **AND G9 passes** (only the targeted cluster changes). Structural-pass reported, not a gate.
- **A3 — ingest robustness** (`drop_other`). Make a fetch failure a graceful per-filing
  `needs_review`, not an uncaught raise (the safe minimum); optional pre-1994-Q3 archive fallback.
  **KEEP iff:** B5 ingest test passes **AND** no silent miss introduced **AND G9 passes** (the ingest
  change must not alter the segmentation of any reachable filing).

**Each fix: KEEP iff a CAN-FAIL independent signal (RED anchor RED→GREEN / char-gold IoU 1.0 / D) moves
the right way AND the full guard (incl. G8 + G9) passes; else DISCARD + document. A fix whose only
movement is on a forbidden proxy OR on structural-pass alone is a DISCARD, not a win.**

---

## 4. STEP C — the scalability finding (alongside, REPORTED)

Record + quantify the round-3 observation that `to_canonical` is super-linear on 1M+ char filings
(73-99s; 16 giant filings exceeded the sweep budget). Deliverable: a perf note (per-size timing curve)
+ a recommended bound (per-filing CPU/size guard, or the killable-process pattern already in the
harness). Optional: a cheap `to_canonical` profile to confirm the super-linear hot spot. This feeds
ASSIGNMENT's **scalability / performance** ask with measured evidence.

---

## 5. Why each step maps to ASSIGNMENT.md (the alignment table)

| Step | ASSIGNMENT.md criterion it serves |
|---|---|
| A1/A2/A3 fixes | **Robustness under format variance** (recover separator-less / cross-ref / legacy filings) |
| B1/B2 RED anchors + char-gold | **Verify without public ground truth** (independent human rulers) |
| B3 needs_review guards | **No silent failures** (known-hard filing must flag, not pass) |
| B4 mutation tests | **Validate-the-validator** (the checks/fixes can actually fail) |
| C perf note | **Scalability / performance analysis** (measured, not assumed) |
| RED→GREEN discipline | **Eval depth + honest reporting** (every fix earns its keep on an independent signal) |

---

## 6. Guards (carry over) + the new anti-Goodhart rule

- G1-G7 from rounds 1-3 (offline green network-free; regex PRIMARY; fallback CONSERVATIVE; char-gold
  stays 5-ish, human-only, never auto-frozen; baseline integrity; rulers tighten-only / never loosened;
  classification-gold human-only).
- **NEW G8 — RED-anchor integrity:** an `expect_red` anchor's `expected_present` (and any new
  char-gold) is **human-labelled from the filing**, NEVER copied from production output. Freezing a
  bug as "correct" = circular = auto-discard. Adding RED anchors is safe ONLY alongside the existing
  GREEN clean-filing gold (which catches a fix that "passes" by over-widening).
- **NEW G9 — no-collateral-change (population over-widening guard), computed CHEAPLY (zero re-fetch).**
  The 1,656 sweep filings have no gold — that is exactly where an over-wide regex hides. **Mechanism:**
  segmentation is deterministic on the canonical bytes, and A1/A2 change ONLY segmentation
  (`segment` / `_split_runs` / `_pick_body_run` / `needs_fallback`), never fetch or normalize. So
  **CACHE all 1,656 canonicals once at baseline** (a one-time sweep that also writes each filing's
  canonical to a local cache, gitignored), then after each A-fix **RE-SEGMENT the cached canonicals
  offline and DIFF the per-filing spans (key + `[start,end]`) BEFORE vs AFTER** — **zero network,
  deterministic, seconds not ~30–40 min** (no re-fetch, no super-linear `to_canonical`). The ONLY
  filings whose spans may change are the **targeted cluster**; any OTHER changed filing is a
  **candidate over-widening regression** to investigate + document — never silently ship a boundary
  move on an untargeted filing. **Check:** `diff(baseline spans, post-fix re-segment spans)` must
  partition into `{targeted-cluster recovered}` ∪ `{∅}`; a non-empty second set **blocks the keep**
  until every member is explained (re-classified as intended, or the fix narrowed). (A3 touches ingest,
  not segmentation, so its G9 is the same offline re-segment diff over the reachable set, plus the
  newly-reachable 1994 filings as the intended change.) **G9 is part of EVERY A-step keep gate,
  alongside the RED anchor and the char-gold.** Tooling for this cache+diff is built in Step B.
- structural-pass labelled **UPPER BOUND, not accuracy** on every line; it is monitored/reported (§1),
  never a keep gate.

## 7. STOP conditions

- **S1** — a fix's only benefit is on a forbidden proxy (coverage/needs_review) → DISCARD (round-1
  pattern).
- **S2** — a fix flips its RED anchor GREEN but regresses a clean char-gold (B) OR fails G9 (changed an
  untargeted filing's segmentation) → DISCARD (the over-widening guard fired). Note: a structural-pass
  *rise* is NEVER the thing that saves a fix here — only the can-fail gates do.
- **S3** — budget / plateau.

## 8. Where it lands + no-push

- This plan: `research/round-4-plan.md` (round-3 worktree, for review).
- Execution: a FRESH worktree off `main`, one probe per iteration, reviewed, merged back only after
  review; findings in `research/round-4-findings.md` + an append-only ledger. **NEVER pushed.**
  `boundary_gold.json` / `classification_gold.json` change only via the human audit checkpoint.
