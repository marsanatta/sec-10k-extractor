# 16 — Eval Frameworks & Statistical Rigor: A Concrete Harness Spec

研究日期: 2026-06-22
來源數量: 7 primary references (all fetched and cited inline)
信心程度: High on the framework structure, metric definitions, and statistical formulas (all quoted from primary sources). Medium-High on the specific N/CI numbers — those are exact binomial arithmetic, but the *adequacy* judgement ("150 gold is enough for X") is a design call tied to our labeling budget, stated as such.

> This doc turns 7 eval-methodology references into a buildable harness for OUR mission: a 10-K item-extraction pipeline with **no public filing-level ground truth**, a **stratified eval set (N≈600)**, a **150-filing gold subset**, and a **~90k silver baseline**. It depends on `08-eval-set-construction.md` (where gold/silver/structural tiers and strata are defined) and `06-confidence-and-silent-failure.md` (structural invariants and escalation band).

---

## TL;DR

- **Structure the harness as Inspect AI's `Task = Dataset + Solver + Scorer`** [Inspect]. Our Solver is the extraction pipeline; we attach **four independent Scorers** that run at different scopes: (1) structural-invariant scorer (100% of filings, label-free), (2) round-trip/coverage scorer (100%, label-free), (3) XBRL-cross-check scorer (Item 8 only, label-free, independent data source), (4) gold-set boundary-F1 scorer (150 filings, the only true ground truth).
- **Grade the produced output, not the path** [Anthropic]. Item boundaries are a state we verify; we never score on which heuristics/LLM-calls the pipeline took to get there.
- **Report every rate with a standard error in parentheses** [Miller], and because filings carry **multiple items each**, use **clustered standard errors** (filing = cluster) for per-item F1 — naive SE can understate uncertainty by >3× [Miller].
- **Abstention is a first-class metric, not a side-effect** [Know Your Limits]. Our "needs-review" escalation band is scored with **Coverage, Reliable-Accuracy (R-Acc), Effective Reliability, and AURC** — so we can prove the band catches the filings we get wrong instead of just refusing the hard-but-correct ones.
- **Reliability across nondeterministic re-runs = pass^k** [tau-bench]. Because LLM escalation is nondeterministic, "filing X extracts reliably" means **all k repeated runs pass**, reported as pass^k, not a single lucky pass@1.
- **Track cost-per-filing as a primary axis** [HAL]: dollars and tokens per filing, broken down by tier (deterministic vs LLM-escalated), reported on the same table as accuracy so we can see the cost/accuracy Pareto.

---

## Research plan (sub-questions → answer location)

1. How should the harness be structured? → §A (Inspect task/solver/scorer)
2. What does each scorer compute and at what scope? → §B
3. What metrics on gold vs 100%? → §C
4. How do we score the escalation/needs-review band? → §D (abstention)
5. How do we report uncertainty on only 150 gold filings? → §E (Miller CIs + clustering)
6. How do we express per-filing reliability under nondeterminism? → §F (pass^k)
7. How do we track cost? → §G (HAL)
8. Final crisp spec → §H ("Our eval harness spec")

---

## A. Framework structure — Inspect AI's `Task = Dataset + Solver + Scorer`

