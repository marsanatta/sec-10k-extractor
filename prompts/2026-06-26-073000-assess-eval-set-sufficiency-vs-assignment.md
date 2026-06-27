# Assess Whether The Eval Set Fulfils ASSIGNMENT.md (And The "~1000 Cases" Question)

- **Datetime:** 2026-06-26 07:30:00
- **Summary:** Critically assess, with code/report evidence, whether the 21-filing eval set meets the assignment bar or needs more cases — and address the user's intuition of a ~1000-case eval set.

## Prompt

> do you think according to the assignment.md our eval set fullfil the requirement? or still need to test more cases from your current status. read the report and code with evidience /save-prompt
>
> my imagination is something like over thousand eval set of something

## What I Did

- Applied the `vici-10k-reviewer` discipline (verify from code, trace both sides, no sycophancy,
  state what I did not check). Gathered evidence directly from the committed repo (no live grader
  test possible):
  - **Era distribution** (`eval/eval_set.json` fiscal years): pre-2001 SGML 3, 2001-2008 HTML 1,
    2009-2012 HTML 2, **2013-2018 = 0 (gap)**, 2019-2025 modern iXBRL 15 (71%). Real era hole at
    2013-2018; 2001-2012 thin.
  - **Gold floors:** char-exact `boundary_gold` = 5, `classification_gold` (Signal D) = 5.
  - **No committed structural-sweep harness** (`ls eval/*sweep*` -> none); ANALYSIS §8 cites a
    ~130-filing sweep (~97% structural-pass) that ran in a SEPARATE worktree -> **not reproducible
    from this repo**; the committed population signal is the §2.5 12-filing batch (~78%).
- **Verdict:** fulfils the assignment's letter with A-level DESIGN depth (12 structure pathologies,
  independent-oracle verification incl. a live-disagreeing Signal D, 6 honest REDs, silent-failure
  0), but B-level POPULATION BREADTH for generalising to held-out filings (era gap + thin char-gold
  accuracy floor + no reproducible large-scale number).
- **On "~1000 cases":** framed three eval tiers at three scales — (1) char-exact human gold
  (accuracy floor) CANNOT scale to 1000 by hand, keep small (grow 5->~15-20); (2) hand-labelled
  curated set ~50-150 ceiling; (3) **label-free structural sweep is where ~500-1000 belongs and is
  feasible** (no human labels) -> a reproducible population UPPER-BOUND robustness number + gross
  failure-tail map. Stressed the rubric caveat: a 1000-case sweep is an UPPER BOUND on robustness,
  NOT accuracy.
- **Prioritised recommendation:** (1) build + commit a label-free structural sweep over ~500-1000
  stratified EDGAR filings (the user's "1000", done right); (2) fill the 2013-2018 era gap + thicken
  2001-2012; (3) grow char-gold 5 -> ~15-20 on hard strata (not 1000). Stated explicitly what I did
  NOT verify (no live held-out test, did not re-run the external sweep, did not re-audit the frozen
  gold labels). No code changed; nothing pushed.
