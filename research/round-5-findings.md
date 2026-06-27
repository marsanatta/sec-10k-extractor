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

**The audit packet then exposed a false-positive class, which traced to a latent regex bug.** Reading
the gained header at each offset (`scratch/r5_audit_packet.py`) showed a handful of gains anchored on
in-prose CROSS-REFERENCES, not headers: `Item 1 under the caption "Risk Factors"`, `Item 8 of this
Report`, `Item 8 herein`. Root cause (traced, not guessed): `_HEADER_RE_LOOSE`'s separator-less branch
ends `\s+(?=[A-Z])`, but the pattern carries `(?i)`, so under IGNORECASE `[A-Z]` also matches lowercase
— the documented "title starts uppercase" guard NEVER actually fired. A1/A2 never exposed it (empty
cluster / Item-1-missing filings have no competing cross-refs); A3's broader application did.

**Fix evolution (each step caught by an independent check — the loop working):**
1. `(?-i:[A-Z])` (case-sensitive uppercase) — rejected the cross-refs BUT the regex-delta probe (buggy
   vs fixed over the cache) showed it also dropped REAL headers whose item number is followed by a
   lowercase token: combined headers (`Item 7 and 7A`, `Item 1 and 2.`) and title-less items
   (`Item 15\n\n a) 1. Financial Statements`). Over-corrected → discarded.
2. Negative-lookahead denylist of cross-ref words with `\s+` — fixed the combined/title-less, but the
   delta then caught it dropping Lowe's `Item 2\n\nAt February 1, 2008...`: a title-less header whose
   BODY starts with "At", and `\s+` let the denylist reach across the newline into the body. Discarded.
3. **Same-line denylist (`[ \t]+`, final):** a title-less header puts its body on the NEXT line, so only
   a SAME-line lowercase connective after the number signals a cross-reference. This rejects the in-prose
   cross-refs and preserves combined / title-less / by-reference (`Item 7A\n\nSee MD&A`) / GIS-style.

**Final measured state (1,735 cached):**
- Regex-delta (original buggy loose regex vs same-line denylist): 7 filings change, ALL 7 are correct
  cross-ref removals (verified by snippet), 0 real headers lost — a clean tightening.
- A3 containment (old A1+A2 vs new A1+A2+A3): **identical=1696, widened=39, collateral=0.** 39 clean
  pure-insertion recoveries, G9 zero-collateral by construction.
- Offline suite **95 passed / 1 skipped, network-free**, across every regex iteration.
- **One residual false positive** (`0001193125-15-070443`, an old=1-key 1.36M-char giant): A3 adds an
  Item 1 anchored on an enumeration line `Item 1 Business, Item 1A Risk Factors, and Note 21...`. The
  denylist can't catch it (the next word, "Business", is a real title word). Low harm — that filing is a
  conspicuously under-segmented giant (2 keys) either way, so the validation layer flags it; it is NOT a
  silent failure. A header-line-names-one-item filter (reject a gained header whose line holds a second
  `Item N`) would close this enumeration class — deferred as a small future refinement, not load-bearing.

## Status / next
- A3 (dominance + anchor-stability guard) + the `_HEADER_RE_LOOSE` same-line cross-ref denylist
  IMPLEMENTED on `round5/a-full-relaxation`: **+39 real recoveries, G9 zero-collateral, suite green.**
  The leading effective candidate; the regex denylist also retroactively hardens A1/A2.
- The 18 relocation cases + the `both` cluster (32 filings: relax net-helps but drops 7A) are LEFT for a
  later **Probe 2** (fix the 7A-drop / restart-vs-intruder ambiguity in `_split_runs_tolerant`) — separate,
  riskier, gated the same way. The 1 enumeration residual + a header-line filter belong there too.
- Pending for the gate: human-audit a sample of the 39 + lock 1–2 char-gold anchors (then RED→GREEN eval
  evidence, as GIS did for A1). First clean candidate: `0000950123-11-019888` (77k chars, old=15 keys,
  gains Part III 11/12/13/14/15).
- Nothing pushed. Working branch `round5/a-full-relaxation`.
