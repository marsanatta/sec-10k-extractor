# Calibrated Confidence, Abstention & Constrained Decoding (Research)

How four primary papers upgrade the confidence/abstention machinery in
`06-confidence-and-silent-failure.md`. The thesis of doc 06 is: attach **calibrated**
confidence to every extracted item, make silent failure structurally impossible, and use an
LLM only on flagged regions. These papers give us (a) a *statistical guarantee* for our
confidence bands, (b) a *hard* fix for LLM parse failures, (c) a *warning* about trusting the
LLM's stated confidence, and (d) a *cheap* escalation trigger.

Sources:
- Conformal prediction for NLP (survey) — https://arxiv.org/abs/2405.01976
- XGrammar (constrained/structured decoding) — https://arxiv.org/abs/2411.15100
- Verbalized confidence (Xiong et al.) — https://arxiv.org/abs/2306.13063
- Semantic Entropy Probes (Kossen et al.) — https://arxiv.org/abs/2406.15927

---

## 1. Conformal prediction → a coverage guarantee on our confidence bands

**Core idea.** Split (inductive) conformal prediction turns *any* heuristic score into a
prediction set with a **distribution-free, model-agnostic** statistical guarantee. It needs
only a held-out calibration set and a nonconformity score; it makes no assumption about the
score being well-calibrated to begin with. ([2405.01976](https://arxiv.org/abs/2405.01976))

**Concrete mechanism.**
1. Pick a nonconformity score `s(x, y)` — "how unlikely is this (input, label) pair." For a
   classifier with probability `p(y|x)`, the standard choice is `s(x,y) = 1 − p(y|x)`.
2. On a calibration set of `n` labelled examples, compute scores `s_i = s(x_i, y_i)`.
3. Set the threshold to the **`⌈(n+1)(1−α)⌉ / n` empirical quantile** of those scores → `q̂`.
4. At test time, output the set `C(x) = { y : s(x, y) ≤ q̂ }`.

**The guarantee (theorem).** `P[ Y_test ∈ C_α(X_test) ] ≥ 1 − α`. This **marginal coverage**
holds under **exchangeability** (weaker than i.i.d.; the joint distribution is permutation-
invariant) — no assumption that the underlying model is correct or calibrated.

**How it maps to our needs — yes, we can give our bands a statistical guarantee.** Doc 06
already plans to "calibrate on a small stratified gold set" mapping signal combinations →
empirical accuracy. Conformal makes that calibration *rigorous* rather than hand-weighted:

- **Per-item, treat boundary/label correctness as the classification target.** Our cheap
  signals (dual-extractor agreement distance, content-heuristic score, XBRL-in-Item-8
  check, template match) become features of a nonconformity score `s` for "is this item's
  span correct." Calibrate `q̂` on the hand-labelled gold subset
  (`08-eval-set-construction.md`). Then **"High" confidence = the conformal set is the
  singleton `{correct}` at our chosen `α`** — and that label now carries a *provable*
  ≥ 1−α coverage rather than a guessed weight.
- **Set size *is* the abstention signal.** "Set size directly encodes uncertainty… single-
  element sets = high confidence; larger sets = ambiguity." A per-item conformal set that
  is empty (score above threshold for every candidate boundary) or large ⇒ **abstain /
  escalate**. This is exactly doc 06's Low/needs-review band, now with a knob (`α`) that
  *controls the escalation rate to a target miss-rate*.
- **Caveat we must respect — exchangeability.** The guarantee assumes the calibration set
  and test filings are exchangeable. 10-K filings are **not** exchangeable across format
  eras (1990s SGML vs modern iXBRL — see `04-format-variance-taxonomy.md`). Naive
  conformal would give correct *marginal* coverage but silently under-cover the legacy
  slice. **Mitigation: stratify / use Mondrian (class-conditional) conformal** — calibrate a
  separate `q̂` per filing-era / per-item-type cohort, so coverage holds *within* each hard
  slice, not just on average. This is the honest move; a single global `q̂` would hide
  legacy failure behind good average numbers — precisely the silent failure doc 06 forbids.

**Adopt.** Conformal is the upgrade that makes our confidence bands *mean* a number.

---

## 2. XGrammar / constrained decoding → guarantee valid line-ID JSON from the escalation LLM

**Core idea.** Grammar-constrained decoding masks the next-token logits at every step to
**only** tokens that keep the output within a context-free grammar, so the generation is
**structurally valid by construction** — not validated after the fact.
([2411.15100](https://arxiv.org/abs/2411.15100))

**Concrete mechanism.** XGrammar represents the grammar as a **byte-level pushdown
automaton** (the formal recognizer for context-free languages) and at each step intersects
the automaton's allowed set with the vocabulary, zeroing the logits of disallowed tokens.

**Why it's fast (the innovation).** It splits the vocabulary into **context-independent**
tokens (whose validity doesn't depend on the parse stack — precomputable into an adaptive
mask cache) and **context-dependent** tokens (resolved at runtime). For Llama-3.1 + JSON,
**context-dependent tokens are < 1% (1,134 of 128k)**, so > 99% is precomputed; mask memory
drops to **0.2% (160 MB → 0.46 MB)**. Result: **up to 100× faster per-token masking**
(< 40 µs/mask), **up to 80× faster end-to-end serving** on H100, and **near-zero TPOT
overhead** (6.2 → 6.3 ms at batch 1).

**How it maps to our needs — this eliminates a whole class of parse failures.** Doc 06's
escalation step is **"index, don't generate"**: the LLM must return *line-IDs / offsets* that
point into the source, never free text. The failure mode of any JSON-from-LLM step is a
malformed or schema-violating response that crashes the pipeline or, worse, gets silently
coerced. Constrain the escalation LLM with a grammar that admits **only** our output shape,
e.g.

```
item_id   = "1" | "1A" | "1B" | "1C" | "2" | ... | "15"   // closed enum
line_ref  = integer within [doc_first_line, doc_last_line]  // bounded
response  = "[" { "{" item_id "," start_line "," end_line "}" } "]"
```

- **Guarantees a parseable, schema-valid response 100% of the time** → removes "LLM
  returned bad JSON" from the silent-failure surface entirely.
- **Restricts `item_id` to the closed canonical set** → the LLM *cannot* invent a non-
  existent item; an out-of-grammar hallucination is impossible at the token level.
- **Bounds `line_ref` to the document's actual line range** → enforces "index, don't
  generate" *mechanically*; the model literally cannot emit an offset outside the source.
- Engines: vLLM/SGLang ship XGrammar; the Outlines/llama.cpp grammar route is equivalent in
  guarantee (slower). If we self-host the escalation model, this is free.

**Caveat (don't over-claim).** Grammar validity ≠ *semantic* correctness. A grammar forces a
*well-formed* line-ID answer; it does **not** force the *right* line. The conformal/round-
trip/dual-extractor checks in doc 06 still decide whether that valid answer is *correct*.
Constrained decoding removes the *parse* failure mode, not the *labelling* one.

**Adopt.** Cheap, high-leverage, removes an entire error class. No downside for our use.

---

## 3. Verbalized confidence → TRAP (with a narrow, supervised exception)

**Core idea.** Verbalized confidence = prompting the LLM to *state* a confidence number
("I'm 90% sure"), a black-box alternative to logit-based confidence usable on closed APIs.
([2306.13063](https://arxiv.org/abs/2306.13063))

**Key finding — they are systematically overconfident.** "LLMs, when verbalizing their
confidence, tend to be overconfident, potentially imitating human patterns." Stated numbers
cluster at round values (90%, 100%); calibration is poor and **AUROC is only ~0.52–0.61** —
barely above the 0.5 coin-flip floor. All methods "struggle in challenging tasks… requiring
professional knowledge" — and 10-K item boundaries on legacy filings *are* exactly that:
specialist, long-context, adversarial-format work.

**Mitigations exist but don't rescue it as a primary signal.** Human-inspired prompts,
sampling multiple responses + consistency aggregation narrow the gap — but the paper's own
conclusion is "significant scope for improvement remains."

**How it maps to our needs — this is a TRAP, and doc 06 already forbids it.** Doc 06's first
principle is **"self-consistency is not validation… an LLM judging its own output cannot
catch confident systematic errors."** Verbalized confidence is precisely that anti-pattern:
the *same* escalation model rating its *own* extraction. Its overconfidence means it will
report "95% confident" on a boundary it got systematically wrong on a 1996 SGML filing — the
exact silent failure we are paid to prevent.

- **Do NOT** use the escalation LLM's stated confidence as a confidence band or an abstention
  trigger. It fails on our hardest slice and is overconfident there.
- **Narrow exception:** if ever used, treat a *low* self-reported confidence as a *weak
  positive escalation signal only* (asymmetric — low can flag, high cannot reassure), and
  cross-check against an *independent* oracle (XBRL, dual-extractor, conformal set). Never
  let high verbalized confidence *raise* a band.

**Verdict: TRAP.** Useful as a paper to justify *why* doc 06 bans self-rating; not adopted as
a signal.

---

## 4. Semantic Entropy Probes → cheap, independent escalation trigger

**Core idea.** Semantic entropy (SE) detects hallucination by sampling several generations,
clustering them by *meaning*, and taking the entropy over semantic clusters — high entropy =
the model is unsure *what* it means. SE is a strong signal but costs **5–10× generations**.
**Semantic Entropy Probes (SEPs)** are linear probes on the hidden states of a **single**
generation that *approximate* SE at **near-zero added cost**.
([2406.15927](https://arxiv.org/abs/2406.15927))

**Concrete mechanism & numbers.**
- A logistic-regression probe on a **mid-to-late layer** hidden state, at the **Token-Before-
  Generation (TBG)** position (last *input* token, before any output) or **Second-Last Token
  (SLT)**. TBG means we get an uncertainty estimate **before spending a single output token**.
- AUROC rises in later layers, reaching **~0.7–0.95** depending on task.
- Probes are **trained to predict (binarized) semantic entropy, not accuracy** — and this
  SE-supervised target **generalizes ~8–10 AUROC points better out-of-distribution** than
  accuracy-trained probes (Mistral-7B +10.5, Phi-3 +9.9, Llama-2-70B +7.9). OOD generalization
  is the property we need, since our test filings span unseen format eras.
- Full SE (10 generations) still beats SEPs, but SEPs capture most of the signal for ~free.

**How it maps to our needs — a cheap, *independent* escalation trigger.** Doc 06's stack is
ordered cheap→expensive and wants a signal that decides *when to spend the expensive LLM
escalation*. SEPs fit:

- **For the escalation LLM step specifically** (where we do run a model on a flagged region),
  a SEP on the model's TBG hidden state gives an **uncertainty score before it generates the
  line-IDs**. High probe-SE on that region ⇒ the model is unsure ⇒ **route to human review**
  instead of trusting the (grammar-valid but possibly wrong) output. This is the calibrated
  abstention layer that verbalized confidence (§3) *cannot* provide.
- **It is independent of self-rating.** A probe on hidden states is a *different* method from
  asking the model — so unlike verbalized confidence, it doesn't violate doc 06's
  independent-oracle rule. It's white-box, but it is not the model judging itself in natural
  language.
- **Requirement / caveat:** SEPs need **hidden-state access** ⇒ only available on a
  **self-hosted / open-weight escalation model** (Llama/Mistral/Phi), not a closed API. This
  aligns with the XGrammar self-host path (§2): if we self-host for constrained decoding, we
  get SEP uncertainty for free off the same forward pass. If escalation runs on a closed API,
  SEPs are unavailable and we fall back to conformal set-size + structural oracles.

**Adopt — conditional on self-hosting the escalation model.** Otherwise note as future work.

---

## How this upgrades our confidence model in doc 06

The four papers slot cleanly into doc 06's three jobs (calibrate, abstain, force valid
output), each feeding a *specific* decision. Signal → decision map:

| Decision in doc 06 | Old (doc 06) | Upgraded signal | Paper |
|---|---|---|---|
| **What does a band *mean*?** Map signals→accuracy on gold set | hand-weighted bands | **Conformal `q̂` on stratified gold set** → bands carry provable ≥ 1−α coverage | 2405.01976 |
| **When to abstain / escalate?** Low/needs-review band | heuristic thresholds | **Conformal set size** (empty/large ⇒ abstain) — `α` directly tunes escalation rate to a target miss-rate | 2405.01976 |
| **Escalation LLM returns valid line-ID JSON** ("index, don't generate") | hope + post-parse | **XGrammar grammar** → 100% schema-valid; `item_id` ∈ closed set, `line_ref` ∈ doc range, by construction | 2411.15100 |
| **Should we trust the escalation LLM's own confidence?** | (banned by principle) | **NO — verbalized confidence is overconfident (AUROC ~0.52–0.61), worst on our hard slice.** Confirms doc 06's ban; allowed only as a weak *low-confidence* flag | 2306.13063 |
| **Cheap pre-generation uncertainty on the escalation step** | none | **SEP on TBG hidden state** (AUROC ~0.7–0.95, OOD-robust) ⇒ route uncertain regions to human review *before* generating | 2406.15927 |

**Concrete upgraded flow for a flagged region:**
1. Structural + round-trip + dual-extractor + XBRL oracles run first (unchanged, free, hard).
2. **Conformal** turns the combined signal vector into a per-item prediction set with a
   coverage guarantee; **set size decides the band** and whether to escalate. Stratify `q̂`
   by format era so legacy filings can't hide behind average coverage.
3. If escalating to the LLM: **XGrammar** forces a valid `{item_id, start_line, end_line}`
   response → no parse failures, no invented items, no out-of-range offsets.
4. **SEP** on the escalation model's TBG hidden state gives a free pre-generation uncertainty
   score; high ⇒ human review, low ⇒ accept the grammar-valid answer (still re-checked by the
   oracles in step 1).
5. **Verbalized confidence is never used to raise a band** — only, at most, a low self-report
   nudges toward review.

Net: doc 06 goes from *"signals combined by hand-tuned weights"* to *"signals combined under a
distribution-free coverage guarantee, with a tunable abstention rate, a mechanically valid
escalation output, and a cheap independent uncertainty probe — and a documented reason the
LLM's own stated confidence is excluded."*
