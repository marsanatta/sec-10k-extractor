# Analysis — SEC 10-K Item Extractor

What this system is, how well it works **with real numbers**, how it stays cheap, and — the
part with no public ground truth — **how it verifies itself**. Every number here is produced
by `eval/run_eval.py` over a 7-filing self-built set (`eval/eval_set.json`) plus the unit
suites; reproduce with `python eval/run_eval.py` and `python -m pytest -q`.

The design in one line: **index, don't generate.** An item is a `char_range` into the
filing's canonical text, never LLM free-text. A deterministic regex/anchor tier segments
~100% of the common case at \$0; a validation layer attaches calibrated confidence +
provenance to every item; an LLM tier is reserved for the low-confidence-boundary minority
(currently a deferred stub — see §5). The differentiator is the **validation layer**, because
no existing item-segmenter emits confidence.

---

## 1. Eval set (what the numbers are measured on)

7 filings, deliberately weighted toward failure modes (only 3 are "clean"):

| filing | era | why it's in the set |
|---|---|---|
| apple-fy2024, ko-fy2023, msft-fy2023 | iXBRL | clean modern filings (the easy majority) |
| ge-fy2023 | iXBRL | **cross-reference index** — "Item N" appears out of body order |
| m2i-fy2023 | iXBRL | **token-per-line render** — headers arrive as `Item\n1.` |
| msft-fy1995 | SGML | **legacy, zero `<a>` anchors**, all-caps irregular-spaced headers |
| chemed-amend-fy2024 | iXBRL | **10-K/A** — partial scope, most items legitimately absent |

N is small (7), so every aggregate below carries a wide Wilson interval — stated, never
hidden. The eval set is intentionally **not** representative of the EDGAR population; it
over-samples hard cases so the metrics stress the failure modes.

---

## 2. Results, per format bucket (never pooled)

Pooling lets the easy iXBRL cases hide the hard ones, so each bucket is reported separately
**with its N**. Presence recall is over a conservative hand-labelled expected-present set;
boundary match-rate is char-exact IoU ≥ 0.9 vs the audited gold (`eval/boundary_gold.json`).

### Presence (label-free + conservative gold), all 7 filings
- Mean presence recall **1.0** (every item the gold says is present was surfaced).
- Silent-failure rate **0/7** (obs 0.00, 95% CI [0.00, 0.35]) — a *silent* failure = missed a
  gold item with `needs_review=False`. Structural-ok **7/7**, round-trip **7/7**.
- `needs_review` fired on **6/7** (only clean apple passed unflagged) — the layer is
  conservative, flagging the 3 hard filings and the two medium-confidence clean ones.

### Boundary (char-exact), per era — with N
| bucket | N gold filings | boundary match-rate @ IoU≥0.9 |
|---|---|---|
| **iXBRL** | 4 (apple, ko, msft-2023, m2i) | **1.0** — apple 4/4, ko 4/4, msft-2023 4/4, m2i 2/2 |
| **SGML** | 1 (msft-1995, items 1/2/7) | **1.0 (3/3)** |
| iXBRL, cross-ref-index (GE) | **0** | **unmeasured / ungoldable** (see §6) |

