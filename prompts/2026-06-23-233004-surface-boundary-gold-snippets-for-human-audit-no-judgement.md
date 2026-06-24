# Surface Boundary-Gold Snippets For Human Audit (No Self-Judgement)

- **Datetime:** 2026-06-23 23:30:04 (Asia/Taipei, UTC+8)
- **Summary:** The 3 'regex-verified' boundary-gold filings (apple-fy2024, ko-fy2023, msft-fy2023) were frozen FROM the regex output, so grading the regex against them is circular. The human needs to confirm the regex was actually right before they count as trusted truth. Surface the raw evidence only -- print the canonical-text snippets at each gold offset so the human can eyeball whether each start is a genuine section body vs a TOC line or cross-reference index (the GE-style trap). Do NOT judge correctness (that would re-introduce the circularity).

## Prompt

> i need to audit the boundary gold, specifically the 3 filings marked source 'regex-verified' (apple-fy2024, ko-fy2023, msft-fy2023). the reason: those gold spans were frozen from the regex output, so using them to grade the regex is circular -- the gold agrees with the extractor only because it came from the extractor. a human (me) has to confirm the regex was actually right on those 3 before they count as trusted truth instead of just a regression anchor. the specific thing this catches is a GE-style trap: regex matching an 'Item N' inside a table-of-contents or a cross-reference index instead of the real section body.
> so DO NOT judge correctness yourself ... just SURFACE the evidence for me to eyeball. for each ... and for each gold item in eval/boundary_gold.json: fetch the filing's canonical text the same way the gold-builder does (eval/build_boundary_gold.py); print: the item key, its [start,end] offsets, ~200 chars of canonical text starting AT the start offset, and ~80 chars ending AT the end offset; lay it out as a clean table per filing ... do NOT [conclude] -- just give me the snippets to read. ... when done, just present the tables and stop. /save-prompt

## What I Did

- Wrote `scratch/audit_boundary_gold.py` (untracked, re-runnable). It reads `eval/boundary_gold.json` and, for the 3 regex-verified filings, fetches the SAME way `eval/build_boundary_gold.py` does -- `to_canonical(fetch_10k(...))` with the identical refs (apple by accession `0000320193-24-000123`; ko by `(KO, 2023)`; msft by `(MSFT, 2023)`). For each gold item it prints the key, `[start, end]` offsets, `repr(canon[start:start+200])`, and `repr(canon[max(0,end-80):end])`.
- Ran it (live SEC fetch). All three re-fetched to the SAME accession stored in the gold (`same_filing=True` for apple/ko/msft), so the offsets index into the exact canonical text the gold was frozen from -- the snippets are valid evidence, not a different filing.
- Hit a Windows cp1252 console crash on the last snippet (curly-quote / box char); re-ran with `PYTHONIOENCODING=utf-8` to capture all 12 cleanly.
- Presented 3 per-filing tables (Item / offsets / START +200 / END -80) and stopped. **Made no correctness judgement** -- per the request, the human reads the start snippets to decide genuine-body vs TOC/cross-ref; I did not classify any span as right or wrong.

## Note
This is the human-in-the-loop step that converts the 3 regex-verified gold filings from "regression anchors" into "trusted truth" (or flags any as circular/wrong). Whatever the human concludes feeds back into `eval/boundary_gold.json` provenance. No repo files were changed by this task.
