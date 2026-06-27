# Evaluate Scaling The Sweep To 1000 + /eng-debug Each Miss + Improvement Plan

- **Datetime:** 2026-06-26 13:35:31
- **Summary:** User proposed growing the label-free structural sweep to ~1000 filings, tracking the misses during the run, running /eng-debug on each missed filing to learn why it failed, then producing another improvement plan — and asked me to evaluate the idea honestly (with permission to deny it on strong ASSIGNMENT.md grounds).

## Prompt

> i want sweep items to increase to 1000, then and during the sweep to track the miss ones, then with those miss set to /eng-debug each why it miss then based on that to come up with the improvement plan again. evaluate this idea, you can deny if you have strong justification that this don't fit the assignement.md /save-prompt

## What I Did

- Evaluated the idea against ASSIGNMENT.md instead of agreeing reflexively (the user invited a denial).
- **Verdict: accept, do not deny.** It maps directly onto a literal Task-2 requirement ("clearly list filings/companies that are still difficult, unreliable, or unsupported, with concrete failure cases") and onto Level-A rewards (failure modes honestly surfaced, edge-case handling, scalability analysis). No strong basis to reject.
- Raised **one necessary structural correction**: do NOT run /eng-debug per missed filing. ~1000 filings → ~110 misses; /eng-debug is a heavyweight 5-phase root-cause skill, so per-filing is over-scoped and wasteful. The misses already cluster by the reason the sweep tags (`empty` / `coverage:0.01` / `lead_item_1_missing` / `header:N` / `TIMEOUT`). Correct move = cluster by reason → confirm + count the already-root-caused classes (cross-ref=GE, common-mode=MS/Citi, no-separator=HON, PART-glued=WMT, collapsed=AMT) at scale, and /eng-debug only ONE representative of each UNEXPLAINED cluster (esp. the OXY/USB/GIS `empty` batch — either the named common-mode ceiling or a tractable styled-iXBRL normalization gap). Net: ~2–3 genuinely-new debug sessions, not ~110.
- Raised **one honesty framing**: this is effectively autoresearch round 3 (failure-mode discovery + ranked improvement plan). Expect a mix of (a) re-confirming the known classes / the named ceiling (a valid negative result = "tail is bounded") and (b) possibly 1–2 new tractable fixes. Any fix still goes through the same anti-Goodhart Modify→Verify→Keep/Discard discipline (independent signal only).
- Stated the honest cost (1000 sweep ~30 min, clustering free, ~2–3 eng-debug, write-up) and noted 1000-vs-471 barely moves the headline number (~88–89%); its real value is a richer failure census + tighter rare-stratum coverage.
- Recommended delivering it as a round-3 plan **review doc** first (same format as rounds 1–2), execution of any fix deferred to a later approved step. Asked whether to author that doc.
- Did NOT touch code, did NOT run the sweep, committed nothing, pushed nothing (standing constraints).
