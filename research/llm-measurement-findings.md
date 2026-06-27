# LLM Escalation Tier — Measurement Findings (does it earn its keep?)

**Status:** measurement complete. REPORTED-only — this measured the tier against the FROZEN human
gold (Signal B = char-exact boundary IoU; Signal D = classification-match); it edited/froze no gold
and changed no production code. Harness: `eval/llm_measure.py`. Model measured:
`copilot:claude-opus-4.8` (the configured default). Run: 2026-06-26, 21 accession-pinned eval-set
filings, LLM-off (deferred, $0) vs LLM-on (real Copilot) on identical canonical per filing.

## Verdict (one line)

**Measured NO independent-signal improvement.** On every gold filing we can score, the LLM moved
**zero** boundaries → **ΔSignal B = 0.000 on all 5 boundary-gold filings, ΔSignal D = 0.000 on all
Signal-D gold**. The apply-loop and the real model demonstrably *work* (the mechanism one-shot fixes
a deliberately-wrong boundary) — they just provide no benefit on the filings where we have ground
truth, because the deterministic path is already correct there. **Disposition: keep as an honest,
default-OFF graceful-fallback tier; not a claimed win.**

## 1. Population trigger rate (the LLM-off free pre-pass)

| metric | value | meaning |
|---|---|---|
| filings triggering ≥1 escalation candidate | **21 / 21** | the confidence gate flags *every* filing |
| filings with ≥1 ACTUAL-call-eligible item (present, not-HIGH, has char_range) | **20 / 21** | only ms-fy2024 (NAMED common-mode, 0 items found) has nothing to call on |
| total real opus-4.8 calls across the 21 | **106** | one per present-low-confidence boundary |
| boundaries actually moved | **2** (ge-fy2009 §15, hon-fy2024 §8) | **1.9%** of calls applied anything |

**Named finding — OVER-BROAD TRIGGER (a cost finding for round-3).** The escalation candidate set is
`present-not-HIGH ∪ extraction_failure`. Because the confidence model rarely assigns HIGH, *clean*
filings flood the trigger: msft-fy2023 fired **10** calls, ge-fy2023 fired **23** — and moved
**nothing**. 106 opus-4.8 calls bought 2 boundary moves. The tier is firing on ~everything and acting
on almost nothing: pure wasted inference if it were on by default.

(Mechanism aside, confirmed from the code + the data: `run_escalation` only *calls* on PRESENT items
that have a `char_range` to move. `extraction_failure` items are counted as candidates but have no
char_range, so the LLM never actually tries to *recover* a missing item — it can only nudge the start
of an already-found one. This bounds what the tier can do: it cannot rescue the gross failures
(empty / collapsed / common-mode) at all.)

## 2. Do any GOLD filings trigger? — YES (correcting the prior assumption)

The hoped-for hard/clean split ("the LLM fires only on hard filings, which have no gold") **does not
hold**: **8 of the gold filings fired real calls.** They trigger; the LLM simply does not move them.

### Signal B (char-exact boundary gold, 5 filings) — before/after

| gold filing | B_off (mean IoU) | B_on | **ΔB** | calls | moved |
|---|---|---|---|---|---|
| apple-fy2024 | 1.000 | 1.000 | **0.000** | 1 | — |
| ko-fy2023 | 1.000 | 1.000 | **0.000** | 3 | — |
| msft-fy2023 | 1.000 | 1.000 | **0.000** | 10 | — |
| **m2i-fy2023** (token-per-line `Item\n1.` headers — the hard one) | 0.993 | 0.993 | **0.000** | 8 | — |
| **msft-fy1995** (pre-2001 legacy SGML — the other hard one) | 1.000 | 1.000 | **0.000** | 3 | — |

The two filings you'd most hope the LLM rescues — m2i and msft-fy1995 — fired 11 calls between them
and changed nothing. m2i even has a *real* small boundary imperfection (IoU 0.993 < 1.0) the LLM left
untouched.

### Signal D (classification gold, 5 filings) — before/after

All ΔD = **0.000** (apple, msft-fy2023, msft-fy1996, chemed-amend-fy2024, scwo-fy2025-amend). This is
**structural, not luck**: the apply-loop only nudges a *present* item's start offset — it never
changes a status — so it is **incapable of moving Signal D by construction**. The amendment Part-I
cells (where Signal D has its resolving power) are `extraction_failure`s with no char_range, so the
LLM is never even called on them.

## 3. Mechanism one-shot (real model + apply-loop, non-tautological)

Injected a deliberately-WRONG boundary on a present item (true start = char 60, moved to char 100,
band forced to MEDIUM), gave the **real** `claude-opus-4.8` the line-ref prompt, and applied its
answer:

```
model=copilot:claude-opus-4.8  item=1  true_start=60  wrong_start=100
real_model_raw_answer="4"  ->  moved_to=60  applied=1  fixed=True
```

**The real model returned the correct line and the boundary snapped back to the true start (IoU
1.0).** LLM-off leaves it wrong (proven by the offline deferred-ledger tests + the existing
`test_escalation_apply_moves_boundary_to_correct_offset` mock contrast). So the tier is **not
broken** — apply-loop + model work end-to-end. This does **not** change the verdict: it tells us the
"no" is *"correct boundaries on our gold leave nothing to fix"*, not *"the machinery is dead."*

## 4. The 2 real-filing moves (honest caveat)

ge-fy2009 (§15) and hon-fy2024 (§8) are the only filings where the LLM moved a boundary. **Both are
non-gold**, so we **cannot verify** whether those moves were correct, harmful, or neutral against an
independent reference. We do not claim them as wins. (To learn, §6 would need a targeted human
reference for those two specific boundaries — see "proposed follow-up.")

## 5. Verdict & disposition

- **Measured: the LLM gives no independent-signal improvement on the gold we can score** (ΔB=0 ×5,
  ΔD=0 ×5). A measured *no* is a complete result.
- **Keep it, default OFF.** It is an honest graceful-fallback (the mechanism works; it doesn't
  degrade anything — the 2 moves aside, it leaves correct boundaries alone). The deterministic regex
  path stays the shipped, $0, reproducible primary; the default `extract` path does not call the LLM.
- **Do not claim it as a win; do not flip it on by default.** README/ANALYSIS describe it as
  *"available, default-off, measured no independent-signal gain on our gold."*
- **Round-3 observability:** the `llm_touched` / `escalation_items_moved` tags (added here) let the
  failure census show the LLM footprint — now confirmed near-zero (2 moves / 21 filings).

## 6. Proposed follow-up (NOT done here — a human checkpoint, like char-gold)

If real-filing benefit beyond the gold overlap is wanted, the only honest path is a **targeted human
reference** for the specific escalated boundaries (e.g. the char-exact correct start of ge-fy2009 §15
and hon-fy2024 §8, and a few m2i low-confidence items), audited and frozen by a human — never scored
by the LLM or by me. Given the measured 1.9% apply rate and 0/5 gold lift, the expected value of
building that reference is low; recorded as an option, not a recommendation.

## What I did NOT verify

- The 2 real-filing moves' correctness (no independent reference — stated above).
- Whether a *different* model (e.g. gpt-5.4-mini) would behave differently — measured only the
  configured default (opus-4.8). The trigger/apply mechanics are model-independent; the *answers* are
  not, but the structural ceiling (can't move Signal D; can't recover failures) is.
- Anything beyond the 21-filing eval set (a 471/1000 full-pipeline LLM-on pass was out of scope —
  ~106 calls already came from 21 filings).
