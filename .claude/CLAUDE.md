# Project Claude Code Rules — SEC 10-K Item Extractor

This is a **PUBLIC** repository submitted as a coding test. Everything committed here
will be read by external reviewers and indexed by anyone. The rules below are
NON-NEGOTIABLE and OVERRIDE any default behavior.

## Public Repo Security & Privacy (CRITICAL — read first)

This repo is public. Before writing, committing, or pushing ANYTHING, treat it as if
the whole internet will read it — because it will.

### Never commit personal or identifying information
- **No real names, emails, usernames, or phone numbers** — not in code, comments,
  commit messages, README, docs, sample data, or config. Use neutral placeholders
  (`you@example.com`, `Your Name`).
- **No employer-internal identifiers** — internal repo names, internal hostnames,
  internal URLs, ticket/PR IDs, team names, datacenter codes, service names, or
  internal file paths (e.g. anything under a corporate workspace). This project is
  unrelated to any employer's internal systems; keep it that way.
- **No local machine paths that leak identity** — avoid hardcoding absolute paths like
  `C:\Users\<name>\...`. Use relative paths or env-configured paths.
- **Git author identity** — make sure commits use a neutral/public identity, not a
  corporate email. Verify with `git config user.email` before the first commit.

### Never commit secrets, tokens, or credentials
- **No API keys, tokens, passwords, connection strings, private keys, or session
  cookies** — not even "temporary" or "test" ones, not even commented out.
- **Secrets come from environment variables only.** Read config via `os.environ` /
  `process.env`. Provide a `.env.example` with KEY=__placeholder__ values, never a real `.env`.
- **`.gitignore` must exclude** `.env`, `*.key`, `*.pem`, credential files, and any
  local cache/output that could contain fetched private data.
- If a secret is ever committed by accident, treat it as compromised: rotate it and
  scrub history — do not just delete in a later commit.
- Before any commit, scan the diff for things that look like secrets (long random
  strings, `sk-`, `Bearer `, `AKIA`, `-----BEGIN`). If unsure, stop and ask.

### Scope hygiene
- Only commit public or self-created material. No copyrighted datasets, no scraped
  private content. SEC filings are public-domain government data — fine to use.

### Pushing (requires explicit permission)
- **NEVER `git push` on your own initiative.** Pushing requires the user's explicit
  permission each time. Committing locally is fine; publishing is not — once pushed to a
  public remote, content is indexed and effectively permanent even if later deleted.
- **Before any push, audit what would be published.** Inspect the outgoing diff
  (`git log origin/<branch>..HEAD`, `git diff origin/<branch>..HEAD`) for:
  - personal / identifying info (real names beyond the public git author, emails, internal
    paths, internal hostnames/repo names, employer-internal identifiers)
  - secrets / tokens / credentials (API keys, passwords, connection strings, private keys,
    cookies; patterns like `sk-`, `Bearer `, `AKIA`, `-----BEGIN`)
- **If anything sensitive is found, do NOT push.** Stop, report exactly what was found and
  where, and let the user decide how to scrub it first. Never push "just this once."

## Think Before Coding

- **State assumptions explicitly.** If multiple interpretations exist, present them —
  don't pick silently. If something is unclear, stop and ask.
- **Surface tradeoffs.** Don't hide cost/benefit. If a simpler approach exists, say so.
  Push back when warranted.
- **No sycophancy.** Agreeing when I'm wrong wastes time. If you think I'm mistaken,
  say so with reasoning.
- **Don't manage your confusion by guessing.** Say "I haven't verified" rather than
  "should work".

## Plan Before Non-Trivial Code

- **For any task touching > 1 file or > ~30 lines:** state a brief plan first (steps +
  how each step is verified), wait for approval, then code.
- **For trivial changes** (typo, one-liner, obvious bug fix): just do it.

## Simplicity First

- **Minimum code that solves the problem.** No speculative features, no configurability
  I didn't ask for, no error handling for impossible scenarios, no abstractions for
  single-use code.
- **Three similar lines beat a premature abstraction.**
- **If you wrote 200 lines and it could be 50, rewrite before showing me.**

## Code Comments

- **Default: write no comments.** Code should self-explain through naming. If you feel
  the urge to comment, first try renaming or extracting a function.
- **When you do comment, explain WHY, never WHAT.** Non-obvious workarounds (link the
  cause), hidden invariants/ordering, race/thread/perf warnings, external spec
  references, genuinely complex algorithms.
- **Never write task-anchored comments** ("added for X", "as requested", "fixes #123",
  "AI-generated"). Those belong in commit messages / PR descriptions.
- **Audience is an engineer reading this in 12 months.**

## Surgical Changes

- **Don't make unnecessary changes.** Don't touch formatting, comments, imports, or
  unrelated code. Every changed line should trace to what was asked.
- **Don't refactor things that aren't broken.** Match existing style.
- **Clean up only your own mess.** Remove imports/variables YOUR changes orphaned.

## Engineering Rigor (CRITICAL — applies to ALL work)

- **NEVER use self-consistency as validation.** Always use independent ground truth. If
  validation uses the same formula as production code, it will pass even when both are wrong.
