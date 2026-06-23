# Empirically Prove The Segmenter Choice And The Boundary Blindness

- **Datetime:** 2026-06-23 07:32:07
- **Summary:** User demanded two empirical proofs (run code, not memory) before growing the eval set: (1) my regex segment() vs edgartools .obj() items on Apple side-by-side, with the real reason I didn't use edgartools' structure; (2) inject a tiling-preserving boundary fault into a clean filing and show that needs_review + the silent-failure metric stay clean — proving the infra can't see a wrong boundary.

## Prompt

> two things i still want to nail before we talk about growing the eval set.
>
> first one you didnt mention at all. you already import edgartools and use it to download the filing (the text and html). but edgartools can also parse the filing into structured items by itself, the .obj() item thing. yet your actual segmentation is your own regex on the flattened text. so why you went regex on flat text instead of using the structure edgartools already give you? is it a real tradeoff, like you need the char offsets / char_range that the structured api dont give, or it just ended up that way and nobody compared. dont answer from memory, actually run apple 2024 both ways, your regex segment() vs edgartools structured items, how many items each and where the boundaries are different. show me the two real outputs side by side.
>
> second, you said the boundary blindness in words, now prove it for real so we know exactly what is missing. take a clean filing that comes back needs_review=False like apple, inject a fault by code that shift one item start +200 chars or let item 7 eat the end of item 6, keep all the items present, then run your full assess and show me what needs_review and the silent failure metric say after. if it still say clean, then thats the real proof that nothing in the current infra can see a wrong boundary, and we know what we actually have to build first before we add 50 filings. /save-prompt

## What I Did

- Wrote two throwaway diagnostics under `scratch/` (untracked; no production code changed) and ran them live.
- **Exp 1 (segment vs edgartools, Apple FY2024):** both find 23 item keys, but edgartools' `.obj()` has a DUPLICATE Item 8, jumbled order, and an Item-14 legacy-parser fallback; it returns text blocks with NO char offsets, and its text stream differs from my canonical (kept nbsp/curly quotes) so `canon.find()` = -1 for all 23 → cannot recover char_range from it. Honest conclusion: a REAL tradeoff (we need offsets) AND I never actually compared before now (the design only assumed it). Upshot: edgartools is a ready independent SECOND extractor (the dual-check the design wants).
- **Exp 2 (boundary blindness, live assess):** baseline clean. Fault A (item1A eats 200 chars of item1, tiling intact, all present) → needs_review=False, SILENT_FAILURE=False, both bands HIGH — IDENTICAL to baseline. Fault B (gap left, tiling broken) → needs_review=True (caught). Proof: infra catches tiling breaks only; it is BLIND to boundary drift; the silent-failure metric is presence-only and definitionally cannot see Fault A.
- **Conclusion delivered:** before adding filings, build a boundary cross-check (wire edgartools .obj()/CRF as independent 2nd extractor, flag boundary disagreement) and/or char-exact gold (STRETCH scorer #4). More filings won't help boundary quality until then.
- Every claim tagged TRACED (ran it) vs HONEST/ASSUMED.
