# Productionize The Boundary Cross-Check, Measure Common-Mode, Give The Gate Verdict

- **Datetime:** 2026-06-23 08:47:16
- **Summary:** Last gate before pointing autoresearch at the repo: productionize the boundary cross-check into sec10k wired into needs_review, promote the fault battery into a real (fail-able) validate-the-validator test, settle the untested common-mode with a measured number, then give one un-softened call on whether the infra is sound enough for autoresearch to grow the eval set and catch regressions or whether a concrete blocker remains.

## Prompt

> let's converge, this is the last gate before i point autoresearch at this repo to grow and refine the eval set, so build the real thing and prove it's sound, no more scratch.
>
> productionize the cross check into sec10k wired into needs_review, and promote the fault battery into a real validate-the-validator test, because that test is exactly what autoresearch will hill climb against later so it has to be able to fail.
>
> before you tell me it's sound, settle the one thing you marked untested, the common mode, that's the whole ballgame. your own CLAUDE.md says independent oracles only, self consistency can't catch confident systematic errors, so a cross check where the two methods secretly fail the same way is not a real gate. construct a boundary fault that your regex and edgartools would both get wrong the same way, and measure how often their boundaries already agree on the big items. if they share a blind spot the check goes silent exactly where it matters and i need that number before i trust it.
>
> then one straight answer, with the cross check wired, common mode measured, and the small item abstain gap you already flagged, is the infrastructure sound enough that i can point autoresearch at it to grow the eval set and have it actually catch regressions, or is there one concrete blocker left. don't soften it, if it's a partial gate say partial and name the exact thing still blind. /save-prompt

## What I Did

- Productionized `sec10k/boundary_crosscheck.py` (head/tail text agreement vs edgartools' item parse as a 2nd extractor; looked up BY KEY so its duplicate/jumbled-order bugs can't false-alarm; abstain on small items). Wired into `validate.assess` (per-item disagreement -> downgrade + `needs_review`) and `pipeline` (edgartools second-extractor on the live path). Commit 4099042; 37 tests pass.
- Promoted the fault battery into `tests/test_boundary_crosscheck.py` (swallow/merge/swap/abstain + an assess-integration assertion) — a real validate-the-validator that fails if the cross-check stops detecting the faults.
- **Measured the common-mode (the ballgame):** agreement on big items across the eval set = **30/31 = 96.8%** (high agreement = low false alarm BUT high correlation). Both methods are header-anchored. Direct simulation: independent 2nd extractor catches Fault A (`['1','1A']`); a 2nd extractor that SHARES the wrong cut -> no disagreement -> SILENT. Coverage collapses on hard filings: cross-check was active on only 3/7 (GE/M2i/MSFT1995/Chemed did 0 boundary checks). Wiring pushed needs_review to 6/7 -> silent-failure metric now effectively N=1 (only Apple unflagged).
- **Verdict (un-softened): PARTIAL gate.** Sound for presence/structural/coverage/Item-8-oracle regressions and boundary regressions on clean big-item filings. NOT sound for boundary-accuracy regressions on hard/header-pathological filings -- the named blocker: the 2nd extractor is NOT decorrelated (both header-anchored, 96.8% correlated -> shared header-error blind spot) AND abstains on the hard filings. Minimal unblock: a decorrelated 2nd extractor (CRF / non-header) OR a small char-exact gold set. Warned: do NOT let autoresearch's reward be "reduce needs_review."
- Every number TRACED (ran it live); scratch measurement in `scratch/exp4_commonmode.py` (untracked).