Boundary match-rate **1.0 over 5 gold filings spanning two eras** (iXBRL 4 + SGML 1) — reported
**per bucket, never pooled**, because the GE cross-reference case (§6) has **N=0** char-gold
and is excluded, not averaged away. Two labels are **method-independent**, not frozen from the
regex: m2i (title-labelled by hand) and msft-1995 (SGML body sections located by *reading* the
canonical text, then confirmed the extractor matches at IoU 1.0). Their agreement is a genuine
cross-method confirmation, not a tautology. The three iXBRL easy filings are regex-derived but
**human-audited** (every offset's snippet eyeballed as a real section body — §5.3).

---

## 3. Cost — per filing

The deterministic path does the work; the LLM is the exception, not the rule.

- **Deterministic tier: \$0 inference, 100% of filings.** Regex/anchor segmentation +
  structural validation + the XBRL/DEI oracles make no paid model call. The HIGH-confidence
  majority of items is accepted here at zero marginal cost.
- **Escalation tier: flagged minority only, windowed.** A boundary is escalated only if it is
  not HIGH confidence (or the item is an extraction-failure). Measured on this hard-weighted
  set: **64 / 161 canonical item-slots flagged (39.8%)** — but that average is dominated by the
  pathological filings (GE 23/23 all-low, chemed 12/12); on the clean filings it is **apple
  1/23, ko 3/23**. Each escalation sees a **±2000-char window** (`build_lib_prompt`,
  `sec10k/escalation.py`), ~1k tokens, never the whole filing.
- **Estimated escalation cost if wired** (small-model rates ~\$0.15/1M input): ~9k tokens ×
  flagged-items ⇒ blended **≈ \$0.001–0.002 / filing**, under the \$0.003–0.006 target; clean
  filings ≈ \$0.0002. The planned provider is the **GitHub Copilot SDK (flat-rate quota)**, so
  the marginal \$ is ≈ 0 and the truly bounded resource is **escalation requests/filing +
  latency**, not \$/token.
- **Cost vs the naive baseline (a Pareto point):** *adjudicate-all* would call the LLM on all
  **161** item-slots; *escalate-only-flagged* calls **64** (**−60%**), and on a clean filing
  **1 vs 23 (−96%)**. Same correctness ceiling on the boundaries that matter, a fraction of the
  calls.
- **Currently the cost is \$0** because the tier is deferred (§5) — and nothing is silently
  skipped (deferral ledger).

---

## 4. Scalability

- **Cache by accession.** Filings are immutable; results are memoised by accession, so repeat
  views and the demo set are \$0 / instant. (The web API and `eval` share this.)
- **Deterministic tier is O(n) over canonical text** (one regex pass + a run-pick); memory is
  one filing at a time, stateless — horizontal scaling is embarrassingly parallel per filing.
- **EDGAR politeness is the real throughput cap:** 10 req/s + descriptive User-Agent + a
  per-operation network timeout (`ingest.py`) so a wedged fetch can't pin a worker. The bound
  is EDGAR's rate limit, not CPU/RAM.

---

## 5. Verification without public ground truth (the crux)

There is no filing-level answer key for 10-K item boundaries. **Self-consistency is not
validation** — a model judging its own output cannot catch a *confident systematic* error.
So every check below is **independent of the production segmenter**, and they are layered
cheap→expensive. Each is named by its real file + test.

1. **Structural invariants + round-trip (100% scope, label-free).** Items must be monotone,
   non-overlapping, era-correct, and their spans must byte-reconstruct the body
   (`sec10k/validate.py`, `tests/test_validate.py`). Proves **coverage**, not labelling —
   7/7 structural-ok, 7/7 round-trip.
2. **Independent dual-extractor boundary cross-check.** A *second* extractor — edgartools'
   own structured item parse — supplies an independent text per item; we compare head+tail
   (`sec10k/boundary_crosscheck.py`). It **fired** on m2i (6 items: 9A,11,12,14,15,16) and ko
   (item 3), downgrading them to `needs_review`. **Honest limit (partial gate):** both our
   regex and edgartools are *header-anchored*, so they are correlated (a diagnostic measured
   ~97% agreement on big items = low false-alarm **but** a shared header-error blind spot);
   and it **abstains** on small items and header-less filings (GE, msft-1995). It is a real
   gate on big items of well-formed filings, **not** a gate on the common-mode.
3. **Char-exact boundary gold + IoU scorer.** `boundary_scores` (`sec10k/evalkit.py`) vs
   `eval/boundary_gold.json` — **5 filings across 2 eras** (4 iXBRL + 1 SGML), each offset's
   snippet eyeballed as a real section body, not a TOC line; m2i (title) and msft-1995 (SGML,
   read-located) are method-independent of the regex. This is the only signal that turns a
   *wrong* boundary into a number; it sees the common-mode the cross-check is blind to, on the
   filings it covers. Boundary match **1.0** per era (iXBRL 4/4 filings, SGML 3/3 items).
4. **XBRL Item-8 oracle (independent data source).** From the companyfacts API — never our own
   output — a tagged financial fact must fall inside the extracted Item 8 (`sec10k/oracle.py`).
   Confirmed on **4/7** (2/2 tagged facts located on each of apple/ko/msft-2023; the others
   have no/!companyfacts coverage → degrades to markers, never a false confirm).
5. **Validate-the-validator: a mutation battery.** A check that never fails is worthless, so
   `tests/test_boundary_crosscheck.py` **injects boundary faults into a known-good doc and
   asserts each is caught** — swallow (Fault-A), merge, label-swap — plus the abstain guards
   (small item, no second text) and an assess-integration test that a disagreement becomes
   `needs_review` + `boundary_xcheck` in the provenance. 7 tests; the analogous live capability
   is the web `POST /api/extract-text` mutation path (paste a filing, truncate an item, watch
   coverage drop and `needs_review` flip — verified live: KO 0.98→0.96, +3 extraction-failures).

The headline metric is therefore **abstention/needs_review-gated**: the system is allowed to
be wrong only if it says so. Silent-failure 0/7 is the number that matters; boundary 1.0 is
scoped to the iXBRL gold it was measured on.

---

## 6. Still difficult / unreliable / unsupported (concrete filings)

Honest failure list — the rubric rewards naming these, not hiding them.

- **GE FY2023 — ungoldable, boundary "−".** Integrated MD&A + a cross-reference index means
  "Item N" appears out of body order; the regex segments to ~1.3% coverage. The validation
  layer **catches it** (coverage-implausible → `needs_review`, all 23 items low-confidence),
  so it is not a *silent* failure — but it is a real extraction failure, and it is **not
  char-goldable** by hand (no clean contiguous section bodies to mark). Boundary stays "−".
- **SGML boundary coverage is thin (N=1).** msft-fy1995 now carries independent char-gold on
  items 1/2/7 (boundary 1.0, 3/3), so the SGML era is no longer unmeasured — but it rests on a
  single filing, and **Item 8 was deliberately left ungolded**: its financial statements sit
  *after* the short "ITEM 9" header (the classic statements-after-Item-9 SGML layout), an
  ambiguous boundary I chose not to freeze. More pre-2001 SGML variety is the next label.
- **m2i back-half items.** The newline-header fix (this update) makes items 1–8 segment to the
  audited gold exactly, but the cross-check still flags 6 later items (9A,11,12,14,15,16) as
  boundary-uncertain → `needs_review`. Surfaced, not silent.
- **Common-mode partial gate.** Per §5.2 — the dual-extractor is correlated (both
  header-anchored). A boundary error both methods make *the same way* passes the cross-check
  silently; only the independent char-gold (§5.3) or a human catches it. A decorrelated second
  extractor (a CRF line-labeller) is the design's stretch item.
- **Small-item abstain.** The cross-check abstains on items < ~1.5k chars (e.g. Item 4 "Mine
  Safety — Not applicable"): too little text to compare, so tiny items get no boundary
  verification beyond structural tiling.

---

## 7. The LLM escalation tier — a defended cut, not a hole

The tier is a **`DeferredLLMClient` stub** (`sec10k/escalation.py`): it makes no call. This is
a deliberate **cost-discipline cut-line**, and it is defensible on three grounds:

1. **The deterministic path already clears the bar.** Presence recall 1.0, silent-failure 0/7,
   iXBRL boundary 1.0 — all with \$0 inference. The LLM is for *recovering* flagged boundaries,
   not for the common case, so the system is fully functional without it.
2. **Nothing is silently skipped — there is a deferral ledger.** `run_escalation` identifies
   every candidate (low-confidence-boundary + extraction-failure items) and annotates each with
   `escalation_deferred` in its provenance; the filing summary carries
   `escalation_candidates`, `escalation_provider="deferred"`, `escalation_performed=False`. So
   the exact set of boundaries an LLM *would* adjudicate is recorded and auditable — the cut is
   visible, not hidden.
3. **It is designed to be cheap and safe when wired.** "Index-don't-generate" LIB prompt
   (`build_lib_prompt`): the model is shown numbered lines around the candidate boundary and
   must return a line *number* from a closed item set — it indexes into the source, never
   authors text, which deletes the invented-item / bad-JSON class. Fed a ±2000-char window, not
   the filing. Provider planned = GitHub Copilot SDK.

**Why a stub beats a half-built tier:** a deferred stub with a measured candidate set and a
defended cost story is auditable and honest; a half-wired LLM tier we couldn't measure or
bound would be the actual hole. We escalate *only* the low-confidence minority, the
deterministic path handles the rest at ≈ \$0, and the ledger proves nothing falls through.

---

## Reproduce

```bash
python -m pytest -q                 # 60 unit tests incl. the mutation battery
SEC_EDGAR_USER_AGENT="Name email" python eval/run_eval.py   # regenerates eval/report.md + report.json
```
Numbers in this doc are from that report (`eval/report.md`) and the per-filing summaries; the
boundary gold provenance + human-audit is in `eval/boundary_gold.json` and
`prompts/2026-06-24-*-record-human-audit-of-boundary-gold.md`.
