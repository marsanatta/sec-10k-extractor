---
name: 10k-expert
description: "Find the authoritative project doc for any question about this SEC 10-K item-extraction system. Routes a question to the right file under docs/ via a layered index. Use when you need to ground a decision in the project's research, locate which doc covers a topic (EDGAR access, format variance, segmentation, confidence/eval, cost, tooling, papers), or answer 'where is X documented'."
argument-hint: "<question about the 10-K extractor project>"
---

# 10k-expert

The query engine over this repo's `docs/`. Given a question about the SEC 10-K
item-extraction project, navigate the index and return the authoritative doc(s) + a
grounded answer. This replaces a flat reference list: the index routes *questions* to
*docs*, and each doc carries its own citations (L2).

Mirrors the `/brain` L0→L1→L2 pattern: **L0** = the category map, **L1** = per-doc routing
entries (in `docs/INDEX.md`), **L2** = the full docs.

## When to Use

- "Where is X documented?" / "Which doc covers …?"
- Grounding a build or design decision in the project's prior research
- Before implementing a stage (ingest, segment, validate, eval, frontend) — find the doc that constrains it
- Locating the paper/citation behind a claim
- Auditing whether a topic is covered at all

## Navigation protocol (L0 → L1 → L2)

1. **Resolve the index.** The index lives at the repo's git root, not beside this skill:
   ```bash
   git rev-parse --show-toplevel    # repo root; index = <root>/docs/INDEX.md
   ```
   Read `<root>/docs/INDEX.md`.
2. **L0 — pick the category.** Match the question to one of the categories (domain /
   design / evaluation / tooling / research) using the category map + the
   "Question → doc" quick-lookup table.
3. **L1 — pick the doc(s).** Within the category, use each doc's **Read when** triggers and
   **Keywords** to choose the 1–2 best docs. A question may legitimately span two docs
   (e.g. confidence design `06` + its calibration papers `13`).
4. **L2 — read the doc** only once the index confirms relevance. Answer from it.
5. **Answer + cite.** Give the answer and name the doc(s): `docs/NN-name.md`. If two docs
   apply, name both and say which is primary.

## Output contract

- Always name the chosen `docs/NN-*.md` path(s) explicitly — the path IS the answer to
  "where is this documented".
- If nothing matches, say so plainly and suggest the nearest category + whether it's a
  genuine coverage gap (don't invent a doc).
- Keep answers grounded in the doc; don't pad with outside knowledge unless flagged.

## Maintenance: rebuild the index

When docs are added/removed/substantially changed, regenerate `docs/INDEX.md`:

1. List `docs/*.md` (excluding `INDEX.md` itself).
2. For each doc, read it and write an L1 entry: **path**, **Read when** (concrete question
   patterns), **Keywords** (the terms a searcher would use), **Answers e.g.** (1–3 sample
   questions), **Key facts/decisions** (1–2 lines).
3. Keep the L0 category map and the "Question → doc" quick-lookup table in sync.
4. The index is judged by one thing: can an agent route an unseen question to the correct
   doc using only the index? If a real question misroutes, add the missing keywords /
   triggers to the offending entry.

## Tips

- The **Keywords** line is the routing signal — put the words a searcher would actually
  type (synonyms, acronyms like iXBRL/DEI/CRF/LIB, and concrete failure names).
- Prefer the quick-lookup table for common questions; fall back to L1 triggers for novel ones.
- One question can map to two docs — that's expected, not a failure; name the primary.
- Never answer a docs question from memory when the index can point to the source doc.
