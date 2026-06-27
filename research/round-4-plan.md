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

## 1. Independent signals that gate KEEP (unchanged from rounds 1-3)

- **A — structural-pass** (label-free, **UPPER BOUND on robustness, NOT accuracy**) on the 1,656 sweep.
- **B — char-gold IoU** on `boundary_gold.json` (human-audited, frozen, the accuracy floor).
- **C — count of new named flagged-not-silent modes.**
- **D — classification-match** vs frozen `classification_gold.json`.
- **NEW — RED regression anchors** in `eval_set.json` (`expect_red: true`): a fix is KEPT only if its
  anchor flips RED→GREEN **on an independently-labelled `expected_present`**, never on frozen output.

**Forbidden as KEEP evidence (carry over):** coverage fraction, `needs_review` count,
`extraction_failure` count, edgartools-alone, or any gold auto-frozen from production.

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
  **KEEP iff:** B1/B2 OXY anchor flips RED→GREEN **AND** the 5 char-gold stay 1.0 (B) **AND** clean
  filings gain no false header (B4 control) **AND** structural-pass (A) rises with no ruler loosened.
- **A2 — cross-reference-intruder run-selection hardening** (`lead_missing_high_cov` ~50 +
  `coverage_partial` ~6 + GIS TOC). Intruder-tolerant `_split_runs` / reject `Item N-<digit>` (the
  Reg S-X `4-08(g)` class) / broaden `needs_fallback`. **KEEP iff:** the XOM/DUK anchors flip GREEN
  **AND** char-gold Item-1 spans stay byte-exact (B) **AND** no TOC-as-body regression (B4).
- **A3 — ingest robustness** (`drop_other`). Make a fetch failure a graceful per-filing
  `needs_review`, not an uncaught raise (the safe minimum); optional pre-1994-Q3 archive fallback.
  **KEEP iff:** B5 ingest test passes AND no silent miss introduced.

**Each fix: KEEP iff a real independent signal moves AND the full guard passes; else DISCARD +
document.** No fix is kept because a forbidden proxy moved.

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
- structural-pass labelled **UPPER BOUND, not accuracy** on every line.

## 7. STOP conditions

- **S1** — a fix's only benefit is on a forbidden proxy (coverage/needs_review) → DISCARD (round-1
  pattern).
- **S2** — a fix flips its RED anchor GREEN but regresses a clean char-gold or clean structural-pass →
  DISCARD (the over-widening guard fired).
- **S3** — budget / plateau.

## 8. Where it lands + no-push

- This plan: `research/round-4-plan.md` (round-3 worktree, for review).
- Execution: a FRESH worktree off `main`, one probe per iteration, reviewed, merged back only after
  review; findings in `research/round-4-findings.md` + an append-only ledger. **NEVER pushed.**
  `boundary_gold.json` / `classification_gold.json` change only via the human audit checkpoint.
