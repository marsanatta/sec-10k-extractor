# Recommend, Don't Survey — Build Char-Gold + Boundary-F1 First, Then Hand Off

- **Datetime:** 2026-06-23 10:32:16
- **Summary:** Made the decision (recommend, not survey): build the char-exact boundary gold + a boundary-F1 scorer FIRST — the decorrelated signal independent of both regex and edgartools — to close the eval-blindness and the dual-extractor common-mode before pointing autoresearch at the eval. Correctly read the 96.8% cross-extractor agreement as high correlation (a shared blind spot), not reassurance.

## Prompt

> if i do not ask you to save-prompt you must not do it remember this. You have a real decision here, so let me recommend rather than survey. Build char-gold + boundary_f1 first (the agent's path A), then hand off. Reason: pointing autoresearch at a knowingly-boundary-blind eval and saying "grow it" is the green-wall risk the whole thread was about — it'd optimize presence while boundaries rot. Char-gold is independent of both regex and edgartools, so it closes the common-mode and the eval-blindness in one bounded build, and it's the design's own deferred scorer #4 — the reviewer sees the team complete their designed verification. (Path B — hand off now scoped to presence/coverage with boundaries explicitly out of scope — is valid if you want to start sooner, but it's the weaker story.)
>
> good, the common mode number is exactly what i needed, 96.8% agreement is high correlation not reassurance, and you read it right, two header anchored methods fail together so the cross check is a partial gate, real on clean big items, blind on the hard ones. and you were straight that the eval still can't measure a boundary on a real filing. i agree with your call, build the decorrelated signal first.
>
> so build the char exact boundary gold, even just 8 to 10 filings, hand label the start and end of the big items, and add a boundary_f1 scorer to run_eval so a wrong boundary finally shows up as a number not just a needs_review flag. this is the scorer #4 you already planned, and it's independent of both regex and edgartools so it closes the common mode too. [message continues with the build spec: prove it on a header-error case where edgartools couldn't, put a hard filing or two in the gold to cover where the cross-check abstains, and once boundary_f1 is in run_eval and proven on a fault, that's the handoff gate for the boundary dimension.]

## What I Did

- Took the decision as given (path A): built the char-exact boundary gold (`eval/boundary_gold.json`, human-audited) and the IoU/boundary scorer (`evalkit.boundary_scores`, wired into `run_eval`) — the design's deferred scorer #4.
- The gold is independent of both the regex and edgartools, so it turns a wrong boundary into a *number* (IoU < 0.9) instead of only a `needs_review` flag, closing both the eval-blindness and the dual-extractor common-mode (the 96.8%-agreement shared blind spot).
- This became the handoff gate for the boundary dimension: only after boundary scoring existed did the autoresearch loop get pointed at the eval — so it could not green-wall presence while boundaries rotted. The gold later grew (5 → 8) on hard strata, never auto-frozen.
