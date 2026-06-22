# LLM-as-Judge and Its Failure Modes — Synthesis for the 10-K Extractor

研究日期: 2026-06-22
來源數量: 8 (primary arXiv abstracts, all fetched and verified)
信心程度: High (every claim below is sourced to the paper's own abstract; numbers quoted verbatim)

## TL;DR

An LLM judge is a *correlated-with-the-generator* signal, not an independent oracle. The evidence is
consistent: judges agree with humans on subjective preference (>80%, MT-Bench) but collapse to near-random
on objectively-correct/wrong tasks (JudgeBench), favor low-perplexity / familiar / own-style text
(self-preference), can be gamed by unfaithful reasoning (up to +90% false positives), and a 9-model panel
buys only ~2 independent votes' worth of signal. For a 10-K extraction pipeline whose whole risk is
*confident systematic errors*, this means: an LLM judge is acceptable only as a **last-resort, non-gating
flag**, never as the primary correctness signal. Independent oracles (XBRL/companyfacts ground truth,
round-trip checks, deterministic validators) must decide; the judge may only triage what the oracles cannot
reach.

## Why this matters for us (the spine)

Our rigor rule (CLAUDE.md "Engineering Rigor"): *never use self-consistency as validation; a model judging
itself cannot catch confident systematic errors.* The 10-K failure modes we care about — wrong Item boundary,
hallucinated figure, dropped negation, mis-segmented section — are exactly the *confident, systematic* errors
that a same-family LLM judge is structurally blind to, because the judge shares the generator's priors and
rewards familiar-looking output. Five of these eight papers are direct evidence FOR that caution.

## Per-paper findings and the failure mode each implies

### 1. MT-Bench / Chatbot Arena — agreement, but on *preference* (arxiv.org/abs/2306.05685)
- Core: GPT-4 judge reaches "over 80% agreement" with human preference, "matching the same level of
  agreement between humans." Names four biases: position, verbosity, self-enhancement, limited reasoning.
- Failure mode for us: the 80% headline is on *subjective preference*, not factual correctness. The paper
  itself names self-enhancement and limited-reasoning bias. Do NOT import the "judges agree with humans"
  result into a correctness-gating context — it was never measured there. Source: https://arxiv.org/abs/2306.05685

### 2. G-Eval — CoT + form-filling (arxiv.org/abs/2303.16634)
- Core: GPT-4 with chain-of-thought + form-filling reaches Spearman 0.514 with humans on summarization,
  beating prior methods "by a large margin."
- The warning: authors "highlight the potential issue of LLM-based evaluators having a bias towards the
  LLM-generated texts."
- Failure mode for us: even the method that *advertises* CoT-judging admits it tilts toward LLM-style text.
  If our extractor and our judge are both LLMs, the judge will reward output that *reads* like a good
  extraction over output that *is* correct. Source: https://arxiv.org/abs/2303.16634

### 3. Prometheus 2 — open evaluator model (arxiv.org/abs/2405.01535)
- Core: best open evaluator; "closely mirrors human and GPT-4 judgements," supports direct assessment +
  pairwise ranking with user-defined criteria; "highest correlation and agreement among all tested open
  evaluator LMs" across 8 benchmarks.
- Best practice it implies: if we ever run a judge, use one with **explicit user-defined rubric criteria**
  (not a vague "is this good?") and prefer a model from a *different family* than our generator. But note:
  "mirrors GPT-4 judgements" is a feature for chat eval and a *liability* for us — it inherits GPT-4's
  blind spots. Source: https://arxiv.org/abs/2405.01535

### 4. JudgeBench — judge correctness meta-eval (arxiv.org/abs/2410.12784) — KEY caution
- Core: on objectively-verifiable correctness across knowledge / reasoning / math / coding, "many strong
  models (e.g., GPT-4o) perform just slightly better than random guessing." Crowd preference "is a poor
  indicator of factual and logical correctness."
- Failure mode for us: this is the load-bearing result. When the task is *was this extraction correct?*
  (objective, like ours) rather than *which answer do you prefer?* (subjective), a frontier judge is near
  a coin flip. A near-random signal CANNOT gate a pipeline. Source: https://arxiv.org/abs/2410.12784

### 5. PoLL — Panel of LLM judges (arxiv.org/abs/2404.18796)
- Core: a panel of smaller, *disjoint-family* models is ">7x less expensive," shows "less intra-model bias,"
  and can outperform a single large judge across 3 settings / 6 datasets.
- What it gets right: diversity across model families reduces self-preference, and cost drops.
- What it does NOT establish: that a panel removes *correlated* error on hard objective tasks — see #6,
  which directly tests that claim and finds it fails. Source: https://arxiv.org/abs/2404.18796

### 6. "Nine Judges, Two Votes" — panels don't fix correlated error (arxiv.org/abs/2605.29800) — KEY caution
- Core: 9 frontier judges from different families "effectively provide only about 2 independent votes' worth
  of information." "The best single judge matches or outperforms the full panel across all conditions."
  "Roughly three-quarters of the panel's nominal independence is lost because the models make the same
  mistakes on the same items." Panel accuracy "falls 8-22 percentage points short of what independent voting
  would achieve"; established fixes "close at most 11% of this gap, even with access to the correct answers."
- The verdict: "The bottleneck is correlated judges, not the aggregation algorithm... scaling up panels
  cannot substitute for genuinely independent evaluation."
- Failure mode for us: this directly refutes the temptation to "just add more judges." A jury of LLMs that
  share training data shares blind spots — exactly the *confident systematic error* our rule forbids us to
  paper over with self-consistency. Source: https://arxiv.org/abs/2605.29800

### 7. Self-preference bias — judges favor own/familiar outputs (arxiv.org/abs/2410.21819)
- Core: a quantitative self-preference metric shows LLMs "assign significantly higher evaluations to outputs
  with lower perplexity than human evaluators, regardless of whether the outputs were self-generated." The
  bias's "essence lies in perplexity" — judges "prefer texts more familiar to them," not literally
  recognizing their own text.
- Failure mode for us: the bias is *familiarity*, which is broader and sneakier than literal self-recognition.
  Avoiding "judging our own model" is necessary but NOT sufficient — any LLM judge over-rewards fluent,
  template-conforming extractions even when the figures are wrong. A wrong-but-fluent 10-K extraction is the
  worst case and the one this bias amplifies. Source: https://arxiv.org/abs/2410.21819

### 8. "Gaming the Judge" — unfaithful CoT fools judges (arxiv.org/abs/2601.14691) — KEY caution
- Core: rewriting only the reasoning trace (actions/observations unchanged) inflates SOTA judge false-positive
  rates "by up to 90% across 800 trajectories." Content-based manipulation (fabricating signals of task
  progress) beats style tweaks. Mitigations — "prompting-based techniques and scaling judge-time compute" —
  "reduce but don't eliminate" it: "a deep structural flaw."
- Failure mode for us: if our extractor emits a confident rationale ("Item 7 begins at the MD&A header on
  p.42"), a judge reading that rationale can be talked into a pass even when the boundary is wrong. The judge
  trusts narration over ground truth. Never let the judge read the generator's own justification as evidence
  of correctness. Source: https://arxiv.org/abs/2601.14691

## Synthesis

### (a) When an LLM judge IS acceptable for us
- **Flagging, never gating.** A judge may *raise* a "needs human/oracle review" flag; it may never *approve*
  an extraction as correct. (JudgeBench: near-random on objective correctness — too weak to gate.)
- Only on items our **independent oracles cannot reach** (no XBRL tag, narrative-only section with no
  structured counterpart) — i.e., last-resort, not first-line.
- With an **explicit rubric** (Prometheus 2) and a **different model family** than the generator (PoLL,
  self-preference) — these reduce, not remove, bias.
- As a **cheap pre-filter to prioritize human review queues**, where a false flag costs a glance, not a
  silent wrong number in output.

### (b) Why a panel/jury does NOT rescue correlated error
Nine Judges, Two Votes shows panels of frontier models share ~75% of their would-be independence — 9 votes
collapse to ~2, the panel is 8-22 pp worse than true independent voting, and even with the correct answers
in hand, aggregation tricks recover ≤11% of the gap. The bottleneck is *correlated judges*, not the voting
rule. Adding judges that share training data adds confidence, not coverage — it manufactures false agreement
on exactly the systematic errors we must catch. This is the formal proof of our self-consistency rule.

### (c) Concrete safeguards
1. **Independent oracles first.** XBRL / companyfacts numeric ground truth, round-trip reconstruction, and
   deterministic structural validators (Item header regex + monotonic offset checks) decide correctness.
   The judge runs *after* and *below* these.
2. **Judge as tie-breaker / triager only.** Its output is a `review_flag`, never a `pass`. No item ships on a
   judge's say-so.
3. **Avoid self-preference: do not judge our own model's output.** Use a different-family judge — and because
   the bias is familiarity/perplexity (not literal self-recognition), still treat fluent output with
   suspicion; fluency is not correctness.
4. **Watch for gamed CoT.** Do NOT feed the generator's own rationale to the judge as evidence. Judge against
   the *source document span* and *structured ground truth*, not against the extractor's narration.
5. **No panel-as-rescue.** Do not add more LLM judges to "increase confidence" on hard items — correlated
   error makes that a confidence illusion. Spend that budget on a real independent oracle or human review.
6. **Meta-eval the judge.** Before trusting any judge config, measure its false-pass / false-fail rate on a
   labeled hard-case set (XBRL-derived gold). If it is near-random on our items (JudgeBench pattern), demote
   it to flag-only and do not weight it.

## Our judge policy (decision)

The LLM judge is a **non-primary, non-gating, last-resort flag**. Correctness is decided by independent
oracles (XBRL/companyfacts ground truth, round-trip checks, deterministic structural validators) and, where
those cannot reach, by human review. The judge's *only* sanctioned job is to *prioritize what humans/oracles
review* — it can say "look here," never "this is correct." We will not use a panel/jury to substitute for an
independent oracle (Nine Judges: panels don't fix correlated error). We will use a different-family judge with
an explicit rubric, judge against source spans and structured ground truth rather than the generator's own
rationale, and meta-evaluate any judge's false-pass rate on XBRL-derived gold before trusting it at all. This
is the operational form of our rigor rule: a model judging itself — or its correlated cousins — cannot catch
the confident systematic errors that are our primary risk.

## Sources
1. MT-Bench / Judging LLM-as-a-Judge — https://arxiv.org/abs/2306.05685
2. G-Eval — https://arxiv.org/abs/2303.16634
3. Prometheus 2 — https://arxiv.org/abs/2405.01535
4. JudgeBench — https://arxiv.org/abs/2410.12784
5. PoLL (Panel of LLM evaluators) — https://arxiv.org/abs/2404.18796
6. Nine Judges, Two Votes — https://arxiv.org/abs/2605.29800
7. Self-Preference Bias in LLM-as-a-Judge — https://arxiv.org/abs/2410.21819
8. Gaming the Judge (unfaithful CoT) — https://arxiv.org/abs/2601.14691
