# Record The Human Audit Of The Boundary Gold (JSON + Provenance Wording)

- **Datetime:** 2026-06-24 17:39:32 (Asia/Taipei, UTC+8)
- **Summary:** After eyeballing the snippets, the human confirmed all 12 spans of the 3 'regex-verified' boundary-gold filings (apple/ko/msft) are genuine section bodies (not TOC / cross-reference lines). Record that audit: a small JSON + doc-wording change, no code logic.

## Prompt

> i have verified them. all good. record it, small json + doc change, no code logic:
> - in eval/boundary_gold.json, for those 3 filings change `source` from "regex-verified" to "regex-verified, human-audited" and add an `"audited": "<today>"` field. do NOT touch m2i (already title-labelled-independent).
> - if run_eval.py / report.md / any doc currently describes the gold as frozen-from-regex / unaudited / "regression-anchor only", update that wording to note these 3 are now human-audited (only m2i was already independent).
> - then commit with a clear message like "gold: mark apple/ko/msft boundary gold human-audited (snippet audit)" /save-prompt

## What I Did

- `eval/boundary_gold.json`: for apple-fy2024, ko-fy2023, msft-fy2023 changed `source` -> `"regex-verified, human-audited"` and added `"audited": "2026-06-24"`. **m2i left untouched** (`title-labelled-independent`, no audited field) -- confirmed it is absent from the diff.
- Updated the frozen-from-regex / "INDEPENDENT" provenance wording in four places (docstrings + report text only, no logic):
  - `eval/build_boundary_gold.py` docstring: note the committed easy-filing spans are now human-audited (trusted truth, not just a regression anchor); re-running regenerates UN-audited spans.
  - `sec10k/evalkit.py` `boundary_scores` docstring: was over-claiming the gold is "independent of both the regex and edgartools" -- corrected to "easy-filing spans are regex-derived but human-audited; m2i is method-independent."
  - `eval/run_eval.py` `_render_md` report text + `eval/report.md` header: "INDEPENDENT gold" -> "audited gold", with the apple/ko/msft regex-derived+human-audited vs m2i method-independent breakdown. Report numbers unchanged (no eval re-run needed; only the descriptive header).
- Verified: gold JSON valid, all 4 entries print expected source/audited, **full suite 58 passed**, m2i not in the diff. Committed `31990de` "gold: mark apple/ko/msft boundary gold human-audited (snippet audit)". Did NOT push.

## Note
This closes the circularity flagged in the prior turn: the 3 regex-verified filings are now trusted truth (human-audited), not just regression anchors. The snippet-audit script remains at `scratch/audit_boundary_gold.py` for re-running if the gold is ever rebuilt.
