# Prototype The Boundary Cross-Check, Fault Battery, And A Go/No-Go Call

- **Datetime:** 2026-06-23 08:13:18
- **Summary:** User asked me to actually build the smallest edgartools-vs-mine boundary cross-check, prove it flips needs_review to True on Fault A, run a fault battery (swallow / merge / swap), report recall + false alarms (given edgartools' own bugs), then give a real call on whether the infra is sound enough to grow the eval set or whether the boundary check must come first.

## Prompt

> this is exactly what i wanted, you actually ran it and fault A is the smoking gun, item1A eats 200 chars of item1 and the whole system says clean, high confidence, identical to baseline. so we agree the infra is boundary blind right now and we can't grow the eval set on top of that, more filings just means more green that can't fail.
>
> the thing you proposed at the end, using edgartools .obj() as the independent second extractor to catch boundary drift, i like the idea but i'm not convinced yet, because in experiment 1 you also showed you can't even line up edgartools items to your offsets, find() came back -1 for all 23, and its parser is buggy here with the duplicate item 8 and the jumbled order. so before we believe it's the fix, build the smallest version of that cross check and point it straight at fault A. like compare your item1 span text against edgartools item1 text, if your span lost 200 chars to item1A the text won't line up anymore. run it and show me needs_review finally flips to true on fault A, the exact case that fooled everything before. i want to see the fix catch the real fault, not just the plan.
>
> if that one works, widen it a little, make a small battery, the +200 swallow, merging two items, swapping two labels, and tell me honest how many it catches and how many still slip. one more thing that worries me, the oracle itself is buggy here, edgartools gave you a duplicate item 8 and jumbled order, so how do you stop the oracle's own mistakes from firing false alarms on a perfectly good filing. once you can show me the battery recall number and that false alarm story, then give me your real call, is the infra sound enough to start adding filings or do we build this boundary check first. /save-prompt

## What I Did

- Built `scratch/exp3_boundary_crosscheck.py` (throwaway; no production code changed): for each item both extractors find, compare my span text vs edgartools' item text at head+tail (difflib ratio), with normalization for nbsp/curly-quote/whitespace differences. Ran on baseline + a 3-fault battery.
- **Fault A caught (the smoking gun):** the cross-check flagged `1:tail` + `1A:head` and flipped `needs_review` to True on the exact case the old infra reported as clean/high-confidence. Verified live.
- **Iterated honestly on false alarms (3 runs):** (1) naive length-mismatch rule false-alarmed on stubs → removed it; (2) head/tail still false-alarmed on short "Not applicable"/Part-III items (their tails legitimately differ between the two tools on a correct filing) → added "abstain on small items (min both lengths < 1500)". Final: **baseline = 0 false alarms** (abstained on ~12-13 of 23), **Fault A caught**, battery **combined 3/3** (old 2/3; cross-check's unique win = Fault A).
- **False-alarm story:** edgartools' duplicate Item 8 / jumbled order did NOT cause false alarms — neutralized by looking up text BY KEY (not position) + one text per key + abstain on no/short text. The real false alarms were genuine short-item boundary differences, fixed by abstaining on small items.
- **Honest limits stated:** covers boundary drift on substantial items only; abstains (blind) on small/stub/Part-III + 3 unparseable items; common-mode (both tools wrong the same way) untested.
- **Real call given:** BUILD THE BOUNDARY CHECK FIRST — infra not sound to grow the eval set yet (Exp 2 proved boundary blindness; Exp 3 proved a cheap cross-check fixes the proven blind spot with 0 false alarms). Sequence: productionize+review the cross-check into needs_review with the fault battery as its validate-the-validator test → then grow the eval set → char-exact gold as the rigorous follow-on for the small-item gap.
- Every claim tagged TRACED (ran it) vs ASSUMED (e.g., common-mode limit).