Inspect composes an eval as **`Task(dataset=..., solver=..., scorer=...)`** — a Dataset of labeled samples, a Solver that produces the answer, and one or more Scorers that evaluate the output ([Inspect AI](https://inspect.aisi.org.uk)). A Solver can be "as simple as a single `generate()` call … or as sophisticated as a full agent that uses tools over many turns" [Inspect] — which maps cleanly onto our tiered pipeline (regex/anchor pass → LLM escalation). Crucially, **a Task can carry multiple scorers**, and scorers can be code-based or model-graded; Inspect ships `match()`, `includes()`, `model_graded_qa()`, and F1-style metrics, plus custom scorers for "domain-specific evaluation logic beyond these built-ins" [Inspect].

This is the right backbone for us because our problem has **four different ground-truth situations at four different scopes**, and Inspect lets each be a separate scorer over the same solver output:

```
Task: 10k-item-extraction
  Dataset:
    - gold:   150 filings, target = char-exact item-boundary offsets (hand-labeled)
    - eval:   ~600 filings, stratified (era × size × pathology), no per-item target
    - silver: ~90k filings, machine-labeled boundaries (EDGAR-CORPUS), known-noisy
  Solver:
    - run_extraction_pipeline()   # deterministic pass + LLM escalation; emits items + confidence + escalation flag
  Scorers (all four attached to the task, each emitting its own metrics):
    1. structural_invariant_scorer   scope: 100% (eval + silver + gold)
    2. roundtrip_coverage_scorer      scope: 100%
    3. xbrl_crosscheck_scorer         scope: 100% where companyfacts exists (Item 8)
    4. gold_boundary_f1_scorer        scope: gold (150) only
```

**Grade state, not path** [Anthropic: "grade what the agent produced, not the path it took"]. We score the *resulting boundary set*, never the sequence of heuristics or LLM calls that produced it — different valid pipelines (anchor-hit vs LLM-recovered) that yield the same correct offsets must score identically. Anthropic also warns that **a 0% pass rate is usually a broken task/grader, not an incapable system**, and to **read the transcripts** — so each scorer must emit, alongside its score, the concrete diff (predicted vs reference offsets, or which invariant tripped) for manual triage.

> Engineering-rigor guard (CLAUDE.md + doc 08): the gold labels and the XBRL cross-check must be **independent of the production code and of the silver toolkit**. If a scorer reuses the same regex lineage as the extractor, agreement is self-consistency and proves nothing [Anthropic stresses calibrating graders against humans; we extend that to *source independence*].

---

## B. The four scorers — what each computes

### B.1 Structural-invariant scorer (label-free, 100%)
Pass/fail per filing on enumerable invariants from `06-confidence-and-silent-failure.md`: item offsets are **monotonic & non-overlapping**, ranges **cover the document body** (no large unassigned gaps), every **expected item for that era is present-or-explicitly-reserved** (e.g. Item 6 `[Reserved]` post-2021, Item 1C post-2023). This is a **code-based grader** — Anthropic's preferred default because it is "fast, cheap, objective" [Anthropic]. Emits: per-invariant pass-rate + an overall structural-pass flag used as one abstention signal (§D).

### B.2 Round-trip / coverage scorer (label-free, 100%)
Reconstruct the source body by concatenating extracted item spans in order; measure **character coverage** (% of non-boilerplate body assigned to exactly one item) and **round-trip fidelity** (reconstructed == original modulo whitespace). This is the analogue of a round-trip validation check: it cannot confirm boundaries are *semantically right*, but it catches dropped/duplicated/overlapping spans with zero labeling. Emits: coverage% and round-trip pass-rate (100% of filings).

### B.3 XBRL-cross-check scorer (label-free, independent source, Item 8 scope)
For filings with iXBRL/companyfacts, the financial-statement block (Item 8) has machine-readable fact anchors from a **different data source** than our text extractor. We check that our Item 8 span **contains the XBRL-tagged financial facts** and that its boundary aligns with the fact layer. This is the one place we get near-ground-truth for free, and because companyfacts is independent of our boundary output it is **not self-consistent** [doc 08]. Emits: Item-8 boundary-agreement rate on the iXBRL-eligible subset.

### B.4 Gold boundary-F1 scorer (true ground truth, 150 filings)
The only scorer with hand-labeled targets. **Per-item boundary F1**: for each item type, predicted span vs reference span. Define a match by character-offset overlap (report both exact-offset and tolerant IoU ≥ 0.95 variants — exact for "did we nail it", tolerant for "off by whitespace"). Aggregate as **macro-F1 over item types** (so rare items like 1C/7A aren't drowned by Item 8) and **micro-F1 over all items**. This is Inspect's F1/`match`-family scorer with a custom offset-overlap predicate. Emits: per-item P/R/F1 with clustered CIs (§E).

---

## C. Metrics — gold vs 100%

| Metric | Scope | Source scorer | What it answers |
|---|---|---|---|
| Per-item boundary **F1** (macro + micro) | 150 gold | B.4 | "How accurate are our boundaries, truly?" |
| Structural-invariant **pass-rate** | 100% (≈600 eval + 90k silver) | B.1 | "On every filing, do boundaries obey the rules?" |
| **Coverage% / round-trip pass-rate** | 100% | B.2 | "Did we drop or overlap any text anywhere?" |
| Item-8 XBRL **agreement rate** | iXBRL subset | B.3 | "Does the one machine-checkable boundary line up?" |
| Silver **disagreement rate** (per stratum) | ~600 vs silver | (diff) | localizes where we or silver are wrong → routes to gold (doc 08) |

The 100%-scope label-free metrics are what let us make claims about the **whole 90k corpus** despite only 150 labeled filings: gold gives us *calibrated accuracy* on a sample, and the structural/coverage/XBRL scorers give us *necessary-condition* coverage on everything. A filing that passes all structural checks isn't proven correct, but a filing that **fails** one is proven suspect — that asymmetry is the backbone of the escalation band.

---

## D. Abstention metrics for the needs-review / escalation band [Know Your Limits]

Our pipeline doesn't just emit boundaries — it emits a **confidence and an escalation flag** ("needs-review"). That is exactly an abstention decision, and the survey gives us the precise metrics to grade it. Partition every scored filing into five cells by (answered vs abstained) × (would-have-been correct vs incorrect), then [[Know Your Limits, arXiv:2407.18418](https://arxiv.org/abs/2407.18418)]:

- **Coverage** = proportion of filings where we *provide* an answer (don't escalate). Survey: "proportion of instances where the model provides an answer."
- **Reliable-Accuracy (R-Acc)** = N₁/(N₁+N₂+N₄) — accuracy *among the filings we did NOT escalate*. This is the number a downstream consumer actually trusts: "extent to which answers can be trusted when they do not abstain." **This is our headline auto-pipe quality metric.**
- **Effective Reliability (ER)** = (N₁ − N₂ − N₄)/total — rewards correct auto-answers, penalizes confident-but-wrong, ignores honest escalations. Balances coverage against reliability in one number.
- **Abstention Recall / Prudence** = N₅/(N₂+N₄+N₅) — of the filings we'd get wrong, what fraction did we correctly escalate? **This is the silent-failure metric**: high recall ⇒ few wrong filings slip through as "confident."
- **Over-abstention (ARSP)** = N₃/(N₁+N₂+N₃) — fraction of filings we needlessly escalated though we'd have been right. The cost side: too high ⇒ humans drowning in false review.
- **AURC / AUACC / Coverage@Accuracy** — threshold-free curves over the confidence score. **AURCC** (area under risk-coverage; "lower indicates better") and **Coverage@Accuracy** ("maximum coverage maintaining a specified accuracy threshold") let us *set* the escalation threshold to hit a target like "auto-pipe R-Acc ≥ 99%, report the resulting coverage."

**How we use it:** sweep the escalation threshold, plot the risk-coverage curve, and pick the operating point as **Coverage@(R-Acc = target)**. We report R-Acc, Coverage, Abstention-Recall, and AURC together — proving the band catches the filings we get wrong (high recall, low risk on covered) without escalating everything (acceptable coverage). The "should abstain when query is unanswerable/ambiguous or model confidence insufficient" criterion [survey] maps directly onto our structural-invariant failures and low-confidence LLM recoveries feeding the flag.

---

## E. Statistical rigor — CIs on 150 gold filings [Miller]

Miller's rule: **report the standard error of the mean beneath every score** (e.g. "F1 = 0.91 (0.02)"), and include the number of questions and clusters in the table [[Adding Error Bars to Evals, arXiv:2411.00640](https://arxiv.org/abs/2411.00640)].

**For a pass-rate / proportion** (structural pass-rate, Item-8 agreement) the Bernoulli SE is:

```
SE = √[ p̂(1 − p̂) / n ]          95% CI = p̂ ± 1.96·SE
```

At the **whole-corpus 100% scope (n ≈ 600 eval, or 90k silver)** this CI is tight: at n=600, p̂=0.90 → SE ≈ 1.2%, half-width ≈ 2.4%. So our **label-free 100%-scope metrics are well-powered** — that is the statistical payoff of having label-free scorers run on everything.

**The 150-gold F1 is the hard case, and it has a clustering problem.** Each gold filing contributes **many item boundaries** (≈10–15 items), so the ~150 filings yield ~1,800 item-level F1 decisions — but those decisions are **correlated within a filing** (a filing whose TOC we misread fails many items at once). Miller's clustered SE (cluster = filing) is mandatory here; he shows clustered SE can be **">3× larger than naive"**:

```
SE_clustered = √[ SE_CLT²  +  (1/n²) Σ_c Σ_i Σ_{j≠i} (s_{i,c} − s̄)(s_{j,c} − s̄) ]
```

So we report F1 with **filing-clustered** CIs, and we report **n_items AND n_filings (=150)** in the table. Naively treating 1,800 item decisions as independent would advertise a falsely tight CI — exactly the over-claim CLAUDE.md forbids.

**Is 150 gold enough?** Honestly: it is enough for a **macro-level F1 with a ±3–5% clustered CI**, which is adequate to *track regressions* and to *calibrate silver*. It is **not** enough to certify per-rare-item F1 (Item 1C, 7A stub) — those strata have a handful of filings and their CIs will be wide; we report them with explicit wide error bars and flag them `[UNVERIFIED at tight CI]` rather than pretending. Miller recommends **≥1,000 questions for good signaling**; our 150 *filings* clear that at the *item* level (~1,800 decisions) for the aggregate, but **not per stratum** — which is the honest limitation. For **comparing two pipeline versions**, use Miller's **paired-difference** SE on the *same* gold filings — `SE_{A−B} = √[SE_A² + SE_B² − 2·Corr·SE_A·SE_B]` — a "free reduction in estimator variance" that detects a small improvement with far fewer filings than two independent runs would need.

---

## F. Per-filing reliability under nondeterminism — pass^k [tau-bench]

LLM escalation makes the pipeline **nondeterministic**: the same filing can extract correctly on one run and fail on another. A single pass@1 overstates reliability. tau-bench introduced **pass^k** precisely for "the reliability of agent behavior over multiple trials," and reports that reliability collapses with k — **pass^8 < 25% in the retail domain** [[tau-bench, arXiv:2406.12045](https://arxiv.org/abs/2406.12045)]. Anthropic frames the same pair: **pass@k** = "likelihood of success in k attempts"; **pass^k** = "probability that *all* k trials succeed," and notes that as k grows "pass@k approaches 100% while pass^k falls to 0%" [Anthropic].

We adopt the standard unbiased estimator: run each eval filing **n times**, count **c** successes (per a chosen per-filing pass predicate), and estimate the probability that k i.i.d. runs all pass as:

```
pass^k(filing) = C(c, k) / C(n, k)        averaged over filings
```

**What "pass" means per filing for us:** the run satisfies all structural invariants AND (on gold) hits the F1 threshold. **Why we use pass^k not pass@k:** our product is a *batch extraction over 90k filings consumed downstream* — we need each filing right *consistently*, not "right if we retry until lucky." That is the customer-facing-reliability case Anthropic says calls for pass^k. We report **pass^1, pass^3, pass^5** per stratum; a filing/stratum whose pass^k decays sharply with k is a **nondeterminism hot-spot** → either pin temperature/seed there or route it permanently to the review band (§D). (tau²-bench reinforces that performance/reliability drops sharply once an interactive/nondeterministic element is added — "significant performance drops … from no-user to dual-control" [[tau²-bench, arXiv:2506.07982](https://arxiv.org/abs/2506.07982)] — a general warning that any added stochastic component degrades reliability, which justifies measuring it explicitly rather than assuming determinism.)

---

## G. Cost-per-filing tracking [HAL]

HAL standardizes a harness that "orchestrates parallel evaluations … reducing evaluation time from weeks to hours" and, critically, **tracks cost as a primary axis** — 21,730 rollouts at ≈ **$1.84 per rollout**, reporting the **cost-vs-accuracy Pareto** and surfacing that "higher reasoning effort reduc[es] accuracy in the majority of runs" [[HAL, arXiv:2510.11977](https://arxiv.org/abs/2510.11977)]. We adopt this directly:

- **Emit per-filing cost**: input/output tokens and $ for any LLM escalation, plus wall-time. A deterministic-pass-only filing costs ~$0; an escalated filing carries the LLM cost. Report **mean and p95 cost-per-filing**, broken down by **tier** (deterministic vs escalated) and **by stratum** (the hard SRC/SGML tail is where escalation — and cost — concentrates).
- **Put cost on the same table as accuracy** so we read the Pareto: e.g. lowering the escalation threshold raises Coverage and R-Acc but raises mean cost-per-filing — HAL's point is that this tradeoff must be *visible*, and that more LLM effort is not monotonically better.
- HAL's reproducibility lesson (agents "searching for the benchmark on HuggingFace instead of solving the task") maps to our **read-the-transcripts** discipline: log raw LLM calls so we can catch the extractor exploiting an artifact (e.g. keying off a filename pattern) rather than reading the document.

---

## H. Our eval harness spec

**Structure (Inspect AI):** one `Task` = our extraction `Solver` + a `Dataset` with three splits (gold 150 / eval ≈600 / silver ≈90k) + **four independent Scorers**, each at its own scope. Grade **output state, not path**; keep gold labels & XBRL check **source-independent** of the extractor and silver.

**Scorers**
1. **Structural-invariant scorer** — label-free, 100%. Monotonic & non-overlapping offsets, body coverage, era-correct item presence/`[Reserved]`. Code-based.
2. **Round-trip / coverage scorer** — label-free, 100%. Char-coverage% + reconstruct-and-compare. Catches drops/overlaps.
3. **XBRL-cross-check scorer** — label-free, Item-8 scope, **independent source** (companyfacts). Boundary-agreement on iXBRL subset.
4. **Gold boundary-F1 scorer** — 150 gold, true ground truth. Per-item P/R/**F1**, macro (rare-item-fair) + micro, exact-offset + IoU≥0.95.

**Metrics**
- **Accuracy:** per-item macro/micro **F1** on 150 gold; structural pass-rate, round-trip pass-rate, Item-8 XBRL agreement on 100%.
- **Abstention (escalation band) [Know Your Limits]:** **R-Acc** (headline auto-pipe quality), **Coverage**, **Effective Reliability**, **Abstention-Recall/Prudence** (silent-failure metric), **Over-abstention (ARSP)**, and **AURC / Coverage@(R-Acc target)** to set the threshold.
- **Reliability under nondeterminism [tau-bench]:** **pass^k** (k=1,3,5) per filing/stratum via `C(c,k)/C(n,k)` over n repeated runs; flag pass^k-decay hot-spots.
- **Cost [HAL]:** mean & p95 **$/filing and tokens/filing**, split by tier and stratum, reported on the same table as accuracy (cost/accuracy Pareto).

**How we report uncertainty [Miller]**
- Every rate prints as **value (SE)** with **n_filings and n_clusters** shown.
- Proportions: Bernoulli **SE = √[p̂(1−p̂)/n]**; 95% CI = p̂ ± 1.96·SE. Tight at 100% scope (n≈600 → ±~2.4%).
- **Per-item F1: filing-clustered SE** (cluster = filing; Miller's estimator) — never treat ~1,800 item decisions as independent (clustered SE can be >3× naive).
- **Honest limits:** 150 gold ⇒ adequate ±3–5% clustered CI on aggregate F1 and for regression-tracking/silver-calibration; **insufficient** for tight per-rare-item-stratum F1 → those reported with explicitly wide bars, marked `[UNVERIFIED at tight CI]`.
- **Version comparison:** Miller **paired-difference** SE on the *same* gold filings for a free variance reduction.
- **Sanity guard [Anthropic]:** a 0% (or 100%) score ⇒ inspect the task/grader first; always keep the predicted-vs-reference diff for transcript review; never let a scorer share lineage with the extractor (no self-consistency).

---

## Sources

1. Anthropic — "Demystifying evals for AI agents." https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents — eval-driven dev, grade-state-not-path, code/model/human graders, pass@k vs pass^k framing, 0%-pass = broken-task, read-the-transcripts.
2. Inspect AI (UK AISI). https://inspect.aisi.org.uk — `Task = Dataset + Solver + Scorer`; multiple scorers per task; built-in `match`/`includes`/`model_graded_qa`/F1; custom scorers.
3. tau-bench — Yao et al. https://arxiv.org/abs/2406.12045 — pass^k as multi-trial reliability metric; pass^8 < 25% (retail). (Estimator `C(c,k)/C(n,k)` is the standard published form; abstract-level fetch confirmed the metric's purpose and the pass^8 figure.)
4. tau²-bench — https://arxiv.org/abs/2506.07982 — dual-control Dec-POMDP; compositional verifiable task generator; "significant performance drops … from no-user to dual-control" (nondeterminism/interaction degrades reliability).
5. HAL (Holistic Agent Leaderboard) — https://arxiv.org/abs/2510.11977 — standardized parallel harness; cost-per-rollout (≈$1.84, $40k/21,730 rollouts); cost/accuracy Pareto; "higher reasoning effort reduc[es] accuracy"; benchmark-exploit transcripts.
6. "Know Your Limits" abstention survey — https://arxiv.org/abs/2407.18418 — Coverage, R-Acc, Effective Reliability, Abstention-Recall/Prudence, ARSP over-abstention, AURCC/AUACC/Coverage@Accuracy; cell definitions N₁..N₅.
7. "Adding Error Bars to Evals" — Miller. https://arxiv.org/abs/2411.00640 — SE of the mean + 1.96·SE CI; Bernoulli SE √[p̂(1−p̂)/n]; **clustered SE** (>3× naive); paired-difference variance reduction; report SE & cluster counts; ≥1,000-question signaling guidance.
