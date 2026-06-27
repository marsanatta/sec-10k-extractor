# Author Round-4 Plan (Fix Tractable Clusters + Promote Failures To Independent Rulers)

- **Datetime:** 2026-06-27 00:54:34
- **Summary:** After teaching the round-3 findings step-by-step (qna mode), the user confirmed Steps A (fix one tractable cluster at a time, starting with `empty`), B (promote the failure cases to RED regression anchors + 1-2 char-gold), and C (record the `to_canonical` super-linear scalability finding), each tied to an ASSIGNMENT.md criterion, and asked me to author the plan for them and save the prompt.

## Prompt

> Step A — 一次修一個 tractable fix(從最大的 empty cluster 開始)。
> 為什麼:這直接提升 robustness under format variance(ASSIGNMENT 第一條)。而且一次只動一個 + 用獨立 signal 量 RED→GREEN,避免「改 A 弄壞 B」。
>
> Step B — 把這些失敗 case 升級成 RED regression anchor(+ 1-2 份 char-gold)。
> 為什麼:這是 verify-without-ground-truth + no-silent-failure(ASSIGNMENT 第二、三條)。失敗被 pin 住後,以後任何改動都會被量;而且獨立人工標的 gold 能擋住「靠放寬規則假裝變好」。
>
> Step C — 記錄 to_canonical 在巨大 filing 上變慢這件事。
> 為什麼:這是 scalability / performance 分析(ASSIGNMENT 要的具體 perf 數據)。我們已經在 sweep 上實際撞到它(16 份巨型 filing 超時),這是真實證據,不是猜的 then do plan for this /save-prompt

## What I Did

- Authored `research/round-4-plan.md` in the round-3 worktree (`round3/sweep-1000` branch) — plan-only review document, no code, nothing pushed, mirroring the rounds-1/2/3 plan discipline.
- **Key design decision surfaced and applied: invert the order to B → A → C.** Reasoned (and got the user's Checkpoint answer confirming it) that Step B must precede Step A — without independent ground truth (RED anchors + char-gold + needs_review guards), a fix could only be "verified" against production output, which is self-consistency and forbidden. B is the measuring instrument; build it before cutting.
- Plan contents: the B→A→C sequencing rationale; the independent KEEP signals (A structural-pass UPPER-BOUND / B char-gold / C new modes / D classification + the new RED `expect_red` anchors); Step B sub-steps (B1 eval_set RED anchors, B2 char-gold 1-2 with a HUMAN audit checkpoint, B3 needs_review silent-failure guards, B4 synthetic mutation tests injecting separator-less headers / in-prose cross-refs into clean fixtures, B5 routing the ingest + COST-false-fail cases to ingest/harness unit tests); Step A fixes one-probe-per-iteration in ROI order (A1 separator-less header recogniser, A2 cross-ref-intruder run-selection hardening, A3 ingest robustness) each gated RED→GREEN on independent anchors + clean char-gold-unchanged; Step C the perf/scalability note.
- Added an ASSIGNMENT.md alignment table (each step → the criterion it serves) and a new guard G8 (RED-anchor integrity: expected values are human-labelled from the filing, NEVER frozen from production output; RED anchors safe only alongside the existing GREEN clean gold).
- Did NOT execute any fix, did NOT touch extractor code or gold files (deliverable = the plan). Nothing committed yet at save time; nothing pushed.
