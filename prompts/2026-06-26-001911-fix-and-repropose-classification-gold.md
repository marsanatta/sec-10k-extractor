# Fix And Re-Propose The Signal-D Classification Gold (Heading-Exists; Drop Incorporated)

- **Datetime:** 2026-06-26 00:19:11
- **Summary:** Auditor caught two errors in the proposed classification reference; fix the presence rule (heading-exists, not content-substance) and drop the incorporated-by-reference category, then re-propose reconciled against real production output — still PROPOSED, not frozen.

## Prompt

> before i audit the classification_gold, i caught two problems in the proposed labels — fix them and RE-PROPOSE so my audit is a quick confirmation, not a rewrite. stay in the round-2 worktree, do NOT freeze anything, do NOT touch the segmenter / char-gold / other code.
>
> problem 1 — the presence definition is wrong. you labelled headed "None." / "Not applicable" sections as legitimately-absent. that's wrong. the correct, objective test is HEADING-EXISTS, not content-substance:
> - present = the "Item X" heading physically exists in the filing body, regardless of content — substantive text, OR "None." / "Not applicable", OR even "incorporated by reference to the proxy". the registrant addressed the item in place; the section is there.
> - legitimately-absent = there is NO "Item X" heading in the filing at all (genuinely omitted, and template-allowed: optional / N/A / not-yet-effective).
> so a headed "None." section is PRESENT. "None" is an answer, not a missing section.
>
> problem 2 — the incorporated-by-reference category is a taxonomy mismatch with production and creates false Signal D mismatches. production Status has only 3 values (present / legitimately_absent / extraction_failure) — there is NO incorporated status. a Part III item like "Item 10. … incorporated by reference to the Proxy" HAS a heading, so the segmenter finds it and production calls it PRESENT. but your gold labels it incorporated-by-reference, and _GOLD_CAT maps that to "ok-absent" — so Signal D would report present-vs-ok-absent as a MISMATCH that isn't a real classification error. fix: DROP "incorporated-by-reference" as a gold category. fold it into the 2-truth-category scheme: an item whose heading exists in the filing (incl. "see proxy" sections the segmenter finds) = present; an item with no heading at all = legitimately-absent. update _GOLD_CAT accordingly (remove the incorporated key) and the gold schema/notes.
>
> then RE-PROPOSE eval/classification_gold.json under these two corrected rules — and reconcile each label against what production actually outputs (run the pipeline on the filings; if production says PRESENT for a headed item, the gold says present too — that's a match, not a bug). keep the file _audit_status = PROPOSED (NOT frozen — still my human audit), keep the mutation refutation control (3a) firing, keep G7. confirm the offline suite stays green and network-free. show me the re-proposed labels per filing (present / legitimately-absent only) + which cells changed from the first proposal + that 3a still fires /save-prompt

## What I Did

- Stayed in the round-2 worktree (`_wt/ar2-10k`, branch `autoresearch/round-2`); touched only
  `sec10k/evalkit.py` (the Signal-D scorer) + `eval/classification_gold.json` + `research/`. Did
  NOT touch the segmenter, char-gold, or any other code; did NOT freeze anything.
- **Fixed `_GOLD_CAT`**: removed the `incorporated-by-reference` key -> two categories only
  (`present`, `legitimately-absent`); updated the scorer comment/docstring to state the objective
  heading-exists rule.
- **Ran the pipeline on the 5 filings** and dumped per-item production status + `Item X` header-
  occurrence counts, then **re-proposed the gold reconciled against that measured output** under
  heading-exists: headed item (occ>=1 / production present) = present; no heading (occ=0) =
  legitimately-absent. Cells changed from proposal-1 are all on the full-10-K controls (apple,
  msft-2023, msft-1996 relabelled — None./N/A/see-proxy sections -> present, Part III -> present);
  the two amendments were already correct and are unchanged.
- The gold reflects TRUTH, so it independently **catches real production errors**: msft-2023 `1C`
  (pre-effective-date, no heading, but production flags extraction_failure) and msft-1996
  `7A/9A/15` (pre-2001 era items production wrongly expects) -> Signal D mismatches that are NOT a
  copy of production (evidence it is a ruler).
- **Measured Signal D vs the re-proposed gold** (from measured statuses, no re-fetch): apple 23/23,
  msft-2023 22/23, msft-1996 20/23 (full-10-K controls), chemed-amend 13/23, scwo-amend 12/23
  (amendments, low due to form-blind failures). The form-aware fix (probe #2, post-freeze) would
  lift the amendments to 23/23 while the controls stay fixed.
- **Control 3a still fires**; offline suite **72 green, network-free**. `_audit_status` stays
  **PROPOSED** (not frozen); G7 intact; nothing gated on unaudited labels. Committed the re-propose
  on the branch (`a778f7a`); NOT pushed, NOT merged. Saved this prompt (Taipei time).
