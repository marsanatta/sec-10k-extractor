# The Eval Is Presence-Blind — What Will Autoresearch Actually Hill-Climb Against?

- **Datetime:** 2026-06-23 09:08:14
- **Summary:** Caught from reading the code that run_eval still scores silent-failure on presence only (not boundaries), and asked the load-bearing question before handing off: what does autoresearch actually optimize against, and does adding more filings buy any boundary coverage — or just more needs_review flags with no gold to check against?

## Prompt

> reading the code i noticed something you didn't call out. the cross check feeds needs_review and the battery test proves the logic, but the eval itself, run_eval, still scores silent_failure on presence only, recall over expected_present, and report.md still says boundary drift not measured here. so the eval on real filings still can't see a wrong boundary, only production needs_review and the synthetic battery can. so be straight with me, when i point autoresearch at this to grow and refine, what exactly does it hill climb against, the pytest battery that can actually fail, or run_eval which is still presence blind. and if i add 30 more filings to eval_set, does that add any boundary coverage at all, or do those filings just get a needs_review flag with no boundary gold to check against. tell me the real verify signal before we hand off, because growing a presence only eval is the green wall problem again

## What I Did

- Confirmed from the code (not memory): `run_eval`'s silent-failure metric is presence-only (recall over `expected_present`); boundary drift was explicitly *not* measured on real filings — only production `needs_review` and the synthetic mutation battery could catch a wrong boundary.
- Gave the straight answer: pointing autoresearch at a presence-only eval would let it hill-climb presence while boundaries silently rot — the "green-wall" Goodhart risk. Adding 30 more filings would add presence/coverage breadth but **zero** boundary coverage, because there was no char-exact gold for them to be checked against.
- Concluded the handoff was not safe yet: the eval needed an independent boundary signal first. This directly set up the next decision — build char-exact boundary gold + a boundary-F1/IoU scorer (the design's deferred scorer #4) before any autoresearch loop.
