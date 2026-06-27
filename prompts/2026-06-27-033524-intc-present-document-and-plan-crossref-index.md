# INTC Items Are Present: Document The Index-Table Class + Plan To Handle It

- **Datetime:** 2026-06-27 03:35:24
- **Summary:** After inspecting the INTC filing, the user ruled its items PRESENT (the cross-reference index counts), agreed to pin-RED but disagreed that ~1% is too small to handle — asking to document the class in ANALYSIS.md first and author a plan to handle it later, and to show what they need to audit for the GIS char-gold.

## Prompt

> agree with the plan for INTC, but we need it in ANALYSIS.md first, and looking into INTC filing this is definitely present for me. and we need a plan to handle it after. i don't think 1% is too small. and show me what need me to audit for GIS /save-prompt

## What I Did

- **Resolved INTC to PRESENT** (human ruling): updated the `intc-fy2018` RED anchor in `eval_set.json` from "ambiguous present-vs-absent" to "human-audited PRESENT → a real extraction miss, not legitimate absence; pinned-RED + future-handle target."
- **Documented the class in ANALYSIS.md** (new FM-4): named the cross-reference-INDEX-TABLE class with the round-3 sweep prevalence (~15–19 / 1,656 ≈ 1%, concentrated in GE ×7 / MCD ×4 / HON ×4 / INTC — filer house-style, not negligible), human-audited present, flagged-not-silent.
- **Authored the handling plan** (`research/todo-exploration-crossref-index-handling.md`) for a future round. Before writing it I verified feasibility and found the naive "index page → char offset" approach is DEAD — `to_canonical` strips all page markers (`<PAGE>`=0, form-feed=0, no "Page N"). Honest plan: viable paths are (B) title-matching (index item→title matched to body title-only headings — needs a body-heading check first) or (D) the decorrelated CRF/structural extractor (the named-ceiling answer, which subsumes this class); (C) preserving page markers in normalize works but is invasive. Gated like round-4 on independent signals.
- Committed the three updates (f7a6b0a); REPORTED-only, no extractor code changed, nothing pushed.
- Presented the GIS FY2018 char-gold (`0001193125-18-209377`) audit checklist for the user to verify + freeze (replacing OXY per the earlier decision): offsets 1=[7807,30002], 1A=[30002,59621], 7=[71799,214293], 8=[217595,450889], with the one convention call (Item 7 ends at 7A, the apple convention) and the CP-1252 \x92 caveat.
- Saved this prompt.