- **NEVER claim "no bug" or "passes" without tracing the actual code with concrete
  examples.** Specific inputs, specific values, step by step. Not "should work."
- **Before saying "I'm sure":** read the code, trace the execution, construct a failing
  scenario. If you haven't done this, say "I haven't verified."
- **Evidence-based debugging:** execution tracing, divergence detection. Never guess
  from stale memory.
- **The standard is high.** Not "good enough." Highest engineering rigor at all times.

## SEC 10-K Extractor — Design / Implementation / Verification Principles

Binding for all build work on this project; they encode what `ASSIGNMENT.md` rewards
(robustness under format variance, verification without ground truth, no silent failures,
cost discipline). Detail + sources live in `docs/` — run **`/10k-expert`** to load the
governing doc before building a stage; the capstone is `docs/10-pipeline-architecture.md`.

### Design
- **Index, don't generate.** Item extraction = indexing into source bytes (char ranges),
  never LLM free-text generation. Preserve byte offsets end-to-end (round-trip depends on it).
- **Layered ensemble, LLM last.** TOC+regex anchors (~95%) → independent CRF line-labeller
  → LLM "index-don't-generate" (LIB) **only** on flagged/low-confidence boundaries and novel
  items. The LLM never touches the common case.
- **The validation layer is the product, not the segmenter** — no existing tool emits
  confidence; that's the differentiator. Every item carries calibrated confidence + provenance.
- **Derive the expected-item template** from filing date + DEI tags before judging
  completeness (Item 1C FY2024+, Item 6 `[Reserved]` post-2021, SRC omissions, Part III
  incorporated-by-reference, 10-K/A scope).
- **Stable item IDs + cross-year boundary consistency are first-class** — boundary drift is a
  silent-failure mode.
- **Cost discipline by construction:** target ~$0.003–0.006/filing blended; cache by
  accession (filings are immutable); honour EDGAR 10 req/s + descriptive User-Agent.

### Implementation
- **Reuse vs build by license:** `edgartools` (MIT) for ingest/normalize; **reimplement** the
  CRF method (itemseg is NonCommercial, edgar-crawler GPL-3.0 — do not embed).
- **CRF features are structural** (`is-line-start`, `prior-item-seen`, `in-TOC`), not
  text-only; train on TOC-derived silver labels.
- **Constrain the escalation LLM** with grammar/structured decoding (XGrammar): emit only
  `{item_id ∈ closed set, line_ref ∈ doc range}` — deletes the bad-JSON / invented-item class.
  Feed a *window* (LumberChunker shape), never the whole filing.
- **Output contract:** `{part, item, title, text, char_range, confidence, signals[], status}`
  + a filing-level summary (AIS-style attribution = char_range + provenance).
- **Classify missing items** (`legitimately-absent` vs `extraction-failure`) — never silently
  drop one or coerce it into the canonical template.
- Handle the three format eras (SGML txt / HTML / iXBRL); scope vision/layout parsing out
  (EDGAR ships text+tags).

### Verification (there is no public filing-level ground truth)
- **Independent oracles ONLY.** Self-consistency is not validation; a model judging its own
  output cannot catch *confident systematic* errors. Oracles/gold labels must be independent
  of the production code and the silver toolkit's lineage.
- **Validation stack (cheap→expensive):** structural invariants → round-trip byte-
  reconstruction (proves *coverage*, not labelling) → independent dual-extractor agreement →
  XBRL Item-8 + DEI oracle → content heuristics.
- **LLM judge = non-gating, last-resort flag only** (JudgeBench: ≈random on objective
  correctness; panels don't fix correlated error). Never feed the generator's rationale to
  the judge.
- **Calibrated confidence with a statistical guarantee:** conformal prediction, stratified
  per era (Mondrian); prediction-set size is the abstention/escalation trigger.
- **Eval harness = Inspect AI `Task = Dataset + Solver + Scorer`**, four independent scorers
  (structural + round-trip on 100%, XBRL Item-8, gold boundary-F1 on 150). Grade the output
  state, not the path.
- **Report honestly:** every rate as `value(SE)` with **filing-clustered** CIs;
  **Abstention-Recall** is the headline silent-failure metric; **pass^k** for the
  nondeterministic escalation; cost/accuracy on one Pareto table; enforce a `run_manifest`.
  150 gold ⇒ ±3–5% aggregate F1 but wide bars on rare strata (1C/7A) — state it, never over-claim.
- **Validate-the-validator:** inject perturbations (delete/reorder/truncate an item) into
  known-good filings and assert each check fires; a check that never fails is worthless.

## Commit Messages

- Commit history should reflect the actual development process (the test asks for this).
- Write clear, English commit messages explaining WHY.
- **NEVER** include `Co-Authored-By` lines or any AI attribution in commits.

## Language

- Converse with me in Traditional Chinese by default; keep technical terms, commands,
  code, error messages, and library/framework names in English.
- Keep all repository artifacts — code, comments, commit messages, README, docs — in
  English (this is a public repo for external reviewers).
