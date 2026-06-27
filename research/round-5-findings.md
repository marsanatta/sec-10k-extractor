# Autoresearch Round 5 — A-full-relaxation (the partial-coverage cluster)

Goal: recover the ~137 PARTIAL-segmentation filings that round-4 deferred (strict already returns a
non-empty result WITH Item 1, so A1/A2 never fire, but it under-segments) — WITHOUT the 35 collateral
degradations that killed the round-4 full-relaxation probes. Must pass the standard gate (G9
zero-collateral + char-gold IoU + RED→GREEN on an independent signal + no forbidden proxy + offline
suite green network-free). All numbers below are recomputed from the 1,735 cached canonicals offline.

## Characterization — the over-drop is concentrated, not a mysterious "third pattern"

Applying full relaxation (loose regex + tolerant split) UNCONDITIONALLY to every cached canonical,
vs the pure strict pass:

| bucket | n | meaning |
|---|---|---|
| identical | 1500 | relax leaves it unchanged |
| keys_gained | 149 | relax recovers items strict missed (the targets — but see below, overlaps A1) |
| keys_lost | 33 | relax DROPS items strict had (the over-drop) |
| both (gain+loss) | 32 | relax swaps keys |
| boundary_shift | 21 | same keys, different offsets |

The over-drop (keys_lost + the loss side of `both`) is dominated by ONE item — **7A** — plus a small
catastrophic tail. Traced root causes (read from the cached bytes, not guessed):

- **7A-drop (most common).** The loose regex admits an in-prose cross-reference (`Item 8` /
  "see Item 8, Financial Statements") between Item 7 and Item 7A. The tolerant split's one-element
  lookahead then sees 7A as an order-dip whose *next* hit (the cross-ref 8) resumes, and SKIPS 7A as a
  lone intruder. Example `0001193125-07-036001`: strict body is perfect (20 items incl. 7A); the relax
  pass admits a false `Item 8@105843` and drops 7A.
- **Catastrophic `_split_runs_tolerant` fragility.** Example `0001193125-07-036143` (strict=20 →
  relax=2): the loose and strict regex hits are IDENTICAL; the ONLY difference is `_split_runs` (correct,
  20) vs `_split_runs_tolerant` (picks `['1','7']`). The tolerant split is simply more fragile than the
  strict split on some tails — independent of the loose regex.

**Decisive observation:** every over-drop filing is one where the STRICT pass (= current production) is
ALREADY correct or already produces its result. Production never applies relax to them (strict non-empty
+ has Item 1 → returns strict). They only "break" in the unconditional experiment. So the fix is the same
confinement insight as A1/A2: apply relax only where it strictly helps.

## Probe 1 — the DOMINANCE keep-guard (IMPLEMENTED as A3)

A third fallback, after A1 (strict empty) and A2 (Item 1 missing): when the strict result is non-empty
and has Item 1, compute the relax candidate and **keep it iff (a) `set(strict) ⊊ set(relax)` (every
strict key preserved, ≥1 new key), (b) every SHARED item keeps its exact start offset, AND (c) coverage
does not drop.** Condition (a) auto-rejects every over-drop class:
- Catastrophic (ED 20→2): relax `{1,7}` is not a superset of strict's 20 → rejected, keep strict.
- 7A-drop (20→19): relax missing 7A → not a superset → rejected, keep strict.
- Pure boundary-shift (21): no key gained → rejected.

**Condition (b) was forced by a caught regression — validate-the-validator working.** The first cut had
only (a)+(c). It FAILED the existing `test_segment.py::test_body_with_fewer_recognised_headers_still_wins`:
on a TOC(1,1A,2,3)+body(1,3) doc, `_split_runs_tolerant` drops the genuine body Item 1 as a false intruder
(its next body hit, Item 3 @order 5, "resumes" the TOC run's last order 5) and re-anchors Item 1 on the
TOC line — yet the KEY "1" is still present, so the set-superset guard accepted a WORSE result. The guard
checked key PRESENCE, not POSITION. Condition (b) — shared items must keep their offset — means the relax
pass may only INSERT newly-found items into the strict skeleton, never RELOCATE an existing one. The pre-
existing test (not me) caught it; that is the ruler doing its job.

**Measured incremental recovery over production (A1+A2), on the 1,735 cached:**
- (a)+(c) only: 62 filings widened. (a)+(b)+(c): **44 filings widened, 0 collateral** — condition (b)
  rejected 18 relocation cases (the same class as the test failure), correctly preferring strict there.
- Gains concentrate on items strict commonly misses: Part III 11/12/13/10/14/15, mid-body 9/8/6/9A/9B,
  separator-less 1/1A/2/3 on iXBRL token-per-line filings.
- **Realness check (header snippet at each gained offset, eyeballed):** the gains are REAL headers, not
  false cross-references — `Item 1A. RISK FACTORS`, `ITEM 2. PROPERTIES`, `Item 1\n\nGeneral` (Lowe's
  iXBRL), `ITEM 1  Business` (separator-less PSEG/Norfolk Southern). The two "suspect" lone-high-order
  gains also read as genuine: `ITEM 11   EXECUTIVE COMPENSATION`, `ITEM 15. Financial Statements...`.

**Why it passes the gate by construction:** only the 44 dominating filings change; the other 1,691 are
byte-identical → G9 zero-collateral (proven offline, old A1+A2 vs new A1+A2+A3: identical=1691,
widened=44, collateral=0). The keep decision is a per-filing can-fail dominance + anchor-stability check,
NOT a forbidden proxy (structural-pass / needs_review / extraction_failure). The relax pass is unchanged
code (`_HEADER_RE_LOOSE` + `_split_runs_tolerant`); only its APPLICATION is widened under the guard.
Offline suite 95 passed / 1 skipped, network-free.

**Residual risk (honest):** the guard proves no key is lost, anchors are stable, and gained headers READ
as real — but it does not by itself prove every gained item's BOUNDARY is byte-correct (a gained item
anchored on a *new* false cross-ref between two stable strict items would still pass). This is what the
human-audited char-gold anchor is for: a sample of the 44 must be read from the filing and 1–2 locked as
RED→GREEN char-gold, the same discipline that earned A1/A2. Audit packet generated in
`scratch/r5_audit_packet.py` output.

## Status / next
- A3 (dominance + anchor-stability guard) IMPLEMENTED on `round5/a-full-relaxation`: +44 real recoveries,
  G9 zero-collateral proven, suite green. The leading effective candidate.
- The 18 relocation cases + the `both` cluster (32 filings: relax net-helps but drops 7A) are LEFT for a
  later **Probe 2** (fix the 7A-drop / restart-vs-intruder ambiguity in `_split_runs_tolerant`) — separate,
  riskier, gated the same way.
- Pending for the gate: human-audit a sample of the 44 + lock 1–2 char-gold anchors (then they become
  RED→GREEN eval evidence, as GIS did for A1).
- Nothing pushed. Working branch `round5/a-full-relaxation`.
