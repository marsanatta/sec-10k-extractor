# Build And Gate-Test The 10k-expert Docs Index Skill

- **Datetime:** 2026-06-22 18:01:21
- **Summary:** Model the /brain skill to build a `10k-expert` index skill over docs/, replace REFERENCES.md with a routing INDEX.md, then validate it with an agent-teams gate loop (assign questions → agents route via the skill → refine until pass).

## Prompt

> read /brain skill and create a similar skill with /skill-writer to create a index structure for the docs folder called 10k-expert. create this skill under .claude/skills in this repo. after you finish spawn /agent-teams you assign each a question and they try this skill. to test if they can correctly find the corresponding reference. this will replace the original references.md this is loop gate process, you assign question, they use skill to find it and give feedback, you refine the index, until pass the gate. /save-prompt

## What I Did

- Read the `/brain` skill (`SKILL.md` + `refs/query.md`) to model its L0/L1/L2 layered-index + query-navigation pattern.
- Authored `.claude/skills/10k-expert/SKILL.md` (skill-writer format): a query engine that resolves the repo git root, reads `docs/INDEX.md`, and routes a question L0 (category) → L1 (doc) → L2 (read). Includes an explicit maintenance/rebuild step and a routing-quality criterion.
- Built `docs/INDEX.md` — the routing index: L0 category map (domain / design / evaluation / tooling / research / meta), a "Question → doc" quick-lookup table, and per-doc L1 entries (Read-when triggers, Keywords, sample questions, key facts). **Deleted `docs/REFERENCES.md`** (replaced).
- Decision flagged: kept docs **flat**, with the index providing categorization virtually (avoids breaking in-doc path refs); physical subfolders offered as optional follow-up.
- Ran the gate as an **agent-teams fan-out**: 10 agents, each blind to the others and to the expected answer, each routing one question using only the index, reporting CHOSEN_DOC + INDEX_CUE + CONFIDENCE + FRICTION.
- **Result: 10/10 correct, all high confidence** — gate passed on round 1.
- Hardened the index from FRICTION feedback even though it passed: added `ingestion` keyword to `01`; added explicit `03`↔`06`↔`13` disambiguation notes; recorded the gate-validation note in `INDEX.md`.
- Nothing committed/pushed (per repo push policy).
